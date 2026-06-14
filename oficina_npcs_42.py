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
import html
from typing import Any, Optional

from nicegui import ui
from nicegui.events import GenericEventArguments
from sqlalchemy import text
from sqlmodel import select

from db import get_session
from models import Npcs
from ui_helpers import aguardar_conexao_websocket, barra_nav
from tema_oficina import CSS_PERGAMINHO


# ====================================================================
# GALERIA DE RETRATOS · pele vitral (Fatia 3)
# CSS escopado em .gp-* + helpers que emitem HTML (re-renderizavel).
# ====================================================================

_GALERIA_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=IM+Fell+English+SC&family=Spectral:ital@0;1&display=swap" rel="stylesheet">
<style>
.q-layout,.q-page-container,.q-page{width:100%!important;max-width:none!important;}
.nicegui-content{width:100%!important;max-width:none!important;padding:0!important;gap:0!important;align-items:stretch!important;}
body{margin:0;}
.gp-screen{position:relative;font-family:'Spectral',Georgia,serif;color:#e8dcc0;min-height:100vh;width:100%;background:linear-gradient(180deg,#0a0d1a 0%,#10141f 50%,#13161f 100%);box-sizing:border-box;}
.gp-inner{max-width:1180px;margin:0 auto;padding:26px 28px 40px;}
.gp-head{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;}
.gp-title{font-family:'IM Fell English',serif;font-size:32px;color:#f6ecd2;}
.gp-count{font-style:italic;font-size:13px;color:#9a8a5a;}
.gp-rule{height:1px;background:linear-gradient(90deg,#5c4413,#c9a227 40%,transparent);margin:16px 0 22px;}
.gp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;}
.gp-card{position:relative;border:1px solid #b8902f;border-radius:5px;overflow:hidden;background:#0c0e16;box-shadow:inset 0 1px 0 rgba(255,238,190,.14);text-decoration:none;display:block;}
.gp-card:hover{border-color:#f0d98a;}
.gp-portrait{position:relative;width:100%;aspect-ratio:3/4;overflow:hidden;background:linear-gradient(160deg,#1a1d2a,#0e1018);}
.gp-portrait img{width:100%;height:100%;object-fit:cover;display:block;}
.gp-dead .gp-portrait img{filter:grayscale(1) brightness(.62);}
.gp-seldead{position:absolute;top:8px;right:8px;font-family:'IM Fell English SC',serif;font-size:10px;letter-spacing:.1em;color:#cdbfa6;background:rgba(10,10,14,.78);border:1px solid #6a6052;border-radius:3px;padding:2px 7px;}
.gp-foot{padding:11px 12px 13px;border-top:1px solid #2c2c1a;background:rgba(10,11,17,.6);}
.gp-name{font-family:'IM Fell English',serif;font-size:17px;color:#f3e7c4;line-height:1.05;}
.gp-epi{font-style:italic;font-size:12.5px;color:#c0a36a;margin-top:2px;line-height:1.2;}
.gp-prof{font-size:11px;color:#7f7558;margin-top:5px;line-height:1.25;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.gp-empty{display:flex;align-items:center;justify-content:center;width:100%;height:100%;}
.gp-initials{font-family:'IM Fell English',serif;font-size:46px;color:#b8902f;opacity:.85;}
.gp-dead .gp-name{color:#cfc7b4;}.gp-dead .gp-epi{color:#9a9078;}
.gp-vazio{text-align:center;font-style:italic;color:#7a6f55;padding:50px 0;}
.gp-filtros{background:rgba(12,14,22,.72)!important;border:1px solid #5c4413!important;border-radius:5px!important;box-shadow:inset 0 1px 0 rgba(255,238,190,.10)!important;}
.gp-filtros .q-field__control{background:rgba(10,11,17,.55)!important;border-radius:4px;font-family:'Spectral',Georgia,serif;}
.gp-filtros .q-field--outlined .q-field__control:before{border:1px solid #6e561f!important;}
.gp-filtros .q-field--outlined .q-field__control:hover:before{border-color:#b8902f!important;}
.gp-filtros .q-field--outlined .q-field__control:after{border-color:#c9a227!important;}
.gp-filtros .q-field__native,.gp-filtros .q-field__input,.gp-filtros .q-field__native span{color:#e8dcc0!important;font-family:'Spectral',Georgia,serif;}
.gp-filtros .q-field__label{color:#9a8a5a!important;font-family:'Spectral',Georgia,serif;}
.gp-filtros .q-icon,.gp-filtros .q-select__dropdown-icon{color:#b8902f!important;}
.gp-filtros .q-field__native::placeholder{color:#7a6f55!important;}
.q-menu{background:#0c0e16!important;border:1px solid #6e561f!important;color:#e8dcc0!important;}
.q-menu .q-item{color:#d8cba8!important;font-family:'Spectral',Georgia,serif;}
.q-menu .q-item:hover,.q-menu .q-item--active,.q-menu .q-item.q-manual-focusable--focused{background:rgba(184,144,47,.18)!important;color:#f3e7c4!important;}
</style>
"""


def _iniciais(nome: str) -> str:
    import html as _h
    partes = [p for p in (nome or "").split() if p]
    if not partes:
        return "?"
    if len(partes) == 1:
        return _h.escape(partes[0][:2].upper())
    return _h.escape((partes[0][:1] + partes[-1][:1]).upper())


def _card_npc(npc: dict) -> str:
    import html as _h
    nome = _h.escape(str(npc.get("nome") or "-"))
    epi = _h.escape(str(npc.get("epiteto") or ""))
    prof = str(npc.get("profissao") or "")
    prof = _h.escape(prof if len(prof) <= 60 else prof[:57] + "…")
    img = npc.get("imagem_url")
    morto = (str(npc.get("status") or "")).lower() == "morto"
    cls_dead = " gp-dead" if morto else ""
    if img:
        src = _h.escape(str(img), quote=True)
        retrato = f'<img src="{src}" alt="" loading="lazy">'
    else:
        retrato = f'<div class="gp-empty"><span class="gp-initials">{_iniciais(npc.get("nome"))}</span></div>'
    selo = '<span class="gp-seldead">&#10013; morto</span>' if morto else ""
    epi_html = f'<div class="gp-epi">{epi}</div>' if epi else ""
    prof_html = f'<div class="gp-prof">{prof}</div>' if prof else ""
    return (
        f'<a class="gp-card{cls_dead}" href="/oficina/npcs/{npc.get("id")}">'
        f'<div class="gp-portrait">{retrato}{selo}</div>'
        f'<div class="gp-foot"><div class="gp-name">{nome}</div>{epi_html}{prof_html}</div></a>'
    )


def _grade_npcs(rows: list[dict]) -> str:
    if not rows:
        return '<div class="gp-vazio">Nenhum nome encontrado com esses filtros.</div>'
    return '<div class="gp-grid">' + "".join(_card_npc(n) for n in rows) + '</div>'


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
    ui.add_head_html(_GALERIA_CSS)

    filtros = {
        "busca": "",
        "camada": None,
        "localizacao": None,
        "faccao": None,
        "status": None,
    }

    opcoes = await _opcoes_filtros()

    counter_ref: dict = {"w": None}
    galeria_ref: dict = {"w": None}

    async def _refresh() -> None:
        # 44 NPCs hoje: rows_per_page=500 traz todos numa galeria so.
        rows, total_atual = await _buscar_pagina_npcs_rica(
            page=1, rows_per_page=500,
            sort_by="nome", descending=False,
            **filtros,
        )
        if galeria_ref["w"]:
            galeria_ref["w"].set_content(_grade_npcs(rows))
        if counter_ref["w"]:
            counter_ref["w"].set_text(
                f"{total_atual} figuras — os que vivem, e os que já viveram"
            )

    def _schedule(coro) -> None:
        asyncio.create_task(coro)

    def set_busca(e) -> None:
        filtros["busca"] = (e.value or "").strip()
        ui.timer(0.05, lambda: _schedule(_refresh()), once=True)

    def set_camada(e) -> None:
        filtros["camada"] = e.value
        ui.timer(0.05, lambda: _schedule(_refresh()), once=True)

    def set_localizacao(e) -> None:
        filtros["localizacao"] = e.value
        ui.timer(0.05, lambda: _schedule(_refresh()), once=True)

    def set_faccao(e) -> None:
        filtros["faccao"] = e.value
        ui.timer(0.05, lambda: _schedule(_refresh()), once=True)

    def set_status(e) -> None:
        filtros["status"] = e.value
        ui.timer(0.05, lambda: _schedule(_refresh()), once=True)

    with ui.column().classes("gp-screen w-full min-h-screen p-0 gap-0"):
        with ui.column().classes("gp-inner w-full gap-4"):

            with ui.row().classes("w-full items-center gap-3"):
                ui.button(
                    icon="arrow_back",
                    on_click=lambda: ui.navigate.to("/oficina"),
                ).props("flat round dense color=amber-2")
                with ui.column().classes("gap-0"):
                    ui.label("Personagens").classes("text-3xl font-bold text-amber-200")
                    counter_ref["w"] = ui.label("").classes("text-sm text-zinc-400 italic")

            with ui.card().classes("gp-filtros w-full p-4"):
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

            galeria_ref["w"] = ui.html("").classes("w-full")

    await _refresh()


# ====================================================================
# PAGINA /oficina/npcs/{id} · DETALHE RICO (com try/except + dict)
# ====================================================================

_PERG = dict(
    folha="#fdf1dc", caixa="#f6ead0", pagina="#efe3c9", arte_bg="#efe2c4",
    tijolo="#58180d", regua="#922610", pill="#6e2410",
    txt="#2a1c0e", sec="#5a4632", rodape="#7a6648",
)
_PSERIF = "'Cinzel',serif"
_PBODY = "'Crimson Text',Georgia,serif"

def _pe(s):  # escape seguro
    return html.escape(str(s)) if s is not None else ""

def _p_pill(txto, *, forte=False):
    P = _PERG
    if forte:
        return (f'<span style="font-family:{_PSERIF};font-size:10px;letter-spacing:.05em;'
                f'color:#fdf1dc;background:{P["pill"]};border-radius:3px;padding:2px 8px;">{_pe(txto)}</span>')
    return (f'<span style="font-family:{_PSERIF};font-size:10px;letter-spacing:.05em;'
            f'color:{P["pill"]};border:1px solid {P["pill"]};border-radius:3px;padding:2px 8px;">{_pe(txto)}</span>')

def _p_secao(titulo, sub, corpo_html):
    P = _PERG
    sub_html = (f'<span style="font-family:{_PBODY};font-style:italic;font-size:12px;'
                f'letter-spacing:0;color:{P["sec"]};margin-left:10px;">{_pe(sub)}</span>') if sub else ""
    return (
        '<div style="margin-top:20px;">'
        f'<div style="font-family:{_PSERIF};font-size:13px;letter-spacing:.14em;color:{P["tijolo"]};'
        f'border-bottom:2px solid {P["regua"]};padding-bottom:5px;margin-bottom:12px;">{_pe(titulo).upper()}{sub_html}</div>'
        f'{corpo_html}</div>'
    )

def _p_kv(rotulo, valor):
    if not valor:
        return ""
    P = _PERG
    return (
        '<div style="display:flex;gap:12px;margin-bottom:6px;">'
        f'<div style="flex:none;width:150px;font-family:{_PSERIF};font-size:11px;letter-spacing:.08em;color:{P["sec"]};">{_pe(rotulo).upper()}</div>'
        f'<div style="flex:1;font-family:{_PBODY};font-size:15px;color:{P["txt"]};">{_pe(valor)}</div>'
        '</div>'
    )

def _p_bloco(rotulo, valor, *, italico=False):
    if not valor:
        return ""
    P = _PERG
    sty = "font-style:italic;" if italico else ""
    return (
        '<div style="margin-bottom:12px;">'
        f'<div style="font-family:{_PSERIF};font-size:11px;letter-spacing:.08em;color:{P["sec"]};margin-bottom:3px;">{_pe(rotulo).upper()}</div>'
        f'<div style="font-family:{_PBODY};font-size:15px;color:{P["txt"]};line-height:1.6;white-space:pre-line;{sty}">{_pe(valor)}</div>'
        '</div>'
    )

def _p_card(corpo_html, *, destaque=False):
    P = _PERG
    borda = f'border-left:3px solid {P["regua"]};' if destaque else f'border:1px solid {P["regua"]};'
    return (f'<div style="background:{P["caixa"]};{borda}border-radius:5px;padding:13px 16px;margin-bottom:9px;">{corpo_html}</div>')

def _p_big_five(rotulo, valor):
    P = _PERG
    v = valor if isinstance(valor, int) else 0
    return (
        '<div style="margin-bottom:9px;">'
        '<div style="display:flex;justify-content:space-between;align-items:baseline;">'
        f'<span style="font-family:{_PSERIF};font-size:12px;color:{P["txt"]};">{_pe(rotulo)}</span>'
        f'<span style="font-family:{_PSERIF};font-size:12px;color:{P["sec"]};">{v}</span></div>'
        f'<div style="height:7px;background:{P["arte_bg"]};border:1px solid {P["regua"]};border-radius:4px;margin-top:3px;overflow:hidden;">'
        f'<div style="height:100%;width:{max(0,min(100,v))}%;background:{P["regua"]};"></div></div>'
        '</div>'
    )

# cores semanticas em pergaminho (mantem o SIGNIFICADO, troca a paleta)
def _p_trust_txt(level):
    lv = level or 0
    if lv <= 3: return "trust " + str(lv)
    return "trust " + str(lv)

def _p_status_html(status):
    P = _PERG
    m = {"vivo": ("●", "vivo"), "morto": ("†", "morto"),
         "desaparecido": ("?", "desaparecido"), "exilado": ("→", "exilado")}
    ch, txt = m.get(status, ("—", status or "?"))
    return _p_pill(f"{ch} {txt}")

def _p_camada_html(camada):
    rot = {1: "Âncora", 2: "Recorrente", 3: "Fundo"}.get(camada, "?")
    return _p_pill(f"C{camada} · {rot}")

def _p_rel_html(rel: dict, nome_key: str, id_key: str) -> str:
    P = _PERG
    tipo = rel.get("tipo", "")
    alvo_id = rel.get(id_key)
    nome = rel.get(nome_key) or "(NPC removido)"
    if alvo_id:
        nome_html = f'<a href="/oficina/npcs/{alvo_id}" style="color:{P["tijolo"]};font-weight:700;text-decoration:none;">{_pe(nome)}</a>'
    else:
        nome_html = f'<span style="color:{P["sec"]};font-style:italic;">{_pe(nome)}</span>'
    nums = (f'{_p_pill("conf " + str(rel.get("confianca", 0)))} '
            f'{_p_pill("afe " + format(rel.get("afeicao", 0), "+d"))} '
            f'{_p_pill("res " + format(rel.get("respeito", 0), "+d"))}')
    if rel.get("medo"):
        nums += " " + _p_pill("medo " + str(rel["medo"]))
    hist = (f'<div style="font-family:{_PBODY};font-style:italic;font-size:13px;color:{P["sec"]};margin-top:4px;">{_pe(rel["historia_previa"])}</div>'
            if rel.get("historia_previa") else "")
    return _p_card(
        '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">'
        f'{_p_pill(tipo)}{nome_html}'
        f'<span style="margin-left:auto;display:flex;gap:6px;flex-wrap:wrap;">{nums}</span>'
        f'</div>{hist}'
    )


def _npc_corpo_html(data: dict) -> str:
    P = _PERG
    npc = data["npc"]
    B = []

    badges = _p_camada_html(npc.get("camada") or 3) + " " + _p_status_html(npc.get("status") or "desconhecido")
    for campo in ("raca", "sexo"):
        if npc.get(campo):
            badges += " " + _p_pill(npc[campo])
    if npc.get("idade_aparente"):
        badges += " " + _p_pill(f'idade {npc["idade_aparente"]}')
    if npc.get("idade_real") and npc["idade_real"] != npc.get("idade_aparente"):
        badges += " " + _p_pill(f'real: {npc["idade_real"]}', forte=True)
    if npc.get("singularidade"):
        badges += " " + _p_pill(f'singularidade {npc["singularidade"]}/10')
    ep = (f'<div style="font-family:{_PBODY};font-style:italic;font-size:16px;color:{P["sec"]};margin-top:3px;">{_pe(npc["epiteto"])}</div>'
          if npc.get("epiteto") else "")
    B.append(
        '<div style="flex:1;min-width:240px;">'
        f'<div style="font-family:{_PSERIF};font-weight:700;font-size:32px;color:{P["tijolo"]};line-height:1.05;">{_pe(npc["nome"])}</div>'
        f'{ep}<div style="margin-top:12px;display:flex;gap:6px;flex-wrap:wrap;">{badges}</div>'
        '</div>'
    )
    cabecalho_texto = "".join(B)

    S = []

    ident = _p_kv("Profissão", npc.get("profissao")) + _p_kv("Localização atual", npc.get("localizacao_atual")) + _p_kv("Localização base", npc.get("localizacao_base"))
    if npc.get("facoes"):
        chips = "".join(_p_pill(f) + " " for f in npc["facoes"])
        ident += (
            '<div style="display:flex;gap:12px;margin-bottom:6px;">'
            f'<div style="flex:none;width:150px;font-family:{_PSERIF};font-size:11px;letter-spacing:.08em;color:{P["sec"]};">FACÇÕES</div>'
            f'<div style="flex:1;display:flex;gap:5px;flex-wrap:wrap;">{chips}</div></div>'
        )
    if data.get("locations"):
        locs = "".join(f'<div style="font-family:{_PBODY};font-size:14px;color:{P["txt"]};">{_pe(l["nome"])} ({_pe(l["tipo_presenca"])})</div>' for l in data["locations"])
        ident += (
            '<div style="display:flex;gap:12px;margin-bottom:6px;">'
            f'<div style="flex:none;width:150px;font-family:{_PSERIF};font-size:11px;letter-spacing:.08em;color:{P["sec"]};">ENCONTRADO EM</div>'
            f'<div style="flex:1;">{locs}</div></div>'
        )
    if ident.strip():
        S.append(_p_secao("Identidade & Contexto", "", ident))

    bf = (_p_big_five("Abertura", npc.get("abertura")) + _p_big_five("Conscienciosidade", npc.get("conscienciosidade"))
          + _p_big_five("Extroversão", npc.get("extroversao")) + _p_big_five("Amabilidade", npc.get("amabilidade"))
          + _p_big_five("Neuroticismo", npc.get("neuroticismo")))
    if npc.get("valores"):
        bf += '<div style="margin-top:10px;display:flex;gap:5px;flex-wrap:wrap;">' + "".join(_p_pill(v) for v in npc["valores"]) + '</div>'
    bf += _p_bloco("Estilo de fala", npc.get("estilo_de_fala"), italico=True)
    S.append(_p_secao("Personalidade", "", bf))

    nar = ""
    if npc.get("tensao_interna"):
        nar += _p_card(f'<div style="font-family:{_PSERIF};font-size:11px;letter-spacing:.08em;color:{P["tijolo"]};">TENSÃO INTERNA</div>'
                       f'<div style="font-family:{_PBODY};font-size:15px;color:{P["txt"]};margin-top:4px;">{_pe(npc["tensao_interna"])}</div>', destaque=True)
    nar += _p_bloco("Identidade (prompt)", npc.get("prompt_identidade"))
    nar += _p_bloco("Diálogo (prompt)", npc.get("prompt_dialogo"))
    nar += _p_bloco("Contexto protagonista (prompt)", npc.get("prompt_contexto_protagonista"))
    nar += _p_bloco("Personality summary", npc.get("personality_summary"))
    if nar.strip():
        S.append(_p_secao("Campos do Narrador IA", "vão direto ao prompt do modelo", nar))

    psi = _p_bloco("Medo principal", npc.get("medo_principal"))
    if npc.get("medos_secundarios"):
        psi += '<div style="margin-bottom:12px;">' + f'<div style="font-family:{_PSERIF};font-size:11px;letter-spacing:.08em;color:{P["sec"]};margin-bottom:3px;">MEDOS SECUNDÁRIOS</div>' + "".join(f'<div style="font-family:{_PBODY};font-size:15px;color:{P["txt"]};">· {_pe(m)}</div>' for m in npc["medos_secundarios"]) + '</div>'
    psi += _p_bloco("Desejo oculto", npc.get("desejo_oculto"))
    psi += _p_bloco("Linha que não cruza", npc.get("linha_que_nao_cruza"))
    psi += _p_bloco("Maior arrependimento", npc.get("maior_arrependimento"))
    if psi.strip():
        S.append(_p_secao("Psicologia Profunda", "", psi))

    if data.get("emotional"):
        e = data["emotional"]
        val = e.get("humor_valence", 0) or 0
        def _kvbox(rot, valor):
            return (f'<div style="margin-right:28px;"><div style="font-family:{_PSERIF};font-size:10px;letter-spacing:.08em;color:{P["sec"]};">{_pe(rot).upper()}</div>'
                    f'<div style="font-family:{_PBODY};font-size:18px;color:{P["txt"]};">{valor}</div></div>')
        emo = ('<div style="display:flex;flex-wrap:wrap;align-items:flex-start;">'
               + _kvbox("Emoção dominante", _pe(e.get("emocao_dominante", "")))
               + _kvbox("Intensidade", f'{e.get("intensidade","?")}/10')
               + _kvbox("Estresse", f'{e.get("estresse_atual","?")}/100')
               + _kvbox("Humor (valência)", format(val, "+d"))
               + '</div>')
        if e.get("causa_principal"):
            emo += _p_bloco("Causa principal", e["causa_principal"], italico=True)
        S.append(_p_secao("Estado Emocional", "baseline canônico 312", emo))

    hist = _p_bloco("Resumo", npc.get("backstory_resumida"))
    if npc.get("backstory_completa"):
        hist += (f'<details style="margin-bottom:12px;"><summary style="font-family:{_PSERIF};font-size:12px;color:{P["tijolo"]};cursor:pointer;">História completa</summary>'
                 f'<div style="font-family:{_PBODY};font-size:15px;color:{P["txt"]};line-height:1.6;white-space:pre-line;margin-top:6px;">{_pe(npc["backstory_completa"])}</div></details>')
    hist += _p_bloco("Evento formativo", npc.get("evento_formativo"), italico=True)
    if hist.strip():
        S.append(_p_secao("História", "", hist))

    if npc.get("o_que_so_ele_pode_fazer") or npc.get("momento_de_singularidade"):
        sg = _p_bloco("O que só ele pode fazer", npc.get("o_que_so_ele_pode_fazer")) + _p_bloco("Momento de singularidade", npc.get("momento_de_singularidade"), italico=True)
        sub = f'{npc["singularidade"]}/10' if npc.get("singularidade") else ""
        S.append(_p_secao("Singularidade", sub, sg))

    if data.get("routine"):
        r = data["routine"]
        partes = ""
        for campo, lab in [("amanhecer","Amanhecer"),("manha","Manhã"),("meio_dia","Meio-dia"),("tarde","Tarde"),("noite","Noite"),("madrugada","Madrugada")]:
            if r.get(campo):
                partes += (f'<div style="margin-bottom:6px;"><div style="font-family:{_PSERIF};font-size:10px;letter-spacing:.08em;color:{P["sec"]};">{lab.upper()}</div>'
                           f'<div style="font-family:{_PBODY};font-size:14px;color:{P["txt"]};line-height:1.55;">{_pe(r[campo])}</div></div>')
        alt = r.get("rotina_alterada_por")
        if alt and isinstance(alt, dict) and alt.get("evento"):
            partes += _p_card(f'<div style="font-family:{_PSERIF};font-size:11px;color:{P["tijolo"]};">ALTERAÇÕES</div><div style="font-family:{_PBODY};font-size:14px;color:{P["txt"]};margin-top:4px;">{_pe(alt["evento"])}</div>', destaque=True)
        if partes.strip():
            S.append(_p_secao("Rotina Diária", "", partes))

    if data.get("secrets"):
        itens = ""
        for s in data["secrets"]:
            top = _p_pill(f'trust {s.get("trust_level_required",0)}')
            if s.get("impacto_emocional"):
                top += " " + _p_pill(f'impacto {s["impacto_emocional"]}/10')
            if s.get("is_discoverable") is False:
                top += " " + _p_pill("não-descoberta", forte=True)
            corpo = (f'<div style="display:flex;gap:6px;flex-wrap:wrap;">{top}</div>'
                     f'<div style="font-family:{_PSERIF};font-weight:700;font-size:15px;color:{P["tijolo"]};margin-top:5px;">{_pe(s.get("titulo",""))}</div>'
                     f'<div style="font-family:{_PBODY};font-size:14px;color:{P["txt"]};line-height:1.6;margin-top:3px;">{_pe(s.get("descricao_interna",""))}</div>')
            if s.get("versao_revelavel"):
                corpo += f'<div style="background:{P["pagina"]};border-radius:4px;padding:8px 10px;margin-top:6px;"><div style="font-family:{_PSERIF};font-size:10px;color:{P["sec"]};font-style:italic;">VERSÃO REVELÁVEL</div><div style="font-family:{_PBODY};font-size:14px;color:{P["txt"]};">{_pe(s["versao_revelavel"])}</div></div>'
            itens += _p_card(corpo)
        S.append(_p_secao("Segredos", f'{len(data["secrets"])} itens', itens))

    if data.get("goals"):
        itens = ""
        for g in data["goals"]:
            top = _p_pill(g.get("tipo","")) + " " + _p_pill(g.get("prazo_narrativo","")) + " " + _p_pill(g.get("nivel_de_consciencia") or "?")
            if g.get("progresso_percentual") is not None:
                top += " " + _p_pill(f'{g["progresso_percentual"]}%')
            if g.get("conflita_com_protagonista"):
                top += " " + _p_pill("conflita c/ protagonista", forte=True)
            itens += _p_card(f'<div style="display:flex;gap:6px;flex-wrap:wrap;">{top}</div>'
                             f'<div style="font-family:{_PBODY};font-size:14px;color:{P["txt"]};margin-top:5px;">{_pe(g.get("descricao",""))}</div>')
        S.append(_p_secao("Objetivos", f'{len(data["goals"])} itens', itens))

    if data.get("rels_out") or data.get("rels_in"):
        total = len(data["rels_out"]) + len(data["rels_in"])
        corpo = ""
        if data.get("rels_out"):
            corpo += f'<div style="font-family:{_PSERIF};font-size:11px;letter-spacing:.08em;color:{P["sec"]};margin:6px 0;">→ SENTIMENTOS DESTE NPC ({len(data["rels_out"])})</div>'
            corpo += "".join(_p_rel_html(r, "alvo_nome", "npc_alvo_id") for r in data["rels_out"])
        if data.get("rels_in"):
            corpo += f'<div style="font-family:{_PSERIF};font-size:11px;letter-spacing:.08em;color:{P["sec"]};margin:14px 0 6px;">← SENTIMENTOS DE OUTROS ({len(data["rels_in"])})</div>'
            corpo += "".join(_p_rel_html(r, "origem_nome", "npc_origem_id") for r in data["rels_in"])
        S.append(_p_secao("Relacionamentos", f'{total} vínculos', corpo))

    if data.get("family"):
        itens = ""
        for f in data["family"]:
            linha = _p_pill(f.get("grau_parentesco","")) + " " + _p_pill(f.get("status_parente") or "?")
            if f.get("parente_id"):
                linha += f' <a href="/oficina/npcs/{f["parente_id"]}" style="color:{P["tijolo"]};font-weight:700;text-decoration:none;">{_pe(f.get("parente_nome") or "?")}</a>'
            else:
                linha += f' <span style="color:{P["sec"]};font-style:italic;">{_pe(f.get("parente_nome") or "?")}</span>'
            if f.get("notas"):
                linha += f' <span style="font-family:{_PBODY};font-style:italic;font-size:13px;color:{P["sec"]};">— {_pe(f["notas"])}</span>'
            itens += f'<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:5px 0;">{linha}</div>'
        S.append(_p_secao("Família", f'{len(data["family"])} parentescos', itens))

    if data.get("memories"):
        itens = ""
        for m in data["memories"]:
            top = _p_pill(f'imp {m.get("importancia",0)}/10')
            if m.get("data_narrativa"):
                top += " " + _p_pill(m["data_narrativa"])
            if m.get("emocao_associada"):
                top += " " + _p_pill(m["emocao_associada"])
            if m.get("esta_suprimida"):
                top += " " + _p_pill("SUPRIMIDA", forte=True)
            corpo = (f'<div style="display:flex;gap:6px;flex-wrap:wrap;">{top}</div>'
                     f'<div style="font-family:{_PBODY};font-size:14px;color:{P["txt"]};line-height:1.6;margin-top:4px;">{_pe(m.get("descricao",""))}</div>')
            if m.get("gatilho_de_superficie"):
                corpo += f'<div style="font-family:{_PBODY};font-style:italic;font-size:13px;color:{P["sec"]};margin-top:3px;">Gatilho: {_pe(m["gatilho_de_superficie"])}</div>'
            if m.get("como_o_gpt_narra"):
                corpo += f'<div style="background:{P["pagina"]};border-left:2px solid {P["regua"]};border-radius:4px;padding:8px 10px;margin-top:6px;"><div style="font-family:{_PSERIF};font-size:10px;color:{P["tijolo"]};">COMO O NARRADOR MANIFESTA</div><div style="font-family:{_PBODY};font-style:italic;font-size:14px;color:{P["txt"]};">{_pe(m["como_o_gpt_narra"])}</div></div>'
            itens += _p_card(corpo)
        S.append(_p_secao("Memórias", f'{len(data["memories"])} episódios', itens))

    if data.get("knowledge"):
        itens = ""
        for k in data["knowledge"]:
            top = f'<span style="font-family:{_PSERIF};font-weight:700;font-size:14px;color:{P["tijolo"]};">{_pe(k.get("topico",""))}</span> ' + _p_pill(f'certeza {k.get("certeza",0)}%')
            if k.get("e_crenca_falsa"):
                top += " " + _p_pill("CRENÇA FALSA", forte=True)
            corpo = (f'<div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;">{top}</div>'
                     f'<div style="font-family:{_PBODY};font-size:14px;color:{P["txt"]};line-height:1.6;margin-top:4px;">{_pe(k.get("conteudo",""))}</div>')
            if k.get("fonte"):
                corpo += f'<div style="font-family:{_PBODY};font-style:italic;font-size:13px;color:{P["sec"]};margin-top:3px;">Fonte: {_pe(k["fonte"])}</div>'
            itens += _p_card(corpo)
        S.append(_p_secao("Conhecimento do Mundo", f'{len(data["knowledge"])} itens', itens))

    return cabecalho_texto, "".join(S)


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
        ui.add_head_html(CSS_PERGAMINHO)
        cab_texto, secoes_html = _npc_corpo_html(data)
        with ui.column().classes("w-full min-h-screen p-0 gap-0").style("background:#efe3c9;color:#2a1c0e;"):
            with ui.column().classes("w-full max-w-5xl mx-auto px-6 py-6 gap-0").style("box-sizing:border-box;"):
                ui.html(
                    '<div style="font-family:\'Cinzel\',serif;font-size:12px;letter-spacing:.1em;color:#7a6648;">'
                    '<a href="/oficina" style="color:#7a6648;text-decoration:none;">OFICINA</a> &middot; '
                    '<a href="/oficina/npcs" style="color:#7a6648;text-decoration:none;">NPCS</a> &middot; '
                    f'<span style="color:#5a4632;">{html.escape(npc.get("nome_curto") or npc.get("nome") or "?")}</span></div>'
                )
                with ui.row().classes("w-full items-start gap-6").style("background:#f6ead0;border:1px solid #922610;border-radius:6px;padding:20px;margin-top:14px;"):

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

                    ui.html(cab_texto).classes("flex-1")

            ui.html(secoes_html).classes("w-full")

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
