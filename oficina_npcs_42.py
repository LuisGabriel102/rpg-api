"""
Oficina do Mestre — Modulo 4.2 · Listagem rica + Detalhe rico de NPCs.

v4 — fix do bug de timeout NiceGUI:
- Adicionado await aguardar_conexao_websocket() no inicio de cada handler.
- Padrao Two-Phase Loading: UI placeholder enviada como resposta HTTP (rapido),
  queries pesadas executam DEPOIS, com mudancas indo via WebSocket sem limite
  de 3 segundos do response_timeout interno do NiceGUI.
- Sem isso, /oficina/npcs/{id} travava em loop "Response not ready after 3.0
  seconds" porque as 10 queries auxiliares + queries da rota detalhe somavam
  >3s e a coroutine era cancelada antes do HTML ser enviado.
- Ver ui_helpers.py pra explicacao completa do bug.

v3 (mantido): NPC convertido pra dict dentro da session (evita detached state),
queries sequenciais (asyncpg nao permite paralelismo na mesma session),
try/except no detalhe pra logar erros.
"""

import asyncio
from typing import Any, Optional

from nicegui import ui
from nicegui.events import GenericEventArguments
from sqlalchemy import text
from sqlmodel import select

from db import get_session
from models import Npcs
from ui_helpers import aguardar_conexao_websocket, barra_nav


# ====================================================================
# HELPERS DE QUERY · listagem paginada
# ====================================================================

_NPC_SORTABLE = {"id", "nome", "camada", "singularidade", "raca", "status"}


async def _opcoes_filtros() -> dict:
    """Valores distintos pra popular dropdowns de filtro."""
    async with get_session() as session:
        locs = await session.execute(text(
            "SELECT DISTINCT localizacao_base FROM npcs "
            "WHERE localizacao_base IS NOT NULL ORDER BY 1"
        ))
        facc = await session.execute(text(
            "SELECT DISTINCT unnest(facoes) AS f FROM npcs "
            "WHERE facoes IS NOT NULL ORDER BY 1"
        ))
        return {
            "locs": [r[0] for r in locs.all()],
            "faccoes": [r[0] for r in facc.all()],
        }


async def _buscar_pagina_npcs_rica(
    page: int,
    rows_per_page: int,
    sort_by: str,
    descending: bool,
    busca: str = "",
    camada: Optional[int] = None,
    localizacao: Optional[str] = None,
    faccao: Optional[str] = None,
    status: Optional[str] = None,
) -> tuple[list[dict], int]:
    """Busca paginada com filtros."""
    if sort_by not in _NPC_SORTABLE:
        sort_by = "nome"

    skip = max(0, (page - 1) * rows_per_page)

    where = []
    params: dict[str, Any] = {}

    if busca:
        where.append(
            "(nome ILIKE :busca OR nome_curto ILIKE :busca OR epiteto ILIKE :busca)"
        )
        params["busca"] = f"%{busca}%"
    if camada is not None:
        where.append("camada = :camada")
        params["camada"] = camada
    if localizacao:
        where.append("localizacao_base = :localizacao")
        params["localizacao"] = localizacao
    if faccao:
        where.append(":faccao = ANY(facoes)")
        params["faccao"] = faccao
    if status:
        where.append("status = :status")
        params["status"] = status

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    order_expr = f"{sort_by} {'DESC' if descending else 'ASC'}, nome ASC"
    if sort_by == "singularidade":
        order_expr = (
            f"COALESCE(singularidade, 0) {'DESC' if descending else 'ASC'}, nome ASC"
        )

    async with get_session() as session:
        count_stmt = text(f"SELECT COUNT(*) FROM npcs {where_sql}")
        total = (await session.execute(count_stmt, params)).scalar_one()

        data_stmt = text(f"""
            SELECT id, nome, nome_curto, epiteto, raca, sexo,
                   idade_aparente, profissao, localizacao_base,
                   facoes, status, camada, singularidade,
                   imagem_url
            FROM npcs
            {where_sql}
            ORDER BY {order_expr}
            LIMIT :limit OFFSET :offset
        """)
        params["limit"] = rows_per_page
        params["offset"] = skip
        result = await session.execute(data_stmt, params)
        rows_raw = result.mappings().all()

    rows = []
    for r in rows_raw:
        prof = (r["profissao"] or "")
        prof_trunc = prof[:50] + "…" if len(prof) > 50 else prof
        facoes = r["facoes"] or []
        facoes_str = ", ".join(facoes[:2]) + (f" +{len(facoes)-2}" if len(facoes) > 2 else "")
        rows.append({
            "id": r["id"],
            "nome": r["nome"] or "-",
            "nome_curto": r["nome_curto"] or "",
            "epiteto": r["epiteto"] or "",
            "raca": r["raca"] or "-",
            "idade": r["idade_aparente"] or "-",
            "profissao": prof_trunc or "-",
            "localizacao": r["localizacao_base"] or "-",
            "facoes_str": facoes_str or "-",
            "status": r["status"] or "-",
            "camada": r["camada"],
            "singularidade": r["singularidade"] or "-",
            "imagem_url": r["imagem_url"],
        })
    return rows, total or 0


# ====================================================================
# HELPERS DE QUERY · detalhe rico (tudo via dict)
# ====================================================================

_NPC_FIELDS = [
    "id", "nome", "nome_curto", "epiteto", "raca", "sexo",
    "idade_aparente", "idade_real", "localizacao_atual", "localizacao_base",
    "profissao", "facoes", "status", "camada", "singularidade",
    "abertura", "conscienciosidade", "extroversao", "amabilidade", "neuroticismo",
    "valores", "estilo_de_fala", "tensao_interna",
    "prompt_identidade", "prompt_dialogo", "prompt_contexto_protagonista",
    "personality_summary",
    "medo_principal", "medos_secundarios", "desejo_oculto",
    "linha_que_nao_cruza", "maior_arrependimento",
    "backstory_resumida", "backstory_completa", "evento_formativo",
    "o_que_so_ele_pode_fazer", "momento_de_singularidade",
    "notas_do_gpt",
]


async def _buscar_npc_detalhe(npc_id: int) -> Optional[dict]:
    """Busca NPC + tabelas associativas. Retorna TUDO como dict (sem objetos detached)."""
    async with get_session() as session:
        # Busca NPC e converte pra dict imediatamente (evita detached state)
        npc_obj = await session.get(Npcs, npc_id)
        if not npc_obj:
            return None
        npc_dict = {f: getattr(npc_obj, f, None) for f in _NPC_FIELDS}

        # Imagem (colunas adicionadas no modulo 4.4, nao estao no SQLModel —
        # buscamos via SQL puro)
        img_row = (await session.execute(text("""
            SELECT imagem_url, imagem_atualizada_em
            FROM npcs WHERE id = :id
        """), {"id": npc_id})).mappings().first()
        npc_dict["imagem_url"] = img_row["imagem_url"] if img_row else None
        npc_dict["imagem_atualizada_em"] = img_row["imagem_atualizada_em"] if img_row else None

        # Galeria completa de imagens (modulo 4.5)
        # Ordenada: principal primeiro, depois mais recentes
        imagens_rows = (await session.execute(text("""
            SELECT id, url, rotulo_narrativo, e_principal, criado_em
            FROM npc_imagens
            WHERE npc_id = :id
            ORDER BY e_principal DESC, criado_em DESC
        """), {"id": npc_id})).mappings().all()
        imagens_lista = [dict(r) for r in imagens_rows]

        # Queries sequenciais (asyncpg nao permite paralelismo na mesma session)
        secrets = [dict(r) for r in (await session.execute(text("""
            SELECT * FROM npc_secrets WHERE npc_id = :id
            ORDER BY trust_level_required, titulo
        """), {"id": npc_id})).mappings().all()]

        goals = [dict(r) for r in (await session.execute(text("""
            SELECT * FROM npc_goals WHERE npc_id = :id
            ORDER BY prazo_narrativo, progresso_percentual DESC
        """), {"id": npc_id})).mappings().all()]

        rels_out = [dict(r) for r in (await session.execute(text("""
            SELECT r.*, n.nome AS alvo_nome, n.camada AS alvo_camada,
                   n.status AS alvo_status
            FROM npc_relationships r
            LEFT JOIN npcs n ON r.npc_alvo_id = n.id
            WHERE r.npc_origem_id = :id
            ORDER BY r.tipo, alvo_nome
        """), {"id": npc_id})).mappings().all()]

        rels_in = [dict(r) for r in (await session.execute(text("""
            SELECT r.*, n.nome AS origem_nome, n.camada AS origem_camada
            FROM npc_relationships r
            LEFT JOIN npcs n ON r.npc_origem_id = n.id
            WHERE r.npc_alvo_id = :id
            ORDER BY r.tipo, origem_nome
        """), {"id": npc_id})).mappings().all()]

        family = [dict(r) for r in (await session.execute(text("""
            SELECT * FROM npc_family WHERE npc_id = :id ORDER BY grau_parentesco
        """), {"id": npc_id})).mappings().all()]

        memories = [dict(r) for r in (await session.execute(text("""
            SELECT * FROM npc_memories WHERE npc_id = :id
            ORDER BY importancia DESC, data_narrativa
        """), {"id": npc_id})).mappings().all()]

        knowledge = [dict(r) for r in (await session.execute(text("""
            SELECT * FROM npc_knowledge WHERE npc_id = :id
            ORDER BY certeza DESC, topico
        """), {"id": npc_id})).mappings().all()]

        emotional_row = (await session.execute(text("""
            SELECT * FROM npc_emotional_state WHERE npc_id = :id
            ORDER BY timestamp_estado DESC LIMIT 1
        """), {"id": npc_id})).mappings().first()
        emotional = dict(emotional_row) if emotional_row else None

        routine_row = (await session.execute(text("""
            SELECT * FROM npc_daily_routine WHERE npc_id = :id
        """), {"id": npc_id})).mappings().first()
        routine = dict(routine_row) if routine_row else None

        locations = [dict(r) for r in (await session.execute(text("""
            SELECT l.nome, l.tipo_local, ln.tipo_presenca, ln.descricao
            FROM location_npcs ln
            JOIN locations l ON ln.location_id = l.id
            WHERE ln.npc_id = :id
            ORDER BY l.nome
        """), {"id": npc_id})).mappings().all()]

    return {
        "npc": npc_dict,
        "secrets": secrets,
        "goals": goals,
        "rels_out": rels_out,
        "rels_in": rels_in,
        "family": family,
        "memories": memories,
        "knowledge": knowledge,
        "emotional": emotional,
        "routine": routine,
        "locations": locations,
        "imagens": imagens_lista,
    }


# ====================================================================
# HELPERS VISUAIS · badges, Big Five, cores
# ====================================================================

def _status_config(status: str) -> tuple[str, str, str]:
    return {
        "vivo": ("text-emerald-400", "bg-emerald-900/40", "●"),
        "morto": ("text-red-400", "bg-red-900/50", "†"),
        "desaparecido": ("text-violet-400", "bg-violet-900/40", "?"),
        "exilado": ("text-orange-400", "bg-orange-900/40", "→"),
    }.get(status, ("text-zinc-400", "bg-zinc-800", "—"))


def _camada_config(camada: int) -> tuple[str, str, str]:
    return {
        1: ("Âncora", "text-amber-300", "bg-amber-900/50"),
        2: ("Recorrente", "text-sky-300", "bg-sky-900/40"),
        3: ("Fundo", "text-zinc-400", "bg-zinc-800"),
    }.get(camada, ("?", "text-zinc-400", "bg-zinc-800"))


def _trust_color(level: int) -> str:
    if level <= 3: return "text-emerald-400 bg-emerald-900/40"
    if level <= 6: return "text-yellow-300 bg-yellow-900/40"
    if level <= 8: return "text-orange-300 bg-orange-900/50"
    return "text-red-300 bg-red-900/50"


def _badge(text_: str, classes: str = "bg-zinc-800 text-zinc-300") -> None:
    ui.label(text_).classes(
        f"px-2 py-0.5 text-xs rounded-full {classes} font-mono whitespace-nowrap"
    )


def _status_badge(status: str) -> None:
    c, bg, ch = _status_config(status)
    _badge(f"{ch} {status}", f"{c} {bg}")


def _camada_badge(camada: int) -> None:
    label, c, bg = _camada_config(camada)
    _badge(f"C{camada} · {label}", f"{c} {bg}")


def _big_five_bar(label: str, value: Optional[int]) -> None:
    if value is None:
        return
    with ui.row().classes("w-full items-center gap-3"):
        ui.label(label).classes("text-sm text-zinc-400 w-40")
        with ui.element("div").classes("flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden"):
            ui.element("div").classes("h-full bg-amber-600").style(f"width: {value}%;")
        ui.label(f"{value}").classes("text-xs text-zinc-300 font-mono w-8 text-right")


def _section_header(text_: str, subtitle: str = "") -> None:
    with ui.row().classes("items-baseline gap-3 mb-2"):
        ui.label(text_).classes("text-lg font-semibold text-amber-200 tracking-wide")
        if subtitle:
            ui.label(subtitle).classes("text-xs text-zinc-500 italic")


def _kv(label: str, value: Any) -> None:
    if not value: return
    with ui.row().classes("items-start gap-2 w-full"):
        ui.label(label).classes("text-xs uppercase text-zinc-500 w-40 tracking-wider pt-0.5")
        ui.label(str(value)).classes("text-sm text-zinc-200 flex-1")


def _block(label: str, value: Optional[str], italic: bool = False) -> None:
    if not value: return
    with ui.column().classes("gap-1 w-full"):
        ui.label(label).classes("text-xs uppercase text-zinc-500 tracking-wider")
        cls = "text-sm text-zinc-300 leading-relaxed whitespace-pre-line"
        if italic: cls += " italic"
        ui.label(value).classes(cls)


# ====================================================================
# PAGINA /oficina/npcs · LISTAGEM RICA COM FILTROS
# ====================================================================

async def pagina_lista_npcs_rica() -> None:
    """Lista paginada com filtros, busca fuzzy, ordenacao."""

    # FIX TIMEOUT NICEGUI: envia placeholder + aguarda WS antes das queries.
    # Hoje a lista carrega em <3s, mas com mais NPCs vai estourar — preventivo.
    await aguardar_conexao_websocket("Catalogando almas do Alderyn...")

    barra_nav("npcs")

    filtros = {
        "busca": "",
        "camada": None,
        "localizacao": None,
        "faccao": None,
        "status": None,
    }
    pagination_state = {
        "rowsPerPage": 20,
        "rowsNumber": 0,
        "page": 1,
        "sortBy": "nome",
        "descending": False,
    }

    opcoes = await _opcoes_filtros()

    rows_iniciais, total = await _buscar_pagina_npcs_rica(
        page=1, rows_per_page=20, sort_by="nome", descending=False,
    )
    pagination_state["rowsNumber"] = total

    columns = [
        {"name": "nome", "label": "Nome", "field": "nome", "sortable": True, "align": "left"},
        {"name": "camada", "label": "Camada", "field": "camada", "sortable": True, "align": "center"},
        {"name": "raca", "label": "Raça", "field": "raca", "sortable": True, "align": "left"},
        {"name": "idade", "label": "Idade", "field": "idade", "sortable": False, "align": "right"},
        {"name": "profissao", "label": "Profissão", "field": "profissao", "sortable": False, "align": "left"},
        {"name": "localizacao", "label": "Localização", "field": "localizacao", "sortable": False, "align": "left"},
        {"name": "facoes_str", "label": "Facções", "field": "facoes_str", "sortable": False, "align": "left"},
        {"name": "status", "label": "Status", "field": "status", "sortable": True, "align": "center"},
        {"name": "singularidade", "label": "Sing.", "field": "singularidade", "sortable": True, "align": "right"},
    ]

    table_ref: dict = {"w": None}
    counter_ref: dict = {"w": None}

    async def refresh() -> None:
        if not table_ref["w"]:
            return
        pag = dict(table_ref["w"].pagination)
        rows, total_atual = await _buscar_pagina_npcs_rica(
            page=pag.get("page", 1),
            rows_per_page=pag.get("rowsPerPage", 20),
            sort_by=pag.get("sortBy") or "nome",
            descending=pag.get("descending", False),
            **filtros,
        )
        pag["rowsNumber"] = total_atual
        pag["page"] = 1
        table_ref["w"].rows = rows
        table_ref["w"].pagination = pag
        table_ref["w"].update()
        if counter_ref["w"]:
            counter_ref["w"].set_text(f"{total_atual} alma(s) filtrada(s)")

    def _schedule(coro) -> None:
        asyncio.create_task(coro)

    def set_busca(e) -> None:
        filtros["busca"] = (e.value or "").strip()
        ui.timer(0.05, lambda: _schedule(refresh()), once=True)

    def set_camada(e) -> None:
        filtros["camada"] = e.value
        ui.timer(0.05, lambda: _schedule(refresh()), once=True)

    def set_localizacao(e) -> None:
        filtros["localizacao"] = e.value
        ui.timer(0.05, lambda: _schedule(refresh()), once=True)

    def set_faccao(e) -> None:
        filtros["faccao"] = e.value
        ui.timer(0.05, lambda: _schedule(refresh()), once=True)

    def set_status(e) -> None:
        filtros["status"] = e.value
        ui.timer(0.05, lambda: _schedule(refresh()), once=True)

    with ui.column().classes("w-full min-h-screen bg-zinc-900 text-zinc-100 p-8 gap-4"):

        with ui.row().classes("w-full items-center justify-between"):
            with ui.row().classes("items-center gap-3"):
                ui.button(
                    icon="arrow_back",
                    on_click=lambda: ui.navigate.to("/oficina"),
                ).props("flat round dense color=amber-2")
                with ui.column().classes("gap-0"):
                    ui.label("NPCs do Alderyn").classes("text-3xl font-bold text-amber-200")
                    counter_ref["w"] = ui.label(
                        f"{total} alma(s) catalogada(s)"
                    ).classes("text-sm text-zinc-400 italic")

        ui.separator().classes("bg-zinc-700")

        with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-4"):
            with ui.row().classes("w-full gap-3 flex-wrap items-end"):
                ui.input(
                    label="Busca (nome, nome_curto, epíteto)",
                    placeholder="ex: Hesar, patriarca, o silente...",
                    on_change=set_busca,
                ).classes("flex-1 min-w-64").props("dense dark outlined clearable")

                ui.select(
                    options={None: "Todas", 1: "C1 Âncora", 2: "C2 Recorrente", 3: "C3 Fundo"},
                    label="Camada", value=None, on_change=set_camada,
                ).classes("w-40").props("dense dark outlined")

                ui.select(
                    options={None: "Todas", **{l: l for l in opcoes["locs"]}},
                    label="Localização", value=None, on_change=set_localizacao,
                ).classes("w-56").props("dense dark outlined")

                ui.select(
                    options={None: "Todas", **{f: f for f in opcoes["faccoes"]}},
                    label="Facção", value=None, on_change=set_faccao,
                ).classes("w-56").props("dense dark outlined")

                ui.select(
                    options={
                        None: "Todos",
                        "vivo": "● vivo",
                        "morto": "† morto",
                        "desaparecido": "? desaparecido",
                        "exilado": "→ exilado",
                    },
                    label="Status", value=None, on_change=set_status,
                ).classes("w-48").props("dense dark outlined")

        table = ui.table(
            columns=columns,
            rows=rows_iniciais,
            row_key="id",
            pagination=pagination_state,
        ).classes("w-full bg-zinc-800 rounded-lg").props(
            'flat bordered dark rows-per-page-options="[10, 20, 50]"'
        )
        table_ref["w"] = table

        table.add_slot("body-cell-camada", r"""
            <q-td :props="props">
                <q-badge :color="props.value === 1 ? 'amber-8' : props.value === 2 ? 'blue-8' : 'grey-7'"
                         rounded>
                    C{{ props.value }}
                </q-badge>
            </q-td>
        """)

        table.add_slot("body-cell-status", r"""
            <q-td :props="props">
                <q-badge :color="
                    props.value === 'vivo' ? 'green-7' :
                    props.value === 'morto' ? 'red-9' :
                    props.value === 'desaparecido' ? 'purple-9' :
                    props.value === 'exilado' ? 'orange-9' : 'grey-7'
                " rounded>
                    {{ props.value }}
                </q-badge>
            </q-td>
        """)

        table.add_slot("body-cell-nome", r"""
            <q-td :props="props">
                <q-item dense class="q-pa-none">
                    <q-item-section avatar>
                        <q-avatar size="36px" color="grey-9" text-color="grey-5">
                            <img v-if="props.row.imagem_url" :src="props.row.imagem_url" />
                            <q-icon v-else name="person" size="20px" />
                        </q-avatar>
                    </q-item-section>
                    <q-item-section>
                        <q-item-label class="text-weight-medium text-zinc-100">{{ props.row.nome }}</q-item-label>
                        <q-item-label v-if="props.row.epiteto" caption class="text-zinc-500 italic">
                            {{ props.row.epiteto.length > 60 ? props.row.epiteto.substring(0,60)+'…' : props.row.epiteto }}
                        </q-item-label>
                    </q-item-section>
                </q-item>
            </q-td>
        """)

        def ir_detalhe(e: GenericEventArguments) -> None:
            row = e.args[1]
            if row and "id" in row:
                ui.navigate.to(f"/oficina/npcs/{row['id']}")

        table.on("rowClick", ir_detalhe)

        async def on_request(e: GenericEventArguments) -> None:
            new_pag = e.args["pagination"]
            rows, total_atual = await _buscar_pagina_npcs_rica(
                page=new_pag.get("page", 1),
                rows_per_page=new_pag.get("rowsPerPage", 20),
                sort_by=new_pag.get("sortBy") or "nome",
                descending=new_pag.get("descending", False),
                **filtros,
            )
            new_pag["rowsNumber"] = total_atual
            table.rows = rows
            table.pagination = new_pag
            table.update()
            if counter_ref["w"]:
                counter_ref["w"].set_text(f"{total_atual} alma(s) filtrada(s)")

        table.on("request", on_request)

        with ui.row().classes("w-full justify-center mt-auto pt-6"):
            ui.label(
                "Módulo 4.2 OK. Clique numa linha pra ver o perfil completo."
            ).classes("text-xs text-zinc-600 italic")


# ====================================================================
# PAGINA /oficina/npcs/{id} · DETALHE RICO (com try/except + dict)
# ====================================================================

async def pagina_npc_detalhe(npc_id: int) -> None:
    """Detalhe rico com 13 cards: identidade, personalidade, prompts, etc."""

    # FIX TIMEOUT NICEGUI: envia placeholder + aguarda WS antes das queries.
    # Esta era a CAUSA do bug de loop infinito — _buscar_npc_detalhe roda 11
    # queries que somam >3s, estourando o response_timeout do NiceGUI e
    # cancelando a coroutine antes do HTML ser enviado.
    await aguardar_conexao_websocket(f"Buscando NPC #{npc_id}...")

    try:
        data = await _buscar_npc_detalhe(npc_id)
    except Exception as e:
        import traceback
        print("\n\n=========== ERRO _buscar_npc_detalhe ===========")
        traceback.print_exc()
        print("================================================\n\n")
        with ui.column().classes("w-full min-h-screen bg-zinc-900 text-zinc-100 p-8 gap-4"):
            ui.label(f"Erro ao buscar NPC {npc_id}").classes("text-2xl text-red-400")
            ui.label(str(e)).classes("text-sm text-zinc-400 font-mono")
            ui.button("Voltar", on_click=lambda: ui.navigate.to("/oficina/npcs")).props("color=amber-8")
        return

    if not data:
        with ui.column().classes(
            "w-full min-h-screen bg-zinc-900 text-zinc-100 p-8 items-center justify-center gap-4"
        ):
            ui.label(f"NPC id={npc_id} não encontrado.").classes("text-2xl text-zinc-400")
            ui.button(
                "Voltar à lista",
                on_click=lambda: ui.navigate.to("/oficina/npcs"),
            ).props("color=amber-8")
        return

    # npc agora e dict (nao objeto SQLModel detached)
    npc = data["npc"]

    try:
        with ui.column().classes("w-full min-h-screen bg-zinc-900 text-zinc-100 p-8 gap-4 max-w-7xl mx-auto"):

            # Breadcrumb
            with ui.row().classes("items-center gap-2 text-sm"):
                ui.link("← Oficina", "/oficina").classes("text-zinc-500 hover:text-amber-200")
                ui.label("/").classes("text-zinc-600")
                ui.link("NPCs", "/oficina/npcs").classes("text-zinc-500 hover:text-amber-200")
                ui.label("/").classes("text-zinc-600")
                ui.label(npc.get("nome_curto") or npc.get("nome") or "?").classes("text-zinc-300")

            # ═══ CABEÇALHO ═══
            with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-6"):
                with ui.row().classes("w-full items-start gap-6"):

                    # ── COLUNA ESQUERDA: imagem principal + galeria ──
                    # Modulo 4.5: galeria de versoes com rotulo narrativo opcional.
                    # Imagem principal grande (224x336, proporcao 2:3 retrato).
                    # Strip horizontal de thumbs das OUTRAS versoes (80x120).
                    with ui.column().classes("gap-3 items-center shrink-0"):
                        # Imagem principal
                        if npc.get("imagem_url"):
                            ui.image(npc["imagem_url"]).classes(
                                "w-56 rounded object-contain bg-zinc-900 "
                                "border border-zinc-700"
                            ).style("height: 336px;")
                        else:
                            with ui.element("div").classes(
                                "w-56 rounded bg-zinc-900 flex items-center "
                                "justify-center border border-dashed border-zinc-700"
                            ).style("height: 336px;"):
                                ui.icon("person", size="5rem").classes("text-zinc-600")

                        # ─── Callbacks da galeria ───

                        async def _tornar_principal(
                            imagem_id, imagem_url, _npc_id=npc["id"]
                        ):
                            """Marca uma imagem da galeria como principal."""
                            try:
                                async with get_session() as session:
                                    await session.execute(text("""
                                        UPDATE npc_imagens
                                        SET e_principal = false
                                        WHERE npc_id = :npc_id
                                    """), {"npc_id": _npc_id})
                                    await session.execute(text("""
                                        UPDATE npc_imagens
                                        SET e_principal = true
                                        WHERE id = :id
                                    """), {"id": imagem_id})
                                    await session.execute(text("""
                                        UPDATE npcs
                                        SET imagem_url = :url,
                                            imagem_atualizada_em = NOW()
                                        WHERE id = :npc_id
                                    """), {"url": imagem_url, "npc_id": _npc_id})
                                    await session.commit()
                                ui.notify(
                                    "Principal atualizada.",
                                    color="positive", timeout=1500,
                                )
                                ui.timer(0.6, lambda: ui.navigate.reload(), once=True)
                            except Exception as exc:
                                import traceback; traceback.print_exc()
                                ui.notify(f"Erro: {exc}", color="negative")

                        async def _deletar_imagem(
                            imagem_id, imagem_url, _npc_id=npc["id"]
                        ):
                            """Deleta imagem do banco + R2 (com promocao automatica
                            de nova principal se necessario)."""
                            try:
                                async with get_session() as session:
                                    img_row = (await session.execute(text("""
                                        SELECT e_principal FROM npc_imagens
                                        WHERE id = :id
                                    """), {"id": imagem_id})).mappings().first()

                                    await session.execute(text("""
                                        DELETE FROM npc_imagens WHERE id = :id
                                    """), {"id": imagem_id})

                                    # Se era principal, promove a mais recente
                                    if img_row and img_row["e_principal"]:
                                        nova = (await session.execute(text("""
                                            SELECT id, url FROM npc_imagens
                                            WHERE npc_id = :npc_id
                                            ORDER BY criado_em DESC LIMIT 1
                                        """), {"npc_id": _npc_id})).mappings().first()
                                        if nova:
                                            await session.execute(text("""
                                                UPDATE npc_imagens
                                                SET e_principal = true
                                                WHERE id = :id
                                            """), {"id": nova["id"]})
                                            await session.execute(text("""
                                                UPDATE npcs
                                                SET imagem_url = :url,
                                                    imagem_atualizada_em = NOW()
                                                WHERE id = :npc_id
                                            """), {"url": nova["url"], "npc_id": _npc_id})
                                        else:
                                            # Era a unica — limpa cache
                                            await session.execute(text("""
                                                UPDATE npcs
                                                SET imagem_url = NULL,
                                                    imagem_atualizada_em = NULL
                                                WHERE id = :npc_id
                                            """), {"npc_id": _npc_id})
                                    await session.commit()

                                # Deleta do R2 (best-effort, nao falha o fluxo)
                                try:
                                    from r2_storage import delete_imagem
                                    await delete_imagem(imagem_url)
                                except Exception as r2_exc:
                                    print(f"[delete] R2 falhou (ignorando): {r2_exc}")

                                ui.notify(
                                    "Imagem deletada.",
                                    color="positive", timeout=1500,
                                )
                                ui.timer(0.6, lambda: ui.navigate.reload(), once=True)
                            except Exception as exc:
                                import traceback; traceback.print_exc()
                                ui.notify(f"Erro: {exc}", color="negative")

                        def _confirmar_delete(imagem_id, imagem_url):
                            """Abre dialog de confirmacao antes de deletar."""
                            with ui.dialog() as confirm, ui.card().classes(
                                "bg-zinc-800 border border-zinc-700 p-6"
                            ):
                                ui.label("Deletar essa versão?").classes(
                                    "text-lg text-amber-200"
                                )
                                ui.label(
                                    "A imagem será removida do R2 também. "
                                    "Não pode ser desfeito."
                                ).classes("text-xs text-zinc-500")
                                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                                    ui.button("Cancelar", on_click=confirm.close).props(
                                        "flat color=zinc-5"
                                    )
                                    async def _ok():
                                        confirm.close()
                                        await _deletar_imagem(imagem_id, imagem_url)
                                    ui.button("Deletar", on_click=_ok).props(
                                        "color=red-9"
                                    )
                            confirm.open()

                        # ─── Dialog de upload com rotulo narrativo opcional ───

                        def _abrir_dialog_upload(_npc_id=npc["id"]):
                            with ui.dialog() as dialog, ui.card().classes(
                                "bg-zinc-800 border border-zinc-700 p-6 w-96"
                            ):
                                ui.label("Adicionar nova imagem").classes(
                                    "text-lg text-amber-200 font-bold"
                                )
                                ui.label(
                                    "Rotule esta versão pra registrar momento "
                                    "narrativo (opcional)."
                                ).classes("text-xs text-zinc-500 mb-2")

                                rotulo_input = ui.input(
                                    label="Rótulo narrativo",
                                    placeholder="ex: aposentado na vila pesqueira",
                                ).props("dark outlined dense").classes("w-full")

                                async def _on_upload(e):
                                    file = e.file
                                    file_bytes = await file.read()
                                    content_type = (
                                        getattr(file, 'content_type', None)
                                        or getattr(file, 'mime_type', None)
                                        or getattr(file, 'type', None)
                                    )
                                    if not content_type:
                                        fname = (
                                            getattr(file, 'filename', None)
                                            or getattr(file, 'name', None)
                                            or ""
                                        ).lower()
                                        if fname.endswith(('.jpg', '.jpeg')):
                                            content_type = "image/jpeg"
                                        elif fname.endswith('.png'):
                                            content_type = "image/png"
                                        elif fname.endswith('.webp'):
                                            content_type = "image/webp"
                                        else:
                                            content_type = "application/octet-stream"

                                    rotulo = (rotulo_input.value or "").strip() or None

                                    try:
                                        from r2_storage import upload_imagem_npc
                                        ui.notify(
                                            f"Enviando {len(file_bytes)/1024:.0f}KB...",
                                            color="info", timeout=2000,
                                        )
                                        url = await upload_imagem_npc(
                                            _npc_id, file_bytes, content_type
                                        )
                                        async with get_session() as session:
                                            count_row = (await session.execute(text("""
                                                SELECT COUNT(*) AS n FROM npc_imagens
                                                WHERE npc_id = :id
                                            """), {"id": _npc_id})).mappings().first()
                                            e_principal = count_row["n"] == 0

                                            await session.execute(text("""
                                                INSERT INTO npc_imagens
                                                  (npc_id, url, rotulo_narrativo,
                                                   e_principal, criado_em)
                                                VALUES
                                                  (:npc_id, :url, :rotulo,
                                                   :principal, NOW())
                                            """), {
                                                "npc_id": _npc_id, "url": url,
                                                "rotulo": rotulo,
                                                "principal": e_principal,
                                            })
                                            if e_principal:
                                                await session.execute(text("""
                                                    UPDATE npcs
                                                    SET imagem_url = :url,
                                                        imagem_atualizada_em = NOW()
                                                    WHERE id = :id
                                                """), {"url": url, "id": _npc_id})
                                            await session.commit()

                                        ui.notify(
                                            "Imagem adicionada. Recarregando...",
                                            color="positive", timeout=1500,
                                        )
                                        dialog.close()
                                        ui.timer(0.6, lambda: ui.navigate.reload(),
                                                 once=True)
                                    except ValueError as exc:
                                        ui.notify(f"Rejeitada: {exc}",
                                                  color="negative")
                                    except Exception as exc:
                                        import traceback; traceback.print_exc()
                                        ui.notify(f"Erro: {exc}", color="negative")

                                ui.upload(
                                    label="Selecionar arquivo",
                                    on_upload=_on_upload,
                                    max_file_size=5 * 1024 * 1024,
                                    auto_upload=True,
                                ).props(
                                    "accept='image/jpeg,image/png,image/webp' "
                                    "color=amber-8 flat dense"
                                ).classes("w-full mt-2")

                                ui.button("Cancelar", on_click=dialog.close).props(
                                    "flat color=zinc-5"
                                ).classes("self-end mt-2")
                            dialog.open()

                        # ─── Botao adicionar (sempre visivel) ───
                        ui.button(
                            "Adicionar imagem",
                            on_click=_abrir_dialog_upload,
                            icon="add_a_photo",
                        ).props("color=amber-8 flat dense").classes("w-56")

                        # --- Botao Abrir Atelie (Modulo 4.6.4) ---
                        ui.button(
                            "Abrir Atelie",
                            on_click=lambda nid=npc["id"]: ui.navigate.to(
                                f"/oficina/atelie/{nid}"
                            ),
                            icon="auto_awesome",
                        ).props("color=amber-8 unelevated dense").classes("w-56")

                        if npc.get("imagem_atualizada_em"):
                            ts = npc["imagem_atualizada_em"]
                            ui.label(
                                f"atualizada {ts.strftime('%d/%m/%Y %H:%M')}"
                            ).classes("text-xs text-zinc-600 italic")

                        # ─── Strip de thumbs das OUTRAS versoes ───
                        outras = [img for img in data["imagens"]
                                  if not img["e_principal"]]
                        if outras:
                            ui.separator().classes("bg-zinc-700 mt-2")
                            ui.label(
                                f"outras versões ({len(outras)})"
                            ).classes("text-xs text-zinc-500 uppercase tracking-wider")

                            with ui.row().classes(
                                "gap-2 overflow-x-auto max-w-56 pb-2"
                            ):
                                for img in outras:
                                    with ui.column().classes("gap-1 shrink-0"):
                                        # Thumb da imagem (80x120 = mesma proporcao 2:3)
                                        thumb = ui.image(img["url"]).classes(
                                            "w-20 rounded object-contain bg-zinc-900 "
                                            "border border-zinc-700"
                                        ).style("height: 120px;")
                                        # Tooltip: rotulo + timestamp
                                        ts_str = img["criado_em"].strftime("%d/%m/%Y")
                                        tip = (
                                            f"{img['rotulo_narrativo']} ({ts_str})"
                                            if img.get("rotulo_narrativo")
                                            else ts_str
                                        )
                                        thumb.tooltip(tip)

                                        # Botoes de acao
                                        with ui.row().classes("gap-0 justify-center w-20"):
                                            async def _on_tornar_principal(_e, iid=img["id"], iurl=img["url"]):
                                                await _tornar_principal(iid, iurl)
                                            ui.button(
                                                icon="star",
                                                on_click=_on_tornar_principal,
                                            ).props(
                                                "flat dense round color=amber-8 size=xs"
                                            ).tooltip("tornar principal")
                                            ui.button(
                                                icon="delete",
                                                on_click=lambda _e, iid=img["id"], iurl=img["url"]:
                                                    _confirmar_delete(iid, iurl),
                                            ).props(
                                                "flat dense round color=red-7 size=xs"
                                            ).tooltip("deletar")

                    # ── COLUNA DIREITA: identidade ──
                    with ui.column().classes("gap-1 flex-1"):
                        ui.label(npc["nome"]).classes(
                            "text-3xl font-bold text-amber-200 tracking-wide"
                        )
                        if npc.get("epiteto"):
                            ui.label(npc["epiteto"]).classes(
                                "text-lg text-zinc-400 italic"
                            )
                        with ui.row().classes("items-center gap-2 mt-3 flex-wrap"):
                            _camada_badge(npc.get("camada") or 3)
                            _status_badge(npc.get("status") or "desconhecido")
                            if npc.get("raca"):
                                _badge(npc["raca"], "bg-zinc-700 text-zinc-300")
                            if npc.get("sexo"):
                                _badge(npc["sexo"], "bg-zinc-700 text-zinc-300")
                            if npc.get("idade_aparente"):
                                _badge(f"idade {npc['idade_aparente']}", "bg-zinc-700 text-zinc-300")
                            if npc.get("idade_real") and npc["idade_real"] != npc.get("idade_aparente"):
                                _badge(
                                    f"real: {npc['idade_real']}",
                                    "bg-violet-900/50 text-violet-300 font-semibold"
                                )
                            if npc.get("singularidade"):
                                _badge(
                                    f"singularidade {npc['singularidade']}/10",
                                    _trust_color(npc["singularidade"])
                                )

            # ═══ IDENTIDADE & CONTEXTO ═══
            with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-5"):
                _section_header("Identidade & Contexto")
                with ui.column().classes("gap-2"):
                    _kv("Profissão", npc.get("profissao"))
                    _kv("Localização atual", npc.get("localizacao_atual"))
                    _kv("Localização base", npc.get("localizacao_base"))

                    if npc.get("facoes"):
                        with ui.row().classes("items-start gap-2 w-full"):
                            ui.label("Facções").classes("text-xs uppercase text-zinc-500 w-40 tracking-wider pt-0.5")
                            with ui.row().classes("gap-1 flex-wrap flex-1"):
                                for f in npc["facoes"]:
                                    _badge(f, "bg-amber-900/50 text-amber-200")

                    if data["locations"]:
                        with ui.row().classes("items-start gap-2 w-full mt-2"):
                            ui.label("Encontrado em").classes("text-xs uppercase text-zinc-500 w-40 tracking-wider pt-0.5")
                            with ui.column().classes("gap-1 flex-1"):
                                for loc in data["locations"]:
                                    ui.label(
                                        f"{loc['nome']} ({loc['tipo_presenca']})"
                                    ).classes("text-sm text-zinc-300")

            # ═══ PERSONALIDADE · Big Five ═══
            with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-5"):
                _section_header("Personalidade")
                with ui.column().classes("gap-3"):
                    _big_five_bar("Abertura", npc.get("abertura"))
                    _big_five_bar("Conscienciosidade", npc.get("conscienciosidade"))
                    _big_five_bar("Extroversão", npc.get("extroversao"))
                    _big_five_bar("Amabilidade", npc.get("amabilidade"))
                    _big_five_bar("Neuroticismo", npc.get("neuroticismo"))

                    if npc.get("valores"):
                        with ui.column().classes("gap-2 mt-3"):
                            ui.label("Valores").classes("text-xs uppercase text-zinc-500 tracking-wider")
                            with ui.row().classes("gap-1 flex-wrap"):
                                for v in npc["valores"]:
                                    _badge(v, "bg-amber-900/40 text-amber-200")

                    _block("Estilo de fala", npc.get("estilo_de_fala"), italic=True)

            # ═══ CAMPOS DO NARRADOR AI ═══
            with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-5"):
                _section_header("Campos do Narrador AI", "vão direto ao prompt do modelo")
                with ui.column().classes("gap-4"):
                    if npc.get("tensao_interna"):
                        with ui.element("div").classes(
                            "bg-amber-900/30 border-l-2 border-amber-500 p-3 rounded"
                        ):
                            ui.label("TENSÃO INTERNA").classes(
                                "text-xs font-bold tracking-wider text-amber-300"
                            )
                            ui.label(npc["tensao_interna"]).classes("text-sm text-zinc-200 mt-1")

                    _block("Identidade (prompt)", npc.get("prompt_identidade"))
                    _block("Diálogo (prompt)", npc.get("prompt_dialogo"))
                    _block("Contexto protagonista (prompt)", npc.get("prompt_contexto_protagonista"))
                    _block("Personality summary", npc.get("personality_summary"))

            # ═══ PSICOLOGIA PROFUNDA ═══
            with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-5"):
                _section_header("Psicologia Profunda")
                with ui.column().classes("gap-3"):
                    _block("Medo principal", npc.get("medo_principal"))
                    if npc.get("medos_secundarios"):
                        with ui.column().classes("gap-1"):
                            ui.label("Medos secundários").classes("text-xs uppercase text-zinc-500 tracking-wider")
                            for m in npc["medos_secundarios"]:
                                ui.label(f"· {m}").classes("text-sm text-zinc-300 ml-2")
                    _block("Desejo oculto", npc.get("desejo_oculto"))
                    _block("Linha que não cruza", npc.get("linha_que_nao_cruza"))
                    _block("Maior arrependimento", npc.get("maior_arrependimento"))

            # ═══ ESTADO EMOCIONAL ═══
            if data["emotional"]:
                e = data["emotional"]
                valence = e.get("humor_valence", 0) or 0
                val_color = "text-emerald-400" if valence > 20 else (
                    "text-red-400" if valence < -20 else "text-zinc-400"
                )
                with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-5"):
                    _section_header("Estado Emocional", "baseline canônico 312")
                    with ui.row().classes("gap-6 flex-wrap items-center"):
                        with ui.column().classes("gap-0"):
                            ui.label("Emoção dominante").classes("text-xs text-zinc-500 uppercase tracking-wider")
                            ui.label(e["emocao_dominante"]).classes("text-lg text-amber-200 font-semibold")
                        with ui.column().classes("gap-0"):
                            ui.label("Intensidade").classes("text-xs text-zinc-500 uppercase tracking-wider")
                            ui.label(f"{e['intensidade']}/10").classes("text-lg text-zinc-100 font-mono")
                        with ui.column().classes("gap-0"):
                            ui.label("Estresse").classes("text-xs text-zinc-500 uppercase tracking-wider")
                            ui.label(f"{e['estresse_atual']}/100").classes("text-lg text-zinc-100 font-mono")
                        with ui.column().classes("gap-0"):
                            ui.label("Humor (valência)").classes("text-xs text-zinc-500 uppercase tracking-wider")
                            ui.label(f"{valence:+d}").classes(f"text-lg {val_color} font-mono font-semibold")
                    if e.get("causa_principal"):
                        _block("Causa principal", e["causa_principal"], italic=True)

            # ═══ HISTÓRIA ═══
            with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-5"):
                _section_header("História")
                with ui.column().classes("gap-3"):
                    _block("Resumo", npc.get("backstory_resumida"))
                    if npc.get("backstory_completa"):
                        with ui.expansion(
                            "História completa", icon="history"
                        ).classes("w-full bg-zinc-900/50 rounded").props("dense"):
                            ui.label(npc["backstory_completa"]).classes(
                                "text-sm text-zinc-300 leading-relaxed whitespace-pre-line p-3"
                            )
                    _block("Evento formativo", npc.get("evento_formativo"), italic=True)

            # ═══ SINGULARIDADE ═══
            if npc.get("o_que_so_ele_pode_fazer") or npc.get("momento_de_singularidade"):
                with ui.card().classes("w-full bg-zinc-800 border-l-2 border-amber-600 border border-zinc-700 p-5"):
                    _section_header("Singularidade", f"{npc['singularidade']}/10" if npc.get("singularidade") else "")
                    with ui.column().classes("gap-3"):
                        _block("O que só ele pode fazer", npc.get("o_que_so_ele_pode_fazer"))
                        _block("Momento de singularidade", npc.get("momento_de_singularidade"), italic=True)

            # ═══ ROTINA DIÁRIA ═══
            if data["routine"]:
                r = data["routine"]
                with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-5"):
                    _section_header("Rotina Diária")
                    with ui.column().classes("gap-2"):
                        for campo, label_pt in [
                            ("amanhecer", "Amanhecer"), ("manha", "Manhã"),
                            ("meio_dia", "Meio-dia"), ("tarde", "Tarde"),
                            ("noite", "Noite"), ("madrugada", "Madrugada"),
                        ]:
                            if r.get(campo):
                                with ui.column().classes("gap-0"):
                                    ui.label(label_pt.upper()).classes(
                                        "text-xs text-zinc-500 font-semibold tracking-wider"
                                    )
                                    ui.label(r[campo]).classes("text-sm text-zinc-300 leading-relaxed")
                        alt = r.get("rotina_alterada_por")
                        if alt and isinstance(alt, dict) and alt.get("evento"):
                            with ui.element("div").classes(
                                "bg-amber-900/30 border-l-2 border-amber-500 p-3 rounded mt-2"
                            ):
                                ui.label("ALTERAÇÕES").classes(
                                    "text-xs font-bold tracking-wider text-amber-300"
                                )
                                ui.label(alt["evento"]).classes("text-sm text-zinc-200 mt-1")

            # ═══ SEGREDOS ═══
            if data["secrets"]:
                with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-5"):
                    _section_header("Segredos", f"{len(data['secrets'])} itens")
                    with ui.column().classes("gap-3"):
                        for s in data["secrets"]:
                            tcolor = _trust_color(s.get("trust_level_required") or 0)
                            with ui.element("div").classes(
                                "border-l-2 border-zinc-700 pl-3 py-1 hover:bg-zinc-900/50 rounded"
                            ):
                                with ui.row().classes("items-center gap-2 flex-wrap"):
                                    _badge(f"trust {s.get('trust_level_required')}", tcolor)
                                    if s.get("impacto_emocional"):
                                        _badge(
                                            f"impacto {s['impacto_emocional']}/10",
                                            "bg-zinc-700 text-zinc-300"
                                        )
                                    if s.get("is_discoverable") is False:
                                        _badge("não-descoberta por confiança", "bg-red-900/50 text-red-300")
                                ui.label(s["titulo"]).classes("text-zinc-100 font-semibold mt-1")
                                ui.label(s["descricao_interna"]).classes(
                                    "text-sm text-zinc-400 mt-1 leading-relaxed"
                                )
                                if s.get("versao_revelavel"):
                                    with ui.element("div").classes("mt-2 bg-zinc-900/60 p-2 rounded"):
                                        ui.label("Versão revelável").classes("text-xs text-zinc-500 italic")
                                        ui.label(s["versao_revelavel"]).classes("text-sm text-zinc-300")

            # ═══ OBJETIVOS ═══
            if data["goals"]:
                with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-5"):
                    _section_header("Objetivos", f"{len(data['goals'])} itens")
                    with ui.column().classes("gap-2"):
                        for g in data["goals"]:
                            with ui.element("div").classes(
                                "border-l-2 border-zinc-700 pl-3 py-1 hover:bg-zinc-900/50 rounded"
                            ):
                                with ui.row().classes("items-center gap-2 flex-wrap"):
                                    _badge(g["tipo"], "bg-sky-900/50 text-sky-300")
                                    _badge(g["prazo_narrativo"], "bg-zinc-700 text-zinc-300")
                                    consc = g.get("nivel_de_consciencia") or "?"
                                    cons_cls = "bg-violet-900/40 text-violet-300" if consc != "consciente" else "bg-zinc-700 text-zinc-300"
                                    _badge(consc, cons_cls)
                                    if g.get("progresso_percentual") is not None:
                                        _badge(f"{g['progresso_percentual']}%", "bg-zinc-700 text-zinc-300")
                                    if g.get("conflita_com_protagonista"):
                                        _badge("conflita com protagonista", "bg-red-900/50 text-red-300")
                                ui.label(g["descricao"]).classes("text-sm text-zinc-300 mt-1")

            # ═══ RELACIONAMENTOS ═══
            if data["rels_out"] or data["rels_in"]:
                total_rels = len(data["rels_out"]) + len(data["rels_in"])
                with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-5"):
                    _section_header("Relacionamentos", f"{total_rels} vínculos")
                    with ui.column().classes("gap-2"):
                        if data["rels_out"]:
                            ui.label(f"→ Sentimentos deste NPC por outros ({len(data['rels_out'])})").classes(
                                "text-xs text-zinc-500 uppercase mt-2 tracking-wider"
                            )
                            for r in data["rels_out"]:
                                _render_rel(r, "alvo_nome", "npc_alvo_id")
                        if data["rels_in"]:
                            ui.label(f"← Sentimentos de outros por este NPC ({len(data['rels_in'])})").classes(
                                "text-xs text-zinc-500 uppercase mt-4 tracking-wider"
                            )
                            for r in data["rels_in"]:
                                _render_rel(r, "origem_nome", "npc_origem_id")

            # ═══ FAMÍLIA ═══
            if data["family"]:
                with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-5"):
                    _section_header("Família", f"{len(data['family'])} parentescos")
                    with ui.column().classes("gap-2"):
                        for f in data["family"]:
                            with ui.row().classes("items-center gap-3 py-1 flex-wrap"):
                                _badge(f["grau_parentesco"], "bg-zinc-700 text-zinc-300")
                                _badge(f.get("status_parente") or "?", "bg-zinc-700 text-zinc-400")
                                if f.get("parente_id"):
                                    ui.link(
                                        f.get("parente_nome") or "?",
                                        f"/oficina/npcs/{f['parente_id']}"
                                    ).classes("text-zinc-200 hover:text-amber-200 font-medium")
                                else:
                                    ui.label(f.get("parente_nome") or "?").classes("text-zinc-400 italic")
                                if f.get("notas"):
                                    ui.label(f"— {f['notas']}").classes("text-xs text-zinc-500 italic")

            # ═══ MEMÓRIAS ═══
            if data["memories"]:
                with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-5"):
                    _section_header("Memórias", f"{len(data['memories'])} episódios")
                    with ui.column().classes("gap-3"):
                        for m in data["memories"]:
                            border = "border-violet-500" if m.get("esta_suprimida") else "border-zinc-700"
                            with ui.element("div").classes(
                                f"border-l-2 {border} pl-3 py-1 hover:bg-zinc-900/50 rounded"
                            ):
                                with ui.row().classes("items-center gap-2 flex-wrap"):
                                    _badge(
                                        f"imp {m['importancia']}/10",
                                        _trust_color(m["importancia"])
                                    )
                                    if m.get("data_narrativa"):
                                        _badge(m["data_narrativa"], "bg-zinc-700 text-zinc-400")
                                    if m.get("emocao_associada"):
                                        _badge(m["emocao_associada"], "bg-sky-900/40 text-sky-300")
                                    if m.get("esta_suprimida"):
                                        _badge("SUPRIMIDA", "bg-violet-900/60 text-violet-200 font-bold")
                                ui.label(m["descricao"]).classes(
                                    "text-sm text-zinc-300 mt-1 leading-relaxed"
                                )
                                if m.get("gatilho_de_superficie"):
                                    ui.label(f"Gatilho: {m['gatilho_de_superficie']}").classes(
                                        "text-xs text-zinc-500 italic mt-1"
                                    )
                                if m.get("como_o_gpt_narra"):
                                    with ui.element("div").classes(
                                        "bg-amber-900/20 border-l border-amber-700 p-2 mt-2 rounded"
                                    ):
                                        ui.label("Como o narrador manifesta").classes(
                                            "text-xs text-amber-300 font-bold tracking-wider"
                                        )
                                        ui.label(m["como_o_gpt_narra"]).classes(
                                            "text-sm text-zinc-300 italic"
                                        )

            # ═══ CONHECIMENTO ═══
            if data["knowledge"]:
                with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-5"):
                    _section_header("Conhecimento do Mundo", f"{len(data['knowledge'])} itens")
                    with ui.column().classes("gap-2"):
                        for k in data["knowledge"]:
                            cert_color = "text-emerald-400" if k["certeza"] >= 80 else (
                                "text-yellow-300" if k["certeza"] >= 50 else "text-orange-300"
                            )
                            with ui.element("div").classes(
                                "border-l-2 border-zinc-700 pl-3 py-1 hover:bg-zinc-900/50 rounded"
                            ):
                                with ui.row().classes("items-center gap-2 flex-wrap"):
                                    ui.label(k["topico"]).classes("text-zinc-100 font-semibold")
                                    _badge(f"certeza {k['certeza']}%", f"{cert_color} bg-zinc-800")
                                    if k.get("e_crenca_falsa"):
                                        _badge("CRENÇA FALSA", "bg-red-900/60 text-red-300 font-bold")
                                ui.label(k["conteudo"]).classes(
                                    "text-sm text-zinc-400 mt-1 leading-relaxed"
                                )
                                if k.get("fonte"):
                                    ui.label(f"Fonte: {k['fonte']}").classes(
                                        "text-xs text-zinc-500 italic mt-1"
                                    )

            with ui.row().classes("w-full justify-center mt-auto pt-6"):
                ui.label(
                    "Módulo 4.2 · Detalhe completo. 13 seções do ecossistema NPC."
                ).classes("text-xs text-zinc-600 italic")

    except Exception as e:
        # Captura qualquer erro de renderizacao. Antes do fix v4 isso nao
        # funcionava porque a coroutine era cancelada (CancelledError nao e
        # Exception). Agora captura erros reais.
        import traceback
        print("\n\n=========== ERRO RENDER DETALHE NPC ===========")
        traceback.print_exc()
        print("================================================\n\n")
        ui.label(f"Erro renderizando NPC: {e}").classes("text-red-400 p-8")


def _render_rel(rel: dict, nome_key: str, id_key: str) -> None:
    """Renderiza uma linha de relacionamento."""
    tipo = rel["tipo"]
    tipo_color = {
        "amizade": "bg-emerald-900/50 text-emerald-300",
        "amor": "bg-pink-900/50 text-pink-300",
        "rivalidade": "bg-orange-900/50 text-orange-300",
        "mentoria": "bg-sky-900/50 text-sky-300",
        "divida": "bg-violet-900/50 text-violet-300",
        "familiar": "bg-amber-900/50 text-amber-300",
        "inimizade": "bg-red-900/50 text-red-300",
        "respeito": "bg-sky-900/40 text-sky-200",
        "medo": "bg-violet-900/60 text-violet-200",
        "lealdade": "bg-amber-900/50 text-amber-300",
        "neutro": "bg-zinc-700 text-zinc-400",
    }.get(tipo, "bg-zinc-700 text-zinc-300")

    alvo_id = rel.get(id_key)

    with ui.element("div").classes(
        "border-l-2 border-zinc-700 pl-3 py-1.5 hover:bg-zinc-900/50 rounded"
    ):
        with ui.row().classes("items-center gap-2 flex-wrap"):
            _badge(tipo, tipo_color)
            nome = rel.get(nome_key) or "(NPC removido)"
            if alvo_id:
                ui.link(nome, f"/oficina/npcs/{alvo_id}").classes(
                    "text-zinc-200 hover:text-amber-200 font-medium"
                )
            else:
                ui.label(nome).classes("text-zinc-400 italic")
            with ui.row().classes("gap-1 ml-auto"):
                _badge(f"conf {rel.get('confianca', 0)}", "bg-zinc-700 text-zinc-400")
                _badge(f"afe {rel.get('afeicao', 0):+d}", "bg-zinc-700 text-zinc-400")
                _badge(f"res {rel.get('respeito', 0):+d}", "bg-zinc-700 text-zinc-400")
                if rel.get("medo"):
                    _badge(f"medo {rel['medo']}", "bg-violet-900/50 text-violet-300")
        if rel.get("historia_previa"):
            ui.label(rel["historia_previa"]).classes(
                "text-xs text-zinc-500 italic mt-1"
            )
