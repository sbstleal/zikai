# Training script for arboviral forecasting models
"""
Machine learning training pipeline.

- Loads the feature dataset.
- Performs a temporal train/test split (default last 12 weeks for test).
- Trains regression models to predict future case counts (target: alvo_casos_1sem).
- Trains classification models to predict risk level (target: alvo_risco_1sem).
- Evaluates models and saves the best performing ones.
"""

import argparse
import json
import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, f1_score

from .split import load_features, temporal_train_test_split


def train_regression(X_train, y_train, X_test, y_test):
    models = {
        "ridge": Ridge(alpha=1.0, random_state=42),
        "rf": RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1),
    }
    best_model = None
    best_mae = float("inf")
    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        rmse = mean_squared_error(y_test, preds, squared=False)
        r2 = r2_score(y_test, preds)
        results[name] = {"mae": mae, "rmse": rmse, "r2": r2}
        if mae < best_mae:
            best_mae = mae
            best_model = (name, model)
    return best_model, results


def train_classification(X_train, y_train, X_test, y_test):
    models = {
        "logreg": LogisticRegression(max_iter=1000, random_state=42),
        "rf": RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
    }
    best_model = None
    best_f1 = -1
    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        f1 = f1_score(y_test, preds, average="weighted")
        results[name] = {"accuracy": acc, "f1": f1}
        if f1 > best_f1:
            best_f1 = f1
            best_model = (name, model)
    return best_model, results


def main(csv_path: str, output_dir: str, test_weeks: int = 12):
    df = load_features(csv_path)
    # Define feature columns (exclude target columns and identifiers)
    target_reg = "alvo_casos_1sem"
    target_clf = "alvo_risco_1sem"
    id_cols = ["municipio_id", "municipio_nome", "data_inicio_se"]
    exclude = id_cols + [target_reg, target_clf]
    feature_cols = [c for c in df.columns if c not in exclude]

    train_df, test_df = temporal_train_test_split(df, test_weeks)

    X_train = train_df[feature_cols]
    X_test = test_df[feature_cols]

    # Regression
    y_train_reg = train_df[target_reg]
    y_test_reg = test_df[target_reg]
    (reg_name, reg_model), reg_metrics = train_regression(X_train, y_train_reg, X_test, y_test_reg)

    # Classification
    y_train_clf = train_df[target_clf]
    y_test_clf = test_df[target_clf]
    (clf_name, clf_model), clf_metrics = train_classification(X_train, y_train_clf, X_test, y_test_clf)

    # Save models
    os.makedirs(output_dir, exist_ok=True)
    reg_path = Path(output_dir) / f"regression_{reg_name}.joblib"
    clf_path = Path(output_dir) / f"classification_{clf_name}.joblib"
    joblib.dump(reg_model, reg_path)
    joblib.dump(clf_model, clf_path)

    # Save metrics report
    report = {
        "regression": {"model": reg_name, "metrics": reg_metrics[reg_name]},
        "classification": {"model": clf_name, "metrics": clf_metrics[clf_name]},
        "features_used": feature_cols,
    }
    with open(Path(output_dir) / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Training complete. Models saved to {output_dir}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train ML models for ZikAI")
    parser.add_argument("csv_path", help="Path to the features CSV (pb_arboviroses_features.csv)")
    parser.add_argument("--output-dir", default="ml/models", help="Directory where models and metrics will be stored")
    parser.add_argument("--test-weeks", type=int, default=12, help="Number of weeks to keep for test set")
    args = parser.parse_args()
    main(args.csv_path, args.output_dir, args.test_weeks)
