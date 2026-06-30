"""
investigar_anomalias_pilar.py - Lista todas as vocacoes com pilar nao-romano.

Agrupa por pilar anomalo. Para cada vocacao mostra: nome, tipo, disponivel,
atributos, vocacoes_origem (se fundida). Ajuda a decidir reclassificacao.
"""
import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import func
from sqlmodel import select

from db import engine, get_session
from models import RefVocacoes


PILARES_VALIDOS = ("I", "II", "III", "IV", "V")


async def main() -> None:
    print("=" * 76)
    print("  INVESTIGACAO - Anomalias de pilar em ref_vocacoes")
    print("=" * 76)

    async with get_session() as session:
        # Busca todas com pilar nao-romano
        result = await session.exec(
            select(RefVocacoes)
            .where(RefVocacoes.pilar.notin_(PILARES_VALIDOS))
            .order_by(RefVocacoes.pilar, RefVocacoes.nome)
        )
        anomalias = list(result.all())

    print(f"\n  Total de anomalias: {len(anomalias)}")

    # Agrupa por pilar
    por_pilar: dict[str, list] = {}
    for v in anomalias:
        por_pilar.setdefault(v.pilar, []).append(v)

    # Resumo de contagem
    print("\n  Resumo por pilar anomalo:")
    for pilar in sorted(por_pilar.keys()):
        vocs = por_pilar[pilar]
        n_base = sum(1 for v in vocs if v.tipo == "base")
        n_fund = sum(1 for v in vocs if v.tipo == "fundida")
        n_bloq = sum(1 for v in vocs if v.disponivel_escolha is False)
        print(
            f"    {pilar!r:12s}  total={len(vocs):3d}  "
            f"base={n_base}  fundida={n_fund}  bloqueadas={n_bloq}"
        )

    # Detalhamento por pilar
    for pilar in sorted(por_pilar.keys()):
        vocs = por_pilar[pilar]
        print(f"\n{'=' * 76}")
        print(f"  PILAR = {pilar!r}  ({len(vocs)} vocacoes)")
        print("=" * 76)

        for v in vocs:
            bloq_str = " [BLOQUEADA]" if v.disponivel_escolha is False else ""
            print(f"\n  [{v.id:3d}] {v.nome}{bloq_str}")
            print(f"       tipo={v.tipo}  atribs={v.atributos_primarios}")
            if v.vocacoes_origem:
                print(f"       origem={v.vocacoes_origem}")
            if v.diferencial_mecanico:
                print(f"       {v.diferencial_mecanico[:100]}")

        # Se o grupo for muito grande (pilar='Fundida' tem 73), trunca
        if len(vocs) > 15:
            print(f"\n  [... {len(vocs)} total; mostrou todas acima]")

    await engine.dispose()

    print("\n" + "=" * 76)
    print("  FIM")
    print("=" * 76)


if __name__ == "__main__":
    asyncio.run(main())