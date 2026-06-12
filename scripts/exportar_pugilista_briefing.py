"""exportar_pugilista_briefing.py - Gera briefing completo do Pugilista."""
import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlmodel import select
from db import engine, get_session
from models import RefVocacoes, RefCaminhos, RefHabilidadesClasseNivel


async def main() -> None:
    async with get_session() as session:
        voc = (await session.exec(
            select(RefVocacoes).where(RefVocacoes.id == 114)
        )).first()

        caminhos = (await session.exec(
            select(RefCaminhos).where(RefCaminhos.vocacao_id == 114)
        )).all()

        habs = (await session.exec(
            select(RefHabilidadesClasseNivel).where(
                RefHabilidadesClasseNivel.vocacao_id == 114
            )
        )).all()

    out = []
    out.append("=" * 76)
    out.append("  VOCACAO-MODELO: PUGILISTA (Alderyn-native completa)")
    out.append("=" * 76)
    out.append(f"\nNome: {voc.nome_ptbr}")
    out.append(f"Pilar: {voc.pilar}")
    out.append(f"Tipo: {voc.tipo}")
    out.append(f"Atributos: {voc.atributos_primarios}")
    out.append(f"\nDescricao:\n{voc.descricao}")
    out.append(f"\nDiferencial mecanico:\n{voc.diferencial_mecanico}")

    out.append(f"\n\n=== CAMINHOS / SUBCLASSES ({len(caminhos)}) ===")
    for c in caminhos:
        nome = getattr(c, 'nome_ptbr', None) or getattr(c, 'nome', '?')
        desc = getattr(c, 'descricao', '') or ''
        out.append(f"\n- {nome}")
        out.append(f"  {desc}")

    out.append(f"\n\n=== HABILIDADES POR NIVEL ({len(habs)}) ===")
    habs_sorted = sorted(habs, key=lambda h: (h.nivel or 0, h.nome or ''))
    for h in habs_sorted:
        out.append(f"\nN{h.nivel} - {h.nome}")
        desc = getattr(h, 'descricao', '') or ''
        out.append(f"  {desc}")
        maestria = getattr(h, 'gera_maestria', False)
        if maestria:
            out.append(f"  [GERA MAESTRIA (sistema ANIMA)]")

    texto = "\n".join(out)

    # Grava em arquivo pra facilitar copy-paste
    with open("briefing_pugilista_modelo.txt", "w", encoding="utf-8") as f:
        f.write(texto)

    print(texto)
    print("\n\n" + "=" * 76)
    print("  Salvo em: briefing_pugilista_modelo.txt")
    print("=" * 76)


if __name__ == "__main__":
    asyncio.run(main())