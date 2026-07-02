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
    # Cura do idle-kill do Neon (incidente 2026-07-02): o autosuspend derruba
    # as conexoes ociosas do pool (min_size fica idle pra sempre — max_idle so
    # recolhe ACIMA do minimo) e o pool as entregava sem checar -> rajada de
    # "SSL connection has been closed unexpectedly" a cada retomada.
    # check: valida no checkout; conexao morta e descartada e outra entregue,
    # transparente pro caller. max_lifetime: recicla por idade (30 min) e
    # reduz a janela de mortas acumuladas.
    check=AsyncConnectionPool.check_connection,
    max_lifetime=1800,
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
