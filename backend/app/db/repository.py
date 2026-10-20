"""Camada de Acesso a Dados (Repositório) para manipulação de registros SQL."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AlertaVigilancia, Municipio, PrevisaoIA, RegistroEpidemiologico

logger = logging.getLogger(__name__)


def upsert_municipios(db: Session, municipios: List[Dict[str, Any]]) -> int:
    """Insere ou atualiza o catálogo de municípios da Paraíba."""
    count = 0
    for item in municipios:
        geocode = int(item["geocode"])
        stmt = select(Municipio).where(Municipio.geocode == geocode)
        existente = db.execute(stmt).scalar_one_or_none()

        if existente:
            existente.nome = item.get("nome", existente.nome)
            existente.microrregiao = item.get("microrregiao", existente.microrregiao)
            existente.mesorregiao = item.get("mesorregiao", existente.mesorregiao)
            if "populacao" in item and item["populacao"]:
                existente.populacao = int(item["populacao"])
        else:
            novo = Municipio(
                geocode=geocode,
                nome=item["nome"],
                microrregiao=item.get("microrregiao"),
                mesorregiao=item.get("mesorregiao"),
                populacao=int(item["populacao"]) if item.get("populacao") else None,
            )
            db.add(novo)
            count += 1

    db.commit()
    logger.info("Municípios processados no banco: %d novos inseridos.", count)
    return count


def load_dataframe_to_registros(db: Session, df: pd.DataFrame) -> int:
    """Carrega dados limpos do InfoDengue (DataFrame) para a tabela de registros SQL."""
    if df.empty:
        return 0

    inserted_or_updated = 0

    for _, row in df.iterrows():
        geocode = int(row["municipio_id"])
        doenca = str(row["doenca"]).lower()
        ano = int(row["ano"])
        semana = int(row["semana_epidemiologica"])

        # Verificar se registro já existe
        stmt = select(RegistroEpidemiologico).where(
            RegistroEpidemiologico.municipio_geocode == geocode,
            RegistroEpidemiologico.doenca == doenca,
            RegistroEpidemiologico.ano == ano,
            RegistroEpidemiologico.semana_epidemiologica == semana,
        )
        registro = db.execute(stmt).scalar_one_or_none()

        data_se = (
            row["data_inicio_se"].date()
            if hasattr(row["data_inicio_se"], "date")
            else pd.to_datetime(row["data_inicio_se"]).date()
        )

        def sanitize_float(val):
            return float(val) if pd.notna(val) else None

        def sanitize_int(val, default=0):
            return int(val) if pd.notna(val) else default

        if registro:
            # Atualizar dados existentes
            registro.casos_notificados = sanitize_int(row.get("casos_notificados"))
            registro.casos_estimados = sanitize_float(row.get("casos_estimados"))
            registro.taxa_reproducao_rt = sanitize_float(row.get("taxa_reproducao_rt"))
            registro.probabilidade_rt_maior_1 = sanitize_float(row.get("probabilidade_rt_maior_1"))
            registro.nivel_alerta = sanitize_int(row.get("nivel_alerta"), default=1)
            registro.temperatura_media = sanitize_float(row.get("temperatura_media"))
            registro.temperatura_minima = sanitize_float(row.get("temperatura_minima"))
            registro.temperatura_maxima = sanitize_float(row.get("temperatura_maxima"))
            registro.umidade_media = sanitize_float(row.get("umidade_media"))
            registro.umidade_minima = sanitize_float(row.get("umidade_minima"))
            registro.umidade_maxima = sanitize_float(row.get("umidade_maxima"))
            registro.incidencia_100k = sanitize_float(row.get("incidencia_100k"))
        else:
            novo = RegistroEpidemiologico(
                municipio_geocode=geocode,
                doenca=doenca,
                data_inicio_se=data_se,
                ano=ano,
                semana_epidemiologica=semana,
                casos_notificados=sanitize_int(row.get("casos_notificados")),
                casos_estimados=sanitize_float(row.get("casos_estimados")),
                taxa_reproducao_rt=sanitize_float(row.get("taxa_reproducao_rt")),
                probabilidade_rt_maior_1=sanitize_float(row.get("probabilidade_rt_maior_1")),
                nivel_alerta=sanitize_int(row.get("nivel_alerta"), default=1),
                temperatura_media=sanitize_float(row.get("temperatura_media")),
                temperatura_minima=sanitize_float(row.get("temperatura_minima")),
                temperatura_maxima=sanitize_float(row.get("temperatura_maxima")),
                umidade_media=sanitize_float(row.get("umidade_media")),
                umidade_minima=sanitize_float(row.get("umidade_minima")),
                umidade_maxima=sanitize_float(row.get("umidade_maxima")),
                incidencia_100k=sanitize_float(row.get("incidencia_100k")),
            )
            db.add(novo)

        inserted_or_updated += 1

    db.commit()
    logger.info("Registros epidemiológicos gravados no banco SQL: %d", inserted_or_updated)
    return inserted_or_updated


def save_previsao(db: Session, previsao_data: Dict[str, Any]) -> PrevisaoIA:
    """Salva a previsão gerada pelo modelo de Machine Learning no banco SQL."""
    nova = PrevisaoIA(
        municipio_geocode=int(previsao_data["municipio_geocode"]),
        doenca=previsao_data["doenca"].lower(),
        horizonte_semanas=int(previsao_data["horizonte_semanas"]),
        ano_alvo=int(previsao_data["ano_alvo"]),
        semana_alvo=int(previsao_data["semana_alvo"]),
        casos_previstos=float(previsao_data["casos_previstos"]),
        intervalo_inferior=previsao_data.get("intervalo_inferior"),
        intervalo_superior=previsao_data.get("intervalo_superior"),
        nivel_risco_previsto=int(previsao_data.get("nivel_risco_previsto", 1)),
        probabilidade_surto=previsao_data.get("probabilidade_surto"),
        modelo_utilizado=str(previsao_data["modelo_utilizado"]),
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova
