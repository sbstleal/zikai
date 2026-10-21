"""Rotas para acesso aos municípios.

Este módulo define endpoints que retornam a lista de municípios cadastrados no banco de dados.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..db.session import get_db
from ..db import models

router = APIRouter()

@router.get("/municipios", response_model=List[Dict[str, Any]])
def listar_municipios(db: Session = Depends(get_db)):
    """Retorna todos os municípios armazenados.

    Cada município é representado como um dicionário contendo os campos principais.
    """
    municipios = db.query(models.Municipio).all()
    if not municipios:
        raise HTTPException(status_code=404, detail="Nenhum município encontrado.")
    return [
        {
            "geocode": m.geocode,
            "nome": m.nome,
            "microrregiao": m.microrregiao,
            "mesorregiao": m.mesorregiao,
            "populacao": m.populacao,
            "latitude": m.latitude,
            "longitude": m.longitude,
        }
        for m in municipios
    ]
