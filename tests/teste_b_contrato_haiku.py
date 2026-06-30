#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste B (Degrau 2.8) — ENCANAMENTO Cronista<->motor com MODELO REAL (Haiku), 1 turno.

NAO e o Teste A (mecanica no mock, 65 verdes). NAO e banco. E UMA pergunta:
  quando o motor pede pro modelo narrar um inicio de briga, a resposta volta no
  CONTRATO (<estado> com combate:1 + inimigo:nome|tier)?

Roda SOZINHO, sob demanda (chama rede + Haiku, custa centavos):
    python tests/teste_b_contrato_haiku.py

Nao e coletado pelo pytest (nome 'teste_*', nao 'test_*'; e sem funcoes de teste),
entao NUNCA entra na rede dos 65 deterministicos. Nao toca Neon.

USA Haiku (barato), NAO Opus. UMA chamada.

Por que logar a resposta CRUA: se o parse falhar, a crua separa os casos —
  - auth rejeitada (401)         -> chave invalida; encanamento chega na Anthropic
  - resposta veio, sem as tags   -> encanamento OK, Haiku nao seguiu o contrato
  - nem resposta                 -> encanamento/rede quebrados
Sem a crua, um fail e ambiguo.
"""
import os
import sys

# repo root no sys.path (rodando como script solto, fora do pytest)
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

from dotenv import load_dotenv  # noqa: E402

load_dotenv()  # carrega ANTHROPIC_API_KEY (e DATABASE_URL, exigida no import de jogo)

# Reusa o MESMO system prompt e os MESMOS regexes que o motor usa -> contrato fiel.
from cronista_prompt import CRONISTA_SYSTEM_PROMPT  # noqa: E402
import jogo  # noqa: E402  (registra @ui.page, mas nao sobe servidor; o harness tb importa assim)

MODELO_HAIKU = "claude-haiku-4-5-20251001"  # id do proprio projeto (jogo.py:1665)

# A acao MINIMA que torna uma briga a resposta natural: o jogador ataca primeiro.
# [ESTADO] leve so pra espelhar a forma real da ultima mensagem do motor.
FALA_DO_JOGADOR = (
    "[ESTADO]\n"
    "local: viela estreita no Pier Negro\n"
    "personagem: Kael\n"
    "vida: 80/80\n"
    "\n"
    "Tres capangas armados me cercam na viela, laminas para fora, e um quarto bloqueia "
    "a unica saida. Nao da pra fugir nem encerrar com um golpe so: eles vieram pra me "
    "matar. Firmo os pes, saco a adaga e parto pra cima do mais proximo. A briga comeca."
)


def _texto_da_resposta(resp) -> str:
    """Concatena os blocos de texto da resposta da Anthropic."""
    partes = []
    for bloco in resp.content:
        if getattr(bloco, "type", None) == "text":
            partes.append(bloco.text)
    return "".join(partes)


def main() -> int:
    if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        print("[ABORT] ANTHROPIC_API_KEY ausente no ambiente (.env nao carregou?). PAREI.")
        return 2

    from anthropic import Anthropic
    import anthropic as _anthropic

    cliente = Anthropic()  # le ANTHROPIC_API_KEY do ambiente, igual ao _get_aclient()

    print("=== TESTE B: contrato de inicio de combate via Haiku (1 chamada) ===")
    print(f"modelo: {MODELO_HAIKU}")
    print(f"acao do jogador:\n{FALA_DO_JOGADOR}\n")

    # --- A CHAMADA (uma so) ---
    try:
        resp = cliente.messages.create(
            model=MODELO_HAIKU,
            max_tokens=1400,                 # mesmo teto do motor (Fatia truncagem)
            system=CRONISTA_SYSTEM_PROMPT,   # MESMO system prompt do Cronista
            messages=[{"role": "user", "content": FALA_DO_JOGADOR}],
        )
    except _anthropic.AuthenticationError as e:
        print(f"\n[FALHA: AUTH 401] o encanamento CHEGOU na Anthropic, mas a chave foi "
              f"REJEITADA. Nao e falha de contrato nem de modelo: a chave do .env e "
              f"invalida/expirada. Detalhe: {type(e).__name__}: {e}")
        return 2
    except Exception as e:  # noqa: BLE001 - rede/SDK: encanamento nao chegou ao modelo
        print(f"\n[FALHA: ENCANAMENTO] nem resposta voltou (rede/SDK). "
              f"Detalhe: {type(e).__name__}: {e}")
        return 3

    crua = _texto_da_resposta(resp)

    print("----- RESPOSTA CRUA DO HAIKU -----")
    print(crua)
    print("----- FIM DA CRUA -----\n")

    # --- PARSE: exatamente como o motor faz (jogo.py:3217-3255) ---
    _m_est = jogo._RE_ESTADO.search(crua) or jogo._RE_ESTADO_ABERTO.search(crua)
    bloco_estado = _m_est.group(1) if _m_est else None
    combate_on = bool(jogo._RE_COMBATE.search(bloco_estado)) if bloco_estado else False
    inimigos = jogo._RE_INIMIGO.findall(bloco_estado) if bloco_estado else []

    print("----- PARSE (regexes do motor) -----")
    print(f"<estado> encontrado : {_m_est is not None}")
    print(f"bloco <estado>      : {bloco_estado!r}")
    print(f"combate:1 presente  : {combate_on}")
    print(f"inimigos (nome|tier): {inimigos}")
    print("----- FIM DO PARSE -----\n")

    # --- VEREDITO DO CONTRATO (estrutural, NAO a prosa) ---
    tem_estado = _m_est is not None
    tem_inimigo = len(inimigos) >= 1
    contrato_ok = tem_estado and combate_on and tem_inimigo

    print("=== VEREDITO DO CONTRATO ===")
    print(f"  [{'PASS' if tem_estado else 'FAIL'}] bloco <estado> presente")
    print(f"  [{'PASS' if combate_on else 'FAIL'}] combate:1 presente")
    print(f"  [{'PASS' if tem_inimigo else 'FAIL'}] inimigo no formato nome|tier "
          f"({len(inimigos)} encontrado(s))")
    print()
    if contrato_ok:
        print("TESTE B: PASS — o Haiku respondeu no contrato de combate.")
        return 0
    # Falhou o contrato, mas a resposta veio: encanamento OK, MODELO nao seguiu.
    print("TESTE B: FAIL (contrato) — a resposta CHEGOU (encanamento OK), mas o Haiku "
          "NAO emitiu o contrato completo (veja a crua acima). Distingue 'modelo fraco' "
          "de 'encanamento quebrado': aqui o encanamento esta OK.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
