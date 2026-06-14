"""
Aplicacao principal da Oficina do Mestre.

Combina FastAPI (API JSON em /api/*) com NiceGUI (UI web em /oficina*) num
unico processo uvicorn. O middleware BasicAuthMiddleware protege tudo exceto
a whitelist (/, /healthz, /_nicegui*).

Paginas NiceGUI:
    /oficina               - home da Oficina (cards de secoes)
    /oficina/npcs          - lista rica de NPCs com filtros (4.2)
    /oficina/npcs/{id}     - detalhe rico de NPC com 13 secoes (4.2)
    /oficina/estrelas      - grid das 12 estrelas do Veu (5.2)
    /oficina/estrelas/{id} - detalhe de estrela com habilidades (5.4)
    /oficina/vocacoes      - lista paginada de vocacoes (6.2)
    /oficina/vocacoes/{id} - detalhe de vocacao com caminhos (6.3)
    /oficina/bestiario     - lista de criaturas canonizadas (7.1)
    /oficina/bestiario/{id}- detalhe de criatura dark fantasy (7.1)

Rodar:
    uvicorn main:app --reload

NOTA TECNICA (Two-Phase Loading):
TODAS as @ui.page async chamam aguardar_conexao_websocket() como primeira
acao. Isso evita o response_timeout de 3s do NiceGUI cancelar o handler
quando queries demoram, causando loop infinito de WebSocket. Ver ui_helpers.py.
"""

import asyncio
import warnings

# Silencia warnings cosmeticos do SQLModel
warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

from fastapi import APIRouter, FastAPI, HTTPException, Query, status
from nicegui import ui
from nicegui.events import GenericEventArguments
from pydantic import BaseModel, Field as PydanticField, field_validator
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

import config
from auth import BasicAuthMiddleware
from db import engine, get_session
from models import Npcs, RefEstrelasNascimento, RefHabilidadesEstrela, RefVocacoes, RefCaminhos, RefHabilidadesClasseNivel, RefPilares
from ui_helpers import aguardar_conexao_websocket, barra_nav
from oficina_npcs_42 import pagina_lista_npcs_rica, pagina_npc_detalhe
from pages.atelie import pagina_atelie
from pages.bestiario import pagina_lista_bestiario, pagina_criatura_detalhe, contar_criaturas_canonizadas


# ====================================================================
# ROUTER da Oficina
# Montado no app do monolito pelo server.py (que tambem chama ui.run_with).
# Antes a Oficina criava o proprio FastAPI + BasicAuthMiddleware + lifespan;
# no monolito o app base e o do backend, e o auth/cleanup ficam no server.py.
# ====================================================================
oficina_router = APIRouter()


# ====================================================================
# ENDPOINTS PUBLICOS
# ====================================================================

@oficina_router.get("/healthz", tags=["publico"])
async def healthcheck() -> dict:
    return {"status": "ok"}


# ====================================================================
# PYDANTIC INPUT MODELS
# ====================================================================

_SEXO_VALIDOS = {"masculino", "feminino", "nao_binario", "desconhecido"}
_STATUS_VALIDOS = {"vivo", "morto", "desaparecido", "exilado"}


class NpcCreate(BaseModel):
    """Payload pra criacao de NPC via POST /api/npcs."""

    # Required
    nome: str = PydanticField(min_length=1, max_length=200)
    nome_curto: str = PydanticField(min_length=1, max_length=100)

    # Required-com-default no banco
    raca: str = "humano"
    status: str = "vivo"
    camada: int = PydanticField(2, ge=1, le=3)
    personality_summary: str = ""

    # Identidade opcional
    epiteto: Optional[str] = None
    sexo: Optional[str] = None
    idade_aparente: Optional[int] = PydanticField(None, gt=0)
    idade_real: Optional[int] = None

    # Localizacao e oficio
    localizacao_atual: Optional[str] = None
    localizacao_base: Optional[str] = None
    profissao: Optional[str] = None
    facoes: Optional[list[str]] = None

    # Big Five
    abertura: Optional[int] = PydanticField(None, ge=0, le=100)
    conscienciosidade: Optional[int] = PydanticField(None, ge=0, le=100)
    extroversao: Optional[int] = PydanticField(None, ge=0, le=100)
    amabilidade: Optional[int] = PydanticField(None, ge=0, le=100)
    neuroticismo: Optional[int] = PydanticField(None, ge=0, le=100)

    # Nucleo psicologico
    valores: Optional[list[str]] = None
    medo_principal: Optional[str] = None
    medos_secundarios: Optional[list[str]] = None
    desejo_oculto: Optional[str] = None
    linha_que_nao_cruza: Optional[str] = None
    maior_arrependimento: Optional[str] = None
    estilo_de_fala: Optional[str] = None

    # Prompts narrativos
    prompt_identidade: Optional[str] = None
    prompt_dialogo: Optional[str] = None
    prompt_contexto_protagonista: Optional[str] = None
    tensao_interna: Optional[str] = None

    # Backstory
    backstory_completa: Optional[str] = None
    backstory_resumida: Optional[str] = None
    evento_formativo: Optional[str] = None

    # Singularidade
    singularidade: Optional[int] = PydanticField(None, ge=1, le=10)
    o_que_so_ele_pode_fazer: Optional[str] = None
    momento_de_singularidade: Optional[str] = None

    # Notas do mestre
    notas_do_gpt: Optional[str] = None

    @field_validator("sexo")
    @classmethod
    def _validar_sexo(cls, v):
        if v in (None, ""):
            return None
        if v not in _SEXO_VALIDOS:
            raise ValueError(f"sexo deve ser um de {sorted(_SEXO_VALIDOS)}")
        return v

    @field_validator("status")
    @classmethod
    def _validar_status(cls, v):
        if v not in _STATUS_VALIDOS:
            raise ValueError(f"status deve ser um de {sorted(_STATUS_VALIDOS)}")
        return v


# ====================================================================
# ENDPOINTS NPCs (API REST)
# ====================================================================

@oficina_router.get("/api/npcs", tags=["npcs"])
async def listar_npcs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[Npcs]:
    """Lista NPCs paginados."""
    async with get_session() as session:
        statement = select(Npcs).order_by(Npcs.id).offset(skip).limit(limit)
        result = await session.exec(statement)
        return list(result.all())


@oficina_router.get("/api/npcs/count", tags=["npcs"])
async def contar_npcs() -> dict:
    async with get_session() as session:
        result = await session.exec(select(func.count()).select_from(Npcs))
        return {"total": result.one()}


@oficina_router.get("/api/npcs/{npc_id}", tags=["npcs"])
async def obter_npc(npc_id: int) -> Npcs:
    async with get_session() as session:
        npc = await session.get(Npcs, npc_id)
        if npc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"NPC {npc_id} nao encontrado",
            )
        return npc


@oficina_router.post("/api/npcs", tags=["npcs"], status_code=status.HTTP_201_CREATED)
async def criar_npc(payload: NpcCreate) -> Npcs:
    """Cria um novo NPC. Levanta 400 em caso de erro de constraint."""
    try:
        return await _criar_npc_no_banco(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ====================================================================
# HELPERS DE QUERY (usados pelos cards da home + API)
# ====================================================================

async def _contar_npcs_total() -> int:
    """Conta total de NPCs (usado pelo card da home)."""
    async with get_session() as session:
        result = await session.exec(select(func.count()).select_from(Npcs))
        return result.one()


async def _criar_npc_no_banco(dados: dict) -> Npcs:
    """Cria um NPC no banco a partir de um dict de dados."""
    dados_limpos = {}
    for k, v in dados.items():
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        if isinstance(v, list) and not v:
            continue
        dados_limpos[k] = v

    dados_limpos.setdefault("personality_summary", "")
    dados_limpos.setdefault("raca", "humano")
    dados_limpos.setdefault("status", "vivo")
    dados_limpos.setdefault("camada", 2)

    if "nome_curto" not in dados_limpos and "nome" in dados_limpos:
        partes = dados_limpos["nome"].split()
        dados_limpos["nome_curto"] = " ".join(partes[:2]) if partes else dados_limpos["nome"]

    novo = Npcs(**dados_limpos)

    async with get_session() as session:
        session.add(novo)
        try:
            await session.commit()
            await session.refresh(novo)
            return novo
        except IntegrityError as e:
            await session.rollback()
            msg_raw = str(e.orig) if e.orig else str(e)
            msg = msg_raw.split("\n")[0].replace("DETAIL:", "").strip()
            raise ValueError(f"Banco rejeitou: {msg}")


# ====================================================================
# UI NICEGUI - Pagina /oficina (home)
# ====================================================================

# ============================================================
# PELE VITRAL DA OFICINA — Fatia 1
# CSS/fonte via add_head_html (não sanitiza); corpo via ui.html.
# Estilo em classes (robustez anti-sanitizador). SVGs decorativos inline.
# ============================================================

_VITRAL_HEAD = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=IM+Fell+English+SC&family=Spectral:ital@0;1&display=swap" rel="stylesheet">
<style>
.q-layout,.q-page-container,.q-page{width:100%!important;max-width:none!important;}
.nicegui-content{width:100%!important;max-width:none!important;padding:0!important;gap:0!important;align-items:stretch!important;}
.cat-screen{box-sizing:border-box;}
body{margin:0;}
.cat-screen{position:relative;font-family:'Spectral',Georgia,serif;color:#e8dcc0;min-height:100vh;width:100%;overflow:hidden;background:linear-gradient(180deg,#0a0d1a 0%,#10141f 42%,#161b27 72%,#1b2029 100%);}
.cat-city{position:absolute;left:0;right:0;bottom:-7vh;width:100%;height:38vh;z-index:0;opacity:.92;}
.cat-moon{position:absolute;border-radius:50%;z-index:2;}
.cat-moon1{top:5vh;left:74%;width:42px;height:42px;background:radial-gradient(circle at 38% 35%,#d8dce4,#aeb4c2 68%,#878fa0);box-shadow:0 0 26px rgba(192,202,222,.2);}
.cat-moon2{top:9vh;left:60%;width:20px;height:20px;background:radial-gradient(circle at 40% 36%,#e0d2b4,#c2ad8c 70%,#937e60);box-shadow:0 0 16px rgba(200,182,150,.18);}
.cat-fog{position:absolute;left:0;right:0;bottom:0;height:30vh;background:linear-gradient(0deg,rgba(150,162,184,.2),rgba(150,162,184,.06) 55%,transparent);z-index:1;animation:haze 13s ease-in-out infinite;}
.cat-veil{position:absolute;inset:0;background:radial-gradient(130% 80% at 50% 16%,rgba(8,9,15,.55),rgba(8,9,15,.12) 50%,transparent 78%);z-index:1;}
.cat-mote{position:absolute;width:3px;height:3px;border-radius:50%;background:radial-gradient(circle,#f0d98a,transparent 70%);opacity:0;z-index:2;animation:float 9s linear infinite;}
.cat-mote.m1{left:18%;bottom:34%;animation-delay:0s;}.cat-mote.m2{left:44%;bottom:26%;animation-delay:2.6s;}.cat-mote.m3{left:68%;bottom:38%;animation-delay:4.3s;}.cat-mote.m4{left:82%;bottom:28%;animation-delay:6.2s;}.cat-mote.m5{left:31%;bottom:42%;animation-delay:7.6s;}
.cat-nav{position:relative;z-index:4;display:flex;align-items:center;gap:2px;padding:14px 30px;background:rgba(10,12,20,.92);border-bottom:1px solid #b8902f;}
.cat-navicon{margin-right:12px;flex:none;}
.cat-navlink{font-family:'IM Fell English SC',serif;letter-spacing:.12em;font-size:15px;color:#b3a06f;text-decoration:none;padding:4px 12px;white-space:nowrap;}
.cat-navlink:hover{color:#e8c66a;}
.cat-navlink.on{color:#f0d98a;border-bottom:1px solid #e8c66a;padding-bottom:3px;}
.cat-enter{font-family:'IM Fell English',serif;font-style:italic;letter-spacing:.04em;color:#e8c66a;text-decoration:none;font-size:16px;}
.cat-enter:hover{color:#f6d98a;}
.cat-inner{position:relative;z-index:4;max-width:1120px;margin:0 auto;padding:34px 30px 0;}
.cat-title{font-family:'IM Fell English',serif;font-size:38px;line-height:1.08;color:#f6ecd2;}
.cat-sub{font-family:'IM Fell English',serif;font-style:italic;font-size:15px;color:#c0a36a;margin-top:5px;}
.cat-rule{height:2px;background:linear-gradient(90deg,#5c4413,#e8c66a,#c89a22,#5c4413);background-size:220% 100%;animation:shimmer 7s linear infinite;margin:18px 0 0;}
.cat-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;padding:24px 0 0;}
.cat-card{position:relative;display:block;min-height:190px;border:1px solid #c9a227;border-radius:5px;overflow:hidden;box-shadow:inset 0 1px 0 rgba(255,238,190,.18);text-decoration:none;}
.cat-card.c-pers{--c1:#2f56b8;--c2:#16306e;--c3:#0b1742;}
.cat-card.c-estr{--c1:#c19022;--c2:#7a5512;--c3:#3f2b06;}
.cat-card.c-voc{--c1:#c4394a;--c2:#7a1f2b;--c3:#440d15;}
.cat-card.c-best{--c1:#239070;--c2:#14523f;--c3:#0a2c22;}
.cat-glass{position:absolute;inset:0;display:block;background:radial-gradient(92% 82% at 50% 8%,var(--c1),var(--c2) 55%,var(--c3));}
.cat-glow{position:absolute;inset:0;display:block;background:radial-gradient(58% 44% at 50% 5%,rgba(255,242,205,.5),transparent 62%);animation:lumen 7s ease-in-out infinite;}
.cat-card.c-estr .cat-glow{animation-delay:1.6s;}.cat-card.c-voc .cat-glow{animation-delay:3.2s;}.cat-card.c-best .cat-glow{animation-delay:4.6s;}
.cat-card:hover .cat-glow{opacity:.9;}
.cat-lead{position:absolute;inset:0;width:100%;height:100%;opacity:.42;}
.cat-body{position:relative;z-index:2;display:block;padding:56px 14px 18px;text-align:center;}
.cat-rot{display:block;font-family:'IM Fell English SC',serif;letter-spacing:.16em;font-size:13px;}
.cat-num{display:block;font-family:'IM Fell English',serif;font-size:50px;line-height:1;color:#f6ecd2;margin:6px 0 10px;text-shadow:0 0 14px rgba(255,232,180,.25);}
.cat-dsc{display:block;font-style:italic;font-size:13px;line-height:1.5;}
.c-pers .cat-rot{color:#c2d4ff;}.c-pers .cat-dsc{color:#aebde8;}
.c-estr .cat-rot{color:#f6dca0;}.c-estr .cat-dsc{color:#ecd296;}
.c-voc .cat-rot{color:#f8c4ca;}.c-voc .cat-dsc{color:#edaeb5;}
.c-best .cat-rot{color:#aeead2;}.c-best .cat-dsc{color:#95dabd;}
.cat-hist{position:relative;z-index:4;display:flex;align-items:center;gap:18px;margin:18px 0 0;padding:18px 24px;border:1px solid #c9a227;border-radius:6px;background:linear-gradient(100deg,rgba(46,33,82,.9),rgba(26,18,52,.82) 70%,rgba(20,14,40,.76));box-shadow:inset 0 1px 0 rgba(228,196,255,.16);text-decoration:none;}
.cat-hist:hover{border-color:#f0d98a;}
.cat-hist-txt{flex:1;}
.cat-hist-t{display:block;font-family:'IM Fell English',serif;font-size:21px;color:#efe6cf;line-height:1.1;}
.cat-hist-d{display:block;font-style:italic;font-size:13px;color:#cbb9e8;margin-top:3px;}
.cat-hist-go{font-family:'IM Fell English',serif;font-style:italic;font-size:14px;color:#e8c66a;white-space:nowrap;}
.cat-foot{position:relative;z-index:4;text-align:center;font-family:'IM Fell English',serif;font-style:italic;font-size:12px;color:#8a7440;padding:88px 0 28px;}
.cat-soon{position:relative;z-index:4;font-style:italic;font-size:15px;color:#9a8a6a;padding:28px 0;}
@keyframes lumen{0%,100%{opacity:.32}50%{opacity:.7}}
@keyframes shimmer{to{background-position:220% 0}}
@keyframes float{0%{transform:translateY(10px);opacity:0}25%{opacity:.7}100%{transform:translateY(-26px);opacity:0}}
@keyframes haze{0%,100%{opacity:.7}50%{opacity:1}}
@media (prefers-reduced-motion: reduce){.cat-glow,.cat-rule,.cat-mote,.cat-fog{animation:none!important;}}
</style>
"""

_VITRAL_ARCO = "M16,74 Q28,20 75,15 Q122,20 134,74 M75,15 L75,188 M16,74 L16,188 M134,74 L134,188 M16,128 L134,128"
_VITRAL_EMBLEMA = {
    "pers": '<circle cx="75" cy="42" r="6"/><path d="M62,62 Q75,44 88,62"/>',
    "estr": '<path d="M75,28 L79,40 L91,42 L79,45 L75,57 L71,45 L59,42 L71,40 Z"/>',
    "voc":  '<path d="M75,28 L88,33 V45 Q88,56 75,60 Q62,56 62,45 V33 Z"/><path d="M75,31 L75,57"/>',
    "best": '<path d="M63,52 Q57,30 68,31 M87,52 Q93,30 82,31"/><circle cx="70" cy="46" r="1.6"/><circle cx="80" cy="46" r="1.6"/>',
}
_VITRAL_STROKE = {"pers": "#e0bd5a", "estr": "#ffe9a8", "voc": "#ffc2c9", "best": "#a7e6cd"}


def _vitral_cena() -> str:
    """Camada de fundo: catedral + casario, duas luas, bruma, véu, poeira."""
    city = (
        '<svg class="cat-city" viewBox="0 0 680 248" preserveAspectRatio="xMidYMax slice" aria-hidden="true">'
        '<path d="M0,248 L0,202 L34,202 L34,180 L72,180 L72,206 L108,206 L108,186 L150,186 L150,248 Z '
        'M512,248 L512,190 L548,190 L548,168 L584,168 L584,198 L622,198 L622,180 L680,180 L680,248 Z" fill="#070a12"/>'
        '<g fill="#070a12"><rect x="300" y="152" width="80" height="96"/><polygon points="300,152 340,120 380,152"/>'
        '<rect x="286" y="122" width="20" height="126"/><polygon points="286,122 296,94 306,122"/>'
        '<rect x="374" y="122" width="20" height="126"/><polygon points="374,122 384,94 394,122"/>'
        '<polygon points="334,152 340,58 346,152"/></g>'
        '<circle cx="340" cy="180" r="11" fill="none" stroke="#b8902f" stroke-width="1.4" opacity=".65"/>'
        '<circle cx="340" cy="180" r="4" fill="#c9a227" opacity=".5"/>'
        '<g fill="#c9a227"><rect x="292" y="150" width="5" height="13" opacity=".5"/><rect x="383" y="150" width="5" height="13" opacity=".5"/>'
        '<rect x="316" y="200" width="6" height="16" rx="3" opacity=".5"/><rect x="358" y="200" width="6" height="16" rx="3" opacity=".5"/>'
        '<rect x="46" y="208" width="4" height="6" opacity=".4"/><rect x="86" y="186" width="4" height="6" opacity=".45"/>'
        '<rect x="120" y="210" width="4" height="6" opacity=".4"/><rect x="560" y="196" width="4" height="6" opacity=".4"/>'
        '<rect x="596" y="204" width="4" height="6" opacity=".45"/></g></svg>'
    )
    return (
        city
        + '<div class="cat-moon cat-moon1"></div><div class="cat-moon cat-moon2"></div>'
        + '<div class="cat-fog"></div><div class="cat-veil"></div>'
        + '<span class="cat-mote m1"></span><span class="cat-mote m2"></span><span class="cat-mote m3"></span>'
        + '<span class="cat-mote m4"></span><span class="cat-mote m5"></span>'
    )


def _vitral_barra(ativo: str = "") -> str:
    """Barra de navegação na pele vitral. Rótulos novos, rotas reais inalteradas."""
    icone = ('<svg class="cat-navicon" width="16" height="14" viewBox="0 0 24 20" fill="none" '
             'stroke="#c9a227" stroke-width="1.1" aria-hidden="true">'
             '<path d="M12 3c3 0 5 2 5 5s-2 7-5 9c-3-2-5-6-5-9s2-5 5-5z"/><path d="M3 10h6M15 10h6"/></svg>')
    itens = [
        ("oficina", "oficina", "/oficina"),
        ("personagens", "personagens", "/oficina/npcs"),
        ("bestiário", "bestiario", "/oficina/bestiario"),
        ("estrelas", "estrelas", "/oficina/estrelas"),
        ("vocações", "vocacoes", "/oficina/vocacoes"),
        ("histórias", "historias", "/oficina/historias"),
    ]
    links = "".join(
        f'<a class="cat-navlink{" on" if chave == ativo else ""}" href="{destino}">{rotulo}</a>'
        for rotulo, chave, destino in itens
    )
    return (f'<div class="cat-nav">{icone}{links}<span style="flex:1"></span>'
            f'<a class="cat-enter" href="/jogar">entrar no mundo</a></div>')


def _vitral_card(cls: str, rotulo: str, numero, frase: str, href: str) -> str:
    """Um vitral-contador clicável."""
    return (
        f'<a class="cat-card c-{cls}" href="{href}">'
        f'<span class="cat-glass"></span><span class="cat-glow"></span>'
        f'<svg class="cat-lead" viewBox="0 0 150 200" fill="none" stroke="{_VITRAL_STROKE[cls]}" '
        f'stroke-width="1.1" aria-hidden="true"><path d="{_VITRAL_ARCO}"/>{_VITRAL_EMBLEMA[cls]}</svg>'
        f'<span class="cat-body"><span class="cat-rot">{rotulo}</span>'
        f'<span class="cat-num">{numero}</span><span class="cat-dsc">{frase}</span></span></a>'
    )


def _vitral_card_historias() -> str:
    livro = ('<svg width="40" height="40" viewBox="0 0 60 60" fill="none" stroke="#e0bd5a" '
             'stroke-width="1.4" style="flex:none" aria-hidden="true">'
             '<path d="M30,16 Q18,9 8,13 L8,46 Q18,42 30,49 Q42,42 52,46 L52,13 Q42,9 30,16 Z"/><path d="M30,16 L30,49"/>'
             '<path d="M13,21 Q20,18 26,21 M13,29 Q20,26 26,29 M34,21 Q40,18 47,21 M34,29 Q40,26 47,29"/></svg>')
    return (
        '<a class="cat-hist" href="/oficina/historias">'
        + livro
        + '<span class="cat-hist-txt"><span class="cat-hist-t">Histórias do mundo</span>'
        '<span class="cat-hist-d">a crônica de Alderyn &mdash; eras, ruínas, e o que sobrou.</span></span>'
        '<span class="cat-hist-go">abrir a crônica &rsaquo;</span></a>'
    )


def _vitral_dashboard(npcs, estrelas, vocacoes, criaturas) -> str:
    return (
        '<div class="cat-screen">'
        + _vitral_cena()
        + _vitral_barra("oficina")
        + '<div class="cat-inner">'
        '<div class="cat-title">Oficina do Mestre</div>'
        '<div class="cat-sub">Sistema Nexus &mdash; mundo de Alderyn</div>'
        '<div class="cat-rule"></div>'
        '<div class="cat-grid">'
        + _vitral_card("pers", "personagens", npcs, "os que vivem &mdash; e os que já viveram.", "/oficina/npcs")
        + _vitral_card("estr", "estrelas", estrelas, "os astros sob os quais se nasce.", "/oficina/estrelas")
        + _vitral_card("voc", "vocações", vocacoes, "ofícios e caminhos do mundo.", "/oficina/vocacoes")
        + _vitral_card("best", "bestiário", criaturas, "o que se move na zona cinzenta.", "/oficina/bestiario")
        + '</div>'
        + _vitral_card_historias()
        + '</div>'
        + '<div class="cat-foot">vigília quebrada &middot; ano 312</div>'
        + '</div>'
    )


@ui.page("/oficina")
async def pagina_oficina():
    # FIX TIMEOUT NICEGUI: envia placeholder + aguarda WS antes das queries.
    await aguardar_conexao_websocket("Carregando Oficina...")

    ui.add_head_html(_VITRAL_HEAD)

    try:
        total_npcs, total_estrelas, total_vocacoes, total_criaturas = await asyncio.wait_for(
            asyncio.gather(
                _contar_npcs_total(),
                _contar_estrelas_total(),
                _contar_vocacoes_total(),
                contar_criaturas_canonizadas(),
            ),
            timeout=10.0,
        )
    except Exception as e:
        print(f"[home] erro ao contar: {e}")
        total_npcs = total_estrelas = total_vocacoes = total_criaturas = 0

    ui.html(_vitral_dashboard(total_npcs, total_estrelas, total_vocacoes, total_criaturas)).classes("w-full")


@ui.page("/oficina/historias")
async def pagina_historias():
    await aguardar_conexao_websocket("Carregando...")
    ui.add_head_html(_VITRAL_HEAD)
    ui.html(
        '<div class="cat-screen">'
        + _vitral_cena()
        + _vitral_barra("historias")
        + '<div class="cat-inner">'
        '<div class="cat-title">Histórias do mundo</div>'
        '<div class="cat-sub">a crônica de Alderyn &mdash; eras, ruínas, e o que sobrou.</div>'
        '<div class="cat-rule"></div>'
        '<div class="cat-soon">A crônica está sendo escrita. Volte em breve.</div>'
        '</div>'
        + '<div class="cat-foot">vigília quebrada &middot; ano 312</div>'
        + '</div>'
    ).classes("w-full")


# ====================================================================
# UI NICEGUI - Paginas /oficina/npcs e /oficina/npcs/{id} (Modulo 4.2)
# ====================================================================
# NOTA: aguardar_conexao_websocket() ja e chamado dentro de
# pagina_lista_npcs_rica e pagina_npc_detalhe (em oficina_npcs_42.py).
# Nao precisa duplicar aqui.

@ui.page("/oficina/npcs")
async def pagina_lista_npcs():
    """Lista rica com filtros + busca fuzzy + 9 colunas."""
    await pagina_lista_npcs_rica()


@ui.page("/oficina/npcs/{npc_id}")
async def pagina_npc_detalhe_route(npc_id: int):
    """Detalhe rico com 13 secoes do ecossistema NPC."""
    await pagina_npc_detalhe(npc_id)

@ui.page("/oficina/atelie/{npc_id}")
async def pagina_atelie_route(npc_id: int):
    """Ateliê de Geração de Imagens (Módulo 4.6.4)."""
    await pagina_atelie(npc_id)


# ====================================================================
# UI NICEGUI - Paginas /oficina/bestiario (Modulo 7.1)
# ====================================================================

@ui.page("/oficina/bestiario")
async def pagina_bestiario_lista():
    """Lista de criaturas canonizadas do Bestiário."""
    await pagina_lista_bestiario()


@ui.page("/oficina/bestiario/{criatura_id}")
async def pagina_bestiario_detalhe(criatura_id: int):
    """Detalhe de criatura com visual dark fantasy."""
    await pagina_criatura_detalhe(criatura_id)


# ====================================================================
# === ESTRELAS DO VEU - ROTAS (Modulo 5.2) ===
# ====================================================================

async def _contar_estrelas_total() -> int:  # Modulo 5.3
    """Conta total de estrelas (usado pelo card da home)."""
    async with get_session() as session:
        result = await session.exec(
            select(func.count()).select_from(RefEstrelasNascimento)
        )
        return result.one()


async def _buscar_estrelas() -> list[dict]:
    """Busca as 12 estrelas ordenadas por id com tudo que o card precisa."""
    async with get_session() as session:
        statement = select(RefEstrelasNascimento).order_by(
            RefEstrelasNascimento.id
        )
        result = await session.exec(statement)
        estrelas = result.all()
    return [
        {
            "id": e.id,
            "nome": e.nome,
            "epiteto": e.epiteto,
            "lema": e.lema,
            "atributos": e.atributos_primarios,
            "pct_1": e.pct_primeira_cat,
            "pct_2": e.pct_segunda_cat,
            "pct_3": e.pct_terceira_cat,
            "lendaria": e.habilidade_100_nome,
        }
        for e in estrelas
    ]


def _render_card_estrela(e: dict) -> None:
    """Renderiza um card individual de estrela no grid."""
    with ui.card().classes(
        "w-full h-full flex flex-col bg-zinc-800 border border-zinc-700 p-5 "
        "cursor-pointer hover:border-amber-700 transition-colors gap-3"
    ).on(
        "click",
        lambda eid=e["id"]: ui.navigate.to(f"/oficina/estrelas/{eid}"),
    ):
        # Cabecalho: nome + epiteto
        with ui.column().classes("w-full gap-0"):
            ui.label(e["nome"]).classes(
                "text-2xl font-bold text-amber-200 tracking-wide"
            )
            ui.label(e["epiteto"]).classes(
                "text-sm text-zinc-400 italic"
            )

        # Lema
        ui.label(f"\u201c{e['lema']}\u201d").classes(
            "text-xs text-zinc-300 italic leading-snug"
        )

        # Atributos primarios
        with ui.row().classes("w-full items-center gap-2"):
            ui.icon("fitness_center", size="1rem").classes("text-zinc-500")
            ui.label(e["atributos"]).classes(
                "text-xs font-mono text-zinc-400"
            )

        # Distribuicao visual
        with ui.column().classes("w-full gap-1"):
            ui.label("Distribuição").classes(
                "text-xs uppercase tracking-wider text-zinc-500"
            )
            with ui.row().classes("w-full items-center gap-0 h-2"):
                ui.element("div").classes(
                    "h-2 bg-amber-700 rounded-l"
                ).style(f"width: {e['pct_1']}%")
                ui.element("div").classes("h-2 bg-amber-500").style(
                    f"width: {e['pct_2']}%"
                )
                ui.element("div").classes(
                    "h-2 bg-amber-300 rounded-r"
                ).style(f"width: {e['pct_3']}%")
            with ui.row().classes("w-full justify-between"):
                ui.label(f"Raras {e['pct_1']}%").classes(
                    "text-xs text-amber-300 font-mono"
                )
                ui.label(f"Médias {e['pct_2']}%").classes(
                    "text-xs text-zinc-500 font-mono"
                )
                ui.label(f"Comuns {e['pct_3']}%").classes(
                    "text-xs text-zinc-600 font-mono"
                )

        ui.separator().classes("bg-zinc-700 mt-auto")

        # Lendária (d100=100)
        with ui.column().classes("w-full gap-0"):
            ui.label("Lendária (d100=100)").classes(
                "text-xs uppercase tracking-wider text-zinc-500"
            )
            ui.label(e["lendaria"]).classes(
                "text-sm text-amber-200 font-semibold italic"
            )


@ui.page("/oficina/estrelas")
async def pagina_estrelas():
    """Grid 4x3 das 12 estrelas do Veu. Primeira tela real da Catedral."""
    # FIX TIMEOUT NICEGUI: envia placeholder + aguarda WS antes das queries.
    await aguardar_conexao_websocket("Catalogando estrelas do Véu...")

    barra_nav("estrelas")

    estrelas = await _buscar_estrelas()

    with ui.column().classes(
        "w-full min-h-screen bg-zinc-900 text-zinc-100 p-8 gap-6"
    ):
        # Header com botao voltar
        with ui.row().classes("w-full items-center justify-between"):
            with ui.row().classes("items-center gap-3"):
                ui.button(
                    icon="arrow_back",
                    on_click=lambda: ui.navigate.to("/oficina"),
                ).props("flat round dense color=amber-2")

                with ui.column().classes("gap-0"):
                    ui.label("Estrelas do Véu").classes(
                        "text-3xl font-bold text-amber-200"
                    )
                    ui.label(
                        f"{len(estrelas)} astros sob os quais as almas nascem"
                    ).classes("text-sm text-zinc-400 italic")

        ui.separator().classes("bg-zinc-700")

        # Grid responsivo 4x3
        with ui.element("div").classes(
            "w-full grid grid-cols-1 md:grid-cols-2 "
            "lg:grid-cols-3 xl:grid-cols-4 gap-4"
        ):
            for e in estrelas:
                _render_card_estrela(e)

        with ui.row().classes("w-full justify-center mt-auto pt-8"):
            ui.label(
                "Módulo 5.4 OK. Clique numa estrela pra ver suas 100 habilidades."
            ).classes("text-xs text-zinc-600 italic")



# ====================================================================
# === ESTRELA DETALHE - ROTAS (Módulo 5.4) ===
# ====================================================================

_CAT_LABELS = {
    1: ("Raras", "amber-700", "auto_awesome"),
    2: ("Médias", "amber-500", "star_half"),
    3: ("Comuns", "zinc-500", "star_outline"),
}


async def _buscar_estrela_por_id(estrela_id: int) -> dict | None:
    """Busca uma estrela pelo id. Retorna None se nao existir."""
    async with get_session() as session:
        result = await session.exec(
            select(RefEstrelasNascimento)
            .where(RefEstrelasNascimento.id == estrela_id)
        )
        e = result.first()
        if not e:
            return None
        return {
            "id": e.id,
            "nome": e.nome,
            "epiteto": e.epiteto,
            "lema": e.lema,
            "atributos": e.atributos_primarios,
            "pct_1": e.pct_primeira_cat,
            "pct_2": e.pct_segunda_cat,
            "pct_3": e.pct_terceira_cat,
            "lendaria_nome": e.habilidade_100_nome,
        }


async def _buscar_habilidades_estrela(
    estrela_id: int,
) -> dict[int, list[dict]]:
    """Busca as 100 habilidades de uma estrela, agrupadas por categoria."""
    async with get_session() as session:
        result = await session.exec(
            select(RefHabilidadesEstrela)
            .where(RefHabilidadesEstrela.estrela_id == estrela_id)
            .order_by(RefHabilidadesEstrela.numero_d100)
        )
        habs = result.all()

    agrupadas: dict[int, list[dict]] = {1: [], 2: [], 3: []}
    for h in habs:
        agrupadas.setdefault(h.categoria, []).append({
            "d100": h.numero_d100,
            "nome": h.nome,
            "descricao": h.descricao_completa,
            "categoria": h.categoria,
            "tem_preco": h.tem_preco,
            "lendaria": h.numero_d100 == 100,
        })
    return agrupadas


def _render_habilidade(h: dict) -> None:
    """Renderiza uma habilidade individual."""
    is_lend = h["lendaria"]
    is_preco = h["tem_preco"]

    border = "border-amber-600" if is_lend else "border-zinc-700"
    bg = "bg-zinc-750" if not is_lend else "bg-zinc-800"

    with ui.card().classes(
        f"w-full {bg} border {border} p-4 gap-2"
    ).props("flat"):
        # Linha do cabecalho: d100 + nome + badges
        with ui.row().classes("w-full items-center gap-2 flex-wrap"):
            ui.badge(
                f"d{h['d100']:02d}",
                color="amber-8" if is_lend else "zinc-6",
            ).props("rounded")

            nome_display = h["nome"]
            nome_cls = (
                "text-base font-bold text-amber-200"
                if is_lend
                else "text-base font-semibold text-zinc-200"
            )
            ui.label(nome_display).classes(nome_cls)

            if is_preco:
                ui.icon("local_fire_department", size="1.2rem").classes(
                    "text-orange-400"
                ).tooltip("Esta habilidade cobra um preco")
            if is_lend:
                ui.badge("LENDARIA", color="amber-9").props("rounded")

        # Descricao com expand/collapse
        desc = h["descricao"]
        if len(desc) <= 250:
            ui.label(desc).classes(
                "text-sm text-zinc-300 whitespace-pre-line leading-relaxed"
            )
        else:
            trecho = desc[:220].rsplit(" ", 1)[0] + "..."
            desc_lbl = ui.label(trecho).classes(
                "text-sm text-zinc-300 whitespace-pre-line leading-relaxed"
            )
            expandido = {"v": False}

            def toggle(
                lbl=desc_lbl, full=desc, short=trecho, state=expandido
            ):
                state["v"] = not state["v"]
                lbl.set_text(full if state["v"] else short)
                btn_expand.set_text(
                    "ver menos" if state["v"] else "ver mais..."
                )

            btn_expand = ui.button(
                "ver mais...", on_click=toggle
            ).props("flat dense size=sm color=amber-4").classes("self-start")


@ui.page("/oficina/estrelas/{estrela_id}")
async def pagina_estrela_detalhe(estrela_id: int):
    """Pagina de detalhe de uma estrela com suas 100 habilidades."""
    # FIX TIMEOUT NICEGUI: envia placeholder + aguarda WS antes das queries.
    await aguardar_conexao_websocket(f"Buscando estrela #{estrela_id}...")

    estrela = await _buscar_estrela_por_id(estrela_id)

    if not estrela:
        with ui.column().classes(
            "w-full min-h-screen bg-zinc-900 text-zinc-100 p-8 items-center "
            "justify-center gap-4"
        ):
            ui.label("Estrela nao encontrada.").classes(
                "text-2xl text-zinc-400"
            )
            ui.button(
                "Voltar", on_click=lambda: ui.navigate.to("/oficina/estrelas")
            ).props("color=amber-8")
        return

    habs_por_cat = await _buscar_habilidades_estrela(estrela_id)

    with ui.column().classes(
        "w-full min-h-screen bg-zinc-900 text-zinc-100 p-8 gap-6"
    ):
        # === Header ===
        with ui.row().classes("w-full items-start justify-between"):
            with ui.row().classes("items-center gap-3"):
                ui.button(
                    icon="arrow_back",
                    on_click=lambda: ui.navigate.to("/oficina/estrelas"),
                ).props("flat round dense color=amber-2")

                with ui.column().classes("gap-0"):
                    with ui.row().classes("items-baseline gap-3"):
                        ui.label(estrela["nome"]).classes(
                            "text-4xl font-bold text-amber-200 tracking-wide"
                        )
                        ui.label(estrela["epiteto"]).classes(
                            "text-xl text-zinc-400 italic"
                        )
                    ui.label(
                        f'\u201c{estrela["lema"]}\u201d'
                    ).classes("text-sm text-zinc-300 italic mt-1")

        # === Stats compactos ===
        with ui.row().classes("w-full items-center gap-6 flex-wrap"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("fitness_center", size="1rem").classes("text-zinc-500")
                ui.label(estrela["atributos"]).classes(
                    "text-sm font-mono text-zinc-400"
                )
            with ui.row().classes("items-center gap-4"):
                ui.label(
                    f'Raras {estrela["pct_1"]}%'
                ).classes("text-xs font-mono text-amber-300")
                ui.label(
                    f'Medias {estrela["pct_2"]}%'
                ).classes("text-xs font-mono text-zinc-500")
                ui.label(
                    f'Comuns {estrela["pct_3"]}%'
                ).classes("text-xs font-mono text-zinc-600")

        ui.separator().classes("bg-zinc-700")

        # === 3 secoes por categoria ===
        for cat in [1, 2, 3]:
            label_cat, cor_cat, icone_cat = _CAT_LABELS[cat]
            habs = habs_por_cat.get(cat, [])
            n = len(habs)

            with ui.expansion(
                f"Categoria {cat} — {label_cat} ({n} habilidades)",
                icon=icone_cat,
                value=(cat <= 2),
            ).classes(
                "w-full bg-zinc-800 rounded mb-2"
            ).props("dense header-class=text-amber-100"):
                with ui.column().classes("w-full gap-3 p-2"):
                    if not habs:
                        ui.label("Nenhuma habilidade nesta categoria.").classes(
                            "text-zinc-500 italic"
                        )
                    else:
                        for h in habs:
                            _render_habilidade(h)

        # === Rodape ===
        with ui.row().classes("w-full justify-center mt-auto pt-8"):
            total = sum(len(v) for v in habs_por_cat.values())
            ui.label(
                f"Módulo 5.4 OK. {total} habilidades de {estrela['nome']}."
            ).classes("text-xs text-zinc-600 italic")



# ====================================================================
# === VOCACOES - ROTAS (Módulo 6.2) ===
# ====================================================================

_VOC_SORTABLE_FIELDS = {"id", "nome_ptbr", "pilar", "tipo"}
_PILARES_CONCEITUAIS = ("corpo", "sombra", "arcano", "espirito", "engenho")
_PILARES_VALIDOS = _PILARES_CONCEITUAIS + ("Fundida",)


async def _buscar_filosofia_pilar(nome: str) -> dict | None:
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
    """Busca pagina de vocacoes com filtros."""
    if sort_by not in _VOC_SORTABLE_FIELDS:
        sort_by = "id"

    skip = max(0, (page - 1) * rows_per_page)

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
        pilar_display = v.pilar if not is_anomalia else f"⚠ {v.pilar}"
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
    # FIX TIMEOUT NICEGUI: envia placeholder + aguarda WS antes das queries.
    await aguardar_conexao_websocket("Catalogando vocações...")

    barra_nav("vocacoes")

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
        pag["page"] = 1
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
                    ("corpo", "Corpo"),
                    ("sombra", "Sombra"),
                    ("arcano", "Arcano"),
                    ("espirito", "Espírito"),
                    ("engenho", "Engenho"),
                    ("Fundida", "Fundida"),
                    ("anomalias", "⚠ Anomalias"),
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
                ui.label("Disponível:").classes("text-xs uppercase text-zinc-500")
                for opcao, label in [
                    ("todos", "Todas"),
                    ("disponiveis", "Disponíveis"),
                    ("bloqueadas", "🚫 Bloqueadas (13)"),
                ]:
                    cor = "amber-8" if opcao != "bloqueadas" else "red-9"
                    ui.button(label, on_click=lambda v=opcao: set_filtro_disponivel(v)).props(
                        f"flat dense size=sm color={cor}"
                    )

        # === Card de filosofia do pilar (reativo) ===
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

        _refresh_original = refresh

        async def refresh_com_filosofia() -> None:
            await _refresh_original()
            await atualizar_filosofia()

        def set_filtro_pilar_v2(valor: str) -> None:
            filtros_state["pilar"] = valor
            asyncio.create_task(refresh_com_filosofia())

        set_filtro_pilar = set_filtro_pilar_v2  # noqa: F811

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

        def ir_pro_detalhe(e: GenericEventArguments) -> None:
            row = e.args[1]
            if row and "id" in row:
                ui.navigate.to(f"/oficina/vocacoes/{row['id']}")

        table.on("rowClick", ir_pro_detalhe)

        with ui.row().classes("w-full justify-center mt-auto pt-6"):
            ui.label(
                "Módulo 6.3 OK. Clique numa linha pra ver detalhes."
            ).classes("text-xs text-zinc-600 italic")



# ====================================================================
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
    # FIX TIMEOUT NICEGUI: envia placeholder + aguarda WS antes das queries.
    await aguardar_conexao_websocket(f"Buscando vocação #{voc_id}...")

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

    pilares_validos = ("corpo", "sombra", "arcano", "espirito", "engenho", "Fundida")
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
                        pilar_txt = f"⚠ {data['pilar']}" if is_anomalia else f"Pilar {data['pilar']}"
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

        # === Filosofia do pilar ===
        if data["pilar"] in ("corpo", "sombra", "arcano", "espirito", "engenho"):
            filosofia_data = await _buscar_filosofia_pilar(data["pilar"])
            if filosofia_data:
                with ui.card().classes(
                    "w-full bg-zinc-800 border border-amber-800 p-4"
                ).props("flat"):
                    with ui.row().classes("items-baseline gap-3"):
                        ui.label(filosofia_data["nome"]).classes(
                            "text-sm font-bold text-amber-200 uppercase tracking-wider"
                        )
                        ui.label(filosofia_data["epiteto"]).classes(
                            "text-xs text-zinc-400 italic"
                        )
                    ui.label(filosofia_data["filosofia"]).classes(
                        "text-xs text-zinc-400 italic leading-relaxed mt-2"
                    )

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



# NiceGUI e montado no app do monolito pelo server.py (ui.run_with la).
