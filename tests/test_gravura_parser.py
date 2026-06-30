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
