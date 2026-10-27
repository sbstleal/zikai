"""Cliente de integração com a API do IBGE para o Estado da Paraíba.

Fornece métodos para obter a lista dos 223 municípios paraibanos e
a malha geográfica vetorial em formato GeoJSON.
"""

from __future__ import annotations

import gzip
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.request

logger = logging.getLogger(__name__)

# Código UF do Estado da Paraíba
UF_PARAIBA_CODE = 25


class IBGEClient:
    """Cliente para consumo de serviços públicos da API do IBGE."""

    BASE_URL_LOCALIDADES = "https://servicodados.ibge.gov.br/api/v1/localidades"
    BASE_URL_MALHAS = "https://servicodados.ibge.gov.br/api/v3/malhas"

    def __init__(self, raw_data_dir: Path | str = "data/raw"):
        self.raw_data_dir = Path(raw_data_dir)
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

    def fetch_pb_municipalities(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Recupera a lista oficial dos 223 municípios da Paraíba com metadados.

        Retorna dicionários contendo geocode (id de 7 dígitos), nome do município,
        microrregião e mesorregião.
        """
        cache_path = self.raw_data_dir / "pb_municipios_ibge.json"

        if cache_path.exists() and not force_refresh:
            logger.info("Carregando municípios da PB a partir do cache: %s", cache_path)
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)

        url = f"{self.BASE_URL_LOCALIDADES}/estados/{UF_PARAIBA_CODE}/municipios"
        logger.info("Requisitando municípios da PB ao IBGE: %s", url)

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "ZikAI-PB/1.0 (TCC Research)",
                "Accept-Encoding": "gzip, deflate",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            raw_data = response.read()
            if response.info().get("Content-Encoding") == "gzip" or raw_data[:2] == b"\x1f\x8b":
                raw_data = gzip.decompress(raw_data)
            data = json.loads(raw_data.decode("utf-8"))

        # Extrair campos chave padronizados
        municipios = []
        for item in data:
            municipios.append(
                {
                    "geocode": int(item["id"]),
                    "nome": item["nome"],
                    "microrregiao": item.get("microrregiao", {}).get("nome"),
                    "mesorregiao": (
                        item.get("microrregiao", {})
                        .get("mesorregiao", {})
                        .get("nome")
                    ),
                }
            )

        # Ordenar por nome
        municipios.sort(key=lambda m: m["nome"])

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(municipios, f, ensure_ascii=False, indent=2)

        logger.info("Total de municípios da PB salvos em cache: %d", len(municipios))
        return municipios

    def fetch_pb_geojson(
        self, quality: str = "minima", force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Baixa a malha vetorial GeoJSON dos 223 municípios da Paraíba.

        Parâmetros:
            quality: 'minima', 'intermediaria' ou 'maxima'.
            force_refresh: se True, ignora o cache e baixa novamente.
        """
        cache_path = self.raw_data_dir / f"pb_malha_municipios_{quality}.geojson"

        if cache_path.exists() and not force_refresh:
            logger.info("Carregando GeoJSON da PB do cache: %s", cache_path)
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)

        url = (
            f"{self.BASE_URL_MALHAS}/estados/{UF_PARAIBA_CODE}"
            f"?formato=application/vnd.geo+json&qualidade={quality}&intrarregiao=municipio"
        )
        logger.info("Baixando malha GeoJSON da PB via IBGE: %s", url)

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "ZikAI-PB/1.0 (TCC Research)",
                "Accept-Encoding": "gzip, deflate",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            raw_data = response.read()
            if response.info().get("Content-Encoding") == "gzip" or raw_data[:2] == b"\x1f\x8b":
                raw_data = gzip.decompress(raw_data)
            geojson_data = json.loads(raw_data.decode("utf-8"))

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, ensure_ascii=False)

        logger.info(
            "GeoJSON dos municípios da PB salvo com sucesso (%d feições)",
            len(geojson_data.get("features", [])),
        )
        return geojson_data
