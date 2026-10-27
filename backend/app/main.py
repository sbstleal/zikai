"""Aplicação principal FastAPI - ZikAI Paraíba.

Ponto de entrada do servidor backend. Registra todas as rotas (endpoints)
e configura middlewares como CORS para comunicação com o frontend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.session import init_db
from .routers import municipios, series, previsoes, alertas, mapa, dashboard

app = FastAPI(
    title="ZikAI Paraíba - API",
    description=(
        "API REST para o Sistema Inteligente de Monitoramento e Previsão "
        "de Arboviroses no Estado da Paraíba. Fornece dados epidemiológicos, "
        "climáticos, geográficos e previsões geradas por modelos de IA."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuração de CORS para permitir chamadas do frontend (React/Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",   # Vite dev server padrão
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rotas agrupadas por domínio
app.include_router(municipios.router, prefix="/api", tags=["Municípios"])
app.include_router(series.router, prefix="/api", tags=["Séries Temporais"])
app.include_router(previsoes.router, prefix="/api", tags=["Previsões IA"])
app.include_router(alertas.router, prefix="/api", tags=["Alertas"])
app.include_router(mapa.router, prefix="/api", tags=["Mapa GeoJSON"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])

@app.on_event("startup")
def on_startup():
    """Inicializa o banco de dados ao iniciar o servidor."""
    init_db()
    # Opcional: popular municípios apenas se a variável de ambiente estiver habilitada (padrão true)
    import os
    populate = os.getenv("POPULATE_MUNICIPIOS", "true").lower() == "true"
    if populate:
        from .db.session import SessionLocal
        from .db import models
        from .db.repository import upsert_municipios
        from pathlib import Path
        import json

        db = SessionLocal()
        try:
            raw_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "pb_municipios_ibge.json"
            enriched_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "pb_municipios_ibge_enriched.json"
            merged_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "pb_municipios_ibge_merged.json"
            file_to_load = merged_path if merged_path.exists() else (enriched_path if enriched_path.exists() else raw_path)

            if file_to_load.exists():
                with open(file_to_load, "r", encoding="utf-8") as f:
                    municipios_data = json.load(f)
                inserted = upsert_municipios(db, municipios_data)
                print(f"🔧 População automática: dados atualizados/inseridos ({len(municipios_data)} municípios processados, arquivo: {file_to_load.name}).")
            else:
                print("⚠️ Arquivo de municípios não encontrado; carregamento automático ignorado.")
        finally:
            db.close()

@app.get("/", tags=["Saúde"])
def health_check():
    """Verificação de saúde da API (health check)."""
    return {
        "status": "ok",
        "projeto": "ZikAI Paraíba",
        "versao": "0.1.0",
    }
