# Nexus — Monolito (backend + Oficina)

Um único processo `uvicorn` servindo as duas coisas:

- **Backend** (API do jogo, `psycopg3`) em **`/api/v1/*`** — intacto, dentro de `app/`.
- **Oficina do Mestre** (painel NiceGUI, `SQLModel/asyncpg`) em **`/oficina*`** — em `oficina_app.py` + módulos na raiz.

O entrypoint é **`server.py`**. Ele importa o app do backend, pluga o auth + as páginas + os endpoints da Oficina, e chama `ui.run_with` uma vez.

---

## Estrutura

```
nexus/
├── server.py          # entrypoint: cola backend + Oficina + ui.run_with
├── app/               # BACKEND intacto (psycopg3, 11 routers /api/v1)
├── oficina_app.py     # main.py da Oficina refatorado (sem app proprio, sem ui.run_with)
├── auth.py            # Basic Auth da Oficina (whitelist liberando o backend)
├── db.py              # SQLModel/asyncpg da Oficina (normaliza a DATABASE_URL)
├── models.py          # models SQLModel da Oficina
├── config/            # config + logging da Oficina
├── pages/             # paginas do atelie + bestiario
├── geradores_imagem/  # flux / gemini / gpt (atelie)
├── ui_helpers.py, r2_storage.py, pipeline_geracao.py, ...  # nucleo da Oficina
├── scripts/           # ~49 scripts one-off (pesquisa/patch/fix) — NAO entram no runtime
├── requirements.txt   # uniao das dependencias dos dois
├── railway.toml       # deploy (1 replica, WebSocket, uvicorn server:app)
└── .env.example       # variaveis unificadas
```

---

## Rodar local (faça ISTO antes de deployar)

O boot real só dá pra validar localmente — eu garanti a sintaxe, não o runtime.

```bash
# 1. ambiente virtual
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. dependencias
pip install -r requirements.txt

# 3. .env (copie e preencha)
cp .env.example .env
#    - DATABASE_URL: a connection string do Neon (formato postgresql://...?sslmode=require)
#    - OFICINA_USER e OFICINA_PASS_HASH: gere o hash com o comando no .env.example
#    - STORAGE_SECRET: qualquer string aleatoria longa
#    - SERVICE_API_KEY: o token do backend

# 4. (teste local) exponha os docs
echo "ENVIRONMENT=dev" >> .env

# 5. smoke de import: se rodar SEM erro, os imports do monolito resolvem
python -c "import server; print('imports OK')"

# 6. sobe o monolito
uvicorn server:app --host 0.0.0.0 --port 8000
```

Depois, no navegador:

- `http://localhost:8000/oficina` → o painel (vai pedir o Basic Auth: OFICINA_USER + senha)
- `http://localhost:8000/docs` → Swagger do backend (se ENVIRONMENT=dev)
- `http://localhost:8000/health` → `{"status":"ok",...}` do backend
- `http://localhost:8000/healthz` → `{"status":"ok"}` da Oficina
- `http://localhost:8000/health/db` → testa OS DOIS bancos (psycopg3 + asyncpg). Os dois `ok` = fusão de banco 100%.

No log de startup, procure a linha **`pool_opened`** — ela confirma que o lifespan do backend rodou dentro do monolito (o risco nº 1). Se ela aparecer, as rotas responderem e o `/oficina` renderizar, o monolito está de pé. **Aí** sobe pro Railway.

---

## O que pode dar errado no boot (pontos de atenção)

Esta é a integração mais sensível do stack (NiceGUI `ui.run_with` em cima de um FastAPI com lifespan/middleware/routers). Se quebrar, é provável que seja num destes pontos:

1. **Ordem de middleware** — o `BasicAuthMiddleware` é adicionado em `server.py` depois dos middlewares do backend. Se o Starlette reclamar de "middleware after app started", o app foi tocado antes da hora (não deve acontecer rodando via `uvicorn server:app`).
2. **`DATABASE_URL`** — tem que estar no formato do backend (`postgresql://...?sslmode=require`). A Oficina deriva o `+asyncpg` sozinha. Se você puser `postgresql+asyncpg://` aqui, o backend (psycopg3) quebra.
3. **Import** — se algum módulo da Oficina puxar um script que eu movi pra `scripts/`, vai dar `ModuleNotFoundError`. Nesse caso, traga o módulo de volta pra raiz. (Mapeei as dependências, mas só o boot real confirma.)
4. **WebSocket** — local funciona direto. No Railway, mantenha **1 réplica** e **sem scale-to-zero** (já está no `railway.toml`).

---

## Deploy no Railway

- `startCommand`: `uvicorn server:app --host 0.0.0.0 --port $PORT` (já no `railway.toml`).
- Configure as variáveis do `.env.example` no painel do Railway.
- `DATABASE_URL` é **uma só**, compartilhada pelos dois lados.
- Healthcheck: `/health`.

---

## Conflitos da fusão (como foram resolvidos)

| Conflito | Resolução |
|---|---|
| Dois apps FastAPI | App do backend é a base; a Oficina virou router + páginas |
| Dois drivers de banco (psycopg3 / asyncpg) | Coexistem; cada camada usa o seu |
| `DATABASE_URL` em 2 formatos | Uma env var; `db.py` deriva o `+asyncpg` em runtime |
| Dois lifespans | Backend mantém o dele; cleanup da Oficina via `on_shutdown` do NiceGUI |
| Basic Auth bloqueando o backend | Whitelist ampliada: `/api/v1`, `/health`, `/docs` liberados |
| `/` e health duplicados | Um `/` (backend); `/health` e `/healthz` coexistem |
| `OPENROUTER_API_KEY` da Oficina | Mantido (uso interno dela, não o narrador) |
