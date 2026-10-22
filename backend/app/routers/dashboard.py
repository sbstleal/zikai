"""Router para agregação de dados e métricas do Dashboard ZikAI Paraíba.

Fornece indicadores consolidados do estado para visualização em cards e resumos
executivos na interface de monitoramento.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..db.session import get_db
from ..db import models

router = APIRouter()


@router.get("/dashboard/resumo", tags=["Dashboard"])
def obter_resumo_dashboard(db: Session = Depends(get_db)):
    """Retorna métricas consolidadas para os cards do dashboard.

    - **total_municipios**: quantidade de municípios cadastrados.
    - **total_alertas_ativos**: quantidade de alertas de vigilância pendentes.
    - **total_previsoes_ia**: quantidade de predições de IA geradas.
    - **distribuicao_gravidade_alertas**: contagem de alertas agrupada por nível de risco.
    """
    total_municipios = db.query(func.count(models.Municipio.geocode)).scalar() or 0
    total_alertas_ativos = (
        db.query(func.count(models.AlertaVigilancia.id))
        .filter(models.AlertaVigilancia.ativo == 1)
        .scalar()
        or 0
    )
    total_previsoes = db.query(func.count(models.PrevisaoIA.id)).scalar() or 0

    # Agrupamento de alertas por nível de gravidade
    gravidade_query = (
        db.query(
            models.AlertaVigilancia.nivel_gravidade,
            func.count(models.AlertaVigilancia.id),
        )
        .filter(models.AlertaVigilancia.ativo == 1)
        .group_by(models.AlertaVigilancia.nivel_gravidade)
        .all()
    )

    alertas_por_gravidade = {
        f"nivel_{nivel}": count for nivel, count in gravidade_query
    }

    return {
        "total_municipios": total_municipios,
        "total_alertas_ativos": total_alertas_ativos,
        "total_previsoes_ia": total_previsoes,
        "alertas_por_gravidade": alertas_por_gravidade,
    }
