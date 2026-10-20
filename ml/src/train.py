"""Pipeline de Treinamento de Modelos de Aprendizado de Máquina - ZikAI Paraíba.

- Carrega o dataset de features processadas.
- Realiza a divisão temporal entre treino e teste (respeitando a cronologia dos dados).
- Trata e limpa features numéricas e codifica variáveis categóricas (One-Hot Encoding).
- Treina modelos de regressão para prever o total de casos futuros (alvo: alvo_casos_1sem).
- Treina modelos de classificação para prever o nível de alerta/risco (alvo: alvo_risco_1sem).
- Avalia os modelos com métricas epidemiológicas (MAE, RMSE, R², Acurácia, F1-Score).
- Persiste os melhores modelos treinados (.joblib) e exporta relatório em JSON.
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
    """Filtra linhas sem variável-alvo, separa atributos (X) e rótulo (y) e codifica variáveis categóricas."""
    # Remover linhas sem o valor do alvo (semanas no final da série histórica)
    valid_df = df.dropna(subset=[target_col]).copy()

    # Remover todas as colunas de horizonte futuro para prevenir vazamento de dados (data leakage)
    target_cols = [c for c in valid_df.columns if c.startswith("alvo_")]
    # Metadados e identificadores não preditivos diretos
    metadata_cols = ["municipio_id", "municipio_nome", "data_inicio_se", "microrregiao", "mesorregiao"]
    drop_cols = list(set(target_cols + metadata_cols))

    X = valid_df.drop(columns=drop_cols, errors="ignore")

    # Codificação One-Hot para variáveis categóricas como 'doenca' (dengue, zika, chikungunya)
    if "doenca" in X.columns:
        X = pd.get_dummies(X, columns=["doenca"], drop_first=False, dtype=float)

    # Garantir que todas as colunas restantes sejam puramente numéricas
    X = X.select_dtypes(include=[np.number])
    y = valid_df[target_col]
    return X, y, valid_df["data_inicio_se"]


def train_regression(X_train, y_train, X_test, y_test):
    """Treina e compara algoritmos de regressão para previsão quantitativa de casos."""
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
    """Treina e compara modelos de classificação multiclasse para o nível de alerta de risco."""
    # Converter rótulos de risco para inteiros
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
    """Executa a rotina completa de ponta a ponta do treinamento dos modelos de IA."""
    df = load_features(csv_path)

    # 1. Pipeline de Regressão (alvo_casos_1sem)
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

    # 2. Pipeline de Classificação (alvo_risco_1sem)
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

    # Persistência dos modelos treinados (.joblib)
    os.makedirs(output_dir, exist_ok=True)
    reg_path = Path(output_dir) / f"regression_{reg_name}.joblib"
    clf_path = Path(output_dir) / f"classification_{clf_name}.joblib"
    joblib.dump(reg_model, reg_path)
    joblib.dump(clf_model, clf_path)

    # Relatório estruturado de métricas para auditoria e monografia
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
    parser = argparse.ArgumentParser(description="Treinamento de Modelos de Machine Learning - ZikAI Paraíba")
    parser.add_argument("csv_path", help="Caminho do CSV de atributos (pb_arboviroses_features.csv)")
    parser.add_argument("--output-dir", default="ml/models", help="Diretório onde os modelos e métricas serão salvos")
    parser.add_argument("--test-weeks", type=int, default=12, help="Número de semanas finais reservadas para teste")
    args = parser.parse_args()
    main(args.csv_path, args.output_dir, args.test_weeks)
