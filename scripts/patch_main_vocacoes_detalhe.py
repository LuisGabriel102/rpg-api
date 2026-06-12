"""
patch_main_vocacoes_detalhe.py - Etapa 3 de vocacoes.

Mudancas:
  1. Import: RefCaminhos, RefHabilidadesClasseNivel
  2. Tabela /oficina/vocacoes ganha on-click pra navegar pro detalhe
  3. Rota /oficina/vocacoes/{id} com info completa
"""
from pathlib import Path
import sys

MAIN = Path("main.py")
SENTINELA = "def pagina_vocacao_detalhe"

IMPORT_OLD = "from models import Npcs, RefEstrelasNascimento, RefHabilidadesEstrela, RefVocacoes"
IMPORT_NEW = "from models import Npcs, RefEstrelasNascimento, RefHabilidadesEstrela, RefVocacoes, RefCaminhos, RefHabilidadesClasseNivel"

# --- Adicionar row-click handler na tabela de vocacoes ---
CLICK_OLD = '''        table.on("request", on_request)

        with ui.row().classes("w-full justify-center mt-auto pt-6"):
            ui.label(
                "Módulo 6.2 OK. Pagina de detalhes chega na Etapa 3."
            ).classes("text-xs text-zinc-600 italic")'''

CLICK_NEW = '''        table.on("request", on_request)

        def ir_pro_detalhe(e: GenericEventArguments) -> None:
            row = e.args[1]  # segundo arg eh o row dict
            if row and "id" in row:
                ui.navigate.to(f"/oficina/vocacoes/{row['id']}")

        table.on("rowClick", ir_pro_detalhe)

        with ui.row().classes("w-full justify-center mt-auto pt-6"):
            ui.label(
                "Módulo 6.3 OK. Clique numa linha pra ver detalhes."
            ).classes("text-xs text-zinc-600 italic")'''

# --- Ancora de insercao ---
ANCORA = "# MOUNT NICEGUI NO APP FASTAPI"

# --- Bloco principal ---
NOVO_BLOCO = '''# ====================================================================
# === VOCACOES DETALHE - ROTAS (Módulo 6.3) ===
# ====================================================================


async def _buscar_vocacao_com_tudo(voc_id: int) -> dict | None:
    """Busca uma vocacao, seus caminhos e habilidades. Retorna dict ou None."""
    async with get_session() as session:
        voc = (await session.exec(
            select(RefVocacoes).where(RefVocacoes.id == voc_id)
        )).first()
        if not voc:
            return None

        caminhos = (await session.exec(
            select(RefCaminhos)
            .where(RefCaminhos.vocacao_id == voc_id)
            .order_by(RefCaminhos.id)
        )).all()

        habs = (await session.exec(
            select(RefHabilidadesClasseNivel)
            .where(RefHabilidadesClasseNivel.vocacao_id == voc_id)
            .order_by(
                RefHabilidadesClasseNivel.nivel,
                RefHabilidadesClasseNivel.nome,
            )
        )).all()

    return {
        "id": voc.id,
        "nome": voc.nome_ptbr,
        "nome_en": voc.nome,
        "pilar": voc.pilar,
        "tipo": voc.tipo,
        "atributos": voc.atributos_primarios or [],
        "origem": voc.vocacoes_origem or [],
        "descricao": voc.descricao,
        "diferencial": voc.diferencial_mecanico,
        "disponivel": voc.disponivel_escolha,
        "caminhos": [
            {
                "id": c.id,
                "nome": c.nome_ptbr,
                "descricao": c.descricao,
                "nivel_desbloqueio": c.nivel_desbloqueio,
            }
            for c in caminhos
        ],
        "habilidades": [
            {
                "id": h.id,
                "nivel": h.nivel,
                "nome": h.nome_ptbr,
                "nome_en": h.nome,
                "tipo": h.tipo,
                "descricao": h.descricao,
                "gera_maestria": h.gera_maestria,
                "requer_caminho": h.requer_caminho,
            }
            for h in habs
        ],
    }


@ui.page("/oficina/vocacoes/{voc_id}")
async def pagina_vocacao_detalhe(voc_id: int):
    """Pagina de detalhe de uma vocacao."""
    data = await _buscar_vocacao_com_tudo(voc_id)

    if not data:
        with ui.column().classes(
            "w-full min-h-screen bg-zinc-900 text-zinc-100 p-8 items-center "
            "justify-center gap-4"
        ):
            ui.label(f"Vocação id={voc_id} não encontrada.").classes(
                "text-2xl text-zinc-400"
            )
            ui.button(
                "Voltar",
                on_click=lambda: ui.navigate.to("/oficina/vocacoes"),
            ).props("color=amber-8")
        return

    pilares_validos = ("I", "II", "III", "IV", "V", "Fundida")
    is_anomalia = data["pilar"] not in pilares_validos

    with ui.column().classes(
        "w-full min-h-screen bg-zinc-900 text-zinc-100 p-8 gap-4"
    ):
        # === Header ===
        with ui.row().classes("w-full items-start justify-between"):
            with ui.row().classes("items-center gap-3"):
                ui.button(
                    icon="arrow_back",
                    on_click=lambda: ui.navigate.to("/oficina/vocacoes"),
                ).props("flat round dense color=amber-2")

                with ui.column().classes("gap-0"):
                    with ui.row().classes("items-baseline gap-3"):
                        ui.label(data["nome"]).classes(
                            "text-4xl font-bold text-amber-200 tracking-wide"
                        )
                        if data["nome"] != data["nome_en"]:
                            ui.label(f"({data['nome_en']})").classes(
                                "text-base text-zinc-500 italic"
                            )
                    with ui.row().classes("items-center gap-3 mt-1"):
                        pilar_txt = f"⚠ Pilar: {data['pilar']}" if is_anomalia else f"Pilar {data['pilar']}"
                        pilar_cls = "text-red-400" if is_anomalia else "text-amber-300"
                        ui.label(pilar_txt).classes(f"text-sm {pilar_cls} font-mono")
                        ui.label(f"• {data['tipo']}").classes("text-sm text-zinc-500")
                        if data["atributos"]:
                            ui.label(f"• {' / '.join(data['atributos'])}").classes(
                                "text-sm font-mono text-zinc-400"
                            )
                        if data["disponivel"] is False:
                            ui.label("• 🚫 BLOQUEADA").classes(
                                "text-sm text-red-400 font-bold"
                            )

        ui.separator().classes("bg-zinc-700")

        # === Origem (se fundida) ===
        if data["origem"]:
            with ui.card().classes(
                "w-full bg-zinc-800 border border-zinc-700 p-4"
            ).props("flat"):
                ui.label("Derivada de").classes(
                    "text-xs uppercase tracking-wider text-zinc-500 mb-1"
                )
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    for i, nome_pai in enumerate(data["origem"]):
                        if i > 0:
                            ui.icon("add", size="1rem").classes("text-zinc-500")
                        ui.label(nome_pai).classes(
                            "text-base text-amber-200 font-semibold"
                        )

        # === Descricao ===
        with ui.card().classes(
            "w-full bg-zinc-800 border border-zinc-700 p-4"
        ).props("flat"):
            ui.label("Descrição").classes(
                "text-xs uppercase tracking-wider text-zinc-500 mb-2"
            )
            ui.label(data["descricao"]).classes(
                "text-sm text-zinc-300 whitespace-pre-line leading-relaxed"
            )

        # === Diferencial mecanico ===
        if data["diferencial"]:
            with ui.card().classes(
                "w-full bg-zinc-800 border border-amber-800 p-4"
            ).props("flat"):
                ui.label("Diferencial mecânico").classes(
                    "text-xs uppercase tracking-wider text-amber-400 mb-2"
                )
                ui.label(data["diferencial"]).classes(
                    "text-sm text-zinc-200 italic whitespace-pre-line leading-relaxed"
                )

        # === Caminhos (subclasses) ===
        n_caminhos = len(data["caminhos"])
        with ui.expansion(
            f"Caminhos / Subclasses ({n_caminhos})",
            icon="fork_right",
            value=n_caminhos > 0,
        ).classes("w-full bg-zinc-800 rounded").props("dense"):
            with ui.column().classes("w-full gap-3 p-2"):
                if n_caminhos == 0:
                    ui.label(
                        "Esta vocação ainda não tem caminhos definidos."
                    ).classes("text-zinc-500 italic")
                else:
                    for c in data["caminhos"]:
                        with ui.card().classes(
                            "w-full bg-zinc-900 border border-zinc-700 p-3"
                        ).props("flat"):
                            with ui.row().classes("items-center gap-2"):
                                ui.label(c["nome"]).classes(
                                    "text-base font-semibold text-amber-200"
                                )
                                if c["nivel_desbloqueio"]:
                                    ui.label(
                                        f"nível {c['nivel_desbloqueio']}"
                                    ).classes(
                                        "text-xs text-zinc-500 font-mono"
                                    )
                            ui.label(c["descricao"]).classes(
                                "text-sm text-zinc-400 mt-1 whitespace-pre-line"
                            )

        # === Habilidades por nivel ===
        n_habs = len(data["habilidades"])
        with ui.expansion(
            f"Habilidades por nível ({n_habs})",
            icon="auto_awesome_motion",
            value=n_habs > 0 and n_habs <= 10,
        ).classes("w-full bg-zinc-800 rounded").props("dense"):
            with ui.column().classes("w-full gap-3 p-2"):
                if n_habs == 0:
                    ui.label(
                        "Esta vocação ainda não tem habilidades mapeadas."
                    ).classes("text-zinc-500 italic")
                else:
                    nivel_atual = None
                    for h in data["habilidades"]:
                        if h["nivel"] != nivel_atual:
                            nivel_atual = h["nivel"]
                            ui.label(f"Nível {nivel_atual}").classes(
                                "text-sm uppercase tracking-wider "
                                "text-amber-400 mt-3 mb-1"
                            )
                        with ui.card().classes(
                            "w-full bg-zinc-900 border border-zinc-700 p-3"
                        ).props("flat"):
                            with ui.row().classes("items-center gap-2 flex-wrap"):
                                ui.label(h["nome"]).classes(
                                    "text-base font-semibold text-zinc-200"
                                )
                                ui.badge(h["tipo"], color="zinc-7").props("rounded")
                                if h["gera_maestria"]:
                                    ui.icon("military_tech", size="1rem").classes(
                                        "text-amber-400"
                                    ).tooltip("Gera maestria")
                                if h["requer_caminho"]:
                                    ui.icon("lock", size="1rem").classes(
                                        "text-zinc-500"
                                    ).tooltip("Requer caminho escolhido")
                            ui.label(h["descricao"]).classes(
                                "text-sm text-zinc-400 mt-1 whitespace-pre-line"
                            )

        with ui.row().classes("w-full justify-center mt-auto pt-6"):
            ui.label(
                f"Módulo 6.3 OK. {n_caminhos} caminhos, {n_habs} habilidades."
            ).classes("text-xs text-zinc-600 italic")


'''


def main() -> int:
    c = MAIN.read_text(encoding="utf-8")
    antes = len(c)

    if SENTINELA in c:
        print(f"  [IDEMPOTENTE] Ja aplicado. {antes} bytes.")
        return 0

    # 1. Import
    if IMPORT_OLD not in c:
        print("[ERRO 1] Import antigo nao encontrado.")
        return 1
    c = c.replace(IMPORT_OLD, IMPORT_NEW, 1)
    print("  [1] Import atualizado: +RefCaminhos +RefHabilidadesClasseNivel")

    # 2. Click handler na tabela
    if CLICK_OLD not in c:
        print("[ERRO 2] Bloco do rodape de vocacoes nao encontrado.")
        return 2
    c = c.replace(CLICK_OLD, CLICK_NEW, 1)
    print("  [2] rowClick handler adicionado na tabela")

    # 3. Inserir bloco antes do MOUNT
    if ANCORA not in c:
        print(f"[ERRO 3] Ancora nao encontrada: {ANCORA!r}")
        return 3

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
    print(f"  [3] Bloco principal inserido ({len(NOVO_BLOCO)} chars)")
    print()
    print("=" * 72)
    print(f"  [OK] Etapa 3 de vocacoes aplicada.")
    print(f"  Antes: {antes} | Depois: {depois} (+{depois - antes})")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())