# -*- coding: utf-8 -*-
"""
FATIA 2 — Andaime do harness: encadeia N turnos NARRADOS chamando a
executar_turno_narrado da Fatia 1 em loop, com estado persistindo entre turnos.

NAO toca jogo.py. NAO chama Opus (MODO_MOCK + _cronista_mock ditado). NAO grava no
banco (helpers *_safe stubados; sem combate -> _resumo_bando(()) devolve None, zero DB).
Deterministico, isolado. Convencao async do repo: def sincrono + asyncio.run via _run.

Prova: (a) historico cresce 2 msgs/turno; (b) a pressao encadeia (antes[N+1]==depois[N]);
(c) transcript tem 1 entrada por acao; (d) cada entrada tem prosa e campos preenchidos.
"""
import asyncio

import jogo


def _run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# [1] EstadoSessao — container persistente de UMA sessao ao longo de N turnos.
#     executar_turno_narrado MUTA o EstadoTurno in-place (historico cresce,
#     pressao_atual encadeia, resultado_pendente atualiza), entao EstadoSessao e
#     um ALIAS FINO: segura UM EstadoTurno vivo e o reusa entre turnos.
#     (NAO mexe no EstadoTurno de jogo.py.)
# ---------------------------------------------------------------------------
class EstadoSessao:
    def __init__(self, sessao_atual, modelo_atual, pressao_inicial=0):
        # EstadoTurno(historico, pressao_atual, sessao_atual, modelo_atual, resultado_pendente)
        self.turno = jogo.EstadoTurno([], pressao_inicial, sessao_atual, modelo_atual, None)

    def para_turno(self):
        """Deriva o EstadoTurno a passar a funcao: o MESMO objeto (mutado in-place)."""
        return self.turno

    @property
    def pressao(self):
        return self.turno.pressao_atual

    @property
    def historico_len(self):
        return len(self.turno.historico)


# ---------------------------------------------------------------------------
# [2] Roteiro — falas do jogador em ordem. SEM gatilhos de combate (Fatia futura).
#     Cada item: (fala, prosa_ditada, pressao_ditada, atmosfera_ditada|None).
# ---------------------------------------------------------------------------
ROTEIRO = [
    ("Doran cruza o salao em silencio.",        "O salao estava vazio.",                 2, None),
    ("Ele forca a porta dos fundos.",           "A madeira cedeu, devagar.",             5, "frio"),
    ("Desce a escada apertando a parede.",      "Os degraus afundavam sob o pe.",        5, None),
    ("Acende o toco de vela que trazia.",       "A chama mal mordia o escuro.",          7, None),
]


def _resp_ditada(prosa, pressao, atmosfera=None):
    """Monta a resposta do Cronista (prosa + bloco <estado> ditado) que _separar_estado parseia."""
    corpo = f"pressao_emocional: {pressao}"
    if atmosfera:
        corpo += f"\natmosfera: {atmosfera}"
    return f"{prosa}\n\n<estado>\n{corpo}\n</estado>"


async def _rodar_andaime(monkeypatch):
    """[4] O LOOP: roda o roteiro turno a turno por executar_turno_narrado, alimentando o
    EstadoSessao e coletando o transcript [3]."""
    # --- stubs (mesmo padrao do montar_motor): Opus mock + DB sem banco ---
    cronista = {"resp": ""}
    monkeypatch.setattr(jogo, "MODO_MOCK", True)
    monkeypatch.setattr(jogo, "_cronista_mock", lambda msgs: cronista["resp"])

    async def _stub_estado(sid, pressao, resultado=None):
        return "[ESTADO]"

    async def _stub_ctx(sid, q=None):
        return ""

    async def _stub_grava(sid, papel, conteudo):
        return None

    monkeypatch.setattr(jogo, "_montar_estado_safe", _stub_estado)
    monkeypatch.setattr(jogo, "_carregar_contexto_safe", _stub_ctx)
    monkeypatch.setattr(jogo, "_gravar_turno_safe", _stub_grava)

    estado = EstadoSessao(sessao_atual=2, modelo_atual="claude-opus-4-8", pressao_inicial=0)
    transcript = []

    for n, (fala, prosa, pressao_dita, atm) in enumerate(ROTEIRO, start=1):
        cronista["resp"] = _resp_ditada(prosa, pressao_dita, atm)
        pressao_antes = estado.pressao
        res = await jogo.executar_turno_narrado(
            estado.para_turno(), fala, True,
            ui=jogo._UI_TURNO_NOOP, inimigos=(), deve_abortar=lambda: False,
        )
        transcript.append({
            "numero_turno": n,
            "fala_jogador": fala,
            "prosa": res.prosa,
            "pressao_antes": pressao_antes,
            "pressao_depois": res.pressao,
            "atmosfera": res.atmosfera,
            "teste": res.teste,
            "historico_len": estado.historico_len,
        })

    return transcript


def test_andaime_encadeia_turnos_narrados(monkeypatch):
    transcript = _run(_rodar_andaime(monkeypatch))

    # transcript visivel (com -s) para auditoria do encadeamento
    print("\n=== TRANSCRIPT DO ANDAIME ===")
    for e in transcript:
        print(f"  turno {e['numero_turno']}: pressao {e['pressao_antes']}->{e['pressao_depois']} "
              f"| atm={e['atmosfera']} | teste={e['teste']} | hist_len={e['historico_len']}")
        print(f"      fala : {e['fala_jogador']!r}")
        print(f"      prosa: {e['prosa']!r}")

    # (c) uma entrada por acao do roteiro
    assert len(transcript) == len(ROTEIRO)

    # (a) o historico cresce 2 msgs (user+assistant) por turno
    for e in transcript:
        assert e["historico_len"] == 2 * e["numero_turno"], \
            f"historico turno {e['numero_turno']}: {e['historico_len']} != {2 * e['numero_turno']}"

    # (b) a pressao encadeia: antes[N+1] == depois[N]
    for i in range(1, len(transcript)):
        assert transcript[i]["pressao_antes"] == transcript[i - 1]["pressao_depois"], \
            f"pressao quebrou entre turno {i} e {i + 1}"

    # primeiro turno entra com a pressao inicial (0) e a ditada sai
    assert transcript[0]["pressao_antes"] == 0
    assert [e["pressao_depois"] for e in transcript] == [2, 5, 5, 7]
    # atmosfera valida passa; ausente fica None
    assert transcript[1]["atmosfera"] == "frio"
    assert transcript[0]["atmosfera"] is None

    # (d) cada entrada com prosa nao-vazia, teste None (sem combate), e campos presentes
    for e in transcript:
        assert e["prosa"] and e["prosa"].strip()
        assert e["teste"] is None
        for campo in ("numero_turno", "fala_jogador", "prosa", "pressao_antes",
                      "pressao_depois", "atmosfera", "teste", "historico_len"):
            assert campo in e
