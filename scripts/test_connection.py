"""
Smoke test do Modulo 1: confirma que a Oficina conecta no Neon Alderyn.

Rodar: python test_connection.py
"""

import asyncio

from sqlalchemy import text

from db import engine, get_session


async def main() -> None:
    print("Testando conexao com Neon Alderyn...\n")

    async with get_session() as session:
        # 1. Teste minimo: o engine consegue executar query?
        result = await session.execute(text("SELECT 1"))
        valor = result.scalar()
        print(f"OK SELECT 1 = {valor}")

        # 2. Versao do Postgres (confirma que e o Neon real respondendo)
        result = await session.execute(text("SELECT version()"))
        versao = result.scalar()
        print(f"OK Postgres: {versao}")

        # 3. Sanity check do schema: deve ter 154 tabelas (conforme handoff)
        result = await session.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            )
        )
        n_tabelas = result.scalar()
        print(f"OK Tabelas no schema public: {n_tabelas}")

        if n_tabelas != 154:
            print(
                f"\nAVISO: Esperado 154 tabelas (handoff), encontrado {n_tabelas}. "
                "Nao e erro fatal -- pode ter sido criado/removido tabela desde "
                "o handoff. Anota e confere depois."
            )

    # Importante: fechar o engine no fim de scripts standalone.
    await engine.dispose()
    print("\nModulo 1 OK. Conexao estabelecida.")


if __name__ == "__main__":
    asyncio.run(main())