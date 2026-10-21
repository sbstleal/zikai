"""Rotas para acesso ao GeoJSON do mapa de municípios.

Este módulo fornece o endpoint que entrega o arquivo GeoJSON contendo a malha dos municípios da Paraíba.
"""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/mapa/geojson", response_model=dict)
def get_geojson():
    """Retorna o GeoJSON com a malha dos municípios.

    O arquivo está localizado em ``data/raw/pb_malha_municipios_minima.geojson``
    relativo ao diretório raiz do projeto.
    """
    # Caminho absoluto ao arquivo GeoJSON
    geojson_path = Path(__file__).resolve().parents[3] / "data" / "raw" / "pb_malha_municipios_minima.geojson"
    if not geojson_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo GeoJSON não encontrado.")
    try:
        with geojson_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler o GeoJSON: {e}")
    return JSONResponse(content=data)
