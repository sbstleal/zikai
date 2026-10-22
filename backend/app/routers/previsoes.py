"""Rotas para acesso às previsões de IA.

Este módulo fornece o endpoint que retorna as previsões de casos de arboviroses
geradas pelos modelos de Inteligência Artificial.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..db.session import get_db
from ..db import models
from ..schemas import PrevisaoIAOut

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
