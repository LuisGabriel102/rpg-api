# -*- coding: utf-8 -*-
"""
FASE 1 — Testes de CARACTERIZACAO da camada pura do motor de combate.

Caracterizacao = fotografa o comportamento ATUAL e trava. Nao prova "certo";
qualquer mudanca futura que altere este comportamento acende alarme.

Determinístico: so import + assert. Zero browser, zero Opus, zero DB.
NAO edita jogo.py nem resolucao_2d10.py.

Fonte da verdade (lido linha a linha):
  - app/resolucao_2d10.py:12  classificar_faixa
  - jogo.py:518/519/521       TIER_HP / CD_TIER / TIER_DANO
  - jogo.py:610               _FAIXA_CRONISTA
  - jogo.py:514..531/607      regexes _RE_*
  - jogo.py:538               _resumo_bando
  - jogo.py:619               _separar_estado
  - jogo.py:561               _atualizar_momentum
"""
import pytest

from app.resolucao_2d10 import classificar_faixa
from jogo import (
    TIER_HP, CD_TIER, TIER_DANO, _FAIXA_CRONISTA,
    _RE_COMBATE, _RE_INIMIGO, _RE_ALVO, _RE_ACAO, _RE_RECUO,
    _RE_FERIDA, _RE_TESTE, _RE_ESTADO, _RE_ESTADO_ABERTO,
    _resumo_bando, _separar_estado, _atualizar_momentum,
)


# ===========================================================================
# 1) classificar_faixa(d1, d2, mod, cd) -> str
#    Logica real (resolucao_2d10.py:12-28), nesta ordem:
#      naturais primeiro: (10,10)->sucesso_critico ; (1,1)->falha_critica
#      senao margem = (d1+d2+mod) - cd
#        margem <= -5         -> falha_critica
#        -4 <= margem <= -1   -> falha
#         0 <= margem <= +2   -> sucesso_parcial
#        +3 <= margem <= +6   -> sucesso
#        +7 ou mais           -> sucesso_critico
# ===========================================================================
@pytest.mark.parametrize("d1,d2,mod,cd,esperado", [
    # --- as 5 faixas por margem (sem naturais) ---
    (2, 2, 0, 12, "falha_critica"),     # soma 4, margem -8
    (5, 5, 0, 12, "falha"),             # soma 10, margem -2
    (6, 6, 0, 12, "sucesso_parcial"),   # soma 12, margem 0
    (8, 7, 0, 12, "sucesso"),           # soma 15, margem +3
    (10, 9, 0, 12, "sucesso_critico"),  # soma 19, margem +7

    # --- naturais (regra especial: vencem a margem) ---
    (10, 10, 0, 20, "sucesso_critico"), # margem 0 daria parcial; natural max forca crit
    (1, 1, 5, 10, "falha_critica"),     # margem -3 daria falha; natural min forca falha_crit

    # --- limiares: virar de faixa com +/-1 no total ---
    (3, 4, 0, 12, "falha_critica"),     # soma 7,  margem -5 -> ainda falha_critica
    (4, 4, 0, 12, "falha"),             # soma 8,  margem -4 -> vira falha
    (5, 6, 0, 12, "falha"),             # soma 11, margem -1 -> ultimo falha
    (6, 6, 0, 12, "sucesso_parcial"),   # soma 12, margem  0 -> primeiro parcial
    (7, 7, 0, 12, "sucesso_parcial"),   # soma 14, margem +2 -> ultimo parcial
    (8, 7, 0, 12, "sucesso"),           # soma 15, margem +3 -> primeiro sucesso
    (9, 9, 0, 12, "sucesso"),           # soma 18, margem +6 -> ultimo sucesso
    (10, 9, 0, 12, "sucesso_critico"),  # soma 19, margem +7 -> primeiro crit
])
def test_classificar_faixa(d1, d2, mod, cd, esperado):
    assert classificar_faixa(d1, d2, mod, cd) == esperado


def test_classificar_faixa_mod_desloca_a_margem():
    # mesmo dado, CD igual: o modificador move a faixa (caracteriza o uso do mod)
    assert classificar_faixa(5, 5, 0, 12) == "falha"            # margem -2
    assert classificar_faixa(5, 5, +3, 12) == "sucesso_parcial" # margem +1
    assert classificar_faixa(5, 5, -4, 12) == "falha_critica"   # margem -6


# ===========================================================================
# 2) Constantes (trava de canon)
# ===========================================================================
def test_const_tier_hp():
    assert TIER_HP == {"comum": 6, "bravo": 12, "elite": 20}

def test_const_cd_tier():
    assert CD_TIER == {"comum": 10, "bravo": 13, "elite": 16}

def test_const_tier_dano():
    assert TIER_DANO == {"comum": 1.0, "bravo": 1.5, "elite": 2.0}

def test_const_faixa_cronista():
    assert _FAIXA_CRONISTA == {
        "sucesso_critico": "sucesso crítico",
        "sucesso": "sucesso",
        "sucesso_parcial": "sucesso parcial",
        "falha": "falha",
        "falha_critica": "falha crítica",
    }


# ===========================================================================
# 3) Regexes — 1 caso que CASA (confirma grupos) + 1 negativo, formato <estado> real
# ===========================================================================
def test_re_combate():
    assert _RE_COMBATE.search("combate: 1").group(1) == "1"
    assert _RE_COMBATE.search("combate: ativo").group(1) == "ativo"
    assert _RE_COMBATE.search("combate: inativo") is None

def test_re_inimigo():
    m = _RE_INIMIGO.search("inimigo: capanga do beco | comum")
    assert m.group(1) == "capanga do beco"
    assert m.group(2) == "comum"
    assert _RE_INIMIGO.search("inimigo: capanga do beco") is None  # falta | tier

def test_re_alvo():
    m = _RE_ALVO.search("inimigo_alvo: capanga da direita")
    assert m.group(1).strip() == "capanga da direita"
    assert _RE_ALVO.search("inimigo: capanga | comum") is None     # nao e inimigo_alvo

def test_re_acao():
    assert _RE_ACAO.search("acao: fugir").group(1) == "fugir"
    assert _RE_ACAO.search("acao: defesa").group(1) == "defesa"
    assert _RE_ACAO.search("acao: pular") is None                   # fora da whitelist

def test_re_recuo():
    m = _RE_RECUO.search("inimigo_recuou: capanga do beco")
    assert m.group(1) == "capanga do beco"
    assert _RE_RECUO.search("inimigo: capanga | comum") is None

def test_re_ferida():
    m = _RE_FERIDA.search("ferida: corte fundo no ombro")
    assert m.group(1) == "corte fundo no ombro"
    assert _RE_FERIDA.search("postura: agressiva") is None

def test_re_teste():
    m = _RE_TESTE.search("teste_pedido: aparar o golpe | destreza | cd 13")
    assert m.group(1) == "aparar o golpe"
    assert m.group(2) == "destreza"
    assert m.group(3) == "13"
    assert _RE_TESTE.search("teste_pedido: aparar o golpe") is None  # falta | atrib | cd

def test_re_estado():
    m = _RE_ESTADO.search("prosa aqui\n<estado>\ncombate: 1\n</estado>")
    assert m.group(1) == "\ncombate: 1\n"
    assert _RE_ESTADO.search("nenhuma tag de estado aqui") is None

def test_re_estado_aberto():
    # fallback tolerante: <estado> sem fechamento (resposta cortada no max_tokens)
    m = _RE_ESTADO_ABERTO.search("prosa\n<estado>\ncombate: 1\nacao: ataque")
    assert m.group(1) == "\ncombate: 1\nacao: ataque"
    assert _RE_ESTADO_ABERTO.search("sem tag alguma") is None


# ===========================================================================
# 4) _resumo_bando(inimigos) -> str | None
#    ratio = hp/hp_max : >0.5 inteiro ; >0.25 ferido ; senao cambaleando
#    postura != neutra vira sufixo " (postura)". Vazio -> None. Nunca expoe numero.
# ===========================================================================
def _inim(nome, hp, hp_max=6, postura="neutra"):
    return {"nome": nome, "hp": hp, "hp_max": hp_max, "postura": postura}

def test_resumo_bando_vazio_e_none():
    assert _resumo_bando([]) is None
    assert _resumo_bando(None) is None

def test_resumo_bando_um_inimigo_inteiro():
    assert _resumo_bando([_inim("capanga", 6, 6)]) == "[bando: capanga inteiro]"

def test_resumo_bando_condicoes_por_ratio():
    assert _resumo_bando([_inim("a", 4, 6)]) == "[bando: a inteiro]"        # 0.667 > 0.5
    assert _resumo_bando([_inim("b", 3, 6)]) == "[bando: b ferido]"        # 0.5 (nao > 0.5)
    assert _resumo_bando([_inim("c", 2, 6)]) == "[bando: c ferido]"        # 0.333
    assert _resumo_bando([_inim("d", 1, 6)]) == "[bando: d cambaleando]"   # 0.166

def test_resumo_bando_dois_e_tres():
    r2 = _resumo_bando([_inim("um", 6, 6), _inim("dois", 2, 6)])
    assert r2 == "[bando: um inteiro, dois ferido]"
    r3 = _resumo_bando([_inim("um", 6, 6), _inim("dois", 3, 6), _inim("tres", 1, 6)])
    assert r3 == "[bando: um inteiro, dois ferido, tres cambaleando]"

def test_resumo_bando_postura_nao_neutra_aparece():
    assert _resumo_bando([_inim("x", 6, 6, "agressiva")]) == "[bando: x inteiro (agressiva)]"
    # neutra NAO aparece (terso)
    assert "(neutra)" not in _resumo_bando([_inim("x", 6, 6, "neutra")])

def test_resumo_bando_nunca_expoe_numero():
    r = _resumo_bando([_inim("um", 6, 6), _inim("dois", 2, 6), _inim("tres", 1, 6)])
    assert not any(ch.isdigit() for ch in r)


# ===========================================================================
# 5) _separar_estado(resposta, pressao_anterior) -> (prosa, nova_pressao, atmosfera, teste, opcoes)
# ===========================================================================
def test_separar_estado_completo():
    resp = (
        "A lâmina desce no escuro.\n\n"
        "<estado>\n"
        "pressao_emocional: 7\n"
        "atmosfera: sangue\n"
        "teste_pedido: aparar o golpe | destreza | cd 13\n"
        "</estado>"
    )
    prosa, nova, atm, teste, _op = _separar_estado(resp, pressao_anterior=3)
    assert prosa == "A lâmina desce no escuro."          # bloco <estado> fora da tela
    assert nova == 7
    assert atm == "sangue"
    assert teste == {"intencao": "aparar o golpe", "atributo": "destreza", "cd": 13}

def test_separar_estado_sem_bloco():
    prosa, nova, atm, teste, _op = _separar_estado("Só prosa, sem estado.", pressao_anterior=5)
    assert prosa == "Só prosa, sem estado."
    assert nova == 5          # mantem a pressao anterior
    assert atm is None
    assert teste is None

def test_separar_estado_sem_teste():
    resp = "Prosa.\n<estado>\npressao_emocional: 2\n</estado>"
    prosa, nova, atm, teste, _op = _separar_estado(resp, pressao_anterior=9)
    assert prosa == "Prosa."
    assert nova == 2
    assert atm is None
    assert teste is None

def test_separar_estado_clamp_pressao():
    _, nova_alta, _, _, _ = _separar_estado("p\n<estado>\npressao_emocional: 99\n</estado>", 0)
    assert nova_alta == 10    # clamp teto 10
    _, nova_baixa, _, _, _ = _separar_estado("p\n<estado>\npressao_emocional: 0\n</estado>", 5)
    assert nova_baixa == 0

def test_separar_estado_atmosfera_fora_da_whitelist_ignorada():
    _, _, atm, _, _ = _separar_estado("p\n<estado>\natmosfera: neon\n</estado>", 0)
    assert atm is None        # 'neon' nao esta na whitelist -> None


# ===========================================================================
# 6) _atualizar_momentum(vigor_atual, vigor_maximo, inimigo) -> dict | None
#    momentum = ratio_jog - ratio_inim
#      > 0.15 pressionando ; < -0.15 recuando ; senao equilibrado
#    limiar = (ratio_inim <= 0.25). Sem inimigo -> None.
# ===========================================================================
def test_momentum_sem_inimigo_none():
    assert _atualizar_momentum(18, 18, None) is None

def test_momentum_pressionando_e_limiar_ligado():
    m = _atualizar_momentum(18, 18, {"hp": 1, "hp_max": 6})   # jog 1.0 - inim 0.166 = 0.833
    assert m == {"estado": "pressionando", "limiar": True}

def test_momentum_recuando_sem_limiar():
    m = _atualizar_momentum(2, 18, {"hp": 6, "hp_max": 6})    # jog 0.111 - inim 1.0 = -0.888
    assert m == {"estado": "recuando", "limiar": False}

def test_momentum_equilibrado():
    m = _atualizar_momentum(9, 18, {"hp": 3, "hp_max": 6})    # 0.5 - 0.5 = 0.0
    assert m == {"estado": "equilibrado", "limiar": False}

def test_momentum_limiar_exato_no_corte():
    # ratio_inim == 0.25 -> limiar True (<=). jog 0.25 -> momentum 0 -> equilibrado
    m = _atualizar_momentum(0.25, 1.0, {"hp": 0.25, "hp_max": 1.0})
    assert m == {"estado": "equilibrado", "limiar": True}

def test_momentum_corte_perto_de_0_15():
    # Corte REAL do codigo: momentum > 0.15 -> pressionando (jogo.py:571).
    # NOTA (caracterizacao): 0.15 exato NAO e representavel em float; logo o corte
    # estrito ">0.15" nao e observavel no ponto exato. Fotografamos valores
    # claramente de cada lado + o caso-fantasma do float.
    assert _atualizar_momentum(0.60, 1.0, {"hp": 0.5, "hp_max": 1.0})["estado"] == "equilibrado"   # ~0.10
    assert _atualizar_momentum(0.70, 1.0, {"hp": 0.5, "hp_max": 1.0})["estado"] == "pressionando"  # ~0.20
    # (0.65 - 0.5) = 0.15000000000000002 > 0.15 -> pressionando (comportamento real, nao "equilibrado")
    assert _atualizar_momentum(0.65, 1.0, {"hp": 0.5, "hp_max": 1.0})["estado"] == "pressionando"
