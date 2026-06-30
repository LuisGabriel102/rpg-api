# -*- coding: utf-8 -*-
"""
FATIA N (Etapa 2) — GOLDEN-FOTOGRAFO do ARCO de combate (a REDE, antes da extracao).

Antes de extrair o combate de jogo.py em fatias futuras, fotografamos o TRACO OBSERVAVEL
INTEIRO de um arco roteirizado e o travamos como ESPERADO. A extracao tera de reproduzir
este golden byte-a-byte; qualquer desvio quebra de proposito. Caracterizacao pura: o
CODIGO ATUAL e a verdade — divergencias se reportam, nao se "consertam".

Deterministico, isolado: zero DB real (FakeSession em memoria), zero Opus, zero browser.
Reusa o harness `montar_motor` (FakeUI no-op + MODO_MOCK + _cronista_mock DITADO +
classificar_faixa FORCADA). com_ficha=True liga o combate completo (feridas/fadiga/
custo/momentum) — necessario p/ fotografar dano-em-voce, custo de Vigor e nascimento
de ferida.

Por PASSO do arco, o snapshot trava:
  - cells   : as 10 nonlocals de combate (teste_pendente, resultado_pendente, tensao,
              alvo, bando, acao, via, feridas_ativas, feridas_ja_usadas, _infeccao_pendente)
  - vitais  : hp / vigor / mp / fadiga do char (espelho do banco via FakeSession)
  - ui      : a sequencia de emits (armarDado, __resolverDado, fichaSetTensao,
              fichaSetVitais, setPressao, momentum) extraida da lista ui.js
  - db      : as ESCRITAS de combate normalizadas em tuplas semanticas (NAO SQL cru)
  - grav    : as gravacoes da espinha (turno jogador/narrador, pressao) na ordem

=== RNG MORTO (pre-requisito do byte-a-byte) ===
Os unicos nao-deterministas do combate sao d1/d2 (`random.randint(1,10)`, jogo.py:3631-3632).
Como a faixa JA e FORCADA (override de classificar_faixa no harness), d1/d2 nao decidem
NADA do veredito — sobrevivem apenas COSMETICAMENTE dentro do emit __resolverDado. Via
escolhida: mock de `random.randint` no escopo do modulo `jogo` (jogo.random e o modulo
global importado em jogo.py:32), fixado num valor constante. monkeypatch reverte ao fim.
Preferida a seed(): a seed fixaria a SEQUENCIA, mas o emit ainda variaria com a ORDEM de
consumo; a constante e mais legivel e torna o emit literal-estavel.
"""
import asyncio

import jogo
from harness_combate import montar_motor, char_padrao


def _run(coro):
    return asyncio.run(coro)


_D_FIXO = 5  # d1 == d2 == 5: faixa ja forcada, isto e so o numero exibido no emit


def _matar_rng(monkeypatch):
    monkeypatch.setattr(jogo.random, "randint", lambda a, b: _D_FIXO)


# --------------------------------------------------------------------------- #
# extratores: ui.js cru -> tokens semanticos; db_log cru -> escritas semanticas
# --------------------------------------------------------------------------- #
def _ui_tags(js):
    """Filtra ui.js para os emits de COMBATE/turno (whitelist), preservando a ORDEM.
    A moldura de shell/stream (Jogar.arrive, fichaSet de render, etc.) e DESCARTADA de
    proposito: a rede fotografa o traco de combate, nao a chrome — assim um tweak de UI
    alheio nao quebra este golden por falso-positivo."""
    out = []
    for c in js:
        c = str(c)
        if "armarDado" in c:
            out.append("armarDado")
        elif "__resolverDado" in c:
            inside = c.split("__resolverDado(", 1)[1].rsplit(")", 1)[0]
            out.append("resolverDado(" + inside + ")")
        elif "fichaSetVitais" in c:
            out.append("vitais")
        elif "fichaSetTensao" in c:
            val = c.split("fichaSetTensao(", 1)[1].rsplit(")", 1)[0]
            out.append("tensao(" + val + ")")
        elif "setPressao" in c:
            val = c.split("setPressao(", 1)[1].rsplit(")", 1)[0]
            out.append("pressao(" + val + ")")
        elif "vignette-momentum" in c:
            out.append("momentum-limpa" if "v.className=''" in c else "momentum-set")
        elif "setAtmosfera" in c:
            out.append("atmosfera")
        # demais strings = chrome de shell/stream -> descartadas (fora do escopo do golden)
    return out


def _norm_db(entries):
    """Normaliza as ESCRITAS (UPDATEs) do combate em tuplas semanticas; ignora SELECTs."""
    out = []
    for low, params in entries:
        s = low.strip()
        if not s.startswith("update"):
            continue
        if "set hp_atual = :hp, vigor_atual = :vig" in s:
            out.append(["hp_vig", params["hp"], params["vig"]])
        elif "set vigor_atual = :v " in s:
            out.append(["vigor", params["v"]])
        elif "set mp_atual = :m" in s:
            out.append(["mp", params["m"]])
        elif "set fadiga_atual = :f" in s:
            out.append(["fadiga", params["f"]])
        elif "ferida_infeccao_pendente" in s:
            out.append(["infeccao", params.get("j")])
        else:
            out.append(["?", s[:40]])
    return out


# --------------------------------------------------------------------------- #
# captura do arco
# --------------------------------------------------------------------------- #
async def _capturar(monkeypatch):
    _matar_rng(monkeypatch)
    m = await montar_motor(monkeypatch, com_ficha=True)

    grav = []
    async def _rec_turno(sid, papel, conteudo):
        grav.append(["turno", papel, conteudo])
    async def _rec_pressao(sid, valor):
        grav.append(["pressao", valor])
    monkeypatch.setattr(jogo, "_gravar_turno_safe", _rec_turno)
    monkeypatch.setattr(jogo, "_gravar_pressao", _rec_pressao)

    golden = []
    cursor = {"n": 0}

    def _snap(passo):
        novos = m.db_log[cursor["n"]:]
        cursor["n"] = len(m.db_log)
        snap = {
            "passo": passo,
            "cells": {
                "teste": m.teste_pendente["intencao"] if m.teste_pendente else None,
                "resultado": m.resultado_pendente,
                "tensao": m.tensao,
                "alvo": m.inimigo["nome"] if m.inimigo else None,
                "bando": [[e["nome"], e["hp"], e["tier"]] for e in m.inimigos],
                "acao": m.acao,
                "via": m._cell("via_atual"),
                "feridas": [f["nome"] for f in m._cell("feridas_ativas")],
                "usadas": list(m._cell("feridas_ja_usadas")),
                "infeccao": [[p["nome"], p["severidade"]] for p in m._cell("_infeccao_pendente")],
            },
            "vitais": {
                "hp": m.char["hp_atual"], "vigor": m.char["vigor_atual"],
                "mp": m.char["mp_atual"], "fadiga": m.char["fadiga_atual"],
            },
            "ui": _ui_tags(m.ui.js),
            "db": _norm_db(novos),
            "grav": list(grav),
        }
        grav.clear()
        golden.append(snap)

    # ===== ARCO ROTEIRIZADO (capanga comum, hp 6; dano sucesso=4) =====
    # 1) SPAWN: combate abre, capanga nasce (hp do tier), motor arma o golpe.
    await m.turno("combate: 1\ninimigo: capanga | comum\nacao: ataque")
    _snap("1-spawn+arma")
    # 2) GOLPE QUE ACERTA: sucesso -> dano no inimigo (6->2); custo de Vigor (fisico).
    await m.rolar("sucesso")
    _snap("2-acerta(6->2)")
    # 3) VESTE o resultado (guard _vestindo): nao re-arma.
    await m.turno("acao: ataque")
    _snap("3-veste")
    # 4) RE-ARMA o golpe (ja nao veste).
    await m.turno("acao: ataque")
    _snap("4-rearma")
    # 5) GOLPE QUE FALHA: falha -> dano EM VOCE (Vigor) + custo do ataque; inimigo intacto.
    await m.rolar("falha")
    _snap("5-falha(dano+custo)")
    # 6) VESTE.
    await m.turno("acao: ataque")
    _snap("6-veste")
    # 7) RE-ARMA.
    await m.turno("acao: ataque")
    _snap("7-rearma")
    # 8) FALHA CRITICA: dano em voce (HP) + fadiga +1 + SINAL p/ o Cronista nomear ferida.
    await m.rolar("falha_critica")
    _snap("8-falha_critica(sinal ferida)")
    # 9) NASCE A FERIDA: o Cronista nomeia (veste o sinal, nao re-arma); sangramento dreva Vigor.
    await m.turno("ferida: corte fundo\nacao: ataque")
    _snap("9-nasce ferida")
    # 10) RE-ARMA (com a ferida sangrando custando Vigor de novo).
    await m.turno("acao: ataque")
    _snap("10-rearma")
    # 11) MORTE: sucesso -> capanga 2->0, sai do bando, tag [capanga caiu], sem alvo.
    await m.rolar("sucesso")
    _snap("11-morte(2->0)")
    # 12) COMBATE FECHA: sem inimigo vivo e sem combate:1 -> tensao some; ferida vira
    #     infeccao pendente; fadiga recupera -3.
    await m.turno("acao: ataque")
    _snap("12-fecha")

    return golden


# GOLDEN esperado — o TRACO EXPLICITO travado, passo a passo (a extracao do combate tera
# de reproduzi-lo byte-a-byte). Capturado contra o combate ATUAL (jogo.py intocado) e
# auditado beat-a-beat: spawn(1) -> acerta 6->2(2) -> falha: dano+custo(5) -> falha
# critica: HP -12 + fadiga +1 + sinal de ferida(8) -> nasce ferida + sangramento(9) ->
# morte 2->0 + [capanga caiu](11) -> combate fecha: ferida->infeccao, fadiga -3(12).
_GRAV_TURNO = [["turno", "jogador", "ajo."], ["turno", "narrador", "A cena se move."], ["pressao", 0]]

ESPERADO = [
    {  # 1 — SPAWN: capanga (hp 6 do tier) nasce, tensao acende, motor arma o golpe.
        "passo": "1-spawn+arma",
        "cells": {"teste": "golpe", "resultado": None, "tensao": 1, "alvo": "capanga",
                  "bando": [["capanga", 6, "comum"]], "acao": "ataque", "via": "fisico",
                  "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 80, "vigor": 18, "mp": 38, "fadiga": 0},
        "ui": ["armarDado", "pressao(0)", "tensao(1)", "vitais"],
        "db": [], "grav": _GRAV_TURNO,
    },
    {  # 2 — ACERTA: sucesso -> inimigo 6->2; sucesso nao fere voce, mas o ataque custa Vigor.
        "passo": "2-acerta(6->2)",
        "cells": {"teste": None, "resultado": "golpe — sucesso", "tensao": 1, "alvo": "capanga",
                  "bando": [["capanga", 2, "comum"]], "acao": "ataque", "via": "fisico",
                  "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 80, "vigor": 17, "mp": 38, "fadiga": 0},
        "ui": ['resolverDado(5,5,1,10,"sucesso","Sucesso")', "vitais", "momentum-set"],
        "db": [["vigor", 17]], "grav": [],
    },
    {  # 3 — VESTE: resultado pendente -> _vestindo True -> nao re-arma (teste None).
        "passo": "3-veste",
        "cells": {"teste": None, "resultado": None, "tensao": 2, "alvo": "capanga",
                  "bando": [["capanga", 2, "comum"]], "acao": "ataque", "via": "fisico",
                  "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 80, "vigor": 17, "mp": 38, "fadiga": 0},
        "ui": ["pressao(0)", "tensao(2)", "vitais"],
        "db": [], "grav": _GRAV_TURNO,
    },
    {  # 4 — RE-ARMA: ja nao veste -> o motor arma o golpe de novo.
        "passo": "4-rearma",
        "cells": {"teste": "golpe", "resultado": None, "tensao": 3, "alvo": "capanga",
                  "bando": [["capanga", 2, "comum"]], "acao": "ataque", "via": "fisico",
                  "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 80, "vigor": 17, "mp": 38, "fadiga": 0},
        "ui": ["armarDado", "pressao(0)", "tensao(3)", "vitais"],
        "db": [], "grav": _GRAV_TURNO,
    },
    {  # 5 — FALHA: dano EM VOCE (Vigor 17->13, write hp_vig) + custo do ataque (->12);
       #     inimigo intacto (falha nao fere). Dois 'vitais' = dano + custo.
        "passo": "5-falha(dano+custo)",
        "cells": {"teste": None, "resultado": "golpe — falha", "tensao": 3, "alvo": "capanga",
                  "bando": [["capanga", 2, "comum"]], "acao": "ataque", "via": "fisico",
                  "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 80, "vigor": 12, "mp": 38, "fadiga": 0},
        "ui": ['resolverDado(5,5,1,10,"falha","Falha")', "vitais", "vitais", "momentum-set"],
        "db": [["hp_vig", 80, 13], ["vigor", 12]], "grav": [],
    },
    {  # 6 — VESTE.
        "passo": "6-veste",
        "cells": {"teste": None, "resultado": None, "tensao": 4, "alvo": "capanga",
                  "bando": [["capanga", 2, "comum"]], "acao": "ataque", "via": "fisico",
                  "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 80, "vigor": 12, "mp": 38, "fadiga": 0},
        "ui": ["pressao(0)", "tensao(4)", "vitais"],
        "db": [], "grav": _GRAV_TURNO,
    },
    {  # 7 — RE-ARMA.
        "passo": "7-rearma",
        "cells": {"teste": "golpe", "resultado": None, "tensao": 5, "alvo": "capanga",
                  "bando": [["capanga", 2, "comum"]], "acao": "ataque", "via": "fisico",
                  "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 80, "vigor": 12, "mp": 38, "fadiga": 0},
        "ui": ["armarDado", "pressao(0)", "tensao(5)", "vitais"],
        "db": [], "grav": _GRAV_TURNO,
    },
    {  # 8 — FALHA CRITICA: HP 80->68 (ceil(80*0.15)=12) + fadiga +1 + SINAL p/ nomear ferida.
       #     Tres 'vitais' = dano(HP) + custo(Vigor) + fadiga.
        "passo": "8-falha_critica(sinal ferida)",
        "cells": {"teste": None,
                  "resultado": "golpe — falha crítica [falha_critica: nomeie UMA ferida nova — "
                               "invente um nome inedito, fora desta lista: nenhuma]",
                  "tensao": 5, "alvo": "capanga", "bando": [["capanga", 2, "comum"]],
                  "acao": "ataque", "via": "fisico", "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 68, "vigor": 11, "mp": 38, "fadiga": 1},
        "ui": ['resolverDado(5,5,1,10,"falha_critica","Falha crítica")',
               "vitais", "vitais", "vitais", "momentum-set"],
        "db": [["hp_vig", 68, 12], ["vigor", 11], ["fadiga", 1]], "grav": [],
    },
    {  # 9 — NASCE A FERIDA: o Cronista nomeia 'corte fundo' (veste o sinal, nao re-arma);
       #     sangramento dreva Vigor 11->10.
        "passo": "9-nasce ferida",
        "cells": {"teste": None, "resultado": None, "tensao": 6, "alvo": "capanga",
                  "bando": [["capanga", 2, "comum"]], "acao": "ataque", "via": "fisico",
                  "feridas": ["corte fundo"], "usadas": ["corte fundo"], "infeccao": []},
        "vitais": {"hp": 68, "vigor": 10, "mp": 38, "fadiga": 1},
        "ui": ["vitais", "pressao(0)", "tensao(6)", "vitais"],
        "db": [["vigor", 10]], "grav": _GRAV_TURNO,
    },
    {  # 10 — RE-ARMA (a ferida sangrando custa Vigor de novo, 10->9).
        "passo": "10-rearma",
        "cells": {"teste": "golpe", "resultado": None, "tensao": 7, "alvo": "capanga",
                  "bando": [["capanga", 2, "comum"]], "acao": "ataque", "via": "fisico",
                  "feridas": ["corte fundo"], "usadas": ["corte fundo"], "infeccao": []},
        "vitais": {"hp": 68, "vigor": 9, "mp": 38, "fadiga": 1},
        "ui": ["vitais", "armarDado", "pressao(0)", "tensao(7)", "vitais"],
        "db": [["vigor", 9]], "grav": _GRAV_TURNO,
    },
    {  # 11 — MORTE: sucesso -> capanga 2->0, sai do bando, tag [capanga caiu], sem alvo.
       #     Custo do ataque (Vigor 9->8). momentum-limpa (sem inimigo).
        "passo": "11-morte(2->0)",
        "cells": {"teste": None, "resultado": "golpe — sucesso [capanga caiu]", "tensao": 7,
                  "alvo": None, "bando": [], "acao": "ataque", "via": "fisico",
                  "feridas": ["corte fundo"], "usadas": ["corte fundo"], "infeccao": []},
        "vitais": {"hp": 68, "vigor": 8, "mp": 38, "fadiga": 1},
        "ui": ['resolverDado(5,5,1,10,"sucesso","Sucesso")', "vitais", "momentum-limpa"],
        "db": [["vigor", 8]], "grav": [],
    },
    {  # 12 — COMBATE FECHA: sem inimigo + sem combate:1 -> tensao some; ferida aberta vira
       #      infeccao pendente [corte fundo, sev 1]; fadiga recupera -3 (1->0).
        "passo": "12-fecha",
        "cells": {"teste": None, "resultado": None, "tensao": None, "alvo": None, "bando": [],
                  "acao": "ataque", "via": "fisico", "feridas": [], "usadas": ["corte fundo"],
                  "infeccao": [["corte fundo", 1]]},
        "vitais": {"hp": 68, "vigor": 8, "mp": 38, "fadiga": 0},
        "ui": ["momentum-limpa", "vitais", "pressao(0)", "tensao(null)", "vitais"],
        "db": [["infeccao", '[{"nome": "corte fundo", "severidade": 1}]'], ["fadiga", 0]],
        "grav": _GRAV_TURNO,
    },
]


def test_golden_arco_combate(monkeypatch):
    golden = _run(_capturar(monkeypatch))
    # auditoria visivel com -s (o juiz e a comparacao com ESPERADO; isto e so leitura humana)
    print("\n=== GOLDEN ARCO COMBATE (capturado) ===")
    for s in golden:
        print("---", s["passo"], "---")
        print("  cells :", s["cells"])
        print("  vitais:", s["vitais"])
        print("  ui    :", s["ui"])
        print("  db    :", s["db"])
        print("  grav  :", s["grav"])
    assert golden == ESPERADO


# =========================================================================== #
# ARCO 2 — VIA MAGICA + COMBO (fecha a lacuna do Gate 1: o arco fisico nunca
# dispara _gastar_mp nem a furada de guarda do combo). Inimigo bravo em postura
# DEFENSIVA: na MESMA faixa (sucesso), o ataque magico passa pela METADE (fator
# 0.5 -> 2 de dano) e o COMBO fura a guarda (fator 1.0 -> 4 de dano). O contraste
# 2-vs-4 no HP do mesmo inimigo TRAVA o efeito do _fator_inimigo (jogo.py:3694).
# MP de partida = 38 (char_padrao); folga de sobra p/ magico(-4) + combo(-4) = -8.
# =========================================================================== #
async def _capturar_magico_combo(monkeypatch):
    _matar_rng(monkeypatch)
    m = await montar_motor(monkeypatch, com_ficha=True, char=char_padrao())  # mp_atual=38

    grav = []
    async def _rec_turno(sid, papel, conteudo):
        grav.append(["turno", papel, conteudo])
    async def _rec_pressao(sid, valor):
        grav.append(["pressao", valor])
    monkeypatch.setattr(jogo, "_gravar_turno_safe", _rec_turno)
    monkeypatch.setattr(jogo, "_gravar_pressao", _rec_pressao)

    golden = []
    cursor = {"n": 0}

    def _snap(passo):
        novos = m.db_log[cursor["n"]:]
        cursor["n"] = len(m.db_log)
        snap = {
            "passo": passo,
            "cells": {
                "teste": m.teste_pendente["intencao"] if m.teste_pendente else None,
                "resultado": m.resultado_pendente,
                "tensao": m.tensao,
                "alvo": m.inimigo["nome"] if m.inimigo else None,
                "bando": [[e["nome"], e["hp"], e["tier"]] for e in m.inimigos],
                "acao": m.acao,
                "via": m._cell("via_atual"),
                "feridas": [f["nome"] for f in m._cell("feridas_ativas")],
                "usadas": list(m._cell("feridas_ja_usadas")),
                "infeccao": [[p["nome"], p["severidade"]] for p in m._cell("_infeccao_pendente")],
            },
            "vitais": {
                "hp": m.char["hp_atual"], "vigor": m.char["vigor_atual"],
                "mp": m.char["mp_atual"], "fadiga": m.char["fadiga_atual"],
            },
            "ui": _ui_tags(m.ui.js),
            "db": _norm_db(novos),
            "grav": list(grav),
        }
        grav.clear()
        golden.append(snap)

    # 1) SPAWN bravo DEFENSIVA + via:magico; o motor arma o golpe (hp 12 do tier bravo).
    await m.turno("combate: 1\ninimigo: couraça | bravo\nacao: ataque\npostura: defensiva\nvia: magico")
    _snap("1-spawn magico (defensiva)")
    # 2) ROLAR MAGICO: sucesso -> custa MP(4), Vigor INTACTO; dano no inimigo pela METADE
    #    (defensiva, fator 0.5): base 4 -> 2, hp 12->10.
    await m.rolar("sucesso")
    _snap("2-magico: MP-4, vigor intacto, dano halved (12->10)")
    # 3) VESTE.
    await m.turno("acao: ataque\npostura: defensiva")
    _snap("3-veste")
    # 4) RE-ARMA com via:combo (mantem a defensiva).
    await m.turno("acao: ataque\npostura: defensiva\nvia: combo")
    _snap("4-rearma combo")
    # 5) ROLAR COMBO: sucesso -> drena Vigor(1) E MP(4); FURA a guarda (fator 1.0):
    #    base 4 -> 4 (cheio), hp 10->6. Contraste com o passo 2 (2 vs 4) = o pierce.
    await m.rolar("sucesso")
    _snap("5-combo: vigor-1 + MP-4, pierce (10->6)")
    # 6) RECUO fecha: o inimigo recua -> bando vazio, combate fecha.
    await m.turno("inimigo_recuou: couraça\nacao: ataque")
    _snap("6-recuo fecha")

    return golden


# GOLDEN esperado do arco MAGICO+COMBO — traco real travado. A chave do beat:
#   passo 2 (MAGICO, defensiva): MP 38->34, Vigor INTACTO 18, dano halved 12->10 (fator 0.5)
#   passo 5 (COMBO,  defensiva): Vigor 18->17 + MP 34->30, dano CHEIO 10->6 (fator 1.0 = pierce)
# O delta de dano (2 vs 4) na MESMA faixa/inimigo prova o _fator_inimigo do combo.
ESPERADO_MC = [
    {  # 1 — SPAWN bravo defensiva + via:magico; arma o golpe (hp 12 do tier bravo).
        "passo": "1-spawn magico (defensiva)",
        "cells": {"teste": "golpe", "resultado": None, "tensao": 1, "alvo": "couraça",
                  "bando": [["couraça", 12, "bravo"]], "acao": "ataque", "via": "magico",
                  "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 80, "vigor": 18, "mp": 38, "fadiga": 0},
        "ui": ["armarDado", "pressao(0)", "tensao(1)", "vitais"],
        "db": [], "grav": _GRAV_TURNO,
    },
    {  # 2 — MAGICO: sucesso -> MP -4 (vigor INTACTO); dano halved pela defensiva (12->10).
        "passo": "2-magico: MP-4, vigor intacto, dano halved (12->10)",
        "cells": {"teste": None, "resultado": "golpe — sucesso", "tensao": 1, "alvo": "couraça",
                  "bando": [["couraça", 10, "bravo"]], "acao": "ataque", "via": "magico",
                  "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 80, "vigor": 18, "mp": 34, "fadiga": 0},
        "ui": ['resolverDado(5,5,1,13,"sucesso","Sucesso")', "vitais", "momentum-set"],
        "db": [["mp", 34]], "grav": [],
    },
    {  # 3 — VESTE (via reseta p/ fisico sem a tag).
        "passo": "3-veste",
        "cells": {"teste": None, "resultado": None, "tensao": 2, "alvo": "couraça",
                  "bando": [["couraça", 10, "bravo"]], "acao": "ataque", "via": "fisico",
                  "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 80, "vigor": 18, "mp": 34, "fadiga": 0},
        "ui": ["pressao(0)", "tensao(2)", "vitais"],
        "db": [], "grav": _GRAV_TURNO,
    },
    {  # 4 — RE-ARMA com via:combo (defensiva mantida).
        "passo": "4-rearma combo",
        "cells": {"teste": "golpe", "resultado": None, "tensao": 3, "alvo": "couraça",
                  "bando": [["couraça", 10, "bravo"]], "acao": "ataque", "via": "combo",
                  "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 80, "vigor": 18, "mp": 34, "fadiga": 0},
        "ui": ["armarDado", "pressao(0)", "tensao(3)", "vitais"],
        "db": [], "grav": _GRAV_TURNO,
    },
    {  # 5 — COMBO: sucesso -> drena Vigor(1) E MP(4); FURA a guarda (fator 1.0): dano cheio 10->6.
        "passo": "5-combo: vigor-1 + MP-4, pierce (10->6)",
        "cells": {"teste": None, "resultado": "golpe — sucesso", "tensao": 3, "alvo": "couraça",
                  "bando": [["couraça", 6, "bravo"]], "acao": "ataque", "via": "combo",
                  "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 80, "vigor": 17, "mp": 30, "fadiga": 0},
        "ui": ['resolverDado(5,5,1,13,"sucesso","Sucesso")', "vitais", "vitais", "momentum-set"],
        "db": [["vigor", 17], ["mp", 30]], "grav": [],
    },
    {  # 6 — RECUO fecha: couraça recua -> bando vazio, tensao some, infeccao limpa [].
        "passo": "6-recuo fecha",
        "cells": {"teste": None, "resultado": None, "tensao": None, "alvo": None, "bando": [],
                  "acao": "ataque", "via": "fisico", "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 80, "vigor": 17, "mp": 30, "fadiga": 0},
        "ui": ["momentum-limpa", "pressao(0)", "tensao(null)", "vitais"],
        "db": [["infeccao", "[]"]], "grav": _GRAV_TURNO,
    },
]


def test_golden_magico_combo(monkeypatch):
    golden = _run(_capturar_magico_combo(monkeypatch))
    print("\n=== GOLDEN MAGICO+COMBO (capturado) ===")
    for s in golden:
        print("---", s["passo"], "---")
        print("  cells :", s["cells"])
        print("  vitais:", s["vitais"])
        print("  ui    :", s["ui"])
        print("  db    :", s["db"])
        print("  grav  :", s["grav"])
    assert golden == ESPERADO_MC


# =========================================================================== #
# Helper de snapshot reaproveitavel (arcos 3 e 4). feridas_ricas=True captura o flag
# `infectada` de cada ferida (preciso p/ provar o seed-back de infeccao no arco 4).
# =========================================================================== #
def _snapshot(m, passo, novos, grav, *, feridas_ricas=False):
    feridas = ([[f["nome"], f.get("infectada", False)] for f in m._cell("feridas_ativas")]
               if feridas_ricas else
               [f["nome"] for f in m._cell("feridas_ativas")])
    return {
        "passo": passo,
        "cells": {
            "teste": m.teste_pendente["intencao"] if m.teste_pendente else None,
            "resultado": m.resultado_pendente,
            "tensao": m.tensao,
            "alvo": m.inimigo["nome"] if m.inimigo else None,
            "bando": [[e["nome"], e["hp"], e["tier"]] for e in m.inimigos],
            "acao": m.acao,
            "via": m._cell("via_atual"),
            "feridas": feridas,
            "usadas": list(m._cell("feridas_ja_usadas")),
            "infeccao": [[p["nome"], p["severidade"]] for p in m._cell("_infeccao_pendente")],
        },
        "vitais": {
            "hp": m.char["hp_atual"], "vigor": m.char["vigor_atual"],
            "mp": m.char["mp_atual"], "fadiga": m.char["fadiga_atual"],
        },
        "ui": _ui_tags(m.ui.js),
        "db": _norm_db(novos),
        "grav": list(grav),
    }


# =========================================================================== #
# ARCO 3 — acao:estancar + acao:curar (parse). Fecha 2 ramos antes so-regex:
#   estancar -> pausa as feridas (turnos_estancada=2) e cansa +2 Fadiga (sem faixa-dano);
#   curar    -> gasta 10 MP (_gastar_mp_cura) e fecha a ferida mais antiga.
# MP de partida = 38 (char_padrao): folga p/ o curar (-10) -> 28.
# =========================================================================== #
async def _capturar_curar_estancar(monkeypatch):
    _matar_rng(monkeypatch)
    m = await montar_motor(monkeypatch, com_ficha=True, char=char_padrao())  # mp_atual=38

    grav = []
    async def _rec_turno(sid, papel, conteudo):
        grav.append(["turno", papel, conteudo])
    async def _rec_pressao(sid, valor):
        grav.append(["pressao", valor])
    monkeypatch.setattr(jogo, "_gravar_turno_safe", _rec_turno)
    monkeypatch.setattr(jogo, "_gravar_pressao", _rec_pressao)

    golden = []
    cursor = {"n": 0}

    def _snap(passo):
        novos = m.db_log[cursor["n"]:]
        cursor["n"] = len(m.db_log)
        golden.append(_snapshot(m, passo, novos, grav, feridas_ricas=True))
        grav.clear()

    # 1) SPAWN + arma (lobo comum hp 6).
    await m.turno("combate: 1\ninimigo: lobo | comum\nacao: ataque")
    _snap("1-spawn")
    # 2) FALHA CRITICA -> sinal de ferida + fadiga +1 (lobo intacto: falha_critica nao fere).
    await m.rolar("falha_critica")
    _snap("2-falha_critica")
    # 3) NASCE a ferida 'arranhao' (veste o sinal); sangramento dreva Vigor.
    await m.turno("ferida: arranhao\nacao: ataque")
    _snap("3-nasce ferida")
    # 4) ESTANCAR: pausa a ferida (turnos_estancada=2->decrementa p/ 1) + Fadiga +2; SEM dano,
    #    SEM ferir o lobo (fora da troca); sangramento nao dreva (ferida pausada).
    await m.turno("acao: estancar")
    _snap("4-estancar (+2 fadiga, sem dano)")
    # 5) CURAR: gasta 10 MP (38->28) e fecha a ferida mais antiga (feridas -> []).
    await m.turno("acao: curar")
    _snap("5-curar (MP-10, fecha ferida)")
    # 6) RECUO fecha o combate (lobo recua).
    await m.turno("inimigo_recuou: lobo\nacao: ataque")
    _snap("6-recuo fecha")

    return golden


# GOLDEN curar+estancar — traco real travado. Chaves: estancar (p4) -> Fadiga +2 (1->3),
# SEM dano e SEM drenar Vigor (ferida pausada); curar (p5) -> MP -10 (38->28) + ferida fechada.
ESPERADO_CE = [
    {  # 1 — SPAWN lobo comum (hp 6) + arma.
        "passo": "1-spawn",
        "cells": {"teste": "golpe", "resultado": None, "tensao": 1, "alvo": "lobo",
                  "bando": [["lobo", 6, "comum"]], "acao": "ataque", "via": "fisico",
                  "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 80, "vigor": 18, "mp": 38, "fadiga": 0},
        "ui": ["armarDado", "pressao(0)", "tensao(1)", "vitais"],
        "db": [], "grav": _GRAV_TURNO,
    },
    {  # 2 — FALHA CRITICA: HP 80->68, Vigor -1, Fadiga +1, sinal de ferida; lobo intacto.
        "passo": "2-falha_critica",
        "cells": {"teste": None,
                  "resultado": "golpe — falha crítica [falha_critica: nomeie UMA ferida nova — "
                               "invente um nome inedito, fora desta lista: nenhuma]",
                  "tensao": 1, "alvo": "lobo", "bando": [["lobo", 6, "comum"]],
                  "acao": "ataque", "via": "fisico", "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 68, "vigor": 17, "mp": 38, "fadiga": 1},
        "ui": ['resolverDado(5,5,1,10,"falha_critica","Falha crítica")',
               "vitais", "vitais", "vitais", "momentum-set"],
        "db": [["hp_vig", 68, 18], ["vigor", 17], ["fadiga", 1]], "grav": [],
    },
    {  # 3 — NASCE 'arranhao' (nao-infectada); sangramento Vigor 17->16.
        "passo": "3-nasce ferida",
        "cells": {"teste": None, "resultado": None, "tensao": 2, "alvo": "lobo",
                  "bando": [["lobo", 6, "comum"]], "acao": "ataque", "via": "fisico",
                  "feridas": [["arranhao", False]], "usadas": ["arranhao"], "infeccao": []},
        "vitais": {"hp": 68, "vigor": 16, "mp": 38, "fadiga": 1},
        "ui": ["vitais", "pressao(0)", "tensao(2)", "vitais"],
        "db": [["vigor", 16]], "grav": _GRAV_TURNO,
    },
    {  # 4 — ESTANCAR: Fadiga +2 (1->3); ferida pausada -> SEM sangramento, SEM dano/ferir.
        "passo": "4-estancar (+2 fadiga, sem dano)",
        "cells": {"teste": None, "resultado": None, "tensao": 3, "alvo": "lobo",
                  "bando": [["lobo", 6, "comum"]], "acao": "estancar", "via": "fisico",
                  "feridas": [["arranhao", False]], "usadas": ["arranhao"], "infeccao": []},
        "vitais": {"hp": 68, "vigor": 16, "mp": 38, "fadiga": 3},
        "ui": ["vitais", "pressao(0)", "tensao(3)", "vitais"],
        "db": [["fadiga", 3]], "grav": _GRAV_TURNO,
    },
    {  # 5 — CURAR: MP -10 (38->28) via _gastar_mp_cura; fecha a ferida (feridas -> []).
        "passo": "5-curar (MP-10, fecha ferida)",
        "cells": {"teste": None, "resultado": None, "tensao": 4, "alvo": "lobo",
                  "bando": [["lobo", 6, "comum"]], "acao": "curar", "via": "fisico",
                  "feridas": [], "usadas": ["arranhao"], "infeccao": []},
        "vitais": {"hp": 68, "vigor": 16, "mp": 28, "fadiga": 3},
        "ui": ["vitais", "pressao(0)", "tensao(4)", "vitais"],
        "db": [["mp", 28]], "grav": _GRAV_TURNO,
    },
    {  # 6 — RECUO fecha: sem ferida -> infeccao []; Fadiga recupera -3 (3->0).
        "passo": "6-recuo fecha",
        "cells": {"teste": None, "resultado": None, "tensao": None, "alvo": None, "bando": [],
                  "acao": "ataque", "via": "fisico", "feridas": [], "usadas": ["arranhao"],
                  "infeccao": []},
        "vitais": {"hp": 68, "vigor": 16, "mp": 28, "fadiga": 0},
        "ui": ["momentum-limpa", "vitais", "pressao(0)", "tensao(null)", "vitais"],
        "db": [["infeccao", "[]"], ["fadiga", 0]], "grav": _GRAV_TURNO,
    },
]


def test_golden_curar_estancar(monkeypatch):
    golden = _run(_capturar_curar_estancar(monkeypatch))
    print("\n=== GOLDEN CURAR+ESTANCAR (capturado) ===")
    for s in golden:
        print("---", s["passo"], "---")
        print("  cells :", s["cells"])
        print("  vitais:", s["vitais"])
        print("  ui    :", s["ui"])
        print("  db    :", s["db"])
        print("  grav  :", s["grav"])
    assert golden == ESPERADO_CE


# =========================================================================== #
# ARCO 4 — SEED-BACK de infeccao (atravessa DOIS combates na mesma sessao). O ramo
# mais importante: a infeccao que sobra do combate 1 (ferida aberta no fim) re-nasce
# como ferida INFECTADA na abertura do combate 2 (jogo.py ~3595-3598). Trava
# _infeccao_pendente e feridas_ativas (com o flag infectada) nos dois lados.
# =========================================================================== #
async def _capturar_seed_infeccao(monkeypatch):
    _matar_rng(monkeypatch)
    m = await montar_motor(monkeypatch, com_ficha=True, char=char_padrao())

    grav = []
    async def _rec_turno(sid, papel, conteudo):
        grav.append(["turno", papel, conteudo])
    async def _rec_pressao(sid, valor):
        grav.append(["pressao", valor])
    monkeypatch.setattr(jogo, "_gravar_turno_safe", _rec_turno)
    monkeypatch.setattr(jogo, "_gravar_pressao", _rec_pressao)

    golden = []
    cursor = {"n": 0}

    def _snap(passo):
        novos = m.db_log[cursor["n"]:]
        cursor["n"] = len(m.db_log)
        golden.append(_snapshot(m, passo, novos, grav, feridas_ricas=True))
        grav.clear()

    # --- COMBATE 1: abre, nasce ferida, fecha deixando infeccao pendente ---
    await m.turno("combate: 1\ninimigo: rato | comum\nacao: ataque")
    _snap("1-c1 spawn")
    await m.rolar("falha_critica")
    _snap("2-c1 falha_critica (sinal ferida)")
    await m.turno("ferida: mordida\nacao: ataque")
    _snap("3-c1 nasce ferida (nao-infectada)")
    # recuo fecha o C1: ferida aberta -> _infeccao_pendente=[mordida]; feridas_ativas=[].
    await m.turno("inimigo_recuou: rato\nacao: ataque")
    _snap("4-c1 fecha -> infeccao pendente")

    # --- COMBATE 2: abre na MESMA sessao -> seed-back ---
    await m.turno("combate: 1\ninimigo: gato | comum\nacao: ataque")
    _snap("5-c2 abre -> SEED-BACK (ferida infectada)")

    return golden


# GOLDEN seed-back de infeccao — atravessa DOIS combates. Chave: o p4 fecha o C1 com
# infeccao pendente [mordida]; o p5 abre o C2 e a mordida RE-NASCE como ferida INFECTADA
# (feridas=[["mordida", True]]) enquanto _infeccao_pendente volta a [].
ESPERADO_SEED = [
    {  # 1 — C1 SPAWN rato comum + arma.
        "passo": "1-c1 spawn",
        "cells": {"teste": "golpe", "resultado": None, "tensao": 1, "alvo": "rato",
                  "bando": [["rato", 6, "comum"]], "acao": "ataque", "via": "fisico",
                  "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 80, "vigor": 18, "mp": 38, "fadiga": 0},
        "ui": ["armarDado", "pressao(0)", "tensao(1)", "vitais"],
        "db": [], "grav": _GRAV_TURNO,
    },
    {  # 2 — C1 FALHA CRITICA: sinal de ferida + HP/Vigor/Fadiga.
        "passo": "2-c1 falha_critica (sinal ferida)",
        "cells": {"teste": None,
                  "resultado": "golpe — falha crítica [falha_critica: nomeie UMA ferida nova — "
                               "invente um nome inedito, fora desta lista: nenhuma]",
                  "tensao": 1, "alvo": "rato", "bando": [["rato", 6, "comum"]],
                  "acao": "ataque", "via": "fisico", "feridas": [], "usadas": [], "infeccao": []},
        "vitais": {"hp": 68, "vigor": 17, "mp": 38, "fadiga": 1},
        "ui": ['resolverDado(5,5,1,10,"falha_critica","Falha crítica")',
               "vitais", "vitais", "vitais", "momentum-set"],
        "db": [["hp_vig", 68, 18], ["vigor", 17], ["fadiga", 1]], "grav": [],
    },
    {  # 3 — C1 NASCE 'mordida' (nao-infectada); sangramento Vigor 17->16.
        "passo": "3-c1 nasce ferida (nao-infectada)",
        "cells": {"teste": None, "resultado": None, "tensao": 2, "alvo": "rato",
                  "bando": [["rato", 6, "comum"]], "acao": "ataque", "via": "fisico",
                  "feridas": [["mordida", False]], "usadas": ["mordida"], "infeccao": []},
        "vitais": {"hp": 68, "vigor": 16, "mp": 38, "fadiga": 1},
        "ui": ["vitais", "pressao(0)", "tensao(2)", "vitais"],
        "db": [["vigor", 16]], "grav": _GRAV_TURNO,
    },
    {  # 4 — C1 FECHA (recuo): ferida aberta -> _infeccao_pendente=[mordida]; feridas=[]; Fadiga -3.
        "passo": "4-c1 fecha -> infeccao pendente",
        "cells": {"teste": None, "resultado": None, "tensao": None, "alvo": None, "bando": [],
                  "acao": "ataque", "via": "fisico", "feridas": [], "usadas": ["mordida"],
                  "infeccao": [["mordida", 1]]},
        "vitais": {"hp": 68, "vigor": 16, "mp": 38, "fadiga": 0},
        "ui": ["momentum-limpa", "vitais", "pressao(0)", "tensao(null)", "vitais"],
        "db": [["infeccao", '[{"nome": "mordida", "severidade": 1}]'], ["fadiga", 0]],
        "grav": _GRAV_TURNO,
    },
    {  # 5 — C2 ABRE -> SEED-BACK: 'mordida' RE-NASCE INFECTADA (feridas=[["mordida", True]]),
       #     _infeccao_pendente volta a []; sangramento da ferida semeada (Vigor 16->15); arma.
        "passo": "5-c2 abre -> SEED-BACK (ferida infectada)",
        "cells": {"teste": "golpe", "resultado": None, "tensao": 1, "alvo": "gato",
                  "bando": [["gato", 6, "comum"]], "acao": "ataque", "via": "fisico",
                  "feridas": [["mordida", True]], "usadas": ["mordida"], "infeccao": []},
        "vitais": {"hp": 68, "vigor": 15, "mp": 38, "fadiga": 0},
        "ui": ["vitais", "armarDado", "pressao(0)", "tensao(1)", "vitais"],
        "db": [["vigor", 15]], "grav": _GRAV_TURNO,
    },
]


def test_golden_seed_infeccao(monkeypatch):
    golden = _run(_capturar_seed_infeccao(monkeypatch))
    print("\n=== GOLDEN SEED-BACK INFECCAO (capturado) ===")
    for s in golden:
        print("---", s["passo"], "---")
        print("  cells :", s["cells"])
        print("  vitais:", s["vitais"])
        print("  ui    :", s["ui"])
        print("  db    :", s["db"])
        print("  grav  :", s["grav"])
    assert golden == ESPERADO_SEED


# =========================================================================== #
# ARCO 5 — CARRY-OVER de infeccao ATRAVES de um GAP narrativo (a REDE do wipe).
# O seed-back (arco 4) atravessa C1->C2 COLADOS — sem turno intermediario. Aqui um
# turno PURAMENTE narrativo (sem combate) se intromete entre o fim do C1 e a reabertura
# do C2. O esperado CORRETO: a infeccao pendente SOBREVIVE ao gap e re-nasce como ferida
# INFECTADA no C2 (igual ao arco 4, so que com o gap no meio). Trava o TRACO que importa
# (feridas c/ flag `infectada` + _infeccao_pendente) nos QUATRO momentos do carry-over:
# fecha / gap / reabre / pos-seed.
#
# NOTA: este golden falha de proposito contra o codigo ATUAL — o wipe de fim-de-combate
# (jogo.py ~L3109-3113) roda em TODO turno fora de combate, entao o gap zera a infeccao
# pendente ANTES da reabertura e o seed-back nao acha nada p/ semear. Ele e a rede que
# captura esse bug; passa quando o transform+gravar forem movidos p/ dentro do guard de
# transicao `if _tensao_antes is not None:`.
# =========================================================================== #
def _traco_infeccao(m):
    """So o par que prova o carry-over: feridas ativas (com o flag infectada) + a
    infeccao pendente. Robusto a tweaks de ui/db de turno (fora do escopo deste bug)."""
    return {
        "feridas": [[f["nome"], f.get("infectada", False)] for f in m._cell("feridas_ativas")],
        "infeccao": [[p["nome"], p["severidade"]] for p in m._cell("_infeccao_pendente")],
    }


async def _capturar_gap_infeccao(monkeypatch):
    _matar_rng(monkeypatch)
    m = await montar_motor(monkeypatch, com_ficha=True, char=char_padrao())

    # so isolamento (igual aos outros goldens): silencia o _gravar_pressao best-effort,
    # que sem stub bate no _FakeResult e loga 'erro' cosmetico. Nao toca o traco asserido.
    async def _noop_pressao(sid, valor):
        return None
    monkeypatch.setattr(jogo, "_gravar_pressao", _noop_pressao)

    traco = []

    # --- COMBATE 1: abre, nasce ferida, fecha deixando infeccao pendente ---
    await m.turno("combate: 1\ninimigo: rato | comum\nacao: ataque")
    await m.rolar("falha_critica")               # sinal de ferida
    await m.turno("ferida: mordida\nacao: ataque")  # nasce 'mordida' (aberta)
    # recuo fecha o C1 com a ferida AINDA aberta -> _infeccao_pendente=[mordida]; feridas=[].
    await m.turno("inimigo_recuou: rato\nacao: ataque")
    traco.append(["fecha", _traco_infeccao(m)])

    # --- GAP: um turno PURAMENTE narrativo, sem combate (o ponto exato do wipe) ---
    await m.turno("")
    traco.append(["gap", _traco_infeccao(m)])

    # --- COMBATE 2: reabre na MESMA sessao -> o seed-back deve disparar ---
    await m.turno("combate: 1\ninimigo: gato | comum\nacao: ataque")
    traco.append(["reabre", _traco_infeccao(m)])

    # --- POS-SEED: mais um turno de combate; a ferida infectada persiste e segue sangrando ---
    await m.turno("combate: 1\ninimigo: gato | comum\nacao: ataque")
    traco.append(["pos-seed", _traco_infeccao(m)])

    return traco


# TRACO esperado (comportamento CORRETO, pos-conserto). Chave: o gap NAO apaga a infeccao
# pendente; ela sobrevive e re-nasce infectada na reabertura.
ESPERADO_GAP = [
    # FECHA: C1 fecha com ferida aberta -> infeccao pendente [mordida]; feridas zeradas.
    ["fecha", {"feridas": [], "infeccao": [["mordida", 1]]}],
    # GAP: o turno narrativo NAO pode apagar a infeccao pendente.  [BUG ATUAL: vira []]
    ["gap", {"feridas": [], "infeccao": [["mordida", 1]]}],
    # REABRE: seed-back dispara -> 'mordida' re-nasce INFECTADA; _infeccao_pendente volta a [].
    #         [BUG ATUAL: feridas=[] — o gap ja apagou a infeccao antes da reabertura]
    ["reabre", {"feridas": [["mordida", True]], "infeccao": []}],
    # POS-SEED: a ferida infectada sobrevive ao turno de combate seguinte.
    ["pos-seed", {"feridas": [["mordida", True]], "infeccao": []}],
]


def test_golden_seed_gap_infeccao(monkeypatch):
    traco = _run(_capturar_gap_infeccao(monkeypatch))
    print("\n=== GOLDEN SEED-BACK ATRAVES DE GAP (capturado) ===")
    for passo, t in traco:
        print("---", passo, "---", t)
    assert traco == ESPERADO_GAP
