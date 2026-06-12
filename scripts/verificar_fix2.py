"""Verificacao precisa do FIX 2 ignorando linhas de comentario."""
import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text
from db import engine


async def main() -> None:
    async with engine.connect() as conn:
        sql = text("""
            SELECT pg_get_functiondef(oid)
            FROM pg_proc
            WHERE proname = 'evoluir_habilidade_astral'
              AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname='public')
        """)
        row = (await conn.execute(sql)).fetchone()
        codigo = row[0]

        # Separa comentarios de codigo ativo
        linhas_codigo = []
        linhas_comentario = []
        for linha in codigo.split("\n"):
            if linha.strip().startswith("--"):
                linhas_comentario.append(linha)
            else:
                linhas_codigo.append(linha)

        corpo = "\n".join(linhas_codigo)

        tem_fix_novo = "4 - v_astro.habilidade_categoria" in corpo
        tem_bug_velho = "habilidade_categoria + 1" in corpo

        print("=" * 60)
        print("VERIFICACAO PRECISA DO FIX 2")
        print("=" * 60)
        print(f"Linhas de codigo:      {len(linhas_codigo)}")
        print(f"Linhas de comentario:  {len(linhas_comentario)}")
        print()
        print("No CODIGO ATIVO (ignorando comentarios):")
        print(f"  Contem '4 - v_astro.habilidade_categoria':  {tem_fix_novo}")
        print(f"  Contem 'habilidade_categoria + 1' (velho):  {tem_bug_velho}")
        print()

        if tem_fix_novo and not tem_bug_velho:
            print("[OK] FIX 2 confirmado no codigo ativo.")
        elif tem_bug_velho and not tem_fix_novo:
            print("[ERRO] FIX 2 NAO foi aplicado — ainda tem o bug.")
        else:
            print("[ALERTA] Estado inesperado, inspecione manualmente.")

        print()
        print("--- LINHA CRITICA (a condicao do IF) ---")
        for linha in linhas_codigo:
            if "grau_atual" in linha and ">=" in linha:
                print(f"  {linha.strip()}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())