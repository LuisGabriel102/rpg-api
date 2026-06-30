# -*- coding: utf-8 -*-
"""
FATIA A2.2 — CAMINHO A: flag incluir_ultimos_instantes no formatador de contexto.

Prova que a flag corta APENAS a seção "## Os últimos instantes", deixando todos os
outros tiers (dívidas, recap, fatos, boatos) byte-idênticos. Default True = de hoje.

Puro (sem DB/Opus): dita o dict ctx que montar_contexto_narrador devolveria.
"""
from formatar_contexto_alderyn import formatar_contexto_para_prompt

HEADER_UI = "## Os últimos instantes"


def _ctx_completo():
    """ctx ditado com TODOS os 5 tiers preenchidos."""
    return {
        "pact_ledger": "DÍVIDA: 3 (tier 1). PACTOS: nenhum.",
        "recap_anterior": {
            "titulo": "A queda da ponte",
            "resumo": "O grupo perdeu o mapa no rio.",
            "pergunta_em_aberto": "Quem traiu a rota?",
            "continuidade": "Chuva continua.",
            "decisoes": ["poupou o ladrão"],
            "relacoes_mudaram": ["Edda: desconfiada"],
        },
        "turnos_recentes": [
            {"turno": 11, "papel": "jogador", "conteudo": "Pergunto ao velho o preço."},
            {"turno": 12, "papel": "narrador", "conteudo": "O velho mediu-o em silêncio e não respondeu logo."},
        ],
        "fatos_relevantes": [
            {"fato": "A Ordem do Limiar conta os dias."},
            {"fato": "Voranthar fica a leste."},
        ],
        "rumores": [
            {"titulo": "Um morto voltou de Voranthar", "conteudo": "Dizem que voltou andando.",
             "veracidade": "distorcido", "perigo": 4},
        ],
    }


def test_a_flag_true_default_mantem_ultimos_instantes():
    """(a) default True: a seção aparece exatamente como hoje."""
    out = formatar_contexto_para_prompt(_ctx_completo())  # default
    assert HEADER_UI in out
    bloco_ui = (HEADER_UI + "\n"
                "[jogador] Pergunto ao velho o preço.\n"
                "[narrador] O velho mediu-o em silêncio e não respondeu logo.")
    assert bloco_ui in out
    # e os outros tiers presentes
    for h in ("## Compromissos e dívidas", "## O que veio antes",
              "## O que se sabe", "## O que se diz — boatos, nem tudo é verdade"):
        assert h in out


def test_b_flag_false_corta_so_ultimos_instantes():
    """(b) False: some "## Os últimos instantes"; todo o resto fica byte-idêntico."""
    ctx = _ctx_completo()
    on = formatar_contexto_para_prompt(ctx, incluir_ultimos_instantes=True)
    off = formatar_contexto_para_prompt(ctx, incluir_ultimos_instantes=False)

    assert HEADER_UI in on
    assert HEADER_UI not in off
    # a prosa/fala daquela seção também some (só existia ali)
    assert "Pergunto ao velho o preço." not in off
    assert "O velho mediu-o em silêncio" not in off
    # os outros tiers seguem presentes
    for h in ("## Compromissos e dívidas", "## O que veio antes",
              "## O que se sabe", "## O que se diz — boatos, nem tudo é verdade"):
        assert h in off

    # PROVA DURA: off == on com APENAS o bloco "Os últimos instantes" removido
    # (separadores \n\n intactos — nada mais mudou).
    blocos_on = on.split("\n\n")
    blocos_sem_ui = [b for b in blocos_on if not b.startswith(HEADER_UI)]
    assert "\n\n".join(blocos_sem_ui) == off


def test_c_sem_turnos_recentes_flag_indiferente():
    """(c) sem turnos_recentes: True e False produzem o MESMO (não havia seção)."""
    ctx = _ctx_completo()
    ctx["turnos_recentes"] = []
    on = formatar_contexto_para_prompt(ctx, incluir_ultimos_instantes=True)
    off = formatar_contexto_para_prompt(ctx, incluir_ultimos_instantes=False)
    assert on == off
    assert HEADER_UI not in on
    # os outros tiers continuam lá
    assert "## Compromissos e dívidas" in on
    assert "## O que se diz — boatos, nem tudo é verdade" in on
