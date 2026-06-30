# -*- coding: utf-8 -*-
"""
PROVA (/jogar/log) — log de diagnostico CRU da sessao por turno.

Sem id 8, sem gastar: alimenta o buffer com turnos SINTETICOS e checa a renderizacao.
Provamos:
  - buffer registra por turno; /jogar/log mostra mais recente EM CIMA, com
    estado_cru/parseado/gravura/custo.
  - estado_cru = bloco <estado> LITERAL (com tags), antes do corte da prosa; "(sem <estado>)"
    quando ausente; tolera <estado> truncado (sem fechamento).
  - DEFENSIVO: append de registro torto NAO levanta; registro que estoura no render vira
    "(registro ilegivel)" sem derrubar o resto.
  - cap por sessao descarta os mais antigos, numeracao de turno estavel.
  - /jogar/log espelha a auth do /jogar (protegida em prod, aberta so com AUTH_OFF_JOGAR).
"""
import auth
import config
import jogo


def _reset(monkeypatch):
    monkeypatch.setattr(jogo, "_LOG_POR_SESSAO", {})
    monkeypatch.setattr(jogo, "_LOG_SEQ", {})


# ------------------------------------------------------------- estado_cru

def test_estado_cru_extrai_bloco_literal_com_tags():
    resp = ("Uma vela tremia na mesa.\n\n"
            "<estado>\npressao_emocional: 2\ngravura: um velho de toga\n</estado>")
    cru = jogo._estado_cru(resp)
    assert cru.startswith("<estado>") and cru.endswith("</estado>")
    assert "pressao_emocional: 2" in cru
    assert "gravura: um velho de toga" in cru


def test_estado_cru_ausente():
    assert jogo._estado_cru("So prosa, sem bloco nenhum.") == "(sem <estado>)"
    assert jogo._estado_cru("") == "(sem <estado>)"
    assert jogo._estado_cru(None) == "(sem <estado>)"


def test_estado_cru_truncado_sem_fechamento():
    # resposta cortada no max_tokens: <estado> aberto, sem </estado>
    resp = "prosa\n<estado>\npressao_emocional: 5"
    cru = jogo._estado_cru(resp)
    assert cru.startswith("<estado>")
    assert "pressao_emocional: 5" in cru


# ------------------------------------------------------------- buffer + render

def test_buffer_registra_e_renderiza_mais_recente_em_cima(monkeypatch):
    _reset(monkeypatch)
    sid = "sess-3"
    # turno 1: com estado + teste + opcoes, sem gravura
    jogo._log_append(sid, {
        "ts": "10:00:00", "acao_jogador": "abro a porta",
        "estado_cru": "<estado>\npressao_emocional: 1\n</estado>",
        "pressao": 1, "teste": {"intencao": "forcar", "atributo": "Corpo", "cd": 12},
        "opcoes": ["empurrar", "espiar"], "gravura_desc": None,
        "gravura_resultado": "(nao pediu)", "custo_turno": 0.0123, "avisos": [],
    })
    # turno 2: com gravura nova
    jogo._log_append(sid, {
        "ts": "10:01:30", "acao_jogador": "encaro o velho",
        "estado_cru": "<estado>\ngravura: um velho de toga\n</estado>",
        "pressao": 2, "teste": None, "opcoes": None,
        "gravura_desc": "um velho de toga dourada",
        "gravura_resultado": "gerada nova (US$0.035)", "custo_turno": 0.0473, "avisos": [],
    })

    txt = jogo._render_log_texto(sid)

    # mais recente (turno 2) aparece ANTES do turno 1
    assert txt.index("TURNO 2") < txt.index("TURNO 1")
    # cabecalho com numero + timestamp
    assert "===== TURNO 2 — 10:01:30 =====" in txt
    assert "===== TURNO 1 — 10:00:00 =====" in txt
    # acao do jogador
    assert "acao: encaro o velho" in txt
    assert "acao: abro a porta" in txt
    # estado cru literal
    assert "<estado>\ngravura: um velho de toga\n</estado>" in txt
    # parseado: pressao/teste/opcoes/gravura
    assert "pressao=1" in txt and "pressao=2" in txt
    assert "intencao=forcar" in txt and "cd=12" in txt
    assert "opcoes=[empurrar | espiar]" in txt
    assert "gravura=um velho de toga dourada" in txt
    # gravura_resultado + custo
    assert "gravura_resultado: gerada nova (US$0.035)" in txt
    assert "custo_turno: US$ 0.0473" in txt
    assert "custo_turno: US$ 0.0123" in txt


def test_turno_sem_estado_sem_gravura(monkeypatch):
    _reset(monkeypatch)
    sid = "sess-x"
    jogo._log_append(sid, {
        "ts": "11:00:00", "acao_jogador": "observo",
        "estado_cru": "(sem <estado>)", "pressao": 0, "teste": None, "opcoes": None,
        "gravura_desc": None, "gravura_resultado": "(nao pediu)",
        "custo_turno": None, "avisos": ["usage ausente"],
    })
    txt = jogo._render_log_texto(sid)
    assert "estado_cru:\n(sem <estado>)" in txt
    assert "teste=(nao pediu)" in txt
    assert "opcoes=[(nenhuma)]" in txt
    assert "gravura=(nao pediu)" in txt
    assert "custo_turno: n/d" in txt   # custo None -> n/d
    assert "avisos: usage ausente" in txt


def test_sessao_vazia():
    assert "sem turnos registrados" in jogo._render_log_texto("sessao-inexistente")


# ------------------------------------------------------------- defensivo

def test_log_append_registro_torto_nao_levanta(monkeypatch):
    _reset(monkeypatch)
    # registro que NAO e dict: _log_append tenta registro["n"]=... e falha -> engole
    jogo._log_append("s", "isto nao e um dict")   # nao deve levantar
    # buffer da sessao continua vazio/inalterado (o append falho nao contaminou)
    assert jogo._render_log_texto("s") == "(sem turnos registrados nesta sessao ainda)"


def test_render_registro_que_estoura_nao_derruba_o_resto(monkeypatch):
    _reset(monkeypatch)
    sid = "sess-def"

    class _Explode:
        def get(self, *a, **k):
            raise RuntimeError("registro podre")

    # injeta direto no buffer: um bom, um que estoura, um bom
    jogo._LOG_POR_SESSAO[sid] = [
        {"n": 1, "ts": "1", "acao_jogador": "ok1", "estado_cru": "(sem <estado>)"},
        _Explode(),
        {"n": 3, "ts": "3", "acao_jogador": "ok3", "estado_cru": "(sem <estado>)"},
    ]
    txt = jogo._render_log_texto(sid)   # NAO pode levantar
    assert "(registro ilegivel)" in txt   # o podre virou marcador
    assert "ok1" in txt and "ok3" in txt  # os bons sobreviveram


def test_cap_descarta_antigos_numeracao_estavel(monkeypatch):
    _reset(monkeypatch)
    sid = "sess-cap"
    total = jogo._LOG_MAX_TURNOS + 5
    for i in range(total):
        jogo._log_append(sid, {"ts": "t", "acao_jogador": f"a{i}",
                               "estado_cru": "(sem <estado>)"})
    buf = jogo._LOG_POR_SESSAO[sid]
    assert len(buf) == jogo._LOG_MAX_TURNOS          # capou
    # numeracao monotonica e estavel: ultimo n == total (nao reiniciou no cap)
    assert buf[-1]["n"] == total
    assert buf[0]["n"] == total - jogo._LOG_MAX_TURNOS + 1


# ------------------------------------------------------------- pagina HTML

def test_pagina_html_tem_textarea_e_copiar(monkeypatch):
    _reset(monkeypatch)
    html_out = jogo._pagina_log_html("TURNO 1 conteudo <estado>x</estado>", personagem=3)
    assert "<textarea" in html_out
    assert "copiar tudo" in html_out
    assert "navigator.clipboard" in html_out
    # conteudo escapado dentro do textarea (sem <estado> cru virando tag)
    assert "&lt;estado&gt;x&lt;/estado&gt;" in html_out
    # link de voltar carrega o personagem
    assert "/jogar?personagem=3" in html_out


# ------------------------------------------------------------- auth (espelha /jogar)

def test_jogar_log_protegida_como_jogar(monkeypatch):
    # AUTH_OFF desligado (= producao): /jogar/log NAO e publico, igual /jogar
    monkeypatch.setattr(config, "AUTH_OFF_JOGAR", False, raising=False)
    assert auth._is_public("/jogar/log") is False
    assert auth._is_public("/jogar") is False
    # AUTH_OFF ligado (= local dev): abre /jogar/log junto com /jogar
    monkeypatch.setattr(config, "AUTH_OFF_JOGAR", True, raising=False)
    assert auth._is_public("/jogar/log") is True
    assert auth._is_public("/jogar") is True
