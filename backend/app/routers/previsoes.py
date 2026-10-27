"""Rotas para acesso às previsões de IA.

Este módulo fornece o endpoint que retorna as previsões de casos de arboviroses
geradas pelos modelos de Inteligência Artificial.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..db.session import get_db
from ..db import models
from ..schemas import PrevisaoIACreate, PrevisaoIAOut

router = APIRouter()

@router.get(
    "/previsoes/{geocode}",
    response_model=List[PrevisaoIAOut],
)
def obter_previsoes(
    geocode: int,
    doenca: Optional[str] = Query(
        None, description="Filtrar por doença (dengue, chikungunya, zika)"
    ),
    db: Session = Depends(get_db),
):
    """Retorna previsões de IA para um município.

    - **geocode**: código IBGE do município.
    - **doenca**: opcional, filtra por tipo de doença.
    """
    query = db.query(models.PrevisaoIA).filter(
        models.PrevisaoIA.municipio_geocode == geocode
    )
    if doenca:
        query = query.filter(models.PrevisaoIA.doenca == doenca)

    previsoes = query.order_by(models.PrevisaoIA.gerado_em.desc()).all()
    if not previsoes:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma previsão encontrada para os parâmetros informados.",
        )
    return previsoes


@router.post(
    "/previsoes",
    response_model=PrevisaoIAOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registra uma nova previsão de IA para um município",
)
def criar_previsao(previsao: PrevisaoIACreate, db: Session = Depends(get_db)):
    """Salva no banco uma previsão gerada pelos modelos de Machine Learning."""
    municipio = db.query(models.Municipio).filter(models.Municipio.geocode == previsao.municipio_geocode).first()
    if not municipio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Município com geocode {previsao.municipio_geocode} não encontrado.",
        )

    nova = models.PrevisaoIA(
        municipio_geocode=previsao.municipio_geocode,
        doenca=previsao.doenca.lower(),
        horizonte_semanas=previsao.horizonte_semanas,
        ano_alvo=previsao.ano_alvo,
        semana_alvo=previsao.semana_alvo,
        casos_previstos=previsao.casos_previstos,
        intervalo_inferior=previsao.intervalo_inferior,
        intervalo_superior=previsao.intervalo_superior,
        nivel_risco_previsto=previsao.nivel_risco_previsto,
        probabilidade_surto=previsao.probabilidade_surto,
        modelo_utilizado=previsao.modelo_utilizado,
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova
