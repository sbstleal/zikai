"""Rotas para acesso ao dashboard resumido.

Este módulo fornece um endpoint de exemplo que pode ser expandido
para agregar dados de diferentes fontes (municipios, séries, previsões,
alertas, etc.). Por enquanto retorna um resumo estático.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/dashboard/summary", tags=["Dashboard"])
def resumo_dashboard():
    """Retorna um resumo estático para demonstração do dashboard.

    Em produção este endpoint poderia agregar estatísticas como:
    - número total de municípios
    - casos recentes por doença
    - alerts ativos
    - previsões de risco
    """
    return {
        "status": "ok",
        "mensagem": "Resumo do dashboard ainda em desenvolvimento.",
        "dados": {
            "municipios": 223,
            "alerts_ativos": 0,
            "previsoes_disponiveis": 0,
        },
    }
