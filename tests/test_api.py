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


def test_criar_e_atualizar_alerta():
    """Valida a criação via POST e atualização de status via PATCH de um alerta."""
    novo_alerta = {
        "municipio_geocode": 2507507,
        "doenca": "chikungunya",
        "titulo": "Alerta de teste automatizado",
        "mensagem": "Detecção de elevação nos casos em João Pessoa.",
        "nivel_gravidade": 3,
    }
    # 1. Criação com sucesso
    res_post = client.post("/api/alertas", json=novo_alerta)
    assert res_post.status_code == 201
    alerta_criado = res_post.json()
    assert alerta_criado["id"] is not None
    assert alerta_criado["municipio_geocode"] == 2507507
    assert alerta_criado["ativo"] == 1
    alerta_id = alerta_criado["id"]

    # 2. Atualização de status (resolver alerta)
    res_patch = client.patch(f"/api/alertas/{alerta_id}/status", json={"ativo": 0})
    assert res_patch.status_code == 200
    assert res_patch.json()["ativo"] == 0

    # 3. Falha ao criar para município inexistente
    novo_alerta["municipio_geocode"] = 9999999
    res_post_invalido = client.post("/api/alertas", json=novo_alerta)
    assert res_post_invalido.status_code == 404


def test_criar_previsao():
    """Valida a criação via POST de uma previsão gerada por IA."""
    nova_prev = {
        "municipio_geocode": 2507507,
        "doenca": "dengue",
        "horizonte_semanas": 4,
        "ano_alvo": 2026,
        "semana_alvo": 45,
        "casos_previstos": 120.5,
        "intervalo_inferior": 90.0,
        "intervalo_superior": 150.0,
        "nivel_risco_previsto": 2,
        "probabilidade_surto": 0.35,
        "modelo_utilizado": "RandomForestRegressor_v1",
    }
    res = client.post("/api/previsoes", json=nova_prev)
    assert res.status_code == 201
    dados = res.json()
    assert dados["municipio_geocode"] == 2507507
    assert dados["casos_previstos"] == 120.5
    assert dados["modelo_utilizado"] == "RandomForestRegressor_v1"

