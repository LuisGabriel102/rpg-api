"""
Carrega configuracoes da Oficina a partir de variaveis de ambiente (.env).

Centraliza leitura do .env num so lugar pra evitar load_dotenv() espalhado.
Tambem expoe o submodulo logging_setup (Modulo 4.6.3).
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    """Le uma env var obrigatoria. Levanta erro claro se faltar."""
    valor = os.getenv(name)
    if not valor:
        raise RuntimeError(
            f"Variavel de ambiente {name!r} nao definida no .env. "
            f"Adicione a linha {name}=... no arquivo .env."
        )
    return valor


# Banco
DATABASE_URL: str = _required("DATABASE_URL")

# Auth da Oficina (Basic Auth single-user, com hash bcrypt)
OFICINA_USER: str = _required("OFICINA_USER")
OFICINA_PASS_HASH: bytes = _required("OFICINA_PASS_HASH").encode("utf-8")

# Secret pra assinar cookies de sessao do NiceGUI (obrigatorio pelo NiceGUI)
STORAGE_SECRET: str = _required("STORAGE_SECRET")