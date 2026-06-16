"""Tier 6 — parse_haiku_output blindado (contador de chaves balanceadas)."""

import pytest

from resolver_fatos_alderyn import parse_haiku_output


def test_json_limpo():
    """Caso feliz: objeto puro."""
    assert parse_haiku_output('{"fatos": []}') == {"fatos": []}


def test_cercas_e_paragrafo_com_chave_solta_no_fim():
    """O caso adversario do enunciado: JSON + ``` + paragrafo com '}' solto no fim.
    A heuristica antiga (1o '{' ao ULTIMO '}') pegaria o '}' da prosa e quebraria;
    o contador balanceado fecha no '}' do objeto e ignora o resto."""
    bruto = (
        "```json\n"
        '{ "fatos": [] }\n'
        "```\n\n"
        "A narracao e atmosferica e nao revela fato duravel. "
        "Nenhuma relacao { de lealdade ou posse } persiste depois da cena.}"
    )
    assert parse_haiku_output(bruto) == {"fatos": []}


def test_saida_real_do_haiku():
    """Replica o formato exato que o Haiku devolveu no run real do flip."""
    bruto = (
        "```json\n"
        "{\n"
        '  "fatos": []\n'
        "}\n"
        "```\n\n"
        "A narracao e inteiramente descritiva e atmosferica. "
        "Nenhum fato duravel e estabelecido."
    )
    assert parse_haiku_output(bruto) == {"fatos": []}


def test_chave_dentro_de_string_nao_confunde():
    """object_text com '{' e '}' dentro de string nao desbalanceia a contagem."""
    bruto = '{"fatos": [{"object": "um anel com a inscricao {selo} rachada"}]}  e mais texto }'
    out = parse_haiku_output(bruto)
    assert out["fatos"][0]["object"] == "um anel com a inscricao {selo} rachada"


def test_preambulo_antes_do_objeto():
    """Texto/cercas antes do '{' tambem sao ignorados."""
    assert parse_haiku_output('Aqui esta:\n```json\n{"fatos": [1]}') == {"fatos": [1]}


def test_objeto_aninhado_fecha_no_lugar_certo():
    """Fecha no '}' que zera o contador, nao no primeiro '}'."""
    out = parse_haiku_output('{"a": {"b": 1}, "c": 2} lixo depois }')
    assert out == {"a": {"b": 1}, "c": 2}


def test_sem_objeto_levanta():
    with pytest.raises(ValueError):
        parse_haiku_output("sem nenhuma chave aqui")
    with pytest.raises(ValueError):
        parse_haiku_output("")


def test_objeto_nao_fechado_levanta():
    with pytest.raises(ValueError):
        parse_haiku_output('{"fatos": [  (nunca fecha)')
