# -*- coding: utf-8 -*-
"""
Parser do sinal de BOTOES DE ACAO: linha `opcoes: A | B | C` dentro do <estado>.

BACK-ONLY: testa _separar_estado (o parser + o retorno). Nao toca UI/JS/prompt.
Shape do retorno hoje: (prosa, nova_pressao, atmosfera, teste, opcoes) -- opcoes e o
5o valor: list[str] (1..6 itens) quando presente, None quando ausente/vazio.

Determinístico: so import + assert. Mesmo estilo de test_motor_combate_puro.py (secao 5).
"""
from jogo import _separar_estado


def _opcoes(resp):
    """Atalho: o 5o valor (opcoes) de _separar_estado."""
    return _separar_estado(resp, 0)[4]


def _prosa(resp):
    """Atalho: o 1o valor (prosa visivel)."""
    return _separar_estado(resp, 0)[0]


def _bloco(corpo_estado, prosa="A cena se move."):
    return f"{prosa}\n\n<estado>\n{corpo_estado}\n</estado>"


# ===========================================================================
# PASSO 4 — casos minimos
# ===========================================================================
def test_1_tres_opcoes():
    assert _opcoes(_bloco("opcoes: A | B | C")) == ["A", "B", "C"]


def test_2_seis_opcoes_passa_inteiro():
    seis = "opcoes: a | b | c | d | e | f"
    assert _opcoes(_bloco(seis)) == ["a", "b", "c", "d", "e", "f"]


def test_3_sete_opcoes_clamp_seis():
    sete = "opcoes: 1 | 2 | 3 | 4 | 5 | 6 | 7"
    out = _opcoes(_bloco(sete))
    assert out == ["1", "2", "3", "4", "5", "6"]
    assert len(out) == 6


def test_4_opcoes_vazio_vira_none():
    # 'opcoes:' sem nada util depois -> None, sem crash
    assert _opcoes(_bloco("opcoes:")) is None
    assert _opcoes(_bloco("opcoes:    ")) is None
    assert _opcoes(_bloco("opcoes: |  | ")) is None   # so separadores/espacos


def test_5_acento_preservado():
    out = _opcoes(_bloco("opcoes: Voltar à aldeia | Acampar | Investigar a runa"))
    assert out == ["Voltar à aldeia", "Acampar", "Investigar a runa"]
    assert "à" in out[0]


def test_6_ausencia_total_nao_quebra_outros_sinais():
    # <estado> com pressao/atmosfera/teste mas SEM opcoes -> opcoes None, resto intacto
    resp = _bloco(
        "pressao_emocional: 7\n"
        "atmosfera: sangue\n"
        "teste_pedido: aparar o golpe | destreza | cd 13"
    )
    prosa, nova, atm, teste, opcoes = _separar_estado(resp, pressao_anterior=3)
    assert opcoes is None
    assert nova == 7
    assert atm == "sangue"
    assert teste == {"intencao": "aparar o golpe", "atributo": "destreza", "cd": 13}


def test_7_prosa_visivel_nao_contem_opcoes():
    resp = _bloco("opcoes: Lutar | Fugir", prosa="O bandido ergue a faca.")
    prosa = _prosa(resp)
    assert "opcoes:" not in prosa
    assert "Lutar" not in prosa and "Fugir" not in prosa   # o bloco inteiro saiu
    assert prosa == "O bandido ergue a faca."


# ===========================================================================
# AUDITORIA DESTRUTIVA — tentativas de quebrar o parser
# ===========================================================================
def test_aud_pipe_no_meio_do_texto_divide():
    # LIMITACAO conhecida (igual teste:/inimigo:): '|' E o separador -> um '|' no texto
    # da opcao a parte em duas. Documentado; o Cronista usa '|' so como separador.
    assert _opcoes(_bloco("opcoes: pegar a espada | ou a adaga | fugir")) == \
        ["pegar a espada", "ou a adaga", "fugir"]


def test_aud_espacos_estranhos_em_volta_da_chave():
    # espacos antes da chave, em volta do ':' e dos itens -> tudo normalizado
    assert _opcoes(_bloco("   opcoes   :    A   |   B   ")) == ["A", "B"]


def test_aud_opcao_so_com_espacos_e_descartada():
    assert _opcoes(_bloco("opcoes: A |     | B")) == ["A", "B"]


def test_aud_linha_opcoes_duplicada_vence_a_primeira():
    # .search pega a 1a ocorrencia (mesmo comportamento de teste:/corrupcao:)
    resp = _bloco("opcoes: primeira | dela\nopcoes: segunda | ignorada")
    assert _opcoes(resp) == ["primeira", "dela"]


def test_aud_opcao_muito_longa_preservada():
    # NAO ha clamp de comprimento (so de quantidade). O texto longo passa inteiro;
    # truncar visualmente e problema do front, nao do parser.
    longa = "x" * 5000
    out = _opcoes(_bloco(f"opcoes: {longa} | curta"))
    assert out == [longa, "curta"]
    assert len(out[0]) == 5000


def test_aud_convive_com_teste_e_corrupcao():
    # opcoes parseado de forma INDEPENDENTE; teste: tambem sai certo; a linha corrupcao:
    # (parseada na camada de combate, nao aqui) nao atrapalha o parse de opcoes.
    resp = _bloco(
        "corrupcao: 2 hemomantic\n"
        "teste_pedido: forcar a porta | forca | cd 12\n"
        "opcoes: Arrombar | Procurar a chave | Desistir"
    )
    prosa, nova, atm, teste, opcoes = _separar_estado(resp, pressao_anterior=0)
    assert opcoes == ["Arrombar", "Procurar a chave", "Desistir"]
    assert teste == {"intencao": "forcar a porta", "atributo": "forca", "cd": 12}
    assert "opcoes:" not in prosa and "corrupcao:" not in prosa
