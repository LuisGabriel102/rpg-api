"""investigar_ladrao_magias_v2.py - Versao sem atributo atribs."""
import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlmodel import select

from db import engine, get_session
from models import RefVocacoes, RefCaminhos, RefHabilidadesClasseNivel


async def main() -> None:
    async with get_session() as session:
        voc = (await session.exec(
            select(RefVocacoes).where(RefVocacoes.id == 99)
        )).first()

        if not voc:
            print("ERRO: vocacao id 99 nao encontrada")
            return

        print("=" * 76)
        print(f"  VOCACAO ID 99 - ESTADO COMPLETO")
        print("=" * 76)

        # Dump de todos os atributos disponiveis (pra descobrir os nomes reais)
        print(f"\n  Campos disponiveis no modelo:")
        for campo, valor in voc.__dict__.items():
            if campo.startswith("_"):
                continue
            val_str = str(valor) if valor is not None else "(None)"
            if len(val_str) > 100:
                val_str = val_str[:100] + "..."
            print(f"    {campo:25s} = {val_str}")

        # Caminhos
        caminhos = (await session.exec(
            select(RefCaminhos).where(RefCaminhos.vocacao_id == 99)
        )).all()
        print(f"\n  Caminhos/subclasses: {len(caminhos)}")
        for c in caminhos:
            nome = getattr(c, 'nome_ptbr', None) or getattr(c, 'nome', '?')
            print(f"    - {nome}")

        # Habilidades
        habs = (await session.exec(
            select(RefHabilidadesClasseNivel).where(
                RefHabilidadesClasseNivel.vocacao_id == 99
            )
        )).all()
        print(f"\n  Habilidades por nivel: {len(habs)}")

        # Referencias
        todas = (await session.exec(select(RefVocacoes))).all()
        referencias = [
            v for v in todas
            if v.id != 99 and v.vocacoes_origem
            and "Ladrão de Magias" in v.vocacoes_origem
        ]
        print(f"\n  Fundidas que apontam pra 'Ladrao de Magias': {len(referencias)}")
        for r in referencias:
            print(f"    [{r.id}] {r.nome_ptbr}")

        max_id = max(v.id for v in todas)
        print(f"\n  Maior ID atual: {max_id}")
        print(f"  Proximo ID livre: {max_id + 1}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())