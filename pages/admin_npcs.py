"""
Central de Admin do Alderyn — Aba NPCs (Onda 1).

VISAO_central_admin_alderyn_v1 (Aba 1) + SPEC_gravura_imagem_mae_admin_npcs_v1 (Fase 4).

Rotas (registradas em oficina_app.py, mesmo padrao do Atelie):
  /oficina/admin/npcs            -> lista: miniatura + nome + bolinha de status
                                    (verde = tem imagem-mae / vermelho = sem retrato)
  /oficina/admin/npcs/{npc_id}   -> detalhe: mae grande + ancora (read-only) +
                                    galeria de candidatas + Subir imagem +
                                    Definir como mae

Decisoes travadas (Gabriel, Onda 1):
- Upload de qualquer imagem e caminho de PRIMEIRA CLASSE (decisao 5 da SPEC):
  arquivo -> R2 (alderyn-npcs) -> linha status='candidata' em npc_imagens ->
  so vira mae pelo botao "Definir como mae".
- "Definir como mae" ESCREVE direto no banco, blindado em codigo (shape aprovado):
  pre-check FOR UPDATE + rebaixa a canonica antiga pra 'arquivada' + promove +
  sincroniza npcs.imagem_url + post-check, tudo NUMA transacao. O indice unico
  parcial (1 canonica por npc — uq_npc_imagens_uma_canonica, ja vivo no banco)
  e a trava dura; o post-check da o erro amigavel na UI.
- Vocabulario da SPEC ('candidata'/'arquivada'): EXIGE o CHECK de
  npc_imagens.status atualizado (ALTER do Gabriel no pgAdmin) — sem o ALTER, o
  INSERT do upload falha com CheckViolation (erro visivel na UI, nada corrompe).
- Ordenacao da lista: ALFABETICA (ajuste 3 — o alvo da onda e a Elara, que e
  verde; vermelhos-no-topo fica pra Onda 2). Busca por nome a mao.
- SEM geracao de imagem nesta onda (fal/img2img e Onda 2; quando chegar:
  FLUX.1 dev -> fal-ai/flux-lora*, NUNCA FLUX.2). O jogo segue leitura pura.

Padrao de banco: asyncpg direto, espelho de pages/atelie_queries.py.
IMPORT LAZY de r2_storage (dentro do handler de upload): importar este modulo
nao exige credencial R2 (a suite coleta sem .env completo).
"""

from __future__ import annotations

import os
import traceback
from typing import Optional

import asyncpg
from nicegui import ui

from ui_helpers import aguardar_conexao_websocket


# =============================================================================
# CONSTANTES + HELPERS PUROS (testaveis sem banco/UI)
# =============================================================================

_TIPOS_ACEITOS = {"image/jpeg", "image/png", "image/webp"}
_MAX_UPLOAD_MB = 10

# bolinha de status da lista: (cor, rotulo acessivel)
_DOT_VERDE = ("#22c55e", "tem imagem-mãe")
_DOT_VERMELHO = ("#ef4444", "sem retrato")

# rotulos PT (com acento) dos campos curtos da ancora — os DADOS ja vem do banco
# com acento; isto so conserta os labels hardcoded (polimento Onda 1, item 4).
_ROTULOS_ANCORA = {
    "rosto": "rosto",
    "olhos": "olhos",
    "cabelo": "cabelo",
    "pele": "pele",
    "wardrobe_padrao": "vestuário padrão",
    "iluminacao_tematica": "iluminação temática",
}


def _dot_status(tem_mae: bool) -> tuple[str, str]:
    """PURO: bolinha da lista. Verde = existe linha canonica em npc_imagens;
    vermelho = nao existe. (Fonte de verdade e npc_imagens, nao npcs.imagem_url.)"""
    return _DOT_VERDE if tem_mae else _DOT_VERMELHO


def _validar_upload(content_type: Optional[str], tamanho_bytes: int) -> Optional[str]:
    """PURO: valida um upload ANTES de gastar banda com o R2.
    Retorna a mensagem de erro (str) ou None quando o arquivo passa."""
    if not content_type or content_type.lower() not in _TIPOS_ACEITOS:
        return f"Tipo não aceito ({content_type or 'desconhecido'}). Use JPG, PNG ou WEBP."
    if tamanho_bytes <= 0:
        return "Arquivo vazio."
    if tamanho_bytes > _MAX_UPLOAD_MB * 1024 * 1024:
        return f"Arquivo grande demais ({tamanho_bytes / (1024 * 1024):.1f} MB; teto {_MAX_UPLOAD_MB} MB)."
    return None


def _r2_key_da_url(url: str) -> str:
    """PURO: a key R2 e o caminho depois do dominio publico (mesma convencao do
    pipeline_geracao: tudo na raiz do bucket -> ultimo segmento)."""
    return (url or "").rsplit("/", 1)[-1]


# =============================================================================
# BANCO (asyncpg direto, espelho de atelie_queries)
# =============================================================================

async def _conectar() -> asyncpg.Connection:
    """Conecta ao Neon. Caller fecha (conn.close()). statement_cache_size=0
    obrigatorio com o pooler do Neon em transaction mode."""
    db_url = os.environ.get("DATABASE_URL", "").replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    if not db_url:
        raise RuntimeError("DATABASE_URL nao definida no .env")
    return await asyncpg.connect(db_url, statement_cache_size=0)


async def _listar_npcs_com_status(busca: str = "") -> list[dict]:
    """Lista pro grid: id, nome, miniatura (npcs.imagem_url) + tem_mae (EXISTS
    canonica em npc_imagens). Alfabetica (ajuste 3). Busca via ILIKE bind param."""
    conn = await _conectar()
    try:
        sql = (
            "SELECT n.id, n.nome, n.imagem_url, "
            "EXISTS (SELECT 1 FROM npc_imagens i "
            "        WHERE i.npc_id = n.id AND i.status = 'canonica') AS tem_mae "
            "FROM npcs n "
        )
        args: list = []
        if busca.strip():
            sql += "WHERE n.nome ILIKE $1 "
            args.append(f"%{busca.strip()}%")
        sql += "ORDER BY n.nome"
        rows = await conn.fetch(sql, *args)
        return [dict(r) for r in rows]
    finally:
        await conn.close()


async def _carregar_detalhe_npc(npc_id: int) -> Optional[dict]:
    """Detalhe: dados do NPC (ancora completa) + a canonica + a galeria de
    nao-canonicas (candidatas novas E legadas 'aprovada'/'rascunho' — qualquer
    uma pode virar mae; 'arquivada'/'aposentada' ficam visiveis como historico)."""
    conn = await _conectar()
    try:
        npc = await conn.fetchrow(
            "SELECT id, nome, imagem_url, rosto, olhos, cabelo, pele, "
            "       wardrobe_padrao, iluminacao_tematica, "
            "       descricao_ancora_pt, descricao_ancora_en "
            "FROM npcs WHERE id = $1",
            npc_id,
        )
        if npc is None:
            return None
        canonica = await conn.fetchrow(
            "SELECT id, url, rotulo_narrativo, modelo_ia, criado_em "
            "FROM npc_imagens WHERE npc_id = $1 AND status = 'canonica' "
            "ORDER BY criado_em DESC LIMIT 1",
            npc_id,
        )
        galeria = await conn.fetch(
            "SELECT id, url, rotulo_narrativo, status, modelo_ia, criado_em "
            "FROM npc_imagens WHERE npc_id = $1 AND status <> 'canonica' "
            "ORDER BY criado_em DESC",
            npc_id,
        )
        return {
            "npc": dict(npc),
            "canonica": dict(canonica) if canonica else None,
            "galeria": [dict(r) for r in galeria],
        }
    finally:
        await conn.close()


async def _inserir_candidata_upload(
    npc_id: int, url: str, rotulo: Optional[str]
) -> int:
    """INSERT do upload como CANDIDATA (decisao 5: primeira classe; nada vira mae
    aqui). modelo_ia='upload' (coluna sem CHECK, confirmado no information_schema)."""
    conn = await _conectar()
    try:
        row = await conn.fetchrow(
            "INSERT INTO npc_imagens "
            "  (npc_id, url, r2_key, rotulo_narrativo, status, modelo_ia, "
            "   e_principal, custo_usd, criado_em) "
            "VALUES ($1, $2, $3, $4, 'candidata', 'upload', FALSE, 0, NOW()) "
            "RETURNING id",
            npc_id, url, _r2_key_da_url(url), (rotulo or "Upload manual"),
        )
        return row["id"]
    finally:
        await conn.close()


async def definir_como_mae(npc_id: int, imagem_id: int) -> str:
    """A transacao 'Definir como mae' — shape aprovado por Gabriel (Onda 1).

    NUMA transacao: pre-check FOR UPDATE -> rebaixa canonica antiga pra
    'arquivada' -> promove a escolhida -> sincroniza npcs.imagem_url ->
    post-check (1 canonica exata + ponteiro batendo). Qualquer violacao levanta
    ValueError com mensagem amigavel e a transacao REVERTE inteira. A trava
    dura contra 2 maes e o indice unico parcial do banco (independente daqui).

    Retorna a URL da nova mae (pro refresh da UI)."""
    conn = await _conectar()
    try:
        async with conn.transaction():
            # PRE-CHECK: a escolhida existe, e DESTE npc e ainda nao e a mae
            alvo = await conn.fetchrow(
                "SELECT id, url FROM npc_imagens "
                "WHERE id = $1 AND npc_id = $2 AND status <> 'canonica' "
                "FOR UPDATE",
                imagem_id, npc_id,
            )
            if alvo is None:
                raise ValueError(
                    "Imagem nao encontrada pra este NPC (ou ja e a imagem-mae)."
                )
            # 1) rebaixa a mae atual (0 linhas OK: NPC ainda sem mae)
            await conn.execute(
                "UPDATE npc_imagens SET status = 'arquivada', e_principal = FALSE "
                "WHERE npc_id = $1 AND status = 'canonica'",
                npc_id,
            )
            # 2) promove a escolhida
            await conn.execute(
                "UPDATE npc_imagens SET status = 'canonica', e_principal = TRUE "
                "WHERE id = $1 AND npc_id = $2",
                imagem_id, npc_id,
            )
            # 3) sincroniza o ponteiro rapido que o jogo le (gravura.url_imagem_mae)
            await conn.execute(
                "UPDATE npcs SET imagem_url = $1 WHERE id = $2",
                alvo["url"], npc_id,
            )
            # POST-CHECK: exatamente UMA canonica e o ponteiro batendo
            n_can = await conn.fetchval(
                "SELECT COUNT(*) FROM npc_imagens "
                "WHERE npc_id = $1 AND status = 'canonica'",
                npc_id,
            )
            if n_can != 1:
                raise ValueError(
                    f"Post-check falhou: {n_can} canonicas (esperado 1). Nada foi gravado."
                )
            ptr = await conn.fetchval(
                "SELECT imagem_url FROM npcs WHERE id = $1", npc_id
            )
            if ptr != alvo["url"]:
                raise ValueError(
                    "Post-check falhou: npcs.imagem_url nao bate com a nova mae. Nada foi gravado."
                )
        return alvo["url"]
    finally:
        await conn.close()


# =============================================================================
# UI — casca da Central + paginas
# =============================================================================

def _casca_central(aba_ativa: str = "NPCs"):
    """Barra de abas minima da Central (VISAO secao 2). Nesta onda so a aba NPCs
    existe; as outras entram nas ondas delas (rotulos visiveis, desabilitados)."""
    with ui.row().classes(
        "w-full items-center gap-3 border-b border-zinc-700 pb-3 mb-2"
    ):
        ui.label("Central de Admin — Alderyn").classes(
            "text-amber-200 text-lg font-semibold mr-4"
        )
        ui.link("NPCs", "/oficina/admin/npcs").classes(
            "text-amber-300 border-b-2 border-amber-400 pb-1"
            if aba_ativa == "NPCs" else "text-zinc-500 hover:text-amber-200"
        )
        for aba_futura in ("Árvore", "Linha do tempo", "Mapa", "Segredos", "Aprovação"):
            ui.label(aba_futura).classes("text-zinc-700 cursor-not-allowed").tooltip(
                "Onda futura"
            )


async def pagina_admin_npcs() -> None:
    """Lista de NPCs: miniatura + nome + bolinha verde/vermelha. Alfabetica,
    busca por nome. Clique -> detalhe."""
    await aguardar_conexao_websocket("Carregando Central de Admin...")

    with ui.column().classes(
        "w-full min-h-screen bg-zinc-900 text-zinc-100 p-6 gap-4 max-w-7xl mx-auto"
    ):
        _casca_central("NPCs")

        busca_input = (
            ui.input(label="Buscar NPC por nome", placeholder="ex: Elara")
            .props("outlined dense clearable color=amber-8 dark")
            .classes("w-80")
        )

        @ui.refreshable
        async def grid_npcs() -> None:
            try:
                npcs = await _listar_npcs_com_status(busca_input.value or "")
            except Exception as e:
                traceback.print_exc()
                ui.label(f"Erro ao listar NPCs: {e}").classes("text-red-400")
                return
            if not npcs:
                ui.label("Nenhum NPC encontrado.").classes("text-zinc-500")
                return
            with ui.grid(columns=4).classes("w-full gap-3"):
                for npc in npcs:
                    cor, rotulo = _dot_status(npc["tem_mae"])
                    with ui.card().tight().classes(
                        "bg-zinc-800 border border-zinc-700 hover:border-amber-400 "
                        "cursor-pointer transition-colors"
                    ).on(
                        "click",
                        lambda _, nid=npc["id"]: ui.navigate.to(
                            f"/oficina/admin/npcs/{nid}"
                        ),
                    ):
                        if npc["imagem_url"]:
                            ui.image(npc["imagem_url"]).classes(
                                "w-full h-40 object-cover"
                            )
                        else:
                            ui.element("div").classes(
                                "w-full h-40 bg-zinc-900 flex items-center "
                                "justify-center"
                            )
                        with ui.row().classes("items-center gap-2 p-3"):
                            ui.element("div").style(
                                f"width:10px;height:10px;border-radius:50%;"
                                f"background:{cor};flex:none;"
                            ).tooltip(rotulo)
                            ui.label(npc["nome"] or f"NPC #{npc['id']}").classes(
                                "text-zinc-100 truncate"
                            )

        busca_input.on("update:model-value", grid_npcs.refresh, throttle=0.5)
        await grid_npcs()


async def pagina_admin_npc_detalhe(npc_id: int) -> None:
    """Detalhe: imagem-mae grande + ancora read-only + galeria de candidatas +
    Subir imagem + Definir como mae."""
    await aguardar_conexao_websocket(f"Carregando NPC #{npc_id}...")

    with ui.column().classes(
        "w-full min-h-screen bg-zinc-900 text-zinc-100 p-6 gap-4 max-w-6xl mx-auto"
    ):
        _casca_central("NPCs")
        with ui.row().classes("items-center gap-2 text-sm"):
            ui.link("← NPCs", "/oficina/admin/npcs").classes(
                "text-zinc-500 hover:text-amber-200"
            )

        @ui.refreshable
        async def detalhe() -> None:
            try:
                dados = await _carregar_detalhe_npc(npc_id)
            except Exception as e:
                traceback.print_exc()
                ui.label(f"Erro ao carregar NPC {npc_id}: {e}").classes("text-red-400")
                return
            if dados is None:
                ui.label(f"NPC id={npc_id} não encontrado.").classes("text-zinc-400")
                return

            npc, canonica, galeria = dados["npc"], dados["canonica"], dados["galeria"]
            ui.label(npc["nome"] or f"NPC #{npc_id}").classes(
                "text-2xl text-amber-200 font-semibold"
            )

            # Polimento Onda 1: 2 colunas de verdade — ESQUERDA = mae + legenda +
            # Subir imagem; DIREITA = ancora + galeria. flex-wrap empilha em tela
            # estreita. SO apresentacao: queries e transacao intactas.
            with ui.row().classes("w-full gap-6 items-start flex-wrap"):
                # ── coluna ESQUERDA: a mae + legenda + upload ──
                with ui.column().classes("w-80 flex-none gap-2"):
                    ui.label("Imagem-mãe").classes(
                        "text-xs uppercase tracking-widest text-zinc-500"
                    )
                    if canonica:
                        ui.image(canonica["url"]).classes(
                            "w-80 rounded border border-amber-700"
                        )
                        # legenda: nome do arquivo + status (item 5; some sem imagem)
                        ui.label(
                            f"{_r2_key_da_url(canonica['url'])} · canônica"
                        ).classes("text-zinc-500 text-xs")
                        # dessincronia = sintoma de integridade: mostra, nao esconde
                        if npc["imagem_url"] != canonica["url"]:
                            ui.label(
                                "npcs.imagem_url NÃO bate com a canônica — "
                                "o jogo pode estar mostrando outra imagem."
                            ).classes("text-red-400 text-xs")
                    elif npc["imagem_url"]:
                        ui.image(npc["imagem_url"]).classes(
                            "w-80 rounded border border-zinc-700 opacity-70"
                        )
                        ui.label(
                            "Sem linha canônica em npc_imagens (só o ponteiro "
                            "npcs.imagem_url). Suba/defina uma mãe."
                        ).classes("text-amber-400 text-xs")
                    else:
                        ui.label("Sem retrato.").classes("text-zinc-500")
                    # item 2: o botao mora aqui, logo abaixo da imagem-mae
                    ui.button(
                        "Subir imagem",
                        on_click=lambda: _dialog_upload(npc_id, detalhe.refresh),
                    ).props("color=amber-8").classes("w-full")

                # ── coluna DIREITA: ancora (read-only — D4) + galeria ──
                with ui.column().classes("grow gap-1").style("min-width:320px"):
                    ui.label("Âncora visual (leitura — editor é Onda 2)").classes(
                        "text-xs uppercase tracking-widest text-zinc-500"
                    )
                    for campo, rotulo in _ROTULOS_ANCORA.items():
                        valor = npc.get(campo)
                        if valor:
                            with ui.row().classes("gap-2 items-baseline"):
                                ui.label(rotulo + ":").classes(
                                    "text-zinc-500 text-sm w-40 flex-none"
                                )
                                ui.label(str(valor)).classes("text-zinc-200 text-sm")
                    # item 3: descricoes longas RECOLHIDAS por padrao
                    if npc.get("descricao_ancora_pt") or npc.get("descricao_ancora_en"):
                        with ui.expansion("Ver descrição completa").classes(
                            "w-full text-zinc-300"
                        ).props("dense"):
                            for campo, rotulo in (
                                ("descricao_ancora_pt", "descrição (PT)"),
                                ("descricao_ancora_en", "descrição (EN)"),
                            ):
                                valor = npc.get(campo)
                                if valor:
                                    ui.label(rotulo + ":").classes(
                                        "text-zinc-500 text-sm mt-2"
                                    )
                                    ui.label(str(valor)).classes(
                                        "text-zinc-300 text-sm italic"
                                    )

                    ui.label("Galeria (não-canônicas)").classes(
                        "text-xs uppercase tracking-widest text-zinc-500 mt-4"
                    )
                    if not galeria:
                        ui.label(
                            "Nenhuma candidata. Suba uma imagem pra começar."
                        ).classes("text-zinc-500")
                    with ui.grid(columns=2).classes("w-full gap-3"):
                        for img in galeria:
                            with ui.card().tight().classes(
                                "bg-zinc-800 border border-zinc-700"
                            ):
                                ui.image(img["url"]).classes("w-full h-40 object-cover")
                                with ui.column().classes("p-2 gap-1"):
                                    ui.label(
                                        f"{img['status']} — {img['rotulo_narrativo'] or img['modelo_ia'] or ''}"
                                    ).classes("text-zinc-400 text-xs truncate")
                                    ui.button(
                                        "Definir como mãe",
                                        on_click=lambda _, iid=img["id"]: _confirmar_mae(
                                            npc_id, iid, detalhe.refresh
                                        ),
                                    ).props("dense color=amber-8 outline").classes("w-full")

        await detalhe()


def _dialog_upload(npc_id: int, refresh) -> None:
    """Dialog 'Subir imagem': valida -> R2 (alderyn-npcs) -> INSERT candidata ->
    refresh. Espelha o padrao de upload do Atelie. r2_storage importado LAZY."""
    with ui.dialog() as dialog, ui.card().classes(
        "bg-zinc-800 text-zinc-100 w-96 gap-2"
    ):
        ui.label("Subir imagem (vira candidata)").classes(
            "text-amber-200 text-lg font-semibold"
        )
        ui.label(
            f"JPG, PNG ou WEBP, até {_MAX_UPLOAD_MB} MB. Nada vira mãe sem o "
            "'Definir como mãe'."
        ).classes("text-zinc-400 text-sm")
        rotulo_input = (
            ui.input(label="Rótulo (opcional)", placeholder="ex: retrato definitivo")
            .props("outlined dense color=amber-8 dark")
            .classes("w-full")
        )
        status_label = ui.label("").classes("text-sm")

        async def _on_upload(e):
            file = e.file
            file_bytes = await file.read()
            content_type = (
                getattr(file, "content_type", None)
                or getattr(file, "mime_type", None)
                or getattr(file, "type", None)
            )
            erro = _validar_upload(content_type, len(file_bytes))
            if erro:
                status_label.text = erro
                status_label.classes(replace="text-sm text-red-400")
                return
            status_label.text = f"Enviando {len(file_bytes) / 1024:.0f} KB..."
            status_label.classes(replace="text-sm text-amber-300")
            try:
                from r2_storage import upload_imagem_npc  # LAZY: credencial so aqui
                url = await upload_imagem_npc(npc_id, file_bytes, content_type)
                imagem_id = await _inserir_candidata_upload(
                    npc_id, url, (rotulo_input.value or "").strip() or None
                )
                ui.notify(
                    f"Candidata #{imagem_id} adicionada.",
                    type="positive", position="top",
                )
                dialog.close()
                refresh()
            except Exception as ex:
                traceback.print_exc()
                status_label.text = f"Erro: {ex}"
                status_label.classes(replace="text-sm text-red-400")

        ui.upload(
            label="Selecionar arquivo",
            on_upload=_on_upload,
            max_file_size=_MAX_UPLOAD_MB * 1024 * 1024,
            auto_upload=True,
        ).props(
            "accept='image/jpeg,image/png,image/webp' color=amber-8 flat dense"
        ).classes("w-full")
        with ui.row().classes("w-full justify-end"):
            ui.button("Fechar", on_click=dialog.close).props("flat color=zinc-5")
    dialog.open()


def _confirmar_mae(npc_id: int, imagem_id: int, refresh) -> None:
    """Confirmacao explicita antes da transacao (trocar a mae afeta o jogo no
    turno seguinte)."""
    with ui.dialog() as dialog, ui.card().classes(
        "bg-zinc-800 text-zinc-100 gap-2"
    ):
        ui.label("Definir esta imagem como a mãe?").classes("text-amber-200")
        ui.label(
            "A mãe atual vira 'arquivada' e o jogo passa a mostrar esta no "
            "próximo turno."
        ).classes("text-zinc-400 text-sm")

        async def _executar():
            try:
                url = await definir_como_mae(npc_id, imagem_id)
                ui.notify(
                    f"Nova imagem-mãe definida ({_r2_key_da_url(url)}).",
                    type="positive", position="top",
                )
                dialog.close()
                refresh()
            except ValueError as ex:
                ui.notify(str(ex), type="negative", position="top", timeout=8000)
            except Exception as ex:
                traceback.print_exc()
                ui.notify(
                    f"Erro na transação (nada foi gravado): {ex}",
                    type="negative", position="top", timeout=8000,
                )

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancelar", on_click=dialog.close).props("flat color=zinc-5")
            ui.button("Definir como mãe", on_click=_executar).props("color=amber-8")
    dialog.open()
