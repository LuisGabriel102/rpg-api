import asyncio, selectors, warnings, logging, json
warnings.filterwarnings("ignore"); logging.disable(logging.WARNING)

async def main():
    from sqlalchemy import text
    from db import get_session
    async with get_session() as s:
        async def one(label, sql, p=None):
            try:
                r = await s.execute(text(sql), p or {})
                rows = r.fetchall()
                print(f"--- {label} ---")
                if not rows: print("  (vazio)"); return
                keys = r.keys()
                for row in rows[:3]:
                    print("  " + ", ".join(f"{k}={v}" for k, v in zip(keys, row)))
            except Exception as e:
                print(f"--- {label}: ERRO {type(e).__name__}: {str(e)[:120]}")

        print("=== consultar_divida assinatura ===")
        try:
            r = await s.execute(text("SELECT pg_get_function_arguments(oid), pg_get_function_result(oid) FROM pg_proc WHERE proname='consultar_divida'"))
            for row in r: print("  args:", row[0], "\n  ret:", row[1])
        except Exception as e: print("  ERRO", e)

        await one("personagens id=8", "SELECT id,nome,raca,classe_primaria,nivel,hp_atual,hp_maximo,divida_viva,divida_tier,conviccao,veretheos_comprehendido,status_narrativo FROM personagens WHERE id=8")
        await one("personagem_mana id=8", "SELECT personagem_id,mp_atual,mp_maximo,mp_temporario FROM personagem_mana WHERE personagem_id=8")
        await one("personagem_saude_mental id=8", "SELECT * FROM personagem_saude_mental WHERE personagem_id=8")
        await one("sessoes do personagem 8", "SELECT id,numero_sessao,personagem_id,data_narrativa_inicio,data_narrativa_fim,status FROM sessoes WHERE personagem_id=8 ORDER BY id")
        await one("sessao id=2", "SELECT id,personagem_id,data_narrativa_inicio,status FROM sessoes WHERE id=2")
        await one("aliados ativos id=8", "SELECT personagem_id,nome_aliado,hp_atual,hp_max FROM personagem_aliados_ativos WHERE personagem_id=8")
        await one("combate_ativo sessao 2", "SELECT id,estado,rodada_atual,local_id FROM combate_ativo WHERE sessao_id=2")
        print("=== colunas com local/regiao/localizacao ===")
        r = await s.execute(text("SELECT table_name,column_name FROM information_schema.columns WHERE table_schema='public' AND column_name ~* '(local|regiao|localizacao|cenario)' ORDER BY table_name,column_name"))
        for row in r: print(f"  {row[0]}.{row[1]}")
        print("=== consultar_divida(8) resultado ===")
        try:
            r = await s.execute(text("SELECT * FROM consultar_divida(8)"))
            rows=r.fetchall(); keys=r.keys()
            for row in rows[:2]: print("  "+", ".join(f"{k}={v}" for k,v in zip(keys,row)))
            if not rows: print("  (vazio)")
        except Exception as e: print("  ERRO", type(e).__name__, str(e)[:150])

loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
loop.run_until_complete(main())
