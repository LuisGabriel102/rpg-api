"""
patch_main_vocacoes.py - Etapa 2 de vocacoes: /oficina/vocacoes tabela paginada.

Mudancas:
  1. Import: adiciona RefVocacoes (as outras 2 ficam pra quando forem usadas)
  2. Insere helpers + rota antes do MOUNT
  3. Adiciona card de Vocacoes na home (terceiro card)

Idempotente via sentinela "def pagina_vocacoes".
"""
from pathlib import Path
import sys

MAIN = Path("main.py")
SENTINELA = "def pagina_vocacoes"

IMPORT_ANTIGO = "from models import Npcs, RefEstrelasNascimento, RefHabilidadesEstrela"
IMPORT_NOVO = "from models import Npcs, RefEstrelasNascimento, RefHabilidadesEstrela, RefVocacoes"

ANCORA = "# MOUNT NICEGUI NO APP FASTAPI"

# --- Novo card de Vocacoes na home (insere depois do card de Estrelas) ---
HOME_OLD = '''                ui.label(
                    "Clique aqui pra ver os 12 astros, da Forja ao Trono."
                ).classes("text-zinc-600 text-sm")'''

HOME_NEW = '''                ui.label(
                    "Clique aqui pra ver os 12 astros, da Forja ao Trono."
                ).classes("text-zinc-600 text-sm")

            # --- Card: Vocacoes ---
            with ui.card().classes(
                "flex-1 min-w-[280px] bg-zinc-800 border border-zinc-700 p-6 "
                "cursor-pointer hover:border-amber-700 transition-colors"
            ).on("click", lambda: ui.navigate.to("/oficina/vocacoes")):
                with ui.row().classes("w-full items-center justify-between"):
                    with ui.column().classes("gap-1"):
                        ui.label("Vocações").classes(
                            "text-sm uppercase tracking-wider text-zinc-400"
                        )
                        ui.label(str(total_vocacoes)).classes(
                            "text-6xl font-bold text-amber-200"
                        )
                    ui.icon("shield", size="2rem").classes("text-zinc-500")

                ui.label("Classes e multiclasses narradas.").classes(
                    "text-zinc-400 mt-4"
                )
                ui.label(
                    "40 bases, 86 fundidas, 5 pilares — e anomalias a descobrir."
                ).classes("text-zinc-600 text-sm")'''

# --- Buscar total_vocacoes na home (depois de total_estrelas) ---
HOME_TOTAL_OLD = """    total_npcs = await _contar_npcs_total()
    total_estrelas = await _contar_estrelas_total()
"""
HOME_TOTAL_NEW = """    total_npcs = await _contar_npcs_total()
    total_estrelas = await _contar_estrelas_total()
    total_vocacoes = await _contar_vocacoes_total()
"""

# --- Bloco principal: helpers + rota ---
NOVO_BLOCO = '''# ====================================================================
# === VOCACOES - ROTAS (Módulo 6.2) ===
# ====================================================================

_VOC_SORTABLE_FIELDS = {"id", "nome_ptbr", "pilar", "tipo"}
_PILARES_ROMANOS = ("I", "II", "III", "IV", "V")
_PILARES_VALIDOS = _PILARES_ROMANOS + ("Fundida",)


async def _contar_vocacoes_total() -> int:
    """Conta total de vocacoes (usado no card da home)."""
    async with get_session() as session:
        result = await session.exec(
            select(func.count()).select_from(RefVocacoes)
        )
        return result.one()


async def _buscar_pagina_vocacoes(
    page: int,
    rows_per_page: int,
    sort_by: str,
    descending: bool,
    filtro_pilar: str = "todos",
    filtro_tipo: str = "todos",
    filtro_disponivel: str = "todos",
    busca_nome: str = "",
) -> tuple[list[dict], int]:
    """
    Busca pagina de vocacoes com filtros.

    filtro_pilar: "todos", "I", "II", "III", "IV", "V", "Fundida", "anomalias"
    filtro_tipo: "todos", "base", "fundida"
    filtro_disponivel: "todos", "disponiveis", "bloqueadas"
    busca_nome: termo de busca em nome_ptbr (case-insensitive)
    """
    if sort_by not in _VOC_SORTABLE_FIELDS:
        sort_by = "id"

    skip = max(0, (page - 1) * rows_per_page)

    # Constroi filtros dinamicamente
    filtros = []
    if filtro_pilar == "anomalias":
        filtros.append(RefVocacoes.pilar.notin_(_PILARES_VALIDOS))
    elif filtro_pilar != "todos":
        filtros.append(RefVocacoes.pilar == filtro_pilar)

    if filtro_tipo != "todos":
        filtros.append(RefVocacoes.tipo == filtro_tipo)

    if filtro_disponivel == "disponiveis":
        filtros.append(RefVocacoes.disponivel_escolha == True)
    elif filtro_disponivel == "bloqueadas":
        filtros.append(RefVocacoes.disponivel_escolha == False)

    if busca_nome:
        filtros.append(RefVocacoes.nome_ptbr.ilike(f"%{busca_nome}%"))

    async with get_session() as session:
        count_stmt = select(func.count()).select_from(RefVocacoes)
        for f in filtros:
            count_stmt = count_stmt.where(f)
        total = (await session.exec(count_stmt)).one()

        sort_col = getattr(RefVocacoes, sort_by)
        order_expr = sort_col.desc() if descending else sort_col.asc()

        stmt = select(RefVocacoes)
        for f in filtros:
            stmt = stmt.where(f)
        stmt = stmt.order_by(order_expr).offset(skip).limit(rows_per_page)

        result = await session.exec(stmt)
        vocs = result.all()

    rows = []
    for v in vocs:
        is_anomalia = v.pilar not in _PILARES_VALIDOS
        pilar_display = v.pilar if not is_anomalia else f"\u26a0 {v.pilar}"
        disp = "[OK]" if v.disponivel_escolha else "[BLOQ]"
        atribs = "/".join(v.atributos_primarios) if v.atributos_primarios else "-"
        rows.append({
            "id": v.id,
            "nome_ptbr": v.nome_ptbr,
            "pilar": pilar_display,
            "tipo": v.tipo,
            "atribs": atribs,
            "disponivel": disp,
        })

    return rows, total


@ui.page("/oficina/vocacoes")
async def pagina_vocacoes():
    """Lista paginada das 126 vocacoes com filtros."""
    filtros_state = {
        "pilar": "todos",
        "tipo": "todos",
        "disponivel": "todos",
        "busca": "",
    }

    pagination_state = {
        "rowsPerPage": 25,
        "rowsNumber": 0,
        "page": 1,
        "sortBy": "id",
        "descending": False,
    }

    rows_iniciais, total = await _buscar_pagina_vocacoes(
        page=1, rows_per_page=25, sort_by="id", descending=False,
    )
    pagination_state["rowsNumber"] = total

    columns = [
        {"name": "id", "label": "ID", "field": "id", "sortable": True, "align": "left"},
        {"name": "nome_ptbr", "label": "Nome", "field": "nome_ptbr", "sortable": True, "align": "left"},
        {"name": "pilar", "label": "Pilar", "field": "pilar", "sortable": True, "align": "left"},
        {"name": "tipo", "label": "Tipo", "field": "tipo", "sortable": True, "align": "left"},
        {"name": "atribs", "label": "Atribs", "field": "atribs", "sortable": False, "align": "left"},
        {"name": "disponivel", "label": "Disp.", "field": "disponivel", "sortable": False, "align": "center"},
    ]

    table_ref: dict = {"widget": None}
    counter_ref: dict = {"widget": None}

    async def refresh() -> None:
        if not table_ref["widget"]:
            return
        pag = dict(table_ref["widget"].pagination)
        rows, total_atual = await _buscar_pagina_vocacoes(
            page=pag.get("page", 1),
            rows_per_page=pag.get("rowsPerPage", 25),
            sort_by=pag.get("sortBy") or "id",
            descending=pag.get("descending", False),
            filtro_pilar=filtros_state["pilar"],
            filtro_tipo=filtros_state["tipo"],
            filtro_disponivel=filtros_state["disponivel"],
            busca_nome=filtros_state["busca"],
        )
        pag["rowsNumber"] = total_atual
        pag["page"] = 1  # reset pra primeira pagina ao filtrar
        table_ref["widget"].rows = rows
        table_ref["widget"].pagination = pag
        table_ref["widget"].update()
        if counter_ref["widget"]:
            counter_ref["widget"].set_text(
                f"{total_atual} vocação(ões) filtrada(s) de 126 total"
            )

    def set_filtro_pilar(valor: str) -> None:
        filtros_state["pilar"] = valor
        asyncio.create_task(refresh())

    def set_filtro_tipo(valor: str) -> None:
        filtros_state["tipo"] = valor
        asyncio.create_task(refresh())

    def set_filtro_disponivel(valor: str) -> None:
        filtros_state["disponivel"] = valor
        asyncio.create_task(refresh())

    def set_busca(e) -> None:
        filtros_state["busca"] = (e.value or "").strip()
        asyncio.create_task(refresh())

    with ui.column().classes(
        "w-full min-h-screen bg-zinc-900 text-zinc-100 p-8 gap-4"
    ):
        # === Header ===
        with ui.row().classes("w-full items-center justify-between"):
            with ui.row().classes("items-center gap-3"):
                ui.button(
                    icon="arrow_back",
                    on_click=lambda: ui.navigate.to("/oficina"),
                ).props("flat round dense color=amber-2")
                with ui.column().classes("gap-0"):
                    ui.label("Vocações do Alderyn").classes(
                        "text-3xl font-bold text-amber-200"
                    )
                    counter_ref["widget"] = ui.label(
                        f"{total} vocação(ões) filtrada(s) de 126 total"
                    ).classes("text-sm text-zinc-400 italic")

        ui.separator().classes("bg-zinc-700")

        # === Filtros ===
        with ui.column().classes("w-full gap-2"):
            # Busca por nome
            ui.input(
                label="Buscar por nome",
                placeholder="Guerreiro, Arcano-Lâmina, Pugilista...",
                on_change=set_busca,
            ).classes("w-full max-w-md").props("dense dark outlined clearable")

            # Filtro Pilar
            with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                ui.label("Pilar:").classes("text-xs uppercase text-zinc-500")
                for opcao, label in [
                    ("todos", "Todos"),
                    ("I", "I"), ("II", "II"), ("III", "III"), ("IV", "IV"), ("V", "V"),
                    ("Fundida", "Fundida"),
                    ("anomalias", "⚠ Anomalias (14)"),
                ]:
                    cor = "amber-8" if opcao != "anomalias" else "red-9"
                    ui.button(label, on_click=lambda v=opcao: set_filtro_pilar(v)).props(
                        f"flat dense size=sm color={cor}"
                    )

            # Filtro Tipo
            with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                ui.label("Tipo:").classes("text-xs uppercase text-zinc-500")
                for opcao, label in [("todos", "Todos"), ("base", "Base"), ("fundida", "Fundida")]:
                    ui.button(label, on_click=lambda v=opcao: set_filtro_tipo(v)).props(
                        "flat dense size=sm color=amber-8"
                    )

            # Filtro Disponibilidade
            with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                ui.label("Disponivel:").classes("text-xs uppercase text-zinc-500")
                for opcao, label in [
                    ("todos", "Todas"),
                    ("disponiveis", "Disponíveis"),
                    ("bloqueadas", "🚫 Bloqueadas (13)"),
                ]:
                    cor = "amber-8" if opcao != "bloqueadas" else "red-9"
                    ui.button(label, on_click=lambda v=opcao: set_filtro_disponivel(v)).props(
                        f"flat dense size=sm color={cor}"
                    )

        ui.separator().classes("bg-zinc-700")

        # === Tabela ===
        table = ui.table(
            columns=columns,
            rows=rows_iniciais,
            row_key="id",
            pagination=pagination_state,
        ).classes("w-full bg-zinc-800 rounded-lg").props(
            'flat bordered dark rows-per-page-options="[10, 25, 50, 100]"'
        )
        table_ref["widget"] = table

        async def on_request(e: GenericEventArguments) -> None:
            new_pag = e.args["pagination"]
            rows, total_atual = await _buscar_pagina_vocacoes(
                page=new_pag.get("page", 1),
                rows_per_page=new_pag.get("rowsPerPage", 25),
                sort_by=new_pag.get("sortBy") or "id",
                descending=new_pag.get("descending", False),
                filtro_pilar=filtros_state["pilar"],
                filtro_tipo=filtros_state["tipo"],
                filtro_disponivel=filtros_state["disponivel"],
                busca_nome=filtros_state["busca"],
            )
            new_pag["rowsNumber"] = total_atual
            table.rows = rows
            table.pagination = new_pag
            table.update()
            counter_ref["widget"].set_text(
                f"{total_atual} vocação(ões) filtrada(s) de 126 total"
            )

        table.on("request", on_request)

        with ui.row().classes("w-full justify-center mt-auto pt-6"):
            ui.label(
                "Módulo 6.2 OK. Pagina de detalhes chega na Etapa 3."
            ).classes("text-xs text-zinc-600 italic")


'''


def main() -> int:
    if not MAIN.exists():
        print("[ERRO] main.py nao encontrado.")
        return 1

    c = MAIN.read_text(encoding="utf-8")
    antes = len(c)

    if SENTINELA in c:
        print(f"  [IDEMPOTENTE] Etapa 2 vocacoes ja aplicada. {antes} bytes.")
        return 0

    # --- 1. Verificar se import precisa mudar ---
    if IMPORT_ANTIGO not in c:
        print(f"[ERRO 1] Import antigo nao encontrado:\n  {IMPORT_ANTIGO}")
        return 2
    c = c.replace(IMPORT_ANTIGO, IMPORT_NOVO, 1)
    print("  [1] Import atualizado: +RefVocacoes")

    # --- 2. Adicionar import de asyncio (pra asyncio.create_task) ---
    if "import asyncio" not in c:
        c = c.replace(
            "import warnings", "import asyncio\nimport warnings", 1
        )
        print("  [2] Import asyncio adicionado")
    else:
        print("  [2] asyncio ja importado")

    # --- 3. Adicionar total_vocacoes na home ---
    if HOME_TOTAL_OLD not in c:
        print("[ERRO 3] Home total antigo nao encontrado")
        return 3
    c = c.replace(HOME_TOTAL_OLD, HOME_TOTAL_NEW, 1)
    print("  [3] total_vocacoes na home OK")

    # --- 4. Adicionar card de vocacoes na home (depois do card de estrelas) ---
    if HOME_OLD not in c:
        print("[ERRO 4] Fim do card de estrelas nao encontrado")
        return 4
    c = c.replace(HOME_OLD, HOME_NEW, 1)
    print("  [4] Card de Vocacoes adicionado na home")

    # --- 5. Inserir bloco principal antes do MOUNT ---
    if ANCORA not in c:
        print(f"[ERRO 5] Ancora nao encontrada: {ANCORA!r}")
        return 5

    linhas = c.split("\n")
    idx_ancora = None
    for i, linha in enumerate(linhas):
        if ANCORA in linha:
            idx_ancora = i
            break

    idx_inicio = idx_ancora
    while idx_inicio > 0 and not linhas[idx_inicio - 1].startswith("# ===="):
        idx_inicio -= 1
    idx_inicio -= 1

    linhas_novas = (
        linhas[:idx_inicio] + NOVO_BLOCO.split("\n") + linhas[idx_inicio:]
    )
    c = "\n".join(linhas_novas)

    MAIN.write_text(c, encoding="utf-8")
    depois = len(c)
    print(f"  [5] Bloco principal inserido ({len(NOVO_BLOCO)} chars)")
    print()
    print("=" * 72)
    print(f"  [OK] Etapa 2 de vocacoes aplicada.")
    print(f"  Antes: {antes} | Depois: {depois} (+{depois - antes})")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())