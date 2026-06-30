"""
smoke_test_estrelas.py - Valida que as 2 novas classes funcionam.

Etapa 1:
  1. Import limpo
  2. Conta linhas (esperado: 12 estrelas, 1200 habilidades)
  3. Le MARKA (id=1) e sua lendaria (d100=100)
  4. Le todas as 12 estrelas ordenadas por id
"""
import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import func
from sqlmodel import select

from db import engine, get_session
from models import RefEstrelasNascimento, RefHabilidadesEstrela


async def main() -> None:
    print("=" * 72)
    print("  SMOKE TEST - Estrelas do Veu")
    print("=" * 72)

    # --- Teste 1: import funcionou ---
    print("\n[1] Import OK:")
    print(f"    RefEstrelasNascimento.__tablename__ = {RefEstrelasNascimento.__tablename__!r}")
    print(f"    RefHabilidadesEstrela.__tablename__ = {RefHabilidadesEstrela.__tablename__!r}")

    async with get_session() as session:
        # --- Teste 2: contagens ---
        print("\n[2] Contagens:")
        total_estrelas = (await session.exec(
            select(func.count()).select_from(RefEstrelasNascimento)
        )).one()
        total_habs = (await session.exec(
            select(func.count()).select_from(RefHabilidadesEstrela)
        )).one()
        print(f"    Estrelas:    {total_estrelas:>5d}  (esperado 12)")
        print(f"    Habilidades: {total_habs:>5d}  (esperado 1200)")

        assert total_estrelas == 12, f"Esperado 12 estrelas, achou {total_estrelas}"
        assert total_habs == 1200, f"Esperado 1200 habilidades, achou {total_habs}"

        # --- Teste 3: MARKA + sua lendaria ---
        print("\n[3] MARKA (id=1) + sua lendaria:")
        marka = (await session.exec(
            select(RefEstrelasNascimento).where(RefEstrelasNascimento.id == 1)
        )).one()
        print(f"    Nome:     {marka.nome}")
        print(f"    Epiteto:  {marka.epiteto}")
        print(f"    Lema:     {marka.lema}")
        print(f"    Temas:    {marka.tema_central[:60]}...")
        print(f"    Atribs:   {marka.atributos_primarios}")
        print(f"    Dist:     cat1={marka.pct_primeira_cat}%  cat2={marka.pct_segunda_cat}%  cat3={marka.pct_terceira_cat}%")
        print(f"    Lendaria: {marka.habilidade_100_nome}")

        lendaria_marka = (await session.exec(
            select(RefHabilidadesEstrela)
            .where(RefHabilidadesEstrela.estrela_id == 1)
            .where(RefHabilidadesEstrela.numero_d100 == 100)
        )).one()
        print(f"\n    Lendaria (da tabela habilidades):")
        print(f"      id={lendaria_marka.id}  categoria={lendaria_marka.categoria}  tem_preco={lendaria_marka.tem_preco}")
        print(f"      nome: {lendaria_marka.nome}")
        print(f"      desc: {lendaria_marka.descricao_completa[:120]}...")

        # --- Teste 4: todas as 12 estrelas ---
        print("\n[4] Todas as 12 estrelas:")
        todas = (await session.exec(
            select(RefEstrelasNascimento).order_by(RefEstrelasNascimento.id)
        )).all()
        for e in todas:
            cats = f"{e.pct_primeira_cat:2d}/{e.pct_segunda_cat:2d}/{e.pct_terceira_cat:2d}"
            print(f"    [{e.id:2d}] {e.nome:10s} - {e.epiteto:15s} ({e.atributos_primarios:12s}) cats {cats}")

    await engine.dispose()

    print("\n" + "=" * 72)
    print("  [SMOKE TEST OK] As 2 classes estao prontas pra usar na Etapa 2.")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(main())