"""dividir_ladrao_magias.py - Divide id 99 em Ladino Arcano + Devorador de Grimorios."""
import asyncio
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text
from db import engine, get_session

APPLY = "--apply" in sys.argv

LADINO_DESC = (
    "Um ladrao que aprendeu magia como aprende gazua ou veneno: por necessidade. "
    "Nao e mago - e alguem que precisava de chave magica pra portas que nao abriam "
    "com ferramenta. Os feiticos dele sao poucos, praticos, e sempre a servico do "
    "oficio. Invisibilidade pra entrar onde nao devia. Fechaduras sensiveis a abrir. "
    "Palavras que confundem guardas. A magia e so mais um item no cinto dele - e "
    "como todo bom ladrao, ele escolhe os itens com cuidado."
)

LADINO_DIFF = (
    "Conhece feiticos de nivel 0-4 de qualquer lista (max 8 feiticos). Usa furtividade "
    "como atributo de conjuracao. Pode 'bolsinhar' um feitico de alvo magico em combate "
    "(1x por longo descanso). Grimorio pequeno, escondido, peso desprezivel."
)

DEVORADOR_DESC = (
    "Ha magica nas palavras escritas, e ha magica no que nao se le. Este nao estuda - "
    "devora. Encosta os dedos na pagina, os olhos na lombada, e algo dentro da cabeca "
    "dele come o feitico como fome come pao. Outros pagam pra aprender magia. Este pega. "
    "Do vivo, do morto, do pergaminho, da memoria alheia. O problema e que nunca para de "
    "ter fome - cada feitico devorado pede dois mais, e o cerebro comeca a caber menos "
    "da propria vida dele."
)

DEVORADOR_DIFF = (
    "Pode 'devorar' feiticos de grimorios, pergaminhos ou mentes inimigas (ritual de "
    "10min sobre o alvo). Adiciona o feitico a propria lista permanentemente. Limite: "
    "INT + nivel. A cada 5 feiticos devorados, perde 1 ponto de atributo mental "
    "(efeito cumulativo, irreversivel). Grimorio-cerebro: nao precisa carregar livro."
)


async def main() -> None:
    modo = "APLICANDO" if APPLY else "DRY RUN"
    print("=" * 76)
    print(f"  DIVISAO DO LADRAO DE MAGIAS - {modo}")
    print("=" * 76)

    async with engine.begin() as conn:
        # 1. UPDATE id 99 -> Ladino Arcano
        print("\n[1] UPDATE id 99 -> Ladino Arcano (sombra)")
        await conn.execute(text("""
            UPDATE ref_vocacoes
            SET nome = :nome,
                nome_ptbr = :nome,
                pilar = 'sombra',
                tipo = 'base',
                vocacoes_origem = NULL,
                descricao = :desc,
                diferencial_mecanico = :diff,
                disponivel_escolha = TRUE
            WHERE id = 99
        """), {
            "nome": "Ladino Arcano",
            "desc": LADINO_DESC,
            "diff": LADINO_DIFF,
        })
        print("    OK")

        # 2. INSERT id 128 -> Devorador de Grimorios
        print("\n[2] INSERT id 128 -> Devorador de Grimorios (arcano)")
        await conn.execute(text("""
            INSERT INTO ref_vocacoes
                (id, nome, nome_ptbr, pilar, tipo, vocacoes_origem,
                 descricao, diferencial_mecanico, disponivel_escolha, criado_em)
            VALUES
                (:id, :nome, :nome, 'arcano', 'base', NULL,
                 :desc, :diff, TRUE, NOW())
        """), {
            "id": 128,
            "nome": "Devorador de Grimórios",
            "desc": DEVORADOR_DESC,
            "diff": DEVORADOR_DIFF,
        })
        print("    OK")

        # 3. Validacao: contar quantas vocacoes em sombra e arcano
        print("\n[3] Validacao:")
        result = await conn.execute(text("""
            SELECT pilar, COUNT(*) as n
            FROM ref_vocacoes
            WHERE pilar IN ('sombra', 'arcano')
            GROUP BY pilar
            ORDER BY pilar
        """))
        for row in result:
            print(f"    {row[0]:10s}  {row[1]}")

        total = await conn.execute(text("SELECT COUNT(*) FROM ref_vocacoes"))
        total_n = total.scalar()
        print(f"\n    Total vocacoes: {total_n} (esperado: 127 apos divisao)")

        if not APPLY:
            print("\n[4] DRY RUN - fazendo ROLLBACK")
            raise Exception("ROLLBACK_DRY_RUN")

    print("\n" + "=" * 76)
    print(f"  [OK] DIVISAO APLICADA")
    print("=" * 76)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        if "ROLLBACK_DRY_RUN" in str(e):
            print("\n" + "=" * 76)
            print("  [DRY RUN] Nada foi escrito. Rode com --apply pra aplicar.")
            print("=" * 76)
        else:
            raise