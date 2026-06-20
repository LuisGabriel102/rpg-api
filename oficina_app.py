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
import json
import unicodedata
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
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

import config
from auth import BasicAuthMiddleware
from db import engine, get_session
from models import Npcs, RefEstrelasNascimento, RefHabilidadesEstrela, RefVocacoes, RefCaminhos, RefHabilidadesClasseNivel, RefPilares
from ui_helpers import aguardar_conexao_websocket, barra_nav, barra_nav_alderyn
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
# A CATEDRAL DO ALDERYN (v6.4) — landing in-place de /oficina (IMERSIVO tela cheia)
# Bloco A: funcao pura (template + render), sem I/O.
# Raiz = faixa de tela cheia (min-height:100vh) com gradiente azul-noite + flex/center;
# wrapper interno (max-width:1440px) centra na horizontal; 6 portais em uma fileira.
# Layout 100% INLINE (Quasar ignora layout em classe); classe so para fonte.
# Sem !important, sem @import (fontes vem do _VITRAL_HEAD).
# ============================================================

_CATEDRAL_TPL = Template(r"""<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500&family=Inter:wght@300;400;500&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
.cat-root{
  --bg:#131110; --panel:#1d1812; --panel-2:#241d15;
  --line:#352c22; --line-soft:#282017;
  --bone:#ece0c6; --ink:#a0957d; --ink-2:#7a6e59; --glow:#f5dcab;
  --blood:#e8493a; --amber:#f4ba3c; --jade:#2fc4a0;
  --venom:#9bd23e; --violet:#b06ff0; --sepia:#d29658;
  --lock:#5c5448; --gold:#f4ba3c;
  --serif:'Cormorant Garamond',Georgia,serif;
  --sans:'Inter',system-ui,sans-serif;
  --mono:'IBM Plex Mono',ui-monospace,monospace;
  position:relative; width:100%; min-height:100vh; overflow:hidden; box-sizing:border-box;
  padding:0; color:var(--bone); font-family:var(--sans); -webkit-font-smoothing:antialiased;
  background:radial-gradient(130% 62% at 50% -14%, rgba(245,220,171,.12), rgba(245,220,171,0) 56%), var(--bg);
}
.cat-root *{ box-sizing:border-box; }
.cat-vignette{ position:absolute; inset:0; pointer-events:none; z-index:1;
  background:radial-gradient(125% 105% at 50% 30%, transparent 50%, rgba(0,0,0,.6) 100%); }
.cat-grain{ position:absolute; inset:0; pointer-events:none; z-index:2; opacity:.05;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"); }
.cat-wrap{ position:relative; z-index:3; max-width:1160px; margin:0 auto; padding:0 26px; }

.cv-banner{ display:flex; gap:24px; align-items:center; padding:64px 0 12px; }
.cv-banner .cv-sig{ color:var(--bone); flex:none; opacity:.95; }
.cv-banner .cv-sig .cv-glow{ fill:var(--gold); }
.cv-eyebrow{ font-family:var(--mono); font-size:.66rem; letter-spacing:.3em; text-transform:uppercase; color:var(--blood); margin:0 0 12px; }
.cv-h1{ font-family:var(--serif); font-weight:700; line-height:.96; font-size:clamp(2.5rem,5.8vw,3.9rem); margin:0; color:var(--bone); }
.cv-sub{ font-family:var(--serif); font-style:italic; font-size:clamp(1.05rem,2.2vw,1.3rem); color:var(--ink); margin:12px 0 0; }
.cv-acervo{ display:flex; align-items:center; gap:16px; margin:44px 0 20px; }
.cv-acervo span{ font-family:var(--mono); font-size:.7rem; letter-spacing:.34em; text-transform:uppercase; color:var(--ink); }
.cv-acervo .cv-rule{ height:1px; background:var(--line); flex:1; }

.cv-grid{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }
.cv-tile{ position:relative; display:block; text-decoration:none; color:inherit;
  background:linear-gradient(180deg, var(--panel-2), var(--panel));
  border:1px solid var(--line); border-radius:4px; padding:26px 22px 20px; min-height:212px;
  transition:transform .26s ease, border-color .26s ease, box-shadow .26s ease; }
.cv-tile:hover{ transform:translateY(-5px); border-color:var(--c);
  box-shadow:0 0 26px -6px var(--c), 0 16px 36px rgba(0,0,0,.5); }
.cv-tile:focus-visible{ outline:2px solid var(--c); outline-offset:3px; }
.cv-cnr{ position:absolute; width:14px; height:14px; opacity:.45; transition:opacity .26s ease; }
.cv-cnr.tl{ top:-1px; left:-1px; border-top:2px solid var(--c); border-left:2px solid var(--c); }
.cv-cnr.tr{ top:-1px; right:-1px; border-top:2px solid var(--c); border-right:2px solid var(--c); }
.cv-cnr.bl{ bottom:-1px; left:-1px; border-bottom:2px solid var(--c); border-left:2px solid var(--c); }
.cv-cnr.br{ bottom:-1px; right:-1px; border-bottom:2px solid var(--c); border-right:2px solid var(--c); }
.cv-tile:hover .cv-cnr{ opacity:1; }
.cv-ic{ color:var(--c); height:42px; margin-bottom:16px; filter:drop-shadow(0 0 10px transparent); transition:filter .26s ease; }
.cv-tile:hover .cv-ic{ filter:drop-shadow(0 0 12px var(--c)); }
.cv-tile h3{ font-family:var(--serif); font-weight:600; font-size:1.68rem; line-height:1.04; margin:0 0 7px; color:var(--bone); }
.cv-tile p{ font-family:var(--sans); font-weight:300; font-size:.9rem; line-height:1.45; color:var(--ink); margin:0; }
.cv-stat{ position:absolute; left:22px; bottom:18px; display:flex; align-items:baseline; gap:8px; font-family:var(--mono); padding-top:11px; }
.cv-stat .cv-num{ font-size:1.5rem; font-weight:600; color:var(--c); line-height:1; }
.cv-stat .cv-lbl{ font-size:.6rem; letter-spacing:.2em; text-transform:uppercase; color:var(--ink-2); }
.cv-stat.word .cv-lbl{ color:var(--c); opacity:.85; }
.cv-tile.locked{ background:linear-gradient(180deg, #181410, #16120e); cursor:default; }
.cv-tile.locked:hover{ transform:none; border-color:var(--line); box-shadow:none; }
.cv-tile.locked:hover .cv-cnr{ opacity:.45; }
.cv-tile.locked:hover .cv-ic{ filter:none; }
.cv-tile.locked .cv-ic{ color:var(--lock); }
.cv-tile.locked h3{ color:#8c826e; }
.cv-tile.locked p{ color:var(--ink-2); }
.cv-ribbon{ position:absolute; top:14px; right:-30px; transform:rotate(45deg);
  background:#2a241b; color:var(--lock); border:1px solid #3a3226;
  font-family:var(--mono); font-size:.54rem; letter-spacing:.22em; text-transform:uppercase; padding:4px 36px; }

.cv-endnav{ margin:56px 0 0; }
.cv-foot-rule{ height:1px; background:var(--line); margin-bottom:26px; }
.cv-nav-row{ display:flex; align-items:center; justify-content:space-between; gap:22px 30px; flex-wrap:wrap; }
.cv-enter{ display:inline-flex; align-items:center; gap:11px; text-decoration:none;
  font-family:var(--serif); font-weight:500; font-size:1.22rem; color:var(--gold);
  border:1px solid var(--gold); border-radius:5px; padding:11px 26px;
  background:linear-gradient(180deg, rgba(244,186,60,.12), rgba(244,186,60,.03));
  transition:box-shadow .26s ease, background .26s ease; }
.cv-enter:hover{ background:linear-gradient(180deg, rgba(244,186,60,.24), rgba(244,186,60,.08)); box-shadow:0 0 30px -4px var(--gold); }
.cv-dests{ display:flex; align-items:center; gap:13px; flex-wrap:wrap; }
.cv-dests a{ font-family:var(--serif); font-size:1.2rem; color:var(--ink); text-decoration:none;
  padding-bottom:2px; border-bottom:1.5px solid transparent; transition:color .25s, border-color .25s; }
.cv-dests a:hover{ color:var(--bone); }
.cv-dests a.on{ color:var(--bone); border-bottom-color:var(--blood); }
.cv-dests .cv-dot{ color:var(--ink-2); font-family:var(--serif); }
.cv-footer{ margin:40px 0 56px; }
.cv-thesis{ font-family:var(--serif); font-style:italic; font-size:1.1rem; color:var(--ink); text-align:center; margin:0; }
.cv-seal{ font-family:var(--mono); font-size:.6rem; letter-spacing:.3em; text-transform:uppercase; color:var(--ink-2); text-align:center; margin:14px 0 0; }

@media (max-width:920px){ .cat-root .cv-grid{ grid-template-columns:repeat(2,1fr); } .cat-root .cv-banner{ flex-direction:column; align-items:flex-start; } }
@media (max-width:560px){ .cat-root .cv-grid{ grid-template-columns:1fr; } .cat-root .cv-nav-row{ justify-content:flex-start; } }
@media (prefers-reduced-motion:reduce){ .cat-root *{ transition:none !important; } }
</style>
<div class="cat-root">
  <div class="cat-vignette"></div>
  <div class="cat-grain"></div>
  <div class="cat-wrap">

    <header class="cv-banner">
      <svg class="cv-sig" viewBox="0 0 100 100" width="78" height="78" aria-hidden="true">
        <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" stroke-width="0.6" opacity="0.42"/>
        <circle cx="50" cy="50" r="34" fill="none" stroke="currentColor" stroke-width="0.5" opacity="0.3"/>
        <g fill="currentColor">
          <circle cx="88" cy="50" r="1.8" opacity=".7"/><circle cx="82.9" cy="69" r="1.5" opacity=".4"/>
          <circle cx="69" cy="82.9" r="1.8" opacity=".6"/><circle cx="50" cy="88" r="1.5" opacity=".45"/>
          <circle cx="31" cy="82.9" r="1.8" opacity=".65"/><circle cx="17.1" cy="69" r="1.5" opacity=".4"/>
          <circle cx="12" cy="50" r="1.8" opacity=".7"/><circle cx="17.1" cy="31" r="1.5" opacity=".42"/>
          <circle cx="31" cy="17.1" r="1.8" opacity=".6"/><circle cx="50" cy="12" r="1.5" opacity=".48"/>
          <circle cx="69" cy="17.1" r="1.8" opacity=".66"/><circle cx="82.9" cy="31" r="1.5" opacity=".4"/>
        </g>
        <circle cx="50" cy="50" r="7.5" fill="none" stroke="var(--gold)" stroke-width="0.6" opacity="0.6"/>
        <circle class="cv-glow" cx="50" cy="50" r="3.3" opacity="0.95"/>
      </svg>
      <div>
        <p class="cv-eyebrow">Arquivo da Catedral &middot; Vig&iacute;lia Quebrada &middot; 312</p>
        <h1 class="cv-h1">A Catedral do Alderyn</h1>
        <p class="cv-sub">Tudo aqui tem um pre&ccedil;o. Inclusive saber.</p>
      </div>
    </header>

    <div class="cv-acervo"><span>O Acervo</span><div class="cv-rule"></div></div>

    <div class="cv-grid">

      <a class="cv-tile" style="--c:var(--blood)" href="$vocacoes_href">
        <i class="cv-cnr tl"></i><i class="cv-cnr tr"></i><i class="cv-cnr bl"></i><i class="cv-cnr br"></i>
        <div class="cv-ic"><svg viewBox="0 0 24 24" width="42" height="42" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22V12"/><path d="M12 12L5 4"/><path d="M12 12l7-8"/><circle cx="5" cy="3.4" r="1.4"/><circle cx="19" cy="3.4" r="1.4"/></svg></div>
        <h3>Voca&ccedil;&otilde;es</h3>
        <p>O que se escolhe ser &#8212; e o que isso custa.</p>
        <span class="cv-stat"><span class="cv-num">$vocacoes_count</span><span class="cv-lbl">Voca&ccedil;&otilde;es</span></span>
      </a>

      <a class="cv-tile" style="--c:var(--amber)" href="$estrelas_href">
        <i class="cv-cnr tl"></i><i class="cv-cnr tr"></i><i class="cv-cnr bl"></i><i class="cv-cnr br"></i>
        <div class="cv-ic"><svg viewBox="0 0 24 24" width="42" height="42" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2.5l1.7 7.8L21.5 12l-7.8 1.7L12 21.5l-1.7-7.8L2.5 12l7.8-1.7z"/></svg></div>
        <h3>Estrelas</h3>
        <p>Os astros sob os quais se nasce.</p>
        <span class="cv-stat word"><span class="cv-lbl">Os Astros</span></span>
      </a>

      <a class="cv-tile" style="--c:var(--jade)" href="$npcs_href">
        <i class="cv-cnr tl"></i><i class="cv-cnr tr"></i><i class="cv-cnr bl"></i><i class="cv-cnr br"></i>
        <div class="cv-ic"><svg viewBox="0 0 24 24" width="42" height="42" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="8.5" cy="8" r="3"/><circle cx="16.5" cy="9" r="2.4"/><path d="M3.5 19c0-3 2.2-5 5-5s5 2 5 5"/><path d="M14.5 19c.2-2.4 1.6-4 4-4 1.4 0 2.6.6 3 2"/></svg></div>
        <h3>NPCs</h3>
        <p>Os vivos &#8212; e o que cada um esconde.</p>
        <span class="cv-stat"><span class="cv-num">$npcs_count</span><span class="cv-lbl">Figuras</span></span>
      </a>

      <a class="cv-tile" style="--c:var(--venom)" href="$bestiario_href">
        <i class="cv-cnr tl"></i><i class="cv-cnr tr"></i><i class="cv-cnr bl"></i><i class="cv-cnr br"></i>
        <div class="cv-ic"><svg viewBox="0 0 24 24" width="42" height="42" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><ellipse cx="12" cy="15.5" rx="4.6" ry="3.6"/><circle cx="6.5" cy="10" r="1.7"/><circle cx="10" cy="6.6" r="1.7"/><circle cx="14" cy="6.6" r="1.7"/><circle cx="17.5" cy="10" r="1.7"/></svg></div>
        <h3>Besti&aacute;rio</h3>
        <p>O que ca&ccedil;a nas margens.</p>
        <span class="cv-stat"><span class="cv-num">$bestiario_count</span><span class="cv-lbl">Criaturas</span></span>
      </a>

      <a class="cv-tile" style="--c:var(--violet)" href="$magias_href">
        <i class="cv-cnr tl"></i><i class="cv-cnr tr"></i><i class="cv-cnr bl"></i><i class="cv-cnr br"></i>
        <div class="cv-ic"><svg viewBox="0 0 24 24" width="42" height="42" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3.5L20.5 19H3.5z"/><circle cx="12" cy="14" r="2.1"/></svg></div>
        <h3>Magias</h3>
        <p>O pre&ccedil;o de dobrar o mundo.</p>
        <span class="cv-stat"><span class="cv-num">$magias_count</span><span class="cv-lbl">Magias</span></span>
      </a>

      <span class="cv-tile locked" style="--c:var(--lock)" aria-disabled="true">
        <i class="cv-cnr tl"></i><i class="cv-cnr tr"></i><i class="cv-cnr bl"></i><i class="cv-cnr br"></i>
        <span class="cv-ribbon">em obras</span>
        <div class="cv-ic"><svg viewBox="0 0 24 24" width="42" height="42" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="9" rx="1.5"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg></div>
        <h3>Itens</h3>
        <p>O que se carrega, e o que pesa.</p>
        <span class="cv-stat word"><span class="cv-lbl">Trancado</span></span>
      </span>

    </div>

    <nav class="cv-endnav" aria-label="Navega&ccedil;&atilde;o principal">
      <div class="cv-foot-rule"></div>
      <div class="cv-nav-row">
        <a class="cv-enter" href="$jogar_href">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h13"/><path d="M13 6l6 6-6 6"/></svg>
          Entrar no Mundo
        </a>
        <div class="cv-dests">
          <a href="/oficina" class="on">Oficina</a>
          <span class="cv-dot">&middot;</span>
          <a href="$jogar_href">Jogo</a>
          <span class="cv-dot">&middot;</span>
          <a href="/oraculo">Or&aacute;culo</a>
          <span class="cv-dot">&middot;</span>
          <a href="/sistema">Sistema</a>
          <span class="cv-dot">&middot;</span>
          <a href="$historias_href">Hist&oacute;rias</a>
        </div>
      </div>
    </nav>

    <footer class="cv-footer">
      <p class="cv-thesis">Tudo tem nome. Todo nome tem pre&ccedil;o.</p>
      <p class="cv-seal">Vig&iacute;lia Quebrada &middot; 312</p>
    </footer>

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
        magias_count=counts.get('magias', '-'),
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
        total_npcs, total_estrelas, total_vocacoes, total_criaturas, total_magias = await asyncio.wait_for(
            asyncio.gather(
                _contar_npcs_total(),
                _contar_estrelas_total(),
                _contar_vocacoes_total(),
                contar_criaturas_canonizadas(),
                _contar_magias_exibiveis(),
            ),
            timeout=10.0,
        )
    except Exception as e:
        print(f"[catedral] erro ao contar: {e}")
        total_npcs = total_estrelas = total_vocacoes = total_criaturas = total_magias = 0

    counts = {
        "vocacoes": total_vocacoes,
        "estrelas": total_estrelas,
        "npcs": total_npcs,
        "bestiario": total_criaturas,
        "magias": total_magias,
    }
    hrefs = {
        "vocacoes": "/oficina/vocacoes",
        "estrelas": "/oficina/estrelas",
        "npcs": "/oficina/npcs",
        "bestiario": "/oficina/bestiario",
        "magias": "/oficina/magias",
        "itens": "#",
        "jogar": "/jogar",
        "historias": "/oficina/historias",
    }

    _full = render_catedral_html(counts, hrefs)
    if "</style>" in _full:
        _head_css, _full = _full.split("</style>", 1)
        ui.add_head_html(_head_css + "</style>")
    ui.html(_full).classes("w-full")


# ============================================================
# GRIMÓRIO DAS MAGIAS (v3) — hub de 8 dominios -> disciplina + Marca da Sombra + Folio.
# So magias nativas Nexus: fonte LIKE 'NEXUS%' (1.666 de 2.252; resto e lixo D&D,
# fica no banco escondido). Sem DELETE/UPDATE. Tudo leitura.
# Hub nao carrega magias (so contagem agregada) -> leve. Disciplina carrega ~40.
# ============================================================

# --- dominios (ordem fixa de exibicao + cor) ---
DOMINIOS = [
    ("Os Elementos", "#6f93b0"),
    ("A Carne",      "#b56a62"),
    ("A Mente",      "#3a8c94"),
    ("O Véu",        "#6d6f9e"),
    ("O Curso",      "#3f8c6e"),
    ("Os Pactos",    "#c2a043"),
    ("A Ordem",      "#97a0a8"),
    ("O Estranho",   "#8f9c5e"),
]
_COR_DOMINIO = dict(DOMINIOS)

EPIGRAFE_DOMINIO = {
    "Os Elementos": "A matéria não tem lado. Só obedece a quem insiste mais.",
    "A Carne":      "O corpo é o primeiro material. E o que menos perdoa.",
    "A Mente":      "Toda porta para dentro de alguém abre nos dois sentidos.",
    "O Véu":        "Há o que se vê, e há o resto. Trabalhamos no resto.",
    "O Curso":      "Tempo, peso, destino: empurre qualquer um e ele empurra de volta.",
    "Os Pactos":    "Toda força maior atende. Nenhuma atende de graça.",
    "A Ordem":      "Regra, runa e máquina: obedecem até a letra. Inclusive a errada.",
    "O Estranho":   "Saberes que não deviam funcionar. E funcionam.",
}

# familia (nome CRU do banco) -> dominio. Auditado em runtime: 42/42, soma 1.666.
FAMILIA_DOMINIO = {
    "Piromancia": "Os Elementos", "Criomancia": "Os Elementos", "Hidromancia": "Os Elementos",
    "Aeromancia": "Os Elementos", "Geomancia": "Os Elementos", "Electromancia": "Os Elementos",
    "Acidomancia": "Os Elementos", "Toxicomancia": "Os Elementos", "Fotomancia": "Os Elementos",
    "Sonomancia": "Os Elementos",
    "Hemomancia": "A Carne", "Biomancia": "A Carne", "Fitomancia": "A Carne",
    "Zoomancia": "A Carne", "Metamorfomancia": "A Carne",
    "Mnemomancia": "A Mente", "Psicomancia": "A Mente", "Emociomancia": "A Mente",
    "Oniromancia": "A Mente", "Encantomancia": "A Mente",
    "Umbramancia": "O Véu", "Ilusionismo": "O Véu", "Magia do Veu": "O Véu",
    "Cronomancia": "O Curso", "Fatomancia": "O Curso", "Gravitomancia": "O Curso",
    "Dimensiomancia": "O Curso", "Entropiomancia": "O Curso",
    "Teomancia": "Os Pactos", "Sacromancia": "Os Pactos", "Pactomancia": "Os Pactos",
    "Magia Ancestral": "Os Pactos", "Necromancia": "Os Pactos", "Divinomancia": "Os Pactos",
    "Nomomancia": "A Ordem", "Runomancia": "A Ordem", "Artificiomancia": "A Ordem",
    "Combatomancia": "A Ordem", "Aegimancia": "A Ordem",
    "Magia Aberrante": "O Estranho", "Magia Feerica": "O Estranho", "Magia Musical": "O Estranho",
}

# nomes de familia sem acento no banco -> exibicao com acento (WHERE usa o cru).
EXIBICAO_FAMILIA = {
    "Magia do Veu": "Magia do Véu",
    "Magia Feerica": "Magia Feérica",
}

EPIGRAFES = {
    "Piromancia": "O fogo não conhece dono. Só combustível.",
    "Criomancia": "O gelo não mata. Só espera você parar de se mexer.",
    "Hidromancia": "A água sempre acha o caminho mais baixo. Como tudo que dura.",
    "Aeromancia": "O vento não toma partido. Só apaga os rastros.",
    "Geomancia": "A pedra tem paciência. Enterra todo mundo no fim.",
    "Electromancia": "O raio escolhe o caminho mais curto. Raramente é o seu.",
    "Acidomancia": "Não corrói o que toca. Corrói o tempo que levaria a apodrecer.",
    "Toxicomancia": "A dose certa cura. A mesma dose, mais tarde, enterra.",
    "Fotomancia": "A luz revela tudo. Inclusive o que era melhor não ter visto.",
    "Sonomancia": "Todo som chega antes de você ver de onde veio.",
    "Hemomancia": "O sangue paga adiantado. Sempre.",
    "Biomancia": "Consertar um corpo é decidir o que ele vai ser depois.",
    "Fitomancia": "A raiz não tem pressa. Vai chegar onde você dorme.",
    "Zoomancia": "O bicho não mente sobre o que quer. Inveje isso.",
    "Metamorfomancia": "Mudar de forma é fácil. Lembrar a sua é que custa.",
    "Mnemomancia": "Apagar uma lembrança deixa a forma do buraco.",
    "Psicomancia": "Entrar numa mente é simples. A porta tranca por dentro na saída.",
    "Emociomancia": "Toda emoção plantada cresce com a raiz de outra pessoa.",
    "Oniromancia": "No sonho não há testemunhas. Por isso ele é honesto.",
    "Encantomancia": "A ordem mais obedecida é a que parece ideia própria.",
    "Umbramancia": "Nenhuma luz é inteira. Nós trabalhamos no resto.",
    "Ilusionismo": "A mentira que todos veem vale mais que a verdade que ninguém olha.",
    "Magia do Veu": "Há um outro lado. Ele também olha de volta.",
    "Cronomancia": "O tempo cede quando empurrado. E cobra os juros depois.",
    "Fatomancia": "Saber o que vem não te livra. Só te deixa esperando.",
    "Gravitomancia": "Tudo que sobe já combinou a queda. Resta saber sobre quem.",
    "Dimensiomancia": "A distância mais curta entre dois pontos passa por lugar nenhum.",
    "Entropiomancia": "Nada se conserta de graça. Algo, em algum lugar, piora.",
    "Teomancia": "Rezar é pedir. Isto aqui é assinar.",
    "Sacromancia": "O sagrado não protege. Cobra fidelidade.",
    "Pactomancia": "Todo pacto é justo. Você é que lê a cláusula tarde demais.",
    "Magia Ancestral": "Os que vieram antes não se foram. Eles cobram aluguel.",
    "Necromancia": "Os mortos não voltam. Mas escutam, e obedecem.",
    "Divinomancia": "Os presságios nunca mentem. Só não explicam.",
    "Nomomancia": "Uma regra dita com força vira lei. Até alguém gritar mais alto.",
    "Runomancia": "A palavra gravada não esquece, não dorme e não perdoa.",
    "Artificiomancia": "A máquina não cansa de obedecer. Nem de errar exatamente igual.",
    "Combatomancia": "A técnica perfeita ainda precisa de alguém disposto a sangrar.",
    "Aegimancia": "Todo escudo ensina ao inimigo onde bater mais forte.",
    "Magia Aberrante": "Algumas portas abrem para dentro de quem bate.",
    "Magia Feerica": "O favor delas é real. O preço também — e nunca é o combinado.",
    "Magia Musical": "A canção entra sem bater. E reorganiza os móveis.",
}

# 8 sigilos (um por dominio), SVG inline witcher-grey, stroke = cor do dominio.
SIGILOS = {
"Os Elementos": '<svg viewBox="0 0 40 40"><rect x="11" y="11" width="18" height="18" transform="rotate(45 20 20)" fill="none" stroke="#6f93b0" stroke-width="1.4"/><line x1="20" y1="6" x2="20" y2="34" stroke="#6f93b0" stroke-width="1"/><line x1="6" y1="20" x2="34" y2="20" stroke="#6f93b0" stroke-width="1"/></svg>',
"A Carne": '<svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="12" fill="none" stroke="#b56a62" stroke-width="1.4"/><path d="M20 9 Q26 20 20 31 Q14 20 20 9" fill="none" stroke="#b56a62" stroke-width="1"/></svg>',
"A Mente": '<svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="13" fill="none" stroke="#3a8c94" stroke-width="1"/><circle cx="20" cy="20" r="8" fill="none" stroke="#3a8c94" stroke-width="1"/><circle cx="20" cy="20" r="3" fill="#3a8c94"/></svg>',
"O Véu": '<svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="12" fill="none" stroke="#6d6f9e" stroke-width="1.4"/><path d="M20 8 A12 12 0 0 1 20 32 Z" fill="#6d6f9e" opacity="0.32"/><line x1="20" y1="8" x2="20" y2="32" stroke="#6d6f9e" stroke-width="1"/></svg>',
"O Curso": '<svg viewBox="0 0 40 40"><path d="M12 9 L28 9 L20 20 L28 31 L12 31 L20 20 Z" fill="none" stroke="#3f8c6e" stroke-width="1.4"/><line x1="12" y1="9" x2="28" y2="9" stroke="#3f8c6e" stroke-width="1.3"/><line x1="12" y1="31" x2="28" y2="31" stroke="#3f8c6e" stroke-width="1.3"/></svg>',
"Os Pactos": '<svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="12" fill="none" stroke="#c2a043" stroke-width="1.4"/><circle cx="20" cy="20" r="6" fill="none" stroke="#c2a043" stroke-width="1"/><line x1="11" y1="29" x2="29" y2="11" stroke="#c2a043" stroke-width="1.2"/></svg>',
"A Ordem": '<svg viewBox="0 0 40 40"><rect x="9" y="9" width="22" height="22" fill="none" stroke="#97a0a8" stroke-width="1.4"/><line x1="20" y1="9" x2="20" y2="31" stroke="#97a0a8" stroke-width="1"/><line x1="9" y1="20" x2="31" y2="20" stroke="#97a0a8" stroke-width="1"/></svg>',
"O Estranho": '<svg viewBox="0 0 40 40"><path d="M7 20 Q20 9 33 20 Q20 31 7 20 Z" fill="none" stroke="#8f9c5e" stroke-width="1.4"/><ellipse cx="20" cy="20" rx="2.6" ry="6" fill="#8f9c5e"/></svg>',
}

# ---------------------------------------------------------------------------
# SIGILOS DOS ELEMENTOS: as 10 familias do dominio "Os Elementos" ganham forma
# PROPRIA (card pequeno ~40px) + brasao GRANDE animado (cabecalho da disciplina).
# As outras 32 familias NAO entram aqui -> seguem com o diamante do dominio.
# ELEMENTO_ESCOLA: familia crua -> nome do elemento (arquivo /static/sigilos/{x}.svg).
# FORMA_ESCOLA: familia crua -> SVG estatico da forma central (inline, ja 40x40).
# ---------------------------------------------------------------------------
ELEMENTO_ESCOLA = {
    "Piromancia": "fogo", "Criomancia": "gelo", "Hidromancia": "agua",
    "Aeromancia": "vento", "Geomancia": "terra", "Electromancia": "raio",
    "Acidomancia": "acido", "Toxicomancia": "veneno", "Fotomancia": "luz",
    "Sonomancia": "trovao",
    "Hemomancia": "hemomancia",
    "Biomancia": "biomancia",
    "Fitomancia": "fitomancia",
    "Zoomancia": "zoomancia",
    "Metamorfomancia": "metamorfomancia",
    "Mnemomancia": "mnemomancia",
    "Psicomancia": "psicomancia",
    "Emociomancia": "emociomancia",
    "Oniromancia": "oniromancia",
    "Encantomancia": "encantomancia",
    "Umbramancia": "umbramancia",
    "Ilusionismo": "ilusionismo",
    "Magia do Veu": "magia-do-veu",
    "Cronomancia": "cronomancia",
    "Fatomancia": "fatomancia",
    "Gravitomancia": "gravitomancia",
    "Dimensiomancia": "dimensiomancia",
    "Entropiomancia": "entropiomancia",
    "Teomancia": "teomancia",
    "Sacromancia": "sacromancia",
    "Pactomancia": "pactomancia",
    "Magia Ancestral": "magia-ancestral",
    "Necromancia": "necromancia",
    "Divinomancia": "divinomancia",
    "Nomomancia": "nomomancia",
    "Runomancia": "runomancia",
    "Artificiomancia": "artificiomancia",
    "Combatomancia": "combatomancia",
    "Aegimancia": "aegimancia",
    "Magia Aberrante": "magia-aberrante",
    "Magia Feerica": "magia-feerica",
    "Magia Musical": "magia-musical",
}
FORMA_ESCOLA = {
"Piromancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M20 34 C13 30 11 22 16 16 C16.5 19 17.5 20.5 19 21 C16.5 15 19 9 17.5 5 C23 8 26 14 24 20 C25.5 18.5 26.5 16.5 26.5 14.5 C30 19 29 27 23 33 C22 34.2 21 34.2 20 34 Z" fill="#e0822e"/><path d="M20 31 C16.5 28 15.5 23 18 19 C18.5 21 19.3 22 20.3 22.6 C19 18.5 20.5 14.5 20 11.5 C22.6 14.5 23.4 18.5 22 22 C23.4 25.5 22.5 28.5 20 31 Z" fill="#ffb24a"/></svg>',
"Criomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><polygon points="20,3 28,12 25,29 20,37 15,29 12,12" fill="#bfe0ec" fill-opacity="0.16" stroke="#79b6cc" stroke-width="1.4" stroke-linejoin="round"/><path d="M20 3 L20 37 M12 12 L28 12 M15 29 L20 20 L25 29" fill="none" stroke="#79b6cc" stroke-width="1" opacity="0.9" stroke-linejoin="round"/></svg>',
"Hidromancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M20 5 C25 14 29 20 29 25 A9 9 0 1 1 11 25 C11 20 15 14 20 5 Z" fill="#3f8a9e"/><path d="M15.5 24 a4.5 4.5 0 0 0 1 7.5" fill="none" stroke="#a6d4df" stroke-width="1.5" opacity="0.75" stroke-linecap="round"/></svg>',
"Aeromancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M7 13 Q19 8 28 12 Q33 14 30 17.5" fill="none" stroke="#e3e9eb" stroke-width="1.7" stroke-linecap="round"/><path d="M6 21 Q20 16 31 20" fill="none" stroke="#e3e9eb" stroke-width="1.7" stroke-linecap="round"/><path d="M9 29 Q19 25 26 28 Q30 29.5 27.5 32.5" fill="none" stroke="#cdd5d7" stroke-width="1.5" stroke-linecap="round"/></svg>',
"Geomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M20 6 L32 12.5 L32 26 L20 32.5 L8 26 L8 12.5 Z" fill="#b5934a" fill-opacity="0.16" stroke="#b5934a" stroke-width="1.4" stroke-linejoin="round"/><path d="M8 12.5 L20 18.7 L32 12.5 M20 18.7 L20 32.5" fill="none" stroke="#b5934a" stroke-width="1.2" opacity="0.9"/></svg>',
"Electromancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M23 4 L12 22 L18 22 L15 36 L28 16 L22 16 L26 4 Z" fill="#ecd84a"/></svg>',
"Acidomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M20 6 C23 12 25 15.5 25 18.5 a5 5 0 1 1 -10 0 C15 15.5 17 12 20 6 Z" fill="#c2b54a"/><ellipse cx="20" cy="31.5" rx="11" ry="3.3" fill="#c2b54a" opacity="0.78"/><ellipse cx="20" cy="31.5" rx="5" ry="1.5" fill="#e1d273"/></svg>',
"Toxicomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M20 6 C24 14 28 19 28 24 A8 8 0 1 1 12 24 C12 19 16 14 20 6 Z" fill="#6f8d36"/><circle cx="22.5" cy="26" r="2.3" fill="#aac26a"/><circle cx="17" cy="22.5" r="1.4" fill="#aac26a"/></svg>',
"Fotomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><polygon points="20.0,3.0 21.6,16.1 27.8,12.2 23.9,18.4 37.0,20.0 23.9,21.6 27.8,27.8 21.6,23.9 20.0,37.0 18.4,23.9 12.2,27.8 16.1,21.6 3.0,20.0 16.1,18.4 12.2,12.2 18.4,16.1" fill="#e0a838"/><circle cx="20" cy="20" r="3.6" fill="#ffd070"/></svg>',
"Sonomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><circle cx="20" cy="20" r="15" fill="none" stroke="#9a82c8" stroke-width="1.5"/><circle cx="20" cy="20" r="10" fill="none" stroke="#9a82c8" stroke-width="1.4" opacity="0.85"/><circle cx="20" cy="20" r="5" fill="none" stroke="#9a82c8" stroke-width="1.3" opacity="0.7"/><circle cx="20" cy="20" r="2" fill="#b4a6da"/></svg>',
"Hemomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><circle cx="20" cy="26" r="8.5" fill="#984e46"/><circle cx="14.5" cy="22" r="6" fill="#984e46"/><circle cx="25.5" cy="22.5" r="6.5" fill="#984e46"/><circle cx="20" cy="15" r="5" fill="#984e46"/><circle cx="19.5" cy="9" r="3.4" fill="#984e46"/><circle cx="22.5" cy="31" r="4.6" fill="#984e46"/><circle cx="14.5" cy="30" r="3.6" fill="#984e46"/></svg>',
"Biomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M14 13 C11 5 20 1 26 4 C21 5 18 8 17 14 Z" fill="#c2837b"/><path d="M28 17 L39 19 L28 23 C31 21 31 20 28 17 Z" fill="#c2837b"/><path d="M14 27 L16 38 Q19 34 21 37 Q20 31 26 30 Z" fill="#c2837b"/><circle cx="20" cy="20" r="8.6" fill="#c2837b"/></svg>',
"Fitomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M20 18 C18 24 22 30 20 36 M19.5 26 C15 28 12 27 8 31 M20.5 30 C25 32 28 31 32 35" fill="none" stroke="#b97068" stroke-width="2.2" stroke-linecap="round"/><path d="M20 18 C20 13 20 9 20 6" fill="none" stroke="#b97068" stroke-width="2.2" stroke-linecap="round"/><path d="M20 4 L23 7 L21 8 L24 11 L21 12 L23 16 L20 18 L17 16 L19 12 L16 11 L19 8 L17 7 Z" fill="#8f5048" stroke="#5e302a" stroke-width="0.7" stroke-linejoin="round"/></svg>',
"Zoomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M 18.9 28.9 L 19.9 28.4 L 20.6 27.7 L 21.3 27.2 L 21.9 26.7 L 22.5 26.3 L 23.1 26.0 L 23.4 25.5 L 23.7 24.9 L 24.0 24.2 L 24.5 23.6 L 25.0 23.0 L 25.6 22.4 L 26.3 21.8 L 26.9 21.3 L 27.6 20.8 L 28.3 20.3 L 29.0 19.9 L 29.7 19.5 L 29.7 19.5 L 29.0 19.8 L 28.2 20.1 L 27.4 20.4 L 26.6 20.6 L 25.8 20.8 L 25.0 21.1 L 24.1 21.3 L 23.3 21.5 L 22.4 21.7 L 21.5 22.1 L 20.6 22.5 L 19.9 23.1 L 19.4 24.0 L 19.1 25.0 L 18.8 25.9 L 18.7 26.9 L 18.6 27.9 L 18.9 28.9 Z" fill="#a85c54"/><path d="M 16.2 22.8 L 17.0 22.4 L 17.5 21.9 L 18.0 21.5 L 18.5 21.2 L 19.0 20.9 L 19.4 20.7 L 19.7 20.4 L 19.9 20.0 L 20.2 19.5 L 20.6 19.1 L 21.1 18.7 L 21.6 18.3 L 22.1 18.0 L 22.6 17.6 L 23.2 17.3 L 23.7 17.0 L 24.3 16.7 L 24.9 16.5 L 24.9 16.5 L 24.3 16.7 L 23.7 16.8 L 23.1 16.9 L 22.4 17.0 L 21.8 17.1 L 21.2 17.1 L 20.5 17.2 L 19.8 17.2 L 19.1 17.3 L 18.3 17.5 L 17.6 17.7 L 16.9 18.1 L 16.5 18.8 L 16.3 19.6 L 16.1 20.4 L 16.0 21.1 L 15.9 21.9 L 16.2 22.8 Z" fill="#a85c54"/><path d="M 12.2 15.4 L 12.9 15.1 L 13.3 14.8 L 13.7 14.5 L 14.1 14.3 L 14.4 14.1 L 14.7 14.1 L 14.9 13.9 L 15.0 13.5 L 15.1 13.2 L 15.4 12.8 L 15.7 12.5 L 16.0 12.2 L 16.4 11.9 L 16.7 11.6 L 17.1 11.3 L 17.5 11.1 L 17.9 10.9 L 18.3 10.7 L 18.3 10.7 L 17.9 10.8 L 17.4 10.9 L 17.0 11.0 L 16.5 11.1 L 16.1 11.1 L 15.6 11.2 L 15.1 11.2 L 14.6 11.3 L 14.1 11.3 L 13.6 11.4 L 13.0 11.6 L 12.6 12.0 L 12.3 12.5 L 12.1 13.1 L 12.0 13.7 L 12.0 14.2 L 12.0 14.8 L 12.2 15.4 Z" fill="#a85c54"/></svg>',
"Metamorfomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M 20 6 C 18.6 9 17.5 12 18.3 15.5 C 19 19 22 21 21.2 24 C 20.6 27 18.4 29.5 19.4 32 C 19.8 33.4 20 33.6 20 34 C 13.6 33 8.8 27.6 8.8 20 C 8.8 12.4 13.6 7 20 6 Z" fill="#a05a52"/><path d="M 20 6 C 18.6 9 17.5 12 18.3 15.5 C 19 19 22 21 21.2 24 C 20.6 27 18.4 29.5 19.4 32 C 19.8 33.4 20 33.6 20 34 C 26.6 33 31.4 27.6 31.4 20 C 31.4 12.4 26.6 7 20 6 Z" fill="#a05a52"/><path d="M 23 9 Q 32 10.5 34 16 Q 29.5 13.5 24.5 14.5 Q 26 11.5 23 9 Z" fill="#944f47" stroke="#62332d" stroke-width="0.9"/><path d="M 24 17 Q 33 18.5 35 24 Q 30.5 21.5 25.5 22.5 Q 27 19.5 24 17 Z" fill="#944f47" stroke="#62332d" stroke-width="0.9"/><path d="M 23 25 Q 31.5 26.5 33.5 32 Q 29 29.5 24 30.5 Q 25.5 27.5 23 25 Z" fill="#944f47" stroke="#62332d" stroke-width="0.9"/><path d="M 20 6 C 18.6 9 17.5 12 18.3 15.5 C 19 19 22 21 21.2 24 C 20.6 27 18.4 29.5 19.4 32 C 19.8 33.4 20 33.6 20 34" fill="none" stroke="#512b25" stroke-width="1.7" stroke-linecap="round"/></svg>',
"Mnemomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M 12 7 Q 9 7 9 10 L 9 30 Q 9 33 12 33 L 28 33 Q 31 33 31 30 L 31 24 L 24 20 L 31 16 L 31 10 Q 31 7 28 7 Z" fill="#348089"/></svg>',
"Psicomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><circle cx="20" cy="15" r="7" fill="#2d6f78"/><path d="M 16.5 16 L 23.5 16 L 27 33 L 13 33 Z" fill="#2d6f78"/></svg>',
"Emociomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><g stroke="#45999f" stroke-width="1.5" stroke-linecap="round" fill="none"><path d="M 20 22 L 20 36"/><path d="M 20 25 C 15 28 10 32 6.5 37"/><path d="M 20 26 C 25 29 30 32 33.5 37"/><path d="M 20 30 C 17 33 15 35 13 38"/><path d="M 20 30 C 23 33 25 35 27 38"/></g><line x1="20" y1="14" x2="20" y2="23" stroke="#45999f" stroke-width="3.4" stroke-linecap="round"/><path d="M 20 16 Q 9 12 7 2 Q 16 7 20 16 Z" fill="#45999f"/><path d="M 20 16 Q 31 12 33 2 Q 24 7 20 16 Z" fill="#45999f"/></svg>',
"Oniromancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M 6 20 Q 20 9 34 20 Q 20 31 6 20 Z" fill="none" stroke="#4fa6ad" stroke-width="2.2"/><circle cx="20" cy="20" r="7.5" fill="#4fa6ad"/><path fill-rule="evenodd" fill="#162e30" d="M 15.5 20 A 4.5 4.5 0 1 0 24.5 20 A 4.5 4.5 0 1 0 15.5 20 Z M 18 20 A 3.6 3.6 0 1 0 25.2 20 A 3.6 3.6 0 1 0 18 20 Z"/></svg>',
"Encantomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><g transform="rotate(0 20 20)"><path d="M 20 20 C 19 11 23 6 32 4 C 27 11 25 16 20 20 Z" fill="#3a8c94"/></g><g transform="rotate(120 20 20)"><path d="M 20 20 C 19 11 23 6 32 4 C 27 11 25 16 20 20 Z" fill="#3a8c94"/></g><g transform="rotate(240 20 20)"><path d="M 20 20 C 19 11 23 6 32 4 C 27 11 25 16 20 20 Z" fill="#3a8c94"/></g><circle cx="20" cy="20" r="3" fill="#48afb9"/></svg>',
"Umbramancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M 20 9 A 11 11 0 0 1 20 31 Q 15 20 20 9 Z" fill="#2a2b40"/><circle cx="20" cy="20" r="11" fill="none" stroke="#5a5c86" stroke-width="1.8"/><path d="M 20 9 A 11 11 0 0 0 20 31" fill="none" stroke="#8486ad" stroke-width="2.2"/><path d="M 20 9 Q 15 20 20 31" fill="none" stroke="#8486ad" stroke-width="0.9" opacity="0.6"/></svg>',
"Ilusionismo": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M 18 8 C 12 9 9 14 9 19 C 9 27 14 33 18 33 C 16 31 14 26 14 19 C 14 14 15 10 18 8 Z" fill="#424356" opacity="0.65"/><path d="M 20 7 C 26 7 29 12 29 19 C 29 27 24 34 20 34 C 16 34 11 27 11 19 C 11 12 14 7 20 7 Z" fill="#8486ad"/><path d="M 15 18 Q 18 16 21 18 Q 18 20 15 18 Z" fill="#2a2b37"/><path d="M 22 18 Q 25 16 27 18 Q 25 20 22 18 Z" fill="#2a2b37"/><path d="M 17 26 Q 20 28 24 26" fill="none" stroke="#2a2b37" stroke-width="1.4" stroke-linecap="round"/></svg>',
"Magia do Veu": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M 7 8 L 17 9 Q 16 20 17 33 L 7 34 Z" fill="#6d6f9e" stroke="#36384f" stroke-width="0.6"/><path d="M 33 8 L 23 9 Q 24 20 23 33 L 33 34 Z" fill="#6d6f9e" stroke="#36384f" stroke-width="0.6"/><line x1="10" y1="11" x2="10" y2="32" stroke="#4a4b6b" stroke-width="0.7" opacity="0.5"/><line x1="13" y1="11" x2="13" y2="32" stroke="#4a4b6b" stroke-width="0.7" opacity="0.5"/><line x1="27" y1="11" x2="27" y2="32" stroke="#4a4b6b" stroke-width="0.7" opacity="0.5"/><line x1="30" y1="11" x2="30" y2="32" stroke="#4a4b6b" stroke-width="0.7" opacity="0.5"/><path d="M 20 12 C 22 16 22 26 20 30 C 18 26 18 16 20 12 Z" fill="#a9acf5"/></svg>',
"Cronomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><rect x="11" y="6" width="18" height="3" rx="1" fill="#4dab86"/><rect x="11" y="31" width="18" height="3" rx="1" fill="#4dab86"/><path d="M 13 9.5 L 27 9.5 L 20 20 Z" fill="#3f8c6e"/><path d="M 20 20 L 27 30.5 L 13 30.5 Z" fill="#3f8c6e"/></svg>',
"Fatomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><line x1="20" y1="6" x2="20" y2="34" stroke="#4a9a7a" stroke-width="2.6"/><path d="M 20 13.5 L 26 20 L 20 26.5 L 14 20 Z" fill="#4a9a7a"/><circle cx="20" cy="20" r="2" fill="#6bdfb1"/></svg>',
"Gravitomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><circle cx="20" cy="27.5" r="6.8" fill="#387a60"/><circle cx="17.5" cy="25" r="2.2" fill="#50ad88" opacity="0.55"/><g fill="none" stroke="#387a60" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M 20 4.5 L 20 18.5 M 17.6 15.6 L 20 18.5 L 22.4 15.6"/><path d="M 6.5 8 L 15.2 20.2 M 12.3 19.4 L 15.2 20.2 L 14.4 16.6"/><path d="M 33.5 8 L 24.8 20.2 M 25.6 16.6 L 24.8 20.2 L 27.7 19.4"/></g></svg>',
"Dimensiomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M 15 11 L 9 11 L 9 29 L 15 29" fill="none" stroke="#55a886" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M 25 11 L 31 11 L 31 29 L 25 29" fill="none" stroke="#55a886" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M 13 20 L 27 20 M 23 16.5 L 28 20 L 23 23.5" fill="none" stroke="#6edaae" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
"Entropiomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><polygon points="21.0,20.0 17.0,26.9 9.0,26.9 5.0,20.0 9.0,13.1 17.0,13.1" fill="#2f6e54"/><g transform="rotate(12 23 17)"><rect x="19.5" y="13.5" width="7" height="7" fill="#2f6e54"/></g><g transform="rotate(-18 30 15)"><rect x="27.5" y="12.5" width="5" height="5" fill="#2f6e54"/></g><g transform="rotate(25 34 23)"><rect x="32" y="21" width="4" height="4" fill="#3d8f6d"/></g><g transform="rotate(-10 37 18)"><rect x="35.5" y="16.5" width="3" height="3" fill="#3f9471" opacity="0.8"/></g></svg>',
"Teomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><line x1="8" y1="31" x2="32" y2="31" stroke="#c2a043" stroke-width="2.4" stroke-linecap="round"/><path d="M 25 7 C 18 13 15 20 17 30 C 22 21 26 14 30 9 C 29 8 27 7 25 7 Z" fill="#c2a043"/></svg>',
"Sacromancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><circle cx="20" cy="20" r="13.5" fill="none" stroke="#b5933a" stroke-width="3"/><line x1="29" y1="11" x2="32.5" y2="7.5" stroke="#b5933a" stroke-width="2" stroke-linecap="round"/><g stroke="#cead52" stroke-width="2.4" stroke-linecap="round"><line x1="19.5" y1="13" x2="18.3" y2="27"/><line x1="13.5" y1="17.5" x2="24.5" y2="15.5"/><line x1="15" y1="25" x2="24" y2="27"/></g></svg>',
"Pactomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><rect x="9" y="7" width="18" height="24" rx="2" fill="#cead52"/><g stroke="#675629" stroke-width="1.5" stroke-linecap="round"><line x1="12" y1="12" x2="24" y2="12"/><line x1="12" y1="16" x2="24" y2="16"/><line x1="12" y1="20" x2="21" y2="20"/></g><circle cx="25" cy="30" r="6" fill="#9a5a3a"/><circle cx="25" cy="30" r="3" fill="none" stroke="#6e3c26" stroke-width="1.1"/></svg>',
"Magia Ancestral": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><ellipse cx="20" cy="11" rx="4.3" ry="6.0" fill="none" stroke="#a3852f" stroke-width="2.4"/><path d="M 20 14.0 A 4.3 6.0 0 0 1 24.3 21.2 M 15.7 20.4 A 4.3 6.0 0 0 1 20 14.0 M 20 26.0 A 4.3 6.0 0 0 0 15.7 19.4" fill="none" stroke="#a3852f" stroke-width="2.4" stroke-linecap="round"/><ellipse cx="20" cy="29" rx="4.3" ry="6.0" fill="none" stroke="#a3852f" stroke-width="2.4"/></svg>',
"Necromancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M 12 23 L 12 13 A 8 8 0 0 1 28 13 L 28 23 Z" fill="#8f7430"/><line x1="8" y1="31" x2="32" y2="31" stroke="#8f7430" stroke-width="2.2" stroke-linecap="round"/><g fill="#3a3320"><rect x="14" y="22" width="2.6" height="9" rx="1.3"/><rect x="18" y="20" width="2.6" height="11" rx="1.3"/><rect x="22" y="23" width="2.6" height="8" rx="1.3"/><rect x="25.5" y="24" width="2.4" height="7" rx="1.2"/></g></svg>',
"Divinomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M 26 16 L 7 23 L 10 28 Z" fill="#b89f5a"/><g transform="rotate(26 28 14)"><path d="M 28.0 7.0 L 30.2 11.8 L 35.0 14.0 L 30.2 16.2 L 28.0 21.0 L 25.8 16.2 L 21.0 14.0 L 25.8 11.8 Z" fill="#d9bb6a"/></g><circle cx="28" cy="14" r="2.3" fill="#ffff9f"/></svg>',
"Nomomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M9 12 Q9 7 13 7 L27 7 Q31 7 31 12 L31 35 L9 35 Z" fill="#7e858b" stroke="#666e74" stroke-width="1" stroke-linejoin="round"/><line x1="13" y1="15" x2="27" y2="15" stroke="#545b61" stroke-width="1.6" stroke-linecap="round"/><line x1="13" y1="21" x2="26" y2="21" stroke="#545b61" stroke-width="1.6" stroke-linecap="round"/><line x1="13" y1="27" x2="27" y2="27" stroke="#545b61" stroke-width="1.6" stroke-linecap="round"/></svg>',
"Runomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M20 5 L20 35 M20 13 L30 5 M20 25 L11 33" fill="none" stroke="#a4adb3" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
"Artificiomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M 33.2,20.0 L 37.0,20.8 L 35.8,26.3 L 32.0,25.4 L 29.3,29.3 L 31.4,32.6 L 26.8,35.6 L 24.7,32.3 L 20.0,33.2 L 19.2,37.0 L 13.7,35.8 L 14.6,32.0 L 10.7,29.3 L 7.4,31.4 L 4.4,26.8 L 7.7,24.7 L 6.8,20.0 L 3.0,19.2 L 4.2,13.7 L 8.0,14.6 L 10.7,10.7 L 8.6,7.4 L 13.2,4.4 L 15.3,7.7 L 20.0,6.8 L 20.8,3.0 L 26.3,4.2 L 25.4,8.0 L 29.3,10.7 L 32.6,8.6 L 35.6,13.2 L 32.3,15.3 Z M 25.0 20.0 A 5.0 5.0 0 1 0 15.0 20.0 A 5.0 5.0 0 1 0 25.0 20.0 Z" fill="#909aa0" fill-rule="evenodd" stroke="#6f787e" stroke-width="1" stroke-linejoin="round"/><circle cx="20" cy="20" r="5.6" fill="none" stroke="#aeb6bb" stroke-width="1.1" opacity="0.7"/></svg>',
"Combatomancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><polygon points="16.2,26.1 30.6,9.4 13.9,23.8" fill="#868d93"/><line x1="15.1" y1="24.9" x2="11.5" y2="28.5" stroke="#868d93" stroke-width="2.4" stroke-linecap="round"/><line x1="11.5" y1="21.4" x2="18.6" y2="28.5" stroke="#868d93" stroke-width="2" stroke-linecap="round"/><polygon points="26.1,23.8 9.4,9.4 23.8,26.1" fill="#868d93"/><line x1="24.9" y1="24.9" x2="28.5" y2="28.5" stroke="#868d93" stroke-width="2.4" stroke-linecap="round"/><line x1="21.4" y1="28.5" x2="28.5" y2="21.4" stroke="#868d93" stroke-width="2" stroke-linecap="round"/></svg>',
"Aegimancia": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M8 9 L32 9 C32 20 30 28 20 36 C10 28 8 20 8 9 Z" fill="#97a0a8" stroke="#6f787e" stroke-width="1.2" stroke-linejoin="round"/><line x1="20" y1="10" x2="20" y2="34" stroke="#7e878d" stroke-width="1.1" opacity="0.5"/></svg>',
"Magia Aberrante": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><polygon points="20,4.5 22.5,11 24.2,18 25.5,24 22.8,30 20,36 17.5,30.5 14.8,24 16,18 17.8,11" fill="#7a8550"/><polygon points="20,8.5 21,12.5 22,18 22.5,24 20.8,29 20,32.5 19,29 17.2,24 18,18 19,12.5" fill="#0c0f0a"/><polygon points="18.7,13.0 19.7,14 18.7,15.0 17.7,14" fill="#c8d4a0"/><polygon points="21,19.7 22.8,21.5 21,23.3 19.2,21.5" fill="#c8d4a0"/><polygon points="19.2,26.7 20.5,28 19.2,29.3 17.9,28" fill="#c8d4a0"/></svg>',
"Magia Feerica": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M 16 22 C 15 27 15 31 17 34 L 23 34 C 25 31 25 27 24 22 Z" fill="#8f9c5e"/><path d="M 8 21 C 8 11 32 11 32 21 C 28 24.5 12 24.5 8 21 Z" fill="#8f9c5e"/><g fill="#3c4227"><ellipse cx="15.5" cy="17.5" rx="2" ry="1.5"/><ellipse cx="24.5" cy="16.5" rx="1.7" ry="1.3"/><ellipse cx="20" cy="19.5" rx="1.4" ry="1.1"/></g></svg>',
"Magia Musical": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><g fill="none" stroke="#a3b072" stroke-width="2" stroke-linecap="round"><line x1="8" y1="14" x2="8" y2="26"/><path d="M 8 14 Q 13 9 18 14 Q 23 19 28 14 Q 31 11 33 14"/><path d="M 8 26 Q 12 20 16 26 Q 19 31 23 22 Q 26 17 30 28 Q 32 31 33 26"/></g></svg>',
}

# Marca da Sombra: escala propria, FORA das 8 cores de dominio (destoa de proposito).
COR_CORRUPCAO = {1: "#7e4a48", 2: "#9c3b3b", 3: "#8a1f1f"}  # doente -> coagulo -> sangue

# escola no banco vem sem acento; normaliza so na exibicao (nao mexe no banco).
_ESCOLA_EXIBICAO = {
    "Transmutacao": "Transmutação",
    "Evocacao": "Evocação",
    "Ilusao": "Ilusão",
    "Abjuracao": "Abjuração",
    "Divinacao": "Divinação",
    "Conjuracao": "Conjuração",
    "Encantamento": "Encantamento",
    "Necromancia": "Necromancia",
}
_COR_ESCOLA = {
    "Transmutacao": "#3f6a9e",
    "Encantamento": "#6f5a96",
    "Conjuracao": "#468268",
    "Evocacao": "#9a4e30",
    "Necromancia": "#8a5a8c",
    "Abjuracao": "#a07e2a",
    "Divinacao": "#c19022",
    "Ilusao": "#5a7aa0",
}


def _slugify(s: str) -> str:
    base = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return base.lower().replace(" ", "-")


_FAMILIA_SLUG = {fam: _slugify(fam) for fam in FAMILIA_DOMINIO}
_SLUG_FAMILIA = {slug: fam for fam, slug in _FAMILIA_SLUG.items()}
if len(_SLUG_FAMILIA) != len(_FAMILIA_SLUG):  # colisao de slug -> aviso (nao quebra)
    print("[magias] AVISO: colisao de slug entre familias")


def _familia_exibicao(fam: str) -> str:
    return EXIBICAO_FAMILIA.get(fam, fam)


def _romano(n) -> str:
    return {1: "I", 2: "II", 3: "III"}.get(n, str(n))


_SQL_CONTAR_MAGIAS = text(
    "SELECT count(*) FROM public.magias WHERE fonte LIKE 'NEXUS%'"
)

# Hub: contagem agregada por familia (n + sombrias). NAO carrega magias.
_SQL_HUB = text("""
    SELECT familia_magica AS familia, count(*) AS n,
           count(*) FILTER (WHERE enhancements->>'anima_sombria' = 'true') AS sombrias
    FROM public.magias
    WHERE fonte LIKE 'NEXUS%'
    GROUP BY familia_magica
""")

# Disciplina: carrega uma familia so, com os campos do folio + enhancements.
_SQL_FAMILIA = text("""
    SELECT id, nome, nivel_original, mp_custo, escola, descricao,
           requer_concentracao, componentes, alcance, tipo_dano, familia_magica,
           tempo_conjuracao, duracao, tem_material, material_desc, enhancements
    FROM public.magias
    WHERE fonte LIKE 'NEXUS%' AND familia_magica = :familia
    ORDER BY escola, nivel_original, nome
""")


async def _contar_magias_exibiveis() -> int:
    """Conta so as magias nativas Nexus (fonte LIKE 'NEXUS%'). Filtrado, nao total."""
    async with get_session() as session:
        result = await session.execute(_SQL_CONTAR_MAGIAS)
        return result.scalar() or 0


async def _buscar_hub_contagens() -> dict:
    """familia -> {'n', 'sombrias'}. Leve: so agregacao, nenhuma magia carregada."""
    async with get_session() as session:
        result = await session.execute(_SQL_HUB)
        linhas = result.all()
    out = {}
    for r in linhas:
        mm = r._mapping
        out[mm["familia"]] = {"n": mm["n"], "sombrias": mm["sombrias"]}
    return out


def _parse_enhancements(raw):
    """enhancements (jsonb) ja vem dict via SQLAlchemy; guarda contra str/None."""
    if raw is None:
        return {}
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}
    return raw if isinstance(raw, dict) else {}


async def _buscar_magias_familia(familia: str) -> list[dict]:
    """Magias de uma familia (~15-51), com folio + marca da sombra parseados."""
    async with get_session() as session:
        result = await session.execute(_SQL_FAMILIA, {"familia": familia})
        linhas = result.all()
    out = []
    for r in linhas:
        m = r._mapping
        enh = _parse_enhancements(m["enhancements"])
        sombria = str(enh.get("anima_sombria")).lower() == "true"
        grau = None
        if sombria:
            try:
                grau = int(enh.get("corrupcao_anima"))
            except (TypeError, ValueError):
                grau = 1
            if grau not in (1, 2, 3):
                grau = 1
        out.append({
            "id": m["id"],
            "nome": m["nome"] or "?",
            "nivel": m["nivel_original"] if m["nivel_original"] is not None else 0,
            "mp": m["mp_custo"],
            "escola": m["escola"] or "",
            "descricao": m["descricao"] or "",
            "concentracao": bool(m["requer_concentracao"]),
            "componentes": list(m["componentes"]) if m["componentes"] else [],
            "alcance": m["alcance"] or "",
            "tipo_dano": list(m["tipo_dano"]) if m["tipo_dano"] else [],
            "familia": m["familia_magica"] or "",
            "tempo_conjuracao": m["tempo_conjuracao"] or "",
            "duracao": m["duracao"] or "",
            "tem_material": bool(m["tem_material"]),
            "material_desc": m["material_desc"] or "",
            "sombria": sombria,
            "grau": grau,
            "motivo": (enh.get("motivo_narrativo") or "").strip(),
            "pot": enh.get("potencializacao"),
        })
    return out


def _card_magia_html(m: dict) -> str:
    escola_raw = m["escola"]
    cor = _COR_ESCOLA.get(escola_raw, "#b8902f")
    escola_txt = html.escape(_ESCOLA_EXIBICAO.get(escola_raw, escola_raw) or "—")
    nome = html.escape(m["nome"])
    nivel = m["nivel"]
    nivel_txt = "Truque" if nivel == 0 else f"Nível {nivel}"
    mp = m["mp"]
    dano = " · ".join(m["tipo_dano"]) if m["tipo_dano"] else ""
    familia = html.escape(_familia_exibicao(m["familia"])) if m["familia"] else ""
    desc = html.escape((m["descricao"] or "").strip())

    meta = [nivel_txt]
    if mp is not None:
        meta.append(f"{mp} MP")
    if m["componentes"]:
        meta.append(" ".join(m["componentes"]))
    if m["alcance"]:
        meta.append(html.escape(m["alcance"]))
    if m["concentracao"]:
        meta.append("Concentração")
    meta_txt = " · ".join(meta)

    selos = (
        f'<span style="font-family:\'IM Fell English SC\',serif;font-size:10px;'
        f'letter-spacing:.1em;color:{cor};">{escola_txt.upper()}</span>'
    )
    if dano:
        selos += (
            '<span style="font-family:\'IM Fell English SC\',serif;font-size:10px;'
            f'letter-spacing:.1em;color:#9a8a5a;margin-left:10px;">{html.escape(dano).upper()}</span>'
        )

    # Marca da Sombra: selo vermelho + custo em prosa (so se anima_sombria).
    selo_sombra = ""
    custo_html = ""
    nome_pr = ""
    if m.get("sombria"):
        grau = m.get("grau") or 1
        ccor = COR_CORRUPCAO.get(grau, COR_CORRUPCAO[1])
        nome_pr = "padding-right:72px;"
        selo_sombra = (
            f'<span style="position:absolute;top:10px;right:12px;font-family:\'IM Fell English SC\',serif;'
            f'font-size:9px;letter-spacing:.12em;color:{ccor};background:{ccor}1f;'
            f'border:1px solid {ccor};border-radius:3px;padding:2px 7px;">SOMBRIA {_romano(grau)}</span>'
        )
        motivo = m.get("motivo") or ""
        if motivo:
            mot = motivo if len(motivo) <= 90 else motivo[:90].rstrip() + "…"
            custo_html = (
                f'<div style="font-family:\'Spectral\',Georgia,serif;font-style:italic;font-size:11.5px;'
                f'color:{ccor};margin-top:8px;line-height:1.4;">{html.escape(mot)}</div>'
            )
    familia_html = (
        f'<div style="font-family:\'Spectral\',Georgia,serif;font-style:italic;font-size:11px;'
        f'color:#7a6f55;margin-top:6px;">{familia}</div>' if familia else ""
    )
    return (
        '<div style="position:relative;display:block;overflow:hidden;height:100%;'
        f'border:1px solid {cor};border-left:4px solid {cor};border-radius:6px;'
        'padding:14px 16px 15px;background:rgba(12,14,22,.55);box-sizing:border-box;">'
        f'{selo_sombra}'
        f'<div style="font-family:\'IM Fell English\',serif;font-size:18px;color:#f3e7c4;line-height:1.15;{nome_pr}">{nome}</div>'
        f'<div style="margin-top:4px;">{selos}</div>'
        f'<div style="font-family:\'Spectral\',Georgia,serif;font-size:12px;color:#c0a36a;margin-top:6px;">{meta_txt}</div>'
        f'<div style="font-family:\'Spectral\',Georgia,serif;font-size:12.5px;color:#a99a78;line-height:1.5;margin-top:8px;">{desc}</div>'
        f'{custo_html}'
        f'{familia_html}'
        '</div>'
    )


def _folio_html(m: dict) -> str:
    """Ficha completa de uma magia (o folio). Reusa a pele vitral (inline)."""
    escola_raw = m["escola"]
    cor = _COR_ESCOLA.get(escola_raw, "#b8902f")
    escola_txt = html.escape(_ESCOLA_EXIBICAO.get(escola_raw, escola_raw) or "—")
    fam_raw = m["familia"]
    fam_txt = html.escape(_familia_exibicao(fam_raw))
    epig = EPIGRAFES.get(fam_raw, "")
    nome = html.escape(m["nome"])
    p = []
    # 1) nome + disciplina + epigrafe
    p.append(f'<div style="font-family:\'IM Fell English\',serif;font-size:24px;color:#f3e7c4;line-height:1.1;">{nome}</div>')
    p.append(f'<div style="font-family:\'IM Fell English SC\',serif;font-size:11px;letter-spacing:.14em;color:{cor};margin-top:4px;">{fam_txt.upper()}</div>')
    if epig:
        p.append(f'<div style="font-family:\'Spectral\',Georgia,serif;font-style:italic;font-size:12.5px;color:#8a7f68;margin-top:6px;">{html.escape(epig)}</div>')
    # 2) marca da sombra (completa)
    if m.get("sombria"):
        grau = m.get("grau") or 1
        ccor = COR_CORRUPCAO.get(grau, COR_CORRUPCAO[1])
        motivo = html.escape(m.get("motivo") or "")
        p.append(
            f'<div style="margin-top:12px;padding:10px 12px;border:1px solid {ccor};border-radius:5px;background:{ccor}1f;">'
            f'<span style="font-family:\'IM Fell English SC\',serif;font-size:10px;letter-spacing:.12em;color:{ccor};">SOMBRIA {_romano(grau)}</span>'
            + (f'<div style="font-family:\'Spectral\',Georgia,serif;font-style:italic;font-size:13px;color:{ccor};margin-top:6px;line-height:1.5;">{motivo}</div>' if motivo else "")
            + '</div>'
        )
    # 3) linha tecnica
    nivel = m["nivel"]
    tec = [escola_txt, "Truque" if nivel == 0 else f"Nível {nivel}"]
    if m["mp"] is not None:
        tec.append(f"{m['mp']} MP")
    if m["componentes"]:
        tec.append(" · ".join(m["componentes"]))
    if m["concentracao"]:
        tec.append("Concentração")
    p.append(f'<div style="font-family:\'Spectral\',Georgia,serif;font-size:12.5px;color:#c0a36a;margin-top:12px;">{html.escape(" · ".join(tec))}</div>')
    # 4) conjuracao
    conj = []
    if m["tempo_conjuracao"]:
        conj.append("Conjuração: " + m["tempo_conjuracao"])
    if m["alcance"]:
        conj.append("Alcance: " + m["alcance"])
    if m["duracao"]:
        conj.append("Duração: " + m["duracao"])
    if conj:
        p.append(f'<div style="font-family:\'Spectral\',Georgia,serif;font-size:12px;color:#9a8a5a;margin-top:6px;">{html.escape(" · ".join(conj))}</div>')
    # 5) componente material (so se houver)
    if m["tem_material"] and m["material_desc"]:
        p.append(f'<div style="font-family:\'Spectral\',Georgia,serif;font-size:12px;color:#9a8a5a;margin-top:6px;"><b>Material:</b> {html.escape(m["material_desc"])}</div>')
    # 6) descricao completa
    p.append(f'<div style="font-family:\'Spectral\',Georgia,serif;font-size:13px;color:#cdbfa6;line-height:1.6;margin-top:12px;">{html.escape(m["descricao"] or "")}</div>')
    # 7) potencializacao (3 formatos: objeto / texto / ausente)
    pot = m.get("pot")
    pot_txt = ""
    if isinstance(pot, dict):
        efeito = pot.get("efeito")
        custo = pot.get("custo_extra_mp")
        partes = []
        if efeito:
            partes.append(html.escape(str(efeito)))
        if custo is not None:
            partes.append(f"(+{html.escape(str(custo))} MP)")
        pot_txt = " ".join(partes)
    elif isinstance(pot, str) and pot.strip():
        pot_txt = html.escape(pot.strip())
    if pot_txt:
        p.append(
            '<div style="margin-top:12px;border-top:1px solid rgba(201,162,58,.3);padding-top:10px;">'
            '<div style="font-family:\'IM Fell English SC\',serif;font-size:10px;letter-spacing:.12em;color:#c9a23a;">EM NÍVEL SUPERIOR</div>'
            f'<div style="font-family:\'Spectral\',Georgia,serif;font-size:12.5px;color:#a99a78;line-height:1.5;margin-top:4px;">{pot_txt}</div>'
            '</div>'
        )
    return '<div style="width:100%;">' + "".join(p) + '</div>'


def _hub_html(contagens: dict) -> str:
    """A parede do grimorio: 8 dominios, cada um com seus selos de disciplina."""
    blocos = []
    for dom, cor in DOMINIOS:
        familias = sorted(
            [f for f in FAMILIA_DOMINIO if FAMILIA_DOMINIO[f] == dom],
            key=lambda f: _familia_exibicao(f),
        )
        sig = SIGILOS.get(dom, "").replace("<svg ", '<svg width="30" height="30" ', 1)
        selos = []
        for fam in familias:
            c = contagens.get(fam, {"n": 0, "sombrias": 0})
            slug = _FAMILIA_SLUG[fam]
            nome = html.escape(_familia_exibicao(fam))
            # forma PROPRIA p/ as 10 escolas dos Elementos (ja vem 40x40); resto =
            # diamante do dominio (so viewBox -> precisa do width/height no replace).
            if fam in FORMA_ESCOLA:
                sig_selo = FORMA_ESCOLA[fam]
            else:
                sig_selo = SIGILOS.get(dom, "").replace("<svg ", '<svg width="32" height="32" ', 1)
            somb = c["sombrias"]
            somb_html = (
                f'<div style="font-family:\'IM Fell English SC\',serif;font-size:10px;letter-spacing:.06em;'
                f'color:{COR_CORRUPCAO[3]};margin-top:6px;">&#9670; {somb} sombrias</div>'
                if somb > 0 else ""
            )
            selos.append(
                f'<a href="/oficina/magias/{slug}" style="display:block;text-decoration:none;'
                f'border:1px solid {cor};border-left:4px solid {cor};border-radius:6px;'
                f'padding:14px 16px;background:rgba(12,14,22,.55);">'
                f'<div style="color:{cor};">{sig_selo}</div>'
                f'<div style="font-family:\'IM Fell English\',serif;font-size:18px;color:#f3e7c4;margin-top:8px;line-height:1.1;">{nome}</div>'
                f'<div style="font-family:\'IM Fell English SC\',serif;font-size:11px;letter-spacing:.1em;color:{cor};margin-top:4px;">{c["n"]} magias</div>'
                f'{somb_html}'
                '</a>'
            )
        grade = (
            '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px;">'
            + "".join(selos) + '</div>'
        )
        epig = html.escape(EPIGRAFE_DOMINIO.get(dom, ""))
        blocos.append(
            '<div style="margin-top:28px;">'
            '<div style="display:flex;align-items:center;gap:12px;">'
            f'<div style="color:{cor};">{sig}</div>'
            f'<div style="font-family:\'IM Fell English\',serif;font-size:22px;color:{cor};">{html.escape(dom)}</div>'
            '</div>'
            f'<div style="font-family:\'Spectral\',Georgia,serif;font-style:italic;font-size:12.5px;color:#8a7f68;margin:4px 0 12px 42px;">{epig}</div>'
            f'{grade}'
            '</div>'
        )
    return "".join(blocos)


@ui.page("/oficina/magias")
async def pagina_magias():
    """Hub do grimorio: 8 dominios -> selos de disciplina. Nao carrega magias."""
    await aguardar_conexao_websocket("Abrindo o grimório...")
    ui.add_head_html(CSS_VITRAL)
    barra_nav("magias")

    contagens = await _buscar_hub_contagens()
    faltando = sorted(set(contagens) - set(FAMILIA_DOMINIO))
    if faltando:
        print(f"[magias] AVISO: familias sem dominio (somem do hub): {faltando}")
    total = sum(c["n"] for c in contagens.values())

    with ui.column().classes("gp-screen w-full min-h-screen p-0 gap-0"):
        with ui.column().classes("gp-inner w-full gap-4"):
            with ui.row().classes("w-full items-center gap-3"):
                ui.button(icon="arrow_back",
                          on_click=lambda: ui.navigate.to("/oficina")
                          ).props("flat round dense color=amber-2")
                with ui.column().classes("gap-0"):
                    ui.label("Grimório do Alderyn").classes("bestiario-title").style("font-size:30px;")
                    ui.label(f"{total} magias · 8 domínios · 42 disciplinas").classes(
                        "bestiario-body").style("font-style:italic;font-size:13px;")
            ui.html('<div class="gp-rule"></div>')
            ui.html(_hub_html(contagens)).classes("w-full")


@ui.page("/oficina/magias/{slug}")
async def pagina_magias_disciplina(slug: str):
    """Disciplina: as magias de uma familia. Reusa grid + filtros; abre folio no clique."""
    await aguardar_conexao_websocket("Folheando o grimório...")
    ui.add_head_html(CSS_VITRAL)
    barra_nav("magias")

    familia = _SLUG_FAMILIA.get(slug)
    if not familia:
        ui.navigate.to("/oficina/magias")
        return

    dom = FAMILIA_DOMINIO.get(familia, "")
    cor = _COR_DOMINIO.get(dom, "#b8902f")
    fam_txt = _familia_exibicao(familia)
    epig = EPIGRAFES.get(familia, "")

    magias = await _buscar_magias_familia(familia)
    total = len(magias)
    estado = {"escola": "todas", "nivel": "todos", "busca": "", "sombra": False}
    grid_ref = {"el": None}
    contador_ref = {"el": None}

    folio = ui.dialog()

    def abrir_folio(m):
        folio.clear()
        with folio, ui.card().style(
            "background:#10131f;border:1px solid #c9a23a;border-radius:8px;"
            "max-width:600px;width:92vw;padding:20px 22px;"
        ):
            ui.html(_folio_html(m)).classes("w-full")
            ui.button("Fechar", on_click=folio.close).props("flat color=amber-2").classes("self-end")
        folio.open()

    def filtrar() -> list[dict]:
        out = magias
        if estado["escola"] != "todas":
            out = [m for m in out if m["escola"] == estado["escola"]]
        if estado["nivel"] != "todos":
            nv = int(estado["nivel"])
            out = [m for m in out if m["nivel"] == nv]
        if estado["sombra"]:
            out = [m for m in out if m.get("sombria")]
        if estado["busca"]:
            q = estado["busca"].lower()
            out = [m for m in out if q in m["nome"].lower()]
        return out

    def render_grid():
        el = grid_ref["el"]
        if el is None:
            return
        el.clear()
        filtrados = filtrar()
        with el:
            if not filtrados:
                ui.html('<div style="text-align:center;font-style:italic;color:#7a6f55;'
                        'padding:50px 0;">Nenhuma magia encontrada.</div>')
            for m in filtrados:
                card = ui.html(_card_magia_html(m)).style("cursor:pointer")
                card.on("click", lambda e, mm=m: abrir_folio(mm))
        if contador_ref["el"]:
            contador_ref["el"].set_text(f"{len(filtrados)} de {total} magias")

    def set_escola(v):
        estado["escola"] = v
        render_grid()

    def set_nivel(v):
        estado["nivel"] = v
        render_grid()

    def set_busca(e):
        estado["busca"] = (e.value or "").strip()
        render_grid()

    def set_sombra(e):
        estado["sombra"] = bool(e.value)
        render_grid()

    escolas_opts = {"todas": "Todas as escolas"}
    for esc in ["Transmutacao", "Encantamento", "Conjuracao", "Evocacao",
                "Necromancia", "Abjuracao", "Divinacao", "Ilusao"]:
        escolas_opts[esc] = _ESCOLA_EXIBICAO.get(esc, esc)
    niveis_opts = {"todos": "Todos os níveis", "0": "Truques"}
    for n in range(1, 10):
        niveis_opts[str(n)] = f"Nível {n}"

    with ui.column().classes("gp-screen w-full min-h-screen p-0 gap-0"):
        with ui.column().classes("gp-inner w-full gap-4"):
            with ui.row().classes("w-full items-center gap-3"):
                ui.button(icon="arrow_back",
                          on_click=lambda: ui.navigate.to("/oficina/magias")
                          ).props("flat round dense color=amber-2")
                # brasao GRANDE animado: so as 10 escolas dos Elementos. O .svg tem
                # SMIL -> anima sozinho como <img>. Resto das familias: sem brasao.
                if familia in ELEMENTO_ESCOLA:
                    ui.html(
                        f'<img src="/static/sigilos/{ELEMENTO_ESCOLA[familia]}.svg" '
                        f'alt="" width="128" height="128" '
                        f'style="width:128px;height:128px;flex:none;display:block;">'
                    )
                with ui.column().classes("gap-0"):
                    ui.label(fam_txt).classes("bestiario-title").style(f"font-size:30px;color:{cor};")
                    contador_ref["el"] = ui.label(f"{total} de {total} magias").classes(
                        "bestiario-body").style("font-style:italic;font-size:13px;")
            if epig:
                ui.html('<div style="font-family:\'Spectral\',Georgia,serif;font-style:italic;'
                        f'font-size:13px;color:#8a7f68;">{html.escape(epig)}</div>')
            ui.html('<div class="gp-rule"></div>')

            with ui.row().classes("gp-filtros w-full items-center gap-3 flex-wrap").style("padding:12px 14px;"):
                ui.input(placeholder="Buscar por nome...", on_change=set_busca
                         ).props("dense outlined dark clearable").style("min-width:220px;")
                ui.select(escolas_opts, value="todas", on_change=lambda e: set_escola(e.value)
                          ).props("dense outlined dark").style("min-width:180px;")
                ui.select(niveis_opts, value="todos", on_change=lambda e: set_nivel(e.value)
                          ).props("dense outlined dark").style("min-width:150px;")
                ui.switch("Só as que cobram a ânima", on_change=set_sombra
                          ).props("color=red-5").style("color:#b0a48a;")

            grid_ref["el"] = ui.element("div").style(
                "display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));"
                "gap:14px;width:100%;align-items:stretch;"
            )
            render_grid()


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
    "corpo": "#e8493a", "sombra": "#b06ff0", "arcano": "#5b8fd6",
    "espirito": "#f4ba3c", "engenho": "#ee8d3a",
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
