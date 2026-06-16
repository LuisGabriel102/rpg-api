from psycopg_pool import AsyncConnectionPool
from app.config import settings


async def _configure(conn):
    """Aplica statement_timeout por sessao (compativel com o pooler do Neon)."""
    await conn.execute("SET statement_timeout = 45000")


pool = AsyncConnectionPool(
    conninfo=settings.database_url,
    min_size=settings.db_pool_min,
    max_size=settings.db_pool_max,
    max_idle=settings.db_pool_max_idle,
    open=False,
    configure=_configure,
    kwargs={
        "autocommit": True,
        "prepare_threshold": 5,
    },
)


async def get_db():
    """Dependency FastAPI: pega conexao do pool, devolve apos uso."""
    async with pool.connection() as conn:
        yield conn
