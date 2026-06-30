#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CHECK 5 — auth do OPUS (o ultimo desconhecido antes do Gabriel jogar).

O Teste B provou auth via HAIKU (200). Aqui: UMA chamada trivial a claude-opus-4-8
(o modelo real do Cronista), sem narrar, sem contrato — so confirmar HTTP 200 + Opus
responde. Centavos. Se 401/403 -> BLOCKER pra jogar.

    python tests/verif_opus_auth.py
"""
import os
import sys

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

MODELO_OPUS = "claude-opus-4-8"  # o modelo_atual real do Cronista (jogo.py:2672)


def main() -> int:
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("[ABORT] ANTHROPIC_API_KEY ausente. PAREI.")
        return 2
    from anthropic import Anthropic
    import anthropic as _anthropic

    cliente = Anthropic()
    print(f"=== CHECK 5: auth do Opus ({MODELO_OPUS}) — 1 chamada trivial ===")
    try:
        resp = cliente.messages.create(
            model=MODELO_OPUS,
            max_tokens=10,
            messages=[{"role": "user", "content": "responda apenas: ok"}],
        )
    except _anthropic.AuthenticationError as e:
        print(f"[BLOCKER: 401/403] Opus NAO autenticou: {type(e).__name__}: {e}")
        print("PARE: a chave nao serve pro Opus. Achar agora e melhor que no meio da 1a sessao.")
        return 2
    except Exception as e:  # noqa: BLE001
        print(f"[FALHA: rede/SDK] nem resposta voltou: {type(e).__name__}: {e}")
        return 3

    texto = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    print(f"[PASS] HTTP 200 — Opus autenticou e respondeu.")
    print(f"  modelo retornado : {getattr(resp, 'model', '?')}")
    print(f"  texto            : {texto!r}")
    print(f"  tokens           : in={resp.usage.input_tokens} out={resp.usage.output_tokens}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
