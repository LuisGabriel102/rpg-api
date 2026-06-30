# -*- coding: utf-8 -*-
"""
GOLDEN — magia conjurada FORA de combate cobra MP (Opcao A).

A REDE (Gate 1 da obra): hoje, fora de combate, o Opus nao dita via:magico e o motor
forca via_atual="fisico" cego (branch not-_combate_on) -> magia narrada fora de combate
NAO cobra mana. Este golden dita via:magico num turno SEM combate (sem inimigo,
tensao=None) e exige que mp_atual caia em 4 (mesmo custo da magia em combate). FALHA
contra o codigo atual; passa quando a obra (prompt ensina o Opus a ditar via:magico fora
de combate + motor le a via e cobra _gastar_mp no narrar) entrar.

A seco: zero Opus, FakeSession em memoria, zero browser. O custo de MP roda pela mesma
maquinaria ja exercitada pelo arco 3 (curar -> 10 MP via _gastar_mp).
"""
import asyncio

import jogo
from harness_combate import montar_motor, char_padrao


def _run(coro):
    return asyncio.run(coro)


async def _conjurar_fora_de_combate(monkeypatch):
    m = await montar_motor(monkeypatch, com_ficha=True, char=char_padrao())  # mp_atual=38

    # higiene (igual aos outros goldens): silencia o _gravar_pressao best-effort, que sem
    # stub bate no _FakeResult e loga 'erro' cosmetico. Nao toca o que se asserta.
    async def _noop_pressao(sid, valor):
        return None
    monkeypatch.setattr(jogo, "_gravar_pressao", _noop_pressao)

    mp_antes = m.char["mp_atual"]
    # JOGADOR conjura magia FORA de combate: <estado> com via:magico, SEM combate:1, SEM
    # inimigo. Hoje o branch not-_combate_on forca fisico e ignora a via -> mp fica intacto.
    await m.turno("via: magico")
    return {"mp_antes": mp_antes, "mp_depois": m.char["mp_atual"],
            "tensao": m.tensao, "inimigo": m.inimigo, "via": m._cell("via_atual")}


def test_golden_magia_fora_combate_cobra_mp(monkeypatch):
    r = _run(_conjurar_fora_de_combate(monkeypatch))
    print(f"\n=== MAGIA FORA DE COMBATE === tensao={r['tensao']} inimigo={r['inimigo']} "
          f"via={r['via']} | mp {r['mp_antes']}->{r['mp_depois']}")
    # pre-condicao: realmente fora de combate (sem inimigo, sem tensao)
    assert r["tensao"] is None and r["inimigo"] is None, "pre-condicao: fora de combate"
    # a obra: conjurar magia fora de combate cobra 4 MP (mesmo custo do combate)
    assert r["mp_depois"] == r["mp_antes"] - 4, (
        f"magia fora de combate deveria cobrar 4 MP: {r['mp_antes']}->{r['mp_depois']}")
