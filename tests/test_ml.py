"""Testes unitários para o pipeline de Machine Learning."""

import json
from pathlib import Path
import tempfile

import pandas as pd
from ml.src.train import main as train_main


def test_training_runs(tmp_path: Path = Path(tempfile.gettempdir())):
    """Verifica se o pipeline de treinamento roda com sucesso e gera os modelos e métricas."""
    csv_path = Path("data/processed/pb_arboviroses_features.csv")

    # Carregar uma amostra para manter a execução rápida do teste
    df = pd.read_csv(csv_path, nrows=200)
    subset_path = tmp_path / "subset_features.csv"
    df.to_csv(subset_path, index=False)

    output_dir = tmp_path / "ml_models"

    # Executar o treinamento com período de teste reduzido (1 semana) para validação
    train_main(str(subset_path), str(output_dir), test_weeks=1)

    # Verificar se os arquivos dos modelos foram criados
    assert (output_dir / "regression_ridge.joblib").exists() or (output_dir / "regression_rf.joblib").exists()
    assert (output_dir / "classification_logreg.joblib").exists() or (output_dir / "classification_rf.joblib").exists()

    # Verificar se o relatório de métricas foi gerado com a estrutura esperada
    metrics_path = output_dir / "metrics.json"
    assert metrics_path.exists()
    with open(metrics_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert "regression" in report and "classification" in report
    assert "features_used" in report
