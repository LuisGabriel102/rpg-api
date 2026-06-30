"""
investigar_grupo_d.py - Mapeia as 73 fundidas com pilar='Fundida'.

Pra cada uma: busca os pilares dos 2 pais e classifica:
  OBVIA    = ambos pais no mesmo pilar (sem ambiguidade)
  AMBIGUA  = pais em pilares diferentes (precisa regra)
  ORFA     = algum pai nao existe no banco (nome errado)
  SOLO     = menos de 2 pais (caso estranho)

No final, imprime resumo + lista completa.
"""
import asyncio
import warnings
from collections import Counter, defaultdict

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlmodel import select

from db import engine, get_session
from models import RefVocacoes


async def main() -> None:
    print("=" * 76)
    print("  INVESTIGACAO DO GRUPO D - 73 fundidas com pilar='Fundida'")
    print("=" * 76)

    async with get_session() as session:
        # Busca TODAS as vocacoes com nome -> pilar (pra lookup)
        todas = (await session.exec(select(RefVocacoes))).all()
        nome_pra_pilar = {v.nome_ptbr: v.pilar for v in todas}
        # Tambem tenta nome em ingles (nome) pra robustez
        for v in todas:
            if v.nome != v.nome_ptbr:
                nome_pra_pilar.setdefault(v.nome, v.pilar)

        # Busca as fundidas com pilar='Fundida'
        fundidas = (await session.exec(
            select(RefVocacoes)
            .where(RefVocacoes.pilar == "Fundida")
            .order_by(RefVocacoes.nome_ptbr)
        )).all()

    print(f"\n  Total de fundidas em Grupo D: {len(fundidas)}")

    # Classifica cada uma
    obvias = []       # ambos pais no mesmo pilar
    ambiguas = []     # pais em pilares diferentes
    orfas = []        # algum pai nao encontrado no banco
    solos = []        # menos de 2 pais

    for f in fundidas:
        origens = f.vocacoes_origem or []
        if len(origens) < 2:
            solos.append((f, origens))
            continue

        pai1_nome = origens[0]
        pai2_nome = origens[1]
        pai1_pilar = nome_pra_pilar.get(pai1_nome)
        pai2_pilar = nome_pra_pilar.get(pai2_nome)

        if pai1_pilar is None or pai2_pilar is None:
            orfas.append((f, origens, pai1_pilar, pai2_pilar))
        elif pai1_pilar == pai2_pilar:
            obvias.append((f, pai1_pilar, pai1_nome, pai2_nome))
        else:
            ambiguas.append((f, pai1_pilar, pai2_pilar, pai1_nome, pai2_nome))

    # === Resumo ===
    print(f"\n  Classificacao:")
    print(f"    OBVIAS  (pais mesmo pilar):        {len(obvias):>3d}")
    print(f"    AMBIGUAS (pais pilares diferentes): {len(ambiguas):>3d}")
    print(f"    ORFAS   (pai nao encontrado):      {len(orfas):>3d}")
    print(f"    SOLOS   (<2 pais):                 {len(solos):>3d}")

    # === 1. OBVIAS - distribuicao por pilar ===
    if obvias:
        print(f"\n{'=' * 76}")
        print(f"  OBVIAS ({len(obvias)}) - distribuicao:")
        print("=" * 76)
        dist_obvias = Counter(pilar for _, pilar, _, _ in obvias)
        for pilar, n in sorted(dist_obvias.items()):
            print(f"    {pilar:12s}  {n:>3d}")

        print(f"\n  Amostra (5 primeiras):")
        for f, pilar, p1, p2 in obvias[:5]:
            print(f"    [{f.id:3d}] {f.nome_ptbr:30s}  -> {pilar}  ({p1} + {p2})")
        if len(obvias) > 5:
            print(f"    [... mais {len(obvias) - 5}]")

    # === 2. AMBIGUAS - casos-limite ===
    if ambiguas:
        print(f"\n{'=' * 76}")
        print(f"  AMBIGUAS ({len(ambiguas)}) - casos limite:")
        print("=" * 76)

        # Conta combinacoes (pilar1, pilar2) mais comuns
        combos = defaultdict(list)
        for f, p1, p2, nome1, nome2 in ambiguas:
            par = tuple(sorted((p1, p2)))
            combos[par].append(f.nome_ptbr)

        print(f"\n  Combinacoes de pilares:")
        for par, nomes in sorted(combos.items(), key=lambda x: -len(x[1])):
            print(f"    {par[0]:10s} + {par[1]:10s}  -> {len(nomes)} fundidas")

        print(f"\n  Lista completa:")
        for f, p1, p2, nome1, nome2 in ambiguas:
            print(f"    [{f.id:3d}] {f.nome_ptbr:30s}  "
                  f"{nome1}({p1}) + {nome2}({p2})")

    # === 3. ORFAS ===
    if orfas:
        print(f"\n{'=' * 76}")
        print(f"  ORFAS ({len(orfas)}) - pais nao encontrados no banco:")
        print("=" * 76)
        for f, origens, p1, p2 in orfas:
            status = []
            if p1 is None:
                status.append(f"{origens[0]} (NAO EXISTE)")
            else:
                status.append(f"{origens[0]} ({p1})")
            if p2 is None:
                status.append(f"{origens[1]} (NAO EXISTE)")
            else:
                status.append(f"{origens[1]} ({p2})")
            print(f"    [{f.id:3d}] {f.nome_ptbr}: {' + '.join(status)}")

    # === 4. SOLOS ===
    if solos:
        print(f"\n{'=' * 76}")
        print(f"  SOLOS ({len(solos)}) - menos de 2 pais:")
        print("=" * 76)
        for f, origens in solos:
            print(f"    [{f.id:3d}] {f.nome_ptbr}: origens={origens}")

    await engine.dispose()

    print("\n" + "=" * 76)
    print("  FIM")
    print("=" * 76)


if __name__ == "__main__":
    asyncio.run(main())