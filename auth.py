"""
HTTP Basic Auth middleware pra Oficina do Mestre.

Implementacao baseada na pesquisa "HTTP Basic Auth no NiceGUI 2.x":
- BaseHTTPMiddleware do Starlette: WebSocket (scope != http) passa direto,
  o que e exatamente o comportamento desejado pro NiceGUI -- a pagina HTML
  e protegida, o WebSocket so abre depois da pagina carregada (post-auth).
- bcrypt cost factor 12: balanceia seguranca e CPU em containers pequenos.
- Dummy hash com mesmo cost: previne timing-based user enumeration.
- Whitelist de paths: /healthz publico (Railway), /_nicegui* publico (assets
  internos do NiceGUI sem os quais a UI nem renderiza), / publico (root).

Aplicado em main.py com:
    app.add_middleware(BasicAuthMiddleware)

DEVE ser registrado ANTES de qualquer @ui.page e antes de ui.run_with(app).
"""

import base64
import secrets

import bcrypt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

import config

# Dummy hash gerado uma unica vez no startup. Mesmo cost factor que o real.
# Quando username invalido, gastamos CPU verificando contra esse hash em vez
# de retornar imediatamente -- assim o tempo de resposta e identico, sem
# vazar "este usuario existe / nao existe" via timing attack.
_DUMMY_HASH: bytes = bcrypt.hashpw(b"dummy-timing-pad", bcrypt.gensalt(rounds=12))

# Paths que NAO exigem autenticacao
_PUBLIC_PATHS: set[str] = {
    "/",             # root (status JSON do backend)
    "/healthz",      # healthcheck da Oficina
    "/health",       # healthcheck do backend (Railway bate aqui)
    "/health/db",    # healthcheck que testa os dois bancos
    # Conserto 4: /docs, /redoc, /openapi.json SAIRAM da whitelist -> exigem a mesma
    # Basic Auth do resto tambem em dev (antes ficavam abertos; em prod ja eram None).
    "/sistema",      # pagina estatica "O Sistema"
}

_PUBLIC_PREFIXES: tuple[str, ...] = (
    "/_nicegui",  # Assets internos NiceGUI: JS, CSS, fonts, Vue, Quasar, Socket.IO
    "/static/",   # Arquivos estaticos da Oficina
    "/api/v1",    # BACKEND: tem auth Bearer proprio; fora do Basic Auth da Oficina
    "/cache",     # endpoints de cache do backend
)

REALM = "Oficina do Mestre - Sistema Nexus"

# Conserto LOCAL: quando config.AUTH_OFF_JOGAR estiver ligado (flag de ambiente, SO
# local), estas rotas do jogo passam sem Basic Auth -> Gabriel/dev entram sem senha.
# Flag ausente (producao) -> ficam protegidas como o resto. So a pagina do jogo entra
# aqui; /oficina*, /oraculo etc. seguem exigindo auth.
_JOGAR_PATHS: frozenset[str] = frozenset({"/jogar", "/jogar-c"})


def _is_public(path: str) -> bool:
    """Retorna True se o path deve passar sem autenticacao."""
    if path in _PUBLIC_PATHS:
        return True
    if config.AUTH_OFF_JOGAR and path in _JOGAR_PATHS:
        return True
    return path.startswith(_PUBLIC_PREFIXES)


def _verify(username: str, password: str) -> bool:
    """
    Verifica credenciais com protecao contra timing attacks.

    Compara username com secrets.compare_digest (timing-safe pra strings)
    e senha contra o hash bcrypt. Se username invalido, ainda gasta CPU
    verificando contra _DUMMY_HASH pra que o tempo total seja identico.
    """
    user_ok = secrets.compare_digest(
        username.encode("utf-8"),
        config.OFICINA_USER.encode("utf-8"),
    )

    if user_ok:
        pass_ok = bcrypt.checkpw(password.encode("utf-8"), config.OFICINA_PASS_HASH)
    else:
        # Burn CPU verificando dummy pra mascarar timing
        bcrypt.checkpw(password.encode("utf-8"), _DUMMY_HASH)
        pass_ok = False

    return user_ok and pass_ok


def _challenge() -> Response:
    """Resposta 401 que faz o browser exibir o prompt de credenciais."""
    return Response(
        content="Credenciais necessarias",
        status_code=401,
        headers={"WWW-Authenticate": f'Basic realm="{REALM}"'},
    )


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware HTTP que protege todas as rotas exceto a whitelist.

    WebSocket connections nao passam por dispatch() (BaseHTTPMiddleware so
    intercepta scope[type] == http), entao o protocolo Socket.IO do NiceGUI
    funciona normalmente apos a pagina HTML ser autenticada.
    """

    async def dispatch(self, request: Request, call_next):
        # Whitelist de paths publicos
        if _is_public(request.url.path):
            return await call_next(request)

        # Le header Authorization
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            return _challenge()

        # Decodifica base64 do header
        try:
            encoded = auth_header.split(" ", 1)[1]
            decoded = base64.b64decode(encoded).decode("utf-8")
            username, password = decoded.split(":", 1)
        except (ValueError, UnicodeDecodeError):
            return _challenge()

        # Verifica credenciais (timing-safe)
        if not _verify(username, password):
            return _challenge()

        # Auth ok -- segue pro proximo handler
        return await call_next(request)