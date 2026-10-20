"""Testes unitários para a camada de Banco de Dados SQL."""

from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import pytest

from backend.app.db.models import Base, Municipio, RegistroEpidemiologico, PrevisaoIA
from backend.app.db.repository import (
    upsert_municipios,
    load_dataframe_to_registros,
    save_previsao,
)


@pytest.fixture
def db_session():
    """Cria banco de dados SQLite em memória para testes isolados."""
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(bind=test_engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def test_upsert_municipios(db_session):
    amostra = [
        {
            "geocode": 2507507,
            "nome": "João Pessoa",
            "microrregiao": "João Pessoa",
            "mesorregiao": "Mata Paraibana",
            "populacao": 830000,
        },
        {
            "geocode": 2504009,
            "nome": "Campina Grande",
            "microrregiao": "Campina Grande",
            "mesorregiao": "Agreste Paraibano",
            "populacao": 415000,
        },
    ]

    count = upsert_municipios(db_session, amostra)
    assert count == 2

    jp = db_session.query(Municipio).filter_by(geocode=2507507).first()
    assert jp is not None
    assert jp.nome == "João Pessoa"
    assert jp.mesorregiao == "Mata Paraibana"


def test_load_dataframe_and_previsao(db_session):
    # Inserir município base
    upsert_municipios(
        db_session,
        [
            {
                "geocode": 2507507,
                "nome": "João Pessoa",
                "microrregiao": "João Pessoa",
                "mesorregiao": "Mata Paraibana",
            }
        ],
    )

    # DataFrame simulado
    df_sample = pd.DataFrame(
        [
            {
                "municipio_id": 2507507,
                "doenca": "dengue",
                "data_inicio_se": "2024-01-07",
                "ano": 2024,
                "semana_epidemiologica": 1,
                "casos_notificados": 15,
                "casos_estimados": 18.5,
                "taxa_reproducao_rt": 1.2,
                "probabilidade_rt_maior_1": 0.8,
                "nivel_alerta": 2,
                "temperatura_media": 28.0,
                "temperatura_minima": 24.0,
                "temperatura_maxima": 32.0,
                "umidade_media": 75.0,
                "umidade_minima": 60.0,
                "umidade_maxima": 88.0,
                "incidencia_100k": 2.1,
            }
        ]
    )

    qtd = load_dataframe_to_registros(db_session, df_sample)
    assert qtd == 1

    reg = db_session.query(RegistroEpidemiologico).first()
    assert reg.casos_notificados == 15
    assert reg.doenca == "dengue"

    # Testar inserção de previsão IA
    prev_data = {
        "municipio_geocode": 2507507,
        "doenca": "dengue",
        "horizonte_semanas": 2,
        "ano_alvo": 2024,
        "semana_alvo": 3,
        "casos_previstos": 22.4,
        "intervalo_inferior": 18.0,
        "intervalo_superior": 26.8,
        "nivel_risco_previsto": 3,
        "probabilidade_surto": 0.72,
        "modelo_utilizado": "XGBoost-Regressor-PB-v1",
    }

    prev = save_previsao(db_session, prev_data)
    assert prev.id is not None
    assert prev.casos_previstos == 22.4
    assert prev.nivel_risco_previsto == 3
