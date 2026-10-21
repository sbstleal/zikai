"""Rotas para acesso aos alertas de vigilância.

Este módulo fornece endpoints que retornam alertas emitidos para os municípios.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from ..db.session import get_db
from ..db import models

router = APIRouter()

@router.get("/alertas", response_model=List[Dict[str, Any]])
def listar_alertas(
    ativo: Optional[int] = Query(None, description="Filtrar por status 1=ativo, 0= resolvido"),
    db: Session = Depends(get_db),
):
    """Retorna alerts de vigilância.

    - **ativo**: opcional, filtra por status (1 ativo, 0 resolvido).
    """
    query = db.query(models.AlertaVigilancia)
    if ativo is not None:
        query = query.filter(models.AlertaVigilancia.ativo == ativo)
    alertas = query.order_by(models.AlertaVigilancia.emitido_em.desc()).all()
    if not alertas:
        raise HTTPException(status_code=404, detail="Nenhum alerta encontrado.")
    return [
        {
            "id": a.id,
            "municipio_geocode": a.municipio_geocode,
            "doenca": a.doenca,
            "titulo": a.titulo,
            "mensagem": a.mensagem,
            "nivel_gravidade": a.nivel_gravidade,
            "ativo": a.ativo,
            "emitido_em": a.emitido_em.isoformat(),
        }
        for a in alertas
    ]
