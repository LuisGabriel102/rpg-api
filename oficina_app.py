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
import html
import warnings

# Silencia warnings cosmeticos do SQLModel
warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from contextlib import asynccontextmanager
from string import Template
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
from tema_oficina import CSS_VITRAL, CSS_PERGAMINHO
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


# ============================================================
# A CATEDRAL DO ALDERYN (v6) — landing in-place de /oficina
# Bloco A: funcao pura (template + render), sem I/O.
# Fontes (IM Fell English / SC / Spectral) ja vem da pele vitral
# (_VITRAL_HEAD), por isso o template NAO tem @import.
# ============================================================

_CATEDRAL_TPL = Template("""
<style>
.ct-sc{font-family:'IM Fell English SC',serif}
.ct-se{font-family:'IM Fell English',serif}
.ct-bo{font-family:'Spectral',serif}
.ct-wrap{max-width:680px;margin:0 auto}
.ct-n{position:relative;height:182px;text-decoration:none;display:block}
.ct-n .body{position:relative;height:100%;display:flex;flex-direction:column;align-items:center;padding:18px 14px 15px;box-sizing:border-box;transition:transform .15s}
.ct-n svg.frame{position:absolute;inset:0;width:100%;height:100%}
.ct-n:hover .body{transform:translateY(-2px)}
.ct-cta{display:inline-flex;align-items:center;gap:9px;background:linear-gradient(180deg,#1f2742,#171d33);border:1.5px solid #caa23a;color:#f0d987;font-size:16px;padding:11px 22px;border-radius:10px;text-decoration:none;transition:transform .15s}
.ct-cta:hover{transform:translateY(-2px)}
.ct-link{display:inline-flex;align-items:center;gap:7px;color:#b6a684;font-size:13.5px;text-decoration:none;border-bottom:1px solid rgba(182,166,132,.35);padding-bottom:2px}
.ct-link:hover{color:#e6c45c;border-bottom-color:#e6c45c}
</style>
<div class="ct-wrap" aria-label="A Catedral do Alderyn" style="background:#13172a;border:1px solid rgba(202,162,58,.34);border-radius:12px;padding:1.4rem 1.3rem 1.5rem">

  <div style="max-width:330px;margin:0 auto;position:relative;height:264px">
    <svg viewBox="0 0 320 262" preserveAspectRatio="none" aria-hidden="true" style="position:absolute;inset:0;width:100%;height:100%">
      <path d="M12 258 L12 96 Q70 26 160 16 Q250 26 308 96 L308 258 Z" fill="#10131f" stroke="#c9a23a" stroke-width="1.6" vector-effect="non-scaling-stroke"/>
      <path d="M18 258 L18 98 Q74 34 160 24 Q246 34 302 98 L302 258" fill="none" stroke="#7e6420" stroke-width="1" opacity=".7" vector-effect="non-scaling-stroke"/>
    </svg>
    <div style="position:relative;height:100%;display:flex;flex-direction:column;align-items:center;padding-top:20px;box-sizing:border-box">
      <svg viewBox="0 0 200 200" width="126" height="126" role="img" aria-label="Rosácea de vitral da Catedral">
        <title>Rosácea de vitral</title>
        <circle cx="100" cy="100" r="84" fill="#10131f"/>
        <line x1="100" y1="100" x2="100" y2="18"  stroke="#5a4a22" stroke-width="1.4" opacity=".5"/>
        <line x1="100" y1="100" x2="171" y2="59"  stroke="#5a4a22" stroke-width="1.4" opacity=".5"/>
        <line x1="100" y1="100" x2="171" y2="141" stroke="#5a4a22" stroke-width="1.4" opacity=".5"/>
        <line x1="100" y1="100" x2="100" y2="182" stroke="#5a4a22" stroke-width="1.4" opacity=".5"/>
        <line x1="100" y1="100" x2="29"  y2="141" stroke="#5a4a22" stroke-width="1.4" opacity=".5"/>
        <line x1="100" y1="100" x2="29"  y2="59"  stroke="#5a4a22" stroke-width="1.4" opacity=".5"/>
        <circle cx="100"    cy="30"     r="9" fill="#233452" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="135"    cy="39.38"  r="9" fill="#2c2748" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="160.62" cy="65"     r="9" fill="#1f3a4e" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="170"    cy="100"    r="9" fill="#2a4636" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="160.62" cy="135"    r="9" fill="#463618" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="135"    cy="160.62" r="9" fill="#3e2228" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="100"    cy="170"    r="9" fill="#233452" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="65"     cy="160.62" r="9" fill="#2c2748" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="39.38"  cy="135"    r="9" fill="#1f3a4e" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="30"     cy="100"    r="9" fill="#2a4636" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="39.38"  cy="65"     r="9" fill="#463618" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="65"     cy="39.38"  r="9" fill="#3e2228" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="100" cy="100" r="84" fill="none" stroke="#b8902f" stroke-width="2.4"/>
        <circle cx="100" cy="100" r="87" fill="none" stroke="#7e6420" stroke-width="1"/>
        <circle cx="100" cy="100" r="50" fill="#10131f" stroke="#b8902f" stroke-width="1.6"/>
        <circle cx="100"    cy="64"     r="11" fill="#9a4e30" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="134.24" cy="88.88"  r="11" fill="#6f5a96" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="121.16" cy="129.12" r="11" fill="#3f6a9e" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="78.84"  cy="129.12" r="11" fill="#468268" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="65.76"  cy="88.88"  r="11" fill="#a07e2a" stroke="#0d1018" stroke-width="1.2"/>
        <circle cx="100" cy="100" r="15"  fill="#c9a23a" stroke="#0d1018" stroke-width="1.4"/>
        <circle cx="100" cy="100" r="6.5" fill="#f3e7c4"/>
      </svg>
      <div class="ct-sc" style="font-size:21px;letter-spacing:.04em;color:#e6c45c;margin-top:8px">A Catedral do Alderyn</div>
      <div class="ct-bo" style="font-style:italic;font-size:12.5px;color:#b6a684;margin-top:3px">Tudo aqui tem um preço. Inclusive saber.</div>
    </div>
  </div>

  <div style="display:flex;align-items:center;justify-content:center;gap:14px;margin:.9rem 0 1.3rem">
    <span style="height:1px;width:64px;background:linear-gradient(90deg,transparent,#b8902f)"></span>
    <span style="color:#caa23a;font-size:12px">&#9670;</span>
    <span style="height:1px;width:64px;background:linear-gradient(90deg,#b8902f,transparent)"></span>
  </div>

  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:14px">

    <a class="ct-n" href="$vocacoes_href">
      <svg class="frame" viewBox="0 0 200 182" preserveAspectRatio="none" aria-hidden="true"><path d="M6 178 L6 64 Q42 14 100 8 Q158 14 194 64 L194 178 Z" fill="#1a2039" stroke="#caa23a" stroke-width="2.4" vector-effect="non-scaling-stroke"/></svg>
      <div class="body">
        <div style="height:40px;display:flex;align-items:center">
          <svg viewBox="0 0 48 48" width="40" height="40" aria-hidden="true">
            <circle cx="24" cy="24" r="16" fill="none" stroke="#b8902f" stroke-width="1.2" opacity=".7"/>
            <circle cx="24" cy="10" r="4.4" fill="#9a4e30"/><circle cx="37.3" cy="19.7" r="4.4" fill="#6f5a96"/><circle cx="32.2" cy="35.3" r="4.4" fill="#3f6a9e"/><circle cx="15.8" cy="35.3" r="4.4" fill="#468268"/><circle cx="10.7" cy="19.7" r="4.4" fill="#a07e2a"/><circle cx="24" cy="24" r="2.4" fill="#e6c45c"/>
          </svg>
        </div>
        <div class="ct-se" style="font-size:19px;color:#f6ecd2;margin-top:3px">Vocações</div>
        <div class="ct-bo" style="font-style:italic;font-size:12px;color:#ab9e82;line-height:1.35;text-align:center;margin-top:3px">O que se escolhe ser &#8212; e o que isso custa.</div>
        <span class="ct-bo" style="margin-top:auto;background:rgba(202,162,58,.16);color:#e6c45c;font-size:11.5px;padding:3px 10px;border-radius:8px">$vocacoes_count vocações</span>
      </div>
    </a>

    <a class="ct-n" href="$estrelas_href">
      <svg class="frame" viewBox="0 0 200 182" preserveAspectRatio="none" aria-hidden="true"><path d="M6 178 L6 64 Q42 14 100 8 Q158 14 194 64 L194 178 Z" fill="#181d34" stroke="#c9a23a" stroke-width="1.4" vector-effect="non-scaling-stroke"/></svg>
      <div class="body">
        <div style="height:40px;display:flex;align-items:center">
          <svg viewBox="0 0 44 32" width="42" height="31" aria-hidden="true">
            <line x1="20" y1="15" x2="34" y2="9" stroke="#b8902f" stroke-width=".8" opacity=".5"/><line x1="20" y1="15" x2="8" y2="25" stroke="#b8902f" stroke-width=".8" opacity=".5"/>
            <path d="M20 4 L23.2 12 L31 15 L23.2 18 L20 26 L16.8 18 L9 15 L16.8 12 Z" fill="#f3e7c4" stroke="#c9a23a" stroke-width=".8"/>
            <circle cx="34" cy="9" r="2" fill="#f3e7c4"/><circle cx="8" cy="25" r="1.6" fill="#f3e7c4"/>
          </svg>
        </div>
        <div class="ct-se" style="font-size:17px;color:#f3e7c4;margin-top:3px">Estrelas</div>
        <div class="ct-bo" style="font-style:italic;font-size:12px;color:#a4977c;line-height:1.35;text-align:center;margin-top:3px">Os astros sob os quais se nasce.</div>
        <span class="ct-bo" style="margin-top:auto;background:rgba(202,162,58,.13);color:#e6c45c;font-size:11.5px;padding:3px 10px;border-radius:8px">$estrelas_count signos</span>
      </div>
    </a>

    <a class="ct-n" href="$npcs_href">
      <svg class="frame" viewBox="0 0 200 182" preserveAspectRatio="none" aria-hidden="true"><path d="M6 178 L6 64 Q42 14 100 8 Q158 14 194 64 L194 178 Z" fill="#181d34" stroke="#c9a23a" stroke-width="1.4" vector-effect="non-scaling-stroke"/></svg>
      <div class="body">
        <div style="height:40px;display:flex;align-items:center">
          <svg viewBox="0 0 44 32" width="42" height="31" aria-hidden="true">
            <circle cx="29" cy="12" r="4" fill="#463618" stroke="#c9a23a" stroke-width="1"/><path d="M21 30 Q21 22 29 22 Q37 22 37 30 Z" fill="#463618" stroke="#c9a23a" stroke-width="1"/>
            <circle cx="16" cy="12" r="5" fill="#5a4420" stroke="#c9a23a" stroke-width="1.1"/><path d="M6 30 Q6 21 16 21 Q26 21 26 30 Z" fill="#5a4420" stroke="#c9a23a" stroke-width="1.1"/>
          </svg>
        </div>
        <div class="ct-se" style="font-size:17px;color:#f3e7c4;margin-top:3px">NPCs</div>
        <div class="ct-bo" style="font-style:italic;font-size:12px;color:#a4977c;line-height:1.35;text-align:center;margin-top:3px">Os vivos &#8212; e o que cada um esconde.</div>
        <span class="ct-bo" style="margin-top:auto;background:rgba(202,162,58,.13);color:#e6c45c;font-size:11.5px;padding:3px 10px;border-radius:8px">$npcs_count figuras</span>
      </div>
    </a>

    <a class="ct-n" href="$bestiario_href">
      <svg class="frame" viewBox="0 0 200 182" preserveAspectRatio="none" aria-hidden="true"><path d="M6 178 L6 64 Q42 14 100 8 Q158 14 194 64 L194 178 Z" fill="#181d34" stroke="#c9a23a" stroke-width="1.4" vector-effect="non-scaling-stroke"/></svg>
      <div class="body">
        <div style="height:40px;display:flex;align-items:center">
          <svg viewBox="0 0 44 40" width="38" height="35" aria-hidden="true">
            <ellipse cx="12" cy="15" rx="3.4" ry="5.2" fill="#3a2620" stroke="#c9a23a" stroke-width="1"/><ellipse cx="18.5" cy="10" rx="3.4" ry="5.2" fill="#3a2620" stroke="#c9a23a" stroke-width="1"/><ellipse cx="25.5" cy="10" rx="3.4" ry="5.2" fill="#3a2620" stroke="#c9a23a" stroke-width="1"/><ellipse cx="32" cy="15" rx="3.4" ry="5.2" fill="#3a2620" stroke="#c9a23a" stroke-width="1"/>
            <ellipse cx="22" cy="29" rx="9" ry="7" fill="#3a2620" stroke="#c9a23a" stroke-width="1.1"/>
          </svg>
        </div>
        <div class="ct-se" style="font-size:17px;color:#f3e7c4;margin-top:3px">Bestiário</div>
        <div class="ct-bo" style="font-style:italic;font-size:12px;color:#a4977c;line-height:1.35;text-align:center;margin-top:3px">O que caça nas margens.</div>
        <span class="ct-bo" style="margin-top:auto;background:rgba(202,162,58,.13);color:#e6c45c;font-size:11.5px;padding:3px 10px;border-radius:8px">$bestiario_count criaturas</span>
      </div>
    </a>

    <a class="ct-n" href="$magias_href" style="opacity:.58">
      <svg class="frame" viewBox="0 0 200 182" preserveAspectRatio="none" aria-hidden="true"><path d="M6 178 L6 64 Q42 14 100 8 Q158 14 194 64 L194 178 Z" fill="#101320" stroke="#5a5340" stroke-width="1.2" stroke-dasharray="4 3" vector-effect="non-scaling-stroke"/></svg>
      <div class="body">
        <div style="height:40px;display:flex;align-items:center">
          <svg viewBox="0 0 36 36" width="34" height="34" aria-hidden="true">
            <circle cx="18" cy="18" r="15" fill="none" stroke="#6a6450" stroke-width="1.2"/><path d="M18 32 L6 11 L30 11 Z" fill="#1f1e30" stroke="#6a6450" stroke-width="1"/><circle cx="18" cy="17" r="2.6" fill="#14131f" stroke="#6a6450" stroke-width=".9"/>
          </svg>
        </div>
        <div class="ct-se" style="font-size:17px;color:#8a8270;margin-top:3px">Magias</div>
        <div class="ct-bo" style="font-style:italic;font-size:12px;color:#6f6a58;line-height:1.35;text-align:center;margin-top:3px">O preço de dobrar o mundo.</div>
        <span class="ct-bo" style="margin-top:auto;background:#1c1b2a;color:#8a8270;font-size:11px;padding:3px 10px;border-radius:8px">em obras</span>
      </div>
    </a>

    <a class="ct-n" href="$itens_href" style="opacity:.58">
      <svg class="frame" viewBox="0 0 200 182" preserveAspectRatio="none" aria-hidden="true"><path d="M6 178 L6 64 Q42 14 100 8 Q158 14 194 64 L194 178 Z" fill="#101320" stroke="#5a5340" stroke-width="1.2" stroke-dasharray="4 3" vector-effect="non-scaling-stroke"/></svg>
      <div class="body">
        <div style="height:40px;display:flex;align-items:center">
          <svg viewBox="0 0 24 40" width="22" height="36" aria-hidden="true">
            <path d="M12 3 L15 9 L15 26 L12 30 L9 26 L9 9 Z" fill="#1f1e30" stroke="#6a6450" stroke-width="1.1"/><line x1="5" y1="28" x2="19" y2="28" stroke="#6a6450" stroke-width="2"/><line x1="12" y1="28" x2="12" y2="36" stroke="#6a6450" stroke-width="2"/><circle cx="12" cy="37.5" r="2" fill="none" stroke="#6a6450" stroke-width="1.2"/>
          </svg>
        </div>
        <div class="ct-se" style="font-size:17px;color:#8a8270;margin-top:3px">Itens</div>
        <div class="ct-bo" style="font-style:italic;font-size:12px;color:#6f6a58;line-height:1.35;text-align:center;margin-top:3px">O que se carrega, e o que pesa.</div>
        <span class="ct-bo" style="margin-top:auto;background:#1c1b2a;color:#8a8270;font-size:11px;padding:3px 10px;border-radius:8px">em obras</span>
      </div>
    </a>

  </div>

  <div style="display:flex;align-items:center;justify-content:center;gap:18px;margin-top:1.5rem;flex-wrap:wrap">
    <a href="$jogar_href" class="ct-cta ct-se">
      <svg viewBox="0 0 24 28" width="18" height="21" aria-hidden="true">
        <path d="M4 26 L4 9 Q12 1 20 9 L20 26 Z" fill="none" stroke="#e6c45c" stroke-width="1.6"/>
        <line x1="12" y1="3.4" x2="12" y2="26" stroke="#e6c45c" stroke-width="1.1"/>
        <line x1="4" y1="14" x2="20" y2="14" stroke="#e6c45c" stroke-width=".9"/>
      </svg>
      Entrar no Mundo
    </a>
    <a href="$historias_href" class="ct-link ct-bo">
      <svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true">
        <path d="M6 3 L16 3 Q19 3 19 6 L19 21 L8 21 Q6 21 6 19 Z" fill="none" stroke="currentColor" stroke-width="1.3"/>
        <line x1="9" y1="8"  x2="16" y2="8"  stroke="currentColor" stroke-width="1"/>
        <line x1="9" y1="12" x2="16" y2="12" stroke="currentColor" stroke-width="1"/>
        <line x1="9" y1="16" x2="13" y2="16" stroke="currentColor" stroke-width="1"/>
      </svg>
      Histórias
    </a>
  </div>

  <div style="text-align:center;margin-top:1.25rem">
    <span class="ct-bo" style="font-style:italic;font-size:12px;color:#7e7158;letter-spacing:.03em">Tudo tem nome. Todo nome tem preço.</span>
  </div>

</div>
""")


def render_catedral_html(counts: dict, hrefs: dict) -> str:
    # counts: {'vocacoes','estrelas','npcs','bestiario'} -> int
    # hrefs:  portais + 'jogar' + 'historias' -> str
    return _CATEDRAL_TPL.safe_substitute(
        vocacoes_count=counts.get('vocacoes', '-'),
        estrelas_count=counts.get('estrelas', '-'),
        npcs_count=counts.get('npcs', '-'),
        bestiario_count=counts.get('bestiario', '-'),
        vocacoes_href=hrefs.get('vocacoes', '#'),
        estrelas_href=hrefs.get('estrelas', '#'),
        npcs_href=hrefs.get('npcs', '#'),
        bestiario_href=hrefs.get('bestiario', '#'),
        magias_href=hrefs.get('magias', '#'),
        itens_href=hrefs.get('itens', '#'),
        jogar_href=hrefs.get('jogar', '/jogar'),
        historias_href=hrefs.get('historias', '#'),
    )


@ui.page("/oficina")
async def pagina_oficina_catedral():
    # A Catedral do Alderyn (v6) — landing in-place de /oficina.
    # FIX TIMEOUT NICEGUI: envia placeholder + aguarda WS antes das queries.
    await aguardar_conexao_websocket("Abrindo a Catedral...")

    ui.add_head_html(_VITRAL_HEAD)

    # Reuso dos 4 helpers de contagem que a home ja usava (PC-4),
    # com gather+timeout+fallback pra resiliencia (mesmo padrao da home antiga).
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
        print(f"[catedral] erro ao contar: {e}")
        total_npcs = total_estrelas = total_vocacoes = total_criaturas = 0

    counts = {
        "vocacoes": total_vocacoes,
        "estrelas": total_estrelas,
        "npcs": total_npcs,
        "bestiario": total_criaturas,
    }
    hrefs = {
        "vocacoes": "/oficina/vocacoes",
        "estrelas": "/oficina/estrelas",
        "npcs": "/oficina/npcs",
        "bestiario": "/oficina/bestiario",
        "magias": "#",
        "itens": "#",
        "jogar": "/jogar",
        "historias": "/oficina/historias",
    }

    ui.html(render_catedral_html(counts, hrefs)).classes("w-full")


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


_E_PERG = dict(folha="#fdf1dc", caixa="#f6ead0", pagina="#efe3c9", arte_bg="#efe2c4",
               tijolo="#58180d", regua="#922610", pill="#6e2410", txt="#2a1c0e",
               sec="#5a4632", rodape="#7a6648")
_E_SERIF = "'Cinzel',serif"
_E_BODY = "'Crimson Text',Georgia,serif"
_ABRE = chr(0x201c)   # aspa curva abre
_FECHA = chr(0x201d)  # aspa curva fecha

def _ee(s):
    return html.escape(str(s)) if s is not None else ""

def _estrela_barra_html(p1, p2, p3, *, escuro: bool) -> str:
    if escuro:
        c1, c2, c3 = "#b8902f", "#8a6d24", "#5a4a20"
        rotulo = "#9a8a5a"
    else:
        P = _E_PERG
        c1, c2, c3 = P["regua"], "#b5754a", "#cda37a"
        rotulo = P["sec"]
    return (
        f'<div style="display:flex;height:8px;border-radius:4px;overflow:hidden;margin-top:4px;">'
        f'<div style="width:{p1}%;background:{c1};"></div>'
        f'<div style="width:{p2}%;background:{c2};"></div>'
        f'<div style="width:{p3}%;background:{c3};"></div></div>'
        f'<div style="display:flex;justify-content:space-between;font-family:{_E_SERIF};font-size:10px;'
        f'letter-spacing:.04em;color:{rotulo};margin-top:3px;">'
        f'<span>Raras {p1}%</span><span>Médias {p2}%</span><span>Comuns {p3}%</span></div>'
    )

CONSTELACOES = {
    1: {  # MARKA - A Forja - bigorna
        "pts": [(28,32,'m'),(50,30,'a'),(74,35,'m'),(50,50,'p'),(34,70,'m'),(66,70,'m'),(50,77,'p')],
        "linhas": [(0,1),(1,2),(1,3),(3,4),(3,5),(4,6),(6,5)],
    },
    2: {  # LIRETH - A Mare - onda em S
        "pts": [(24,34,'m'),(44,27,'p'),(55,45,'a'),(45,62,'p'),(60,76,'p'),(80,68,'m')],
        "linhas": [(0,1),(1,2),(2,3),(3,4),(4,5)],
    },
    3: {  # VORN - A Sombra - fragmentada, um ponto solto (ausencia)
        "pts": [(26,30,'p'),(62,28,'p'),(46,52,'m'),(70,68,'p'),(34,72,'p')],
        "linhas": [(0,2),(2,3),(2,4)],
    },
    4: {  # THESSAR - O Fogo Vivo - chama subindo, duas linguas
        "pts": [(38,80,'m'),(62,80,'m'),(42,62,'p'),(58,56,'p'),(46,40,'p'),(56,30,'m'),(50,17,'a')],
        "linhas": [(0,1),(0,2),(2,4),(4,5),(5,6),(1,3),(3,4)],
    },
    5: {  # AUREN - A Raiz - tronco central + raizes
        "pts": [(50,18,'m'),(50,42,'a'),(50,60,'p'),(30,76,'m'),(42,82,'p'),(60,82,'p'),(72,74,'m')],
        "linhas": [(0,1),(1,2),(2,3),(2,4),(2,5),(2,6)],
    },
    6: {  # CALDRIS - O Gelo - cristal hexagonal simetrico
        "pts": [(50,20,'m'),(76,35,'p'),(76,65,'p'),(50,80,'m'),(24,65,'p'),(24,35,'p')],
        "linhas": [(0,1),(1,2),(2,3),(3,4),(4,5),(5,0)],
    },
    7: {  # MIREHN - O Limiar - portal (2 pilares + verga)
        "pts": [(32,24,'m'),(50,20,'a'),(68,24,'m'),(32,52,'p'),(32,80,'p'),(68,80,'p')],
        "linhas": [(0,1),(1,2),(0,3),(3,4),(2,5)],
    },
    8: {  # DORRAS - A Tempestade - raio em ziguezague
        "pts": [(42,16,'m'),(62,33,'p'),(40,45,'a'),(62,57,'p'),(40,67,'p'),(60,79,'p'),(46,88,'m')],
        "linhas": [(0,1),(1,2),(2,3),(3,4),(4,5),(5,6)],
    },
    9: {  # SAEL - O Cantor - arco de som (curva)
        "pts": [(24,64,'m'),(33,46,'p'),(46,35,'p'),(58,33,'a'),(70,40,'p'),(78,56,'m')],
        "linhas": [(0,1),(1,2),(2,3),(3,4),(4,5)],
    },
    10: {  # VRETH - A Besta - cranio de fera (chifres + face triangular)
        "pts": [(24,42,'m'),(36,26,'p'),(50,34,'a'),(64,26,'p'),(76,42,'m'),(50,60,'m')],
        "linhas": [(0,1),(1,2),(2,3),(3,4),(1,5),(4,5)],
    },
    11: {  # ILUVEN - O Veu - olho (amendoa + pupila central isolada)
        "pts": [(24,50,'m'),(40,38,'p'),(58,38,'p'),(76,50,'m'),(58,62,'p'),(40,62,'p'),(50,50,'a')],
        "linhas": [(0,1),(1,2),(2,3),(3,4),(4,5),(5,0)],
    },
    12: {  # ORRATH - O Trono - coroa (base + 5 pontas)
        "pts": [(30,62,'m'),(70,62,'m'),(30,44,'p'),(43,36,'p'),(50,28,'a'),(57,36,'p'),(70,44,'p')],
        "linhas": [(0,1),(0,2),(2,3),(3,4),(4,5),(5,6),(6,1)],
    },
}

_C_TIER = {'a': (4.4, 0.22, 2.1), 'm': (2.9, 0.18, 1.45), 'p': (0.0, 0.0, 1.0)}

def _constelacao_svg(eid: int, px: int = 150, pergaminho: bool = False) -> str:
    c = CONSTELACOES.get(eid)
    if not c:
        # fallback neutro: placa de ceu vazia (estrela sem forma definida)
        moldura = ('stroke="#58180d" stroke-width="0.8" stroke-opacity="0.55"' if pergaminho
                   else 'stroke="#caa23a" stroke-width="0.5" stroke-opacity="0.22"')
        return (f'<svg viewBox="0 0 100 100" width="{px}" height="{px}" xmlns="http://www.w3.org/2000/svg">'
                f'<rect x="0" y="0" width="100" height="100" rx="7" fill="#11151f"/>'
                f'<rect x="0.6" y="0.6" width="98.8" height="98.8" rx="6.6" fill="none" {moldura}/></svg>')
    pts = c["pts"]
    linhas = ""
    for i, j in c["linhas"]:
        x1, y1, _ = pts[i]
        x2, y2, _ = pts[j]
        linhas += (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                   f'stroke="#b8902f" stroke-width="0.5" stroke-opacity="0.30"/>')
    estrelas = ""
    for (x, y, t) in pts:
        hr, ho, nr = _C_TIER[t]
        if hr > 0:
            estrelas += f'<circle cx="{x}" cy="{y}" r="{hr}" fill="#d8b24a" fill-opacity="{ho}"/>'
        estrelas += f'<circle cx="{x}" cy="{y}" r="{nr}" fill="#f3e7c4"/>'
    moldura = ('stroke="#58180d" stroke-width="0.8" stroke-opacity="0.55"' if pergaminho
               else 'stroke="#caa23a" stroke-width="0.5" stroke-opacity="0.22"')
    return (
        f'<svg viewBox="0 0 100 100" width="{px}" height="{px}" xmlns="http://www.w3.org/2000/svg">'
        f'<defs><radialGradient id="ceu{eid}" cx="50%" cy="42%" r="72%">'
        f'<stop offset="0%" stop-color="#222c49"/>'
        f'<stop offset="62%" stop-color="#141a2e"/>'
        f'<stop offset="100%" stop-color="#080b14"/>'
        f'</radialGradient></defs>'
        f'<rect x="0" y="0" width="100" height="100" rx="7" fill="url(#ceu{eid})"/>'
        f'<rect x="0.6" y="0.6" width="98.8" height="98.8" rx="6.6" fill="none" {moldura}/>'
        f'{linhas}{estrelas}</svg>'
    )


def _card_estrela_html(e: dict) -> str:
    cor = "#b8902f"
    barra = _estrela_barra_html(e["pct_1"], e["pct_2"], e["pct_3"], escuro=True)
    return (
        f'<a href="/oficina/estrelas/{e["id"]}" class="criatura-card" '
        'style="display:block;text-decoration:none;padding:16px 18px;">'
        f'<div style="display:flex;justify-content:center;margin-bottom:12px;">'
        f'{_constelacao_svg(e["id"], px=132)}</div>'
        f'<div style="font-family:\'IM Fell English\',serif;font-size:23px;color:#f3e7c4;line-height:1.1;">{_ee(e["nome"])}</div>'
        f'<div style="font-family:\'IM Fell English SC\',serif;font-size:11px;letter-spacing:.1em;color:{cor};margin-top:4px;">{_ee(e["epiteto"])}</div>'
        f'<div style="font-family:\'Spectral\',Georgia,serif;font-style:italic;font-size:13px;color:#c0a36a;margin-top:10px;line-height:1.5;">“{_ee(e["lema"])}”</div>'
        f'<div style="font-family:\'IM Fell English SC\',serif;font-size:11px;letter-spacing:.08em;color:#9a8a5a;margin-top:10px;">{_ee(e["atributos"])}</div>'
        f'<div style="margin-top:12px;">{barra}</div>'
        f'<div style="border-top:1px solid #2a2418;margin-top:14px;padding-top:10px;">'
        f'<div style="font-family:\'IM Fell English SC\',serif;font-size:10px;letter-spacing:.1em;color:#7a6f55;">LENDÁRIA &middot; d100=100</div>'
        f'<div style="font-family:\'Spectral\',Georgia,serif;font-style:italic;font-size:14px;color:{cor};margin-top:2px;">{_ee(e["lendaria"])}</div>'
        '</div></a>'
    )

def _hab_estrela_html(h: dict) -> str:
    P = _E_PERG
    lend = h.get("lendaria")
    preco = h.get("tem_preco")
    borda = f'2px solid {P["regua"]}' if lend else f'1px solid {P["regua"]}'
    pills = (f'<span style="font-family:{_E_SERIF};font-size:11px;color:#fdf1dc;background:{P["pill"]};'
             f'border-radius:3px;padding:1px 7px;">d{h["d100"]:02d}</span>')
    if preco:
        pills += (f' <span style="font-family:{_E_SERIF};font-size:10px;color:{P["pill"]};border:1px solid {P["pill"]};'
                  f'border-radius:3px;padding:1px 7px;">COBRA PREÇO</span>')
    if lend:
        pills += (f' <span style="font-family:{_E_SERIF};font-size:10px;color:#fdf1dc;background:{P["tijolo"]};'
                  f'border-radius:3px;padding:1px 7px;">LENDÁRIA</span>')
    nome_cor = P["tijolo"]
    return _e_card(
        f'<div style="display:flex;align-items:center;gap:7px;flex-wrap:wrap;">'
        f'{pills}<span style="font-family:{_E_SERIF};font-weight:700;font-size:15px;color:{nome_cor};">{_ee(h["nome"])}</span></div>'
        f'<div style="font-family:{_E_BODY};font-size:14px;color:{P["txt"]};line-height:1.6;white-space:pre-line;margin-top:5px;">{_ee(h["descricao"])}</div>'
    )

def _e_card(corpo):
    P = _E_PERG
    return f'<div style="background:{P["caixa"]};border:1px solid {P["regua"]};border-radius:5px;padding:12px 15px;margin-bottom:9px;">{corpo}</div>'


@ui.page("/oficina/estrelas")
async def pagina_estrelas():
    """Galeria vitral das 12 estrelas do Veu."""
    await aguardar_conexao_websocket("Catalogando estrelas do Véu...")
    ui.add_head_html(CSS_VITRAL)
    barra_nav("estrelas")

    estrelas = await _buscar_estrelas()
    cards = "".join(_card_estrela_html(e) for e in estrelas)
    grade = '<div class="gp-grid">' + cards + '</div>'

    with ui.column().classes("gp-screen w-full min-h-screen p-0 gap-0"):
        with ui.column().classes("gp-inner w-full gap-4"):
            ui.html(
                '<div style="font-family:\'IM Fell English\',serif;font-size:34px;color:#f3e7c4;line-height:1.1;">Estrelas do Véu</div>'
                f'<div style="font-family:\'IM Fell English SC\',serif;font-size:12px;letter-spacing:.14em;color:#9a8a5a;margin-top:6px;">'
                f'{len(estrelas)} ASTROS SOB OS QUAIS SE NASCE</div>'
            )
            ui.html(grade).classes("w-full")



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

    ui.add_head_html(CSS_PERGAMINHO)

    if not estrela:
        with ui.column().classes(
            "w-full min-h-screen items-center justify-center gap-4 p-8"
        ).style("background:#efe3c9;color:#2a1c0e;"):
            ui.html(
                '<div style="font-family:\'Cinzel\',serif;font-size:22px;color:#58180d;">'
                'Estrela não encontrada.</div>'
            )
            ui.button(
                "Voltar", on_click=lambda: ui.navigate.to("/oficina/estrelas")
            ).props("flat color=brown-8")
        return

    habs_por_cat = await _buscar_habilidades_estrela(estrela_id)
    P = _E_PERG
    cat_meta = {1: "Raras", 2: "Médias", 3: "Comuns"}

    placa_det = _constelacao_svg(estrela["id"], px=120, pergaminho=True)
    barra = _estrela_barra_html(
        estrela["pct_1"], estrela["pct_2"], estrela["pct_3"], escuro=False
    )
    cabecalho = (
        f'<div style="background:{P["caixa"]};border:1px solid {P["regua"]};border-radius:6px;'
        f'padding:22px 26px;display:flex;gap:22px;align-items:flex-start;flex-wrap:wrap;">'
        f'<div style="flex:0 0 auto;">{placa_det}</div>'
        f'<div style="flex:1 1 240px;min-width:240px;">'
        f'<div style="font-family:{_E_SERIF};font-weight:700;font-size:34px;color:{P["tijolo"]};line-height:1.05;">{_ee(estrela["nome"])}</div>'
        f'<div style="font-family:{_E_BODY};font-style:italic;font-size:16px;color:{P["sec"]};margin-top:3px;">{_ee(estrela["epiteto"])}</div>'
        f'<div style="font-family:{_E_BODY};font-style:italic;font-size:15px;color:{P["txt"]};margin-top:10px;">{_ABRE}{_ee(estrela["lema"])}{_FECHA}</div>'
        f'<div style="font-family:{_E_SERIF};font-size:12px;letter-spacing:.08em;color:{P["pill"]};margin-top:14px;">{_ee(estrela["atributos"])}</div>'
        f'<div style="max-width:420px;margin-top:10px;">{barra}</div>'
        f'</div></div>'
    )

    secoes = ""
    for cat in (1, 2, 3):
        habs = habs_por_cat.get(cat, [])
        n = len(habs)
        if habs:
            corpo = "".join(_hab_estrela_html(h) for h in habs)
        else:
            corpo = (
                f'<div style="font-family:{_E_BODY};font-style:italic;'
                f'color:{P["sec"]};">Nenhuma habilidade nesta categoria.</div>'
            )
        aberto = " open" if cat <= 2 else ""
        secoes += (
            f'<details{aberto} style="margin-top:18px;">'
            f'<summary style="font-family:{_E_SERIF};font-size:13px;'
            f'letter-spacing:.12em;color:{P["tijolo"]};'
            f'border-bottom:2px solid {P["regua"]};padding-bottom:5px;'
            f'margin-bottom:12px;cursor:pointer;">'
            f'CATEGORIA {cat} — {cat_meta[cat].upper()} '
            f'({n} HABILIDADES)</summary>{corpo}</details>'
        )

    with ui.column().classes("w-full min-h-screen p-0 gap-0").style(
        "background:#efe3c9;color:#2a1c0e;"
    ):
        with ui.column().classes(
            "w-full max-w-4xl mx-auto px-6 py-8 gap-3"
        ).style("box-sizing:border-box;"):
            ui.html(
                '<a href="/oficina/estrelas" style="text-decoration:none;'
                'font-family:\'Cinzel\',serif;font-size:12px;'
                'letter-spacing:.12em;color:#7a6648;">‹ ESTRELAS DO VÉU</a>'
            )
            ui.html(cabecalho).classes("w-full")
            ui.html(secoes).classes("w-full")



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


_COR_PILAR = {
    "corpo": "#c0653f", "sombra": "#9b7fc0", "arcano": "#4f86c6",
    "espirito": "#5aa882", "engenho": "#c9a23a",
}

_NOME_PILAR = {
    "corpo": "Corpo", "sombra": "Sombra", "arcano": "Arcano",
    "espirito": "Espírito", "engenho": "Engenho",
}
_ESSENCIA_PILAR = {
    "corpo": "A Carne", "sombra": "O Silêncio", "arcano": "A Palavra",
    "espirito": "O Pacto", "engenho": "A Construção",
}
_GLIFO_PILAR = {
    "corpo": '''<svg viewBox="0 0 100 100" width="100%" height="100%" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><path d="M50 16 Q45 38 50 50 Q55 62 50 84"/><path d="M39 27 L61 31" stroke-width="2.5"/><path d="M39 43 L61 45" stroke-width="2.5"/><path d="M40 59 L60 61" stroke-width="2.5"/><path d="M42 73 L58 73" stroke-width="2.5"/></svg>''',
    "sombra": '''<svg viewBox="0 0 100 100" width="100%" height="100%" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"><path d="M50 14 L41 44 L50 52 L59 44 Z"/><path d="M44 58 L50 64 L56 58" opacity="0.7"/><path d="M45 70 L50 75 L55 70" opacity="0.45"/><path d="M47 82 L50 86 L53 82" opacity="0.25"/></svg>''',
    "arcano": '''<svg viewBox="0 0 100 100" width="100%" height="100%" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="50" cy="50" r="36"/><path d="M50 20 L50 80"/><path d="M50 38 L67 28"/><path d="M50 52 L33 42"/><path d="M50 64 L67 55"/></svg>''',
    "espirito": '''<svg viewBox="0 0 100 100" width="100%" height="100%" fill="none" stroke="currentColor"><circle cx="50" cy="50" r="7" fill="currentColor"/><circle cx="50" cy="50" r="19" stroke-width="3"/><circle cx="50" cy="50" r="31" stroke-width="2.5" opacity="0.65"/><circle cx="50" cy="50" r="43" stroke-width="2" opacity="0.35"/></svg>''',
    "engenho": '''<svg viewBox="0 0 100 100" width="100%" height="100%" fill="none" stroke="currentColor" stroke-width="3"><circle cx="50" cy="50" r="22"/><circle cx="50" cy="50" r="7"/><g stroke-width="4" stroke-linecap="round"><path d="M50 14 L50 21"/><path d="M50 79 L50 86"/><path d="M14 50 L21 50"/><path d="M79 50 L86 50"/><path d="M25 25 L30 30"/><path d="M70 70 L75 75"/><path d="M75 25 L70 30"/><path d="M30 70 L25 75"/></g></svg>''',
}

def _cabecalho_pilar_html(cor, nome, essencia, epiteto, filosofia, glifo):
    return (
        f'<div style="position:relative;overflow:hidden;border:1px solid {cor};'
        f'border-left:4px solid {cor};border-radius:6px;padding:22px 26px;'
        'background:rgba(12,14,22,.55);">'
        f'<div style="position:absolute;right:-24px;top:50%;transform:translateY(-50%);'
        f'width:240px;height:240px;color:{cor};opacity:.06;pointer-events:none;">{glifo}</div>'
        '<div style="position:relative;display:flex;gap:20px;align-items:flex-start;">'
        f'<div style="flex:none;width:62px;height:62px;color:{cor};margin-top:4px;">{glifo}</div>'
        '<div style="flex:1;min-width:0;">'
        f'<div style="font-family:\'IM Fell English\',serif;font-size:34px;color:{cor};line-height:1;">{html.escape(nome)}</div>'
        f'<div style="font-family:\'IM Fell English SC\',serif;font-size:13px;letter-spacing:.18em;color:#c0a36a;margin-top:5px;">{html.escape(essencia.upper())}</div>'
        f'<div style="font-family:\'Spectral\',Georgia,serif;font-style:italic;font-size:15px;color:#9a8a5a;margin-top:12px;">{html.escape(epiteto)}</div>'
        f'<div style="font-family:\'Spectral\',Georgia,serif;font-size:14px;color:#c0a36a;line-height:1.65;margin-top:10px;max-width:780px;">{html.escape(filosofia)}</div>'
        '</div></div></div>'
    )

_ORDEM_PILARES = ["corpo", "sombra", "arcano", "espirito", "engenho"]

def _card_pilar_html(slug, cor, nome, essencia, epiteto, n):
    glifo = _GLIFO_PILAR.get(slug, "")
    plural = "vocação" if n == 1 else "vocações"
    return (
        f'<a href="/oficina/vocacoes/pilar/{slug}" class="portal-pilar" '
        'style="position:relative;display:block;text-decoration:none;overflow:hidden;'
        f'border:1px solid {cor};border-left:4px solid {cor};border-radius:6px;'
        'padding:26px 24px 22px;background:rgba(12,14,22,.55);min-height:232px;">'
        f'<div style="position:absolute;right:-20px;bottom:-20px;width:150px;height:150px;'
        f'color:{cor};opacity:.06;pointer-events:none;">{glifo}</div>'
        f'<div style="position:relative;width:54px;height:54px;color:{cor};">{glifo}</div>'
        f'<div style="position:relative;font-family:\'IM Fell English\',serif;font-size:30px;'
        f'color:{cor};line-height:1;margin-top:14px;">{html.escape(nome)}</div>'
        f'<div style="position:relative;font-family:\'IM Fell English SC\',serif;font-size:12px;'
        f'letter-spacing:.18em;color:#c0a36a;margin-top:6px;">{html.escape(essencia.upper())}</div>'
        f'<div style="position:relative;font-family:\'Spectral\',Georgia,serif;font-style:italic;'
        f'font-size:14px;color:#9a8a5a;margin-top:12px;line-height:1.5;">{html.escape(epiteto)}</div>'
        f'<div style="position:relative;font-family:\'IM Fell English SC\',serif;font-size:11px;'
        f'letter-spacing:.12em;color:#7a6f55;margin-top:14px;">{n} {plural}</div>'
        '</a>'
    )

async def _buscar_todas_vocacoes() -> list[dict]:
    async with get_session() as session:
        result = await session.exec(
            select(RefVocacoes).order_by(RefVocacoes.nome_ptbr.asc())
        )
        vocs = result.all()
    out = []
    for v in vocs:
        out.append({
            "id": v.id,
            "nome": v.nome_ptbr or "?",
            "pilar": v.pilar or "",
            "tipo": v.tipo or "",
            "atribs": "/".join(v.atributos_primarios) if v.atributos_primarios else "",
            "disponivel": bool(v.disponivel_escolha),
            "imagem_url": v.imagem_url,
        })
    return out

def _card_vocacao_html(v: dict) -> str:
    cor = _COR_PILAR.get(v["pilar"], "#b8902f")
    pilar_txt = html.escape(v["pilar"].upper()) if v["pilar"] else "—"
    nome = html.escape(v["nome"])
    linha2 = " · ".join(p for p in [html.escape(v["tipo"]) if v["tipo"] else "",
                                    html.escape(v["atribs"]) if v["atribs"] else ""] if p)
    corpo2 = (f'<div class="bestiario-body" style="font-size:13px;margin-top:4px;">{linha2}</div>'
              if linha2 else "")
    selo = "" if v["disponivel"] else (
        "<span style=\"position:absolute;top:8px;right:8px;z-index:2;font-family:'IM Fell English SC',serif;"
        'font-size:9px;letter-spacing:.1em;color:#cdbfa6;background:rgba(10,10,14,.78);'
        'border:1px solid #6a6052;border-radius:3px;padding:2px 7px;">bloqueada</span>'
    )
    url = (v.get("imagem_url") or "").strip()
    if url:
        arte_img = (
            f'<img src="{html.escape(url, quote=True)}" alt="" '
            "onerror=\"this.style.display='none'\" "
            'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block;z-index:1;">'
        )
    else:
        arte_img = ""
    arte = (
        '<div style="position:relative;width:100%;aspect-ratio:3/4;overflow:hidden;'
        f'background:linear-gradient(160deg,#1a1d2a,#0e1018);border-bottom:1px solid {cor};">'
        f'{selo}'
        '<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;'
        "font-family:'IM Fell English',serif;font-style:italic;font-size:12px;color:#5a5440;"
        'text-align:center;padding:14px;">arte a gerar</div>'
        f'{arte_img}'
        '</div>'
    )
    return (
        f'<a href="/oficina/vocacoes/{v["id"]}" class="criatura-card" '
        'style="position:relative;display:block;text-decoration:none;overflow:hidden;">'
        f'{arte}'
        '<div style="padding:12px 14px 14px;">'
        f'<div class="bestiario-title" style="font-size:17px;line-height:1.1;">{nome}</div>'
        "<div style=\"font-family:'IM Fell English SC',serif;font-size:10px;letter-spacing:.12em;"
        f'color:{cor};margin-top:4px;">{pilar_txt}</div>'
        f'{corpo2}'
        '</div></a>'
    )

def _grade_vocacoes_html(lista: list[dict]) -> str:
    if not lista:
        return ('<div style="text-align:center;font-style:italic;color:#7a6f55;'
                'padding:50px 0;">Nenhuma vocação encontrada.</div>')
    return '<div class="gp-grid">' + "".join(_card_vocacao_html(v) for v in lista) + '</div>'


@ui.page("/oficina/vocacoes")
async def pagina_vocacoes_hub():
    """Hub: os 5 pilares como portais, cada um leva ao seu salao."""
    await aguardar_conexao_websocket("Abrindo a catedral...")
    ui.add_head_html(CSS_VITRAL)
    ui.add_head_html(
        "<style>.portal-pilar{transition:transform .15s ease;}"
        ".portal-pilar:hover{transform:translateY(-3px);}</style>"
    )
    barra_nav("vocacoes")

    todas = await _buscar_todas_vocacoes()
    contagem = {}
    for v in todas:
        contagem[v["pilar"]] = contagem.get(v["pilar"], 0) + 1
    total = len(todas)

    cards = []
    for slug in _ORDEM_PILARES:
        cor = _COR_PILAR.get(slug, "#b8902f")
        nome = _NOME_PILAR.get(slug, slug)
        essencia = _ESSENCIA_PILAR.get(slug, "")
        fil = await _buscar_filosofia_pilar(slug) or {}
        epiteto = fil.get("epiteto", "") or ""
        n = contagem.get(slug, 0)
        cards.append(_card_pilar_html(slug, cor, nome, essencia, epiteto, n))

    grade_html = (
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));'
        'gap:16px;width:100%;">' + "".join(cards) + "</div>"
    )

    with ui.column().classes("gp-screen w-full min-h-screen p-0 gap-0"):
        with ui.column().classes("gp-inner w-full gap-4"):
            ui.html(
                '<div style="font-family:\'IM Fell English\',serif;font-size:34px;'
                'color:#f3e7c4;line-height:1.1;">Vocações do Alderyn</div>'
                '<div style="font-family:\'IM Fell English SC\',serif;font-size:12px;'
                f'letter-spacing:.14em;color:#9a8a5a;margin-top:6px;">{total} VOCAÇÕES &middot; CINCO PILARES</div>'
            )
            ui.html(grade_html).classes("w-full")


async def _galeria_plana_orfa():
    """Galeria vitral das vocacoes do Alderyn, com filtros em memoria. (orfa - sem rota)"""
    await aguardar_conexao_websocket("Catalogando vocações...")
    ui.add_head_html(CSS_VITRAL)
    barra_nav("vocacoes")

    todas = await _buscar_todas_vocacoes()
    total = len(todas)
    estado = {"pilar": "todos", "tipo": "todos", "disp": "todos", "busca": ""}
    grade_ref = {"el": None}
    contador_ref = {"el": None}
    refs = {"filosofia": None}

    def filtrar() -> list[dict]:
        out = todas
        if estado["pilar"] != "todos":
            out = [v for v in out if v["pilar"] == estado["pilar"]]
        if estado["tipo"] != "todos":
            out = [v for v in out if v["tipo"] == estado["tipo"]]
        if estado["disp"] == "disponiveis":
            out = [v for v in out if v["disponivel"]]
        elif estado["disp"] == "bloqueadas":
            out = [v for v in out if not v["disponivel"]]
        if estado["busca"]:
            q = estado["busca"].lower()
            out = [v for v in out if q in v["nome"].lower()]
        return out

    def re_render():
        filtrados = filtrar()
        if grade_ref["el"]:
            grade_ref["el"].set_content(_grade_vocacoes_html(filtrados))
        if contador_ref["el"]:
            contador_ref["el"].set_text(f"{len(filtrados)} de {total} vocações")

    async def atualizar_filosofia():
        cont = refs["filosofia"]
        if cont is None:
            return
        cont.clear()
        nome = estado["pilar"]
        if nome not in ("corpo", "sombra", "arcano", "espirito", "engenho"):
            return
        data = await _buscar_filosofia_pilar(nome)
        if not data:
            return
        cor = _COR_PILAR.get(nome, "#b8902f")
        with cont:
            ui.html(
                f'<div style="background:rgba(12,14,22,.6);border:1px solid {cor};'
                f'border-left:3px solid {cor};border-radius:5px;padding:14px 18px;">'
                "<div style=\"font-family:'IM Fell English',serif;font-size:18px;"
                f'color:{cor};letter-spacing:.05em;">{html.escape((data["nome"] or "").upper())}'
                '<span style="font-style:italic;font-size:13px;color:#9a8a5a;margin-left:10px;">'
                f'{html.escape(data["epiteto"] or "")}</span></div>'
                "<div style=\"font-family:'Spectral',Georgia,serif;font-style:italic;"
                'color:#c0a36a;font-size:14px;line-height:1.6;margin-top:8px;">'
                f'{html.escape(data["filosofia"] or "")}</div></div>'
            )

    def set_pilar(v):
        estado["pilar"] = v
        re_render()
        asyncio.create_task(atualizar_filosofia())

    def set_tipo(v):
        estado["tipo"] = v
        re_render()

    def set_disp(v):
        estado["disp"] = v
        re_render()

    def set_busca(e):
        estado["busca"] = (e.value or "").strip()
        re_render()

    with ui.column().classes("gp-screen w-full min-h-screen p-0 gap-0"):
        with ui.column().classes("gp-inner w-full gap-4"):
            with ui.row().classes("w-full items-center gap-3"):
                ui.button(icon="arrow_back",
                          on_click=lambda: ui.navigate.to("/oficina")
                          ).props("flat round dense color=amber-2")
                with ui.column().classes("gap-0"):
                    ui.label("Vocações do Alderyn").classes("bestiario-title").style("font-size:30px;")
                    contador_ref["el"] = ui.label(f"{total} de {total} vocações").classes(
                        "bestiario-body").style("font-style:italic;font-size:13px;")
            ui.html('<div class="gp-rule"></div>')

            with ui.row().classes("gp-filtros w-full items-center gap-3 flex-wrap").style("padding:12px 14px;"):
                ui.input(placeholder="Buscar por nome...", on_change=set_busca
                         ).props("dense outlined dark clearable").style("min-width:240px;")
                ui.select({"todos": "Todos os pilares", "corpo": "Corpo", "sombra": "Sombra",
                           "arcano": "Arcano", "espirito": "Espírito", "engenho": "Engenho"},
                          value="todos", on_change=lambda e: set_pilar(e.value)
                          ).props("dense outlined dark").style("min-width:170px;")
                ui.select({"todos": "Todos os tipos", "base": "Base", "fusao": "Fusão",
                           "cross": "Cross", "especial": "Especial"},
                          value="todos", on_change=lambda e: set_tipo(e.value)
                          ).props("dense outlined dark").style("min-width:160px;")
                ui.select({"todos": "Todas", "disponiveis": "Disponíveis", "bloqueadas": "Bloqueadas"},
                          value="todos", on_change=lambda e: set_disp(e.value)
                          ).props("dense outlined dark").style("min-width:150px;")

            refs["filosofia"] = ui.column().classes("w-full")
            grade_ref["el"] = ui.html(_grade_vocacoes_html(todas)).classes("w-full")


@ui.page("/oficina/vocacoes/pilar/{slug}")
async def pagina_vocacoes_pilar(slug: str):
    """Salao de um pilar: filosofia + galeria so das vocacoes daquele pilar."""
    await aguardar_conexao_websocket("Abrindo o salão...")
    ui.add_head_html(CSS_VITRAL)
    barra_nav("vocacoes")
    slug = (slug or "").lower().strip()

    if slug not in _NOME_PILAR:
        with ui.column().classes("gp-screen w-full min-h-screen p-0 gap-0"):
            with ui.column().classes("gp-inner w-full gap-4"):
                ui.label("Pilar desconhecido.").classes("bestiario-title").style("font-size:22px;")
                ui.button("Voltar aos pilares",
                          on_click=lambda: ui.navigate.to("/oficina/vocacoes")
                          ).props("flat color=amber-2")
        return

    cor = _COR_PILAR.get(slug, "#b8902f")
    nome = _NOME_PILAR[slug]
    essencia = _ESSENCIA_PILAR[slug]
    glifo = _GLIFO_PILAR[slug]
    fil = await _buscar_filosofia_pilar(slug) or {}
    epiteto = fil.get("epiteto", "") or ""
    filosofia = fil.get("filosofia", "") or ""

    todas = await _buscar_todas_vocacoes()
    desta = [v for v in todas if v["pilar"] == slug]
    total = len(desta)

    estado = {"tipo": "todos", "disp": "todos", "busca": ""}
    grade_ref = {"el": None}
    contador_ref = {"el": None}

    def filtrar():
        out = desta
        if estado["tipo"] != "todos":
            out = [v for v in out if v["tipo"] == estado["tipo"]]
        if estado["disp"] == "disponiveis":
            out = [v for v in out if v["disponivel"]]
        elif estado["disp"] == "bloqueadas":
            out = [v for v in out if not v["disponivel"]]
        if estado["busca"]:
            q = estado["busca"].lower()
            out = [v for v in out if q in v["nome"].lower()]
        return out

    def re_render():
        f = filtrar()
        if grade_ref["el"]:
            grade_ref["el"].set_content(_grade_vocacoes_html(f))
        if contador_ref["el"]:
            contador_ref["el"].set_text(f"{len(f)} de {total} vocações")

    def set_tipo(v):
        estado["tipo"] = v
        re_render()

    def set_disp(v):
        estado["disp"] = v
        re_render()

    def set_busca(e):
        estado["busca"] = (e.value or "").strip()
        re_render()

    with ui.column().classes("gp-screen w-full min-h-screen p-0 gap-0"):
        with ui.column().classes("gp-inner w-full gap-4"):
            ui.html(
                '<a href="/oficina/vocacoes" style="text-decoration:none;'
                "font-family:'IM Fell English SC',serif;font-size:12px;letter-spacing:.12em;"
                'color:#9a8a5a;">&lsaquo; CATEDRAL &middot; TODOS OS PILARES</a>'
            )
            ui.html(_cabecalho_pilar_html(cor, nome, essencia, epiteto, filosofia, glifo))

            with ui.row().classes("gp-filtros w-full items-center gap-3 flex-wrap").style("padding:12px 14px;"):
                ui.input(placeholder="Buscar por nome...", on_change=set_busca
                         ).props("dense outlined dark clearable").style("min-width:240px;")
                ui.select({"todos": "Todos os tipos", "base": "Base", "fusao": "Fusão",
                           "cross": "Cross", "especial": "Especial"},
                          value="todos", on_change=lambda e: set_tipo(e.value)
                          ).props("dense outlined dark").style("min-width:160px;")
                ui.select({"todos": "Todas", "disponiveis": "Disponíveis", "bloqueadas": "Bloqueadas"},
                          value="todos", on_change=lambda e: set_disp(e.value)
                          ).props("dense outlined dark").style("min-width:150px;")
                contador_ref["el"] = ui.label(f"{total} de {total} vocações").classes(
                    "bestiario-body").style("font-style:italic;font-size:13px;margin-left:auto;")

            grade_ref["el"] = ui.html(_grade_vocacoes_html(desta)).classes("w-full")


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
        "imagem_url": voc.imagem_url,
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


def _ficha_vocacao_html(data: dict) -> str:
    FOLHA = "#fdf1dc"; CAIXA = "#f6ead0"; PAGINA = "#efe3c9"
    ARTE_BG = "#efe2c4"; TIJOLO = "#58180d"; REGUA = "#922610"
    PILL = "#6e2410"; TXT = "#2a1c0e"; SEC = "#5a4632"
    serif = "'Cinzel',serif"
    body = "'Crimson Text',Georgia,serif"
    e = lambda s: html.escape(str(s)) if s is not None else ""

    nome = e(data["nome"])
    nome_en = data.get("nome_en") or ""
    mostra_en = bool(nome_en) and nome_en != data["nome"]
    pilar = data["pilar"] or ""
    conceitual = pilar in ("corpo", "sombra", "arcano", "espirito", "engenho")

    meta = [f'Pilar {e(pilar)}' if conceitual else f'⚠ {e(pilar)}']
    if data.get("tipo"):
        meta.append(e(data["tipo"]))
    if data.get("atributos"):
        meta.append(e(" / ".join(data["atributos"])))
    meta_txt = "  ·  ".join(meta)

    bloqueada = ""
    if data.get("disponivel") is False:
        bloqueada = (f'<span style="font-family:{serif};font-size:11px;letter-spacing:.1em;'
                     f'color:#fdf1dc;background:{PILL};border-radius:3px;padding:3px 9px;margin-left:10px;">BLOQUEADA</span>')

    url = (data.get("imagem_url") or "").strip()
    img = (f'<img src="{html.escape(url, quote=True)}" alt="" '
           "onerror=\"this.style.display='none'\" "
           'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;">') if url else ""
    retrato = (
        f'<div style="flex:none;width:172px;aspect-ratio:3/4;position:relative;overflow:hidden;'
        f'border:1px solid {TIJOLO};border-radius:4px;background:{ARTE_BG};">'
        f'<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;'
        f'font-family:{body};font-style:italic;font-size:12px;color:{SEC};text-align:center;padding:12px;">arte a gerar</div>'
        f'{img}</div>'
    )

    cabecalho = (
        f'<div style="display:flex;gap:22px;align-items:flex-start;flex-wrap:wrap;background:{CAIXA};'
        f'border:1px solid {REGUA};border-radius:6px;padding:22px 24px;">'
        f'{retrato}'
        '<div style="flex:1;min-width:220px;">'
        f'<div style="font-family:{serif};font-weight:700;font-size:34px;color:{TIJOLO};line-height:1.05;">{nome}</div>'
        + (f'<div style="font-family:{body};font-style:italic;font-size:15px;color:{SEC};margin-top:4px;">({e(nome_en)})</div>' if mostra_en else '')
        + f'<div style="font-family:{serif};font-size:12px;letter-spacing:.08em;color:{PILL};margin-top:12px;">{meta_txt}{bloqueada}</div>'
        '</div></div>'
    )
    blocos = [cabecalho]

    def secao(titulo, corpo_html):
        return (
            '<div style="margin-top:18px;">'
            f'<div style="font-family:{serif};font-size:13px;letter-spacing:.14em;color:{TIJOLO};'
            f'border-bottom:2px solid {REGUA};padding-bottom:5px;margin-bottom:10px;">{html.escape(titulo).upper()}</div>'
            f'{corpo_html}</div>'
        )

    fp = data.get("filosofia_pilar")
    if fp:
        blocos.append(
            f'<div style="margin-top:18px;background:{PAGINA};border-left:3px solid {REGUA};border-radius:4px;padding:14px 18px;">'
            f'<div style="font-family:{serif};font-size:12px;letter-spacing:.12em;color:{TIJOLO};">{e(fp.get("nome","")).upper()}'
            f'<span style="font-family:{body};font-style:italic;letter-spacing:0;font-size:13px;color:{SEC};margin-left:10px;">{e(fp.get("epiteto",""))}</span></div>'
            f'<div style="font-family:{body};font-style:italic;font-size:14px;color:{TXT};line-height:1.6;margin-top:8px;">{e(fp.get("filosofia",""))}</div>'
            '</div>'
        )

    if data.get("origem"):
        chips = f' <span style="color:{SEC};">+</span> '.join(
            f'<span style="color:{TIJOLO};font-weight:700;">{e(o)}</span>' for o in data["origem"])
        blocos.append(secao("Derivada de",
            f'<div style="font-family:{body};font-size:15px;color:{TXT};">{chips}</div>'))

    blocos.append(secao("Descricao".replace("Descricao", "Descrição"),
        f'<div style="font-family:{body};font-size:15px;color:{TXT};line-height:1.7;white-space:pre-line;">{e(data["descricao"])}</div>'))

    if data.get("diferencial"):
        blocos.append(secao("Diferencial mecânico",
            f'<div style="font-family:{body};font-style:italic;font-size:15px;color:{TXT};line-height:1.7;white-space:pre-line;">{e(data["diferencial"])}</div>'))

    caminhos = data.get("caminhos") or []
    if caminhos:
        itens = []
        for c in caminhos:
            niv = (f' <span style="font-family:{serif};font-size:11px;color:{SEC};">nível {e(c.get("nivel_desbloqueio"))}</span>'
                   if c.get("nivel_desbloqueio") else "")
            itens.append(
                f'<div style="background:{CAIXA};border:1px solid {REGUA};border-radius:4px;padding:12px 14px;margin-bottom:8px;">'
                f'<div style="font-family:{serif};font-weight:700;font-size:15px;color:{TIJOLO};">{e(c.get("nome",""))}{niv}</div>'
                f'<div style="font-family:{body};font-size:14px;color:{TXT};line-height:1.6;white-space:pre-line;margin-top:4px;">{e(c.get("descricao",""))}</div>'
                '</div>')
        corpo_c = "".join(itens)
    else:
        corpo_c = f'<div style="font-family:{body};font-style:italic;color:{SEC};">Esta vocação ainda não tem caminhos definidos.</div>'
    aberto_c = " open" if caminhos else ""
    blocos.append(
        f'<details{aberto_c} style="margin-top:18px;">'
        f'<summary style="font-family:{serif};font-size:13px;letter-spacing:.14em;color:{TIJOLO};'
        f'border-bottom:2px solid {REGUA};padding-bottom:5px;margin-bottom:10px;cursor:pointer;">'
        f'CAMINHOS / SUBCLASSES ({len(caminhos)})</summary>{corpo_c}</details>'
    )

    habs = data.get("habilidades") or []
    if habs:
        partes = []
        nivel_atual = object()
        for h in habs:
            if h.get("nivel") != nivel_atual:
                nivel_atual = h.get("nivel")
                partes.append(f'<div style="font-family:{serif};font-size:12px;letter-spacing:.12em;color:{REGUA};margin:14px 0 6px;">NÍVEL {e(nivel_atual)}</div>')
            pills = []
            if h.get("tipo"):
                pills.append(f'<span style="font-family:{serif};font-size:10px;letter-spacing:.06em;color:{SEC};border:1px solid {SEC};border-radius:3px;padding:1px 7px;">{e(h["tipo"])}</span>')
            if h.get("gera_maestria"):
                pills.append(f'<span style="font-family:{serif};font-size:10px;letter-spacing:.06em;color:#fdf1dc;background:{PILL};border-radius:3px;padding:1px 7px;">MAESTRIA</span>')
            if h.get("requer_caminho"):
                pills.append(f'<span style="font-family:{serif};font-size:10px;letter-spacing:.06em;color:{PILL};border:1px solid {PILL};border-radius:3px;padding:1px 7px;">REQUER CAMINHO</span>')
            partes.append(
                f'<div style="background:{CAIXA};border:1px solid {REGUA};border-radius:4px;padding:11px 14px;margin-bottom:8px;">'
                f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">'
                f'<span style="font-family:{serif};font-weight:700;font-size:15px;color:{TXT};">{e(h.get("nome",""))}</span>{" ".join(pills)}</div>'
                f'<div style="font-family:{body};font-size:14px;color:{TXT};line-height:1.6;white-space:pre-line;margin-top:4px;">{e(h.get("descricao",""))}</div>'
                '</div>')
        corpo_h = "".join(partes)
    else:
        corpo_h = f'<div style="font-family:{body};font-style:italic;color:{SEC};">Esta vocação ainda não tem habilidades mapeadas.</div>'
    aberto_h = " open" if (0 < len(habs) <= 10) else ""
    blocos.append(
        f'<details{aberto_h} style="margin-top:18px;">'
        f'<summary style="font-family:{serif};font-size:13px;letter-spacing:.14em;color:{TIJOLO};'
        f'border-bottom:2px solid {REGUA};padding-bottom:5px;margin-bottom:10px;cursor:pointer;">'
        f'HABILIDADES POR NÍVEL ({len(habs)})</summary>{corpo_h}</details>'
    )

    return "".join(blocos)


@ui.page("/oficina/vocacoes/{voc_id}")
async def pagina_vocacao_detalhe(voc_id: int):
    """Ficha de uma vocacao, em pergaminho."""
    await aguardar_conexao_websocket(f"Abrindo a ficha #{voc_id}...")
    ui.add_head_html(CSS_PERGAMINHO)

    data = await _buscar_vocacao_com_tudo(voc_id)
    if not data:
        with ui.column().classes("w-full min-h-screen p-8 items-center justify-center gap-4").style("background:#efe3c9;"):
            ui.html(f'<div style="font-family:\'Cinzel\',serif;font-size:22px;color:#58180d;">Vocação #{voc_id} não encontrada.</div>')
            ui.button("Voltar", on_click=lambda: ui.navigate.to("/oficina/vocacoes")).props("flat color=brown-8")
        return

    pilar = data["pilar"] or ""
    if pilar in ("corpo", "sombra", "arcano", "espirito", "engenho"):
        data["filosofia_pilar"] = await _buscar_filosofia_pilar(pilar)
        voltar_href = f"/oficina/vocacoes/pilar/{pilar}"
        voltar_txt = f"‹ SALÃO DO {pilar.upper()}"
    else:
        voltar_href = "/oficina/vocacoes"
        voltar_txt = "‹ TODOS OS PILARES"

    with ui.column().classes("w-full min-h-screen p-0 gap-0").style("background:#efe3c9;color:#2a1c0e;"):
        with ui.column().classes("w-full max-w-4xl mx-auto px-6 py-8 gap-3").style("box-sizing:border-box;"):
            ui.html(f'<a href="{voltar_href}" style="text-decoration:none;font-family:\'Cinzel\',serif;'
                    f'font-size:12px;letter-spacing:.12em;color:#7a6648;">{voltar_txt}</a>')
            ui.html(_ficha_vocacao_html(data)).classes("w-full")



# NiceGUI e montado no app do monolito pelo server.py (ui.run_with la).
