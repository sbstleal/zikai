"""Testes unitários para o cliente da API do IBGE."""

from pathlib import Path
import pytest
from data_pipeline.ibge import IBGEClient


def test_ibge_fetch_municipalities(tmp_path: Path):
    client = IBGEClient(raw_data_dir=tmp_path)
    municipios = client.fetch_pb_municipalities()

    assert isinstance(municipios, list)
    assert len(municipios) == 223, "A Paraíba possui exatamente 223 municípios"

    # Verificar estrutura do primeiro elemento
    primeiro = municipios[0]
    assert "geocode" in primeiro
    assert "nome" in primeiro
    assert "microrregiao" in primeiro
    assert "mesorregiao" in primeiro
    assert str(primeiro["geocode"]).startswith("25"), "Código IBGE da PB deve iniciar com 25"


def test_ibge_fetch_geojson(tmp_path: Path):
    client = IBGEClient(raw_data_dir=tmp_path)
    geojson = client.fetch_pb_geojson(quality="minima")

    assert isinstance(geojson, dict)
    assert geojson.get("type") == "FeatureCollection"
    assert "features" in geojson
    assert len(geojson["features"]) == 223
