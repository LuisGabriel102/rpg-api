"""
Bloco da campanha do protagonista (Gabriel Varekhor, personagem 8) — Modo Infância + canon.

FONTE: CRONISTA_CAMPANHA_INFANCIA_VAREKHOR_v1.md (raiz). Carregado uma vez e cacheado em
módulo (lru_cache). Entra no contexto do Cronista SO na campanha do protagonista (is_infancia);
quando essa campanha não está ativa, o bloco simplesmente não é montado. O conteúdo NÃO é
reescrito aqui — este módulo só lê o arquivo do Gabriel e o devolve cru.
"""
from functools import lru_cache
from pathlib import Path

_ARQUIVO = Path(__file__).resolve().parent / "CRONISTA_CAMPANHA_INFANCIA_VAREKHOR_v1.md"


@lru_cache(maxsize=1)
def bloco_campanha_infancia() -> str:
    """Devolve o texto do bloco da campanha (cacheado). Lê o .md da raiz na 1a chamada."""
    return _ARQUIVO.read_text(encoding="utf-8").strip()
