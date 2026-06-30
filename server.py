"""
Entrypoint do monolito Nexus.

Funde, num unico processo uvicorn:
  - Backend FastAPI (psycopg3): API do jogo em /api/v1/*  (intacto, em app/)
  - Oficina do Mestre (NiceGUI + SQLModel/asyncpg): UI em /oficina*  (em oficina_app.py)

Como as duas camadas convivem:
  - Banco: dois drivers lado a lado. O backend usa o pool psycopg3; a Oficina usa
    SQLAlchemy+asyncpg com NullPool (o pgbouncer do Neon e o pool real). A mesma
    env var DATABASE_URL serve as duas (db.py normaliza o formato pro asyncpg).
  - Auth: o BasicAuthMiddleware da Oficina protege /oficina*; a whitelist (auth.py)
    libera /api/v1*, /health, /docs -> o backend cuida do proprio Bearer.
  - Lifespan: o do backend (abre/fecha o pool psycopg3) continua no app base; o
    cleanup do engine asyncpg da Oficina entra via hook on_shutdown do NiceGUI.

Rodar local:
    uvicorn server:app --host 0.0.0.0 --port 8000

IMPORTANTE: rode com UM worker so. O NiceGUI guarda estado de UI em memoria por
conexao; multiplos workers/replicas quebram a sessao sem sticky sessions.
"""

# ---------------------------------------------------------------------------
# 1. App base = backend. Importar app.main ja cria o FastAPI com os routers
#    /api/v1/*, o middleware (CORS, security headers, rate limit...) e o
#    lifespan que abre/fecha o pool psycopg3.
# ---------------------------------------------------------------------------
from app.main import app

# ---------------------------------------------------------------------------
# 2. Auth da Oficina. Adicionado ANTES de registrar as @ui.page e antes do
#    ui.run_with (exigencia do BaseHTTPMiddleware da Oficina). A whitelist em
#    auth.py ja foi ampliada pra nao bloquear o backend.
# ---------------------------------------------------------------------------
from auth import BasicAuthMiddleware

app.add_middleware(BasicAuthMiddleware)

# ---------------------------------------------------------------------------
# 3. Importar a Oficina. O import executa os decoradores @ui.page e registra
#    todas as paginas /oficina* no NiceGUI. Tambem expoe oficina_router com os
#    endpoints JSON (/api/npcs*, /healthz).
# ---------------------------------------------------------------------------
import oficina_app
import jogo  # noqa: F401 — registra @ui.page("/jogar")
import oraculo  # noqa: F401 — registra @ui.page("/oraculo")

# ---------------------------------------------------------------------------
# 4. Montar os endpoints JSON da Oficina no app.
# ---------------------------------------------------------------------------
app.include_router(oficina_app.oficina_router)

# ---------------------------------------------------------------------------
# 5. Cleanup do engine asyncpg da Oficina no shutdown. Com NullPool e quase
#    no-op, mas fecha conexoes pendentes de forma limpa. Usa o hook do NiceGUI
#    (disparado quando o app encerra), sem mexer no lifespan do backend.
# ---------------------------------------------------------------------------
from nicegui import app as nicegui_app
from db import engine as oficina_engine


async def _fechar_oficina_engine() -> None:
    await oficina_engine.dispose()


nicegui_app.on_shutdown(_fechar_oficina_engine)

# ---------------------------------------------------------------------------
# 5b. Healthcheck que valida OS DOIS bancos -> confirma a fusao: pool psycopg3
#     do backend + engine asyncpg da Oficina (com a DATABASE_URL normalizada).
#     /health continua leve (liveness, o Railway bate nele); /health/db e o
#     teste real de banco, pra rodar manualmente apos subir.
# ---------------------------------------------------------------------------
from fastapi.responses import JSONResponse
from app.database import pool as _backend_pool
from sqlalchemy import text as _sa_text


@app.get("/health/db", include_in_schema=False)
async def health_db():
    estado: dict[str, str] = {}
    try:
        async with _backend_pool.connection() as conn:
            cur = await conn.execute("SELECT 1")
            await cur.fetchone()
        estado["backend_psycopg3"] = "ok"
    except Exception as exc:  # noqa: BLE001
        estado["backend_psycopg3"] = f"erro: {exc}"
    try:
        async with oficina_engine.connect() as conn:
            await conn.execute(_sa_text("SELECT 1"))
        estado["oficina_asyncpg"] = "ok"
    except Exception as exc:  # noqa: BLE001
        estado["oficina_asyncpg"] = f"erro: {exc}"
    tudo_ok = all(v == "ok" for v in estado.values())
    return JSONResponse(
        status_code=200 if tudo_ok else 503,
        content={"status": "ok" if tudo_ok else "degraded", **estado},
    )


# ---------------------------------------------------------------------------
# 5c. Pagina "O Sistema": explicacao estatica do sistema de dados (2d10).
#     HTML standalone em static/sistema.html, servido numa URL limpa /sistema.
#     So le o arquivo e devolve. Liberada sem login pela whitelist do auth.py.
# ---------------------------------------------------------------------------
from pathlib import Path
from fastapi.responses import HTMLResponse

_SISTEMA_HTML = Path(__file__).resolve().parent / "static" / "sistema.html"


@app.get("/sistema", include_in_schema=False)
async def pagina_sistema():
    return HTMLResponse(_SISTEMA_HTML.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 6. Montar o NiceGUI no app do monolito (UMA vez). storage_secret assina os
#    cookies de sessao do NiceGUI.
# ---------------------------------------------------------------------------
from nicegui import ui
import config as oficina_config

ui.run_with(
    app,
    storage_secret=oficina_config.STORAGE_SECRET,
    title="Oficina do Mestre - Sistema Nexus",
    dark=True,
)
