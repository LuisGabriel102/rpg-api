"""
Conexao async com Neon Postgres para a Oficina do Mestre.

Padroes obrigatorios SQLModel + asyncpg + Neon (pgbouncer transaction mode):

- NullPool: o pgbouncer do Neon ja e o pool. Double-pooling causa stale
  connections e ResourceClosedError intermitente.

- statement_cache_size=0: asyncpg cacheia prepared statements internamente
  que quebram com pgbouncer transaction mode (proxy reaproveita conexoes
  backend, prepared statements de uma transacao nao existem na proxima).

- prepared_statement_cache_size=0: SQLAlchemy dialect tem o PROPRIO cache
  separado do asyncpg. Precisa desabilitar tambem ou o problema acima volta.

- prepared_statement_name_func: nomes UNICOS por prepared statement evitam
  colisao se rodar multiplos workers no Railway no futuro. Sem isso, dois
  workers podem tentar criar prepared statement com mesmo nome no mesmo
  backend e um falha silenciosamente.

- command_timeout=30: SEM ISSO, query travada (Neon scaling, hiccup de rede,
  contention no backend) fica esperando para SEMPRE. asyncpg nao tem
  timeout default. 30s e generoso pra queries reais e curto o suficiente
  pra detectar problema antes do user desistir.

- ssl=require: asyncpg NAO aceita sslmode (sintaxe libpq), so ssl.

- expire_on_commit=False: evita lazy-load failure em contexto async apos
  commit. Tambem evita DetachedInstanceError ao acessar atributos depois
  do commit.

Padrao de uso no resto da Oficina:
    async with get_session() as session:
        result = await session.execute(...)

Sempre uma session por operacao. Nunca compartilhar session entre handlers.
asyncpg NAO permite multiplos cursors na mesma session (asyncio.gather
de queries na mesma session = InterfaceError).
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator
from uuid import uuid4

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel.ext.asyncio.session import AsyncSession

load_dotenv()

_raw_url = os.getenv("DATABASE_URL")
if not _raw_url:
    raise RuntimeError(
        "DATABASE_URL nao encontrada. Confirme se o .env existe na raiz do "
        "projeto e contem DATABASE_URL=postgresql://... (formato do backend)."
    )


def _normalizar_para_asyncpg(url: str) -> str:
    """Converte a DATABASE_URL (compartilhada com o backend psycopg3) pro
    formato que SQLAlchemy + asyncpg espera.

    O backend usa  postgresql://...?sslmode=require  (libpq / psycopg3).
    O asyncpg NAO aceita sslmode na URL (usa ssl via connect_args) e exige o
    prefixo do driver. Entao trocamos o prefixo e removemos os query params
    libpq. Se a URL ja vier no formato +asyncpg, usamos como esta.
    """
    if url.startswith("postgresql+asyncpg://"):
        return url
    base = url.split("?", 1)[0]  # remove ?sslmode=... (asyncpg usa connect_args)
    if base.startswith("postgresql://"):
        return base.replace("postgresql://", "postgresql+asyncpg://", 1)
    if base.startswith("postgres://"):
        return base.replace("postgres://", "postgresql+asyncpg://", 1)
    return base


DATABASE_URL = _normalizar_para_asyncpg(_raw_url)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # mude pra True se quiser ver todo SQL gerado no console
    poolclass=NullPool,
    connect_args={
        # SSL obrigatorio pro Neon
        "ssl": "require",

        # Desabilita cache interno do asyncpg (prepared statements)
        "statement_cache_size": 0,

        # Desabilita cache do dialect SQLAlchemy (separado do asyncpg)
        "prepared_statement_cache_size": 0,

        # Nomes unicos de prepared statements (multi-worker safe)
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",

        # Timeout duro por query — sem isso, hangs sao eternos
        "command_timeout": 30,
    },
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """
    Context manager pra abrir uma session async.

    Uso:
        async with get_session() as session:
            result = await session.execute(...)
    """
    async with async_session_factory() as session:
        yield session