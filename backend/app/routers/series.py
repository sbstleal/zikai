"""Rotas para acesso às séries temporais epidemiológicas.

Este módulo expõe o endpoint que retorna as séries históricas de casos e variáveis climáticas por município.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from ..db.session import get_db
from ..db import models
from ..schemas import SerieEpidemiologicaOut

router = APIRouter()

@router.get("/series/{geocode}", response_model=List[SerieEpidemiologicaOut])
def obter_series(
    geocode: int,
    doenca: Optional[str] = Query(None, description="Filtrar por doença (dengue, chikungunya, zika)"),
    data_inicio: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    data_fim: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)"),
    limite: int = Query(100, ge=1, le=1000, description="Quantidade máxima de registros retornados"),
    offset: int = Query(0, ge=0, description="Quantidade de registros para pular (paginação)"),
    db: Session = Depends(get_db),
):
    """Retorna séries temporais para um município com suporte a paginação e filtros.

    - **geocode**: código IBGE do município.
    - **doenca**: opcional, filtra por tipo de doença.
    - **data_inicio** / **data_fim**: intervalo de datas (coluna `data_inicio_se`).
    - **limite**: quantidade máxima de registros por página (padrão 100, máx 1000).
    - **offset**: deslocamento para paginação (padrão 0).
    """
    query = db.query(models.RegistroEpidemiologico).filter(
        models.RegistroEpidemiologico.municipio_geocode == geocode
    )
    if doenca:
        query = query.filter(models.RegistroEpidemiologico.doenca == doenca)
    if data_inicio:
        query = query.filter(models.RegistroEpidemiologico.data_inicio_se >= data_inicio)
    if data_fim:
        query = query.filter(models.RegistroEpidemiologico.data_inicio_se <= data_fim)

    registros = (
        query.order_by(models.RegistroEpidemiologico.data_inicio_se.desc())
        .offset(offset)
        .limit(limite)
        .all()
    )
    if not registros and offset == 0:
        raise HTTPException(status_code=404, detail="Nenhuma série encontrada para os parâmetros informados.")
    return registros
