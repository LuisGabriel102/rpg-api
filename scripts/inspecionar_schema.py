"""
Inspecao de schema das tabelas npc_* via db.py do Catedral.

Roda assim:
    python inspecionar_schema.py

Imprime no terminal todas as colunas das tabelas que importam pro
modulo 4.2 (detalhe NPC). Usa a conexao asyncpg/SQLAlchemy que ja
esta configurada — nao depende de pgAdmin nem de Neon Console.

Apos rodar, copia tudo do terminal e cola no chat.
"""

import asyncio
from sqlalchemy import text
from db import get_session


TABELAS_DE_INTERESSE = [
    "npc_secrets",
    "npc_goals",
    "npc_relationships",
    "npc_family",
    "npc_memories",
    "npc_knowledge",
    "npc_emotional_state",
    "npc_daily_routine",
    "location_npcs",
]


async def inspecionar() -> None:
    async with get_session() as session:
        result = await session.execute(text("""
            SELECT
                table_name,
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = ANY(:tabelas)
            ORDER BY table_name, ordinal_position
        """), {"tabelas": TABELAS_DE_INTERESSE})

        rows = result.mappings().all()

    if not rows:
        print("Nenhuma tabela encontrada. Schema vazio ou nomes errados.")
        return

    # Agrupa por tabela pra ficar legivel
    tabela_atual = None
    for r in rows:
        if r["table_name"] != tabela_atual:
            tabela_atual = r["table_name"]
            print(f"\n========== {tabela_atual} ==========")
        nullable = "NULL" if r["is_nullable"] == "YES" else "NOT NULL"
        print(f"  {r['column_name']:35s} {r['data_type']:25s} {nullable}")

    # Lista quais tabelas NAO foram encontradas (talvez tenham nomes diferentes)
    encontradas = {r["table_name"] for r in rows}
    faltando = set(TABELAS_DE_INTERESSE) - encontradas
    if faltando:
        print(f"\n!!! Tabelas NAO encontradas no banco: {sorted(faltando)}")
        print("Pode ser nome diferente. Vou procurar tabelas similares...")

        # Busca tabelas que comecem com "npc_"
        async with get_session() as session:
            result = await session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name LIKE 'npc_%'
                ORDER BY table_name
            """))
            todas_npc = [r[0] for r in result.all()]
        print(f"\nTabelas com prefixo 'npc_' no banco: {todas_npc}")


if __name__ == "__main__":
    asyncio.run(inspecionar())
