"""Rotas para acesso aos municípios.

Este módulo fornece o endpoint que lista todos os municípios cadastrados.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ..db.session import get_db
from sqlalchemy.orm import Session
from ..db import models
from ..schemas import MunicipioOut

router = APIRouter()

@router.get("/municipios", response_model=List[MunicipioOut])
def listar_municipios(db: Session = Depends(get_db)):
    """Retorna todos os municípios armazenados.
    
    O retorno já está compatível com o schema ``MunicipioOut``.
    """
    municipios = db.query(models.Municipio).all()
    if not municipios:
        raise HTTPException(status_code=404, detail="Nenhum município encontrado.")
    return municipios
