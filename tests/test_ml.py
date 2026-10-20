import os
import json
import tempfile
from pathlib import Path

import pandas as pd
import pathlib
from ml.src.train import main as train_main


def test_training_runs(tmp_path: pathlib.Path = Path(tempfile.gettempdir())):
    # Use a small subset of the existing feature CSV for quick test
    csv_path = Path('C:/Users/Leal/Documents/Projetos/TCC/zikai/data/processed/pb_arboviroses_features.csv')
    # Load a few rows to keep test fast
    df = pd.read_csv(csv_path, nrows=200)
    subset_path = tmp_path / 'subset_features.csv'
    df.to_csv(subset_path, index=False)

    output_dir = tmp_path / 'ml_models'
    # Run training with a tiny test period (1 week) to speed up
    train_main(str(subset_path), str(output_dir), test_weeks=1)

    # Check that models and metrics were created
    assert (output_dir / 'regression_ridge.joblib').exists() or (output_dir / 'regression_rf.joblib').exists()
    assert (output_dir / 'classification_logreg.joblib').exists() or (output_dir / 'classification_rf.joblib').exists()
    metrics_path = output_dir / 'metrics.json'
    assert metrics_path.exists()
    with open(metrics_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    # Verify report contains expected keys
    assert 'regression' in report and 'classification' in report
    assert 'features_used' in report
