# Harness de teste LOCAL do /oraculo. Espelha o _serve_test.py do /jogar, com diferencas:
#   - NAO forca MODO_MOCK: usa a API real (precisa ANTHROPIC_API_KEY no ambiente) e o
#     banco real (so SELECT, via executar_select_seguro -> seguro).
#   - Auth publico (bypass do BasicAuth SO neste processo de teste).
#   - SelectorEventLoop (Windows + async/psycopg/asyncpg).
#   - Porta 8098.
# Objetivo: servir o app pra abrir http://127.0.0.1:8098/oraculo no navegador.
import asyncio, selectors, uvicorn
import auth
auth._is_public = lambda p: True   # bypass do BasicAuth SO neste processo de teste
loop_factory = lambda: asyncio.SelectorEventLoop(selectors.SelectSelector())
cfg = uvicorn.Config("server:app", host="127.0.0.1", port=8098, log_level="warning")
asyncio.run(uvicorn.Server(cfg).serve(), loop_factory=loop_factory)
