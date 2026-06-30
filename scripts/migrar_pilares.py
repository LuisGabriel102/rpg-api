"""
migrar_pilares.py - Migracao dos pilares romanos pra conceituais.

Ordem de operacoes (tudo em UMA transacao, rollback total se qualquer erro):
  1. CREATE TABLE ref_pilares (se nao existir)
  2. INSERT 5 pilares com filosofias
  3. Preview: mostra quem vai ser afetado (antes de mudar)
  4. UPDATE ref_vocacoes: I->corpo, II->sombra, III->arcano, IV->espirito, V->engenho
  5. Verifica: conta cada pilar depois, alerta se bateu alguma constraint
  6. COMMIT (ou ROLLBACK se --dry-run)

Uso:
  python migrar_pilares.py            # DRY RUN (nao escreve nada)
  python migrar_pilares.py --apply    # aplica de verdade
"""
import asyncio
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text as sql_text

from db import engine


# === Definicao dos 5 pilares ===
PILARES = [
    {
        "nome": "corpo",
        "epiteto": "A via da carne que resiste.",
        "filosofia": (
            "O corpo é a primeira arma e o último limite. Quem segue este "
            "pilar aprende pela experiência direta — pelo músculo cansado, "
            "pela respiração contada, pela distância medida em passos. Cada "
            "habilidade foi paga em suor, sangue ou cicatriz. O corpo ensina "
            "o que livro nenhum sabe, mas nunca ensina de graça."
        ),
    },
    {
        "nome": "sombra",
        "epiteto": "A via do que não se vê.",
        "filosofia": (
            "Viver na sombra é entender que o combate mais perigoso nunca "
            "começa de frente. Lâminas silenciosas, disfarces perfeitos, "
            "memórias alteradas — todos partilham a mesma disciplina: não "
            "ser notado até o instante em que importa. Quem segue este "
            "pilar estuda o silêncio como outros estudam o fogo."
        ),
    },
    {
        "nome": "arcano",
        "epiteto": "A via da palavra que altera.",
        "filosofia": (
            "O arcano é a linguagem secreta do que existe — a gramática "
            "oculta sob os eventos, as sílabas que precedem o mundo. Magos, "
            "feiticeiros e pactuados discordam sobre como pronunciá-las: "
            "uns estudam, outros herdam, outros negociam. Mas todos "
            "reconhecem a mesma verdade: há regras por trás do real, e "
            "algumas podem ser ditas em voz alta."
        ),
    },
    {
        "nome": "espirito",
        "epiteto": "A via dos que servem.",
        "filosofia": (
            "Nada no Alderyn está verdadeiramente só. Deuses silenciosos, "
            "espíritos ancestrais, natureza que lembra — todos têm voz, e "
            "alguns escolhem falar. Quem segue este pilar se ata a algo "
            "maior: escuta humildemente ou impõe com juramento, mas nunca "
            "age sozinho. A força não vem do indivíduo — vem do pacto "
            "firmado, da ancestralidade ouvida, ou do voto sustentado."
        ),
    },
    {
        "nome": "engenho",
        "epiteto": "A via da mente que constrói.",
        "filosofia": (
            "O engenho é o pilar dos que recusam o mundo como ele é. "
            "Artífices forjam máquinas, psionicistas moldam o pensamento, "
            "alquimistas transformam matéria, estrategistas movem exércitos "
            "como peças. A crença é a mesma: a realidade cede a quem "
            "insiste o suficiente. Mas o preço também é o mesmo — o "
            "engenho desgasta quem o exerce, e cada construção cobra algo "
            "de seu construtor."
        ),
    },
]

# Mapeamento romano -> conceitual
ROMANO_PARA_CONCEITUAL = {
    "I":   "corpo",
    "II":  "sombra",
    "III": "arcano",
    "IV":  "espirito",
    "V":   "engenho",
}

# Mapeamento pilares-palavra existentes (Pugilista+filhas) -> conceitual
# ATENCAO: 'tecnico' -> 'engenho' pra alinhar com decisao
# ATENCAO: 'sagrado' -> 'espirito' pra alinhar com decisao
PALAVRA_PARA_CONCEITUAL = {
    "corpo":   "corpo",   # ja ok
    "sombra":  "sombra",  # ja ok
    "arcano":  "arcano",  # ja ok
    "sagrado": "espirito",  # realinhamento
    "tecnico": "engenho",   # realinhamento
}


async def main(apply: bool) -> int:
    modo = "APLICANDO" if apply else "DRY RUN (nada sera escrito)"
    print("=" * 76)
    print(f"  MIGRACAO DOS PILARES - Modo: {modo}")
    print("=" * 76)

    async with engine.begin() as conn:

        # === 1. Criar tabela ref_pilares ===
        print("\n[1] Criando tabela ref_pilares (se nao existir)...")
        await conn.execute(sql_text("""
            CREATE TABLE IF NOT EXISTS ref_pilares (
                nome TEXT PRIMARY KEY,
                epiteto TEXT NOT NULL,
                filosofia TEXT NOT NULL,
                criado_em TIMESTAMP DEFAULT now()
            )
        """))
        print("    OK")

        # === 2. Inserir os 5 pilares (ON CONFLICT para idempotencia) ===
        print("\n[2] Inserindo os 5 pilares...")
        for p in PILARES:
            await conn.execute(
                sql_text("""
                    INSERT INTO ref_pilares (nome, epiteto, filosofia)
                    VALUES (:nome, :epiteto, :filosofia)
                    ON CONFLICT (nome) DO UPDATE
                        SET epiteto = EXCLUDED.epiteto,
                            filosofia = EXCLUDED.filosofia
                """),
                p
            )
            print(f"    + {p['nome']}")

        # === 3. Preview do estado atual ===
        print("\n[3] Estado ANTES da migracao:")
        result = await conn.execute(sql_text("""
            SELECT pilar, COUNT(*) as n
            FROM ref_vocacoes
            GROUP BY pilar
            ORDER BY pilar
        """))
        antes = {r[0]: r[1] for r in result.fetchall()}
        for pilar, n in sorted(antes.items()):
            print(f"    {pilar!r:15s} {n:>4d}")

        # === 4. Aplicar UPDATEs ===
        print("\n[4] Aplicando migracoes em ref_vocacoes...")

        # 4a: romanos -> conceituais
        for romano, conceitual in ROMANO_PARA_CONCEITUAL.items():
            result = await conn.execute(
                sql_text(
                    "UPDATE ref_vocacoes SET pilar = :novo "
                    "WHERE pilar = :velho"
                ),
                {"novo": conceitual, "velho": romano},
            )
            n = result.rowcount
            print(f"    {romano!r:5s} -> {conceitual!r:10s}  ({n} linhas)")

        # 4b: sagrado -> espirito, tecnico -> engenho (realinhamentos)
        for palavra, conceitual in PALAVRA_PARA_CONCEITUAL.items():
            if palavra == conceitual:
                continue
            result = await conn.execute(
                sql_text(
                    "UPDATE ref_vocacoes SET pilar = :novo "
                    "WHERE pilar = :velho"
                ),
                {"novo": conceitual, "velho": palavra},
            )
            n = result.rowcount
            print(f"    {palavra!r:10s} -> {conceitual!r:10s}  ({n} linhas)")

        # === 5. Preview do estado novo ===
        print("\n[5] Estado DEPOIS da migracao:")
        result = await conn.execute(sql_text("""
            SELECT pilar, COUNT(*) as n
            FROM ref_vocacoes
            GROUP BY pilar
            ORDER BY pilar
        """))
        depois = {r[0]: r[1] for r in result.fetchall()}
        for pilar, n in sorted(depois.items()):
            marcador = ""
            if pilar in ("corpo", "sombra", "arcano", "espirito", "engenho"):
                marcador = "  [OK]"
            elif pilar == "Fundida":
                marcador = "  [Grupo D - nao tocado]"
            else:
                marcador = "  <-- INESPERADO"
            print(f"    {pilar!r:15s} {n:>4d}{marcador}")

        # === 6. Validacao ===
        print("\n[6] Validacao de integridade:")
        total_antes = sum(antes.values())
        total_depois = sum(depois.values())
        print(f"    Total antes:  {total_antes}")
        print(f"    Total depois: {total_depois}")
        assert total_antes == total_depois == 126, "Total mudou!"
        print("    Total preservado em 126. OK.")

        # Checa se alguma vocacao ficou com pilar invalido
        validos_esperados = set(["corpo", "sombra", "arcano", "espirito",
                                  "engenho", "Fundida"])
        pilares_restantes = set(depois.keys())
        invalidos = pilares_restantes - validos_esperados
        if invalidos:
            print(f"    [ATENCAO] Pilares inesperados: {invalidos}")
        else:
            print("    Todos os pilares batem com o esperado.")

        # === 7. COMMIT ou ROLLBACK ===
        if apply:
            print("\n[7] Aplicando COMMIT...")
            # engine.begin() faz commit automatico ao sair do bloco
        else:
            print("\n[7] DRY RUN - fazendo ROLLBACK...")
            await conn.rollback()

    await engine.dispose()

    print("\n" + "=" * 76)
    if apply:
        print("  [OK] MIGRACAO APLICADA COM SUCESSO")
    else:
        print("  [DRY RUN] Nada foi escrito. Rode com --apply pra aplicar.")
    print("=" * 76)
    return 0


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    sys.exit(asyncio.run(main(apply)))