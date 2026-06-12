import asyncio
import selectors
import uvicorn

loop_factory = lambda: asyncio.SelectorEventLoop(selectors.SelectSelector())
config = uvicorn.Config("server:app", host="127.0.0.1", port=8000)
server = uvicorn.Server(config)
asyncio.run(server.serve(), loop_factory=loop_factory)