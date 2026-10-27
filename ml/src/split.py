"""Módulo de utilitários para divisão temporal (Train/Test Split) de séries temporais.

Funções para dividir o conjunto de features em treino e teste mantendo
rigorosamente a ordem cronológica, evitando vazamento de dados temporais (data leakage).
A divisão é baseada nas semanas epidemiológicas mais recentes.
"""

from datetime import datetime
import pandas as pd


def load_features(csv_path: str) -> pd.DataFrame:
    """Carrega o dataset de features em CSV gerado pelo pipeline.

    Parâmetros
    ----------
    csv_path: str
        Caminho para o arquivo ``pb_arboviroses_features.csv``.

    Retorna
    -------
    pd.DataFrame
        DataFrame com a coluna ``data_inicio_se`` tipada como ``datetime``.
    """
    df = pd.read_csv(csv_path, parse_dates=["data_inicio_se"], dayfirst=False)
    return df


def temporal_train_test_split(
    df: pd.DataFrame,
    test_weeks: int = 12,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Divide o DataFrame em conjuntos de treino e teste utilizando as semanas mais recentes.

    Parâmetros
    ----------
    df: pd.DataFrame
        DataFrame de atributos ordenado por ``data_inicio_se``.
    test_weeks: int, padrão 12
        Número de semanas finais reservadas exclusivamente para o conjunto de teste.

    Retorna
    -------
    (train_df, test_df): tupla contendo (DataFrame de treino, DataFrame de teste)
    """
    if "data_inicio_se" not in df.columns:
        raise ValueError("Coluna 'data_inicio_se' não encontrada no DataFrame.")

    df = df.sort_values("data_inicio_se").reset_index(drop=True)

    # Determinar a data de corte temporal
    max_date = df["data_inicio_se"].max()
    cutoff_date = max_date - pd.Timedelta(weeks=test_weeks)

    train_df = df[df["data_inicio_se"] <= cutoff_date].copy()
    test_df = df[df["data_inicio_se"] > cutoff_date].copy()

    return train_df, test_df


if __name__ == "__main__":
    # Interface CLI simples para verificação rápida do particionamento
    import argparse

    parser = argparse.ArgumentParser(description="Divisão temporal cronológica do conjunto de atributos")
    parser.add_argument("csv_path", help="Caminho do CSV de features")
    parser.add_argument("--test-weeks", type=int, default=12, help="Semanas reservadas para teste")
    args = parser.parse_args()

    df = load_features(args.csv_path)
    train, test = temporal_train_test_split(df, args.test_weeks)
    print(f"Linhas de Treino: {len(train)}, Linhas de Teste: {len(test)}")
