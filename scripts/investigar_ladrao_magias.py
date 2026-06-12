"""investigar_ladrao_magias.py - Estado completo da vocacao id 99."""
import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlmodel import select

from db import engine, get_session
from models import RefVocacoes, RefCaminhos, RefHabilidadesClasseNivel


async def main() -> None:
    async with get_session() as session:
        # 1. Dados basicos da vocacao
        voc = (await session.exec(
            select(RefVocacoes).where(RefVocacoes.id == 99)
        )).first()

        if not voc:
            print("ERRO: vocacao id 99 nao encontrada")
            return

        print("=" * 76)
        print(f"  VOCACAO ID 99 - ESTADO ATUAL")
        print("=" * 76)
        print(f"\n  Nome (EN): {voc.nome}")
        print(f"  Nome (PT): {voc.nome_ptbr}")
        print(f"  Pilar:     {voc.pilar}")
        print(f"  Tipo:      {voc.tipo}")
        print(f"  Atribs:    {voc.atribs}")
        print(f"  Origens:   {voc.vocacoes_origem}")
        print(f"  Disponivel: {voc.disponivel}")
        print(f"\n  Descricao:")
        print(f"  {voc.descricao or '(vazio)'}")
        print(f"\n  Diferencial mecanico:")
        print(f"  {voc.diferencial_mecanico or '(vazio)'}")

        # 2. Caminhos desta vocacao
        caminhos = (await session.exec(
            select(RefCaminhos).where(RefCaminhos.vocacao_id == 99)
        )).all()
        print(f"\n  Caminhos/subclasses: {len(caminhos)}")
        for c in caminhos:
            print(f"    - {c.nome_ptbr or c.nome}")

        # 3. Habilidades por nivel
        habs = (await session.exec(
            select(RefHabilidadesClasseNivel).where(
                RefHabilidadesClasseNivel.vocacao_id == 99
            )
        )).all()
        print(f"\n  Habilidades por nivel: {len(habs)}")

        # 4. Outras fundidas que apontam pra "Ladrao de Magias"
        todas = (await session.exec(select(RefVocacoes))).all()
        referencias = [
            v for v in todas
            if v.id != 99 and v.vocacoes_origem
            and "Ladrão de Magias" in v.vocacoes_origem
        ]
        print(f"\n  Fundidas que apontam pra 'Ladrao de Magias': {len(referencias)}")
        for r in referencias:
            print(f"    [{r.id}] {r.nome_ptbr}")

        # 5. Verificar se ha maior id livre para novo INSERT
        max_id = max(v.id for v in todas)
        print(f"\n  Maior ID atual na tabela: {max_id}")
        print(f"  Proximo ID livre: {max_id + 1}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())