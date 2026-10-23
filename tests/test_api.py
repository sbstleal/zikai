"""Testes automatizados para os endpoints da API ZikAI Paraíba.

Utiliza FastAPI TestClient para validar status code, estrutura dos schemas e
comportamento das rotas principais.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_check():
    """Valida o endpoint raiz / de saúde."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["projeto"] == "ZikAI Paraíba"


def test_listar_municipios():
    """Valida a listagem de municípios."""
    response = client.get("/api/municipios")
    assert response.status_code == 200
    municipios = response.json()
    assert isinstance(municipios, list)
    assert len(municipios) > 0
    # Verifica formato do primeiro município retornado
    primeiro = municipios[0]
    assert "geocode" in primeiro
    assert "nome" in primeiro


def test_listar_alertas():
    """Valida a listagem de alertas da vigilância."""
    response = client.get("/api/alertas")
    assert response.status_code == 200
    alertas = response.json()
    assert isinstance(alertas, list)
    assert len(alertas) > 0
    alerta = alertas[0]
    assert "municipio_geocode" in alerta
    assert "titulo" in alerta
    assert "nivel_gravidade" in alerta


def test_obter_previsoes_existente():
    """Valida o endpoint de previsões de IA para o município com seed (João Pessoa: 2507507)."""
    response = client.get("/api/previsoes/2507507")
    assert response.status_code == 200
    previsoes = response.json()
    assert isinstance(previsoes, list)
    assert len(previsoes) > 0
    prev = previsoes[0]
    assert prev["municipio_geocode"] == 2507507
    assert "casos_previstos" in prev
    assert "modelo_utilizado" in prev


def test_obter_previsoes_inexistente():
    """Valida que município sem previsões cadastradas retorna 404."""
    response = client.get("/api/previsoes/9999999")
    assert response.status_code == 404


def test_obter_series_com_paginacao():
    """Valida se a rota /api/series aplica limite e offset corretamente."""
    response = client.get("/api/series/2507507?limite=10&offset=0")
    assert response.status_code == 200
    series = response.json()
    assert isinstance(series, list)
    assert len(series) <= 10



def test_mapa_geojson():
    """Valida se o endpoint do GeoJSON da malha estadual responde corretamente."""
    response = client.get("/api/mapa/geojson")
    assert response.status_code == 200
    dados = response.json()
    assert dados.get("type") == "FeatureCollection"
    assert "features" in dados
    assert len(dados["features"]) > 0


def test_dashboard_resumo():
    """Valida se o resumo do dashboard consolida métricas da aplicação."""
    response = client.get("/api/dashboard/resumo")
    assert response.status_code == 200
    resumo = response.json()
    assert "total_municipios" in resumo
    assert "total_alertas_ativos" in resumo
    assert "total_previsoes_ia" in resumo
    assert "alertas_por_gravidade" in resumo

