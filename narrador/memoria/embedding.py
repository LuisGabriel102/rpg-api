"""
Modulo UNICO de embedding (Alderyn / Caminho B) — a fonte de verdade do modelo.
====================================================================================

TRAVA Nº 1 (inegociavel): o vetor da fala do jogador (query_vec, no fluxo de
turno) e o vetor dos fatos (batch gerar_embeddings) TEM que sair daqui — mesmo
modelo, mesma normalizacao. Indexar com um modelo e consultar com outro (ou sem
normalizar) faz os dois vetores viverem em espacos diferentes: a busca vetorial
vira ruido, SEM dar erro nenhum. Por isso existe um lugar so.

Decisoes travadas pelo banco (nao mude sem mudar a coluna world_facts.embedding):
  - vector(768)            -> output_dimensionality TEM que ser 768.
  - index vector_cosine_ops -> embeddings NORMALIZADOS (L2).

MOTOR: Gemini API (gemini-embedding-001) via google-genai. Substituiu o mpnet
local (sentence-transformers/torch) — agora nao baixa modelo de ~1 GB nem carrega
nada na memoria; o custo virou uma chamada de rede por texto.

ATENCAO L2: com output_dimensionality < 3072 (nativo do modelo) o Gemini NAO
devolve o vetor normalizado. Por isso aplicamos _l2_normalize aqui SEMPRE — e o
que mantem a TRAVA nº 1 (indexacao e consulta no mesmo espaco unitario, cosseno).

O client carrega LAZY, uma unica vez (singleton thread-safe), so quando embed_* e
chamado pela primeira vez. Importar este modulo NAO cria client nem exige chave.

ASYNC: embed_* faz I/O de rede (sincrono). No FastAPI/NiceGUI, chame via
asyncio.to_thread(embed_texto, fala) para nao travar o event loop.
"""
from __future__ import annotations

import math
import os
import threading

from google import genai
from google.genai import types

# 768-dim travado pela coluna world_facts.embedding -> vector(768).
# NAO troque a dimensao sem migrar a coluna (e reindexar tudo).
MODELO = "gemini-embedding-001"
_DIM = 768

_client = None
_lock = threading.Lock()


def _get_client() -> genai.Client:
    """Retorna o client Gemini singleton (thread-safe, lazy).

    Mesmo padrao de credencial de geradores_imagem/gerador_gemini.py:
    aceita GEMINI_API_KEY ou GOOGLE_API_KEY, passada EXPLICITAMENTE.
    """
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    raise RuntimeError(
                        "GEMINI_API_KEY (ou GOOGLE_API_KEY) nao definida no ambiente. "
                        "Verifique .env — o embedding agora usa a Gemini API."
                    )
                _client = genai.Client(api_key=api_key)
    return _client


def _l2_normalize(vec):
    """Normaliza L2 em Python puro (sem numpy). norm 0 -> retorna como veio."""
    norm = math.sqrt(sum(float(x) * float(x) for x in vec))
    if norm == 0.0:
        return list(vec)
    return [float(x) / norm for x in vec]


def to_pgvector(vec) -> str:
    """lista/array de floats -> '[0.012,-0.034,...]' que o cast ::vector aceita."""
    return "[" + ",".join(f"{float(x):.8f}" for x in vec) + "]"


def _embed_um(texto: str, task: str):
    """Uma frase -> lista de floats L2-normalizada (768-dim). Helper interno."""
    resp = _get_client().models.embed_content(
        model=MODELO,
        contents=texto,
        config=types.EmbedContentConfig(
            task_type=task,
            output_dimensionality=_DIM,
        ),
    )
    valores = resp.embeddings[0].values
    return _l2_normalize(valores)


def embed_texto(texto: str, task: str = "RETRIEVAL_QUERY") -> str:
    """Uma frase -> string pgvector '[...]' (768-dim, L2-normalizado).

    task default RETRIEVAL_QUERY: este e o vetor da consulta (fala do jogador).
    """
    return to_pgvector(_embed_um(texto, task))


def embed_lote(textos, task: str = "RETRIEVAL_DOCUMENT") -> list[str]:
    """Lista de frases -> lista de strings pgvector (usado pelo batch de indexacao).

    task default RETRIEVAL_DOCUMENT: estes sao os vetores dos fatos indexados.

    Itera 1 a 1 de proposito: gemini-embedding-001 aceita um texto por request, o
    volume e pequeno (~centenas) e a velocidade nao importa — em troca cada item
    tem mapeamento direto e uma falha nao derruba o lote inteiro de forma confusa.
    """
    return [to_pgvector(_embed_um(t, task)) for t in textos]
