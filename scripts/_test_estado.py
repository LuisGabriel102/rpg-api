import asyncio, selectors, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.WARNING)

_SQL_ESTADO = (
    "SELECT s.data_narrativa_inicio AS data, s.personagem_id AS pid, "
    "p.nome, p.classe_primaria AS classe, p.nivel, p.hp_atual, p.hp_maximo, "
    "p.status_narrativo AS status, m.mp_atual, m.mp_maximo, "
    "(SELECT ce.local_atual_desc FROM campanha_estado_atual ce "
    " WHERE ce.campanha_id = s.campanha_id LIMIT 1) AS local, "
    "(SELECT string_agg(a.nome, ', ') FROM personagem_aliados_ativos a "
    " WHERE a.sessao_id = s.id) AS companheiros, "
    "(SELECT c.estado FROM combate_ativo c WHERE c.sessao_id = s.id "
    " ORDER BY c.criado_em DESC LIMIT 1) AS combate "
    "FROM sessoes s "
    "LEFT JOIN personagens p ON p.id = s.personagem_id "
    "LEFT JOIN personagem_mana m ON m.personagem_id = s.personagem_id "
    "WHERE s.id = :sid"
)

async def montar(sessao_id, pressao_atual):
    from db import get_session
    from sqlalchemy import text
    linhas = [f"pressao_emocional: {pressao_atual}"]
    try:
        async with get_session() as s:
            row = (await s.execute(text(_SQL_ESTADO), {"sid": sessao_id})).mappings().first()
            if row:
                if row["data"]:  linhas.append(f"data: {row['data']}")
                if row["local"]: linhas.append(f"local: {row['local']}")
                if row["nome"]:
                    ident = row["nome"]
                    extra = ", ".join(x for x in (
                        row["classe"],
                        f"nivel {row['nivel']}" if row["nivel"] is not None else None) if x)
                    if extra:  ident += f" ({extra})"
                    if row["status"]: ident += f" — {row['status']}"
                    linhas.append(f"personagem: {ident}")
                if row["hp_atual"] is not None and row["hp_maximo"] is not None:
                    linhas.append(f"vida: {row['hp_atual']}/{row['hp_maximo']}")
                if row["mp_atual"] is not None and row["mp_maximo"] is not None:
                    linhas.append(f"mana: {row['mp_atual']}/{row['mp_maximo']}")
                linhas.append(f"companheiros: {row['companheiros'] or 'nenhum'}")
                linhas.append(f"combate: {row['combate'] or 'inativo'}")
                pid = row["pid"]
                if pid is not None:
                    try:
                        d = (await s.execute(text("SELECT consultar_divida(:pid) AS d"),
                                             {"pid": pid})).scalar()
                        if d:
                            tier_nome = (d.get("tier_info") or {}).get("nome_tier")
                            ld = f"divida: {d.get('divida_viva', 0)} (tier {d.get('divida_tier', 0)}"
                            if tier_nome: ld += f" — {tier_nome}"
                            ld += f"), conviccao: {d.get('conviccao', 0)}"
                            linhas.append(ld)
                    except Exception as exc:
                        print(f"[estado] divida falhou: {type(exc).__name__}: {exc}")
    except Exception as exc:
        print(f"[estado] FALHA: {type(exc).__name__}: {exc}")
    bloco = "[ESTADO]\n" + "\n".join(linhas)
    assert "\n\n" not in bloco, "bloco tem \\n\\n interno (quebraria _texto_do_jogador)!"
    return bloco

async def main():
    for sid, label in ((7, "sessao 7 = Varekhor id 8"), (2, "sessao 2 = binding vivo /jogar")):
        print(f"########## {label} ##########")
        print(await montar(sid, 3))
        print()

loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
loop.run_until_complete(main())
