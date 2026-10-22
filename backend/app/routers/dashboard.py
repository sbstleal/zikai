'''Router para dashboard.

Placeholder mínimo para que a aplicação importe corretamente.
Será expandido futuramente com rotas reais.
'''

from fastapi import APIRouter

router = APIRouter()

@router.get("/dashboard", tags=["Dashboard"])
async def get_dashboard() -> dict:
    """Retorna dados de exemplo para o dashboard.
    
    Returns
    -------
    dict
        Dados fictícios do dashboard.
    """
    return {"message": "Dashboard endpoint placeholder"}
