"""listar_51_ambiguas.py - Extrai a lista canonica das 51 fundidas ambiguas."""
import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlmodel import select

from db import engine, get_session
from models import RefVocacoes


async def main() -> None:
    async with get_session() as session:
        todas = (await session.exec(select(RefVocacoes))).all()
        nome_pra_pilar = {v.nome_ptbr: v.pilar for v in todas}
        for v in todas:
            if v.nome != v.nome_ptbr:
                nome_pra_pilar.setdefault(v.nome, v.pilar)

        fundidas = (await session.exec(
            select(RefVocacoes)
            .where(RefVocacoes.pilar == "Fundida")
            .order_by(RefVocacoes.id)
        )).all()

    obvias = []
    ambiguas = []

    for f in fundidas:
        origens = f.vocacoes_origem or []
        if len(origens) < 2:
            continue
        p1 = nome_pra_pilar.get(origens[0])
        p2 = nome_pra_pilar.get(origens[1])
        if p1 is None or p2 is None:
            continue
        if p1 == p2:
            obvias.append((f, p1, origens))
        else:
            ambiguas.append((f, p1, p2, origens))

    print("=" * 76)
    print(f"  LISTA CANONICA")
    print("=" * 76)
    print(f"\n  Total obvias: {len(obvias)}")
    print(f"  Total ambiguas: {len(ambiguas)}")

    print(f"\n{'=' * 76}")
    print(f"  OBVIAS ({len(obvias)}) - completa (sera fix automatico):")
    print("=" * 76)
    for f, p, origens in sorted(obvias, key=lambda x: x[0].id):
        print(f"  [{f.id:3d}] {f.nome_ptbr:35s} -> {p:10s} ({origens[0]} + {origens[1]})")

    print(f"\n{'=' * 76}")
    print(f"  AMBIGUAS ({len(ambiguas)}) - precisa decisao manual:")
    print("=" * 76)
    for f, p1, p2, origens in sorted(ambiguas, key=lambda x: x[0].id):
        print(f"  [{f.id:3d}] {f.nome_ptbr:35s} {origens[0]}({p1}) + {origens[1]}({p2})")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())