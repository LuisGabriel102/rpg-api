# Notas de operação

## Verificação de boot

No log de startup, a linha **`pool_opened`** confirma que o lifespan do backend rodou dentro do monolito. Checklist de "está de pé": `pool_opened` no log, rotas `/api/v1` respondendo, `/oficina` renderizando e `/health/db` com os dois bancos `ok`.

## Pontos sensíveis da integração

A parte mais delicada do stack é o NiceGUI (`ui.run_with`) montado sobre um FastAPI com lifespan, middleware e routers próprios:

1. **Ordem de middleware** — o `BasicAuthMiddleware` é adicionado em `server.py` depois dos middlewares do backend. Se o Starlette reclamar de "middleware after app started", o app foi tocado antes da hora (não acontece rodando via `uvicorn server:app`).
2. **`DATABASE_URL`** — precisa estar no formato do backend (`postgresql://...?sslmode=require`). A Oficina deriva o `+asyncpg` sozinha (`db.py`). Com `postgresql+asyncpg://` na env, o backend (psycopg3) quebra.
3. **WebSocket** — local funciona direto. Em produção, manter **1 réplica** e **sem scale-to-zero** (`railway.toml`): o NiceGUI guarda estado de UI em memória, por conexão.
