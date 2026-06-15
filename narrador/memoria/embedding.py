"""
Modulo UNICO de embedding (Alderyn / Caminho B) — a fonte de verdade do modelo.
====================================================================================

TRAVA Nº 1 (inegociavel): o vetor da fala do jogador (query_vec, no fluxo de
turno) e o vetor dos fatos (batch gerar_embeddings) TEM que sair daqui — mesmo
modelo, mesma normalizacao. Indexar com um modelo e consultar com outro (ou sem
normalizar) faz os dois vetores viverem em espacos diferentes: a busca vetorial
vira ruido, SEM dar erro nenhum. Por isso existe um lugar so.

Decisoes travadas pelo banco (nao mude sem mudar a coluna world_facts.embedding):
  - vector(768)            -> o modelo TEM que ser 768-dim.
  - index vector_cosine_ops -> embeddings NORMALIZADOS (L2).

O modelo (~1 GB) carrega LAZY, uma unica vez (singleton), so quando embed_* e
chamado pela primeira vez. Importar este modulo NAO baixa nem carrega nada — assim
o app sobe sem pagar o custo enquanto a memoria nao for usada.

ASYNC: encode() e CPU-bound e sincrono. No FastAPI/NiceGUI, chame embed_texto via
asyncio.to_thread(embed_texto, fala) para nao travar o event loop.
"""
from __future__ import annotations

import threading

# 768-dim, multilingue forte em PT, cosseno, sem pegadinha de prefixo.
# NAO troque por modelo de outra dimensao (ex.: e5-large = 1024) -> quebra vector(768).
MODELO = "paraphrase-multilingual-mpnet-base-v2"
_DIM = 768

_model = None
_lock = threading.Lock()


def _get_model():
    """Carrega o SentenceTransformer uma unica vez (singleton thread-safe)."""
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer

                m = SentenceTransformer(MODELO)
                dim = m.get_sentence_embedding_dimension()
                if dim != _DIM:
                    raise RuntimeError(
                        f"Modelo {MODELO} tem {dim} dimensoes, mas a coluna exige {_DIM}."
                    )
                _model = m
    return _model


def to_pgvector(vec) -> str:
    """lista/array de floats -> '[0.012,-0.034,...]' que o cast ::vector aceita."""
    return "[" + ",".join(f"{float(x):.8f}" for x in vec) + "]"


def embed_texto(texto: str) -> str:
    """Uma frase -> string pgvector '[...]' (768-dim, L2-normalizado)."""
    vec = _get_model().encode(
        texto, normalize_embeddings=True, show_progress_bar=False
    )
    return to_pgvector(vec)


def embed_lote(textos) -> list[str]:
    """Lista de frases -> lista de strings pgvector (usado pelo batch de indexacao)."""
    vetores = _get_model().encode(
        list(textos), normalize_embeddings=True, show_progress_bar=False
    )
    return [to_pgvector(v) for v in vetores]
