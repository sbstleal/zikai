"""Orquestrador do Pipeline de Dados - ZikAI Paraíba.

Executa a ingestão combinada de dados do InfoDengue e do IBGE para o Estado da Paraíba.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd

from .features import build_feature_dataset
from .ibge import IBGEClient
from .infodengue import InfoDengueClient
from backend.app.db.session import SessionLocal, init_db
from backend.app.db.repository import upsert_municipios, load_dataframe_to_registros

# Municípios estratégicos representativos das mesorregiões da Paraíba
PRINCIPAIS_MUNICIPIOS_PB = {
    2507507: "João Pessoa",      # Mata Paraibana / Litoral (Capital)
    2504009: "Campina Grande",   # Agreste Paraibano (Polo Tecnológico)
    2510808: "Patos",            # Sertão Paraibano
    2516201: "Sousa",            # Alto Sertão
    2503704: "Cajazeiras",       # Alto Sertão / Fronteira CE
    2506301: "Guarabira",        # Brejo Paraibano
    2509701: "Monteiro",         # Cariri Ocidental
    2513703: "Santa Rita",       # Região Metropolitana de JP
    2501807: "Bayeux",           # Região Metropolitana de JP
    2503209: "Cabedelo",         # Região Metropolitana de JP / Litoral Norte
}

logger = logging.getLogger("zikai.pipeline")


def run_pipeline(
    geocodes: Optional[List[int]] = None,
    diseases: Optional[List[str]] = None,
    start_year: int = 2018,
    end_year: int = 2025,
    output_dir: str = "data/processed",
    force_refresh: bool = False,
    generate_features: bool = True,
) -> pd.DataFrame:
    """Executa o pipeline completo de coleta e consolidação de dados da Paraíba.

    1. Baixa metadados e malha vetorial dos 223 municípios via IBGE.
    2. Coleta séries históricas epidemiológicas e climáticas via InfoDengue.
    3. Consolida e exporta os datasets processados (CSV).
    4. Gera atributos de Machine Learning (lags, clima, médias móveis, sazonalidade).
    5. Sincroniza opcionalmente com o Banco de Dados SQL.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if geocodes is None:
        geocodes = list(PRINCIPAIS_MUNICIPIOS_PB.keys())

    if diseases is None:
        diseases = ["dengue", "chikungunya", "zika"]

    ibge_client = IBGEClient()
    infodengue_client = InfoDengueClient()

    # 1. Obter e salvar catálogo de todos os 223 municípios da PB e GeoJSON
    logger.info("=== 1. Coleta de Metadados e Malha Geográfica da PB (IBGE) ===")
    municipios_pb = ibge_client.fetch_pb_municipalities(force_refresh=force_refresh)
    ibge_client.fetch_pb_geojson(quality="minima", force_refresh=force_refresh)
    logger.info("Catálogo IBGE pronto: %d municípios mapeados.", len(municipios_pb))

    # Mapear geocode -> microrregiao / mesorregiao para enriquecimento
    geo_meta = {
        m["geocode"]: {
            "microrregiao": m.get("microrregiao"),
            "mesorregiao": m.get("mesorregiao"),
            "nome_oficial": m.get("nome"),
        }
        for m in municipios_pb
    }

    # 2. Coletar dados do InfoDengue
    logger.info("=== 2. Coleta de Séries Temporais (InfoDengue) ===")
    logger.info(
        "Municípios alvos: %d | Doenças: %s | Anos: %d-%d",
        len(geocodes),
        diseases,
        start_year,
        end_year,
    )

    dataframes: List[pd.DataFrame] = []

    for geocode in geocodes:
        city_meta = geo_meta.get(geocode, {})
        city_name = city_meta.get(
            "nome_oficial", PRINCIPAIS_MUNICIPIOS_PB.get(geocode, str(geocode))
        )

        for disease in diseases:
            logger.info("Processando: %s (IBGE %d) - %s", city_name, geocode, disease.upper())
            df_city = infodengue_client.fetch_city_data(
                geocode=geocode,
                disease=disease,
                start_year=start_year,
                end_year=end_year,
                force_refresh=force_refresh,
            )

            if not df_city.empty:
                df_city["microrregiao"] = city_meta.get("microrregiao")
                df_city["mesorregiao"] = city_meta.get("mesorregiao")
                if "municipio_nome" not in df_city.columns or df_city["municipio_nome"].isna().all():
                    df_city["municipio_nome"] = city_name
                dataframes.append(df_city)

    if not dataframes:
        logger.warning("Nenhum dado retornado para a seleção informada.")
        return pd.DataFrame()

    df_consolidated = pd.concat(dataframes, ignore_index=True)

    # Ordenação canônica para séries temporais
    df_consolidated = df_consolidated.sort_values(
        ["doenca", "municipio_id", "data_inicio_se"]
    ).reset_index(drop=True)

    # 3. Exportar dados consolidados para CSV
    csv_file = output_path / "pb_arboviroses_consolidado.csv"
    df_consolidated.to_csv(csv_file, index=False, encoding="utf-8")
    logger.info("Dataset consolidado salvo em: %s (Total linhas: %d)", csv_file, len(df_consolidated))

    # 4. Engenharia de Recursos (Feature Engineering para IA)
    if generate_features:
        try:
            logger.info("=== 3. Gerando Dataset Analítico com Features para IA ===")
            df_features = build_feature_dataset(df_consolidated)
            feat_file = output_path / "pb_arboviroses_features.csv"
            df_features.to_csv(feat_file, index=False, encoding="utf-8")
            logger.info(
                "Dataset de Features salvo em: %s (Linhas: %d, Atributos: %d)",
                feat_file,
                len(df_features),
                df_features.shape[1],
            )
        except Exception as feat_err:
            logger.warning("Aviso: Falha ao gerar dataset de features: %s", feat_err)

    # 5. Sincronização com o Banco de Dados SQL (PostgreSQL / SQLite)
    try:
        logger.info("=== 4. Sincronização com Banco de Dados SQL ===")
        init_db()
        with SessionLocal() as db:
            upsert_municipios(db, municipios_pb)
            load_dataframe_to_registros(db, df_consolidated)
        logger.info("Sincronização com o banco de dados concluída com sucesso.")
    except Exception as db_err:
        logger.warning("Aviso: Falha ao sincronizar com banco SQL (operação opcional): %s", db_err)

    return df_consolidated


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Pipeline de Extração de Dados ZikAI Paraíba")
    parser.add_argument("--all-pb", action="store_true", help="Baixa dados de todos os 223 municípios da PB")
    parser.add_argument("--force-refresh", action="store_true", help="Ignora cache e força novo download das APIs")
    parser.add_argument("--start-year", type=int, default=2018, help="Ano de início (padrão: 2018)")
    parser.add_argument("--end-year", type=int, default=2025, help="Ano de fim (padrão: 2025)")

    args = parser.parse_args()

    geocodes = None
    if args.all_pb:
        ibge_client = IBGEClient()
        todos = ibge_client.fetch_pb_municipalities()
        geocodes = [m["geocode"] for m in todos]

    run_pipeline(
        geocodes=geocodes,
        start_year=args.start_year,
        end_year=args.end_year,
        force_refresh=args.force_refresh,
    )


if __name__ == "__main__":
    main()
