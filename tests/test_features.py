"""Testes unitários para o módulo de Feature Engineering."""

import numpy as np
import pandas as pd
import pytest

from data_pipeline.features import (
    add_cyclical_features,
    add_lag_features,
    add_rolling_features,
    add_target_variables,
    build_feature_dataset,
)


@pytest.fixture
def sample_timeseries():
    """Gera série temporal sintética com 2 municípios e 20 semanas."""
    records = []
    for mun in [2507507, 2504009]:
        for w in range(1, 21):
            records.append(
                {
                    "municipio_id": mun,
                    "doenca": "dengue",
                    "data_inicio_se": pd.to_datetime(f"2024-01-01") + pd.Timedelta(weeks=w - 1),
                    "ano": 2024,
                    "semana_epidemiologica": w,
                    "casos_notificados": w * 2,
                    "casos_estimados": w * 2.5,
                    "taxa_reproducao_rt": 1.1,
                    "nivel_alerta": 2 if w < 10 else 3,
                    "temperatura_media": 28.0,
                    "temperatura_maxima": 32.0,
                    "umidade_media": 75.0,
                    "incidencia_100k": 10.0,
                }
            )
    return pd.DataFrame(records)


def test_cyclical_features(sample_timeseries):
    df_cyc = add_cyclical_features(sample_timeseries)

    assert "semana_sin" in df_cyc.columns
    assert "semana_cos" in df_cyc.columns
    assert (df_cyc["semana_sin"] >= -1.0).all() and (df_cyc["semana_sin"] <= 1.0).all()
    assert (df_cyc["semana_cos"] >= -1.0).all() and (df_cyc["semana_cos"] <= 1.0).all()


def test_lag_features_grouped(sample_timeseries):
    df_lag = add_lag_features(sample_timeseries, columns=["casos_notificados"], lags=[1, 2])

    assert "casos_notificados_lag_1" in df_lag.columns
    assert "casos_notificados_lag_2" in df_lag.columns

    # Para a semana 3 do município 2507507, lag 1 deve ser semana 2 (4 casos) e lag 2 deve ser semana 1 (2 casos)
    row_w3 = df_lag[(df_lag["municipio_id"] == 2507507) & (df_lag["semana_epidemiologica"] == 3)].iloc[0]
    assert row_w3["casos_notificados_lag_1"] == 4
    assert row_w3["casos_notificados_lag_2"] == 2


def test_target_variables(sample_timeseries):
    df_target = add_target_variables(sample_timeseries, horizons=[1, 2])

    assert "alvo_casos_1sem" in df_target.columns
    assert "alvo_casos_2sem" in df_target.columns
    assert "alvo_surto_2sem" in df_target.columns

    # Para semana 1, alvo_casos_1sem deve ser semana 2 (4 casos)
    row_w1 = df_target[(df_target["municipio_id"] == 2507507) & (df_target["semana_epidemiologica"] == 1)].iloc[0]
    assert row_w1["alvo_casos_1sem"] == 4
    assert row_w1["alvo_casos_2sem"] == 6


def test_build_feature_dataset(sample_timeseries):
    df_feat = build_feature_dataset(sample_timeseries, horizons=[1, 2], drop_na=True)

    assert not df_feat.empty
    assert "casos_notificados_lag_1" in df_feat.columns
    assert "alvo_casos_1sem" in df_feat.columns
    assert df_feat["casos_notificados_lag_1"].isna().sum() == 0
