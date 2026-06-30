"""
Catedral do Alderyn — Oficina do Mestre
Módulo 4.2 · Páginas /oficina/npcs (lista + detalhe)

Módulo auto-contido. Expõe:
  • render_npcs_list_page(pool, request)  → renderiza /oficina/npcs
  • render_npc_detail_page(pool, npc_id)  → renderiza /oficina/npcs/{id}

Integração em main.py:

    from oficina.routes.npcs import render_npcs_list_page, render_npc_detail_page

    @ui.page('/oficina/npcs')
    async def npcs_list():
        await render_npcs_list_page(pool)

    @ui.page('/oficina/npcs/{npc_id:int}')
    async def npc_detail(npc_id: int):
        await render_npc_detail_page(pool, npc_id)

Dependências:
  • nicegui >= 3.10
  • asyncpg (usa pool compartilhado com o resto da Catedral)
  • Auth BaseHTTPMiddleware já configurado em main.py

Padrão seguido: home → lista → detalhe, consistente com Estrelas/Vocações.
Estilo: witcher-grey, cards escuros, cores mutadas.
"""
from nicegui import ui
from typing import Optional
import asyncpg

# ═══════════════════════════════════════════════════════════════════
# CORES & ESTILO
# ═══════════════════════════════════════════════════════════════════

# Paleta witcher-grey (consistente com resto da Catedral)
COLOR_BG_CARD = 'bg-stone-900'
COLOR_BG_SUBTLE = 'bg-stone-800'
COLOR_BORDER = 'border-stone-700'
COLOR_ACCENT = 'text-amber-500'
COLOR_ACCENT_BG = 'bg-amber-900/30'
COLOR_TEXT = 'text-stone-200'
COLOR_TEXT_MUTED = 'text-stone-400'
COLOR_TEXT_DIM = 'text-stone-500'

# Cores de status
STATUS_STYLES = {
    'vivo': ('text-emerald-400', 'bg-emerald-900/30', '●'),
    'morto': ('text-red-500', 'bg-red-900/30', '†'),
    'desaparecido': ('text-violet-400', 'bg-violet-900/30', '?'),
    'exilado': ('text-orange-400', 'bg-orange-900/30', '→'),
    'desconhecido': ('text-stone-400', 'bg-stone-800', '—'),
}

# Cores de camada
CAMADA_STYLES = {
    1: ('Âncora', 'text-amber-400', 'bg-amber-900/40'),
    2: ('Recorrente', 'text-sky-400', 'bg-sky-900/30'),
    3: ('Fundo', 'text-stone-400', 'bg-stone-800'),
}

# Cores de trust level (segredos)
def trust_color(level: int) -> str:
    if level <= 3: return 'text-emerald-400 bg-emerald-900/30'
    if level <= 6: return 'text-yellow-400 bg-yellow-900/30'
    if level <= 8: return 'text-orange-400 bg-orange-900/30'
    return 'text-red-400 bg-red-900/40'

# ═══════════════════════════════════════════════════════════════════
# QUERIES
# ═══════════════════════════════════════════════════════════════════

async def query_npcs_filter_options(pool: asyncpg.Pool) -> dict:
    """Retorna valores distintos para dropdowns de filtro."""
    async with pool.acquire() as conn:
        locs = await conn.fetch(
            "SELECT DISTINCT localizacao_base FROM npcs WHERE localizacao_base IS NOT NULL ORDER BY 1"
        )
        faccoes_raw = await conn.fetch(
            "SELECT DISTINCT unnest(facoes) AS f FROM npcs WHERE facoes IS NOT NULL ORDER BY 1"
        )
        return {
            'localizacoes': [r['localizacao_base'] for r in locs],
            'faccoes': [r['f'] for r in faccoes_raw],
        }

async def query_npcs_list(
    pool: asyncpg.Pool,
    busca: str = '',
    camada: Optional[int] = None,
    localizacao: Optional[str] = None,
    faccao: Optional[str] = None,
    status: Optional[str] = None,
    ordem: str = 'nome',
    pagina: int = 1,
    por_pagina: int = 20,
) -> tuple[list, int]:
    """Lista NPCs paginada com filtros. Retorna (rows, total)."""
    where_clauses = []
    params = []

    if busca:
        params.append(f'%{busca}%')
        idx = len(params)
        where_clauses.append(
            f"(nome ILIKE ${idx} OR nome_curto ILIKE ${idx} OR epiteto ILIKE ${idx})"
        )
    if camada is not None:
        params.append(camada)
        where_clauses.append(f"camada = ${len(params)}")
    if localizacao:
        params.append(localizacao)
        where_clauses.append(f"localizacao_base = ${len(params)}")
    if faccao:
        params.append(faccao)
        where_clauses.append(f"${len(params)} = ANY(facoes)")
    if status:
        params.append(status)
        where_clauses.append(f"status = ${len(params)}")

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    order_map = {
        'nome': 'nome ASC',
        'camada': 'camada ASC, nome ASC',
        'singularidade': 'COALESCE(singularidade, 0) DESC, nome ASC',
    }
    order_sql = order_map.get(ordem, 'nome ASC')

    async with pool.acquire() as conn:
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM npcs {where_sql}", *params
        )
        offset = (pagina - 1) * por_pagina
        rows = await conn.fetch(f"""
            SELECT id, nome, nome_curto, epiteto, raca, sexo,
                   idade_aparente, profissao, localizacao_base,
                   facoes, status, camada, singularidade
            FROM npcs
            {where_sql}
            ORDER BY {order_sql}
            LIMIT {por_pagina} OFFSET {offset}
        """, *params)
        return list(rows), total or 0

async def query_npc_detail(pool: asyncpg.Pool, npc_id: int) -> Optional[dict]:
    """Busca NPC + todas as tabelas associativas."""
    async with pool.acquire() as conn:
        npc = await conn.fetchrow("SELECT * FROM npcs WHERE id = $1", npc_id)
        if not npc:
            return None

        secrets = await conn.fetch(
            "SELECT * FROM npc_secrets WHERE npc_id = $1 ORDER BY trust_level_required, titulo",
            npc_id
        )
        goals = await conn.fetch(
            "SELECT * FROM npc_goals WHERE npc_id = $1 ORDER BY prazo_narrativo, progresso_percentual DESC",
            npc_id
        )
        rels = await conn.fetch("""
            SELECT r.*, n.nome AS alvo_nome, n.nome_curto AS alvo_nome_curto,
                   n.camada AS alvo_camada, n.status AS alvo_status
            FROM npc_relationships r
            LEFT JOIN npcs n ON r.npc_alvo_id = n.id
            WHERE r.npc_origem_id = $1
            ORDER BY r.tipo, alvo_nome
        """, npc_id)
        rels_inverse = await conn.fetch("""
            SELECT r.*, n.nome AS origem_nome, n.nome_curto AS origem_nome_curto,
                   n.camada AS origem_camada
            FROM npc_relationships r
            LEFT JOIN npcs n ON r.npc_origem_id = n.id
            WHERE r.npc_alvo_id = $1
            ORDER BY r.tipo, origem_nome
        """, npc_id)
        family = await conn.fetch(
            "SELECT * FROM npc_family WHERE npc_id = $1 ORDER BY grau_parentesco",
            npc_id
        )
        memories = await conn.fetch(
            "SELECT * FROM npc_memories WHERE npc_id = $1 ORDER BY importancia DESC, data_narrativa",
            npc_id
        )
        knowledge = await conn.fetch(
            "SELECT * FROM npc_knowledge WHERE npc_id = $1 ORDER BY certeza DESC, topico",
            npc_id
        )
        emotional = await conn.fetchrow(
            "SELECT * FROM npc_emotional_state WHERE npc_id = $1 ORDER BY criado_em DESC LIMIT 1",
            npc_id
        )
        routine = await conn.fetchrow(
            "SELECT * FROM npc_daily_routine WHERE npc_id = $1",
            npc_id
        )
        locations = await conn.fetch("""
            SELECT l.nome, l.tipo_local, ln.tipo_presenca, ln.descricao
            FROM location_npcs ln
            JOIN locations l ON ln.location_id = l.id
            WHERE ln.npc_id = $1
            ORDER BY l.nome
        """, npc_id)

        return {
            'npc': dict(npc),
            'secrets': [dict(s) for s in secrets],
            'goals': [dict(g) for g in goals],
            'rels': [dict(r) for r in rels],
            'rels_inverse': [dict(r) for r in rels_inverse],
            'family': [dict(f) for f in family],
            'memories': [dict(m) for m in memories],
            'knowledge': [dict(k) for k in knowledge],
            'emotional': dict(emotional) if emotional else None,
            'routine': dict(routine) if routine else None,
            'locations': [dict(l) for l in locations],
        }

# ═══════════════════════════════════════════════════════════════════
# COMPONENTES VISUAIS REUSÁVEIS
# ═══════════════════════════════════════════════════════════════════

def badge(text: str, classes: str = 'bg-stone-800 text-stone-300'):
    """Badge pequeno."""
    ui.label(text).classes(f'px-2 py-0.5 text-xs rounded-full {classes} font-mono')

def status_badge(status: str):
    cls, bg, char = STATUS_STYLES.get(status, STATUS_STYLES['desconhecido'])
    badge(f'{char} {status}', f'{cls} {bg}')

def camada_badge(camada: int):
    label, cls, bg = CAMADA_STYLES.get(camada, ('?', 'text-stone-400', 'bg-stone-800'))
    badge(f'C{camada} · {label}', f'{cls} {bg}')

def big_five_bar(label: str, value: int):
    """Renderiza barra horizontal para Big Five (0-100)."""
    with ui.row().classes('w-full items-center gap-2'):
        ui.label(label).classes(f'{COLOR_TEXT_MUTED} text-sm w-40')
        with ui.element('div').classes('flex-1 h-2 bg-stone-800 rounded-full overflow-hidden'):
            ui.element('div').classes(
                f'h-full bg-amber-500 transition-all'
            ).style(f'width: {value}%;')
        ui.label(f'{value}').classes(f'{COLOR_TEXT} font-mono text-xs w-8 text-right')

def section_header(text: str, subtitle: str = ''):
    with ui.row().classes('items-baseline gap-2 mb-2'):
        ui.label(text).classes(f'{COLOR_ACCENT} text-lg font-semibold tracking-wide')
        if subtitle:
            ui.label(subtitle).classes(f'{COLOR_TEXT_DIM} text-sm italic')

# ═══════════════════════════════════════════════════════════════════
# PÁGINA DE LISTA /oficina/npcs
# ═══════════════════════════════════════════════════════════════════

async def render_npcs_list_page(pool: asyncpg.Pool):
    """Renderiza /oficina/npcs com filtros, busca, paginação."""

    # Estado reativo
    state = {
        'busca': '', 'camada': None, 'localizacao': None,
        'faccao': None, 'status': None, 'ordem': 'nome',
        'pagina': 1, 'por_pagina': 20, 'total': 0,
    }

    options = await query_npcs_filter_options(pool)

    # Container principal com classe witcher-grey
    ui.query('body').classes(f'{COLOR_TEXT}').style('background: #1c1917;')

    with ui.column().classes('w-full max-w-7xl mx-auto p-6 gap-4'):
        # Cabeçalho
        with ui.row().classes('items-baseline justify-between w-full'):
            with ui.row().classes('items-baseline gap-3'):
                ui.link('← Oficina', '/oficina').classes(f'{COLOR_TEXT_MUTED} text-sm hover:{COLOR_ACCENT}')
                ui.label('NPCs').classes(f'{COLOR_ACCENT} text-3xl font-bold tracking-wide')
                total_label = ui.label('').classes(f'{COLOR_TEXT_DIM} text-sm')
            ui.label('Listagem · Fase 5B-3').classes(f'{COLOR_TEXT_DIM} text-xs italic')

        # Filtros
        with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-4'):
            with ui.row().classes('w-full gap-3 flex-wrap items-end'):
                busca_in = ui.input(
                    label='Busca (nome, nome_curto, epíteto)',
                    placeholder='ex: Hesar, Velar, patriarca'
                ).classes('flex-1 min-w-64').props('dense dark')

                camada_sel = ui.select(
                    options={None: 'Todas', 1: 'C1 Âncora', 2: 'C2 Recorrente', 3: 'C3 Fundo'},
                    label='Camada', value=None
                ).classes('w-40').props('dense dark')

                loc_sel = ui.select(
                    options={None: 'Todas', **{l: l for l in options['localizacoes']}},
                    label='Localização', value=None
                ).classes('w-48').props('dense dark')

                faccao_sel = ui.select(
                    options={None: 'Todas', **{f: f for f in options['faccoes']}},
                    label='Facção', value=None
                ).classes('w-48').props('dense dark')

                status_sel = ui.select(
                    options={None: 'Todos', 'vivo': '● vivo', 'morto': '† morto',
                             'desaparecido': '? desaparecido', 'exilado': '→ exilado'},
                    label='Status', value=None
                ).classes('w-40').props('dense dark')

                ordem_sel = ui.select(
                    options={'nome': 'Nome', 'camada': 'Camada', 'singularidade': 'Singularidade'},
                    label='Ordenar por', value='nome'
                ).classes('w-40').props('dense dark')

                ui.button('Limpar', on_click=lambda: reset_filters()).props('dense flat').classes(f'{COLOR_TEXT_MUTED}')

        # Container da tabela e paginação
        tabela_container = ui.column().classes('w-full gap-2')

        async def reload():
            """Recarrega a lista com os filtros atuais."""
            rows, total = await query_npcs_list(
                pool, state['busca'], state['camada'], state['localizacao'],
                state['faccao'], state['status'], state['ordem'],
                state['pagina'], state['por_pagina']
            )
            state['total'] = total
            total_label.set_text(f'({total} NPCs)')
            render_tabela(rows)

        def render_tabela(rows):
            tabela_container.clear()
            with tabela_container:
                if not rows:
                    with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-8'):
                        ui.label('Nenhum NPC encontrado com esses filtros.').classes(
                            f'{COLOR_TEXT_DIM} text-center italic'
                        )
                    return

                # Tabela
                with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-0 overflow-hidden'):
                    # Header da tabela
                    with ui.row().classes(
                        f'w-full px-4 py-2 {COLOR_BG_SUBTLE} border-b {COLOR_BORDER} '
                        f'text-xs {COLOR_TEXT_MUTED} uppercase tracking-wide font-semibold'
                    ):
                        ui.label('Nome').classes('w-64')
                        ui.label('Camada').classes('w-32')
                        ui.label('Raça').classes('w-28')
                        ui.label('Profissão').classes('flex-1 min-w-40')
                        ui.label('Localização').classes('w-40')
                        ui.label('Status').classes('w-32')
                        ui.label('Sing').classes('w-12 text-right')

                    # Linhas
                    for r in rows:
                        is_dead = r['status'] != 'vivo'
                        row_bg = 'hover:bg-stone-800/60 cursor-pointer transition-colors'
                        if is_dead:
                            row_bg += ' opacity-70'
                        row_border = 'border-b border-stone-800/50'

                        with ui.row().classes(
                            f'w-full px-4 py-3 items-center {row_bg} {row_border}'
                        ).on('click', lambda e, npc_id=r['id']: ui.navigate.to(f'/oficina/npcs/{npc_id}')):
                            # Nome + epíteto
                            with ui.column().classes('w-64 gap-0'):
                                ui.label(r['nome']).classes(f'{COLOR_TEXT} font-medium')
                                if r['epiteto']:
                                    ui.label(r['epiteto']).classes(
                                        f'{COLOR_TEXT_DIM} text-xs italic truncate max-w-60'
                                    )
                            # Camada
                            with ui.element('div').classes('w-32'):
                                camada_badge(r['camada'])
                            # Raça
                            ui.label(r['raca'] or '—').classes(f'{COLOR_TEXT_MUTED} text-sm w-28')
                            # Profissão (truncada)
                            prof = (r['profissao'] or '')[:60]
                            if len(r['profissao'] or '') > 60: prof += '…'
                            ui.label(prof).classes(f'{COLOR_TEXT_MUTED} text-sm flex-1 min-w-40')
                            # Localização
                            ui.label(r['localizacao_base'] or '—').classes(f'{COLOR_TEXT_MUTED} text-sm w-40')
                            # Status
                            with ui.element('div').classes('w-32'):
                                status_badge(r['status'] or 'desconhecido')
                            # Singularidade
                            sing = r['singularidade']
                            sing_color = COLOR_ACCENT if sing and sing >= 8 else COLOR_TEXT_MUTED
                            ui.label(str(sing) if sing else '—').classes(
                                f'{sing_color} font-mono text-sm w-12 text-right'
                            )

                # Paginação
                total_paginas = max(1, (state['total'] + state['por_pagina'] - 1) // state['por_pagina'])
                inicio = (state['pagina'] - 1) * state['por_pagina'] + 1
                fim = min(state['pagina'] * state['por_pagina'], state['total'])

                with ui.row().classes('w-full items-center justify-between mt-2'):
                    ui.label(f'Mostrando {inicio}–{fim} de {state["total"]}').classes(
                        f'{COLOR_TEXT_MUTED} text-sm'
                    )
                    with ui.row().classes('gap-1'):
                        ui.button(
                            '← Anterior',
                            on_click=lambda: change_page(state['pagina'] - 1)
                        ).props('dense flat').classes(f'{COLOR_TEXT}').bind_enabled_from(
                            state, 'pagina', lambda p: p > 1
                        )
                        ui.label(f'{state["pagina"]} / {total_paginas}').classes(
                            f'{COLOR_TEXT} font-mono px-3 py-1'
                        )
                        ui.button(
                            'Próximo →',
                            on_click=lambda: change_page(state['pagina'] + 1)
                        ).props('dense flat').classes(f'{COLOR_TEXT}').bind_enabled_from(
                            state, 'pagina', lambda p: p < total_paginas
                        )

        # Handlers reativos
        async def on_change():
            state['pagina'] = 1  # reset paginação quando filtra
            await reload()

        async def change_page(nova):
            total_paginas = max(1, (state['total'] + state['por_pagina'] - 1) // state['por_pagina'])
            if 1 <= nova <= total_paginas:
                state['pagina'] = nova
                await reload()

        def reset_filters():
            busca_in.set_value('')
            camada_sel.set_value(None)
            loc_sel.set_value(None)
            faccao_sel.set_value(None)
            status_sel.set_value(None)
            ordem_sel.set_value('nome')

        # Bindings — handlers async pra que on_change() seja awaited
        async def _on_busca(e):
            state.update({'busca': e.args or ''})
            await on_change()

        async def _on_camada(e):
            state.update({'camada': e.args})
            await on_change()

        async def _on_loc(e):
            state.update({'localizacao': e.args})
            await on_change()

        async def _on_faccao(e):
            state.update({'faccao': e.args})
            await on_change()

        async def _on_status(e):
            state.update({'status': e.args})
            await on_change()

        async def _on_ordem(e):
            state.update({'ordem': e.args})
            await on_change()

        busca_in.on('update:model-value', _on_busca)
        camada_sel.on('update:model-value', _on_camada)
        loc_sel.on('update:model-value', _on_loc)
        faccao_sel.on('update:model-value', _on_faccao)
        status_sel.on('update:model-value', _on_status)
        ordem_sel.on('update:model-value', _on_ordem)

        # Carga inicial
        await reload()

# ═══════════════════════════════════════════════════════════════════
# PÁGINA DE DETALHE /oficina/npcs/{id}
# ═══════════════════════════════════════════════════════════════════

async def render_npc_detail_page(pool: asyncpg.Pool, npc_id: int):
    """Detalhe rico com todos os cards: identidade, personalidade, prompts,
       psicologia, história, vida social, vida interior, vida diária."""

    data = await query_npc_detail(pool, npc_id)

    ui.query('body').classes(f'{COLOR_TEXT}').style('background: #1c1917;')

    if not data:
        with ui.column().classes('w-full max-w-4xl mx-auto p-6'):
            ui.link('← Voltar à lista', '/oficina/npcs').classes(f'{COLOR_TEXT_MUTED} text-sm')
            ui.label(f'NPC #{npc_id} não encontrado').classes(f'{COLOR_TEXT} text-2xl mt-4')
        return

    npc = data['npc']
    with ui.column().classes('w-full max-w-6xl mx-auto p-6 gap-4'):
        # Breadcrumb
        with ui.row().classes('items-center gap-2'):
            ui.link('← Oficina', '/oficina').classes(f'{COLOR_TEXT_MUTED} text-sm hover:{COLOR_ACCENT}')
            ui.label('/').classes(f'{COLOR_TEXT_DIM} text-sm')
            ui.link('NPCs', '/oficina/npcs').classes(f'{COLOR_TEXT_MUTED} text-sm hover:{COLOR_ACCENT}')
            ui.label('/').classes(f'{COLOR_TEXT_DIM} text-sm')
            ui.label(npc['nome_curto'] or npc['nome']).classes(f'{COLOR_TEXT} text-sm')

        # Cabeçalho principal
        with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-6'):
            with ui.row().classes('items-start justify-between w-full'):
                with ui.column().classes('gap-1 flex-1'):
                    ui.label(npc['nome']).classes(f'{COLOR_ACCENT} text-3xl font-bold tracking-wide')
                    if npc['epiteto']:
                        ui.label(npc['epiteto']).classes(f'{COLOR_TEXT_MUTED} text-lg italic')
                    with ui.row().classes('items-center gap-2 mt-3 flex-wrap'):
                        camada_badge(npc['camada'])
                        status_badge(npc['status'])
                        badge(f"{npc['raca']}", 'bg-stone-800 text-stone-300')
                        badge(f"{npc['sexo']}", 'bg-stone-800 text-stone-300')
                        badge(f"idade {npc['idade_aparente']}", 'bg-stone-800 text-stone-300')
                        if npc['idade_real'] and npc['idade_real'] != npc['idade_aparente']:
                            badge(
                                f"real: {npc['idade_real']}",
                                'bg-violet-900/40 text-violet-300 font-semibold'
                            )
                        if npc['singularidade']:
                            badge(
                                f"singularidade {npc['singularidade']}/10",
                                f'{trust_color(npc["singularidade"])}'
                            )

        # ─── Grid de cards (2 colunas em telas grandes) ───
        with ui.column().classes('w-full gap-4'):

            # ── Identidade & Contexto ──
            with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-5'):
                section_header('Identidade & Contexto')
                with ui.column().classes('gap-2'):
                    _kv('Profissão', npc['profissao'])
                    _kv('Localização atual', npc['localizacao_atual'])
                    _kv('Localização base', npc['localizacao_base'])
                    if npc['facoes']:
                        with ui.row().classes('items-start gap-2'):
                            ui.label('Facções').classes(f'{COLOR_TEXT_MUTED} text-sm w-40')
                            with ui.row().classes('gap-1 flex-wrap flex-1'):
                                for f in npc['facoes']:
                                    badge(f, f'{COLOR_ACCENT_BG} {COLOR_ACCENT}')
                    if data['locations']:
                        with ui.row().classes('items-start gap-2 mt-2'):
                            ui.label('Encontrado em').classes(f'{COLOR_TEXT_MUTED} text-sm w-40')
                            with ui.column().classes('gap-1 flex-1'):
                                for loc in data['locations']:
                                    ui.label(
                                        f"{loc['nome']} ({loc['tipo_presenca']})"
                                    ).classes(f'{COLOR_TEXT} text-sm')

            # ── Personalidade · Big Five + valores + estilo ──
            with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-5'):
                section_header('Personalidade')
                with ui.column().classes('gap-3'):
                    big_five_bar('Abertura', npc['abertura'])
                    big_five_bar('Conscienciosidade', npc['conscienciosidade'])
                    big_five_bar('Extroversão', npc['extroversao'])
                    big_five_bar('Amabilidade', npc['amabilidade'])
                    big_five_bar('Neuroticismo', npc['neuroticismo'])
                    if npc['valores']:
                        with ui.column().classes('mt-3 gap-2'):
                            ui.label('Valores').classes(f'{COLOR_TEXT_MUTED} text-sm')
                            with ui.row().classes('gap-1 flex-wrap'):
                                for v in npc['valores']:
                                    badge(v, f'{COLOR_ACCENT_BG} {COLOR_ACCENT}')
                    if npc['estilo_de_fala']:
                        _block('Estilo de fala', npc['estilo_de_fala'], italic=True)

            # ── Campos do Narrador AI ──
            with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-5'):
                section_header('Campos do Narrador AI', 'vão direto ao prompt do modelo')
                with ui.column().classes('gap-4'):
                    if npc['tensao_interna']:
                        with ui.element('div').classes(f'{COLOR_ACCENT_BG} border-l-2 border-amber-500 p-3 rounded'):
                            ui.label('TENSÃO INTERNA').classes(f'{COLOR_ACCENT} text-xs font-bold tracking-wider')
                            ui.label(npc['tensao_interna']).classes(f'{COLOR_TEXT} text-sm mt-1')
                    _block('Identidade (prompt)', npc['prompt_identidade'])
                    _block('Diálogo (prompt)', npc['prompt_dialogo'])
                    _block('Contexto protagonista (prompt)', npc['prompt_contexto_protagonista'])
                    _block('Personality summary', npc['personality_summary'])

            # ── Psicologia Profunda ──
            with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-5'):
                section_header('Psicologia Profunda')
                with ui.column().classes('gap-3'):
                    _block('Medo principal', npc['medo_principal'])
                    if npc['medos_secundarios']:
                        with ui.column().classes('gap-1'):
                            ui.label('Medos secundários').classes(f'{COLOR_TEXT_MUTED} text-sm')
                            for m in npc['medos_secundarios']:
                                ui.label(f'· {m}').classes(f'{COLOR_TEXT} text-sm ml-2')
                    _block('Desejo oculto', npc['desejo_oculto'])
                    _block('Linha que não cruza', npc['linha_que_nao_cruza'])
                    _block('Maior arrependimento', npc['maior_arrependimento'])

            # ── Estado Emocional Atual ──
            if data['emotional']:
                e = data['emotional']
                valence = e.get('humor_valence', 0)
                valence_color = 'text-emerald-400' if valence > 20 else (
                    'text-red-400' if valence < -20 else 'text-stone-400'
                )
                with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-5'):
                    section_header('Estado Emocional (baseline 312)')
                    with ui.row().classes('gap-4 flex-wrap'):
                        with ui.column().classes('gap-1'):
                            ui.label('Emoção dominante').classes(f'{COLOR_TEXT_MUTED} text-xs')
                            ui.label(e['emocao_dominante']).classes(f'{COLOR_ACCENT} text-lg font-semibold')
                        with ui.column().classes('gap-1'):
                            ui.label('Intensidade').classes(f'{COLOR_TEXT_MUTED} text-xs')
                            ui.label(f'{e["intensidade"]}/10').classes(f'{COLOR_TEXT} font-mono text-lg')
                        with ui.column().classes('gap-1'):
                            ui.label('Estresse').classes(f'{COLOR_TEXT_MUTED} text-xs')
                            ui.label(f'{e["estresse_atual"]}/100').classes(f'{COLOR_TEXT} font-mono text-lg')
                        with ui.column().classes('gap-1'):
                            ui.label('Humor (valência)').classes(f'{COLOR_TEXT_MUTED} text-xs')
                            ui.label(f'{valence:+d}').classes(f'{valence_color} font-mono text-lg font-semibold')
                    if e.get('causa_principal'):
                        _block('Causa principal', e['causa_principal'], italic=True)

            # ── História ──
            with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-5'):
                section_header('História')
                with ui.column().classes('gap-3'):
                    _block('Resumo', npc['backstory_resumida'])
                    if npc['backstory_completa']:
                        with ui.expansion('História completa', icon='history').classes('w-full').props('dense'):
                            ui.label(npc['backstory_completa']).classes(f'{COLOR_TEXT} text-sm leading-relaxed p-2')
                    _block('Evento formativo', npc['evento_formativo'], italic=True)

            # ── Singularidade ──
            if npc.get('o_que_so_ele_pode_fazer') or npc.get('momento_de_singularidade'):
                with ui.card().classes(f'w-full {COLOR_BG_CARD} border-l-2 border-amber-500 {COLOR_BORDER} p-5'):
                    section_header('Singularidade', f"{npc['singularidade']}/10")
                    with ui.column().classes('gap-3'):
                        _block('O que só ele pode fazer', npc['o_que_so_ele_pode_fazer'])
                        _block('Momento de singularidade', npc['momento_de_singularidade'], italic=True)

            # ── Rotina Diária ──
            if data['routine']:
                r = data['routine']
                with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-5'):
                    section_header('Rotina Diária')
                    with ui.column().classes('gap-2'):
                        for periodo, label_pt in [
                            ('amanhecer', 'Amanhecer'), ('manha', 'Manhã'),
                            ('meio_dia', 'Meio-dia'), ('tarde', 'Tarde'),
                            ('noite', 'Noite'), ('madrugada', 'Madrugada')
                        ]:
                            if r.get(periodo):
                                _kv_stacked(label_pt, r[periodo])
                    if r.get('rotina_alterada_por'):
                        alt = r['rotina_alterada_por']
                        if isinstance(alt, dict) and alt.get('evento'):
                            with ui.element('div').classes(f'{COLOR_ACCENT_BG} border-l-2 border-amber-500 p-3 rounded mt-2'):
                                ui.label('ALTERAÇÕES').classes(f'{COLOR_ACCENT} text-xs font-bold tracking-wider')
                                ui.label(alt['evento']).classes(f'{COLOR_TEXT} text-sm mt-1')

            # ── Segredos ──
            if data['secrets']:
                with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-5'):
                    section_header('Segredos', f'{len(data["secrets"])} itens')
                    with ui.column().classes('gap-3'):
                        for s in data['secrets']:
                            trust_c = trust_color(s['trust_level_required'])
                            with ui.element('div').classes(
                                f'border-l-2 {COLOR_BORDER} pl-3 py-1 hover:bg-stone-800/40 rounded'
                            ):
                                with ui.row().classes('items-center gap-2'):
                                    badge(f"trust {s['trust_level_required']}", trust_c)
                                    badge(f"impacto {s.get('impacto_emocional', '—')}/10", 'bg-stone-800 text-stone-400')
                                    if not s.get('is_discoverable'):
                                        badge('não-descoberta via confiança', 'bg-red-900/40 text-red-400')
                                ui.label(s['titulo']).classes(f'{COLOR_TEXT} font-semibold mt-1')
                                ui.label(s['descricao_interna']).classes(f'{COLOR_TEXT_MUTED} text-sm mt-1 leading-relaxed')
                                if s.get('versao_revelavel'):
                                    with ui.element('div').classes('mt-2 bg-stone-800/60 p-2 rounded'):
                                        ui.label('Versão revelável').classes(f'{COLOR_TEXT_DIM} text-xs italic')
                                        ui.label(s['versao_revelavel']).classes(f'{COLOR_TEXT} text-sm')

            # ── Objetivos ──
            if data['goals']:
                with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-5'):
                    section_header('Objetivos', f'{len(data["goals"])} itens')
                    with ui.column().classes('gap-2'):
                        for g in data['goals']:
                            with ui.element('div').classes(
                                f'border-l-2 {COLOR_BORDER} pl-3 py-1 hover:bg-stone-800/40 rounded'
                            ):
                                with ui.row().classes('items-center gap-2 flex-wrap'):
                                    badge(g['tipo'], 'bg-sky-900/40 text-sky-300')
                                    badge(g['prazo_narrativo'], 'bg-stone-800 text-stone-300')
                                    badge(
                                        g['nivel_de_consciencia'],
                                        'bg-violet-900/30 text-violet-300'
                                        if g['nivel_de_consciencia'] != 'consciente' else 'bg-stone-800 text-stone-300'
                                    )
                                    if g.get('progresso_percentual') is not None:
                                        badge(f"{g['progresso_percentual']}%", 'bg-stone-800 text-stone-300')
                                    if g.get('conflita_com_protagonista'):
                                        badge('conflita com protagonista', 'bg-red-900/40 text-red-400')
                                ui.label(g['descricao']).classes(f'{COLOR_TEXT} text-sm mt-1')

            # ── Relacionamentos ──
            if data['rels'] or data['rels_inverse']:
                with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-5'):
                    total_rels = len(data['rels']) + len(data['rels_inverse'])
                    section_header('Relacionamentos', f'{total_rels} vínculos')
                    with ui.column().classes('gap-2'):
                        # Saídas (origem=este NPC)
                        if data['rels']:
                            ui.label(f"→ Sentimentos deste NPC por outros ({len(data['rels'])})").classes(
                                f'{COLOR_TEXT_MUTED} text-xs uppercase mt-2'
                            )
                            for r in data['rels']:
                                _rel_line(r, alvo_key='alvo_nome', direction='to')
                        # Entradas (alvo=este NPC)
                        if data['rels_inverse']:
                            ui.label(f"← Sentimentos de outros por este NPC ({len(data['rels_inverse'])})").classes(
                                f'{COLOR_TEXT_MUTED} text-xs uppercase mt-2'
                            )
                            for r in data['rels_inverse']:
                                _rel_line(r, alvo_key='origem_nome', direction='from')

            # ── Família ──
            if data['family']:
                with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-5'):
                    section_header('Família', f'{len(data["family"])} parentescos')
                    with ui.column().classes('gap-2'):
                        for f in data['family']:
                            with ui.row().classes('items-center gap-3 py-1'):
                                badge(f['grau_parentesco'], 'bg-stone-800 text-stone-300')
                                badge(f['status_parente'], 'bg-stone-800 text-stone-400')
                                if f.get('parente_id'):
                                    ui.link(
                                        f['parente_nome'],
                                        f"/oficina/npcs/{f['parente_id']}"
                                    ).classes(f'{COLOR_TEXT} hover:{COLOR_ACCENT}')
                                else:
                                    ui.label(f['parente_nome']).classes(f'{COLOR_TEXT_MUTED} italic')
                                if f.get('notas'):
                                    ui.label(f'— {f["notas"]}').classes(f'{COLOR_TEXT_DIM} text-sm italic')

            # ── Memórias ──
            if data['memories']:
                with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-5'):
                    section_header('Memórias', f'{len(data["memories"])} episódios')
                    with ui.column().classes('gap-3'):
                        for m in data['memories']:
                            border = 'border-l-2 border-violet-500' if m.get('esta_suprimida') else f'border-l-2 {COLOR_BORDER.replace("border-", "border-")}'
                            with ui.element('div').classes(f'{border} pl-3 py-1 hover:bg-stone-800/40 rounded'):
                                with ui.row().classes('items-center gap-2'):
                                    badge(f"imp {m['importancia']}/10",
                                          trust_color(m['importancia']))
                                    if m.get('data_narrativa'):
                                        badge(m['data_narrativa'], 'bg-stone-800 text-stone-400')
                                    if m.get('emocao_associada'):
                                        badge(m['emocao_associada'], 'bg-sky-900/30 text-sky-300')
                                    if m.get('esta_suprimida'):
                                        badge('suprimida', 'bg-violet-900/60 text-violet-300 font-bold')
                                ui.label(m['descricao']).classes(f'{COLOR_TEXT} text-sm mt-1 leading-relaxed')
                                if m.get('gatilho_de_superficie'):
                                    ui.label(f"Gatilho: {m['gatilho_de_superficie']}").classes(
                                        f'{COLOR_TEXT_DIM} text-xs italic mt-1'
                                    )
                                if m.get('como_o_gpt_narra'):
                                    with ui.element('div').classes(f'{COLOR_ACCENT_BG} border-l border-amber-600 p-2 mt-2 rounded'):
                                        ui.label('Como o narrador manifesta').classes(f'{COLOR_ACCENT} text-xs font-bold')
                                        ui.label(m['como_o_gpt_narra']).classes(f'{COLOR_TEXT} text-sm italic')

            # ── Conhecimento ──
            if data['knowledge']:
                with ui.card().classes(f'w-full {COLOR_BG_CARD} border {COLOR_BORDER} p-5'):
                    section_header('Conhecimento do Mundo', f'{len(data["knowledge"])} itens')
                    with ui.column().classes('gap-2'):
                        for k in data['knowledge']:
                            cert_color = 'text-emerald-400' if k['certeza'] >= 80 else (
                                'text-yellow-400' if k['certeza'] >= 50 else 'text-orange-400'
                            )
                            with ui.element('div').classes(
                                f'border-l-2 {COLOR_BORDER} pl-3 py-1 hover:bg-stone-800/40 rounded'
                            ):
                                with ui.row().classes('items-center gap-2'):
                                    ui.label(k['topico']).classes(f'{COLOR_TEXT} font-semibold')
                                    badge(f"certeza {k['certeza']}%", f'{cert_color} bg-stone-800')
                                    if k.get('e_crenca_falsa'):
                                        badge('CRENÇA FALSA', 'bg-red-900/60 text-red-300 font-bold')
                                ui.label(k['conteudo']).classes(f'{COLOR_TEXT_MUTED} text-sm mt-1 leading-relaxed')
                                if k.get('fonte'):
                                    ui.label(f'Fonte: {k["fonte"]}').classes(f'{COLOR_TEXT_DIM} text-xs italic mt-1')

# ═══════════════════════════════════════════════════════════════════
# HELPERS DE RENDERIZAÇÃO
# ═══════════════════════════════════════════════════════════════════

def _kv(label: str, value: str):
    """Renderiza linha chave:valor."""
    if not value: return
    with ui.row().classes('items-start gap-2'):
        ui.label(label).classes(f'{COLOR_TEXT_MUTED} text-sm w-40')
        ui.label(value).classes(f'{COLOR_TEXT} text-sm flex-1')

def _kv_stacked(label: str, value: str):
    """Renderiza label em cima, valor embaixo."""
    if not value: return
    with ui.column().classes('gap-0.5'):
        ui.label(label.upper()).classes(f'{COLOR_TEXT_DIM} text-xs font-semibold tracking-wider')
        ui.label(value).classes(f'{COLOR_TEXT} text-sm leading-relaxed')

def _block(label: str, value: str, italic: bool = False):
    """Renderiza bloco de texto com label."""
    if not value: return
    with ui.column().classes('gap-1'):
        ui.label(label).classes(f'{COLOR_TEXT_MUTED} text-sm')
        classes = f'{COLOR_TEXT} text-sm leading-relaxed'
        if italic: classes += ' italic'
        ui.label(value).classes(classes)

def _rel_line(rel: dict, alvo_key: str, direction: str):
    """Renderiza uma linha de relacionamento."""
    conf = rel.get('confianca', 0)
    afeic = rel.get('afeicao', 0)
    resp = rel.get('respeito', 0)
    medo = rel.get('medo', 0)

    # Cor do tipo
    tipo = rel['tipo']
    tipo_color = {
        'amizade': 'bg-emerald-900/40 text-emerald-300',
        'amor': 'bg-pink-900/40 text-pink-300',
        'rivalidade': 'bg-orange-900/40 text-orange-300',
        'mentoria': 'bg-sky-900/40 text-sky-300',
        'divida': 'bg-violet-900/40 text-violet-300',
        'familiar': 'bg-amber-900/40 text-amber-300',
        'inimizade': 'bg-red-900/40 text-red-300',
        'respeito': 'bg-sky-900/30 text-sky-200',
        'medo': 'bg-violet-900/50 text-violet-200',
        'lealdade': 'bg-amber-900/40 text-amber-300',
        'neutro': 'bg-stone-800 text-stone-400',
    }.get(tipo, 'bg-stone-800 text-stone-300')

    alvo_id_key = 'npc_alvo_id' if direction == 'to' else 'npc_origem_id'
    alvo_id = rel.get(alvo_id_key)

    with ui.element('div').classes(f'border-l-2 {COLOR_BORDER} pl-3 py-1.5 hover:bg-stone-800/40 rounded'):
        with ui.row().classes('items-center gap-2 flex-wrap'):
            badge(tipo, tipo_color)
            nome_display = rel.get(alvo_key) or '(NPC removido)'
            if alvo_id:
                ui.link(nome_display, f'/oficina/npcs/{alvo_id}').classes(
                    f'{COLOR_TEXT} hover:{COLOR_ACCENT} font-medium'
                )
            else:
                ui.label(nome_display).classes(f'{COLOR_TEXT_MUTED} italic')
            with ui.row().classes('gap-1 ml-auto'):
                badge(f'conf {conf}', 'bg-stone-800 text-stone-400')
                badge(f'afe {afeic:+d}', 'bg-stone-800 text-stone-400')
                badge(f'res {resp:+d}', 'bg-stone-800 text-stone-400')
                if medo:
                    badge(f'medo {medo}', 'bg-violet-900/40 text-violet-300')
        if rel.get('historia_previa'):
            ui.label(rel['historia_previa']).classes(f'{COLOR_TEXT_MUTED} text-xs italic mt-1')
