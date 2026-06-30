"""patch_filosofias_ui.py - Mostra filosofias dos pilares na UI de vocacoes."""
from pathlib import Path
import sys

MODELS = Path("models.py")
MAIN = Path("main.py")

# === 1. Classe SQLModel RefPilares ===
MODELS_SENTINELA = "class RefPilares(SQLModel"
MODELS_NOVA = '''


# === PILARES (Modulo 6.4) ===

class RefPilares(SQLModel, table=True):
    __tablename__ = 'ref_pilares'
    __table_args__ = (
        PrimaryKeyConstraint('nome', name='ref_pilares_pkey'),
    )

    nome: str = Field(sa_column=Column('nome', Text, primary_key=True))
    epiteto: str = Field(sa_column=Column('epiteto', Text, nullable=False))
    filosofia: str = Field(sa_column=Column('filosofia', Text, nullable=False))
    criado_em: Optional[datetime.datetime] = Field(default=None, sa_column=Column('criado_em', DateTime, server_default=text('now()')))
'''

# === 2. Import em main.py ===
MAIN_IMPORT_OLD = "from models import Npcs, RefEstrelasNascimento, RefHabilidadesEstrela, RefVocacoes, RefCaminhos, RefHabilidadesClasseNivel"
MAIN_IMPORT_NEW = "from models import Npcs, RefEstrelasNascimento, RefHabilidadesEstrela, RefVocacoes, RefCaminhos, RefHabilidadesClasseNivel, RefPilares"

# === 3. Adicionar helper + card na tela ===
MAIN_SENTINELA = "async def _buscar_filosofia_pilar"

HELPER_ANCORA = "async def _contar_vocacoes_total() -> int:"

HELPER_NOVO = '''async def _buscar_filosofia_pilar(nome: str) -> dict | None:
    """Busca epiteto + filosofia de um pilar. Retorna None se nao existir."""
    async with get_session() as session:
        result = await session.exec(
            select(RefPilares).where(RefPilares.nome == nome)
        )
        p = result.first()
        if not p:
            return None
        return {
            "nome": p.nome,
            "epiteto": p.epiteto,
            "filosofia": p.filosofia,
        }


'''

# === 4. Adicionar card de filosofia na tela + handler reativo ===
# Ancora: logo apos as 3 rows de filtros, antes do separator
CARD_OLD = '''        ui.separator().classes("bg-zinc-700")

        # === Tabela ==='''

CARD_NEW = '''        # === Card de filosofia do pilar (reativo) ===
        filosofia_container = ui.column().classes("w-full")

        async def atualizar_filosofia() -> None:
            filosofia_container.clear()
            nome = filtros_state["pilar"]
            if nome not in ("corpo", "sombra", "arcano", "espirito", "engenho"):
                return
            data = await _buscar_filosofia_pilar(nome)
            if not data:
                return
            with filosofia_container:
                with ui.card().classes(
                    "w-full bg-zinc-800 border border-amber-800 p-4"
                ).props("flat"):
                    with ui.row().classes("items-baseline gap-3"):
                        ui.label(data["nome"]).classes(
                            "text-xl font-bold text-amber-200 uppercase tracking-wider"
                        )
                        ui.label(data["epiteto"]).classes(
                            "text-sm text-zinc-400 italic"
                        )
                    ui.label(data["filosofia"]).classes(
                        "text-sm text-zinc-300 italic leading-relaxed mt-2"
                    )

        # Substitui refresh pra tambem atualizar filosofia
        _refresh_original = refresh

        async def refresh_com_filosofia() -> None:
            await _refresh_original()
            await atualizar_filosofia()

        # Sobrescreve os setters dos filtros
        def set_filtro_pilar_v2(valor: str) -> None:
            filtros_state["pilar"] = valor
            asyncio.create_task(refresh_com_filosofia())

        set_filtro_pilar = set_filtro_pilar_v2  # noqa: F811

        ui.separator().classes("bg-zinc-700")

        # === Tabela ==='''


def patch_models() -> bool:
    c = MODELS.read_text(encoding="utf-8")
    if MODELS_SENTINELA in c:
        print("  [IDEMPOTENTE] RefPilares ja existe em models.py")
        return False
    novo = c.rstrip() + MODELS_NOVA + "\n"
    MODELS.write_text(novo, encoding="utf-8")
    print("  [OK] RefPilares adicionado em models.py")
    return True


def patch_main() -> bool:
    c = MAIN.read_text(encoding="utf-8")

    if MAIN_SENTINELA in c:
        print("  [IDEMPOTENTE] main.py ja tem _buscar_filosofia_pilar")
        return False

    # 1. Import
    if MAIN_IMPORT_OLD not in c:
        print("  [ERRO] Import antigo nao encontrado")
        return False
    c = c.replace(MAIN_IMPORT_OLD, MAIN_IMPORT_NEW, 1)
    print("  [1] Import +RefPilares")

    # 2. Helper antes de _contar_vocacoes_total
    if HELPER_ANCORA not in c:
        print("  [ERRO] Ancora helper nao encontrada")
        return False
    c = c.replace(HELPER_ANCORA, HELPER_NOVO + HELPER_ANCORA, 1)
    print("  [2] _buscar_filosofia_pilar adicionado")

    # 3. Card + handler reativo
    if CARD_OLD not in c:
        print("  [ERRO] Ancora do card nao encontrada")
        return False
    c = c.replace(CARD_OLD, CARD_NEW, 1)
    print("  [3] Card de filosofia + handler reativo adicionados")

    MAIN.write_text(c, encoding="utf-8")
    return True


def main() -> int:
    print("=" * 72)
    print("  PATCH - Filosofias dos pilares na UI")
    print("=" * 72)

    patch_models()
    print()
    patch_main()

    print("=" * 72)
    print("  [OK] Patch aplicado.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())