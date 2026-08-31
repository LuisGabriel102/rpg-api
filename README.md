# Nexus — RPG narrado por IA (backend + Oficina)

Nexus é um RPG de mesa jogado contra um narrador de IA: o jogador age, um Claude Opus narra o mundo (com regras de voz e canon travadas em prompt), e o sistema mantém combate, fichas, inventário e a memória de longo prazo do mundo. Tudo roda num único serviço: a API do jogo e o painel de administração ("Oficina do Mestre") no mesmo processo.

## A camada de IA (o coração do projeto)

- **Narrador multi-modelo.** Claude Opus narra todos os turnos. O system prompt é um prefixo **cacheável e byte-idêntico entre chamadas** (prompt caching) — a parte autoral do prompt não muda, só o turno; isso controla latência e custo.
- **Modelos pequenos como guardrail.** Um Claude Haiku **valida cada narração** (responde uma única palavra: ok ou qual regra de voz quebrou); outro Haiku **extrai os fatos duráveis** do turno em JSON estrito, sem narrar nem opinar.
- **Memória de mundo por embeddings.** Fatos canônicos viram vetores de **768 dimensões** gravados no Postgres. Modelo e normalização vivem num módulo único (`narrador/memoria/embedding.py`) — indexação e consulta importam do mesmo lugar, então o vetor gravado e o vetor consultado nunca divergem.
- **Pipeline de imagem multi-provedor.** Geração de arte via **3 provedores** (Flux, Gemini, GPT) em `geradores_imagem/`, com pipeline de aprovação no painel.

## Arquitetura — e por que monolito

Um único processo `uvicorn` (`server.py`) serve as duas metades:

- **Backend** (API do jogo): FastAPI com **11 routers** e **86 endpoints** em `/api/v1/*`, acesso a banco via `psycopg3`.
- **Oficina do Mestre** (painel admin): NiceGUI com **29 páginas** em `/oficina*`, ORM `SQLModel/asyncpg`, **14 tabelas**.

Por que monolito: o NiceGUI mantém estado de UI **em memória, por conexão WebSocket** — múltiplos workers ou réplicas quebram a sessão do painel. Um processo, uma réplica, sem scale-to-zero (está no `railway.toml`). O custo dessa escolha (um deploy para tudo) é menor que o custo de sincronizar estado de UI entre réplicas.

### psycopg3 × asyncpg — por que os dois

O backend usa `psycopg3` (sync, SQL explícito); a Oficina usa `SQLModel/asyncpg` (async, ORM). Os dois coexistem de propósito: cada camada mantém o driver com que nasceu, e a fusão não reescreveu nenhuma das duas. A `DATABASE_URL` é **uma só**, no formato libpq (`postgresql://...?sslmode=require`); `db.py` deriva em runtime a variante `+asyncpg` (troca o prefixo, remove `sslmode`, desliga caches de prepared statement por causa do pgbouncer em transaction mode do Neon).

## Deploy

Empacotado para **Railway** sobre **Neon Postgres**: 1 réplica, sem scale-to-zero, healthcheck em `/health` (tudo no `railway.toml`). Uma réplica só, de propósito: o NiceGUI mantém estado de UI **em memória, por conexão WebSocket** — réplicas múltiplas quebrariam a sessão do painel.

A instância publicada esteve no ar entre 30/06 e 02/07/2026; hoje está desligada por custo — é projeto pessoal.

## Estrutura

```
nexus/
├── server.py          # entrypoint: cola backend + Oficina + ui.run_with
├── app/               # BACKEND (psycopg3): 11 routers, 86 endpoints em /api/v1
├── oficina_app.py     # main da Oficina (sem app próprio, sem ui.run_with)
├── auth.py            # Basic Auth da Oficina (whitelist liberando o backend)
├── db.py              # SQLModel/asyncpg da Oficina (normaliza a DATABASE_URL)
├── models.py          # models SQLModel da Oficina
├── narrador/          # camada de IA: voz, memória, embeddings
├── config/            # config + logging da Oficina
├── pages/             # páginas do ateliê + bestiário
├── geradores_imagem/  # flux / gemini / gpt (ateliê)
├── ui_helpers.py, r2_storage.py, pipeline_geracao.py, ...  # núcleo da Oficina
├── scripts/           # utilitários de manutenção, fora do runtime
├── docs/              # handoffs, calibrações e docs de projeto (assets em docs/assets/)
├── requirements.txt   # união das dependências dos dois
├── railway.toml       # deploy (1 réplica, WebSocket, uvicorn server:app)
└── .env.example       # variáveis unificadas
```

---

## Rodar local

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

Notas de operação (verificação de boot e pontos sensíveis da integração): [`docs/OPERACAO.md`](docs/OPERACAO.md).

---

## Deploy no Railway

- `startCommand`: `uvicorn server:app --host 0.0.0.0 --port $PORT` (já no `railway.toml`).
- Configure as variáveis do `.env.example` no painel do Railway.
- `DATABASE_URL` é **uma só**, compartilhada pelos dois lados.
- Healthcheck: `/health`.

---

## Decisões de arquitetura

| Conflito | Resolução |
|---|---|
| Dois apps FastAPI | App do backend é a base; a Oficina virou router + páginas |
| Dois drivers de banco (psycopg3 / asyncpg) | Coexistem; cada camada usa o seu |
| `DATABASE_URL` em 2 formatos | Uma env var; `db.py` deriva o `+asyncpg` em runtime |
| Dois lifespans | Backend mantém o dele; cleanup da Oficina via `on_shutdown` do NiceGUI |
| Basic Auth bloqueando o backend | Whitelist ampliada: `/api/v1`, `/health`, `/docs` liberados |
| `/` e health duplicados | Um `/` (backend); `/health` e `/healthz` coexistem |
| `OPENROUTER_API_KEY` da Oficina | Mantido (uso interno dela, não o narrador) |
