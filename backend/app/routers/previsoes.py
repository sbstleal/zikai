"""Rotas para acesso às previsões de IA.

Este módulo fornece endpoints que retornam as previsões de casos de arboviroses geradas pelos modelos de IA.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from ..db.session import get_db
from ..db import models

router = APIRouter()

@router.get("/previsoes/{geocode}", response_model=List[Dict[str, Any]])
def obter_previsoes(
    geocode: int,
    doenca: Optional[str] = Query(None, description="Filtrar por doença (dengue, chikungunya, zika)"),
    db: Session = Depends(get_db),
):
    """Retorna previsões de IA para um município.

    - **geocode**: código IBGE do município.
    - **doenca**: opcional, filtra por tipo de doença.
    """
    query = db.query(models.PrevisaoIA).filter(models.PrevisaoIA.municipio_geocode == geocode)
    if doenca:
        query = query.filter(models.PrevisaoIA.doenca == doenca)
    previsoes = query.order_by(models.PrevisaoIA.gerado_em.desc()).all()
    if not previsoes:
        raise HTTPException(status_code=404, detail="Nenhuma previsão encontrada para os parâmetros informados.")
    return [
        {
            "geocode": p.municipio_geocode,
            "doenca": p.doenca,
            "horizonte_semanas": p.horizonte_semanas,
            "ano_alvo": p.ano_alvo,
            "semana_alvo": p.semana_alvo,
            "casos_previstos": p.casos_previstos,
            "intervalo_inferior": p.intervalo_inferior,
            "intervalo_superior": p.intervalo_superior,
            "nivel_risco_previsto": p.nivel_risco_previsto,
            "probabilidade_surto": p.probabilidade_surto,
            "modelo_utilizado": p.modelo_utilizado,
            "gerado_em": p.gerado_em.isoformat(),
        }
        for p in previsoes
    ]
