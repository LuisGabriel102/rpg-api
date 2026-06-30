#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
E2E de PERSISTENCIA REAL (Degrau 2.8) — Neon vivo, SCRIPT STANDALONE.

Rode com:  python tests/e2e_persistencia.py   (NAO via pytest — o pytest pendura
na coleta por importar app+DB; este script solto faz warm-up e nao pendura.)

O que prova: gravar turno + pressao -> "fechar" -> "reabrir" (NOVA sessao de banco,
simula processo novo) -> o estado sobreviveu (turno persistido, pressao=7 nao zerou).

BLINDAGEM (o banco tem dados REAIS do Gabriel — campanha do Varekhor id 8):
  - O script CRIA a propria bolha descartavel (campanha+personagem+sessao) via
    RETURNING, guarda os IDs, e SO toca esses IDs.
  - Trava de seguranca antes de qualquer escrita/delete: reconfirma nome da bolha
    e pertencimento; assert pers_id/camp_id != 8.
  - TODO DELETE tem WHERE no id especifico. Nenhum DELETE sem WHERE, nenhum por
    nome solto, nenhum TRUNCATE.
  - TEARDOWN sempre roda (try/finally) e remove SO o que foi criado.
"""
import asyncio
import os
import sys

# repo root no sys.path (pra importar 'db' e 'narrador' rodando como script solto)
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

from sqlalchemy import text  # noqa: E402
from db import get_session  # noqa: E402
from narrador.memoria.escrita import gravar_turno  # noqa: E402

CAMP_NOME = "__E2E_DESCARTAVEL__"
PERS_NOME = "__E2E_PERS__"
PRESSAO_ALVO = 7


def _log(msg: str) -> None:
    print(msg, flush=True)


async def warmup() -> None:
    """Acorda o Neon (cold start). command_timeout=30 do db.py cobre a espera."""
    async with get_session() as s:
        v = (await s.execute(text("SELECT 1"))).scalar()
    if v != 1:
        raise RuntimeError(f"warm-up devolveu {v!r}, esperado 1")
    _log("[warm-up] OK — Neon respondeu SELECT 1.")


async def introspectar_sessao_turnos() -> list[dict]:
    """READ do schema real ANTES de inserir — NAO assume nomes de coluna."""
    async with get_session() as s:
        rows = (await s.execute(text(
            "SELECT column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns "
            "WHERE table_name = 'sessao_turnos' "
            "ORDER BY ordinal_position"
        ))).mappings().all()
    cols = [dict(r) for r in rows]
    _log("[schema] sessao_turnos (information_schema):")
    for c in cols:
        _log(f"    - {c['column_name']} {c['data_type']} "
             f"null={c['is_nullable']} default={c['column_default']}")
    return cols


async def setup() -> tuple[int, int, int]:
    """Cria a bolha descartavel numa transacao unica. Retorna (camp_id, pers_id, sess_id)."""
    async with get_session() as s:
        camp_id = (await s.execute(text(
            "INSERT INTO campanhas (nome) VALUES (:n) RETURNING id"
        ), {"n": CAMP_NOME})).scalar()
        pers_id = (await s.execute(text(
            "INSERT INTO personagens (campanha_id, nome) VALUES (:c, :n) RETURNING id"
        ), {"c": camp_id, "n": PERS_NOME})).scalar()
        sess_id = (await s.execute(text(
            "INSERT INTO sessoes (campanha_id, personagem_id, numero_sessao, status) "
            "VALUES (:c, :p, 1, 'ativa') RETURNING id"
        ), {"c": camp_id, "p": pers_id})).scalar()
        await s.commit()
    camp_id, pers_id, sess_id = int(camp_id), int(pers_id), int(sess_id)
    _log(f"[setup] bolha criada: campanha={camp_id} personagem={pers_id} sessao={sess_id}")
    return camp_id, pers_id, sess_id


async def trava_seguranca(camp_id: int, pers_id: int, sess_id: int) -> None:
    """Antes de QUALQUER escrita/delete: confirma que a bolha e a bolha. Aborta se nao."""
    assert camp_id != 8, "ABORTAR: camp_id == 8 (dado real do Gabriel)"
    assert pers_id != 8, "ABORTAR: pers_id == 8 (dado real do Gabriel)"
    async with get_session() as s:
        nome = (await s.execute(text(
            "SELECT nome FROM campanhas WHERE id = :i"
        ), {"i": camp_id})).scalar()
        if nome != CAMP_NOME:
            raise RuntimeError(
                f"ABORTAR: campanha {camp_id} nome={nome!r} != {CAMP_NOME!r} — NAO e a bolha"
            )
        pc = (await s.execute(text(
            "SELECT campanha_id FROM personagens WHERE id = :i"
        ), {"i": pers_id})).scalar()
        if pc != camp_id:
            raise RuntimeError(
                f"ABORTAR: personagem {pers_id} campanha_id={pc} != {camp_id}"
            )
        sc = (await s.execute(text(
            "SELECT campanha_id, personagem_id FROM sessoes WHERE id = :i"
        ), {"i": sess_id})).mappings().first()
        if not sc or sc["campanha_id"] != camp_id or sc["personagem_id"] != pers_id:
            raise RuntimeError(
                f"ABORTAR: sessao {sess_id} nao pertence a bolha ({sc})"
            )
    _log("[trava] OK — bolha confirmada (nome + pertencimento + != id 8).")


async def gravar_estado(pers_id: int, sess_id: int) -> None:
    """O 'fechar': grava um turno (caminho REAL gravar_turno) e a pressao=7."""
    # a. turno via o MESMO caminho do jogo (escrita.gravar_turno -> sessao_turnos)
    numero = await gravar_turno(sess_id, "jogador", "e2e: enfrento a sombra no pier.")
    _log(f"[grava] turno gravado em sessao_turnos (numero_turno={numero}).")
    # b. pressao persistida (o estado que precisa sobreviver ao reload)
    async with get_session() as s:
        await s.execute(text(
            "INSERT INTO personagem_saude_mental (personagem_id, pressao_atual) "
            "VALUES (:p, :v)"
        ), {"p": pers_id, "v": PRESSAO_ALVO})
        await s.commit()
    _log(f"[grava] pressao_atual={PRESSAO_ALVO} persistida em personagem_saude_mental.")


async def reabrir_e_verificar(pers_id: int, sess_id: int) -> tuple[int, int]:
    """O 'reabrir': NOVA sessao de banco (processo novo simulado). Re-le do zero."""
    async with get_session() as s:
        n_turnos = (await s.execute(text(
            "SELECT count(*) FROM sessao_turnos WHERE sessao_id = :i"
        ), {"i": sess_id})).scalar()
        pressao = (await s.execute(text(
            "SELECT pressao_atual FROM personagem_saude_mental WHERE personagem_id = :i"
        ), {"i": pers_id})).scalar()
    return int(n_turnos), (None if pressao is None else int(pressao))


async def teardown(camp_id: int, pers_id: int, sess_id: int) -> int:
    """Remove SO a bolha, na ordem de FK. Reconfirma o nome antes de deletar.
    Retorna o count de campanhas WHERE id=camp_id (esperado 0)."""
    async with get_session() as s:
        # reconfirma que ainda e a bolha (nunca deletar dado real)
        nome = (await s.execute(text(
            "SELECT nome FROM campanhas WHERE id = :i"
        ), {"i": camp_id})).scalar()
        if nome is not None and nome != CAMP_NOME:
            raise RuntimeError(
                f"TEARDOWN ABORTADO: campanha {camp_id} nome={nome!r} != bolha — NAO deleto"
            )
        assert camp_id != 8 and pers_id != 8, "TEARDOWN ABORTADO: id 8 jamais"
        # ordem de FK: filhos -> pais. TODO DELETE com WHERE no id especifico.
        await s.execute(text("DELETE FROM sessao_turnos WHERE sessao_id = :i"), {"i": sess_id})
        await s.execute(text("DELETE FROM personagem_saude_mental WHERE personagem_id = :i"), {"i": pers_id})
        await s.execute(text("DELETE FROM sessoes WHERE id = :i"), {"i": sess_id})
        await s.execute(text("DELETE FROM personagens WHERE id = :i"), {"i": pers_id})
        await s.execute(text("DELETE FROM campanhas WHERE id = :i"), {"i": camp_id})
        await s.commit()
        restante = (await s.execute(text(
            "SELECT count(*) FROM campanhas WHERE id = :i"
        ), {"i": camp_id})).scalar()
    _log(f"[teardown] bolha removida — campanhas WHERE id={camp_id}: count={restante}")
    return int(restante)


async def main() -> int:
    # 1. WARM-UP
    try:
        await warmup()
    except Exception as e:  # noqa: BLE001
        _log(f"[ABORT] warm-up falhou: {type(e).__name__}: {e}")
        return 2

    await introspectar_sessao_turnos()

    camp_id = pers_id = sess_id = None
    a1 = a2 = False
    try:
        # 2. SETUP
        camp_id, pers_id, sess_id = await setup()
        # 3. TRAVA DE SEGURANCA
        await trava_seguranca(camp_id, pers_id, sess_id)
        # 4. O TESTE
        await gravar_estado(pers_id, sess_id)
        n_turnos, pressao = await reabrir_e_verificar(pers_id, sess_id)
        a1 = n_turnos >= 1
        a2 = (pressao == PRESSAO_ALVO)
        _log("")
        _log("=== RESULTADO ===")
        _log(f"  [{'PASS' if a1 else 'FAIL'}] turno sobreviveu ao reload: "
             f"count(sessao_turnos)={n_turnos} (esperado >=1)")
        _log(f"  [{'PASS' if a2 else 'FAIL'}] pressao sobreviveu ao reload: "
             f"pressao_atual={pressao} (esperado {PRESSAO_ALVO})")
        _log("")
    finally:
        # 5. TEARDOWN — sempre, mesmo se o teste falhou
        if camp_id is not None:
            try:
                restante = await teardown(camp_id, pers_id, sess_id)
                if restante != 0:
                    _log(f"[AVISO] teardown deixou count={restante} (esperado 0).")
            except Exception as e:  # noqa: BLE001
                _log(f"[ERRO] teardown falhou: {type(e).__name__}: {e}")
                _log(f"[ERRO] IDs da bolha p/ limpeza manual: "
                     f"campanha={camp_id} personagem={pers_id} sessao={sess_id}")
        else:
            _log("[teardown] nada criado (setup nao chegou a inserir) — nada a remover.")

    ok = a1 and a2
    _log(f"E2E PERSISTENCIA: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
