"""Seed script – insere registros de exemplo nas tabelas PrevisaoIA e AlertaVigilancia
para que os endpoints /api/previsoes/{geocode} e /api/alertas retornem dados.

Execute:
    python scripts/seed_data.py
"""

import sys
from pathlib import Path

# Garantir que o diretório raiz do projeto está no PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from backend.app.db.session import SessionLocal
from backend.app.db import models


def main() -> None:
    db = SessionLocal()
    try:
        # ---- Previsão de IA -------------------------------------------------
        previsao = models.PrevisaoIA(
            municipio_geocode=2507507,
            doenca="dengue",
            horizonte_semanas=2,
            ano_alvo=2024,
            semana_alvo=10,
            casos_previstos=15.0,
            intervalo_inferior=13.0,
            intervalo_superior=17.0,
            nivel_risco_previsto=2,
            probabilidade_surto=0.45,
            modelo_utilizado="XGBoost-Test",
        )
        db.add(previsao)

        # ---- Alerta de vigilância -------------------------------------------
        alerta = models.AlertaVigilancia(
            municipio_geocode=2507507,
            doenca="dengue",
            titulo="Alerta de aumento de casos",
            mensagem="Atenção ao aumento de casos de dengue nas últimas semanas.",
            nivel_gravidade=3,
            ativo=1,
        )
        db.add(alerta)

        db.commit()
        print("✅ Dados de seed inseridos com sucesso.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
