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
        from_attributes = True


class SerieEpidemiologicaOut(BaseModel):
    municipio_geocode: int = Field(..., description="Código IBGE do município")
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
        from_attributes = True
        validate_by_name = True


class PrevisaoIACreate(BaseModel):
    municipio_geocode: int = Field(..., description="Código IBGE do município")
    doenca: str = Field(..., description="Doença (dengue, chikungunya ou zika)")
    horizonte_semanas: int = Field(..., ge=1, le=12, description="Horizonte de semanas à frente previsto")
    ano_alvo: int = Field(..., description="Ano epidemiológico alvo")
    semana_alvo: int = Field(..., ge=1, le=53, description="Semana epidemiológica alvo")
    casos_previstos: float = Field(..., ge=0.0, description="Quantidade prevista de casos")
    intervalo_inferior: Optional[float] = Field(None, description="Limite inferior do intervalo de confiança")
    intervalo_superior: Optional[float] = Field(None, description="Limite superior do intervalo de confiança")
    nivel_risco_previsto: int = Field(1, ge=1, le=4, description="Nível de risco previsto (1 a 4)")
    probabilidade_surto: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probabilidade estimada de surto")
    modelo_utilizado: str = Field("RandomForestRegressor", description="Nome/versão do modelo utilizado")


class PrevisaoIAOut(BaseModel):
    municipio_geocode: int = Field(..., description="Código IBGE do município")
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
        from_attributes = True


class AlertaCreate(BaseModel):
    municipio_geocode: int = Field(..., description="Código IBGE do município")
    doenca: str = Field(..., description="Arbovirose: dengue, chikungunya ou zika")
    titulo: str = Field(..., description="Título resumido do alerta")
    mensagem: str = Field(..., description="Mensagem descritiva do alerta")
    nivel_gravidade: int = Field(..., ge=1, le=4, description="Nível de gravidade (1=Verde a 4=Vermelho)")


class AlertaUpdateStatus(BaseModel):
    ativo: int = Field(..., ge=0, le=1, description="Status do alerta (1=Ativo, 0=Resolvido)")


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
        from_attributes = True


AlertaOut = AlertaVigilanciaOut
