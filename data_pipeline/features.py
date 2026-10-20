"""Módulo de Engenharia de Recursos (Feature Engineering) para Séries Temporais Epidemiológicas.

Transforma as séries históricas brutas em matrizes de atributos supervisionados:
- Defasagens temporais (lags) de casos notificados e estimados
- Defasagens climáticas (temperatura e umidade)
- Médias e desvios móveis
- Codificação periódica da semana epidemiológica (seno/cosseno)
- Variáveis-alvo para múltiplos horizontes de previsão (1 a 4 semanas à frente)
"""

from __future__ import annotations

import logging
from typing import List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def add_cyclical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Codifica a semana epidemiológica em componentes cíclicos contínuos (seno e cosseno).

    A semana 52/53 e a semana 1 possuem proximidade temporal real.
    A transformação trigonométrica preserva essa continuidade para modelos de IA.
    """
    df = df.copy()
    if "semana_epidemiologica" in df.columns:
        # Número médio de semanas epidemiológicas no ano (~52.1775)
        periodo = 52.1775
        semana = df["semana_epidemiologica"].astype(float)
        df["semana_sin"] = np.sin(2 * np.pi * semana / periodo)
        df["semana_cos"] = np.cos(2 * np.pi * semana / periodo)

    if "data_inicio_se" in df.columns:
        mes = pd.to_datetime(df["data_inicio_se"]).dt.month
        df["mes_sin"] = np.sin(2 * np.pi * mes / 12.0)
        df["mes_cos"] = np.cos(2 * np.pi * mes / 12.0)

    return df


def add_lag_features(
    df: pd.DataFrame,
    columns: List[str],
    lags: List[int] = [1, 2, 3, 4],
    group_cols: List[str] = ["municipio_id", "doenca"],
) -> pd.DataFrame:
    """Adiciona defasagens temporais (lags) para as variáveis selecionadas por município e doença.

    Exemplo: casos no tempo t-1, t-2, t-3, t-4.
    """
    df = df.copy()
    df = df.sort_values(group_cols + ["data_inicio_se"]).reset_index(drop=True)

    grouped = df.groupby(group_cols)

    for col in columns:
        if col not in df.columns:
            continue
        for lag in lags:
            col_name = f"{col}_lag_{lag}"
            df[col_name] = grouped[col].shift(lag)

    return df


def add_rolling_features(
    df: pd.DataFrame,
    columns: List[str],
    windows: List[int] = [4, 8],
    group_cols: List[str] = ["municipio_id", "doenca"],
) -> pd.DataFrame:
    """Adiciona estatísticas móveis (média e desvio padrão) calculadas com dados passados.

    Importante: aplica shift(1) antes da janela móvel para evitar vazamento de dados futuros (data leakage).
    """
    df = df.copy()
    df = df.sort_values(group_cols + ["data_inicio_se"]).reset_index(drop=True)

    grouped = df.groupby(group_cols)

    for col in columns:
        if col not in df.columns:
            continue
        for window in windows:
            # Shift 1 para usar apenas o passado
            shifted = grouped[col].shift(1)
            # Agrupar novamente a série deslocada para aplicar rolling dentro do grupo
            df[f"{col}_media_movel_{window}"] = (
                shifted.groupby([df[g] for g in group_cols])
                .rolling(window, min_periods=max(2, window // 2))
                .mean()
                .reset_index(drop=True)
            )
            df[f"{col}_desvio_movel_{window}"] = (
                shifted.groupby([df[g] for g in group_cols])
                .rolling(window, min_periods=max(2, window // 2))
                .std()
                .reset_index(drop=True)
            )

    return df


def add_target_variables(
    df: pd.DataFrame,
    horizons: List[int] = [1, 2, 3, 4],
    group_cols: List[str] = ["municipio_id", "doenca"],
) -> pd.DataFrame:
    """Cria variáveis-alvo (labels) supervisionadas para os modelos de regressão e classificação.

    - alvo_casos_Hsem: número de casos a H semanas à frente (regressão)
    - alvo_risco_Hsem: nível de alerta do InfoDengue a H semanas à frente (classificação 1 a 4)
    - alvo_surto_2sem: classificação binária de surto (1 se casos > limiar epidêmico, 0 caso contrário)
    """
    df = df.copy()
    df = df.sort_values(group_cols + ["data_inicio_se"]).reset_index(drop=True)

    grouped = df.groupby(group_cols)

    for h in horizons:
        # Previsão contínua de casos
        if "casos_notificados" in df.columns:
            df[f"alvo_casos_{h}sem"] = grouped["casos_notificados"].shift(-h)

        # Previsão do nível de risco (1: Verde, 2: Amarelo, 3: Laranja, 4: Vermelho)
        if "nivel_alerta" in df.columns:
            df[f"alvo_risco_{h}sem"] = grouped["nivel_alerta"].shift(-h)

    # Indicador binário de surto a 2 semanas (alerta Laranja ou Vermelho: nível >= 3)
    if "alvo_risco_2sem" in df.columns:
        df["alvo_surto_2sem"] = (df["alvo_risco_2sem"] >= 3).astype(float)

    return df


def build_feature_dataset(
    df: pd.DataFrame,
    horizons: List[int] = [1, 2, 3, 4],
    drop_na: bool = True,
) -> pd.DataFrame:
    """Pipeline completo de transformação de dados para aprendizado de máquina.

    Recebe o DataFrame consolidado do InfoDengue/IBGE e produz o conjunto de treino/teste estruturado.
    """
    if df.empty:
        return df

    logger.info("Iniciando engenharia de atributos em %d registros...", len(df))

    # 1. Componentes sazonais cíclicos
    df_feat = add_cyclical_features(df)

    # 2. Lags temporais de casos (1 a 4 semanas passadas)
    df_feat = add_lag_features(
        df_feat,
        columns=["casos_notificados", "casos_estimados", "taxa_reproducao_rt"],
        lags=[1, 2, 3, 4],
    )

    # 3. Lags climáticos (temperatura e umidade de 1 a 3 semanas atrás)
    df_feat = add_lag_features(
        df_feat,
        columns=["temperatura_media", "temperatura_maxima", "umidade_media"],
        lags=[1, 2, 3],
    )

    # 4. Médias e desvios móveis (tendências de 4 e 8 semanas)
    df_feat = add_rolling_features(
        df_feat,
        columns=["casos_notificados", "temperatura_media", "umidade_media"],
        windows=[4, 8],
    )

    # 5. Adicionar variáveis-alvo (labels futuras)
    df_feat = add_target_variables(df_feat, horizons=horizons)

    # 6. Tratar valores ausentes (primeiras semanas sem histórico de lag)
    if drop_na:
        # Remover apenas linhas onde os lags principais e os alvos imediatos são nulos
        essential_cols = ["casos_notificados_lag_1", "casos_notificados_lag_2", "alvo_casos_1sem"]
        df_feat = df_feat.dropna(subset=[c for c in essential_cols if c in df_feat.columns])
        df_feat = df_feat.reset_index(drop=True)

    logger.info(
        "Engenharia de atributos concluída. Colunas geradas: %d | Linhas válidas: %d",
        df_feat.shape[1],
        len(df_feat),
    )
    return df_feat
