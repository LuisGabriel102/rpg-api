"""
investigar_bases_sem_caminhos.py - Descobre quais bases nao tem caminhos.

Para cada base sem caminhos, mostra: nome, pilar, atributos, numero de
habilidades mapeadas, diferencial mecanico (primeiros 120 chars).

Adicionalmente: mostra a distribuicao "numero de caminhos por base" pra
contexto (as 40 bases, quantos caminhos cada uma tem).
"""
import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import func, text as sql_text
from sqlmodel import select

from db import engine, get_session
from models import RefVocacoes, RefCaminhos, RefHabilidadesClasseNivel


async def main() -> None:
    print("=" * 76)
    print("  INVESTIGACAO - Vocacoes base sem caminhos")
    print("=" * 76)

    async with get_session() as session:
        # === 1. Quantas bases tem no total ===
        total_bases = (await session.exec(
            select(func.count()).select_from(RefVocacoes)
            .where(RefVocacoes.tipo == "base")
        )).one()
        print(f"\n  Total de vocacoes base: {total_bases}")

        # === 2. Distribuicao: quantos caminhos por base ===
        print("\n[1] Distribuicao - numero de caminhos por base:")
        sql = sql_text("""
            SELECT v.nome_ptbr, v.pilar,
                COUNT(c.id) AS n_caminhos
            FROM ref_vocacoes v
            LEFT JOIN ref_caminhos c ON c.vocacao_id = v.id
            WHERE v.tipo = 'base'
            GROUP BY v.id, v.nome_ptbr, v.pilar
            ORDER BY n_caminhos ASC, v.pilar, v.nome_ptbr
        """)
        rows = (await session.exec(sql)).all()

        contagem_por_n = {}
        for r in rows:
            contagem_por_n[r[2]] = contagem_por_n.get(r[2], 0) + 1

        print(f"    {'n_caminhos':12s} {'qtd_bases':10s}")
        for n in sorted(contagem_por_n.keys()):
            marcador = "  <-- atencao" if n == 0 else ""
            print(f"    {n:>10d}   {contagem_por_n[n]:>6d}{marcador}")

        # === 3. As bases sem caminhos ===
        sem_caminhos = [r for r in rows if r[2] == 0]
        print(f"\n[2] Bases com ZERO caminhos ({len(sem_caminhos)}):")

        if not sem_caminhos:
            print("    Nenhuma.")
        else:
            for nome, pilar, _ in sem_caminhos:
                print(f"    - {nome}  (pilar {pilar})")

        # === 4. Detalhes de cada base sem caminhos ===
        if sem_caminhos:
            print(f"\n[3] Detalhamento:")
            for nome, pilar, _ in sem_caminhos:
                voc = (await session.exec(
                    select(RefVocacoes).where(RefVocacoes.nome_ptbr == nome)
                )).first()

                if not voc:
                    continue

                # Conta habilidades por nivel dessa vocacao
                n_habs = (await session.exec(
                    select(func.count()).select_from(RefHabilidadesClasseNivel)
                    .where(RefHabilidadesClasseNivel.vocacao_id == voc.id)
                )).one()

                print(f"\n  [{voc.id:3d}] {voc.nome_ptbr}")
                print(f"         pilar: {voc.pilar}  tipo: {voc.tipo}")
                print(f"         atribs: {voc.atributos_primarios}")
                print(f"         disponivel: {voc.disponivel_escolha}")
                print(f"         habilidades mapeadas: {n_habs}")
                if voc.diferencial_mecanico:
                    dif = voc.diferencial_mecanico[:130]
                    if len(voc.diferencial_mecanico) > 130:
                        dif += "..."
                    print(f"         diferencial: {dif}")
                if voc.descricao:
                    desc = voc.descricao[:130]
                    if len(voc.descricao) > 130:
                        desc += "..."
                    print(f"         descricao: {desc}")

        # === 5. Top 3 bases com mais caminhos (pra comparacao) ===
        top = [r for r in rows if r[2] >= 4]
        if top:
            print(f"\n[4] Bases com 4+ caminhos (pra comparacao):")
            for nome, pilar, n in top:
                print(f"    {nome:30s} pilar {pilar}  ({n} caminhos)")

    await engine.dispose()

    print("\n" + "=" * 76)
    print("  FIM")
    print("=" * 76)


if __name__ == "__main__":
    asyncio.run(main())