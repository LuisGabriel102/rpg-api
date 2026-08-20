import asyncio, selectors, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.WARNING)

async def main():
    from sqlalchemy import text
    from db import get_session

    async def q(label, sql, p=None):
        # sessao nova por query -> erro nao envenena as demais
        async with get_session() as s:
            try:
                r = await s.execute(text(sql), p or {})
                rows = r.fetchall(); keys = r.keys()
                print(f"--- {label} ---")
                if not rows: print("  (vazio)"); return
                for row in rows[:4]:
                    print("  " + ", ".join(f"{k}={v}" for k, v in zip(keys, row)))
            except Exception as e:
                print(f"--- {label}: ERRO {type(e).__name__}: {str(e)[:140]}")

    await q("local/regiao/localizacao cols",
        "SELECT table_name,column_name FROM information_schema.columns WHERE table_schema='public' AND column_name ~* '(^|_)(local|regiao|localizacao|cenario|lugar)($|_)' ORDER BY table_name,column_name")
    await q("personagem_aliados_ativos cols",
        "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='personagem_aliados_ativos' ORDER BY ordinal_position")
    await q("aliados do personagem 8",
        "SELECT * FROM personagem_aliados_ativos WHERE personagem_id=8")
    await q("combate_ativo da sessao 7",
        "SELECT id,estado,rodada_atual,local_id FROM combate_ativo WHERE sessao_id=7")
    await q("consultar_divida(8)", "SELECT consultar_divida(8) AS d")
    await q("fichaPersonagem(8)", 'SELECT * FROM "fichaPersonagem"(8)')

loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
loop.run_until_complete(main())
