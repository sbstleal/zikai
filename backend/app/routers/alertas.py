"""Rotas para acesso aos alertas de vigilância.

Este módulo fornece endpoints que retornam alertas emitidos para os municípios.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..db.session import get_db
from ..db import models
from ..schemas import AlertaCreate, AlertaOut, AlertaUpdateStatus, AlertaVigilanciaOut

router = APIRouter()

@router.get(
    "/alertas",
    response_model=List[AlertaVigilanciaOut],
)
def listar_alertas(
    ativo: Optional[int] = Query(
        None, description="Filtrar por status 1=ativo, 0= resolvido"
    ),
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
    return alertas


@router.post(
    "/alertas",
    response_model=AlertaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo alerta de vigilância epidemiológica",
)
def criar_alerta(alerta: AlertaCreate, db: Session = Depends(get_db)):
    """Cria um alerta de vigilância epidemiológica associado a um município existente."""
    municipio = db.query(models.Municipio).filter(models.Municipio.geocode == alerta.municipio_geocode).first()
    if not municipio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Município com geocode {alerta.municipio_geocode} não encontrado.",
        )

    novo = models.AlertaVigilancia(
        municipio_geocode=alerta.municipio_geocode,
        doenca=alerta.doenca.lower(),
        titulo=alerta.titulo,
        mensagem=alerta.mensagem,
        nivel_gravidade=alerta.nivel_gravidade,
        ativo=1,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.patch(
    "/alertas/{alerta_id}/status",
    response_model=AlertaOut,
    summary="Atualiza o status de um alerta (resolver ou reativar)",
)
def atualizar_status_alerta(
    alerta_id: int,
    status_update: AlertaUpdateStatus,
    db: Session = Depends(get_db),
):
    """Atualiza o campo `ativo` de um alerta (1 para ativo, 0 para resolvido)."""
    alerta = db.query(models.AlertaVigilancia).filter(models.AlertaVigilancia.id == alerta_id).first()
    if not alerta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alerta com id {alerta_id} não encontrado.",
        )

    alerta.ativo = status_update.ativo
    db.commit()
    db.refresh(alerta)
    return alerta
