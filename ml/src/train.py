# Training script for arboviral forecasting models
"""
Machine learning training pipeline.

- Loads the feature dataset.
- Performs temporal train/test split.
- Cleans and prepares numerical and categorical features.
- Trains regression models to predict future case counts (target: alvo_casos_1sem).
- Trains classification models to predict risk level (target: alvo_risco_1sem).
- Evaluates models and saves the best performing ones.
"""

import argparse
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    accuracy_score,
    f1_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .split import load_features, temporal_train_test_split


def prepare_data(df: pd.DataFrame, target_col: str):
    """Filter missing target rows, separate features and target, and encode categoricals."""
    # Drop rows without target
    valid_df = df.dropna(subset=[target_col]).copy()

    # Drop all target columns from features
    target_cols = [c for c in valid_df.columns if c.startswith("alvo_")]
    # Metadata / non-predictive identifiers
    metadata_cols = ["municipio_id", "municipio_nome", "data_inicio_se", "microrregiao", "mesorregiao"]
    drop_cols = list(set(target_cols + metadata_cols))

    X = valid_df.drop(columns=drop_cols, errors="ignore")
    # One-hot encode categorical columns like 'doenca'
    if "doenca" in X.columns:
        X = pd.get_dummies(X, columns=["doenca"], drop_first=False, dtype=float)

    # Ensure all remaining columns are numeric
    X = X.select_dtypes(include=[np.number])
    y = valid_df[target_col]
    return X, y, valid_df["data_inicio_se"]


def train_regression(X_train, y_train, X_test, y_test):
    pipelines = {
        "ridge": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=1.0, random_state=42)),
        ]),
        "rf": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("model", RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)),
        ]),
    }
    best_model = None
    best_mae = float("inf")
    results = {}

    for name, pipe in pipelines.items():
        pipe.fit(X_train, y_train)
        preds = pipe.predict(X_test)
        mae = float(mean_absolute_error(y_test, preds))
        mse = float(mean_squared_error(y_test, preds))
        rmse = float(np.sqrt(mse))
        r2 = float(r2_score(y_test, preds))
        results[name] = {"mae": mae, "rmse": rmse, "r2": r2}
        if mae < best_mae:
            best_mae = mae
            best_model = (name, pipe)

    return best_model, results


def train_classification(X_train, y_train, X_test, y_test):
    # Cast targets to int
    y_train = y_train.astype(int)
    y_test = y_test.astype(int)

    pipelines = {
        "logreg": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=1000, random_state=42)),
        ]),
        "rf": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("model", RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)),
        ]),
    }
    best_model = None
    best_f1 = -1
    results = {}

    for name, pipe in pipelines.items():
        pipe.fit(X_train, y_train)
        preds = pipe.predict(X_test)
        acc = float(accuracy_score(y_test, preds))
        f1 = float(f1_score(y_test, preds, average="weighted", zero_division=0))
        results[name] = {"accuracy": acc, "f1": f1}
        if f1 > best_f1:
            best_f1 = f1
            best_model = (name, pipe)

    return best_model, results


def main(csv_path: str, output_dir: str, test_weeks: int = 12):
    df = load_features(csv_path)

    # 1. Regressão (alvo_casos_1sem)
    target_reg = "alvo_casos_1sem"
    X_reg, y_reg, dates_reg = prepare_data(df, target_reg)

    reg_df = X_reg.copy()
    reg_df["data_inicio_se"] = dates_reg
    reg_df[target_reg] = y_reg

    train_reg, test_reg = temporal_train_test_split(reg_df, test_weeks)
    features_reg = [c for c in X_reg.columns]

    X_train_reg = train_reg[features_reg]
    y_train_reg = train_reg[target_reg]
    X_test_reg = test_reg[features_reg]
    y_test_reg = test_reg[target_reg]

    (reg_name, reg_model), reg_metrics = train_regression(
        X_train_reg, y_train_reg, X_test_reg, y_test_reg
    )

    # 2. Classificação (alvo_risco_1sem)
    target_clf = "alvo_risco_1sem"
    X_clf, y_clf, dates_clf = prepare_data(df, target_clf)

    clf_df = X_clf.copy()
    clf_df["data_inicio_se"] = dates_clf
    clf_df[target_clf] = y_clf

    train_clf, test_clf = temporal_train_test_split(clf_df, test_weeks)
    features_clf = [c for c in X_clf.columns]

    X_train_clf = train_clf[features_clf]
    y_train_clf = train_clf[target_clf]
    X_test_clf = test_clf[features_clf]
    y_test_clf = test_clf[target_clf]

    (clf_name, clf_model), clf_metrics = train_classification(
        X_train_clf, y_train_clf, X_test_clf, y_test_clf
    )

    # Salvar modelos
    os.makedirs(output_dir, exist_ok=True)
    reg_path = Path(output_dir) / f"regression_{reg_name}.joblib"
    clf_path = Path(output_dir) / f"classification_{clf_name}.joblib"
    joblib.dump(reg_model, reg_path)
    joblib.dump(clf_model, clf_path)

    report = {
        "regression": {
            "target": target_reg,
            "best_model": reg_name,
            "metrics": reg_metrics,
            "test_samples": int(len(test_reg)),
            "train_samples": int(len(train_reg)),
        },
        "classification": {
            "target": target_clf,
            "best_model": clf_name,
            "metrics": clf_metrics,
            "test_samples": int(len(test_clf)),
            "train_samples": int(len(train_clf)),
        },
        "features_used": features_reg,
    }

    metrics_file = Path(output_dir) / "metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Treinamento concluído. Modelos salvos em: {output_dir}")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train ML models for ZikAI")
    parser.add_argument("csv_path", help="Path to the features CSV (pb_arboviroses_features.csv)")
    parser.add_argument("--output-dir", default="ml/models", help="Directory where models and metrics will be stored")
    parser.add_argument("--test-weeks", type=int, default=12, help="Number of weeks to keep for test set")
    args = parser.parse_args()
    main(args.csv_path, args.output_dir, args.test_weeks)
