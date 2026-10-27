"""Modelos Relacionais (ORM) do Banco de Dados SQL - ZikAI Paraíba."""

from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .session import Base


def utc_now():
    return datetime.now(timezone.utc)


class Municipio(Base):
    """Tabela que armazena os 223 municípios do Estado da Paraíba."""

    __tablename__ = "municipios"

    geocode = Column(BigInteger, primary_key=True, doc="Código IBGE de 7 dígitos (ex: 2507507)")
    nome = Column(String(100), nullable=False, index=True)
    microrregiao = Column(String(100), nullable=True)
    mesorregiao = Column(String(100), nullable=True)
    populacao = Column(Integer, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    criado_em = Column(DateTime, default=utc_now)

    # Relacionamentos
    registros = relationship(
        "RegistroEpidemiologico", back_populates="municipio", cascade="all, delete-orphan"
    )
    previsoes = relationship(
        "PrevisaoIA", back_populates="municipio", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Municipio(geocode={self.geocode}, nome='{self.nome}', mesorregiao='{self.mesorregiao}')>"


class RegistroEpidemiologico(Base):
    """Tabela de séries temporais semanais de arboviroses e clima por município."""

    __tablename__ = "registros_epidemiologicos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    municipio_geocode = Column(
        BigInteger, ForeignKey("municipios.geocode", ondelete="CASCADE"), nullable=False, index=True
    )
    doenca = Column(String(20), nullable=False, index=True)  # 'dengue', 'chikungunya', 'zika'
    data_inicio_se = Column(Date, nullable=False, index=True)
    ano = Column(Integer, nullable=False, index=True)
    semana_epidemiologica = Column(Integer, nullable=False, index=True)

    # Métricas Epidemiológicas (InfoDengue / SUS)
    casos_notificados = Column(Integer, default=0)
    casos_estimados = Column(Float, default=0.0)
    taxa_reproducao_rt = Column(Float, nullable=True)
    probabilidade_rt_maior_1 = Column(Float, nullable=True)
    nivel_alerta = Column(Integer, default=1)  # 1: Verde, 2: Amarelo, 3: Laranja, 4: Vermelho
    incidencia_100k = Column(Float, nullable=True)

    # Variáveis Meteorológicas Acopladas
    temperatura_media = Column(Float, nullable=True)
    temperatura_minima = Column(Float, nullable=True)
    temperatura_maxima = Column(Float, nullable=True)
    umidade_media = Column(Float, nullable=True)
    umidade_minima = Column(Float, nullable=True)
    umidade_maxima = Column(Float, nullable=True)

    criado_em = Column(DateTime, default=utc_now)

    # Relacionamento
    municipio = relationship("Municipio", back_populates="registros")

    # Restrição de unicidade para evitar duplicação de dados históricos
    __table_args__ = (
        UniqueConstraint(
            "municipio_geocode",
            "doenca",
            "ano",
            "semana_epidemiologica",
            name="uq_municipio_doenca_semana",
        ),
    )

    def __repr__(self):
        return (
            f"<RegistroEpidemiologico(municipio={self.municipio_geocode}, "
            f"doenca='{self.doenca}', SE={self.ano}W{self.semana_epidemiologica}, casos={self.casos_notificados})>"
        )


class PrevisaoIA(Base):
    """Tabela de predições geradas pelos modelos de Inteligência Artificial."""

    __tablename__ = "previsoes_ia"

    id = Column(Integer, primary_key=True, autoincrement=True)
    municipio_geocode = Column(
        BigInteger, ForeignKey("municipios.geocode", ondelete="CASCADE"), nullable=False, index=True
    )
    doenca = Column(String(20), nullable=False, index=True)
    horizonte_semanas = Column(Integer, nullable=False)  # 1 a 4 semanas à frente
    ano_alvo = Column(Integer, nullable=False)
    semana_alvo = Column(Integer, nullable=False)

    # Saídas dos Modelos de IA
    casos_previstos = Column(Float, nullable=False)
    intervalo_inferior = Column(Float, nullable=True)
    intervalo_superior = Column(Float, nullable=True)
    nivel_risco_previsto = Column(Integer, default=1)  # 1 a 4
    probabilidade_surto = Column(Float, nullable=True)  # 0.0 a 1.0

    # Metadados de Auditoria do Modelo
    modelo_utilizado = Column(String(50), nullable=False)  # ex: 'XGBoost-Regressor-PB-v1'
    gerado_em = Column(DateTime, default=utc_now)

    # Relacionamento
    municipio = relationship("Municipio", back_populates="previsoes")

    def __repr__(self):
        return (
            f"<PrevisaoIA(municipio={self.municipio_geocode}, doenca='{self.doenca}', "
            f"alvo={self.ano_alvo}W{self.semana_alvo}, casos={self.casos_previstos:.1f})>"
        )


class AlertaVigilancia(Base):
    """Tabela para registro de notificações de alerta emitidas para a vigilância em saúde."""

    __tablename__ = "alertas_vigilancia"

    id = Column(Integer, primary_key=True, autoincrement=True)
    municipio_geocode = Column(
        BigInteger, ForeignKey("municipios.geocode", ondelete="CASCADE"), nullable=False, index=True
    )
    doenca = Column(String(20), nullable=False)
    titulo = Column(String(150), nullable=False)
    mensagem = Column(String(500), nullable=False)
    nivel_gravidade = Column(Integer, nullable=False)  # 1 (Baixo) a 4 (Crítico)
    ativo = Column(Integer, default=1)  # 1: Ativo, 0: Resolvido
    emitido_em = Column(DateTime, default=utc_now)
