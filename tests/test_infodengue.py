"""Testes unitários para o cliente da API do InfoDengue."""

from pathlib import Path
import pytest
import pandas as pd
from data_pipeline.infodengue import InfoDengueClient


def test_infodengue_invalid_disease(tmp_path: Path):
    client = InfoDengueClient(raw_data_dir=tmp_path)
    with pytest.raises(ValueError, match="Doença inválida"):
        client.fetch_city_data(geocode=2507507, disease="covid19")


def test_infodengue_records_normalization(tmp_path: Path):
    client = InfoDengueClient(raw_data_dir=tmp_path)

    # Amostra simulada de resposta do InfoDengue
    fake_records = [
        {
            "data_iniSE": 1704585600000,
            "SE": 202401,
            "casos": 12,
            "casos_est": 15,
            "Rt": 1.25,
            "p_rt1": 0.85,
            "nivel": 2,
            "tempmed": 27.5,
            "tempmin": 23.0,
            "tempmax": 31.0,
            "umidmed": 78.0,
            "umidmin": 65.0,
            "umidmax": 90.0,
            "pop": 830000,
            "p_inc100k": 1.8,
            "municipio_nome": "João Pessoa",
        }
    ]

    df = client._records_to_dataframe(fake_records, disease="dengue", geocode=2507507)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["municipio_id"] == 2507507
    assert df.iloc[0]["doenca"] == "dengue"
    assert df.iloc[0]["ano"] == 2024
    assert df.iloc[0]["semana_epidemiologica"] == 1
    assert df.iloc[0]["casos_notificados"] == 12
    assert df.iloc[0]["casos_estimados"] == 15
    assert df.iloc[0]["taxa_reproducao_rt"] == 1.25
    assert df.iloc[0]["temperatura_media"] == 27.5
