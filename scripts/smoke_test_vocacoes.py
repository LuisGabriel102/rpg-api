"""smoke_test_vocacoes.py - Valida as 3 classes novas."""
import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import func
from sqlmodel import select

from db import engine, get_session
from models import RefVocacoes, RefCaminhos, RefHabilidadesClasseNivel


async def main() -> None:
    print("=" * 76)
    print("  SMOKE TEST - Vocacoes")
    print("=" * 76)

    print("\n[1] Import OK:")
    print(f"    RefVocacoes.__tablename__              = {RefVocacoes.__tablename__!r}")
    print(f"    RefCaminhos.__tablename__              = {RefCaminhos.__tablename__!r}")
    print(f"    RefHabilidadesClasseNivel.__tablename__ = {RefHabilidadesClasseNivel.__tablename__!r}")

    async with get_session() as session:
        print("\n[2] Contagens:")
        t_voc = (await session.exec(select(func.count()).select_from(RefVocacoes))).one()
        t_cam = (await session.exec(select(func.count()).select_from(RefCaminhos))).one()
        t_hab = (await session.exec(select(func.count()).select_from(RefHabilidadesClasseNivel))).one()
        print(f"    Vocacoes:    {t_voc:>4d}  (esperado 126)")
        print(f"    Caminhos:    {t_cam:>4d}  (esperado 88)")
        print(f"    Habilidades: {t_hab:>4d}  (esperado 320)")

        assert t_voc == 126
        assert t_cam == 88
        assert t_hab == 320

        print("\n[3] Guerreiro (id=1) + seus caminhos:")
        guerreiro = (await session.exec(
            select(RefVocacoes).where(RefVocacoes.id == 1)
        )).one()
        print(f"    Nome:      {guerreiro.nome}")
        print(f"    Pilar:     {guerreiro.pilar}")
        print(f"    Tipo:      {guerreiro.tipo}")
        print(f"    Atribs:    {guerreiro.atributos_primarios}")
        print(f"    Diferencial: {guerreiro.diferencial_mecanico[:80]}...")

        caminhos_g = (await session.exec(
            select(RefCaminhos).where(RefCaminhos.vocacao_id == 1).order_by(RefCaminhos.id)
        )).all()
        print(f"\n    Caminhos do Guerreiro ({len(caminhos_g)}):")
        for c in caminhos_g:
            print(f"      - {c.nome}")

        print("\n[4] Distribuicao por pilar:")
        sql_pilar = (
            select(RefVocacoes.pilar, func.count())
            .group_by(RefVocacoes.pilar)
            .order_by(RefVocacoes.pilar)
        )
        result = await session.exec(sql_pilar)
        for pilar, n in result.all():
            marcador = "  <-- ANOMALIA" if pilar not in ("I", "II", "III", "IV", "V") else ""
            print(f"    pilar={pilar!r:>8s}  {n:>4d}{marcador}")

        print("\n[5] Distribuicao por tipo:")
        result = await session.exec(
            select(RefVocacoes.tipo, func.count())
            .group_by(RefVocacoes.tipo)
            .order_by(RefVocacoes.tipo)
        )
        for tipo, n in result.all():
            print(f"    tipo={tipo!r:>20s}  {n:>4d}")

        print("\n[6] Vocacoes com disponivel_escolha = FALSE:")
        result = await session.exec(
            select(RefVocacoes)
            .where(RefVocacoes.disponivel_escolha == False)
            .order_by(RefVocacoes.nome)
        )
        bloqueadas = result.all()
        print(f"    Total bloqueadas: {len(bloqueadas)}")
        for v in bloqueadas[:5]:
            print(f"      - {v.nome} (pilar {v.pilar}, tipo {v.tipo})")
        if len(bloqueadas) > 5:
            print(f"      ... + {len(bloqueadas) - 5} mais")

    await engine.dispose()
    print("\n" + "=" * 76)
    print("  [SMOKE TEST OK]")
    print("=" * 76)


if __name__ == "__main__":
    asyncio.run(main())