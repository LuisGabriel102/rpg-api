import asyncio, selectors, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.WARNING)

async def main():
    from sqlalchemy import text
    from db import get_session
    async with get_session() as s:
        print("=== world_facts: colunas relevantes ===")
        for r in await s.execute(text(
          "SELECT column_name, data_type, udt_name FROM information_schema.columns "
          "WHERE table_schema='public' AND table_name='world_facts' "
          "AND column_name IN ('fact_id','fact_text','embedding') ORDER BY column_name")):
            print(f"  world_facts.{r[0]} ({r[1]} / {r[2]})")
        print("=== contagem embeddings ===")
        for r in await s.execute(text(
          "SELECT count(*) total, count(*) FILTER (WHERE embedding IS NOT NULL) com_vec, "
          "count(*) FILTER (WHERE fact_text IS NOT NULL AND fact_text<>'') com_texto FROM world_facts")):
            print(f"  total={r[0]}  com_embedding={r[1]}  com_texto={r[2]}")
        print("=== indices em world_facts (HNSW/ivfflat?) ===")
        for r in await s.execute(text(
          "SELECT indexname, indexdef FROM pg_indexes WHERE tablename='world_facts'")):
            print(f"  {r[0]}: {r[1]}")
        print("=== def de montar_contexto_narrador ===")
        try:
            r = await s.execute(text(
              "SELECT pg_get_functiondef(oid) FROM pg_proc WHERE proname='montar_contexto_narrador' LIMIT 1"))
            body = r.scalar()
            print(body)
        except Exception as e:
            print("  ERRO:", type(e).__name__, str(e)[:160])

loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
loop.run_until_complete(main())
