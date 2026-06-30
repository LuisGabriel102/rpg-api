#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bateria de verificacao do fim do Andar 2 — CHECK 1 (personagem 8 resolve) +
CHECK 2 (inventario real). READ-ONLY: so SELECT, nunca escreve.

    python tests/verif_fim_andar2.py

Nao e coletado pelo pytest (nome 'verif_*'). Faz warm-up (acorda o Neon) antes de ler.
"""
import asyncio
import os
import sys

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from sqlalchemy import text  # noqa: E402
from db import get_session  # noqa: E402
import jogo  # noqa: E402  (reusa jogo._ler_inventario, o caminho real)

PID = 8
ESPERADOS = [
    "Adaga gasta", "Capa de viagem", "Cantil de couro",
    "Caderno de anotacoes", "Isca de breu",
]


def _log(m=""):
    print(m, flush=True)


async def warmup():
    async with get_session() as s:
        v = (await s.execute(text("SELECT 1"))).scalar()
    assert v == 1, "warm-up falhou"
    _log("[warm-up] Neon respondeu SELECT 1 (acordado).")


async def check1():
    """O que /jogar?personagem=8 PUSHA pro HUD/ficha sai destas colunas
    (mesmas lidas por _empurrar_vitais + _montar_estado). Confirmo contra o banco."""
    _log("\n=== CHECK 1 — personagem 8 resolve vs banco (READ-ONLY) ===")
    async with get_session() as s:
        p = (await s.execute(text(
            "SELECT id, nome, classe_primaria, nivel, "
            "hp_atual, hp_maximo, vigor_atual, vigor_maximo, "
            "fadiga_atual, fadiga_maximo, divida_viva, "
            "mod_forca, mod_destreza, mod_constituicao, "
            "mod_inteligencia, mod_sabedoria, mod_carisma "
            "FROM personagens WHERE id = :i"
        ), {"i": PID})).mappings().first()
        m = (await s.execute(text(
            "SELECT mp_atual, mp_maximo FROM personagem_mana WHERE personagem_id = :i"
        ), {"i": PID})).mappings().first()
    if not p:
        _log(f"  [FAIL] personagem {PID} NAO existe no banco.")
        return False
    _log(f"  nome             : {p['nome']!r}")
    _log(f"  vocacao/classe   : {p['classe_primaria']!r}   nivel: {p['nivel']}")
    _log(f"  vida (hp)        : {p['hp_atual']}/{p['hp_maximo']}")
    _log(f"  vigor            : {p['vigor_atual']}/{p['vigor_maximo']}")
    _log(f"  fadiga           : {p['fadiga_atual']}/{p['fadiga_maximo']}   divida_viva: {p['divida_viva']}")
    _log(f"  mana (mp)        : {(str(m['mp_atual'])+'/'+str(m['mp_maximo'])) if m else 'sem linha personagem_mana'}")
    _log(f"  atributos (mods) : FOR{p['mod_forca']:+d} DEX{p['mod_destreza']:+d} CON{p['mod_constituicao']:+d} "
         f"INT{p['mod_inteligencia']:+d} SAB{p['mod_sabedoria']:+d} CHA{p['mod_carisma']:+d}")
    nome_ok = bool(p["nome"])
    vida_ok = p["hp_atual"] is not None and p["hp_maximo"] is not None
    classe_ok = bool(p["classe_primaria"])
    _log(f"  -> nome presente: {nome_ok} | classe presente: {classe_ok} | vida nao-nula: {vida_ok}")
    return nome_ok and vida_ok and classe_ok


async def check2():
    """_ler_inventario(8) deve devolver os 5 itens reais (custom witcher-grey),
    NAO os 6 fakes hardcoded. E a lista vazia deve dar [] (caminho 'Mochila vazia.')."""
    _log("\n=== CHECK 2 — inventario real (nao os fakes) ===")
    itens = await jogo._ler_inventario(PID)
    _log(f"  _ler_inventario({PID}) -> {len(itens)} item(ns):")
    nomes = []
    for it in itens:
        nomes.append(it["nome"])
        _log(f"    - {it['nome']!r:32} x{it['quantidade']} eq={it['equipado']} "
             f"rar={it['raridade']!r} tipo={it['tipo']!r}")
    # nenhum dos 6 fakes deve aparecer
    FAKES = {"faca de mato", "capa de la encerada", "cantil de couro",
             "racao de viagem", "bolsa surrada", "pingente de prata"}
    achou_fake = [n for n in nomes if n.strip().lower() in FAKES]
    cinco_ok = len(itens) == 5
    _log(f"  -> {len(itens)} itens (esperado 5): {cinco_ok}")
    _log(f"  -> nenhum dos 6 fakes hardcoded presente: {not achou_fake}"
         + (f"  (ACHOU: {achou_fake})" if achou_fake else ""))

    # caminho do estado vazio: personagem inexistente -> [] (sem escrever, sem erro).
    vazio = await jogo._ler_inventario(999999999)
    vazio_ok = vazio == []
    _log(f"  -> _ler_inventario(999999999) (sem itens) -> {vazio!r} == [] : {vazio_ok}")
    _log("     (lista vazia -> o hook window.fichaSetInventario renderiza 'Mochila vazia.')")
    return cinco_ok and not achou_fake and vazio_ok


async def main():
    try:
        await warmup()
    except Exception as e:  # noqa: BLE001
        _log(f"[ABORT] warm-up falhou: {type(e).__name__}: {e}")
        return 2
    ok1 = await check1()
    ok2 = await check2()
    _log("\n=== RESUMO ===")
    _log(f"  CHECK 1 (personagem 8 resolve): {'PASS' if ok1 else 'FAIL'}")
    _log(f"  CHECK 2 (inventario real = 5) : {'PASS' if ok2 else 'FAIL'}")
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
