"""Contador de gasto real da sessao (Tarefa 8). PURO: so calcula custo a partir do
usage do Anthropic e do custo da gravura. Sem estado global, sem I/O, sem tocar o
motor/parser/pipeline. A leitura defensiva (try/except) vive no chamador; aqui as
funcoes ja toleram usage ausente/torto devolvendo 0.0 — a narracao nunca quebra por
causa da contabilidade.

PRECOS Claude Opus 4.8 — por 1M tokens (skill claude-api, cached 2026-06-24):
  input        US$ 5.00
  output       US$ 25.00
  cache write  US$ 6.25   (5m TTL = 1.25x input)
  cache read   US$ 0.50   (0.1x input)
Gravura (fal-ai/flux-lora): US$ 0.035 por imagem GERADA (cache hit nao soma).
Cambio: taxa FIXA aproximada, constante editavel abaixo — NAO chama API de cambio.
"""

# --- precos por 1M tokens (US$) — Claude Opus 4.8, 2026-06-24 ---
USD_IN_POR_MTOK = 5.00
USD_OUT_POR_MTOK = 25.00
USD_CACHE_WRITE_POR_MTOK = 6.25
USD_CACHE_READ_POR_MTOK = 0.50

# --- gravura (fal-ai/flux-lora): custo por imagem nova ---
USD_POR_GRAVURA = 0.035

# --- cambio fixo aproximado (editavel; NAO chama API) ---
BRL_POR_USD = 5.40


def _tok(usage, *nomes) -> int:
    """Le um campo de token do usage do Anthropic (objeto OU dict), tolerante: tenta
    cada nome, devolve int >= 0; qualquer coisa estranha -> 0."""
    for nome in nomes:
        if isinstance(usage, dict):
            v = usage.get(nome)
        else:
            v = getattr(usage, nome, None)
        if v is None:
            continue
        try:
            n = int(v)
        except (TypeError, ValueError):
            continue
        if n >= 0:
            return n
    return 0


def custo_texto_usd(usage) -> float:
    """Custo em US$ de UMA resposta do Cronista, a partir do .usage do final_message
    (ou de um dict acumulado com as mesmas chaves). Defensivo: usage None/torto -> 0.0
    (mock nao tem usage -> 0.0; o turno nunca quebra por causa disto)."""
    if usage is None:
        return 0.0
    inp = _tok(usage, "input_tokens")
    out = _tok(usage, "output_tokens")
    cw = _tok(usage, "cache_creation_input_tokens")
    cr = _tok(usage, "cache_read_input_tokens")
    return (
        inp * USD_IN_POR_MTOK
        + out * USD_OUT_POR_MTOK
        + cw * USD_CACHE_WRITE_POR_MTOK
        + cr * USD_CACHE_READ_POR_MTOK
    ) / 1_000_000.0


def usd_para_brl(usd: float) -> float:
    """Converte US$ -> R$ pela taxa fixa. Defensivo: entrada torta -> 0.0."""
    try:
        return float(usd) * BRL_POR_USD
    except (TypeError, ValueError):
        return 0.0
