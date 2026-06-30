import os

# LOCAL ONLY: liga o pulo da Basic Auth do /jogar (config.AUTH_OFF_JOGAR). Este runner
# NUNCA roda no Railway (la e `uvicorn server:app`), entao o flag e impossivel de vazar
# pra producao por aqui. setdefault: se ja vier do ambiente, respeita.
os.environ.setdefault("OFICINA_AUTH_OFF", "1")

import asyncio
import selectors
import uvicorn

loop_factory = lambda: asyncio.SelectorEventLoop(selectors.SelectSelector())
config = uvicorn.Config("server:app", host="127.0.0.1", port=8000)
server = uvicorn.Server(config)
asyncio.run(server.serve(), loop_factory=loop_factory)