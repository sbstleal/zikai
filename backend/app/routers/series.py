"""Rotas para acesso às séries temporais epidemiológicas.

Este módulo expõe endpoint que retornam as séries históricas de casos e variáveis climáticas por município.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import date

from ..db.session import get_db
from ..db import models

router = APIRouter()

@router.get("/series/{geocode}", response_model=List[Dict[str, Any]])
def obter_series(
    geocode: int,
    doenca: Optional[str] = Query(None, description="Filtrar por doença (dengue, chikungunya, zika)"),
    data_inicio: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    data_fim: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Retorna séries temporais para um município.

    - **geocode**: código IBGE do município.
    - **doenca**: opcional, filtra por tipo de doença.
    - **data_inicio**/ **data_fim**: intervalo de datas (coluna `data_inicio_se`).
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

    registros = query.order_by(models.RegistroEpidemiologico.data_inicio_se).all()
    if not registros:
        raise HTTPException(status_code=404, detail="Nenhuma série encontrada para os parâmetros informados.")
    return [
        {
            "geocode": r.municipio_geocode,
            "doenca": r.doenca,
            "data_inicio_se": r.data_inicio_se.isoformat(),
            "ano": r.ano,
            "semana_epidemiologica": r.semana_epidemiologica,
            "casos_notificados": r.casos_notificados,
            "casos_estimados": r.casos_estimados,
            "taxa_reproducao_rt": r.taxa_reproducao_rt,
            "probabilidade_rt_maior_1": r.probabilidade_rt_maior_1,
            "nivel_alerta": r.nivel_alerta,
            "incidencia_100k": r.incidencia_100k,
            "temperatura_media": r.temperatura_media,
            "temperatura_minima": r.temperatura_minima,
            "temperatura_maxima": r.temperatura_maxima,
            "umidade_media": r.umidade_media,
            "umidade_minima": r.umidade_minima,
            "umidade_maxima": r.umidade_maxima,
        }
        for r in registros
    ]
