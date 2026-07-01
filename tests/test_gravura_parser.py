# -*- coding: utf-8 -*-
"""
PROVA A (P3) — parse da linha 'gravura:' dentro do <estado>.

BACK-ONLY: testa _extrair_gravura (parser separado, aditivo) + confirma que a tag NAO
vaza na prosa (o corte de _separar_estado a remove, pois ela vive no <estado>). Sem 'gravura:'
-> None (nada dispara). Determinístico: so import + assert. Mesmo estilo de test_opcoes_parser.py.
"""
from jogo import _extrair_gravura, _separar_estado


def _bloco(corpo_estado, prosa="A cena se move."):
    return f"{prosa}\n\n<estado>\n{corpo_estado}\n</estado>"


def test_gravura_presente_extrai_descricao():
    resp = _bloco("pressao_emocional: 4\ngravura: a velha taverna a luz de velas")
    assert _extrair_gravura(resp) == "a velha taverna a luz de velas"


def test_gravura_ausente_devolve_none():
    # <estado> com outros sinais mas SEM gravura -> None (nao dispara imagem)
    resp = _bloco("pressao_emocional: 4\nopcoes: Entrar | Recuar")
    assert _extrair_gravura(resp) is None


def test_sem_estado_devolve_none():
    assert _extrair_gravura("so prosa, sem bloco nenhum") is None


def test_gravura_nao_vaza_na_prosa():
    # a tag esta DENTRO do <estado> -> a prosa visivel nunca a contem
    resp = _bloco("gravura: um rosto cansado sob o capuz", prosa="Ela te encara em silencio.")
    prosa = _separar_estado(resp, 0)[0]
    assert "gravura:" not in prosa
    assert "rosto cansado" not in prosa
    assert prosa == "Ela te encara em silencio."
    assert _extrair_gravura(resp) == "um rosto cansado sob o capuz"


def test_gravura_estado_truncado_ainda_extrai():
    # <estado> SEM fechamento (resposta cortada no max_tokens) -> fallback tolerante pega
    resp = "Prosa qualquer.\n\n<estado>\npressao_emocional: 3\ngravura: o porto sob neblina"
    assert _extrair_gravura(resp) == "o porto sob neblina"


def test_gravura_vazia_devolve_none():
    # 'gravura:' sem descricao -> None (nao dispara geracao de nada)
    resp = _bloco("gravura:   ")
    assert _extrair_gravura(resp) is None


# ---------------------------------------------------------------------------
# FASE 2/3 (imagem-mae) — _npc_id_gravura: id EXPLICITO da linha ('gravura: 41').
# PURO, sem banco. Texto legado NAO vira id (cai nas outras regras do resolvedor).
# ---------------------------------------------------------------------------
from jogo import _npc_id_gravura


def test_id_puro_extrai():
    assert _npc_id_gravura("41") == 41


def test_id_com_nota_apos_separador_extrai():
    assert _npc_id_gravura("41 — a curandeira debrucada") == 41
    assert _npc_id_gravura("41, Elara") == 41
    assert _npc_id_gravura("41: Elara") == 41


def test_id_dentro_do_estado_ponta_a_ponta():
    # o caminho real: _extrair_gravura pega a linha, _npc_id_gravura le o id
    resp = _bloco("pressao_emocional: 2\ngravura: 41")
    assert _npc_id_gravura(_extrair_gravura(resp)) == 41


def test_texto_legado_nao_vira_id():
    # digitos seguidos de palavra NAO sao id ('41 anos...' e descricao legada)
    assert _npc_id_gravura("41 anos ao relento, o rosto gasto") is None
    assert _npc_id_gravura("um velho de toga dourada") is None


def test_none_e_vazio_devolvem_none():
    assert _npc_id_gravura(None) is None
    assert _npc_id_gravura("") is None
    assert _npc_id_gravura("   ") is None
