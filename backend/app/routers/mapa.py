'''Router para mapas e geojson.

Este é um placeholder mínimo para que a aplicação importe corretamente.
Mais tarde pode ser expandido com endpoints reais.
'''

from fastapi import APIRouter

router = APIRouter()

@router.get("/mapa", tags=["Mapa"])
async def get_mapa() -> dict:
    """Retorna um objeto placeholder representando o mapa.
    
    Returns
    -------
    dict
        Dados de exemplo para o mapa.
    """
    return {"message": "Mapa endpoint placeholder"}
