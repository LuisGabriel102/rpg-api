"""
Smoke test do Modulo 2: confirma que os SQLModel models geradas pelo
sqlacodegen funcionam contra o Neon Alderyn via async session.

Estrategia minimalista: testa apenas a classe Npcs (a tabela-foco do Modulo 2).
Se Npcs funciona, o pipeline inteiro esta validado e qualquer outra classe
do models.py funciona pelo mesmo molde. As outras 4 tabelas (Continents,
Regions, Locations, LocationNpcs) serao exercidas no Modulo 4.

Rodar: python test_models.py
"""

import asyncio
import warnings

# Silencia warnings cosmeticos do SQLModel sobre execute() vs exec()
warnings.filterwarnings('ignore', category=DeprecationWarning, module='sqlmodel')

from sqlmodel import select

from db import engine, get_session
from models import Npcs


async def main() -> None:
    print("Smoke test do Modulo 2: models reflectindo o banco real\n")

    async with get_session() as session:
        # Teste 1: SELECT COUNT pra confirmar conexao via ORM
        from sqlalchemy import func
        result = await session.exec(select(func.count()).select_from(Npcs))
        total = result.one()
        print(f"OK Total de NPCs no banco: {total}")

        # Teste 2: SELECT 3 NPCs e exibe campos relevantes
        statement = select(Npcs).limit(3)
        result = await session.exec(statement)
        npcs = result.all()

        if not npcs:
            print("\nAVISO: Nenhum NPC encontrado. Tabela esta vazia.")
            print("Nao e erro do Modulo 2 -- so significa que voce ainda")
            print("nao populou NPCs. O ORM funcionou.")
        else:
            print(f"\nOK Carregou {len(npcs)} NPC(s) via ORM:")
            for npc in npcs:
                epiteto = f' \"{npc.epiteto}\"' if npc.epiteto else ''
                print(f"\n  [{npc.id}] {npc.nome}{epiteto}")
                print(f"      Raca: {npc.raca} | Sexo: {npc.sexo or '?'} | Status: {npc.status}")
                print(f"      Camada narrativa: {npc.camada}")
                print(f"      Local atual: {npc.localizacao_atual or '?'}")
                if npc.facoes:
                    print(f"      Faccoes: {', '.join(npc.facoes)}")
                if npc.medo_principal:
                    print(f"      Medo principal: {npc.medo_principal}")

        # Teste 3: confirma que os campos type-safe funcionam (acesso direto a atributo)
        # Se o sqlacodegen tivesse gerado errado, isso quebraria com AttributeError
        if npcs:
            primeiro = npcs[0]
            assert isinstance(primeiro.id, int), "id deveria ser int"
            assert isinstance(primeiro.nome, str), "nome deveria ser str"
            assert isinstance(primeiro.camada, int), "camada deveria ser int"
            print("\nOK Type checking passou: campos chegam tipados corretamente.")

    await engine.dispose()
    print("\nModulo 2 OK. ORM funcionando contra o Neon Alderyn.")


if __name__ == '__main__':
    asyncio.run(main())