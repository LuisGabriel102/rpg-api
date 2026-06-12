"""aplicar_mecanica_2_vocacoes.py - Aplica os 2 SQLs do outro chat."""
import asyncio
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text
from db import engine

APPLY = "--apply" in sys.argv
SQLS = ["ladino_arcano_mecanica.sql", "devorador_grimorios_mecanica.sql"]


async def main() -> None:
    modo = "APLICANDO" if APPLY else "DRY RUN"
    print("=" * 76)
    print(f"  APLICAR MECANICA - Ladino Arcano + Devorador - {modo}")
    print("=" * 76)

    for sql_file in SQLS:
        path = Path(sql_file)
        if not path.exists():
            print(f"\n[ERRO] {sql_file} nao encontrado em {path.absolute()}")
            return

        print(f"\n>>> {sql_file} ({path.stat().st_size} bytes)")
        sql_text = path.read_text(encoding="utf-8")

        async with engine.begin() as conn:
            # Estado antes
            voc_id = 99 if "ladino" in sql_file else 128
            r = await conn.execute(text(f"""
                SELECT
                  (SELECT COUNT(*) FROM ref_caminhos WHERE vocacao_id={voc_id}) AS c,
                  (SELECT COUNT(*) FROM ref_habilidades_classe_nivel WHERE vocacao_id={voc_id}) AS h
            """))
            antes = r.first()
            print(f"    ANTES: caminhos={antes[0]} habilidades={antes[1]}")

            # Executa o SQL inteiro
            # NOTA: o SQL ja tem BEGIN/COMMIT, mas SQLAlchemy gerencia transacao,
            # entao removo as palavras BEGIN/COMMIT do texto antes de executar
            sql_clean = sql_text.replace("BEGIN;", "").replace("COMMIT;", "")
            # Executa statement por statement (split por ;)
            statements = [s.strip() for s in sql_clean.split(";") if s.strip() and not s.strip().startswith("--")]
            print(f"    Executando {len(statements)} statements...")
            for stmt in statements:
                await conn.execute(text(stmt))

            # Estado depois
            r = await conn.execute(text(f"""
                SELECT
                  (SELECT COUNT(*) FROM ref_caminhos WHERE vocacao_id={voc_id}) AS c,
                  (SELECT COUNT(*) FROM ref_habilidades_classe_nivel WHERE vocacao_id={voc_id}) AS h,
                  (SELECT COUNT(*) FROM ref_habilidades_classe_nivel WHERE vocacao_id={voc_id} AND gera_maestria=true) AS m
            """))
            depois = r.first()
            print(f"    DEPOIS: caminhos={depois[0]} habilidades={depois[1]} maestria={depois[2]}")
            print(f"    Esperado: caminhos=6 habilidades=22 maestria=8")

            if depois[0] != 6 or depois[1] != 22 or depois[2] != 8:
                raise Exception(f"VALIDACAO FALHOU: {sql_file}")

            if not APPLY:
                raise Exception("ROLLBACK_DRY_RUN")

    print("\n" + "=" * 76)
    print(f"  [OK] {modo} CONCLUIDO")
    print("=" * 76)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        if "ROLLBACK_DRY_RUN" in str(e):
            print("\n" + "=" * 76)
            print("  [DRY RUN] Nada foi escrito. Rode com --apply.")
            print("=" * 76)
        else:
            print(f"\n[ERRO] {e}")
            raise