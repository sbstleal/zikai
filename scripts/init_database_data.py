"""Script de Carga e Inicialização Completa do Banco de Dados ZikAI Paraíba.

Executa:
1. Ingestão de todos os municípios da Paraíba a partir de data/raw/pb_municipios_ibge.json.
2. Ingestão de séries históricas do InfoDengue dos arquivos locais em data/raw/.
3. Geração de registros de alerta e predição de exemplo para os municípios polos.

Execução:
    python scripts/init_database_data.py
"""

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from backend.app.db.session import SessionLocal, init_db
from backend.app.db.repository import upsert_municipios, load_dataframe_to_registros
from backend.app.db import models
from data_pipeline.infodengue import InfoDengueClient


def popular_municipios(db, raw_dir: Path) -> int:
    """Carrega os 223 municípios da Paraíba no banco."""
    ibge_path = raw_dir / "pb_municipios_ibge.json"
    if not ibge_path.exists():
        print(f"Aviso: Arquivo {ibge_path} não encontrado.")
        return 0

    with open(ibge_path, "r", encoding="utf-8") as f:
        municipios_data = json.load(f)

    # Coordenadas aproximadas para cidades principais se disponíveis na malha
    novos = upsert_municipios(db, municipios_data)
    print(f"Municipios processados: {len(municipios_data)} (novos inseridos: {novos}).")
    return len(municipios_data)


def popular_series_historicas(db, raw_dir: Path) -> int:
    """Carrega séries temporais dos arquivos JSON do InfoDengue em data/raw/."""
    client = InfoDengueClient(raw_data_dir=raw_dir)
    arquivos_infodengue = list(raw_dir.glob("infodengue_*.json"))
    total_registros = 0

    print(f"Encontrados {len(arquivos_infodengue)} arquivos do InfoDengue para ingestao...")
    for arquivo in arquivos_infodengue:
        partes = arquivo.stem.split("_")
        # Padrão: infodengue_{doenca}_{geocode}_{ano_inicio}_{ano_fim}
        if len(partes) >= 3:
            doenca = partes[1]
            try:
                geocode = int(partes[2])
            except ValueError:
                continue

            with open(arquivo, "r", encoding="utf-8") as f:
                raw_json = json.load(f)

            if raw_json:
                df = client._records_to_dataframe(raw_json, disease=doenca, geocode=geocode)
                if not df.empty:
                    inseridos = load_dataframe_to_registros(db, df)
                    total_registros += inseridos

    print(f"Total de registros de séries temporais inseridos/atualizados: {total_registros}")
    return total_registros


def popular_alertas_e_previsoes_base(db):
    """Garante predições e alertas de exemplo para João Pessoa e Campina Grande."""
    polos = [
        {"geocode": 2507507, "nome": "João Pessoa"},
        {"geocode": 2504009, "nome": "Campina Grande"},
    ]

    for polo in polos:
        geo = polo["geocode"]
        # Verifica se já tem previsão
        prev_existente = db.query(models.PrevisaoIA).filter(models.PrevisaoIA.municipio_geocode == geo).first()
        if not prev_existente:
            db.add(
                models.PrevisaoIA(
                    municipio_geocode=geo,
                    doenca="dengue",
                    horizonte_semanas=2,
                    ano_alvo=2024,
                    semana_alvo=12,
                    casos_previstos=28.5,
                    intervalo_inferior=22.0,
                    intervalo_superior=35.0,
                    nivel_risco_previsto=3,
                    probabilidade_surto=0.68,
                    modelo_utilizado="XGBoost-Regressor-PB-v1",
                )
            )

        # Verifica se já tem alerta
        alerta_existente = db.query(models.AlertaVigilancia).filter(models.AlertaVigilancia.municipio_geocode == geo).first()
        if not alerta_existente:
            db.add(
                models.AlertaVigilancia(
                    municipio_geocode=geo,
                    doenca="dengue",
                    titulo=f"Alerta de Risco Alto - {polo['nome']}",
                    mensagem=f"Transmissão sustentada identificada para as próximas semanas em {polo['nome']}.",
                    nivel_gravidade=3,
                    ativo=1,
                )
            )

    db.commit()
    print("Alertas e previsoes de exemplo garantidos.")


def main():
    print("=== Inicializando Banco de Dados ZikAI Paraíba ===")
    init_db()
    db = SessionLocal()
    raw_dir = ROOT / "data" / "raw"

    try:
        popular_municipios(db, raw_dir)
        popular_series_historicas(db, raw_dir)
        popular_alertas_e_previsoes_base(db)
        print("=== Banco de dados populado com sucesso! ===")
    finally:
        db.close()


if __name__ == "__main__":
    main()
