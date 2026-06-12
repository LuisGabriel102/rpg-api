"""ver_pugilista.py - Ve o Pugilista completo (id 114)."""
import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlmodel import select

from db import engine, get_session
from models import RefVocacoes, RefCaminhos, RefHabilidadesClasseNivel


async def main() -> None:
    print("=" * 76)
    print("  PUGILISTA - Vocacao-laboratorio do Alderyn")
    print("=" * 76)

    async with get_session() as session:
        voc = (await session.exec(
            select(RefVocacoes).where(RefVocacoes.id == 114)
        )).first()

        if not voc:
            print("  [ERRO] Pugilista (id 114) nao encontrado.")
            return

        print(f"\n  Nome: {voc.nome_ptbr}  (id {voc.id})")
        print(f"  Pilar: {voc.pilar}  |  Tipo: {voc.tipo}")
        print(f"  Atribs: {voc.atributos_primarios}")
        print(f"  Disponivel: {voc.disponivel_escolha}")
        print(f"\n  Descricao:")
        print(f"    {voc.descricao}")
        print(f"\n  Diferencial Mecanico:")
        print(f"    {voc.diferencial_mecanico}")

        # === 6 Caminhos ===
        caminhos = (await session.exec(
            select(RefCaminhos)
            .where(RefCaminhos.vocacao_id == 114)
            .order_by(RefCaminhos.id)
        )).all()

        print(f"\n{'=' * 76}")
        print(f"  {len(caminhos)} CAMINHOS DO PUGILISTA")
        print("=" * 76)
        for i, c in enumerate(caminhos, 1):
            print(f"\n  [{i}] {c.nome_ptbr}  (nivel {c.nivel_desbloqueio})")
            print(f"      {c.descricao}")

        # === Habilidades ===
        habs = (await session.exec(
            select(RefHabilidadesClasseNivel)
            .where(RefHabilidadesClasseNivel.vocacao_id == 114)
            .order_by(
                RefHabilidadesClasseNivel.nivel,
                RefHabilidadesClasseNivel.nome,
            )
        )).all()

        print(f"\n{'=' * 76}")
        print(f"  HABILIDADES POR NIVEL ({len(habs)})")
        print("=" * 76)

        nivel_atual = None
        for h in habs:
            if h.nivel != nivel_atual:
                nivel_atual = h.nivel
                print(f"\n  Nivel {nivel_atual}:")
            maestria = " [MAESTRIA]" if h.gera_maestria else ""
            caminho = " [REQUER CAMINHO]" if h.requer_caminho else ""
            print(f"    - {h.nome_ptbr} ({h.tipo}){maestria}{caminho}")
            desc = h.descricao[:150]
            if len(h.descricao) > 150:
                desc += "..."
            print(f"      {desc}")

    await engine.dispose()
    print("\n" + "=" * 76)
    print("  FIM")
    print("=" * 76)


if __name__ == "__main__":
    asyncio.run(main())