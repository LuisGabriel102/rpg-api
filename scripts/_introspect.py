import asyncio, selectors, warnings, logging
warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

async def main():
    from sqlalchemy import text
    from db import get_session
    async with get_session() as s:
        print("=== FUNCOES existentes ===")
        rows = await s.execute(text(
          "SELECT proname FROM pg_proc WHERE proname IN "
          "('fichaPersonagem','consultar_divida','montar_contexto_narrador',"
          "'get_contexto_enriquecido','iniciarSessao','get_estado_vitais') ORDER BY proname"))
        for r in rows: print(" FN:", r[0])

        print("=== COLUNAS vitais (hp/vida/mana/mp/vigor/fadiga/tensao/pressao) ===")
        rows = await s.execute(text(
          "SELECT table_name, column_name, data_type FROM information_schema.columns "
          "WHERE table_schema='public' AND column_name ~* "
          "'(^|_)(hp|vida|mana|mp|vigor|fadiga|tensao|pressao|stamina|fatigue)($|_)' "
          "ORDER BY table_name, column_name"))
        for r in rows: print(f"  {r[0]}.{r[1]} ({r[2]})")

        for tbl in ("sessoes", "sessao", "personagens", "combate_ativo"):
            rows = await s.execute(text(
              "SELECT column_name, data_type FROM information_schema.columns "
              "WHERE table_schema='public' AND table_name=:t ORDER BY ordinal_position"), {"t": tbl})
            cols = [(r[0], r[1]) for r in rows]
            if cols:
                print(f"=== COLUNAS {tbl} ===")
                for c, d in cols: print(f"  {tbl}.{c} ({d})")
            else:
                print(f"=== {tbl}: NAO EXISTE ===")

loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
loop.run_until_complete(main())
