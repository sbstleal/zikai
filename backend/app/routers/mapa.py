"""Router para mapas e dados GeoJSON da Paraíba.

Fornece a malha geográfica dos municípios da Paraíba em formato GeoJSON,
permitindo a renderização direta em bibliotecas como Leaflet ou MapLibre no frontend.
"""

from pathlib import Path
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

# Caminho para o GeoJSON da malha municipal mínima da Paraíba
GEOJSON_PATH = Path(__file__).resolve().parents[3] / "data" / "raw" / "pb_malha_municipios_minima.geojson"


@router.get("/mapa/geojson", tags=["Mapa GeoJSON"])
def obter_malha_geojson():
    """Retorna o GeoJSON da malha dos municípios da Paraíba.

    Estrutura: FeatureCollection com geometrias e propriedades (codarea / geocode).
    """
    if not GEOJSON_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Arquivo GeoJSON da malha municipal não encontrado no servidor.",
        )

    try:
        with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao carregar dados geográficos: {str(e)}",
        )
