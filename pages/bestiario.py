"""
Modulo Bestiario da Oficina do Mestre.

Paginas:
    pagina_lista_bestiario()     -> /oficina/bestiario
    pagina_criatura_detalhe(id)  -> /oficina/bestiario/{id}

Le de ref_criaturas. Mostra apenas criaturas com status_refino = 'refinado_v1'.
Estilo visual: dark fantasy (Witcher 3 bestiary).
v2: silhuetas SVG por tipo de criatura.
"""

import html
import json
from typing import Any, Optional

from nicegui import ui
from sqlalchemy import text

from db import get_session
from ui_helpers import aguardar_conexao_websocket, barra_nav


# ====================================================================
# QUERIES
# ====================================================================

_SQL_CONTAR_CANONIZADAS = text("""
    SELECT COUNT(*) FROM ref_criaturas
    WHERE status_refino = 'refinado_v1'
""")

_SQL_LISTAR_CANONIZADAS = text("""
    SELECT
        id, nome, slug, tipo, subtipo, cr,
        tamanho, origem, continente, perigo,
        pilar_associado, behavior_archetype,
        forca, destreza, constituicao,
        inteligencia, sabedoria, carisma,
        ca, hp_medio, velocidades,
        epigrafe, descricao,
        dados_json
    FROM ref_criaturas
    WHERE status_refino = 'refinado_v1'
    ORDER BY nome
""")

_SQL_BUSCAR_CRIATURA = text("""
    SELECT
        id, nome, slug, tipo, subtipo, cr, fonte,
        tamanho, alinhamento, origem,
        andar_primario, pilar_associado,
        continente, habitat, comportamento,
        behavior_archetype, morale_modifier, morale_immune,
        organizacao, perigo,
        forca, destreza, constituicao,
        inteligencia, sabedoria, carisma,
        ca, hp_medio, dado_vida, velocidades,
        resistencias, imunidades, vulnerabilidades,
        sentidos, percepcao_passiva, idiomas,
        epigrafe, descricao,
        supersticao_popular, sinais_presenca,
        fraqueza_conhecida, fraqueza_real,
        ecologia, loot_table,
        descricao_sensorial, camada_narrativa,
        dados_json, status_refino
    FROM ref_criaturas
    WHERE id = :id
""")


# ====================================================================
# HELPERS
# ====================================================================

async def contar_criaturas_canonizadas() -> int:
    async with get_session() as session:
        result = await session.execute(_SQL_CONTAR_CANONIZADAS)
        return result.scalar() or 0


def _safe_json(val: Any) -> dict | list | None:
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return None


def _cor_perigo(perigo: str) -> str:
    return {"Ameaca": "amber", "Destruidor": "red", "Letal": "purple"}.get(perigo, "zinc")


def _cor_origem(origem: str) -> str:
    return {"Natural": "green", "Ressonante": "blue", "Cicatricial": "purple",
            "Corrompida": "red", "Marginal": "pink"}.get(origem, "zinc")


# ====================================================================
# SILHUETAS SVG POR TIPO
# ====================================================================

_TIPO_CORES = {
    "besta":          ("#4a3728", "#6b4423", "#c9a96e"),
    "morto-vivo":     ("#2a2535", "#3d2b4a", "#8b6faa"),
    "aberracao":      ("#1a2a2a", "#2a3535", "#5a8b7a"),
    "constructo":     ("#2a2a30", "#35353d", "#7a7a8b"),
    "fada":           ("#1a2530", "#2a354a", "#6a8baa"),
    "planta":         ("#1a2a1a", "#2a3a2a", "#5a7a4a"),
    "monstruosidade": ("#2a1a1a", "#3a2525", "#8b5a5a"),
    "elemental":      ("#2a2015", "#3a2a1a", "#aa6a2a"),
}

_TIPO_PATHS = {
    "besta": '''<g transform="translate(90,50)" opacity="0.35" fill="{a}">
        <path d="M0,80 Q10,40 30,50 Q40,20 50,35 Q60,10 70,30 Q80,15 85,40
                 Q100,30 110,50 Q130,35 140,80 Q120,75 100,78 Q80,70 60,78 Q40,75 20,80 Z"/>
        <circle cx="45" cy="48" r="3" fill="#c9a96e" opacity="0.9"/>
        <circle cx="95" cy="48" r="3" fill="#c9a96e" opacity="0.9"/>
    </g><g transform="translate(55,65)" opacity="0.15" fill="{a}">
        <path d="M0,80 Q5,50 20,55 Q30,35 40,45 Q50,20 55,40 Q65,25 70,50
                 Q85,40 90,60 Q100,50 105,80 Z"/>
        <circle cx="38" cy="50" r="2" fill="#c9a96e" opacity="0.6"/>
        <circle cx="68" cy="50" r="2" fill="#c9a96e" opacity="0.6"/>
    </g>''',

    "morto-vivo": '''<g transform="translate(110,30)" opacity="0.35" fill="{a}">
        <path d="M50,0 Q80,10 90,40 Q95,60 85,80 Q80,95 60,105
                 Q40,110 20,105 Q5,95 0,80 Q-5,60 5,40 Q15,10 50,0 Z"/>
        <ellipse cx="30" cy="50" rx="12" ry="15" fill="#0d0b09"/>
        <ellipse cx="70" cy="50" rx="12" ry="15" fill="#0d0b09"/>
        <path d="M35,78 L40,85 L45,78 L50,85 L55,78 L60,85 L65,78"
              stroke="#0d0b09" stroke-width="2" fill="none"/>
        <circle cx="30" cy="48" r="4" fill="{a}" opacity="0.4"/>
        <circle cx="70" cy="48" r="4" fill="{a}" opacity="0.4"/>
    </g>''',

    "aberracao": '''<g transform="translate(100,35)" opacity="0.3" fill="{a}">
        <ellipse cx="60" cy="55" rx="50" ry="45"/>
        <path d="M20,30 Q0,10 -10,25" stroke="{a}" stroke-width="4" fill="none" opacity="0.6"/>
        <path d="M100,30 Q120,10 130,25" stroke="{a}" stroke-width="4" fill="none" opacity="0.6"/>
        <path d="M30,90 Q15,110 5,100" stroke="{a}" stroke-width="3" fill="none" opacity="0.5"/>
        <path d="M90,90 Q105,110 115,100" stroke="{a}" stroke-width="3" fill="none" opacity="0.5"/>
        <circle cx="40" cy="45" r="8" fill="#0d0b09"/>
        <circle cx="80" cy="45" r="8" fill="#0d0b09"/>
        <circle cx="60" cy="65" r="6" fill="#0d0b09"/>
        <circle cx="40" cy="45" r="3" fill="{a}" opacity="0.5"/>
        <circle cx="80" cy="45" r="3" fill="{a}" opacity="0.5"/>
        <circle cx="60" cy="65" r="2" fill="{a}" opacity="0.4"/>
    </g>''',

    "constructo": '''<g transform="translate(110,25)" opacity="0.35" fill="{a}">
        <rect x="20" y="0" width="60" height="30" rx="3"/>
        <rect x="15" y="35" width="70" height="50" rx="2"/>
        <rect x="5" y="38" width="15" height="40" rx="2"/>
        <rect x="80" y="38" width="15" height="40" rx="2"/>
        <rect x="25" y="90" width="20" height="35" rx="2"/>
        <rect x="55" y="90" width="20" height="35" rx="2"/>
        <rect x="30" y="8" width="14" height="14" rx="7" fill="#0d0b09"/>
        <rect x="56" y="8" width="14" height="14" rx="7" fill="#0d0b09"/>
        <circle cx="37" cy="15" r="4" fill="{a}" opacity="0.5"/>
        <circle cx="63" cy="15" r="4" fill="{a}" opacity="0.5"/>
    </g>''',

    "fada": '''<g transform="translate(120,40)" opacity="0.3" fill="{a}">
        <ellipse cx="40" cy="50" rx="15" ry="20"/>
        <circle cx="40" cy="30" r="12"/>
        <path d="M25,35 Q-10,15 5,50 Q10,55 25,48" opacity="0.6"/>
        <path d="M55,35 Q90,15 75,50 Q70,55 55,48" opacity="0.6"/>
        <path d="M25,40 Q-5,55 10,65 Q15,58 25,52" opacity="0.4"/>
        <path d="M55,40 Q85,55 70,65 Q65,58 55,52" opacity="0.4"/>
        <circle cx="35" cy="28" r="2" fill="{a}" opacity="0.7"/>
        <circle cx="45" cy="28" r="2" fill="{a}" opacity="0.7"/>
    </g><g opacity="0.15" fill="{a}">
        <circle cx="100" cy="60" r="2"/><circle cx="220" cy="80" r="1.5"/>
        <circle cx="130" cy="100" r="1"/><circle cx="200" cy="50" r="1.5"/>
    </g>''',

    "planta": '''<g transform="translate(80,20)" opacity="0.3" fill="{a}">
        <path d="M80,130 Q75,100 60,80 Q50,65 55,50 Q60,35 70,30
                 Q65,20 75,10 Q80,5 85,10 Q95,20 90,30
                 Q100,35 105,50 Q110,65 100,80 Q85,100 80,130 Z"/>
        <path d="M55,50 Q30,35 20,55 Q15,65 25,70 Q35,68 55,55" opacity="0.6"/>
        <path d="M105,50 Q130,35 140,55 Q145,65 135,70 Q125,68 105,55" opacity="0.6"/>
        <path d="M60,80 Q40,75 30,90 Q28,100 40,98 Q50,92 62,82" opacity="0.5"/>
        <path d="M100,80 Q120,75 130,90 Q132,100 120,98 Q110,92 98,82" opacity="0.5"/>
    </g>''',

    "monstruosidade": '''<g transform="translate(85,30)" opacity="0.3" fill="{a}">
        <path d="M75,0 Q90,5 100,20 Q110,10 115,25 Q120,35 110,45
                 Q120,55 115,70 Q110,85 100,95 Q90,105 75,110
                 Q60,105 50,95 Q40,85 35,70 Q30,55 40,45
                 Q30,35 35,25 Q40,10 50,20 Q60,5 75,0 Z"/>
        <circle cx="55" cy="40" r="8" fill="#0d0b09"/>
        <circle cx="95" cy="40" r="8" fill="#0d0b09"/>
        <circle cx="55" cy="40" r="3" fill="#8b3a3a" opacity="0.6"/>
        <circle cx="95" cy="40" r="3" fill="#8b3a3a" opacity="0.6"/>
        <path d="M60,65 Q75,75 90,65" stroke="#0d0b09" stroke-width="2" fill="none"/>
        <path d="M35,25 Q20,10 15,20" stroke="{a}" stroke-width="3" fill="none" opacity="0.5"/>
        <path d="M115,25 Q130,10 135,20" stroke="{a}" stroke-width="3" fill="none" opacity="0.5"/>
    </g>''',

    "elemental": '''<g transform="translate(110,25)" opacity="0.35" fill="{a}">
        <path d="M50,120 Q30,100 25,75 Q20,55 30,40 Q25,30 35,20
                 Q40,10 50,5 Q60,0 70,10 Q80,5 85,20
                 Q90,30 80,40 Q85,55 75,75 Q70,100 50,120 Z"/>
        <path d="M50,120 Q40,95 38,70 Q35,50 45,35 Q50,25 55,35
                 Q65,50 62,70 Q60,95 50,120 Z" fill="#0d0b09" opacity="0.3"/>
        <circle cx="42" cy="50" r="4" fill="#0d0b09"/>
        <circle cx="62" cy="50" r="4" fill="#0d0b09"/>
        <circle cx="42" cy="50" r="2" fill="{a}" opacity="0.8"/>
        <circle cx="62" cy="50" r="2" fill="{a}" opacity="0.8"/>
    </g><g opacity="0.12" fill="{a}">
        <circle cx="130" cy="60" r="2"/><circle cx="190" cy="80" r="1.5"/>
    </g>''',
}


def _svg_silhueta(tipo: str, w: int = 320, h: int = 160) -> str:
    t = (tipo or "").lower().strip()
    # normalizar acentos
    t = t.replace("\u00e3", "a").replace("\u00e7", "c").replace("\u00e1", "a")
    bg1, bg2, accent = _TIPO_CORES.get(t, ("#1a1a1a", "#2a2a2a", "#8b7355"))
    paths = _TIPO_PATHS.get(t, _TIPO_PATHS["monstruosidade"]).replace("{a}", accent)
    uid = t or "default"
    return f'''<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg"
        style="width:100%;height:{h}px;border-radius:4px 4px 0 0;">
        <defs>
            <linearGradient id="bg_{uid}_{w}" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="{bg1}"/>
                <stop offset="100%" stop-color="{bg2}"/>
            </linearGradient>
            <radialGradient id="glow_{uid}_{w}" cx="50%" cy="60%" r="50%">
                <stop offset="0%" stop-color="{accent}" stop-opacity="0.06"/>
                <stop offset="100%" stop-color="{bg1}" stop-opacity="0"/>
            </radialGradient>
        </defs>
        <rect width="{w}" height="{h}" fill="url(#bg_{uid}_{w})"/>
        <rect width="{w}" height="{h}" fill="url(#glow_{uid}_{w})"/>
        <ellipse cx="{w//2}" cy="{h-15}" rx="{w//4}" ry="6" fill="{accent}" opacity="0.08"/>
        {paths}
    </svg>'''


def _svg_silhueta_hero(tipo: str) -> str:
    return _svg_silhueta(tipo, w=800, h=300)




# ====================================================================
# CSS DARK FANTASY
# ====================================================================

_CSS_DARK_FANTASY = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
.bestiario-title { font-family: 'Cinzel', serif !important; letter-spacing: 2px; }
.bestiario-body { font-family: 'Crimson Text', Georgia, serif !important; line-height: 1.7; }
.criatura-card {
    background: #231f1b !important; border: 1px solid #8b7355 !important;
    border-radius: 4px; transition: border-color 0.3s, transform 0.2s; cursor: pointer;
}
.criatura-card:hover { border-color: #c9a96e !important; transform: translateY(-2px); }
.epigrafe-box {
    border-left: 2px solid #8b3a3a; padding: 12px 16px;
    background: rgba(139, 58, 58, 0.06);
    font-family: 'Crimson Text', Georgia, serif !important; font-style: italic;
}
.section-header {
    font-family: 'Cinzel', serif !important; font-size: 12px; font-weight: 600;
    letter-spacing: 3px; text-transform: uppercase; color: #c9a96e;
    border-bottom: 1px solid rgba(139, 115, 85, 0.2); padding-bottom: 8px; margin-bottom: 12px;
}
.weakness-box {
    background: rgba(42, 37, 32, 0.6); border: 1px solid rgba(139, 115, 85, 0.2);
    border-radius: 3px; padding: 14px 16px;
}
.eco-row { display: flex; gap: 12px; padding: 6px 0; border-bottom: 1px solid rgba(139, 115, 85, 0.08); }
.eco-label {
    font-family: 'Cinzel', serif !important; font-size: 11px; color: #c9a96e;
    letter-spacing: 1px; text-transform: uppercase; min-width: 90px;
}
.tag-pill {
    font-family: 'Cinzel', serif !important; font-size: 10px; letter-spacing: 1.5px;
    text-transform: uppercase; padding: 3px 10px;
    border: 1px solid rgba(139, 115, 85, 0.3); border-radius: 2px; color: #9a8b70;
}
</style>
"""


# ====================================================================
# PAGINA LISTA
# ====================================================================

async def pagina_lista_bestiario():
    await aguardar_conexao_websocket("Abrindo o Bestiario...")
    async with get_session() as session:
        result = await session.execute(_SQL_LISTAR_CANONIZADAS)
        rows = result.mappings().all()
    ui.add_head_html(_CSS_DARK_FANTASY)
    barra_nav("bestiario")
    with ui.column().classes("w-full min-h-screen bg-zinc-900 text-zinc-100 p-8 gap-6"):
        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("gap-0"):
                with ui.row().classes("items-center gap-3"):
                    ui.button(icon="arrow_back",
                              on_click=lambda: ui.navigate.to("/oficina"),
                              ).props("flat round dense color=amber-2")
                    ui.label("Bestiario de Alderyn").classes(
                        "text-3xl font-bold text-amber-200 bestiario-title")
                ui.label(f"{len(rows)} criaturas canonizadas").classes(
                    "text-sm text-zinc-400 italic ml-12")
        ui.separator().classes("bg-zinc-700")
        if not rows:
            with ui.column().classes("w-full items-center py-20 gap-4"):
                ui.icon("pets", size="4rem").classes("text-zinc-600")
                ui.label("O bestiario ainda esta vazio.").classes(
                    "text-xl text-zinc-500 bestiario-title")
            return
        with ui.row().classes("w-full gap-4 flex-wrap"):
            for row in rows:
                _render_card_lista(row)
        with ui.row().classes("w-full justify-center mt-auto pt-6"):
            ui.label(f"Bestiario de Alderyn - {len(rows)} criaturas").classes(
                "text-xs text-zinc-600 italic")


def _render_card_lista(row):
    cid = row["id"]
    nome = row["nome"] or "?"
    tipo = row["tipo"] or "?"
    cr = row["cr"] or 0
    origem = row["origem"] or "?"
    perigo = row["perigo"] or "?"
    continentes = row["continente"] or []
    epigrafe = row["epigrafe"] or ""
    dados = _safe_json(row.get("dados_json")) or {}
    portrait = dados.get("portrait_url")
    cor_p = _cor_perigo(perigo)
    cor_o = _cor_origem(origem)
    epi = epigrafe[:120] + "..." if len(epigrafe) > 120 else epigrafe

    with ui.card().classes("criatura-card flex-none p-0").style("width:320px").on(
        "click", lambda c=cid: ui.navigate.to(f"/oficina/bestiario/{c}")):
        if portrait:
            ui.image(portrait).classes("w-full").style(
                "height:160px;object-fit:cover;border-radius:4px 4px 0 0;")
        else:
            ui.html(_svg_silhueta(tipo))
        with ui.column().classes("w-full p-5 gap-3"):
            with ui.row().classes("w-full items-start justify-between"):
                ui.label(nome).classes("text-xl font-bold text-amber-200 bestiario-title")
                ui.badge(f"CR {cr}", color=f"{cor_p}-8").props("rounded")
            with ui.row().classes("gap-2 flex-wrap"):
                ui.badge(tipo, color="zinc-7").props("rounded outline")
                ui.badge(origem, color=f"{cor_o}-8").props("rounded outline")
                if isinstance(continentes, list) and continentes:
                    ui.badge(continentes[0] if len(continentes) == 1
                             else f"{continentes[0]} +{len(continentes)-1}",
                             color="zinc-6").props("rounded outline")
            with ui.row().classes("gap-3 mt-1"):
                for s, v in [("FOR", row.get("forca")), ("DES", row.get("destreza")),
                              ("CA", row.get("ca")), ("HP", row.get("hp_medio"))]:
                    if v is not None:
                        ui.label(f"{s} {v}").classes("text-xs font-mono text-zinc-500")
            if epi:
                ui.label(epi).classes(
                    "text-sm text-zinc-500 italic bestiario-body mt-1"
                ).style("line-height:1.4")
        with ui.row().classes("w-full px-5 py-3 items-center justify-between").style(
            "border-top:1px solid rgba(139,115,85,0.15)"):
            ui.label(perigo).classes(f"text-xs text-{cor_p}-400 bestiario-title")
            ui.label(f"id {cid}").classes("text-xs text-zinc-600 font-mono")


# ====================================================================
# PAGINA DETALHE
# ====================================================================

async def pagina_criatura_detalhe(criatura_id: int):
    await aguardar_conexao_websocket(f"Consultando criatura #{criatura_id}...")
    async with get_session() as session:
        result = await session.execute(_SQL_BUSCAR_CRIATURA, {"id": criatura_id})
        row = result.mappings().first()
    ui.add_head_html(_CSS_DARK_FANTASY)
    if not row:
        with ui.column().classes("w-full min-h-screen bg-zinc-900 items-center justify-center gap-4"):
            ui.label(f"Criatura #{criatura_id} nao encontrada").classes(
                "text-2xl text-zinc-400 bestiario-title")
            ui.button("Voltar", on_click=lambda: ui.navigate.to("/oficina/bestiario")).props("color=amber-8")
        return

    nome = row["nome"] or "?"
    tipo = row["tipo"] or "?"
    cr = row["cr"] or 0
    origem = row["origem"] or "?"
    perigo = row["perigo"] or "?"
    continentes = row["continente"] or []
    cont_str = ", ".join(continentes) if isinstance(continentes, list) else str(continentes)
    epigrafe = row["epigrafe"] or ""
    descricao = row["descricao"] or ""
    supersticao = row["supersticao_popular"] or ""
    sinais = row["sinais_presenca"] or ""
    fraq_conhecida = row["fraqueza_conhecida"] or ""
    fraq_real = row["fraqueza_real"] or ""
    habitat = row["habitat"] or ""
    organizacao = row["organizacao"] or ""
    desc_sensorial = row["descricao_sensorial"] or ""
    ecologia = _safe_json(row["ecologia"]) or {}
    loot = _safe_json(row["loot_table"]) or []
    camada_nar = _safe_json(row["camada_narrativa"]) or {}
    dados_json = _safe_json(row["dados_json"]) or {}
    portrait = dados_json.get("portrait_url")
    cor_p = _cor_perigo(perigo)

    with ui.column().classes("w-full min-h-screen bg-zinc-900 text-zinc-100 p-0"):
        # HERO
        with ui.column().classes("w-full px-8 pt-6 pb-2").style("background:#0d0b09;"):
            ui.button(icon="arrow_back",
                      on_click=lambda: ui.navigate.to("/oficina/bestiario"),
                      ).props("flat round dense color=amber-2")
        if portrait:
            ui.image(portrait).classes("w-full").style(
                "height:400px;object-fit:cover;object-position:center 30%;"
                "border-bottom:1px solid #8b7355;")
        else:
            ui.html(_svg_silhueta_hero(tipo))
        with ui.column().classes("w-full px-8 py-4 gap-1").style(
            "background:#0d0b09;border-bottom:1px solid #8b7355;"):
            ui.label(nome).classes("text-4xl font-bold text-amber-100 bestiario-title").style(
                "letter-spacing:3px;text-transform:uppercase;")
            ui.label(f"{origem} - {cont_str} - {row.get('andar_primario','Superficie')}").classes(
                "text-sm text-amber-600 bestiario-title").style(
                "letter-spacing:3px;text-transform:uppercase;")

        # STATS BAR
        with ui.row().classes("w-full").style(
            "background:#2a2520;border-bottom:1px solid rgba(139,115,85,0.3);"):
            for label, val, hl in [("CR",cr,True),("FOR",row["forca"] or 0,False),
                ("DES",row["destreza"] or 0,False),("CON",row["constituicao"] or 0,False),
                ("INT",row["inteligencia"] or 0,False),("SAB",row["sabedoria"] or 0,False),
                ("CAR",row["carisma"] or 0,False),("CA",row["ca"] or 0,True),
                ("HP",row["hp_medio"] or 0,False)]:
                with ui.column().classes("flex-1 items-center py-3").style(
                    "border-right:1px solid rgba(139,115,85,0.1);"):
                    ui.label(label).classes("text-xs text-zinc-500 bestiario-title").style("letter-spacing:2px;")
                    c = "text-amber-300" if hl else "text-zinc-200"
                    ui.label(str(val)).classes(f"text-lg font-bold {c} bestiario-title")
            with ui.column().classes("flex-1 items-center py-3"):
                ui.label("PERIGO").classes("text-xs text-zinc-500 bestiario-title").style("letter-spacing:2px;")
                ui.badge(perigo, color=f"{cor_p}-8").props("rounded")

        # CONTENT
        with ui.column().classes("w-full p-8 gap-6 max-w-4xl mx-auto"):
            if epigrafe:
                ui.html(f'<div class="epigrafe-box"><span style="color:#9a8b70;font-size:16px;">{html.escape(epigrafe)}</span></div>')
            with ui.row().classes("gap-2 flex-wrap"):
                for t in [tipo, row.get("tamanho",""), origem, row.get("pilar_associado",""),
                           row.get("behavior_archetype","")]:
                    if t and t != "Nenhum":
                        ui.html(f'<span class="tag-pill">{html.escape(t)}</span>')
            if descricao: _render_section("Aparencia", descricao)
            if habitat: _render_section("Habitat", habitat)
            if organizacao: _render_section("Organizacao", organizacao)
            if supersticao: _render_section("Supersticao Popular", supersticao)
            if sinais: _render_section("Sinais de Presenca", sinais)
            if fraq_conhecida or fraq_real:
                ui.html('<div class="section-header">Fraquezas</div>')
                with ui.row().classes("w-full gap-4"):
                    if fraq_conhecida:
                        with ui.column().classes("flex-1"):
                            ui.html(f'''<div class="weakness-box">
                                <div style="font-family:Cinzel,serif;font-size:11px;color:#c9a96e;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">Conhecida (povo)</div>
                                <div class="bestiario-body" style="font-size:14px;color:#9a8b70;">{html.escape(fraq_conhecida)}</div></div>''')
                    if fraq_real:
                        with ui.column().classes("flex-1"):
                            ui.html(f'''<div class="weakness-box">
                                <div style="font-family:Cinzel,serif;font-size:11px;color:#c9a96e;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">Real (cacador)</div>
                                <div class="bestiario-body" style="font-size:14px;color:#9a8b70;">{html.escape(fraq_real)}</div></div>''')
            if ecologia:
                ui.html('<div class="section-header">Cadeia Ecologica</div>')
                for chave in ["presa","predador","competidor","simbionte","indicador"]:
                    items = ecologia.get(chave, [])
                    if items:
                        for item in (items if isinstance(items, list) else [items]):
                            ui.html(f'<div class="eco-row"><span class="eco-label">{chave}</span><span style="font-size:14px;color:#9a8b70;">{html.escape(str(item))}</span></div>')
            if loot:
                ui.html('<div class="section-header">Materiais Coletaveis</div>')
                for item in loot:
                    with ui.card().classes("w-full p-3").style(
                        "background:rgba(42,37,32,0.4);border:1px solid rgba(139,115,85,0.15);border-radius:3px;").props("flat"):
                        with ui.row().classes("items-center gap-2"):
                            ui.label(item.get("material","?")).classes("text-sm font-bold text-amber-200 bestiario-title")
                            ui.badge(item.get("raridade","?"), color="zinc-7").props("rounded outline")
                        if item.get("uso"):
                            ui.label(item["uso"]).classes("text-sm text-zinc-400 mt-1 bestiario-body")
            if desc_sensorial: _render_section("Encontro - Descricao Sensorial", desc_sensorial)
            if camada_nar:
                ui.html('<div class="section-header">Camada Narrativa (IA)</div>')
                for k, lab in [("cheiro","Cheiro"),("som","Som"),("descoberta_fazendo","Descoberta Fazendo"),
                               ("quer","Quer")]:
                    if camada_nar.get(k): _render_subsection(lab, camada_nar[k])
                falas = camada_nar.get("falas_exemplo")
                if falas:
                    if isinstance(falas, list): _render_subsection("Falas", " / ".join(falas))
                    elif isinstance(falas, str) and falas.lower() not in ("null","n/a"):
                        _render_subsection("Falas", falas)
                desf = camada_nar.get("desfechos_nao_combate", [])
                if desf and isinstance(desf, list):
                    _render_subsection("Desfechos Nao-Combate", "\n".join(f"* {d}" for d in desf))
        with ui.row().classes("w-full px-8 py-4 items-center justify-between").style(
            "background:#2a2520;border-top:1px solid rgba(139,115,85,0.2);"):
            ui.label("Bestiario de Alderyn").classes("text-xs text-zinc-500 bestiario-title").style("letter-spacing:2px;")
            fonte = row.get("fonte", "")
            ui.label(f"id {criatura_id} - {fonte}" if fonte else f"id {criatura_id}").classes(
                "text-xs text-zinc-600 font-mono")


# ====================================================================
# RENDER HELPERS
# ====================================================================

def _render_section(titulo: str, conteudo: str):
    ui.html(f'<div class="section-header">{titulo}</div>')
    ui.html(f'<div class="bestiario-body" style="color:#d4c5a9;font-size:16px;">{html.escape(conteudo).replace(chr(10), "<br>")}</div>')


def _render_subsection(titulo: str, conteudo: str):
    ui.html(f'''<div style="margin-bottom:12px;">
        <span style="font-family:Cinzel,serif;font-size:11px;color:#c9a96e;letter-spacing:1px;text-transform:uppercase;">{titulo}</span>
        <div class="bestiario-body" style="color:#9a8b70;font-size:14px;margin-top:4px;">{html.escape(conteudo).replace(chr(10), "<br>")}</div>
    </div>''')
