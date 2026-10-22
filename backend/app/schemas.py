"""Schemas Pydantic usados pelos endpoints da API ZikAI Paraíba.

Cada schema representa a estrutura JSON retornada por cada rota.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class MunicipioOut(BaseModel):
    geocode: int = Field(..., description="Código IBGE de 7 dígitos")
    nome: str = Field(..., description="Nome do município")
    microrregiao: Optional[str] = Field(None, description="Microrregião")
    mesorregiao: Optional[str] = Field(None, description="Mesorregião")
    populacao: Optional[int] = Field(None, description="População estimada")
    latitude: Optional[float] = Field(None, description="Latitude geográfica")
    longitude: Optional[float] = Field(None, description="Longitude geográfica")

    class Config:
        orm_mode = True


class SerieEpidemiologicaOut(BaseModel):
    geocode: int = Field(..., alias="geocode", description="Código IBGE do município")
    doenca: str
    data_inicio_se: date
    ano: int
    semana_epidemiologica: int
    casos_notificados: int
    casos_estimados: float
    taxa_reproducao_rt: Optional[float] = None
    probabilidade_rt_maior_1: Optional[float] = None
    nivel_alerta: int
    incidencia_100k: Optional[float] = None
    temperatura_media: Optional[float] = None
    temperatura_minima: Optional[float] = None
    temperatura_maxima: Optional[float] = None
    umidade_media: Optional[float] = None
    umidade_minima: Optional[float] = None
    umidade_maxima: Optional[float] = None

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class PrevisaoIAOut(BaseModel):
    geocode: int = Field(..., description="Código IBGE do município")
    doenca: str
    horizonte_semanas: int
    ano_alvo: int
    semana_alvo: int
    casos_previstos: float
    intervalo_inferior: Optional[float] = None
    intervalo_superior: Optional[float] = None
    nivel_risco_previsto: int
    probabilidade_surto: Optional[float] = None
    modelo_utilizado: str
    gerado_em: datetime

    class Config:
        orm_mode = True


class AlertaVigilanciaOut(BaseModel):
    id: int
    municipio_geocode: int
    doenca: str
    titulo: str
    mensagem: str
    nivel_gravidade: int
    ativo: int
    emitido_em: datetime

    class Config:
        orm_mode = True
