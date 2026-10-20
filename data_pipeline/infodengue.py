"""Cliente de integração com a API pública do InfoDengue (Fiocruz / FGV).

Permite baixar o histórico epidemiológico semanal de Dengue, Chikungunya e Zika
para municípios da Paraíba com dados climáticos acoplados.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import urllib.parse
import urllib.request

import pandas as pd

logger = logging.getLogger(__name__)

VALID_DISEASES = ("dengue", "chikungunya", "zika")


class InfoDengueClient:
    """Cliente para a API pública REST do InfoDengue."""

    BASE_URL = "https://info.dengue.mat.br/api/alertcity"

    def __init__(self, raw_data_dir: Path | str = "data/raw"):
        self.raw_data_dir = Path(raw_data_dir)
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

    def fetch_city_data(
        self,
        geocode: int,
        disease: str = "dengue",
        start_year: int = 2018,
        end_year: int = 2025,
        ew_start: int = 1,
        ew_end: int = 53,
        force_refresh: bool = False,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> pd.DataFrame:
        """Busca a série temporal epidemiológica de um município no InfoDengue.

        Parâmetros:
            geocode: Código IBGE de 7 dígitos do município (ex: 2507507 para João Pessoa).
            disease: Uma dentre 'dengue', 'chikungunya' ou 'zika'.
            start_year: Ano de início da série histórica.
            end_year: Ano final da série histórica.
            ew_start: Semana epidemiológica inicial (1 a 53).
            ew_end: Semana epidemiológica final (1 a 53).
            force_refresh: Força novo download ignorando cache local.
            max_retries: Tentativas em caso de falha de conexão.
            retry_delay: Intervalo entre tentativas.

        Retorna:
            pd.DataFrame limpo e ordenado cronologicamente.
        """
        disease = disease.lower()
        if disease not in VALID_DISEASES:
            raise ValueError(f"Doença inválida '{disease}'. Opções: {VALID_DISEASES}")

        cache_filename = f"infodengue_{disease}_{geocode}_{start_year}_{end_year}.json"
        cache_path = self.raw_data_dir / cache_filename

        if cache_path.exists() and not force_refresh:
            logger.info("Carregando dados do InfoDengue em cache: %s", cache_path)
            with open(cache_path, "r", encoding="utf-8") as f:
                records = json.load(f)
            return self._records_to_dataframe(records, disease=disease, geocode=geocode)

        params = {
            "geocode": geocode,
            "disease": disease,
            "format": "json",
            "ew_start": ew_start,
            "ew_end": ew_end,
            "ey_start": start_year,
            "ey_end": end_year,
        }
        query_string = urllib.parse.urlencode(params)
        full_url = f"{self.BASE_URL}?{query_string}"

        logger.info(
            "Consultando InfoDengue para geocode=%s, doenca=%s (%d a %d)...",
            geocode,
            disease,
            start_year,
            end_year,
        )

        records: List[Dict[str, Any]] = []
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                req = urllib.request.Request(
                    full_url,
                    headers={
                        "User-Agent": "ZikAI-Paraiba-Research/1.0 (academic TCC project)",
                        "Accept": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=25) as response:
                    raw_content = response.read().decode("utf-8")
                    records = json.loads(raw_content)
                break
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Tentativa %d falhou para %s (%s): %s",
                    attempt,
                    geocode,
                    disease,
                    exc,
                )
                time.sleep(retry_delay * attempt)

        if not records and last_error:
            logger.error(
                "Falha ao obter dados do InfoDengue para geocode %s: %s", geocode, last_error
            )
            # Retorna DataFrame vazio estruturado
            return self._records_to_dataframe([], disease=disease, geocode=geocode)

        # Salvar em cache
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False)

        return self._records_to_dataframe(records, disease=disease, geocode=geocode)

    def _records_to_dataframe(
        self, records: List[Dict[str, Any]], disease: str, geocode: int
    ) -> pd.DataFrame:
        """Converte e padroniza a lista de registros da API para DataFrame do Pandas."""
        if not records:
            return pd.DataFrame(
                columns=[
                    "data_inicio_se",
                    "ano",
                    "semana_epidemiologica",
                    "municipio_id",
                    "municipio_nome",
                    "doenca",
                    "casos_notificados",
                    "casos_estimados",
                    "taxa_reproducao_rt",
                    "probabilidade_rt_maior_1",
                    "nivel_alerta",
                    "temperatura_media",
                    "temperatura_minima",
                    "temperatura_maxima",
                    "umidade_media",
                    "umidade_minima",
                    "umidade_maxima",
                    "populacao",
                    "incidencia_100k",
                ]
            )

        df = pd.DataFrame(records)

        # Tratar data_iniSE (pode vir em milissegundos timestamp ou data)
        if "data_iniSE" in df.columns:
            if pd.api.types.is_numeric_dtype(df["data_iniSE"]):
                df["data_inicio_se"] = pd.to_datetime(df["data_iniSE"], unit="ms")
            else:
                df["data_inicio_se"] = pd.to_datetime(df["data_iniSE"])
        else:
            df["data_inicio_se"] = pd.NaT

        # Extrair ano e semana a partir do campo 'SE' (formato YYYYWW, ex: 202401)
        if "SE" in df.columns:
            se_series = df["SE"].astype(str)
            df["ano"] = se_series.str[:4].astype(int)
            df["semana_epidemiologica"] = se_series.str[4:].astype(int)
        else:
            df["ano"] = df["data_inicio_se"].dt.year
            df["semana_epidemiologica"] = df["data_inicio_se"].dt.isocalendar().week

        # Mapeamento e renomeação intuitiva em português
        rename_map = {
            "casos": "casos_notificados",
            "casos_est": "casos_estimados",
            "Rt": "taxa_reproducao_rt",
            "p_rt1": "probabilidade_rt_maior_1",
            "nivel": "nivel_alerta",
            "tempmed": "temperatura_media",
            "tempmin": "temperatura_minima",
            "tempmax": "temperatura_maxima",
            "umidmed": "umidade_media",
            "umidmin": "umidade_minima",
            "umidmax": "umidade_maxima",
            "pop": "populacao",
            "p_inc100k": "incidencia_100k",
        }

        for old_col, new_col in rename_map.items():
            if old_col in df.columns:
                df[new_col] = df[old_col]

        df["municipio_id"] = geocode
        df["doenca"] = disease

        # Nomes das colunas finais
        target_cols = [
            "data_inicio_se",
            "ano",
            "semana_epidemiologica",
            "municipio_id",
            "municipio_nome",
            "doenca",
            "casos_notificados",
            "casos_estimados",
            "taxa_reproducao_rt",
            "probabilidade_rt_maior_1",
            "nivel_alerta",
            "temperatura_media",
            "temperatura_minima",
            "temperatura_maxima",
            "umidade_media",
            "umidade_minima",
            "umidade_maxima",
            "populacao",
            "incidencia_100k",
        ]

        # Garantir presença de todas as colunas alvo
        for col in target_cols:
            if col not in df.columns:
                df[col] = None

        df = df[target_cols].sort_values("data_inicio_se").reset_index(drop=True)
        return df
