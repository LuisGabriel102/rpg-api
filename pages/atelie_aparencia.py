"""
Sub-aba "Aparência" do Ateliê — Catedral do Alderyn (Módulo 4.6.4).

Form completo de edição da aparência canônica de um NPC.
Cobre as 16 colunas adicionadas na Migration 4.6:

  Visuais físicos (5):  rosto, olhos, cabelo, corpo, pele
  Visuais contextuais (3): wardrobe_padrao, iluminacao_tematica, postura_canonica
                          (cada um com flag _herdado de facção)
  Narrativos (3):       voz_descritiva, cheiro_caracteristico, tiques_e_maneirismos (JSONB)
  Âncoras (2):          descricao_ancora_pt, descricao_ancora_en

PADRÕES DE UI:
  - Inputs ui.input/textarea com on_change=...salvar_campo (debounced)
  - Botão "Salvar tudo" no rodapé pra salvar batch
  - Cards visuais agrupando (Físicos | Contextuais | Narrativos | Âncoras)
  - Indicador "herdado" com botão "tornar próprio" quando flag herdado=True
"""

from __future__ import annotations

from typing import Awaitable, Callable

from nicegui import ui

from pages.atelie_queries import (
    salvar_aparencia_npc,
    buscar_template_faccoes,
)


# =============================================================================
# Estado em memória — sub-aba mantém dict mutável dos campos editados
# =============================================================================

class EstadoAparencia:
    """Container do estado em memória do form de aparência.

    Atributos editáveis pelos inputs. Salvar persiste tudo no banco.
    """

    def __init__(self, dados_npc: dict):
        # Visuais físicos
        self.rosto = dados_npc.get("rosto") or ""
        self.olhos = dados_npc.get("olhos") or ""
        self.cabelo = dados_npc.get("cabelo") or ""
        self.corpo = dados_npc.get("corpo") or ""
        self.pele = dados_npc.get("pele") or ""

        # Visuais contextuais
        self.wardrobe_padrao = dados_npc.get("wardrobe_padrao") or ""
        self.iluminacao_tematica = dados_npc.get("iluminacao_tematica") or ""
        self.postura_canonica = dados_npc.get("postura_canonica") or ""
        self.wardrobe_padrao_herdado = bool(dados_npc.get("wardrobe_padrao_herdado"))
        self.iluminacao_tematica_herdada = bool(dados_npc.get("iluminacao_tematica_herdada"))
        self.postura_canonica_herdada = bool(dados_npc.get("postura_canonica_herdada"))

        # Narrativos
        self.voz_descritiva = dados_npc.get("voz_descritiva") or ""
        self.cheiro_caracteristico = dados_npc.get("cheiro_caracteristico") or ""
        # tiques_e_maneirismos vem como list[dict]
        self.tiques_e_maneirismos: list[dict] = list(
            dados_npc.get("tiques_e_maneirismos") or []
        )

        # Âncoras
        self.descricao_ancora_pt = dados_npc.get("descricao_ancora_pt") or ""
        self.descricao_ancora_en = dados_npc.get("descricao_ancora_en") or ""

    def to_dict(self) -> dict:
        """Serializa todos campos pra dict (pronto pro UPDATE)."""
        return {
            "rosto": self.rosto.strip() or None,
            "olhos": self.olhos.strip() or None,
            "cabelo": self.cabelo.strip() or None,
            "corpo": self.corpo.strip() or None,
            "pele": self.pele.strip() or None,
            "wardrobe_padrao": self.wardrobe_padrao.strip() or None,
            "iluminacao_tematica": self.iluminacao_tematica.strip() or None,
            "postura_canonica": self.postura_canonica.strip() or None,
            "wardrobe_padrao_herdado": self.wardrobe_padrao_herdado,
            "iluminacao_tematica_herdada": self.iluminacao_tematica_herdada,
            "postura_canonica_herdada": self.postura_canonica_herdada,
            "voz_descritiva": self.voz_descritiva.strip() or None,
            "cheiro_caracteristico": self.cheiro_caracteristico.strip() or None,
            "tiques_e_maneirismos": self.tiques_e_maneirismos,
            "descricao_ancora_pt": self.descricao_ancora_pt.strip() or None,
            "descricao_ancora_en": self.descricao_ancora_en.strip() or None,
        }


# =============================================================================
# Helpers de UI
# =============================================================================

def _label_secao(texto: str, subtitulo: str = "") -> None:
    """Header de seção dentro do form."""
    with ui.row().classes("w-full items-baseline gap-3 mt-4"):
        ui.label(texto).classes(
            "text-amber-200 text-lg font-semibold uppercase tracking-wider"
        )
        if subtitulo:
            ui.label(subtitulo).classes("text-zinc-500 text-xs italic")
    ui.separator().classes("bg-zinc-700 mb-2")


def _field_textarea(
    rotulo: str,
    estado: EstadoAparencia,
    attr: str,
    placeholder: str = "",
    rows: int = 2,
    classes: str = "",
) -> ui.textarea:
    """Cria textarea bound a um atributo do estado.

    Usa on_change direto no construtor (NiceGUI 3.10 padrão correto) em vez de
    .on('update:model-value', ...) que não funciona consistentemente em widgets Quasar.
    """
    valor_inicial = getattr(estado, attr)

    def _on_change(e):
        setattr(estado, attr, e.value or "")

    elem = (
        ui.textarea(
            label=rotulo, placeholder=placeholder,
            value=valor_inicial, on_change=_on_change,
        )
        .props(f"outlined dense color=amber-8 dark rows={rows}")
        .classes(f"w-full {classes}")
    )
    return elem


def _field_input(
    rotulo: str,
    estado: EstadoAparencia,
    attr: str,
    placeholder: str = "",
) -> ui.input:
    """Cria input bound a um atributo do estado."""
    valor_inicial = getattr(estado, attr)

    def _on_change(e):
        setattr(estado, attr, e.value or "")

    elem = (
        ui.input(
            label=rotulo, placeholder=placeholder,
            value=valor_inicial, on_change=_on_change,
        )
        .props("outlined dense color=amber-8 dark")
        .classes("w-full")
    )
    return elem


# =============================================================================
# RENDER PRINCIPAL DA SUB-ABA
# =============================================================================

async def render_aba_aparencia(
    npc_id: int,
    dados_npc: dict,
    on_salvo: Callable[[], Awaitable[None]],
) -> None:
    """Renderiza a sub-aba Aparência.

    Args:
        npc_id: ID do NPC sendo editado.
        dados_npc: dict do NPC carregado (carregar_npc_completo).
        on_salvo: callback chamado após salvar com sucesso (pra refresh).
    """
    estado = EstadoAparencia(dados_npc)

    # Buscar templates de facção (pra mostrar opção "herdar")
    facoes_nomes: list[str] = list(dados_npc.get("facoes") or [])
    templates_faccao: list[dict] = []
    if facoes_nomes:
        try:
            templates_faccao = await buscar_template_faccoes(facoes_nomes)
        except Exception:
            templates_faccao = []

    with ui.column().classes("w-full gap-2"):

        # ─── Aviso se NPC não tem âncora (pré-requisito pra gerar imagem) ───
        if not (estado.descricao_ancora_pt or estado.descricao_ancora_en):
            with ui.card().classes("w-full bg-red-900/30 border border-red-700 p-3"):
                ui.label("⚠ Sem âncora de identidade").classes(
                    "text-red-300 font-semibold"
                )
                ui.label(
                    "Preencha 'Âncora EN' (ou ao menos 'Âncora PT') pra "
                    "conseguir gerar imagens. Sem âncora, o pipeline rejeita."
                ).classes("text-red-200 text-sm")

        # =====================================================================
        # SEÇÃO 1: ÂNCORAS DE IDENTIDADE (mais importante — primeiro)
        # =====================================================================
        _label_secao(
            "Âncoras de identidade",
            "Bloco IMUTÁVEL que define quem o NPC é. EN é o que vai pra IA.",
        )

        _field_textarea(
            "Âncora EN (texto enviado à IA — preferencial)",
            estado, "descricao_ancora_en",
            placeholder="64-year-old human man, face deeply lined by decades of "
                        "kitchen work, calloused hands, tired but attentive brown "
                        "eyes... DOES NOT HAVE: tattoos, rings.",
            rows=4,
        )

        _field_textarea(
            "Âncora PT (versão canônica em português)",
            estado, "descricao_ancora_pt",
            placeholder="Homem humano de 64 anos, rosto vincado por décadas de "
                        "cozinha, mãos calejadas...",
            rows=4,
        )

        # =====================================================================
        # SEÇÃO 2: VISUAIS FÍSICOS (5 campos)
        # =====================================================================
        _label_secao("Físicos", "Detalhes do corpo (compõem a âncora)")

        with ui.grid(columns=2).classes("w-full gap-2"):
            _field_textarea("Rosto", estado, "rosto",
                            placeholder="rosto vincado, mandíbula firme...")
            _field_textarea("Olhos", estado, "olhos",
                            placeholder="castanhos cansados mas atentos...")
            _field_textarea("Cabelo", estado, "cabelo",
                            placeholder="preto com fios brancos, rareando no topo...")
            _field_textarea("Corpo", estado, "corpo",
                            placeholder="magro, postura curvada de cozinheiro...")
            _field_textarea("Pele", estado, "pele",
                            placeholder="oliva desgastada, cicatriz no antebraço...")

        # =====================================================================
        # SEÇÃO 3: VISUAIS CONTEXTUAIS (3 campos + flags herdado)
        # =====================================================================
        _label_secao(
            "Contextuais",
            "Roupa, iluminação e postura — podem herdar de facção"
            + (f" ({', '.join(facoes_nomes)})" if facoes_nomes else "")
        )

        # Wardrobe + flag
        _render_campo_com_herdado(
            estado, "wardrobe_padrao", "wardrobe_padrao_herdado",
            "Vestimenta padrão",
            "avental de couro envelhecido manchado de gordura...",
            templates_faccao, "wardrobe_padrao",
        )

        # Iluminação + flag
        _render_campo_com_herdado(
            estado, "iluminacao_tematica", "iluminacao_tematica_herdada",
            "Iluminação temática",
            "luz amber lateral de fogão a lenha, brasa fora de quadro...",
            templates_faccao, "iluminacao_tematica",
        )

        # Postura + flag
        _render_campo_com_herdado(
            estado, "postura_canonica", "postura_canonica_herdada",
            "Postura canônica",
            "ligeiramente curvado, mãos sempre fazendo algo...",
            templates_faccao, "postura_canonica",
        )

        # =====================================================================
        # SEÇÃO 4: NARRATIVOS (3 campos — não viram prompt mas são canônicos)
        # =====================================================================
        _label_secao(
            "Narrativos",
            "Não vão pro prompt visual — usados pelo narrador IA durante o jogo",
        )

        _field_textarea(
            "Voz descritiva",
            estado, "voz_descritiva",
            placeholder="rouca, baixa, monossilábica em público; calorosa quando confia",
            rows=2,
        )

        _field_textarea(
            "Cheiro característico",
            estado, "cheiro_caracteristico",
            placeholder="fumaça de lenha, gordura quente, ervas frescas e couro velho",
            rows=2,
        )

        # Tiques são lista de {tique, gatilho_emocao} — UI especial
        _render_tiques_editor(estado)

        # =====================================================================
        # RODAPÉ: Botão Salvar
        # =====================================================================
        ui.separator().classes("bg-zinc-700 mt-6")

        with ui.row().classes("w-full justify-end items-center gap-3 mt-2"):
            status_label = ui.label("").classes("text-sm text-zinc-400")

            async def _salvar():
                try:
                    btn_salvar.props("loading disabled")
                    status_label.text = "Salvando..."
                    status_label.classes(replace="text-sm text-amber-300")
                    await salvar_aparencia_npc(npc_id, estado.to_dict())
                    status_label.text = "✓ Salvo"
                    status_label.classes(replace="text-sm text-green-400")
                    ui.notify(
                        "Aparência salva no banco",
                        type="positive", position="top",
                    )
                    await on_salvo()
                except Exception as e:
                    status_label.text = f"✗ Erro: {e}"
                    status_label.classes(replace="text-sm text-red-400")
                    ui.notify(
                        f"Falha ao salvar: {e}",
                        type="negative", position="top",
                    )
                finally:
                    btn_salvar.props(remove="loading disabled")

            btn_salvar = ui.button("Salvar aparência", on_click=_salvar).props(
                "color=amber-8 unelevated"
            ).classes("min-w-[160px]")


# =============================================================================
# Helpers de campo com flag "herdado"
# =============================================================================

def _render_campo_com_herdado(
    estado: EstadoAparencia,
    attr_texto: str,
    attr_flag: str,
    rotulo: str,
    placeholder: str,
    templates_faccao: list[dict],
    chave_template: str,
) -> None:
    """Renderiza campo de texto + checkbox 'herdado' + botão 'aplicar template'."""
    with ui.card().classes("w-full bg-zinc-800/40 border border-zinc-700 p-3 gap-2"):
        elem_textarea = _field_textarea(
            rotulo, estado, attr_texto,
            placeholder=placeholder, rows=2, classes="",
        )

        with ui.row().classes("w-full items-center gap-3"):
            def _on_check(e):
                setattr(estado, attr_flag, bool(e.value))

            cb = (
                ui.checkbox(
                    "Herdado de facção",
                    value=getattr(estado, attr_flag),
                    on_change=_on_check,
                )
                .props("color=amber-8 dark dense")
                .classes("text-zinc-300 text-sm")
            )

            # Botões "Aplicar template de [Casa X]"
            for tmpl in templates_faccao:
                valor_template = tmpl.get(chave_template) or ""
                if not valor_template:
                    continue
                nome_faccao = tmpl["faccao_nome"]

                def _aplicar(
                    valor=valor_template,
                    nome=nome_faccao,
                    elem=elem_textarea,
                    attr=attr_texto,
                    flag_attr=attr_flag,
                    cb_elem=cb,
                ):
                    setattr(estado, attr, valor)
                    setattr(estado, flag_attr, True)
                    elem.value = valor
                    cb_elem.value = True
                    ui.notify(
                        f"Aplicado template de {nome}",
                        type="info", position="bottom-right",
                    )

                ui.button(f"⮬ {nome_faccao}", on_click=_aplicar).props(
                    "flat dense color=amber-7"
                ).classes("text-xs")


def _render_tiques_editor(estado: EstadoAparencia) -> None:
    """Editor de tiques_e_maneirismos (list[{tique, gatilho_emocao}])."""
    with ui.card().classes("w-full bg-zinc-800/40 border border-zinc-700 p-3 gap-2"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Tiques e maneirismos").classes("text-zinc-200 font-medium")

            def _add():
                estado.tiques_e_maneirismos.append({"tique": "", "gatilho_emocao": ""})
                container.refresh()

            ui.button("+ Adicionar tique", on_click=_add).props(
                "flat dense color=amber-7"
            )

        @ui.refreshable
        def container():
            if not estado.tiques_e_maneirismos:
                ui.label("(nenhum tique definido)").classes(
                    "text-zinc-500 italic text-sm"
                )
                return

            for idx, tique in enumerate(list(estado.tiques_e_maneirismos)):
                with ui.row().classes("w-full items-center gap-2"):
                    def _upd_t(e, i=idx, key="tique"):
                        if i < len(estado.tiques_e_maneirismos):
                            estado.tiques_e_maneirismos[i][key] = e.value or ""

                    def _upd_g(e, i=idx):
                        if i < len(estado.tiques_e_maneirismos):
                            estado.tiques_e_maneirismos[i]["gatilho_emocao"] = e.value or ""

                    inp_tique = (
                        ui.input(
                            label=f"Tique #{idx + 1}",
                            value=tique.get("tique", ""),
                            placeholder="ex: limpar mãos no avental",
                            on_change=_upd_t,
                        )
                        .props("outlined dense color=amber-8 dark")
                        .classes("flex-1")
                    )
                    inp_gatilho = (
                        ui.input(
                            label="Gatilho",
                            value=tique.get("gatilho_emocao", ""),
                            placeholder="ex: nervosismo",
                            on_change=_upd_g,
                        )
                        .props("outlined dense color=amber-8 dark")
                        .classes("w-40")
                    )

                    def _del(i=idx):
                        if i < len(estado.tiques_e_maneirismos):
                            estado.tiques_e_maneirismos.pop(i)
                            container.refresh()

                    ui.button(icon="delete", on_click=_del).props(
                        "flat dense color=red-7 round"
                    )

        container()
