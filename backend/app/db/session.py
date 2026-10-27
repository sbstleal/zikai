"""Configuração da sessão e conexão com o Banco de Dados SQL (PostgreSQL / SQLite)."""

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Caminho padrão para SQLite local de desenvolvimento / testes
DEFAULT_DB_PATH = Path("data") / "zikai.db"
DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Suporte dinâmico: usa PostgreSQL se DATABASE_URL estiver configurada (ex: Supabase/Neon),
# ou SQLite local para desenvolvimento sem necessidade de internet/servidores.
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.resolve()}")

# Ajuste para compatibilidade do Heroku/Render com PostgreSQL moderno (postgres:// -> postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Alterne para True para debug de queries SQL no console
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Cria todas as tabelas no banco de dados se não existirem."""
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI para injeção de sessões transacionais de banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
