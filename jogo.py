"""
Tela de jogo narrativo - /jogar - PELE "A GRAVURA".

O loop do Cronista e IDENTICO ao da versao anterior (soulsborne): canal duplo
prosa + bloco <estado> oculto, Pressao Emocional 0-10, MODO_MOCK pra testar sem
custo, tratamento de erro que preserva a alternancia user/assistant. O que mudou
foi SO a casca: xilogravura (IM Fell English / Spectral / JetBrains Mono), a luz
que pousa no bloco novo, a estampa, o HUD-marginalia.

HUD (decisao iii): por ora aparece SO a Pressao Emocional (0-10). As barras de
Vida/Vigor/Mana/Fadiga e a Tensao de combate (0-5) existem na camada cliente
(window.Jogar.setStat / setTensao) como base pronta, mas NAO sao exibidas ate o
Degrau de combate ligar - numero que aparece e numero que significa algo.

CANON: Pressao Emocional (0-10, ADR-003) != Tensao de combate (0-5, ADR-004).
Eixos separados. O numero NUNCA aparece na prosa - vive no HUD, por setPressao.

A camada cliente (a luz, o HUD, o input) e o bundle TypeScript em
static/jogar.js (window.Jogar), compilado por esbuild a partir de
client/src/jogar.ts. O loop cliente<->Python anda por emitEvent:
  - 'jogar_action'    {text}  -> o jogador agiu
  - 'jogar_comecar'   {}      -> Adentrar (abre a cena)
  - 'jogar_recomecar' {}      -> Recomecar (zera, custo zero)

MODO_MOCK (no topo): True = prosa FALSA, custo zero, valida a casca; False =
Opus 4.8 real (paga), com prompt caching ligado.
"""

import asyncio
import html
import json
import random
import re
import time
import traceback
from pathlib import Path

from nicegui import ui
from anthropic import AsyncAnthropic
from cronista_prompt import CRONISTA_SYSTEM_PROMPT
from ui_helpers import aguardar_conexao_websocket

# ---------------------------------------------------------------------------
# Tier 4 - memoria do narrador. O /jogar deixa de ser stateless: cada turno e
# gravado em sessao_turnos e o contexto (5 tiers) e lido de volta pro prompt do
# Cronista. Import GUARDADO de proposito: se DATABASE_URL faltar (ex.: rodar a
# casca em mock, sem credencial), o modulo db.py levanta no import - aqui isso
# vira so _MEMORIA_OK=False e o /jogar segue funcionando SEM memoria (degrada
# sem quebrar, como o resto do monolito). SESSAO_ID fixo: Tier 4 binda o /jogar
# a sessao 2 / personagem 3 (a sessao ja carrega o personagem_id no banco).
# ---------------------------------------------------------------------------
SESSAO_ID = 2
try:
    from narrador.memoria.contexto import carregar_contexto
    from narrador.memoria.escrita import gravar_turno
    from narrador.memoria.fim_sessao import encerrar_sessao
    _MEMORIA_OK = True
    _MEMORIA_ERR = None
except Exception as _e:  # noqa: BLE001 - qualquer falha de import desliga a memoria
    _MEMORIA_OK = False
    _MEMORIA_ERR = _e
    print(f"[memoria] desligada (import falhou): {type(_e).__name__}: {_e}")

# ---------------------------------------------------------------------------
# Static: serve a camada cliente (jogar.js) e a estampa. Montado AQUI (no proprio
# modulo, importado pelo server.py DEPOIS de app.main) pra nao precisar tocar no
# server.py - o enxerto fica contido no /jogar. Usamos o mount do FastAPI direto
# no app do backend (robusto: a rota vive no app que o uvicorn serve, sem
# depender de internals do NiceGUI). A whitelist do auth.py ja libera /static/.
# NOTA: em producao a estampa pode migrar pro R2 - basta trocar o src no _BODY
#       por https://imagens.luisgabriel.uk/cenarios/... (ver Secao 5 do handoff).
# ---------------------------------------------------------------------------
_BASE = Path(__file__).resolve().parent
try:
    from app.main import app as _fastapi_app
    from fastapi.staticfiles import StaticFiles

    if not any(getattr(r, "path", None) == "/static" for r in _fastapi_app.routes):
        _fastapi_app.mount(
            "/static", StaticFiles(directory=str(_BASE / "static")), name="static"
        )
except Exception:
    # se /static ja existir, ou em execucao standalone (sem app.main), seguimos
    pass


ABERTURA_MSG = (
    "[ABERTURA] Abra a cena inicial. O protagonista e um andarilho sem nome que chega, "
    "ao anoitecer, a um povoado pequeno em algum lugar de Alderyn, na era da Vigilia "
    "Quebrada. Estabeleca o ambiente pelos sentidos e termine deixando o protagonista "
    "livre para agir. Nao decida nenhuma acao, fala ou pensamento dele."
)


# ============================================================================
# INTERRUPTOR DE MODO
# MODO_MOCK = True  -> prosa FALSA embutida, ZERO custo. Valida a casca toda
#                     (layout da Gravura, canal duplo, Pressao) sem chamar a IA.
# MODO_MOCK = False -> Opus 4.8 de verdade (paga). Valida o tom do Cronista.
# ============================================================================
MODO_MOCK = False  # marco final: Opus 4.8 + Haiku reais (paga). Validado 1 turno+selar.


# Prosa falsa do modo mock - witcher-grey, ambigua (serve pra qualquer acao),
# sem numeros na prosa. Cada trecho carrega um delta que faz a Pressao mexer.
# Cada trecho carrega (prosa, delta_pressao, atmosfera). No mock, as atmosferas
# ciclam de proposito (ermo na abertura, depois mata/frio/sangue/corte) pra dar
# pra TESTAR as 5 peles visuais sem IA - a prosa aqui e placeholder generico.
_MOCK_ABERTURA = (
    "A estrada morria nos primeiros casebres quando o sol já se fora. "
    "Cheirava a fumaça velha, e por baixo dela algo que a fumaça não cobria. "
    "Uma porta batia ao vento, sozinha, e ninguém ia fechá-la. Nas janelas, "
    "nenhuma luz. No fim da ruela, um cão ergueu a cabeça, não latiu, e tornou "
    "a deitar.",
    1,
    "ermo",
)
# Ordem IMPORTA: primeira intencao que casar vence. Agressao testada primeiro
# (a cena mais pesada ganha quando o texto mistura sinais, ex.: "saio atacando").
_INTENCOES = [
    ("agressao", re.compile(
        r"atac|golpe|esfaque|apunhal|soc[oa]|murr|chut|agrid|agred|investe|empunh|"
        r"desembainh|esmag|estrangul|degol|espanc|surr|porrad|pancad|parto pra cima|"
        r"vou pra cima|mato|matar|fer[ie]r", re.IGNORECASE)),
    ("fuga", re.compile(
        r"fuj|fug|corr|escap|recu|afast|saio|me sai|disparo|bat[eo] em retirada|"
        r"me escond|escond|sumo|debando", re.IGNORECASE)),
    ("dialogo", re.compile(
        r"fal[ao]|grit|cham|pergunt|respond|diz[eo]|berr|sussurr|interpel|saud|"
        r"cumpriment|conver|negoci|implor|exij|pedind", re.IGNORECASE)),
    ("cautela", re.compile(
        r"observ|escut|ou[cç]|ouv|espreit|espi|olh|examin|inspecion|vigi|avali|"
        r"aguard|esper|fic[ao] parad|fic[ao] imo", re.IGNORECASE)),
    ("avanco", re.compile(
        r"entr|abr[oae]|avanc|avan[çc]|sig[ao]|segu|and[ao]|caminh|vou |adentr|"
        r"sob[oe]|des[çc]|desc[oe]|atravess|cruz|aproxim|chega|prossig|avante|rumo", re.IGNORECASE)),
]

# Quanto cada intencao mexe na Pressao (clampada 0-10 no retorno).
_DELTA = {"agressao": 3, "fuga": -2, "cautela": 0, "dialogo": 1, "avanco": 1, "ambiguo": -1}

# Banco de prosa: intencao -> faixa de pressao -> lista de trechos.
# A faixa (calma/tensa/critica) modula o TOM; a atmosfera (pele) vem da
# intencao, em _ATM_POR_INTENCAO. 2 trechos por bucket -> anti-repeticao alterna.
_BANCO_REACOES = {
    "agressao": {
        "calma": [
            "O golpe saiu inteiro e encontrou menos do que esperava. O ar cedeu, a rua não, e o que quer que estivesse ali recuou um palmo — sem pressa, como quem ainda decide se vale o trabalho de responder.",
            "Ferro contra o nada, e o nada absorveu. Por um instante pareceu desperdício; depois, ao fundo, uma tábua assentou sob um peso que escolheu não se mostrar.",
        ],
        "tensa": [
            "O golpe partiu o silêncio antes de partir qualquer outra coisa. No vão que abriu, algo se mexeu — devagar, do jeito de quem já contava ter de aparecer.",
            "O ferro encontrou o ar frio e o ar devolveu mais frio ainda. Adiante, na penumbra, uma respiração se firmou. Não era a de quem foge.",
        ],
        "critica": [
            "O golpe caiu e o povoado respondeu de uma vez: madeira estalando em três casas ao mesmo tempo, passos que largaram o disfarce. O que vinha não vinha sozinho, e não vinha para conversar.",
            "A lâmina mal completou o arco e o ar já fervia de movimento. Portas que fingiam vazio se abriram do lado de dentro, e o escuro entre elas tinha agora forma, peso, e fome de acabar aquilo.",
        ],
    },
    "fuga": {
        "calma": [
            "A rua que viera curta ficou longa na volta. O povoado deixou ir sem um som, do jeito de quem solta de propósito o que pretende reaver.",
            "Os casebres ficaram para trás um a um, e nenhum se importou. O recuo foi fácil — fácil demais, do tipo que depois cobra o preço de ter sido.",
        ],
        "tensa": [
            "O fôlego encurtou e o beco fechou à frente. Atrás, nenhum passo perseguia — e a ausência de passos pesou mais do que pesaria a perseguição.",
            "A distância cresceu entre as casas, mas o frio não ficou para trás: veio colado na nuca, e com ele a impressão de que a saída se estreitava a cada passo.",
        ],
        "critica": [
            "Correr já não bastava. O beco despejou em outro, e o outro em muro, e o som atrás — que antes não existia — agora existia e ganhava terreno. O ar faltava na hora errada.",
            "Cada porta por onde tentou sair estava trancada do lado de fora. O fôlego rasgava, o frio mordia, e a única coisa que se movia rápido naquela noite vinha exatamente na direção dele.",
        ],
    },
    "cautela": {
        "calma": [
            "A quietude se estendeu e o povoado a acompanhou. A rua continuou rua, as janelas, janelas. Por ora, nada pedia para ser temido.",
            "Olhar com calma não revelou ameaça nenhuma — só fumaça assentando, uma porta batendo ao vento, o cão lá no fim que nem ergueu a cabeça desta vez.",
        ],
        "tensa": [
            "Atrás de uma fresta, algo ajustou a postura — o gesto curto de quem não quer ser notado notando. Depois a fresta voltou a ser só fresta.",
            "Primeiro o ouvido: madeira sob um peso, um arrasto breve, e então nada. O nada durou tempo demais para ter sido o vento.",
        ],
        "critica": [
            "Parar para escutar, naquele ponto, foi como segurar a respiração à beira de um poço. O silêncio não estava vazio: estava cheio, contido, à espera de que ele fizesse o primeiro ruído.",
            "Os olhos varreram a rua e a rua olhou de volta. De cada sombra vinha a mesma certeza muda — de que esperavam isto, de que o tempo de medir já tinha passado.",
        ],
    },
    "avanco": {
        "calma": [
            "Os passos seguiram entre os casebres sem encontrar resistência. O escuro abriu caminho, indiferente, e por enquanto guardava o que guardava sem ainda cobrar nada.",
            "A ruela aceitou o avanço em silêncio. Nada barrou, nada chamou; só a fumaça velha e a sensação morna de estar entrando onde já o esperavam, sem urgência.",
        ],
        "tensa": [
            "Cada passo afundou um pouco mais no escuro que o povoado guardava. A porta que batia ao vento parou de bater na aproximação — como se, do outro lado, uma mão a tivesse segurado.",
            "O caminho seguiu entre as casas, e as casas seguiram fingindo-se vazias. Numa delas o fingimento falhou: uma respiração, contida tarde demais.",
        ],
        "critica": [
            "Adiante, o escuro deixou de ser escuro e passou a ser presença. O cheiro mudou — algo por baixo da fumaça, fundo e errado — e cada passo a mais era um passo para dentro do que estava prestes a se decidir.",
            "A ruela estreitou até caber só ele, e no fim dela a noite se adensava num ponto que não se movia e respirava. Avançar agora era escolher chegar primeiro.",
        ],
    },
    "dialogo": {
        "calma": [
            "A voz saiu e a rua a engoliu sem eco. As casas continuaram caladas, e o vazio que respondeu não tinha urgência nenhuma — só a indiferença de quem não precisa responder.",
            "O chamado se perdeu entre os telhados e nada o devolveu. Por ora, falar ou calar dava no mesmo: o povoado seguia surdo, ou fingia muito bem.",
        ],
        "tensa": [
            "Ninguém devolveu palavra. Mas uma janela fechada deixou de estar fechada, sem ruído, e ficou assim: aberta, negra, à espera do resto.",
            "A voz encontrou ouvidos — isso o ar deixou sentir. De um ponto que não dava para apontar, algo se ajeitou para escutar melhor, e o silêncio depois foi de propósito.",
        ],
        "critica": [
            "Chamar, ali, foi acender um pavio. O escuro respondeu de uma vez e de muitos lugares: um arrastar de pés que parou junto, combinado, perto demais para ainda se chamar de seguro.",
            "A palavra mal saiu e a noite inteira pareceu virar-se para ele. Não houve resposta em voz — houve movimento, cerco, a certeza de que tinha sido ouvido por exatamente quem não devia ouvir.",
        ],
    },
    "ambiguo": {
        "calma": [
            "O gesto se perdeu no ar parado. O povoado não deu sinal de ter notado — ou fingiu não notar, que ali parecia dar no mesmo.",
            "Fosse o que fosse, a rua absorveu sem resposta. A fumaça seguiu assentando, a noite seguiu morna, e nada naquele instante pediu para ser temido.",
        ],
        "tensa": [
            "O gesto não encontrou resposta, mas o ar já não era o mesmo: estava carregado, atento, e a falta de reação tinha o peso de uma reação adiada.",
            "Nada se moveu — e o nada, desta vez, custou. O silêncio que veio depois era do tipo que escuta de volta, e seguia escutando muito depois de o gesto ter passado.",
        ],
        "critica": [
            "Nada reagiu, e foi pior do que se algo tivesse reagido. O silêncio agora era o de quem já decidiu e só espera o momento; cada casa parecia conter a respiração junto com ele.",
            "O gesto caiu no vazio, mas o vazio estava cheio. À beira daquilo, a indiferença do povoado não era indiferença — era pontaria, paciência, a calma de quem sabe que a noite ainda não acabou.",
        ],
    },
}

# Atmosfera (pele) por intencao. "" = mantem a pele atual (parser ignora ausencia).
_ATM_POR_INTENCAO = {
    "agressao": "sangue",
    "fuga": "corte",
    "cautela": "frio",
    "avanco": "mata",
    "dialogo": "ermo",
    "ambiguo": "",
}


_RE_CONTEXTO_BLOCO = re.compile(r"<contexto>.*?</contexto>", re.S | re.I)


def _texto_do_jogador(conteudo: str) -> str:
    # O narrar monta "[ESTADO] ...\n\n<contexto>...</contexto>\n\n{texto}". Isola o
    # texto: tira o bloco <contexto> (Tier 4) e depois a linha [ESTADO]. O que sobra
    # e a fala do jogador - o mock classifica a intencao em cima dela, nao da
    # maquinaria. Robusto se o bloco <contexto> estiver ausente (turno sem memoria).
    texto = _RE_CONTEXTO_BLOCO.sub("", conteudo)
    if texto.startswith("[ESTADO]"):
        partes = texto.split("\n\n", 1)
        texto = partes[1] if len(partes) > 1 else ""
    return texto.strip()


def _classificar_intencao(texto: str) -> str:
    for nome, rx in _INTENCOES:
        if rx.search(texto):
            return nome
    return "ambiguo"


def _faixa_pressao(p: int) -> str:
    # calma 0-3 | tensa 4-6 | critica 7-10. Robusta fora do range (clampa o sentido).
    if p <= 3:
        return "calma"
    if p <= 6:
        return "tensa"
    return "critica"


def _cronista_mock(historico: list[dict]) -> str:
    """Narrador FALSO, REATIVO. Le a Pressao e a intencao do texto do jogador.
    A intencao define a pele (atmosfera); a faixa da Pressao RESULTANTE define o
    tom da prosa (calma/tensa/critica). Devolve prosa + bloco <estado>."""
    ultima = historico[-1]["content"] if historico else ""
    m = _RE_PRESSAO.search(ultima)
    pressao_entrada = int(m.group(1)) if m else 0
    turno = sum(1 for x in historico if x["role"] == "user")

    if turno <= 1:
        prosa, delta, atm = _MOCK_ABERTURA
        nova = max(0, min(10, pressao_entrada + delta))
    else:
        intencao = _classificar_intencao(_texto_do_jogador(ultima))
        delta = _DELTA[intencao]
        nova = max(0, min(10, pressao_entrada + delta))
        faixa = _faixa_pressao(nova)
        banco = _BANCO_REACOES[intencao][faixa]
        # anti-repeticao: evita o trecho usado no ultimo turno do assistente
        ultima_assist = next(
            (x["content"] for x in reversed(historico) if x["role"] == "assistant"), ""
        )
        candidatos = [t for t in banco if t not in ultima_assist] or banco
        prosa = random.choice(candidatos)
        atm = _ATM_POR_INTENCAO[intencao]

    if atm:
        corpo = f"pressao_emocional: {nova}\natmosfera: {atm}"
    else:
        corpo = f"pressao_emocional: {nova}"
    return f"{prosa}\n\n<estado>\n{corpo}\n</estado>"


_aclient = None


def _get_aclient() -> AsyncAnthropic:
    """Cliente ASYNC (lazy), usado SO pro streaming do Cronista (messages.stream
    roda no event loop do NiceGUI). Lazy de proposito: o MODO_MOCK nao instancia
    nada, entao roda sem credencial."""
    global _aclient
    if _aclient is None:
        _aclient = AsyncAnthropic()
    return _aclient


# ---------------------------------------------------------------------------
# Memoria (Tier 4): gravar turno + carregar contexto. Ambos sao "safe": se a
# memoria estiver desligada (import falhou) ou o banco vacilar, logam e seguem
# sem derrubar o turno. O jogo nunca quebra por causa da memoria.
# ---------------------------------------------------------------------------
async def _gravar_turno_safe(sessao_id: int, papel: str, conteudo: str) -> None:
    if not _MEMORIA_OK:
        return
    try:
        numero = await gravar_turno(sessao_id, papel, conteudo)
        print(f"[memoria] turno gravado: sessao={sessao_id} papel={papel} numero_turno={numero}")
    except Exception as exc:  # noqa: BLE001
        print(f"[memoria] FALHA ao gravar turno ({papel}): {type(exc).__name__}: {exc}")


async def _carregar_contexto_safe(sessao_id: int, query_text: str | None) -> str:
    if not _MEMORIA_OK:
        return ""
    try:
        # query_vec=None de proposito (decisao ii do Tier 4): sem torch/modelo no
        # container, a busca cai pras 3 vias (full-text + trigram + entidade), como
        # a SPEC preve. O vetorial ao vivo entra depois, sem mexer aqui.
        return await carregar_contexto(sessao_id, query_text=query_text, query_vec=None)
    except Exception as exc:  # noqa: BLE001
        print(f"[memoria] FALHA ao carregar contexto: {type(exc).__name__}: {exc}")
        return ""


# Haiku mockado pro fim de sessao enquanto MODO_MOCK=True: zero token. Devolve
# "nenhum fato duravel" - a extracao em si ja foi provada no Tier 5; aqui o foco e
# o WIRING (encerrar -> recap -> nova sessao -> rebind). Com MODO_MOCK=False, o
# encerrar_sessao usa o Haiku real (default).
def _haiku_mock_jogar(narracao: str, lista_entidades: str) -> str:
    return '{"fatos": []}'


_RE_ESTADO = re.compile(r"<estado>(.*?)</estado>", re.S | re.I)
_RE_PRESSAO = re.compile(r"pressao_emocional\s*:\s*(\d+)", re.I)

# As 5 atmosferas da Gravura. O Cronista pode pedir uma trocando a pele da cena
# pelo bloco <estado> (atmosfera: X). Whitelist fechada: nome fora dela e ignorado
# (a cena mantem a atmosfera atual) - degrada sem quebrar, e blinda contra valor
# torto vindo do LLM. ESPELHA a lista no JS de window.setAtmosfera (manter juntas).
ATMOSFERAS = ("ermo", "mata", "frio", "sangue", "corte")
_RE_ATMOSFERA = re.compile(r"atmosfera\s*:\s*([a-z]+)", re.I)


def _separar_estado(resposta: str, pressao_anterior: int) -> tuple[str, int, str | None]:
    """Separa a prosa do bloco <estado>. Devolve (prosa, nova_pressao, atmosfera).

    O bloco <estado> e maquinaria: NUNCA vai pra tela. A validacao aqui e o clamp
    0-10 da Pressao e a whitelist da atmosfera. Se o bloco faltar ou vier torto, a
    prosa passa inteira, a Pressao se mantem e a atmosfera vem None (a cena nao
    troca) - degrada sem quebrar.
    """
    m = _RE_ESTADO.search(resposta)
    if not m:
        return resposta.strip(), pressao_anterior, None
    prosa = resposta[: m.start()].rstrip()
    bloco = m.group(1)
    nova = pressao_anterior
    mp = _RE_PRESSAO.search(bloco)
    if mp:
        nova = max(0, min(10, int(mp.group(1))))
    atm = None
    ma = _RE_ATMOSFERA.search(bloco)
    if ma and ma.group(1).lower() in ATMOSFERAS:
        atm = ma.group(1).lower()
    return prosa, nova, atm


def _prosa_para_html(texto: str) -> str:
    """Prosa segura pra injetar via window.Jogar.arrive (vai pra innerHTML).
    Escapa HTML (a prosa vem do LLM) e converte paragrafos (linha em branco)
    em <p> separados. Quebras simples viram espaco - o corpo e justificado.
    O arrive ja envolve o todo em <p>...</p>, entao juntamos com '</p><p>'.
    """
    esc = html.escape(texto.strip())
    paras = [p.replace("\n", " ").strip() for p in re.split(r"\n\s*\n", esc)]
    return "</p><p>".join(p for p in paras if p)


# Marcador do bloco de estado (oculto). O stream pinga so a parte VISIVEL: corta no
# inicio de "<estado" assim que ele aparece - e, enquanto o marcador chega pedaco a
# pedaco, esconde tambem o prefixo parcial no fim ("<e", "<est"...). Assim a tag
# crua NUNCA pinga na tela. No fim, _separar_estado (que usa "<estado>") faz o corte
# canonico pro processamento - este aqui e so pra exibicao ao vivo.
_MARCADOR_ESTADO = "<estado"


def parte_visivel(acc: str) -> str:
    """So a narracao, sem o bloco de estado. Corta no marcador completo ou no
    prefixo parcial que esteja chegando no fim do texto acumulado."""
    low = acc.lower()
    idx = low.find(_MARCADOR_ESTADO)
    if idx != -1:
        return acc[:idx]
    # marcador a meio caminho no fim do acumulado: esconde o prefixo parcial
    for k in range(len(_MARCADOR_ESTADO) - 1, 0, -1):
        if low.endswith(_MARCADOR_ESTADO[:k]):
            return acc[: len(acc) - k]
    return acc


# ============================================================================
# A PELE: A GRAVURA
# ============================================================================
_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?'
    'family=IM+Fell+English:ital@0;1&family=IM+Fell+English+SC&'
    'family=JetBrains+Mono:wght@500&'
    'family=Spectral:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">'
    # Tabler Icons (outline) - icones das Fichas de Narrador e do Guia.
    '<link href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.31.0/dist/tabler-icons.min.css" rel="stylesheet">'
)

_CSS = """
<style>
:root{
  --ground:#0e0b08; --pagina:#17130c; --breu:#080706;
  --osso:#cdbf9f; --osso2:#8c8167; --leitura:#dbcfb3;
  --brasa:#c67a33; --frio:#aeb6b8;
  --t-sangue:#a8564a; --t-ambar:#ad8744; --t-aco:#5f7f95; --t-malva:#8a7488;
  --regua:rgba(205,191,159,.22); --regua2:rgba(205,191,159,.42);
}
/* --- resets p/ vencer o Quasar/NiceGUI: APP-SHELL de tela cheia (pagina fixa) ---
   A pagina NAO rola: html/body/q-page travados em 100% e overflow:hidden. O
   .nicegui-content vira coluna flex de 100dvh; o wrapper que contem a cena enche
   a coluna inteira (flex:1) - sem barra de nav no topo (a navegacao virou botoes
   no card: oraculo + oficina). O scroll existe SO dentro do .miolo (e do .config-scroll). */
html, body{ height:100%; margin:0; overflow:hidden; }
body, .q-page, .q-page-container, .nicegui-content{ background: var(--ground) !important; }
.q-page-container{ min-height:0 !important; height:100%; }
.q-page{ min-height:0 !important; }
.nicegui-content{ padding:0 !important; gap:0 !important;
  height:100vh; height:100dvh; overflow:hidden; display:flex; flex-direction:column; }
.nicegui-content > div{ width:100% !important; }
.nicegui-content > div:has(.alderyn-stage){ flex:1 1 auto; min-height:0; display:flex; flex-direction:column; }
.oculto{ display:none !important; }

.alderyn-stage{
  width:100%; flex:1 1 auto; min-height:0; display:flex; align-items:stretch; justify-content:center;
  padding:clamp(8px,1.4vh,16px) clamp(10px,1.6vw,22px); position:relative; overflow:hidden;
  background-color:#0a0806;
  background-repeat:no-repeat; background-position:center 40%; background-size:cover;
  /* 3 camadas empilhadas: overlay de leitura | foto (o JS sorteia em --cena) |
     cor de fallback (por atmosfera). Sem foto/sem R2 -> --cena:none e fica a cor. */
  --tint:linear-gradient(180deg, rgba(9,7,6,.40), rgba(8,6,5,.60));
  --cena:none;
  --fallback:radial-gradient(130% 100% at 50% 12%, #1a150e 0%, #110d09 48%, #0a0806 100%);
  background-image:var(--tint), var(--cena), var(--fallback);
  transition:background-color 1s ease;
}
.entrada-cena{ position:absolute; inset:0; z-index:0; pointer-events:none;
  background:linear-gradient(180deg,rgba(9,7,6,.30),rgba(8,6,5,.52)), url("/static/cenarios/entrada/tarelea_vespera.webp");
  background-size:cover; background-position:center; transition:opacity 1.4s ease; }
.alderyn-stage:has(#portal.indo) .entrada-cena{ opacity:0; }
.alderyn-stage::before{
  content:""; position:absolute; inset:0; pointer-events:none; z-index:0;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.6'/%3E%3C/svg%3E");
  opacity:.06; mix-blend-mode:overlay;
}

/* ===========================================================================
   ATMOSFERA: a pele da cena. Cor vai pro MUNDO (--fallback + --aura); a folha e o
   texto ficam INTOCADOS. A classe .atm-X escolhe so a COR; a FOTO entra por --cena,
   que o JS (window.setAtmosfera) SORTEIA entre as variacoes daquela cena. O stage
   empilha: overlay de leitura | --cena (foto) | --fallback (cor). Sem R2/sem foto,
   --cena fica none e aparece a cor - o jogo roda igual. Degrada sem quebrar.
   =========================================================================== */
.alderyn-stage::after{
  content:""; position:absolute; inset:0; pointer-events:none; z-index:0;
  background:radial-gradient(62% 52% at 50% 32%, var(--aura, transparent), transparent 72%);
  opacity:.5; mix-blend-mode:screen; animation:respira 9s ease-in-out infinite;
}
@keyframes respira{ 0%,100%{opacity:.3} 50%{opacity:.62} }

/* BRUMA: nevoa/escuridao que DERIVA lentissima atras da moldura (z-index:0, SEMPRE
   atras da .pagina que e z-index:1 -> nunca sobre o texto). Oversize (inset negativo)
   + translate3d/scale num ciclo bem longo: transform-only, sem reflow. O stage tem
   overflow:hidden, entao a camada maior que a tela e clipada sem gerar rolagem. */
.bruma{ position:absolute; inset:-25%; z-index:0; pointer-events:none; opacity:.5; mix-blend-mode:multiply;
  background:
    radial-gradient(42% 52% at 28% 32%, rgba(6,5,4,0), rgba(5,4,3,.55) 72%),
    radial-gradient(46% 56% at 74% 70%, rgba(6,5,4,0), rgba(4,3,2,.5) 75%);
  animation:bruma-deriva 54s ease-in-out infinite alternate; will-change:transform; }
@keyframes bruma-deriva{ from{transform:translate3d(-2%,-1.5%,0) scale(1.06)} to{transform:translate3d(2.5%,2%,0) scale(1.12)} }

.alderyn-stage.atm-ermo  { --aura:rgba(178,98,46,.34);  --fallback:radial-gradient(130% 100% at 50% 72%, #241710, #130d09 58%, #0a0806); }
.alderyn-stage.atm-mata  { --aura:rgba(72,150,98,.28);  --fallback:radial-gradient(130% 100% at 50% 60%, #122017, #0c130d 58%, #070a08); }
.alderyn-stage.atm-frio  { --aura:rgba(96,152,192,.28); --fallback:radial-gradient(130% 100% at 50% 55%, #14202b, #0c1219 58%, #080b0e); }
.alderyn-stage.atm-sangue{ --aura:rgba(170,74,66,.32);  --fallback:radial-gradient(130% 100% at 50% 58%, #2a1110, #160b0a 58%, #0a0606); }
.alderyn-stage.atm-corte { --aura:rgba(192,152,72,.28); --fallback:radial-gradient(130% 100% at 50% 50%, #221a0e, #14100a 58%, #0a0806); }
.pagina{
  position:relative; z-index:1; width:100%; max-width:min(1600px,96vw); box-sizing:border-box;
  height:100%; display:flex; flex-direction:column; overflow:hidden;
  background:
    radial-gradient(60% 50% at 6% 4%, rgba(60,42,20,.32), transparent 60%),
    radial-gradient(55% 45% at 96% 97%, rgba(50,35,18,.3), transparent 60%),
    linear-gradient(180deg, #19140d, #130f09);
  border:1px solid var(--regua2);
  box-shadow:inset 0 0 0 1px rgba(0,0,0,.4), 0 38px 100px -42px rgba(0,0,0,.8);
  padding:clamp(16px,2.2vw,30px) clamp(22px,3.4vw,48px); animation:rise .8s ease both;
}
.pagina::after{ content:""; position:absolute; inset:9px; border:1px solid var(--regua); pointer-events:none; z-index:0; }
/* So UMA tela visivel por vez (tela-jogo / tela-config). A .oculto (display:none)
   sai do flow do stage, deixando a outra centrada e em altura cheia. */
.tela{ position:relative; }
/* MIOLO: a UNICA zona que rola (cena + narracao). head/marg/scrawl ficam fixos. */
.miolo{ flex:1 1 auto; min-height:0; overflow-y:auto; overflow-x:hidden; position:relative; z-index:1; }
/* TELA DE CONFIG: app-shell dedicada; o conteudo respira numa coluna larga, centrada. */
.tela-config .head-config{ flex-wrap:wrap; }
.config-scroll{ padding-top:6px; }
.config-scroll > .config-tabs,
.config-scroll > .config-pane{ max-width:min(940px,96%); margin-left:auto; margin-right:auto; }
.config-scroll > .config-pane[data-pane="tela"]{ max-width:min(720px,96%); }
@keyframes rise{ from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:none} }
@keyframes arrive{ from{opacity:0;transform:translateY(9px)} to{opacity:1;transform:none} }
@keyframes pulseglow{ 0%{opacity:.45} 40%{opacity:1} 100%{opacity:.85} }

.head{ display:flex; align-items:center; gap:14px; position:relative; z-index:2; flex:none; }
.head .ttl{ font-family:"IM Fell English SC",serif !important; letter-spacing:.16em; font-size:14px; color:var(--osso); text-transform:lowercase; }
/* brasa do titulo: halo ambar respirando LENTISSIMO e minimo (opacity-only, atras do texto) */
.tela-jogo .head .ttl{ position:relative; z-index:0; }
.tela-jogo .head .ttl::after{ content:""; position:absolute; left:-10%; right:-10%; top:-40%; bottom:-40%; z-index:-1;
  background:radial-gradient(58% 100% at 50% 50%, rgba(198,122,51,.22), transparent 70%);
  opacity:0; pointer-events:none; animation:brasa-ttl 12s ease-in-out infinite; }
@keyframes brasa-ttl{ 0%,100%{opacity:0} 50%{opacity:.5} }
.head .fleur{ flex:none; opacity:.8; }
.head .ln{ flex:1; height:1px; background:var(--regua); }
/* CONTROLES = acessibilidade vence o tom (a atmosfera fica na cena). Secundarios:
   borda 2px ambar + texto claro + fundo translucido; hover preenche. >=44px. */
.head .sair{ font-family:"IM Fell English",serif; font-size:15px; letter-spacing:.04em;
  color:var(--osso); text-decoration:none; white-space:nowrap;
  border:2px solid var(--brasa); border-radius:6px; background:rgba(198,122,51,.10);
  min-height:44px; display:inline-flex; align-items:center; padding:0 16px;
  transition:background .2s ease, color .2s ease; }
.head .sair:hover{ background:var(--brasa); color:#140d04; }
.head .sair:focus-visible{ outline:2px solid #f0e6d2; outline-offset:2px; }
.head .selar{ font-family:"IM Fell English",serif; font-size:15px; letter-spacing:.04em;
  color:var(--osso); background:rgba(198,122,51,.10); border:2px solid var(--brasa);
  border-radius:6px; min-height:44px; padding:0 16px; cursor:pointer; white-space:nowrap;
  display:inline-flex; align-items:center; transition:background .2s ease, color .2s ease; }
.head .selar:hover{ background:var(--brasa); color:#140d04; }
.head .selar:focus-visible{ outline:2px solid #f0e6d2; outline-offset:2px; }
.head .engr{ font-family:"IM Fell English",serif; font-size:15px; letter-spacing:.04em; line-height:1; color:var(--osso);
  background:rgba(198,122,51,.10); border:2px solid var(--brasa); border-radius:6px; white-space:nowrap;
  min-height:44px; padding:0 16px; display:inline-flex; align-items:center; gap:8px;
  cursor:pointer; transition:background .2s ease, color .2s ease; }
.head .engr .ti{ font-size:20px; }
.head .engr:hover{ background:var(--brasa); color:#140d04; }
.head .engr:focus-visible{ outline:2px solid #f0e6d2; outline-offset:2px; }
/* oraculo: MESMO estilo dourado do grupo (espelha .engr) + olho coerente; vizinho do configuracoes */
.head .oraculo{ font-family:"IM Fell English",serif; font-size:15px; letter-spacing:.04em; line-height:1; color:var(--osso);
  background:rgba(198,122,51,.10); border:2px solid var(--brasa); border-radius:6px; white-space:nowrap; text-decoration:none;
  min-height:44px; padding:0 16px; display:inline-flex; align-items:center; gap:8px;
  cursor:pointer; transition:background .2s ease, color .2s ease; }
.head .oraculo .ti{ font-size:20px; }
.head .oraculo:hover{ background:var(--brasa); color:#140d04; }
.head .oraculo:focus-visible{ outline:2px solid #f0e6d2; outline-offset:2px; }
/* "voltar ao jogo" (tela de config): grande, alto contraste, no mesmo registro */
.head .voltar-jogo{ font-family:"IM Fell English",serif; font-size:15px; letter-spacing:.04em; color:var(--osso);
  background:rgba(198,122,51,.10); border:2px solid var(--brasa); border-radius:6px; white-space:nowrap;
  min-height:44px; padding:0 18px; display:inline-flex; align-items:center; gap:8px;
  cursor:pointer; transition:background .2s ease, color .2s ease; }
.head .voltar-jogo .ti{ font-size:20px; }
.head .voltar-jogo:hover{ background:var(--brasa); color:#140d04; }
.head .voltar-jogo:focus-visible{ outline:2px solid #f0e6d2; outline-offset:2px; }
.head .ttl-config{ font-size:18px; letter-spacing:.1em; }

/* marginalia: HOJE so a Pressao Emocional (0-10). Stats/Tensao ficam pro combate. */
.marg{ display:flex; align-items:center; justify-content:flex-end; gap:14px; flex-wrap:wrap; flex:none;
  margin-top:13px; padding-bottom:15px; border-bottom:1px solid var(--regua); position:relative; z-index:2; }
.bar{ width:42px; height:5px; border:0.8px solid var(--osso2); position:relative; background:rgba(0,0,0,.25); }
.bar>i{ display:block; height:100%; width:0; transition:width .7s ease, background .7s ease; }
.num{ font-family:"JetBrains Mono",monospace !important; font-size:13px; color:var(--osso) !important; font-variant-numeric:tabular-nums; letter-spacing:0; line-height:1; }

/* selo da Pressao Emocional */
.pressao{ display:flex; align-items:center; gap:8px; }
.pressao .plab{ font-family:"IM Fell English SC",serif !important; font-size:11px; letter-spacing:.18em; color:var(--osso2); text-transform:lowercase; }
.pressao .bar{ width:88px; }
.pressao .bar>i{ background:var(--osso2); }
.pressao .num{ color:var(--osso) !important; }
.pressao.alta .bar>i{ background:var(--t-sangue); }
.pressao.alta .num{ color:var(--t-sangue) !important; text-shadow:0 0 12px rgba(168,86,74,.4); }
.pressao.alta .plab{ color:var(--t-sangue); }

/* base pronta pro combate (nao exibida hoje) */
.stamps{ display:flex; gap:15px; flex-wrap:wrap; }
.st{ display:flex; align-items:center; gap:6px; }
.tens{ display:flex; align-items:center; gap:7px; }
.tens .lab{ font-family:"IM Fell English SC",serif !important; font-size:11px; letter-spacing:.18em; color:var(--osso2); text-transform:lowercase; }
.lz{ width:9px; height:9px; transform:rotate(45deg); border:0.9px solid var(--osso2); }
.lz.on{ background:var(--brasa); border-color:var(--brasa); }

.plate{ position:relative; z-index:2; margin:22px 0 6px; animation:plate-in 1.4s ease both; }
.plate .frame{ position:relative; border:1px solid var(--regua2); overflow:hidden; background:#0a0806; }
/* Ken Burns LENTISSIMO: scale 1 -> 1.04 num ciclo longo, ida e volta (transform-only,
   nao mexe no layout). O .frame ja tem overflow:hidden, entao o zoom nunca vaza. */
.plate img{ display:block; width:100%; height:clamp(216px,36vh,380px); object-fit:cover; object-position:55% 38%; filter:saturate(.92) contrast(1.02);
  transform-origin:52% 42%; animation:kenburns 26s ease-in-out 1s infinite alternate; will-change:transform; }
@keyframes plate-in{ from{opacity:0} to{opacity:1} }
@keyframes kenburns{ from{transform:scale(1)} to{transform:scale(1.04)} }
.plate .frame::after{ content:""; position:absolute; inset:0; pointer-events:none; box-shadow:inset 0 0 64px 12px rgba(10,8,6,.82), inset 0 0 0 1px rgba(0,0,0,.5); }
.plate .cap{ font-family:"IM Fell English",serif !important; font-style:italic; font-size:11.5px; color:var(--osso2); text-align:center; margin-top:7px; letter-spacing:.03em; }

.corpo{ max-width:min(720px,72ch); margin:22px auto 0; position:relative; z-index:2;
  font-size:clamp(17px,1.25vw,19px); line-height:1.72; text-align:justify; hyphens:auto; -webkit-hyphens:auto;
  font-family:"Spectral",Georgia,serif !important; color:var(--leitura); min-height:120px; }
.corpo p{ font-family:"Spectral",Georgia,serif !important; }
.corpo .glow{ position:relative; margin:0 0 1em; transition:color .8s ease; }
.corpo .glow::before{ content:""; position:absolute; inset:-12px -30px; z-index:-1; border-radius:20px;
  background:radial-gradient(70% 130% at 30% 42%, rgba(196,150,80,.085), transparent 70%); pointer-events:none; opacity:1; transition:opacity .9s ease; }
.corpo .glow p{ margin:0; }
.corpo .glow.faded{ color:var(--osso2); }
.corpo .glow.faded::before{ opacity:0; }
.corpo .glow.show{ animation:arrive .8s ease both; }
.corpo .glow.pulse::before{ animation:pulseglow 1.2s ease; }
.corpo .glow.done{ animation:none; opacity:1; transform:none; }

/* DIGITACAO ao vivo (stream): o texto escorre alinhado a esquerda e sem hifen (pra
   nao "dancar"); no fim o bloco vira .done e volta ao justify herdado do .corpo. O
   motor de revelacao vive no cliente (requestAnimationFrame). O caret pisca. */
.corpo .glow.streaming{ white-space:pre-wrap; text-align:left; hyphens:none; -webkit-hyphens:none; animation:none; }
.corpo .glow.streaming p{ margin:0; }
.caret{ display:inline-block; width:2px; height:1.05em; margin-left:1px; vertical-align:-2px;
  background:var(--brasa); animation:caretblink 1.05s steps(1,end) infinite; }
@keyframes caretblink{ 0%,55%{opacity:1} 56%,100%{opacity:0} }

/* eco do jogador - a acao dita, recuada e surda */
.corpo .glow.eco{ margin:0 0 1.2em; }
.eco-p{ font-family:"IM Fell English",serif !important; font-style:italic; color:var(--osso2);
  font-size:clamp(15px,1.05vw,16.5px); line-height:1.5; border-left:1px solid var(--regua);
  padding-left:14px; margin:0; }

/* voz do Fiador */
.fiador{ position:relative; display:flex; gap:13px; align-items:flex-start;
  padding:15px 17px; border-left:1px solid rgba(174,182,184,.34);
  background:linear-gradient(90deg, rgba(174,182,184,.05), transparent 70%); }
.fiador svg{ flex:none; margin-top:4px; }
.fline{ font-family:"IM Fell English",serif !important; font-style:italic; color:#d4d8d6;
  font-size:clamp(16.5px,1.2vw,18.5px); line-height:1.6; letter-spacing:.01em; margin:0; }

/* "o Cronista pondera..." */
.pondera{ font-family:"IM Fell English",serif !important; font-style:italic; color:var(--osso2);
  text-align:center; font-size:15px; letter-spacing:.02em; margin:14px 0 0; opacity:.85; position:relative; z-index:2; }
.pondera .ret span{ animation:pulsa 1.4s infinite ease-in-out; }
.pondera .ret span:nth-child(2){ animation-delay:.2s; }
.pondera .ret span:nth-child(3){ animation-delay:.4s; }
@keyframes pulsa{ 0%,100%{opacity:.2} 50%{opacity:.95} }

/* PORTAL DE ENTRADA (o ritual, no registro da Gravura) */
.portal{ text-align:center; padding:7vh 0 5vh; transition:opacity .7s ease, transform .7s ease; }
.portal.indo{ opacity:0; transform:translateY(-14px); }
.portal-nome{ font-family:"IM Fell English",serif !important; font-size:clamp(2.1rem,6.5vw,3.4rem);
  letter-spacing:.06em; color:var(--osso); line-height:1.1; }
.portal-traco{ width:6rem; height:1px; margin:1.4rem auto 0;
  background:linear-gradient(90deg, transparent, var(--regua2), transparent); }
/* PRIMARIO: preenchido ambar + texto escuro, na cara. */
.adentrar{ margin-top:2.6rem; font-family:"IM Fell English SC",serif !important;
  letter-spacing:.04em; text-transform:lowercase; font-size:18px; font-weight:600;
  color:#140d04; background:var(--brasa); border:2px solid var(--brasa); border-radius:6px;
  min-height:52px; padding:0 36px; cursor:pointer; transition:background .25s ease, box-shadow .25s ease; }
.adentrar:hover{ background:#e08a3e; border-color:#e08a3e; color:#140d04;
  box-shadow:0 0 26px rgba(198,122,51,.35); }
.adentrar:focus-visible{ outline:2px solid #f0e6d2; outline-offset:3px; }

/* a inscricao (input) - some ate Adentrar */
.scrawl{ display:flex; align-items:center; gap:12px; margin-top:20px; position:relative; z-index:2; flex:none; }
/* recomecar: secundario (borda 2px ambar) */
.scrawl .recomecar-btn{ font-family:"IM Fell English SC",serif !important; letter-spacing:.04em;
  text-transform:lowercase; font-size:15px; color:var(--osso); background:rgba(198,122,51,.10);
  border:2px solid var(--brasa); border-radius:6px; cursor:pointer; min-height:44px; padding:0 16px;
  transition:background .2s, color .2s; white-space:nowrap; }
.scrawl .recomecar-btn:hover{ background:var(--brasa); color:#140d04; }
.scrawl .recomecar-btn:focus-visible{ outline:2px solid #f0e6d2; outline-offset:2px; }
/* campo de comando: borda 2px clara, alto contraste, "digite aqui" */
.scrawl input{ flex:1; background:rgba(10,8,6,.55); border:2px solid var(--osso2);
  border-radius:6px; outline:none; color:var(--leitura);
  font-family:"Spectral",serif; font-size:17px; min-height:48px;
  padding:0 16px; box-shadow:none; transition:border-color .2s ease; }
.scrawl input::placeholder{ color:var(--osso); opacity:.85; font-style:italic; font-family:"IM Fell English",serif; }
.scrawl input:focus-visible, .scrawl.lit input{ border-color:var(--brasa); }
/* enviar: primario preenchido */
.scrawl button.send-btn{ background:var(--brasa); border:2px solid var(--brasa);
  border-radius:6px; color:#140d04; cursor:pointer; min-width:52px; min-height:48px;
  display:inline-flex; align-items:center; justify-content:center; transition:background .2s; }
.scrawl button.send-btn:hover{ background:#e08a3e; border-color:#e08a3e; }
.scrawl button.send-btn:focus-visible{ outline:2px solid #f0e6d2; outline-offset:2px; }
.scrawl button.send-btn svg{ width:24px; height:24px; }
/* desabilitado (defensivo): apagado mas mantem a FORMA de botao */
.scrawl button.send-btn:disabled, .scrawl button.send-btn[disabled]{
  background:rgba(198,122,51,.25); border-color:rgba(198,122,51,.45);
  color:rgba(20,13,4,.55); cursor:default; }

/* selo do modo mock */
.selo-mock{ position:fixed; top:.9rem; left:1rem; z-index:50;
  font-family:"IM Fell English SC",serif !important; font-size:.62rem; letter-spacing:.12em;
  text-transform:lowercase; color:var(--osso2); opacity:.6;
  border:1px dashed rgba(140,129,103,.5); border-radius:2px; padding:.2rem .55rem; background:rgba(14,11,8,.5); }

/* ===========================================================================
   CONFIGURACOES = TELA separada (.tela-config), nao mais overlay. O conteudo
   (abas, Fichas, Guia/Combate/Demo, controles) vive no .config-scroll rolavel.
   Casca CSS/JS pura, no mesmo registro da Gravura. Sem componentes ui.* novos.
   =========================================================================== */
.config-sec{ margin-bottom:22px; }
.config-sub{ font-family:"IM Fell English SC",serif !important; font-size:12px; letter-spacing:.18em;
  text-transform:lowercase; color:var(--osso2); margin:0 0 12px; padding-bottom:6px; border-bottom:1px solid var(--regua); }

/* cards de modelo (seletor de narracao) */
.modelo-cards{ display:flex; flex-direction:column; gap:9px; }
.mcard{ position:relative; display:block; width:100%; text-align:left; cursor:pointer;
  background:rgba(0,0,0,.22); border:1px solid var(--regua); padding:11px 13px;
  transition:border-color .25s ease, background .25s ease, box-shadow .25s ease; }
.mcard:hover{ border-color:var(--osso2); }
.mcard:focus-visible{ outline:none; border-color:var(--osso); box-shadow:0 0 0 2px rgba(205,191,159,.25); }
/* ATIVO = 3 sinais: borda brasa + borda dupla via inset box-shadow (engrossa SEM
   mudar a largura da borda -> sem pulo de layout) + fundo alaranjado mais forte. */
.mcard.ativo{ border-color:var(--brasa); background:rgba(198,122,51,.14); box-shadow:inset 0 0 0 1px var(--brasa); }
.mcard-top{ display:flex; align-items:baseline; gap:9px; flex-wrap:wrap; }
.mcard-nome{ font-family:"IM Fell English",serif !important; font-size:16px; color:var(--osso); }
.mcard-custo{ font-family:"IM Fell English SC",serif !important; font-size:10.5px; letter-spacing:.1em;
  text-transform:lowercase; color:var(--osso2); }
/* selo "em uso": empurrado pra direita no .mcard-top, so visivel no card ativo */
.mcard-selo{ display:none; margin-left:auto; align-self:center; font-family:"IM Fell English SC",serif !important;
  font-size:10px; letter-spacing:.08em; text-transform:lowercase; color:var(--brasa);
  border:1px solid var(--brasa); border-radius:10px; padding:1px 6px; white-space:nowrap; }
.mcard.ativo .mcard-selo{ display:inline-flex; }
.mcard-desc{ display:block; margin-top:4px; font-family:"Spectral",Georgia,serif !important;
  font-size:13px; color:var(--leitura); opacity:.78; line-height:1.45; }

/* "ver detalhes": gatilho do accordion (botao REAL dentro do card que virou <div>) */
.mcard-vermais{ display:inline-block; margin-top:8px; font-family:"IM Fell English SC",serif !important;
  font-size:10.5px; letter-spacing:.08em; text-transform:lowercase; color:var(--osso2);
  background:none; border:none; padding:0; cursor:pointer; text-decoration:underline;
  text-underline-offset:2px; transition:color .2s ease; }
.mcard-vermais:hover{ color:var(--brasa); }
/* bloco de detalhes: accordion deslizante, fechado por padrao */
.mcard-detalhe{ max-height:0; overflow:hidden; opacity:0; margin-top:0; padding-top:0; border-top:1px solid transparent;
  transition:max-height .35s ease, opacity .3s ease, margin-top .35s ease, padding-top .35s ease; }
.mcard.expandido .mcard-detalhe{ max-height:520px; opacity:1; margin-top:10px; padding-top:10px; border-top:1px solid var(--regua); }
.det-linha{ margin:0 0 6px; font-family:"Spectral",Georgia,serif !important; font-size:12.5px;
  color:var(--leitura); opacity:.85; line-height:1.5; }
.det-linha:last-child{ margin-bottom:0; }
.det-rotulo{ font-family:"IM Fell English SC",serif !important; font-size:10.5px; letter-spacing:.1em;
  text-transform:lowercase; color:var(--osso2); margin-right:6px; }

/* nota do tier fechado (Mythos), no rodape da secao Narracao */
.modelo-nota{ margin-top:12px; font-family:"IM Fell English",serif !important; font-style:italic;
  font-size:11.5px; color:var(--osso2); opacity:.8; line-height:1.5; }

/* linha generica: rotulo a esquerda, controle a direita */
.config-linha{ display:flex; align-items:center; justify-content:space-between; gap:14px; margin-bottom:12px; }
.config-rotulo{ font-family:"Spectral",Georgia,serif !important; font-size:14px; color:var(--leitura); opacity:.85; }

/* tamanho do texto: A- A A+ */
.txt-tam{ display:flex; gap:6px; }
.txt-tam .tbtn{ font-family:"IM Fell English",serif !important; color:var(--osso);
  background:rgba(198,122,51,.10); border:2px solid var(--brasa); border-radius:6px; cursor:pointer;
  min-width:48px; min-height:44px; padding:0 12px;
  transition:background .2s ease, color .2s ease; }
.txt-tam .tbtn:nth-child(1){ font-size:15px; }
.txt-tam .tbtn:nth-child(2){ font-size:18px; }
.txt-tam .tbtn:nth-child(3){ font-size:21px; }
.txt-tam .tbtn:hover{ background:var(--brasa); color:#140d04; }
.txt-tam .tbtn.ativo{ color:#140d04; background:var(--brasa); }
.txt-tam .tbtn:focus-visible{ outline:2px solid #f0e6d2; outline-offset:2px; }

/* toggle do modo foco */
.foco-toggle{ font-family:"IM Fell English SC",serif !important; letter-spacing:.04em; text-transform:lowercase;
  font-size:15px; color:var(--osso); background:rgba(198,122,51,.10); border:2px solid var(--brasa); cursor:pointer;
  border-radius:6px; min-height:44px; padding:0 16px; transition:background .2s ease, color .2s ease; }
.foco-toggle:hover{ background:var(--brasa); color:#140d04; }
.foco-toggle.on{ color:#140d04; background:var(--brasa); }
.foco-toggle:focus-visible{ outline:2px solid #f0e6d2; outline-offset:2px; }

/* TAMANHO DO TEXTO: 3 niveis fixos aplicados ao container da narracao (#corpo).
   A classe vive no <body> (ancestral estavel), entao vence o clamp do .corpo. */
body.txt-nivel-0 .corpo{ font-size:16px; }
body.txt-nivel-1 .corpo{ font-size:19px; }
body.txt-nivel-2 .corpo{ font-size:23px; line-height:1.8; }

/* MODO FOCO: esconde o cromo (header, marginalia, estampa, selo), deixa narracao + input.
   A moldura da folha tambem some pra leitura limpa. */
body.foco .tela-jogo .head, body.foco .tela-jogo .marg, body.foco .plate, body.foco .selo-mock{ display:none !important; }
body.foco .pagina{ border-color:transparent; box-shadow:none; }
body.foco .pagina::after{ display:none; }
.sair-foco{ display:none; position:fixed; top:14px; right:16px; z-index:55;
  font-family:"IM Fell English SC",serif !important; letter-spacing:.12em; text-transform:lowercase; font-size:.66rem;
  color:var(--osso2); background:rgba(14,11,8,.6); border:1px solid var(--regua); cursor:pointer; padding:.3rem .7rem;
  opacity:.5; transition:opacity .25s ease, color .25s ease; }
.sair-foco:hover{ opacity:1; color:var(--brasa); }
body.foco .sair-foco{ display:block; }

/* ===========================================================================
   ZONA DE DADOS (Balde 1): 2d10 + 2 criticos + 5 faixas. O Python e o cerebro; o
   dado so MOSTRA. Maquina: dormant(hidden) -> armed -> rolling -> resolved -> dormant.
   Paleta REAL (--brasa ambar, --t-sangue sangue, --osso osso); so transform/opacity
   nas animacoes; tom witcher-grey (lento, baixa amplitude), no espirito de plate-in/
   kenburns/arrive. Estados por data-estado; desenho do resultado por data-faixa.
   =========================================================================== */
.dado-zona{ position:relative; z-index:2; max-width:min(520px,92%); margin:24px auto 6px;
  display:flex; flex-direction:column; align-items:center; gap:12px;
  padding:18px 18px 20px; border-top:1px solid var(--regua);
  animation:dado-in .5s ease both; }
.dado-zona[hidden]{ display:none; }
.dado-cue{ font-family:"IM Fell English",serif !important; font-style:italic; font-size:14px;
  color:var(--osso2); letter-spacing:.02em; opacity:0; transition:opacity .6s ease; }
.dado-zona[data-estado="armed"] .dado-cue{ opacity:.9; }
.dado-par{ display:flex; gap:16px; }
/* DADO = losango d10 (escopado em .dado-zona; SEM classe .dado global colidente).
   clip-path corta borda E box-shadow -> os brilhos vao por filter:drop-shadow,
   que segue a forma do losango. Hex literais do prototipo, autorizados na zona. */
.dado-zona .dado{ width:62px; height:62px; display:flex; align-items:center; justify-content:center;
  clip-path:polygon(50% 0, 93% 50%, 50% 100%, 7% 50%);
  background:linear-gradient(145deg,#F7C871,#D58A20);
  color:#2a2008; font-family:"Spectral",Georgia,serif !important; font-size:25px; font-weight:700; line-height:1;
  filter:drop-shadow(0 3px 7px rgba(0,0,0,.45));
  transition:background .4s ease, color .4s ease, filter .5s ease; }
@media (max-width:480px){ .dado-zona .dado{ width:52px; height:52px; font-size:22px; } }
.dado-conta{ font-family:"JetBrains Mono",monospace !important; font-size:14px; color:var(--osso);
  letter-spacing:0; min-height:18px; }
.dado-faixa{ font-family:"IM Fell English SC",serif !important; font-size:14px; letter-spacing:.12em;
  text-transform:lowercase; color:var(--osso); min-height:18px; text-align:center; }
/* botao: primario ambar, alto contraste, foco visivel (acessibilidade vence o tom) */
.dado-btn{ position:relative; font-family:"IM Fell English SC",serif !important; letter-spacing:.06em;
  text-transform:lowercase; font-size:16px; font-weight:600; color:#140d04; background:var(--brasa);
  border:2px solid var(--brasa); border-radius:6px; min-height:46px; padding:0 30px; cursor:pointer;
  transition:background .25s ease, box-shadow .25s ease, opacity .25s ease; }
.dado-btn:hover{ background:#e08a3e; border-color:#e08a3e; box-shadow:0 0 22px rgba(198,122,51,.32); }
.dado-btn:focus-visible{ outline:2px solid #f0e6d2; outline-offset:3px; }
.dado-btn:disabled{ background:rgba(198,122,51,.22); border-color:rgba(198,122,51,.40);
  color:rgba(20,13,4,.55); cursor:default; box-shadow:none; }
/* armed: botao em destaque (halo ambar pulsando = opacity only) */
.dado-zona[data-estado="armed"] .dado-btn::after{ content:""; position:absolute; inset:-4px; border-radius:9px;
  box-shadow:0 0 18px rgba(198,122,51,.5); opacity:0; pointer-events:none;
  animation:dado-pulsebtn 2.2s ease-in-out infinite; }
/* rolling: os dados GIRAM (classe .rolling via JS); resolved: pousam */
.dado-zona .dado.rolling{ animation:spin10 .17s linear infinite; }
.dado-zona[data-estado="resolved"] .dado{ animation:dado-land .42s ease both; }

/* camada-palco: clarao + raio (Kokusen), fio (parcial), sangue (falha critica).
   overflow visivel pro raio e as fagulhas saltarem alem da caixa. */
.dado-fx{ position:absolute; inset:0; pointer-events:none; overflow:visible; }
.dado-fx > span{ position:absolute; opacity:0; }
.fx-clarao{ inset:0; z-index:1;
  background:radial-gradient(closest-side, rgba(255,236,180,.92), rgba(240,169,60,.4) 45%, transparent 75%); }
.fx-raio{ left:50%; top:-10%; width:3px; height:120%; transform-origin:top; z-index:1;
  background:linear-gradient(180deg, transparent, #ECC972, #fff7e0, #ECC972, transparent);
  box-shadow:0 0 18px rgba(247,206,120,.85); }
.fx-fio{ left:6%; right:6%; top:54%; height:1.5px; transform-origin:left; transform:scaleX(0);
  background:linear-gradient(90deg, transparent, var(--t-sangue), transparent); }
.fx-sangue{ inset:0; box-shadow:inset 0 0 26px 6px rgba(168,86,74,.5); }
/* fagulhas do Kokusen: 16 spans criados via JS, removidos em ~1.15s */
.dado-fx .koku-spark{ position:absolute; width:5px; height:5px; border-radius:50%; bottom:32%; z-index:3;
  background:radial-gradient(circle,#fff3cf,#F0A93C); box-shadow:0 0 8px rgba(247,206,120,.9);
  opacity:0; animation:kokuspark 1s ease-out forwards; }

/* ---- desenho por faixa (resolved) ---- */
/* sucesso_critico = KOKUSEN: dados ACENDEM + palco treme + clarao + raio + fagulhas(JS). SEM x2,5. */
.dado-zona[data-faixa="sucesso_critico"]{ animation:kokushake .5s ease both; }
.dado-zona[data-faixa="sucesso_critico"] .dado{ background:linear-gradient(145deg,#FFE9A8,#F0A93C);
  filter:drop-shadow(0 3px 7px rgba(0,0,0,.45)) drop-shadow(0 0 16px rgba(247,206,120,.82)); }
.dado-zona[data-faixa="sucesso_critico"] .dado-faixa{ color:var(--brasa); }
.dado-zona[data-faixa="sucesso_critico"] .fx-clarao{ animation:kokuflash .7s ease-out both; }
.dado-zona[data-faixa="sucesso_critico"] .fx-raio{ animation:kokuray .62s ease-out both; }
/* sucesso: brilho ambar calmo */
.dado-zona[data-faixa="sucesso"] .dado{ filter:drop-shadow(0 3px 7px rgba(0,0,0,.45)) drop-shadow(0 0 12px rgba(198,122,51,.5)); }
.dado-zona[data-faixa="sucesso"] .dado-faixa{ color:var(--brasa); }
/* sucesso_parcial: ambar + fio fino de --t-sangue cruzando (a alma do tom) */
.dado-zona[data-faixa="sucesso_parcial"] .dado{ filter:drop-shadow(0 3px 7px rgba(0,0,0,.45)) drop-shadow(0 0 10px rgba(198,122,51,.4)); }
.dado-zona[data-faixa="sucesso_parcial"] .dado-faixa{ color:var(--t-ambar); }
.dado-zona[data-faixa="sucesso_parcial"] .fx-fio{ animation:fx-fio 1.2s ease .2s both; }
/* falha: esfria pra cinza/--osso, sem drama */
.dado-zona[data-faixa="falha"] .dado{ filter:grayscale(.66) brightness(.82) drop-shadow(0 3px 7px rgba(0,0,0,.45)); }
.dado-zona[data-faixa="falha"] .dado-faixa{ color:var(--osso2); }
/* falha_critica = A QUEDA: dados RUBI caem (faildrop) + borda sangrando. SEM flash/raio/fagulhas. */
.dado-zona[data-faixa="falha_critica"] .dado{ background:linear-gradient(145deg,#e87f8a,#c63e4d); color:#2a0c0f;
  animation:faildrop .45s ease both; }
.dado-zona[data-faixa="falha_critica"] .dado-faixa{ color:var(--t-sangue); }
.dado-zona[data-faixa="falha_critica"] .fx-sangue{ animation:fx-sangue 1.5s ease both; }

@keyframes dado-in{ from{opacity:0; transform:translateY(8px)} to{opacity:1; transform:none} }
@keyframes dado-pulsebtn{ 0%,100%{opacity:0} 50%{opacity:.8} }
@keyframes dado-land{ 0%{transform:scale(1.12)} 60%{transform:scale(.97)} 100%{transform:scale(1)} }
@keyframes spin10{ 0%{transform:rotate(-9deg) scale(1)} 50%{transform:rotate(9deg) scale(1.06)} 100%{transform:rotate(-9deg) scale(1)} }
@keyframes faildrop{ 0%{transform:translateY(-7px) rotate(-6deg)} 55%{transform:translateY(2px) rotate(3deg)} 100%{transform:translateY(0) rotate(0)} }
@keyframes kokushake{ 0%,100%{transform:translateX(0)} 20%{transform:translateX(-3px)} 40%{transform:translateX(3px)} 60%{transform:translateX(-2px)} 80%{transform:translateX(2px)} }
@keyframes kokuflash{ 0%{opacity:0} 12%{opacity:1} 100%{opacity:0} }
@keyframes kokuray{ 0%{opacity:0; transform:translateX(-50%) scaleY(0)} 18%{opacity:1} 60%{opacity:1; transform:translateX(-50%) scaleY(1)} 100%{opacity:0; transform:translateX(-50%) scaleY(1)} }
@keyframes kokuspark{ 0%{opacity:0; transform:translate(0,0) scale(.6)} 15%{opacity:1} 100%{opacity:0; transform:translate(var(--dx,0px),-118px) scale(1)} }
@keyframes fx-fio{ 0%{opacity:0; transform:scaleX(0)} 30%{opacity:.85} 100%{opacity:.8; transform:scaleX(1)} }
@keyframes fx-sangue{ 0%{opacity:0} 35%{opacity:1} 100%{opacity:.7} }

@media (prefers-reduced-motion:reduce){
  .pagina, .corpo .glow.show{ animation:none; }
  .caret{ animation:none; opacity:.7; }   /* o motor revela tudo de uma vez; caret estatico */
  .pondera .ret span{ animation:none; }
  .alderyn-stage::after{ animation:none; }
  /* atmosfera da tela do jogo: tudo PARADO no estado final */
  .plate, .plate img, .bruma{ animation:none; }
  .tela-jogo .head .ttl::after{ animation:none; opacity:0; }
  /* ZONA DE DADOS: sem giro, sem clarao/sangue animados. Dados pulam pros valores
     (o JS nao gira em reduced); cada faixa vira ESTADO DE COR estatico + rotulo.
     A maquina de estados e o botao continuam funcionando. Seletores na MESMA
     specificity (0,3,x) das regras-base, e DEPOIS delas, pra realmente vencer. */
  .dado-zona{ animation:none; }
  .dado-zona[data-faixa]{ animation:none; }                                  /* mata kokushake */
  .dado-zona[data-estado] .dado, .dado-zona[data-faixa] .dado, .dado-zona .dado.rolling{ animation:none; }
  .dado-zona[data-estado="armed"] .dado-btn::after{ animation:none; }
  .dado-zona[data-faixa] .dado-fx > span, .dado-fx .koku-spark{ animation:none; }
  .dado-zona .dado-cue{ transition:none; }
  /* estados FINAIS estaticos: o look por data-faixa (bg/filter dos dados) ja e estatico
     -> dados acesos / rubi / cinza + rotulo permanecem; so a cinetica some. */
  .dado-zona[data-faixa="sucesso_parcial"] .fx-fio{ opacity:.8; transform:scaleX(1); }
  .dado-zona[data-faixa="falha_critica"] .fx-sangue{ opacity:.7; }
}

/* ====== FICHAS DE NARRADOR (controle gamificado; acessivel, alto contraste) ====== */
.fichas{ display:flex; flex-direction:column; gap:12px; }
.ficha{ border:2px solid var(--regua2); border-radius:8px; background:rgba(12,10,8,.5);
  padding:14px 16px; cursor:pointer; transition:border-color .2s ease, background .2s ease; }
.ficha:hover{ border-color:var(--osso2); }
.ficha:focus-visible{ outline:2px solid #f0e6d2; outline-offset:2px; }
.ficha.ativo{ border-color:var(--brasa); background:rgba(198,122,51,.12);
  box-shadow:inset 0 0 0 1px var(--brasa); }
.ficha-head{ display:flex; align-items:center; gap:12px; }
.ficha-ico{ font-size:30px; color:var(--brasa); flex:none; line-height:1; }
.ficha-id{ display:flex; flex-direction:column; gap:1px; flex:1; min-width:0; }
.ficha-nome{ font-family:"IM Fell English",serif !important; font-size:20px; color:var(--osso); line-height:1.1; }
.ficha-epiteto{ font-family:"Spectral",serif !important; font-style:italic; font-size:13px; color:var(--osso2); }
.ficha-selo{ font-family:"IM Fell English SC",serif !important; font-size:10.5px; letter-spacing:.1em;
  text-transform:lowercase; padding:3px 9px; border-radius:4px; white-space:nowrap; flex:none; }
.ficha-selo.rec{ background:var(--brasa); color:#140d04; }
.ficha-selo.eq, .ficha-selo.eco{ border:1px solid var(--brasa); color:var(--osso); }
.ficha-selo.myth{ border:1px solid #b9a36a; color:#d8c184; }
.ficha-attrs{ display:flex; flex-direction:column; gap:6px; margin-top:12px; }
.attr{ display:flex; align-items:center; gap:10px; }
.attr-lbl{ font-family:"IM Fell English SC",serif !important; font-size:11px; letter-spacing:.08em;
  color:var(--leitura); width:104px; flex:none; }
.bars{ display:flex; gap:4px; }
.bars .seg{ width:22px; height:9px; border-radius:2px; background:rgba(205,191,159,.14); }
.bars .seg.on.ambar{ background:var(--brasa); }
.bars .seg.on.sangue{ background:var(--t-sangue); }
.ficha-desc{ font-family:"Spectral",Georgia,serif !important; font-size:13.5px; color:var(--leitura);
  line-height:1.55; margin-top:12px; }
.ficha-quando{ font-family:"Spectral",serif !important; font-size:13px; color:var(--osso2);
  font-style:italic; margin-top:8px; }
.ficha-quando b{ font-style:normal; color:var(--osso); }
.ficha-aviso{ font-family:"Spectral",serif !important; font-size:12.5px; color:var(--t-sangue);
  background:rgba(168,86,74,.1); border:1px solid rgba(168,86,74,.4); border-radius:5px;
  padding:7px 10px; margin-top:10px; display:flex; gap:7px; align-items:flex-start; line-height:1.45; }
.ficha-aviso .ti{ flex:none; font-size:16px; margin-top:1px; }
.ficha-ctrls{ display:flex; align-items:center; gap:12px; flex-wrap:wrap; margin-top:12px; }
.ficha-ver-lbl{ font-family:"IM Fell English SC",serif !important; font-size:11px; letter-spacing:.08em;
  color:var(--osso2); display:flex; align-items:center; gap:7px; }
.ficha-ver{ font-family:"Spectral",serif !important; font-size:14px; color:var(--leitura);
  background:rgba(10,8,6,.6); border:2px solid var(--osso2); border-radius:6px; padding:7px 10px;
  min-height:40px; cursor:pointer; }
.ficha-ex-btn{ font-family:"IM Fell English SC",serif !important; font-size:13px; letter-spacing:.04em;
  text-transform:lowercase; color:var(--osso); background:rgba(198,122,51,.10);
  border:2px solid var(--brasa); border-radius:6px; min-height:40px; padding:0 14px; cursor:pointer;
  transition:background .2s ease, color .2s ease; }
.ficha-ex-btn:hover{ background:var(--brasa); color:#140d04; }
.ficha-ex-btn:focus-visible, .ficha-ver:focus-visible{ outline:2px solid #f0e6d2; outline-offset:2px; }
.ficha-ex{ margin-top:10px; border-left:2px solid var(--brasa); padding:8px 0 4px 14px; }
.ficha-ex[hidden]{ display:none; }
.ficha-ex p{ font-family:"Spectral",Georgia,serif !important; font-size:13.5px; color:var(--leitura);
  line-height:1.62; font-style:italic; margin:0; }

/* ====== ABAS DO PAINEL (Narrador / Guia / Tela) ====== */
.config-tabs{ display:flex; gap:6px; margin-bottom:18px; border-bottom:1px solid var(--regua); }
.config-tab{ font-family:"IM Fell English SC",serif !important; letter-spacing:.08em; font-size:14px;
  color:var(--osso2); background:none; border:none; border-bottom:3px solid transparent;
  padding:10px 14px; min-height:44px; cursor:pointer; transition:color .2s ease, border-color .2s ease; }
.config-tab:hover{ color:var(--osso); }
.config-tab.ativo{ color:var(--osso); border-bottom-color:var(--brasa); }
.config-tab:focus-visible{ outline:2px solid #f0e6d2; outline-offset:2px; }
.config-pane[hidden]{ display:none; }
.guia-intro{ font-family:"Spectral",Georgia,serif !important; font-style:italic; font-size:13px;
  color:var(--osso2); line-height:1.5; margin:0 0 16px; }

/* ====== GUIA: 6 cartas de referencia ====== */
.guia{ display:flex; flex-direction:column; gap:14px; }
.g-card{ border:2px solid var(--regua2); border-radius:8px; background:rgba(12,10,8,.5); padding:14px 16px; }
.g-head{ display:flex; align-items:center; gap:12px; }
.g-ico{ font-size:28px; color:var(--brasa); flex:none; line-height:1; }
.g-id{ display:flex; flex-direction:column; gap:1px; }
.g-titulo{ font-family:"IM Fell English",serif !important; font-size:19px; color:var(--osso); line-height:1.1; }
.g-sub{ font-family:"Spectral",serif !important; font-style:italic; font-size:12.5px; color:var(--osso2); }
.g-txt{ font-family:"Spectral",Georgia,serif !important; font-size:13.5px; color:var(--leitura); line-height:1.55; margin:12px 0 0; }
.g-fecho{ font-family:"Spectral",serif !important; font-style:italic; font-size:13px; color:var(--osso); line-height:1.5;
  margin:10px 0 0; border-left:2px solid var(--brasa); padding-left:12px; }
/* pilares */
.g-pilares{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:9px; margin-top:12px; }
.g-pilar{ border:1px solid; border-left-width:4px; border-radius:6px; background:rgba(10,8,6,.4); padding:9px 11px;
  display:flex; flex-direction:column; gap:3px; }
.g-pilar i{ font-size:22px; }
.g-pnome{ font-family:"IM Fell English SC",serif !important; letter-spacing:.1em; font-size:12px; color:var(--osso); }
.g-pln{ font-family:"Spectral",serif !important; font-size:12px; color:var(--leitura); line-height:1.45; }
/* barras */
.g-barras{ display:flex; flex-direction:column; gap:11px; margin-top:12px; }
.g-barra{ display:flex; flex-direction:column; gap:5px; }
.g-blbl{ display:flex; align-items:center; gap:9px; }
.g-bnome{ font-family:"IM Fell English SC",serif !important; letter-spacing:.08em; font-size:12px; }
.g-bwarn{ font-family:"Spectral",serif !important; font-style:italic; font-size:11px; color:var(--t-sangue);
  border:1px solid rgba(168,86,74,.5); border-radius:3px; padding:1px 6px; }
.g-btrack{ height:11px; border-radius:3px; background:rgba(205,191,159,.12); overflow:hidden; }
.g-bfill{ display:block; height:100%; border-radius:3px; }
.g-barra.inv .g-btrack{ display:flex; justify-content:flex-end; }
.g-btxt{ font-family:"Spectral",serif !important; font-size:12.5px; color:var(--osso2); line-height:1.45; margin:0; }
/* rolagem */
.g-roll{ display:flex; gap:16px; margin-top:12px; }
.g-d10{ font-family:"IM Fell English",serif !important; font-size:16px; color:var(--osso); display:flex; align-items:center; gap:6px; }
.g-d10 i{ font-size:26px; color:var(--brasa); }
.g-regua{ display:flex; align-items:center; gap:10px; margin-top:12px; }
.g-rlbl{ font-family:"IM Fell English SC",serif !important; font-size:11px; letter-spacing:.06em; color:var(--osso2); white-space:nowrap; }
.g-rbar{ flex:1; height:12px; border-radius:6px; position:relative;
  background:linear-gradient(90deg, #5a3030, #6a5028 45%, #5a6a3a); overflow:hidden; }
.g-rcusto{ position:absolute; left:38%; width:24%; top:0; bottom:0; background:rgba(198,122,51,.5);
  border-left:1px solid var(--osso2); border-right:1px solid var(--osso2); }
.g-rcaption{ font-family:"Spectral",serif !important; font-style:italic; font-size:11.5px; color:var(--osso2); text-align:center; margin-top:5px; }
/* medidores */
.g-medrow{ display:flex; gap:16px; margin-top:12px; flex-wrap:wrap; }
.g-medcol{ flex:1; min-width:132px; display:flex; flex-direction:column; gap:6px; }
.g-medcap{ font-family:"IM Fell English SC",serif !important; letter-spacing:.06em; font-size:12px; color:var(--osso); display:flex; align-items:center; gap:6px; }
.g-medsub{ font-family:"Spectral",serif !important; font-style:italic; font-size:11.5px; color:var(--osso2); }
.g-divida{ height:13px; border-radius:4px; background:rgba(205,191,159,.12); overflow:hidden; }
.g-dfill{ display:block; width:72%; height:100%; background:linear-gradient(90deg, var(--brasa), var(--t-sangue)); }
.g-dissol{ min-height:34px; display:flex; align-items:center; justify-content:center;
  font-family:"Spectral",serif !important; font-style:italic; font-size:12px; color:var(--osso2);
  border:1px dashed var(--regua2); border-radius:4px; filter:blur(.4px); opacity:.85; }
.g-med{ height:13px; border-radius:4px; background:rgba(205,191,159,.12); overflow:hidden; }
.g-med i{ display:block; height:100%; }
.g-med.tensao i{ background:var(--brasa); }
.g-med.pressao i{ background:#8a7488; }
/* rolo da medula */
.g-medula{ display:flex; align-items:center; justify-content:center; gap:22px; padding:14px 0; margin-top:8px; color:var(--osso2); }
.g-medula i{ font-size:40px; }
.g-medula i:first-child{ color:var(--brasa); }

/* ====== GUIA: sub-secoes + O COMBATE ====== */
.g-secao{ font-family:"IM Fell English",serif !important; font-size:17px; color:var(--brasa);
  letter-spacing:.02em; margin:6px 0 12px; padding-bottom:6px; border-bottom:1px solid var(--regua2); }
.guia-grupo{ display:flex; flex-direction:column; gap:14px; margin-bottom:24px; }
.g-abertura{ font-family:"Spectral",Georgia,serif !important; font-size:13.5px; color:var(--leitura); line-height:1.55; margin:0 0 8px; }
.g-tensao-ref{ font-family:"Spectral",serif !important; font-style:italic; font-size:12px; color:var(--osso2); margin:0 0 14px; }
/* A - economia: pips de acao (cheios x gastos) */
.g-acoes{ display:flex; align-items:center; gap:7px; flex-wrap:wrap; margin-top:12px; }
.g-acao{ width:16px; height:16px; border-radius:50%; flex:none; }
.g-acao.on{ background:var(--brasa); }
.g-acao.spent{ background:none; border:2px solid var(--regua2); }
.g-acoes-lbl{ font-family:"Spectral",serif !important; font-style:italic; font-size:12px; color:var(--osso2); margin-left:6px; }
/* B - guarda que ENCHE + quebra */
.g-guarda-row{ display:flex; gap:24px; align-items:flex-end; margin-top:12px; }
.g-guarda-col{ display:flex; flex-direction:column; align-items:center; gap:6px; }
.g-gcap{ font-family:"IM Fell English SC",serif !important; font-size:11px; letter-spacing:.08em; color:var(--osso2); }
.g-gcap.quebra{ color:var(--t-sangue); }
.g-guarda{ width:30px; height:70px; border:1px solid var(--regua2); border-radius:4px; display:flex; align-items:flex-end; overflow:hidden; }
.g-guarda i{ display:block; width:100%; background:var(--brasa); }
.g-guarda.cheia{ border-color:var(--t-sangue); box-shadow:0 0 12px rgba(168,86,74,.5); }
.g-guarda.cheia i{ background:var(--t-sangue); }
/* C - ritmo: rapida/firme/pesada */
.g-ritmo{ display:flex; gap:10px; margin-top:12px; flex-wrap:wrap; }
.g-ritmo-c{ flex:1; min-width:96px; border:1px solid var(--regua2); border-radius:6px; padding:10px;
  display:flex; flex-direction:column; align-items:center; gap:6px; background:rgba(10,8,6,.4); }
.g-rnome{ font-family:"IM Fell English",serif !important; font-size:15px; color:var(--osso); }
.g-pips{ display:flex; gap:4px; }
.g-pip{ width:9px; height:9px; border-radius:50%; border:1px solid var(--osso2); }
.g-pip.on{ background:var(--brasa); border-color:var(--brasa); }
.g-rrisco{ font-family:"Spectral",serif !important; font-style:italic; font-size:11px; color:var(--osso2); }
/* D - matriz Posicao x Efeito */
.g-matriz{ display:grid; grid-template-columns:auto 1fr 1fr 1fr; gap:4px; margin-top:12px; }
.g-mh{ font-family:"IM Fell English SC",serif !important; font-size:10.5px; letter-spacing:.05em; color:var(--osso2); text-align:center; padding:4px 2px; }
.g-mr{ font-family:"IM Fell English SC",serif !important; font-size:10.5px; letter-spacing:.05em; color:var(--osso2); display:flex; align-items:center; padding-right:6px; }
.g-mc{ height:30px; border:1px solid var(--regua2); border-radius:4px; background:rgba(205,191,159,.05); }
.g-mc.alta{ border-color:var(--t-sangue); background:rgba(168,86,74,.18); color:var(--t-sangue);
  display:flex; align-items:center; justify-content:center; font-family:"IM Fell English SC",serif !important;
  font-size:10px; letter-spacing:.05em; text-align:center; line-height:1.1; }
/* E - cartao de ferimento */
.g-ferimento{ display:flex; align-items:center; gap:12px; margin-top:12px; padding:11px 13px;
  border:1px solid var(--t-sangue); border-left:4px solid var(--t-sangue); border-radius:6px; background:rgba(168,86,74,.08); }
.g-ferimento i{ font-size:24px; color:var(--t-sangue); flex:none; }
.g-fnome{ display:block; font-family:"IM Fell English",serif !important; font-size:15px; color:var(--osso); }
.g-fefeito{ display:block; font-family:"Spectral",serif !important; font-style:italic; font-size:12.5px; color:var(--leitura); }
/* F - vinculo + intervencoes */
.g-vinculo-wrap{ display:flex; flex-direction:column; gap:8px; margin-top:12px; }
.g-vcap{ font-family:"IM Fell English SC",serif !important; font-size:11px; letter-spacing:.08em; color:var(--osso); }
.g-vinculo{ height:12px; border-radius:4px; background:rgba(205,191,159,.12); overflow:hidden; }
.g-vinculo i{ display:block; height:100%; background:linear-gradient(90deg,var(--brasa),#d8c184); }
.g-chips{ display:flex; gap:8px; flex-wrap:wrap; }
.g-chip{ font-family:"Spectral",serif !important; font-size:12px; color:var(--osso); display:flex; align-items:center; gap:5px;
  border:1px solid var(--brasa); border-radius:14px; padding:4px 11px; background:rgba(198,122,51,.08); }
.g-chip i{ font-size:14px; color:var(--brasa); }
.g-vsub{ font-family:"Spectral",serif !important; font-style:italic; font-size:11.5px; color:var(--osso2); }
/* G - timeline round a round */
.g-tl-intro{ font-family:"Spectral",serif !important; font-style:italic; font-size:13px; color:var(--osso); line-height:1.5; margin:12px 0; }
.g-timeline{ display:flex; flex-direction:column; gap:10px; border-left:2px solid var(--regua2); padding-left:14px; }
.g-round{ display:flex; gap:11px; align-items:flex-start; }
.g-round i{ font-size:22px; color:var(--brasa); flex:none; margin-top:2px; }
.g-round.quebra i{ color:var(--t-sangue); }
.g-rlabel{ display:block; font-family:"IM Fell English SC",serif !important; font-size:11px; letter-spacing:.1em; color:var(--osso2); margin-bottom:2px; }
.g-round.quebra .g-rlabel{ color:var(--t-sangue); }
.g-round p{ font-family:"Spectral",Georgia,serif !important; font-size:13px; color:var(--leitura); line-height:1.5; margin:0; }

/* ====== NUMEROS DE EXEMPLO: selo + nota + rodape ====== */
.selo-ilus{ display:inline-flex; align-items:center; gap:5px; font-family:"Spectral",serif !important;
  font-size:11px; font-style:italic; color:var(--brasa); border:1px solid var(--brasa); border-radius:12px;
  padding:2px 9px; background:rgba(198,122,51,.08); white-space:nowrap; }
.selo-ilus i{ font-size:13px; font-style:normal; }
.num-nota{ border:1px solid var(--brasa); border-left:4px solid var(--brasa); border-radius:6px;
  background:rgba(198,122,51,.07); padding:11px 14px; margin:0 0 16px; display:flex; flex-direction:column; gap:7px; align-items:flex-start; }
.num-nota-txt{ font-family:"Spectral",Georgia,serif !important; font-size:13px; color:var(--leitura); line-height:1.5; margin:0; }
.num-perso{ font-family:"Spectral",serif !important; font-size:12.5px; color:var(--osso2); line-height:1.5; margin:0; }
.num-perso b{ color:var(--osso); }
.ex-foot{ margin-top:13px; border-top:1px solid var(--regua2); padding-top:10px; }
.ex-foot-top{ display:flex; align-items:center; gap:9px; margin-bottom:6px; flex-wrap:wrap; }
.ex-foot-lbl{ font-family:"IM Fell English SC",serif !important; font-size:11px; letter-spacing:.1em; color:var(--osso); }
.ex-foot-body{ font-family:"Spectral",Georgia,serif !important; font-size:12.5px; color:var(--leitura); line-height:1.55; }
.ex-foot-body b{ color:var(--brasa); font-style:normal; }

/* ====== DEMONSTRACAO ANIMADA ====== */
.demo-card{ border-color:var(--brasa); box-shadow:inset 0 0 0 1px rgba(198,122,51,.25); }
.demo-estado{ display:grid; grid-template-columns:repeat(auto-fit,minmax(184px,1fr)); gap:9px 18px; margin:12px 0 14px; }
.demo-meter{ display:flex; align-items:center; gap:8px; }
.demo-mlbl{ font-family:"IM Fell English SC",serif !important; font-size:10.5px; letter-spacing:.04em; color:var(--osso2); width:118px; flex:none; }
.demo-mtrack{ flex:1; height:9px; border-radius:3px; background:rgba(205,191,159,.12); overflow:hidden; }
.demo-mfill{ display:block; height:100%; border-radius:3px; transition:width .8s ease, background .5s ease; }
.demo-mtrack.quebrou{ box-shadow:inset 0 0 0 1px var(--t-sangue), 0 0 10px rgba(168,86,74,.55); }
.demo-mval{ font-family:"JetBrains Mono",monospace !important; font-size:11px; color:var(--leitura); width:54px; text-align:right; flex:none; }
.demo-acoes{ display:flex; gap:6px; flex:1; }
.demo-passos{ list-style:none; margin:6px 0 0; padding:0; display:flex; flex-direction:column; gap:9px;
  border-left:2px solid var(--regua2); padding-left:14px; }
.demo-passo{ font-family:"Spectral",Georgia,serif !important; }
.demo-passo p{ font-size:13px; color:var(--leitura); line-height:1.55; margin:0; }
.demo-passo b{ color:var(--osso); }
.demo-final{ margin-top:4px; padding-top:8px; border-top:1px solid var(--regua2); display:flex; flex-direction:column; gap:7px; align-items:flex-start; }
.demo-final p{ font-style:italic; color:var(--osso2); }
.demo-tag{ display:inline-block; font-size:11px; font-style:italic; color:var(--brasa);
  border:1px solid var(--brasa); border-radius:4px; padding:1px 7px; margin-left:4px; }
.demo-tag.usado{ color:var(--t-sangue); border-color:var(--t-sangue); text-decoration:line-through; }
.demo-selo{ display:inline-block; font-family:"IM Fell English SC",serif !important; font-size:10px; letter-spacing:.06em;
  border-radius:4px; padding:2px 7px; margin-left:5px; }
.demo-selo.desesp, .demo-selo.grande{ color:var(--t-sangue); border:1px solid var(--t-sangue); background:rgba(168,86,74,.1); }
.demo-selo.exposto{ color:#140d04; background:var(--brasa); }
.demo-dados{ display:inline-flex; gap:5px; vertical-align:middle; }
.demo-dado{ display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px;
  font-family:"JetBrains Mono",monospace !important; font-size:13px; color:var(--osso); border:1px solid var(--brasa);
  border-radius:5px; background:rgba(198,122,51,.08); }
.demo-num{ color:var(--brasa); }
.demo-num.dano{ color:var(--t-sangue); font-size:16px; }
.demo-acerto{ display:inline-flex; align-items:center; gap:4px; font-family:"IM Fell English SC",serif !important;
  font-size:11px; letter-spacing:.08em; color:#140d04; background:var(--brasa); border-radius:4px; padding:2px 8px; margin:0 4px; }
.demo-quebra-txt{ color:var(--t-sangue); }
.demo-replay{ margin-top:14px; display:inline-flex; align-items:center; gap:7px; font-family:"IM Fell English SC",serif !important;
  font-size:13px; letter-spacing:.04em; text-transform:lowercase; color:var(--osso); background:rgba(198,122,51,.1);
  border:2px solid var(--brasa); border-radius:6px; min-height:44px; padding:0 16px; cursor:pointer; transition:background .2s ease, color .2s ease; }
.demo-replay:hover{ background:var(--brasa); color:#140d04; }
.demo-replay:focus-visible{ outline:2px solid #f0e6d2; outline-offset:2px; }
.demo-replay i{ font-size:16px; }

/* ====== ANIMACOES DE APOIO (entrada): so com .go no ancestral (JS). reduced-motion
   nao adiciona .go, entao os elementos ficam no estado final estatico. ====== */
@keyframes guia-growx{ from{ transform:scaleX(0); } }
@keyframes guia-growy{ from{ transform:scaleY(0); } }
@keyframes guia-diceroll{ 0%{ transform:rotate(-20deg) scale(.8); opacity:.4; } 55%{ transform:rotate(14deg) scale(1.06); } 100%{ transform:none; opacity:1; } }
@keyframes guia-tensao{ 0%{ transform:scaleX(0); } 45%{ transform:scaleX(1.18); } 70%{ transform:scaleX(.82); } 100%{ transform:scaleX(1); } }
@keyframes guia-stepin{ from{ opacity:0; transform:translateY(7px); } }
@keyframes guia-crack{ 0%{ box-shadow:0 0 0 0 rgba(168,86,74,0); } 35%{ box-shadow:inset 0 0 0 2px var(--t-sangue), 0 0 14px rgba(168,86,74,.7); } 100%{ box-shadow:inset 0 0 0 1px rgba(168,86,74,.5); } }
.go .g-bfill{ transform-origin:left; animation:guia-growx .9s ease both; }
.go .g-barra.inv .g-bfill{ transform-origin:right; }
.go .g-d10 i{ display:inline-block; transform-origin:center; animation:guia-diceroll .7s ease; }
.go .g-dfill{ transform-origin:left; animation:guia-growx 1.1s ease both; }
.go .g-dissol{ animation:guia-crack 1.5s ease both; animation-delay:.5s; }
.go .g-med.pressao i{ transform-origin:left; animation:guia-growx 1s ease both; }
.go .g-med.tensao i{ transform-origin:left; animation:guia-tensao 1.6s ease both; }
.go .g-guarda i{ transform-origin:bottom; animation:guia-growy .9s ease both; }
.go .g-guarda.cheia{ animation:guia-crack 1.5s ease both; animation-delay:.8s; }
.demo-passo.in{ animation:guia-stepin .4s ease; }
</style>
"""

# ============================================================================
# FICHAS DE NARRADOR - 4 modelos como fichas de personagem (atributos em barras,
# seletor de versao, exemplo de narracao toggle). Geradas a partir de _FICHAS e
# injetadas no _BODY no marcador @@FICHAS@@. Versoes sondadas na API: claude-opus-4-6
# responde (entra como 2a versao do Opus); claude-fable-5 -> 404 (mostrado com aviso).
# ============================================================================
_FICHAS = [
    {
        "key": "opus", "nome": "Opus 4.8", "epiteto": "o narrador completo",
        "selo": "Recomendado", "selo_cls": "rec", "ico": "feather", "ativo": True,
        "prof": 5, "vel": 2, "custo": 4, "aviso": None,
        "desc": "Lê a cena inteira antes de escrever. Lembra do que você fez três turnos atrás — e cobra por isso. A prosa tem peso: silêncios que importam, vilões com motivo, escolhas que doem. É o que melhor sustenta o cinza de Alderyn, onde ninguém é só herói nem só algoz. Em troca, pensa devagar e pesa no bolso.",
        "quando": "um duelo com o Fiador, uma morte, a traição que vira a campanha de cabeça pra baixo.",
        "versoes": [("claude-opus-4-8", "Opus 4.8 — atual"), ("claude-opus-4-6", "Opus 4.6")],
        "exemplo": "A porta não quer abrir; cede só quando você empurra com o ombro, e o rangido entra na sala antes de você. As conversas não param — param os olhos. Três pares, depois quatro, depois o costume de não encarar volta a cobrir tudo como poeira. Turfa, cerveja virando vinagre, e por baixo um cheiro adocicado que ninguém menciona. O estalajadeiro é grande de um jeito que já foi força e agora é só volume; ele te olha demorado — não a cara, mas o cinto, as botas, o quanto você carrega e como. — Quarto, três. Agora, não de manhã. — Você paga. Ele guarda a moeda sem agradecer, porque agradecer seria admitir que precisava. Lá de cima, alguém tosse e para no meio, como quem se lembra de que não está sozinho.",
    },
    {
        "key": "sonnet", "nome": "Sonnet 4.6", "epiteto": "o cavalo de batalha",
        "selo": "Equilíbrio", "selo_cls": "eq", "ico": "pencil", "ativo": False,
        "prof": 4, "vel": 4, "custo": 2, "aviso": None,
        "desc": "Quase toda a profundidade do Opus, numa fração do tempo e do custo. Narra cenas longas sem te deixar esperando e conduz os NPCs com competência real. Onde cede é no detalhe fino — uma metáfora a menos, um subtexto que escapa. Em oito de cada dez cenas, você não nota a diferença.",
        "quando": "uma viagem longa, uma negociação de rotina, explorar um vilarejo sem pressa.",
        "versoes": [("claude-sonnet-4-6", "Sonnet 4.6 — atual")],
        "exemplo": "A porta cede com um rangido que cala as conversas por um instante — só um instante, antes que voltem, mais baixas. Turfa, cerveja azeda, suor velho na madeira. O estalajadeiro é um homem grande de mãos pequenas; ele te mede do umbral ao cinto antes de abrir a boca. — Quarto sai três. Pagas agora, não de manhã. — Não é hostilidade. É só um homem que já viu gente demais subir e não descer pra pagar. Quando a moeda troca de mão, ele aponta a escada com o queixo e te esquece.",
    },
    {
        "key": "haiku", "nome": "Haiku 4.5", "epiteto": "o veloz",
        "selo": "Econômico", "selo_cls": "eco", "ico": "bolt", "ativo": False,
        "prof": 2, "vel": 5, "custo": 1, "aviso": None,
        "desc": "Responde quase na hora e quase de graça. A prosa é direta e funcional — conta o que aconteceu, sem floreio. Brilha no mundano: cruzar uma estrada, comprar mantimentos, uma troca rápida num balcão. Onde o peso importa, entrega leve demais. Use pra poupar fôlego e moeda nas cenas que não pedem alma.",
        "quando": "comprar num mercado, uma transição curta entre dois lugares.",
        "versoes": [("claude-haiku-4-5-20251001", "Haiku 4.5 — atual")],
        "exemplo": "A porta range. Dentro, fumaça e cheiro de cerveja azeda. Algumas cabeças se viram e voltam ao copo. O estalajadeiro ergue os olhos do balcão. — Quarto? Três moedas. Última porta lá em cima. — Ele estende a mão pra moeda e volta a esfregar um caneco, sem te olhar de novo.",
    },
    {
        "key": "fable", "nome": "Fable 5", "epiteto": "o ápice",
        "selo": "Tier Mythos", "selo_cls": "myth", "ico": "crown", "ativo": False,
        "prof": 5, "vel": 1, "custo": 5,
        "aviso": "Acesso ao Tier Mythos pode estar suspenso agora por diretriz de exportação — pode não responder até liberarem.",
        "desc": "O tier mais alto que existe, um degrau acima do Opus — o teto absoluto de capacidade. Reserve pra quando a cena tem que ser inesquecível: o clímax de uma campanha de cinquenta sessões, a morte que você vai lembrar por anos. É o mais lento e o mais caro de todos, de longe. Não é pro dia a dia. É pro momento.",
        "quando": "o grande final, o momento que define a saga.",
        "versoes": [("claude-fable-5", "Fable 5 — atual")],
        "exemplo": "A porta resiste, e na resistência há algo que parece menos madeira inchada e mais aviso: certas soleiras a gente cruza, outras devia deixar fechadas. Você cruza. O rangido chega antes de você e faz o que a sua entrada sozinha não faria — interrompe. Não as bocas; os olhos. Eles te encontram, te pesam na moeda invisível com que lugares assim avaliam estranhos, e te devolvem ao anonimato com a mesma pressa, porque encarar custa e ninguém ali tem o que gastar. O ar é espesso: turfa, cerveja já do lado errado da fermentação, e, lá no fundo, aquele duçor que a memória reconhece antes da razão e prefere não nomear. O estalajadeiro foi grande um dia; agora é a lembrança de um homem grande, mãos pequenas demais pro corpo, como se tivessem parado de crescer no dia em que ele parou de revidar. Ele não olha o seu rosto — olha o que rostos não dizem: o peso do cinto, a lama nas botas, a pressa que você não tem. — Três. Pelo quarto. Agora. — A palavra \"agora\" não é grosseria; é experiência. E quando a moeda passa de mão, ele a faz sumir sem uma palavra, porque o obrigado dele morreu há muito, junto com a parte que ainda acreditava que as pessoas voltavam pra pagar o que deviam.",
    },
]


def _barras(v, cor):
    segs = "".join(
        f'<i class="seg {cor}{" on" if i < v else ""}"></i>' for i in range(5)
    )
    return f'<span class="bars" role="img" aria-label="{v} de 5">{segs}</span>'


def _ficha_html(f):
    aviso = ""
    if f.get("aviso"):
        aviso = ('<p class="ficha-aviso"><i class="ti ti-alert-triangle" aria-hidden="true"></i>'
                 f'<span>{html.escape(f["aviso"])}</span></p>')
    opts = "".join(
        f'<option value="{v}">{html.escape(lbl)}</option>' for v, lbl in f["versoes"]
    )
    attrs = (
        f'<div class="attr"><span class="attr-lbl">Profundidade</span>{_barras(f["prof"], "ambar")}</div>'
        f'<div class="attr"><span class="attr-lbl">Velocidade</span>{_barras(f["vel"], "ambar")}</div>'
        f'<div class="attr"><span class="attr-lbl">Custo</span>{_barras(f["custo"], "sangue")}</div>'
    )
    return (
        f'<div class="ficha{" ativo" if f.get("ativo") else ""}" role="button" tabindex="0" '
        f'data-modelo="{f["versoes"][0][0]}" data-key="{f["key"]}">'
        f'<div class="ficha-head"><i class="ti ti-{f["ico"]} ficha-ico" aria-hidden="true"></i>'
        f'<div class="ficha-id"><span class="ficha-nome">{html.escape(f["nome"])}</span>'
        f'<span class="ficha-epiteto">{html.escape(f["epiteto"])}</span></div>'
        f'<span class="ficha-selo {f["selo_cls"]}">{html.escape(f["selo"])}</span></div>'
        f'<div class="ficha-attrs">{attrs}</div>'
        f'<p class="ficha-desc">{html.escape(f["desc"])}</p>'
        f'<p class="ficha-quando"><b>Quando convocar — </b>{html.escape(f["quando"])}</p>'
        f'{aviso}'
        '<div class="ficha-ctrls">'
        '<label class="ficha-ver-lbl">versão '
        f'<select class="ficha-ver" aria-label="versão de {html.escape(f["nome"])}">{opts}</select></label>'
        '<button type="button" class="ficha-ex-btn">ver como ele narra ▾</button></div>'
        f'<div class="ficha-ex" hidden><p>{html.escape(f["exemplo"])}</p></div>'
        '</div>'
    )


def _fichas_html():
    return "".join(_ficha_html(f) for f in _FICHAS)


# ============================================================================
# GUIA - 6 cartas de referencia (consulta opcional). Mesmo espirito das fichas:
# icone Tabler + titulo + subtitulo + visual + texto witcher-grey. Injetado no
# _BODY no marcador @@GUIA@@. Cores por pilar/barra ajustadas a paleta sobria.
# ============================================================================
_PILARES = [
    ("CORPO", "sword", "#a8564a", "o aço e a carne. A força que não pede licença."),
    ("SOMBRA", "eye-off", "#7d6a93", "a fronteira. O que se ganha na margem, no silêncio, no engano."),
    ("ARCANO", "sparkles", "#5f7f95", "a Trama. As equações da realidade, lidas e reescritas por quem aguenta o preço."),
    ("ESPÍRITO", "flame", "#c67a33", "a fé. Convicção, o sagrado, o pacto com algo maior que você."),
    ("ENGENHO", "tools", "#8a8a5e", "a forja. A mente que inventa, mistura e constrói o que a natureza negou."),
]
_BARRAS_G = [
    ("VIDA", "#a8564a", 70, False, "Quando chega a zero, você cai. E o que vem depois raramente perdoa."),
    ("VIGOR", "#c67a33", 55, False, "Sua reserva de fôlego de combate. Golpes pesados, esquivas, esforço físico: tudo sai daqui. Acaba, e o corpo recua."),
    ("MANA", "#5f7f95", 60, False, "A energia da magia. Cada feitiço cobra. Um descanso curto devolve metade; o resto pede tempo."),
    ("FADIGA", "#8a7488", 80, True, "O cansaço que não vai embora sozinho. Sobe com o esforço, não desce com um respiro. Só um descanso longo zera. Quanto mais cheia, pior pra você."),
]


def _g_pilares():
    ab = "Todo poder em Alderyn nasce de um dos cinco. Sua vocação pertence a um deles — e ele decide como você dobra o mundo."
    selos = "".join(
        f'<div class="g-pilar" style="border-color:{cor}">'
        f'<i class="ti ti-{ic}" style="color:{cor}" aria-hidden="true"></i>'
        f'<span class="g-pnome">{html.escape(nome)}</span>'
        f'<span class="g-pln">{html.escape(linha)}</span></div>'
        for nome, ic, cor, linha in _PILARES
    )
    return f'<p class="g-txt">{html.escape(ab)}</p><div class="g-pilares">{selos}</div>'


def _g_barras():
    ab = "Quatro reservas medem o que resta de você. Três você gasta; uma se acumula contra você."
    fecho = "Vigor é o fôlego de agora. Fadiga é o peso de tudo que você já fez hoje."
    linhas = ""
    for nome, cor, pct, inv, txt in _BARRAS_G:
        warn = '<span class="g-bwarn">cheia = ruim</span>' if inv else ""
        linhas += (
            f'<div class="g-barra{" inv" if inv else ""}">'
            f'<div class="g-blbl"><span class="g-bnome" style="color:{cor}">{html.escape(nome)}</span>{warn}</div>'
            f'<div class="g-btrack"><i class="g-bfill" style="width:{pct}%;background:{cor}"></i></div>'
            f'<p class="g-btxt">{html.escape(txt)}</p></div>'
        )
    return (f'<p class="g-txt">{html.escape(ab)}</p><div class="g-barras">{linhas}</div>'
            f'<p class="g-fecho">{html.escape(fecho)}</p>')


def _g_rolagem():
    txt = "Quando o resultado está em dúvida, dois dados de dez lados decidem. Você soma o modificador da sua perícia e compara com a dificuldade da tarefa. Quanto mais alto, melhor — mas o mundo raramente responde com um sim limpo. Muitas vezes você consegue o que queria e paga um preço pelo caminho. Sucesso e custo costumam vir no mesmo lance."
    fecho = "Não é só passar ou falhar. É quanto a tarefa vai te custar pra passar."
    vis = ('<div class="g-roll"><span class="g-d10"><i class="ti ti-dice-5" aria-hidden="true"></i> d10</span>'
           '<span class="g-d10"><i class="ti ti-dice-5" aria-hidden="true"></i> d10</span></div>'
           '<div class="g-regua"><span class="g-rlbl">falha</span>'
           '<div class="g-rbar"><i class="g-rcusto"></i></div>'
           '<span class="g-rlbl">sucesso</span></div>'
           '<div class="g-rcaption">a faixa do meio: sucesso com custo</div>')
    return f'{vis}<p class="g-txt">{html.escape(txt)}</p><p class="g-fecho">{html.escape(fecho)}</p>'


def _g_magia():
    txt = "Magia em Alderyn não cobra só mana. A magia que toca o proibido — sangue, pactos, o que veio do Além — deixa uma dívida. Ela não é castigo. É cláusula: você pediu poder, o mundo anotou o preço. A dívida se acumula e quase nunca volta atrás. Quem entende o que está assinando administra o saldo; quem não entende paga sem saber, e o mundo cobra com juros. O arcano pesado tem o seu próprio preço — a Dissolução: a mente que reescreve a realidade começa a se desfazer junto, e você passa a se ver de fora, como se o corpo fosse de outra pessoa. No limite de qualquer um desses preços, o que você invocou refaz você à imagem dele."
    fecho = "Todo feitiço grande tem dois preços: o que você paga agora, e o que ele cobra de quem você é."
    vis = ('<div class="g-medrow">'
           '<div class="g-medcol"><span class="g-medcap">a dívida sobe</span>'
           '<div class="g-divida"><i class="g-dfill"></i></div></div>'
           '<div class="g-medcol"><span class="g-medcap">a dissolução</span>'
           '<div class="g-dissol">você, de fora</div></div></div>')
    return f'{vis}<p class="g-txt">{html.escape(txt)}</p><p class="g-fecho">{html.escape(fecho)}</p>'


def _g_tensao():
    txt = "Duas coisas medem o quanto a situação aperta — e elas são opostas no tempo. A Tensão é o calor da luta: sobe a cada troca de golpes, deixa todo mundo mais perigoso, e some quando o combate acaba. Nasce e morre na briga. A Pressão é o peso do que você viveu: o que você viu, o que fez, o que carregou. Isso não evapora quando a luta termina. Fica. Se acumula em silêncio e cobra mais tarde, longe do campo de batalha."
    fecho = "Tensão some quando a luta acaba. Pressão é o que a luta deixou em você."
    vis = ('<div class="g-medrow">'
           '<div class="g-medcol"><span class="g-medcap" style="color:#c67a33">Tensão <i class="ti ti-arrows-vertical" aria-hidden="true"></i></span>'
           '<div class="g-med tensao"><i style="width:62%"></i></div>'
           '<span class="g-medsub">sobe e desce — some na luta</span></div>'
           '<div class="g-medcol"><span class="g-medcap" style="color:#8a7488">Pressão</span>'
           '<div class="g-med pressao"><i style="width:45%"></i></div>'
           '<span class="g-medsub">só sobe — fica como cicatriz</span></div></div>')
    return f'{vis}<p class="g-txt">{html.escape(txt)}</p><p class="g-fecho">{html.escape(fecho)}</p>'


def _g_medula():
    txt = "Quando sua Vida chega a zero, você não morre na hora — você rola pela própria carne. É o Rolo da Medula: o lance que decide se você se agarra à consciência ou apaga. Mas a morte em Alderyn tem memória. Cada vez que você cai e volta, fica uma dívida que nunca se paga, e o próximo Rolo da Medula vem mais difícil que o anterior. Voltar não é de graça — é um empréstimo, e os juros se acumulam. E há quem diga que, quando o último dado cai errado e tudo deveria acabar, você não fica totalmente sozinho no escuro. Mas esse é um trato pra outra hora."
    fecho = "Você pode voltar. Mas cada volta custa mais que a anterior."
    vis = ('<div class="g-medula"><i class="ti ti-dice-5" aria-hidden="true"></i>'
           '<i class="ti ti-bone" aria-hidden="true"></i></div>')
    return f'{vis}<p class="g-txt">{html.escape(txt)}</p><p class="g-fecho">{html.escape(fecho)}</p>'


_GUIA = [
    ("columns-3", "Os Cinco Pilares", "de onde vem o que você faz", _g_pilares),
    ("battery-3", "As Quatro Barras", "o que mantém você de pé", _g_barras),
    ("dice-5", "A Rolagem", "como o destino responde", _g_rolagem),
    ("flask-2", "O Custo da Magia", "poder não é de graça", _g_magia),
    ("activity", "Tensão e Pressão", "dois pesos que não se misturam", _g_tensao),
    ("bone", "O Rolo da Medula", "quando o corpo chega ao fim", _g_medula),
]


def _g_card(ico, titulo, sub, body):
    """Casca padrao de uma carta do Guia: cabecalho (icone+titulo+sub) + corpo."""
    return (
        '<div class="g-card">'
        f'<div class="g-head"><i class="ti ti-{ico} g-ico" aria-hidden="true"></i>'
        f'<div class="g-id"><span class="g-titulo">{html.escape(titulo)}</span>'
        f'<span class="g-sub">{html.escape(sub)}</span></div></div>'
        f'{body}</div>'
    )


# ============================================================================
# O COMBATE - sub-secao do Guia. CONCEITUAL: custos/quantidades RELATIVOS (pontos),
# nunca numeros absolutos. Nenhuma logica de jogo nova - so explicacao visual.
# ============================================================================
_COMBATE_ABERTURA = ("O combate em Alderyn é curto, tenso e mortal. Não existe troca de golpes infinita "
                     "até alguém cair — cada round muda alguma coisa. E quando você luta sozinho, ferido, "
                     "sem ninguém pra te cobrir, é quando o mundo mostra os dentes. Aqui está como uma luta "
                     "funciona por dentro.")
_COMBATE_TENSAO_REF = ("A Tensão — o calor que sobe na luta — é uma das camadas do combate; "
                       "a carta dela está acima, em “O Personagem e o Sistema”.")


def _corpo(vis, txt, fecho):
    return f'{vis}<p class="g-txt">{html.escape(txt)}</p><p class="g-fecho">{html.escape(fecho)}</p>'


def _c_economia():
    vis = ('<div class="g-acoes">'
           '<i class="g-acao on"></i><i class="g-acao on"></i><i class="g-acao on"></i>'
           '<i class="g-acao spent"></i><i class="g-acao spent"></i>'
           '<span class="g-acoes-lbl">a reserva do round — algumas ações já gastas</span></div>')
    txt = ("Num combate, o seu lado não age “um de cada vez”. Vocês compartilham um punhado de ações "
           "por round — uma reserva que se gasta. Atacar onde dói, explorar a fraqueza do inimigo, rende mais: "
           "você faz mais com a mesma reserva. Errar feio é caro: você desperdiça ações e entrega o ritmo pro "
           "outro lado. O inimigo joga pela mesma regra. Quem usa as ações melhor domina o round.")
    return _corpo(vis, txt, "Combate não é quem bate mais. É quem gasta as ações melhor.")


def _c_guarda():
    vis = ('<div class="g-guarda-row">'
           '<div class="g-guarda-col"><span class="g-gcap">enchendo</span>'
           '<div class="g-guarda"><i style="height:68%"></i></div></div>'
           '<div class="g-guarda-col"><span class="g-gcap quebra">QUEBRA</span>'
           '<div class="g-guarda cheia"><i style="height:100%"></i></div></div></div>')
    txt = ("Inimigos sérios — elites e chefes — não caem só no dano. Eles têm uma guarda. Cada vez que você "
           "pressiona — golpes certeiros, aparar um ataque, jogadas que abalam — a guarda dele enche. Quando "
           "chega ao topo, a guarda QUEBRA: por um instante ele fica exposto, e seus golpes acertam com força "
           "muito maior. Mas se você recua e para de pressionar, a guarda se recupera. O combate vira um pulso: "
           "pressiona, pressiona, QUEBRA, pune — e recomeça.")
    return _corpo(vis, txt, "Não espere o chefe cansar. Force a guarda dele até quebrar.")


def _c_ritmo():
    def cartao(nome, pontos, risco):
        pips = "".join(f'<i class="g-pip{" on" if i < pontos else ""}"></i>' for i in range(3))
        return (f'<div class="g-ritmo-c"><span class="g-rnome">{nome}</span>'
                f'<span class="g-pips">{pips}</span><span class="g-rrisco">{risco}</span></div>')
    vis = ('<div class="g-ritmo">'
           + cartao("Rápida", 1, "risco baixo") + cartao("Firme", 2, "risco médio")
           + cartao("Pesada", 3, "risco alto") + '</div>')
    txt = ("Cada coisa que você faz tem um preço na sua reserva de ações. Uma ação rápida custa pouco e é "
           "segura, mas faz pouco — um bote, um reposicionamento, ler o inimigo. Uma ação firme é o golpe "
           "padrão: custo médio, resultado confiável. Uma ação pesada custa caro e te deixa aberto enquanto "
           "você a prepara, mas quando entra, devasta. Escolher o ritmo é metade da luta: economizar e cutucar, "
           "ou apostar tudo num golpe que pode virar o jogo — ou te custar caro se falhar.")
    return _corpo(vis, txt, "O golpe pesado ganha lutas. Também perde, quando erra.")


def _c_posicao():
    cols = ["Controlada", "Arriscada", "Desesperada"]
    cels = ('<span class="g-mh"></span>' + "".join(f'<span class="g-mh">{c}</span>' for c in cols)
            + '<span class="g-mr">Normal</span><span class="g-mc"></span><span class="g-mc"></span><span class="g-mc"></span>'
            + '<span class="g-mr">Grande</span><span class="g-mc"></span><span class="g-mc"></span>'
            + '<span class="g-mc alta">aposta alta</span>')
    vis = f'<div class="g-matriz" role="img" aria-label="matriz Posição por Efeito">{cels}</div>'
    txt = ("Antes de uma ação importante, duas coisas são pesadas. A POSIÇÃO diz o quanto você está exposto: "
           "controlada (você está firme, o contragolpe é pequeno), arriscada (a troca é justa, dói se der errado), "
           "ou desesperada (você está no fio — se falhar, o preço é brutal). O EFEITO diz o quanto a ação muda o "
           "combate: normal, ou grande. Uma jogada desesperada de efeito grande é a aposta clássica do herói "
           "ferido: pode encerrar a luta — ou encerrar você.")
    return _corpo(vis, txt, "Quanto mais desesperada a posição, mais a falha cobra.")


def _c_ferimentos():
    vis = ('<div class="g-ferimento"><i class="ti ti-bandage" aria-hidden="true"></i>'
           '<div><span class="g-fnome">Corte no braço esquerdo</span>'
           '<span class="g-fefeito">seus golpes custam mais</span></div></div>')
    txt = ("Dano em Alderyn nem sempre é só um número que desce. Golpes que importam deixam ferimentos com nome "
           "— um corte no braço que atrapalha sua arma, uma perna ferida que rouba seu passo. Cada ferimento pesa "
           "nas ações seguintes e aparece na narração: o Cronista lembra do seu braço sangrando quando descreve o "
           "próximo golpe. Você não está só perdendo pontos. Você está se danificando, e isso muda como a luta "
           "continua.")
    return _corpo(vis, txt, "Cada ferimento sério muda a luta que ainda falta.")


def _c_acompanhado():
    chips = ('<span class="g-chip"><i class="ti ti-shield-half" aria-hidden="true"></i>interceptar</span>'
             '<span class="g-chip"><i class="ti ti-heartbeat" aria-hidden="true"></i>reanimar</span>'
             '<span class="g-chip"><i class="ti ti-reload" aria-hidden="true"></i>segunda chance</span>')
    vis = ('<div class="g-vinculo-wrap"><span class="g-vcap">Vínculo</span>'
           '<div class="g-vinculo"><i style="width:66%"></i></div>'
           f'<div class="g-chips">{chips}</div>'
           '<span class="g-vsub">poucas, e não se renovam no meio da luta</span></div>')
    txt = ("Se você luta ao lado de um companheiro, o vínculo entre vocês vira força em combate. Esse vínculo "
           "permite intervenções nos momentos críticos: interceptar um golpe que ia te acertar, te puxar de volta "
           "quando você cai, te dar uma segunda chance num lance falho. As intervenções são poucas e não se "
           "renovam no meio da luta — gastá-las é uma decisão. E o vínculo tem peso real: cresce com lealdade e "
           "batalhas divididas, e pode cair se você trai ou abandona. Lutar sozinho é mais mortal justamente "
           "porque ninguém está lá pra te cobrir.")
    return _corpo(vis, txt, "Sozinho, cada erro é só seu. Acompanhado, alguém pode pagar por você — uma vez.")


def _c_round_a_round():
    intro = "Você (um guerreiro) e sua companheira contra o Cavaleiro Corrompido — sem fraqueza elemental, só guarda e aço."
    rounds = [
        ("run", "Round 1", "A tensão ainda é baixa. Você e ela trocam golpes firmes; a guarda dele começa a encher. Ele ergue o montante negro acima da cabeça: um aviso. A sombra da lâmina se espalha pelo chão. Você lê o golpe e esquiva — o peso dele desce no vazio.", ""),
        ("droplet", "Rounds depois", "A tensão subiu, o ar pesa, os dois ofegam. Você carrega um corte no braço esquerdo: cada golpe seu agora custa mais. Sua posição virou arriscada. Ela mira a junta do joelho dele; a guarda enche mais. O cavaleiro recua um passo.", ""),
        ("shield-bolt", "O round da quebra", "A guarda QUEBRA. Por um instante o cavaleiro está aberto. Sua companheira gasta o vínculo pra rasgar ainda mais a brecha. Você está quase sem vida — posição desesperada — e mesmo assim aposta num golpe pesado de efeito grande na fenda da armadura. Aço encontra carne. Ele urra.", "quebra"),
        ("arrow-back-up", "O depois", "Ele se recupera. A guarda volta, mais dura que antes. A tensão está no auge: agora os dois lados machucam mais. A luta continua — mais perigosa pra todo mundo.", ""),
    ]
    blocos = "".join(
        f'<div class="g-round {extra}"><i class="ti ti-{ic}" aria-hidden="true"></i>'
        f'<div class="g-round-txt"><span class="g-rlabel">{html.escape(lbl)}</span>'
        f'<p>{html.escape(t)}</p></div></div>'
        for ic, lbl, t, extra in rounds
    )
    vis = (f'<p class="g-tl-intro">{html.escape(intro)}</p>'
           f'<div class="g-timeline">{blocos}</div>')
    fecho = "Uma luta não é uma fila de golpes. É um pulso que sobe até alguém quebrar."
    return f'{vis}<p class="g-fecho">{html.escape(fecho)}</p>'


# ---- selo reutilizavel + rodape de exemplo (PARTES A/B). TODO numero e ilustrativo. ----
def _selo():
    return ('<span class="selo-ilus"><i class="ti ti-flask-2" aria-hidden="true"></i>'
            'números ilustrativos</span>')


def _ex_foot(linhas):
    return (f'<div class="ex-foot"><div class="ex-foot-top">'
            f'<span class="ex-foot-lbl">Exemplo</span>{_selo()}</div>'
            f'<div class="ex-foot-body">{linhas}</div></div>')


# numeros EXATOS do brief (ilustrativos). Por titulo de carta.
_EX_FOOTERS = {
    "A Rolagem": ("2d10 + modificador, contra a dificuldade. Tarefa média = <b>12</b>; difícil = <b>14</b>. "
                  "Ex.: 2d10 = <b>6+4 = 10</b>, + Espada <b>+3</b> = <b>13</b> contra <b>12</b> → acerta. "
                  "Total bem acima = acerto limpo; <b>1–2</b> acima = acerto com custo; abaixo = erro."),
    "O Rolo da Medula": ("Vida em 0: role 2d10 + o Vigor que restou, contra dificuldade <b>14</b>. "
                         "Cada morte anterior tira <b>1</b> do total. Ex.: 2d10 = <b>11</b>, + Vigor <b>4</b> "
                         "= <b>15</b> contra <b>14</b> → passou por pouco, você se agarra à consciência."),
    "A Economia da Luta": ("Reserva por round: <b>4</b> ações. Custo — Rápida <b>1</b> · Firme <b>2</b> · "
                           "Pesada <b>3</b>. Acertar a fraqueza do inimigo devolve <b>1</b> ação."),
    "A Guarda e a Quebra": ("Guarda do Cavaleiro: <b>0 a 20</b>. Golpe certeiro <b>+3</b> · aparar <b>+2</b> · "
                            "crítico <b>+4</b> · pesado que conecta <b>+5</b>. Em <b>20</b>: QUEBRA — próximos golpes "
                            "causam o <b>dobro</b>. Parar de pressionar recupera <b>2</b> por round."),
    "O Ritmo das Ações": ("Custo na reserva (de <b>4</b>): Rápida <b>1</b> · Firme <b>2</b> · Pesada <b>3</b>. "
                          "Dano — golpe firme <b>~12</b> · golpe pesado <b>~20</b>."),
    "Posição e Efeito": ("Posição <b>desesperada</b>: se você falhar, o contragolpe é grande. "
                         "Efeito <b>grande</b>: o dano dobra."),
}


# ---- PARTE C: a Demonstracao animada. Estado inicial + 10 passos + replay. ----
def _demo_meter(nome, val, pct, cor, key):
    return (f'<div class="demo-meter"><span class="demo-mlbl">{html.escape(nome)}</span>'
            f'<div class="demo-mtrack"><i class="demo-mfill" id="dm-{key}" '
            f'style="width:{pct}%;background:{cor}"></i></div>'
            f'<span class="demo-mval" id="dmv-{key}">{html.escape(val)}</span></div>')


def _c_demo():
    estado = (
        '<div class="demo-estado">'
        + _demo_meter("Vida", "34/120", 28, "#a8564a", "vida")
        + _demo_meter("Vigor", "6/30", 20, "#c67a33", "vigor")
        + _demo_meter("Fadiga", "12/30", 40, "#8a7488", "fadiga")
        + _demo_meter("Tensão", "4/10", 40, "#c67a33", "tensao")
        + _demo_meter("Guarda do Cavaleiro", "17/20", 85, "#a8564a", "guarda")
        + '<div class="demo-meter"><span class="demo-mlbl">Ações</span>'
          '<div class="demo-acoes" id="dm-acoes">'
          '<i class="g-acao on"></i><i class="g-acao on"></i>'
          '<i class="g-acao on"></i><i class="g-acao on"></i></div>'
          '<span class="demo-mval" id="dmv-acoes">4</span></div>'
        + '</div>'
    )
    passos = [
        '<p>Você escolhe um <b>golpe pesado</b> na fenda da armadura. '
        '<span class="demo-tag">Ação Pesada custa 3</span></p>',
        '<p>Posição: <b>Desesperada</b> (Vida em 28%). Efeito: <b>Grande</b> (a guarda está quase no limite). '
        '<span class="demo-selo desesp">Desesperada</span><span class="demo-selo grande">Efeito grande</span></p>',
        '<p>A rolagem. <span class="demo-dados"><span class="demo-dado" id="dm-d1">6</span>'
        '<span class="demo-dado" id="dm-d2">4</span></span> = 10, + Espada <b>+3</b> = <b class="demo-num">13</b></p>',
        '<p><b>13</b> contra dificuldade <b>12</b>. <span class="demo-acerto"><i class="ti ti-check" '
        'aria-hidden="true"></i>ACERTO</span> Passou por pouco — acerta, mas te deixa exposto.</p>',
        '<p>O dano. Golpe pesado <b>20</b>, dobrado pelo efeito grande = <b class="demo-num dano">40</b>.</p>',
        '<p>A guarda enche — de <b>17</b>, passa de <b>20</b> e <b class="demo-quebra-txt">QUEBRA</b>.</p>',
        '<p><b>Guarda quebrada</b> — o cavaleiro está exposto. '
        '<span class="demo-selo exposto">exposto</span></p>',
        '<p>Sua companheira gasta o <b>Vínculo</b> pra rasgar mais a brecha. '
        '<span class="demo-tag" id="dm-vinc">−1 intervenção</span></p>',
        '<p>A tensão sobe — de <b>4</b> para <b>5</b>.</p>',
    ]
    # SEM hidden: visiveis por padrao (degrada bem se o JS falhar). O JS esconde so
    # pra rodar a sequencia animada; com reduced-motion mostra tudo de uma vez.
    lis = "".join(f'<li class="demo-passo" data-step="{i}">{p}</li>' for i, p in enumerate(passos))
    final = (f'<li class="demo-passo demo-final" data-step="{len(passos)}">'
             '<p>Números ilustrativos — os valores finais do sistema ainda estão sendo afinados.</p>'
             f'{_selo()}</li>')
    return (
        '<div class="demo">'
        f'{estado}'
        f'<ol class="demo-passos" id="demo-passos">{lis}{final}</ol>'
        '<button type="button" class="demo-replay" id="demo-replay">'
        '<i class="ti ti-reload" aria-hidden="true"></i>ver de novo</button>'
        '</div>'
    )


_COMBATE = [
    ("coins", "A Economia da Luta", "ação é moeda", _c_economia),
    ("shield-bolt", "A Guarda e a Quebra", "o ritmo da pressão", _c_guarda),
    ("swords", "O Ritmo das Ações", "rápida, firme ou pesada", _c_ritmo),
    ("target-arrow", "Posição e Efeito", "o risco e o tamanho", _c_posicao),
    ("bandage", "Ferimentos", "dano que vira história", _c_ferimentos),
    ("heart-handshake", "Lutar Acompanhado", "alguém pra te cobrir", _c_acompanhado),
    ("timeline", "Uma Luta, Round a Round", "tudo junto, em movimento", _c_round_a_round),
]


def _carta_guia(ico, t, sub, fn):
    body = fn()
    if t in _EX_FOOTERS:   # rodape de exemplo visivel (numeros ilustrativos)
        body += _ex_foot(_EX_FOOTERS[t])
    return _g_card(ico, t, sub, body)


def _guia_html():
    sistema = "".join(_carta_guia(*x) for x in _GUIA)
    combate = "".join(_carta_guia(*x) for x in _COMBATE)
    nota = (
        '<div class="num-nota">'
        f'{_selo()}'
        '<p class="num-nota-txt">Os números abaixo são exemplos, pra você entender como a mecânica '
        'funciona. Os valores finais do sistema ainda estão sendo afinados e podem mudar.</p>'
        '<p class="num-perso">Personagem de exemplo: você é um <b>Guerreiro</b> — Vida 120, Vigor 30, '
        'Mana 10, Fadiga 0/30, modificador de Espada +3. Inimigo: <b>Cavaleiro Corrompido</b>, Guarda 0 a 20.</p>'
        '</div>'
    )
    demo = (
        '<div class="g-card demo-card">'
        '<div class="g-head"><i class="ti ti-player-play g-ico" aria-hidden="true"></i>'
        '<div class="g-id"><span class="g-titulo">Demonstração — Um Round, Por Dentro</span>'
        '<span class="g-sub">tudo junto, em movimento (números ilustrativos)</span></div></div>'
        f'{_c_demo()}</div>'
    )
    return (
        '<h3 class="g-secao">O Personagem e o Sistema</h3>'
        f'<div class="guia-grupo">{sistema}</div>'
        '<h3 class="g-secao">O Combate</h3>'
        f'<p class="g-abertura">{html.escape(_COMBATE_ABERTURA)}</p>'
        f'<p class="g-tensao-ref">{html.escape(_COMBATE_TENSAO_REF)}</p>'
        f'{nota}'
        f'<div class="guia-grupo">{combate}{demo}</div>'
    )


_BODY = """
<div class="alderyn-stage atm-ermo">
  <div class="entrada-cena" aria-hidden="true"></div>
  <div class="bruma" aria-hidden="true"></div>

  <!-- TELA DO JOGO -->
  <main class="pagina tela tela-jogo" id="tela-jogo" aria-label="Folha do almanaque - tela de jogo">

    <div class="head">
      <svg class="fleur" width="16" height="14" viewBox="0 0 24 20" fill="none" stroke="#8c8167" stroke-width="1.1">
        <path d="M12 3c3 0 5 2 5 5s-2 7-5 9c-3-2-5-6-5-9s2-5 5-5z"/><path d="M3 10h6M15 10h6"/>
      </svg>
      <span class="ttl">vig&iacute;lia&nbsp;quebrada</span>
      <span class="ln"></span>
      <button type="button" class="selar" id="encerrar-sessao" title="Selar a sess&atilde;o e abrir a pr&oacute;xima">selar&nbsp;sess&atilde;o</button>
      <button type="button" class="engr" id="abrir-config" title="Configura&ccedil;&otilde;es" aria-label="Configura&ccedil;&otilde;es"><i class="ti ti-settings" aria-hidden="true"></i>configura&ccedil;&otilde;es</button>
      <a class="oraculo" href="/oraculo" title="Consultar o Or&aacute;culo"><i class="ti ti-eye" aria-hidden="true"></i>or&aacute;culo</a>
      <a class="sair" href="/oficina" title="Voltar &agrave; oficina">&larr;&nbsp;oficina</a>
    </div>

    <div class="marg">
      <div class="pressao" id="pressao" title="Press&atilde;o Emocional">
        <span class="plab">press&atilde;o</span>
        <span class="bar"><i></i></span>
        <span class="num"><b id="pressao-num">0</b>&nbsp;/&nbsp;10</span>
      </div>
    </div>

    <!-- MIOLO: a unica zona que rola (cena + narracao). -->
    <div class="miolo" id="miolo">
      <figure class="plate">
        <div class="frame"><img src="/static/estampa_porta.webp" alt="Gravura: uma porta arqueada entreaberta, com uma fresta de luz e degraus de pedra"></div>
        <figcaption class="cap">figura &mdash; a porta, ao cair da noite</figcaption>
      </figure>

      <div class="corpo" id="corpo">
        <div class="portal" id="portal">
          <div class="portal-nome">Vig&iacute;lia Quebrada</div>
          <div class="portal-traco"></div>
          <button id="adentrar" class="adentrar">adentrar</button>
        </div>
      </div>

      <!-- ZONA DE DADOS (Balde 1): so MOSTRA; o Python decide. Comeca oculta (dormant).
           O Cronista a "arma" (window.armarDado) -> botao libera. ids estaveis (JS depende). -->
      <div class="dado-zona" id="dado-zona" data-estado="dormant" aria-live="polite" hidden>
        <div class="dado-cue" id="dado-cue">o momento pede um lance</div>
        <div class="dado-par">
          <div class="dado" id="dado-1">&mdash;</div>
          <div class="dado" id="dado-2">&mdash;</div>
        </div>
        <div class="dado-conta" id="dado-conta"></div>
        <div class="dado-faixa" id="dado-faixa"></div>
        <button class="dado-btn" id="dado-btn" type="button" aria-label="Rolar os dados" disabled>rolar</button>
        <div class="dado-fx" id="dado-fx" aria-hidden="true">
          <span class="fx-clarao"></span>
          <span class="fx-raio"></span>
          <span class="fx-fio"></span>
          <span class="fx-sangue"></span>
        </div>
      </div>

      <div class="pondera oculto" id="pondera">o Cronista pondera<span class="ret"><span>.</span><span>.</span><span>.</span></span></div>
    </div>

    <div class="scrawl oculto" id="scrawl">
      <button id="recomecar" class="recomecar-btn" title="Recome&ccedil;ar">recome&ccedil;ar</button>
      <input type="text" id="cmd" placeholder="aja, ou observe..." aria-label="Sua a&ccedil;&atilde;o">
      <button id="send" class="send-btn" aria-label="Inscrever">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 21l4-1L20 7a2 2 0 0 0-3-3L4 17l-1 4z"/><path d="M14 6l3 3"/></svg>
      </button>
    </div>
  </main>

  <!-- TELA DE CONFIGURACOES: substitui a tela do jogo (NAO e overlay). App-shell propria:
       head fixo com "voltar ao jogo" + conteudo rolavel (.config-scroll). Reusa TODO o
       conteudo (abas, Fichas, Guia/Combate/Demo, controles de tela). -->
  <section class="pagina tela tela-config oculto" id="tela-config" role="region" aria-label="Configura&ccedil;&otilde;es">

    <div class="head head-config">
      <button type="button" class="voltar-jogo" id="voltar-jogo" title="Voltar ao jogo"><i class="ti ti-arrow-left" aria-hidden="true"></i>voltar ao jogo</button>
      <span class="ln"></span>
      <span class="ttl ttl-config">configura&ccedil;&otilde;es</span>
    </div>

    <div class="miolo config-scroll">
      <div class="config-tabs" role="tablist">
        <button type="button" class="config-tab ativo" data-tab="narrador" role="tab" aria-selected="true">Narrador</button>
        <button type="button" class="config-tab" data-tab="guia" role="tab" aria-selected="false">Guia</button>
        <button type="button" class="config-tab" data-tab="tela" role="tab" aria-selected="false">Tela</button>
      </div>

      <div class="config-pane ativo" data-pane="narrador">
        <div class="fichas" id="fichas">@@FICHAS@@</div>
      </div>

      <div class="config-pane" data-pane="guia" hidden>
        <p class="guia-intro">Consulta opcional. O jogo ensina cada conceito aos poucos, dentro da pr&oacute;pria narra&ccedil;&atilde;o &mdash; isto aqui &eacute; s&oacute; pra quando voc&ecirc; quiser entender o sistema.</p>
        <div class="guia" id="guia">@@GUIA@@</div>
      </div>

      <div class="config-pane" data-pane="tela" hidden>
        <div class="config-linha">
          <span class="config-rotulo">Tamanho do texto</span>
          <div class="txt-tam" id="txt-tam">
            <button type="button" class="tbtn" data-nivel="0" title="Menor" aria-label="Diminuir">A&minus;</button>
            <button type="button" class="tbtn ativo" data-nivel="1" title="Padr&atilde;o" aria-label="Padr&atilde;o">A</button>
            <button type="button" class="tbtn" data-nivel="2" title="Maior" aria-label="Aumentar">A+</button>
          </div>
        </div>
        <div class="config-linha">
          <span class="config-rotulo">Modo foco</span>
          <button type="button" class="foco-toggle" id="foco-toggle" aria-pressed="false"><span class="foco-estado">Desligado</span></button>
        </div>
      </div>
    </div>
  </section>

  <!-- botao discreto pra sair do modo foco (alem do ESC). So aparece com body.foco. -->
  <button type="button" class="sair-foco" id="sair-foco" title="Sair do modo foco (ESC)">sair do foco</button>

</div>
"""
_BODY = _BODY.replace("@@FICHAS@@", _fichas_html())
_BODY = _BODY.replace("@@GUIA@@", _guia_html())


# Mapa de quantas variacoes cada atmosfera tem no R2 (1 = so {slug}.webp).
# Arquivos: variacao 1 = {slug}.webp ; 2..N = {slug}-2.webp ... {slug}-N.webp.
# DEVE casar com o que foi subido no R2. sangue=3 de proposito (a 4a, com armas
# explicitas, ficou de fora pra preservar a sutileza witcher-grey).
_ATM_VARIACOES = {"ermo": 4, "mata": 3, "frio": 4, "sangue": 3, "corte": 4}

# Helper proprio (NAO mexe no bundle jogar.js minificado). Troca a pele da cena
# (classe .atm-X = cor) e SORTEIA a foto da cena em --cena. Whitelist fechada
# (LISTA) ESPELHA ATMOSFERAS do Python. A foto so e re-sorteada quando a atmosfera
# MUDA (ou forcar=true) - a mesma cena nao troca de imagem embaixo do jogador.
_ATMOSFERA_JS = """
<script>
(function () {
  var LOCAL = '/static/cenarios/atmosferas/';
  var R2 = 'https://imagens.luisgabriel.uk/cenarios/atmosferas/';
  var VARS = __VARS__;
  var LISTA = Object.keys(VARS);
  var atual = null;
  var ultimaVar = {};
  var reqId = 0;

  function rel(nome, n) { return nome + (n > 1 ? '-' + n : '') + '.webp'; }
  function sorteia(nome) {
    var total = VARS[nome] || 1, n;
    if (total <= 1) return 1;
    do { n = Math.floor(Math.random() * total) + 1; } while (n === ultimaVar[nome]);
    ultimaVar[nome] = n;
    return n;
  }

  // Cascata: tenta LOCAL; se falhar, tenta R2; se falhar, cai na cor (--cena:none -> --fallback).
  // reqId evita corrida: se a cena mudar antes do probe terminar, o resultado antigo e descartado.
  function pintarCena(s, nome) {
    var meu = ++reqId;
    var arq = rel(nome, sorteia(nome));
    var local = LOCAL + arq, remoto = R2 + arq;
    var p1 = new Image();
    p1.onload = function () { if (meu === reqId) s.style.setProperty('--cena', 'url("' + local + '")'); };
    p1.onerror = function () {
      var p2 = new Image();
      p2.onload = function () { if (meu === reqId) s.style.setProperty('--cena', 'url("' + remoto + '")'); };
      p2.onerror = function () { if (meu === reqId) s.style.setProperty('--cena', 'none'); };
      p2.src = remoto;
    };
    p1.src = local;
  }

  window.setAtmosfera = function (nome, opts) {
    var s = document.querySelector('.alderyn-stage');
    if (!s || LISTA.indexOf(nome) < 0) return;
    var forcar = !!(opts && opts.forcar);
    if (nome === atual && !forcar) return;
    LISTA.forEach(function (a) { s.classList.remove('atm-' + a); });
    s.classList.add('atm-' + nome);
    pintarCena(s, nome);
    atual = nome;
  };

  function init() { window.setAtmosfera('ermo', { forcar: true }); }
  if (document.readyState !== 'loading') { init(); }
  else { document.addEventListener('DOMContentLoaded', init); }
})();
</script>
"""
_ATMOSFERA_JS = _ATMOSFERA_JS.replace("__VARS__", json.dumps(_ATM_VARIACOES))


# Casca do painel de Configuracoes - CSS/JS puro, SEM componente ui.* novo. Abre/fecha
# o overlay; os cards de modelo reusam o evento 'trocar_modelo' que ja existe (mesmo
# backend); tamanho do texto e modo foco sao 100% cliente, lembrados em localStorage.
# Injetado por run_javascript (porta nao-sanitizada), como o resto do /jogar.
_CONFIG_JS = """
(function () {
  if (window.__configWired) return;
  window.__configWired = true;

  // CONFIG agora e uma TELA separada (nao overlay): alterna tela-jogo <-> tela-config.
  // Uma fica .oculto (display:none) por vez; nada de caixa flutuante sobre o jogo.
  var telaJogo = document.getElementById('tela-jogo');
  var telaConfig = document.getElementById('tela-config');
  var abrir = document.getElementById('abrir-config');
  var voltar = document.getElementById('voltar-jogo');

  // ABAS: Narrador / Guia / Tela. selTab centraliza a troca (clique e abertura).
  var tabs = document.querySelectorAll('.config-tab');
  var panes = document.querySelectorAll('.config-pane');
  function selTab(nome) {
    tabs.forEach(function (x) {
      var on = x.dataset.tab === nome;
      x.classList.toggle('ativo', on); x.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    panes.forEach(function (p) {
      if (p.dataset.pane === nome) p.removeAttribute('hidden'); else p.setAttribute('hidden', '');
    });
    // ao mostrar a aba Guia, dispara as animacoes de entrada + a Demonstracao
    if (nome === 'guia' && typeof onGuiaShown === 'function') onGuiaShown();
  }
  tabs.forEach(function (t) { t.addEventListener('click', function () { selTab(t.dataset.tab); }); });

  function abreConfig() {
    if (telaJogo) telaJogo.classList.add('oculto');
    if (telaConfig) {
      telaConfig.classList.remove('oculto');
      var sc = telaConfig.querySelector('.miolo'); if (sc) sc.scrollTop = 0;
    }
    selTab('narrador');                 // aba padrao ao entrar na config
  }
  function voltaJogo() {
    if (telaConfig) telaConfig.classList.add('oculto');
    if (telaJogo) telaJogo.classList.remove('oculto');
  }
  if (abrir) abrir.addEventListener('click', abreConfig);
  if (voltar) voltar.addEventListener('click', voltaJogo);

  // FICHAS DE NARRADOR. Tres acoes no mesmo card:
  //  - SELECIONAR (corpo da ficha, ou Enter/Espaco): vira o narrador ativo. Manda
  //    'trocar_modelo' com a VERSAO escolhida no seletor da ficha.
  //  - SELETOR DE VERSAO (<select>): stopPropagation pra nao selecionar; ao mudar,
  //    atualiza data-modelo e, se a ficha estiver ativa, reemite 'trocar_modelo'.
  //  - "ver como ele narra": toggle do exemplo, stopPropagation pra nao selecionar.
  var fichas = document.querySelectorAll('#fichas .ficha');
  function selecionaFicha(f) {
    fichas.forEach(function (x) { x.classList.remove('ativo'); });
    f.classList.add('ativo');
    var sel = f.querySelector('.ficha-ver');
    emitEvent('trocar_modelo', { modelo: sel ? sel.value : f.dataset.modelo });
  }
  fichas.forEach(function (f) {
    f.addEventListener('click', function () { selecionaFicha(f); });
    f.addEventListener('keydown', function (e) {
      if (e.target !== f) return;   // so a ficha em si seleciona pelo teclado
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
        e.preventDefault();
        selecionaFicha(f);
      }
    });
    var sel = f.querySelector('.ficha-ver');
    if (sel) {
      sel.addEventListener('click', function (e) { e.stopPropagation(); });
      sel.addEventListener('keydown', function (e) { e.stopPropagation(); });
      sel.addEventListener('change', function (e) {
        e.stopPropagation();
        f.dataset.modelo = sel.value;
        if (f.classList.contains('ativo')) emitEvent('trocar_modelo', { modelo: sel.value });
      });
    }
    var exBtn = f.querySelector('.ficha-ex-btn');
    var exPainel = f.querySelector('.ficha-ex');
    if (exBtn && exPainel) exBtn.addEventListener('click', function (e) {
      e.stopPropagation();   // CRITICO: abrir o exemplo NAO seleciona a ficha
      var abrir = exPainel.hasAttribute('hidden');
      if (abrir) exPainel.removeAttribute('hidden'); else exPainel.setAttribute('hidden', '');
      exBtn.textContent = abrir ? 'ocultar ▴' : 'ver como ele narra ▾';
    });
  });

  // TAMANHO DO TEXTO: 3 niveis, classe no <body>, lembrado em localStorage.
  var NIVEIS = ['0', '1', '2'];
  var tbtns = document.querySelectorAll('#txt-tam .tbtn');
  function aplicaTexto(nivel) {
    document.body.classList.remove('txt-nivel-0', 'txt-nivel-1', 'txt-nivel-2');
    document.body.classList.add('txt-nivel-' + nivel);
    tbtns.forEach(function (b) { b.classList.toggle('ativo', b.dataset.nivel === nivel); });
  }
  var nivelSalvo = localStorage.getItem('jogar_txt_nivel');
  if (NIVEIS.indexOf(nivelSalvo) < 0) nivelSalvo = '1';
  aplicaTexto(nivelSalvo);
  tbtns.forEach(function (b) {
    b.addEventListener('click', function () {
      aplicaTexto(b.dataset.nivel);
      localStorage.setItem('jogar_txt_nivel', b.dataset.nivel);
    });
  });

  // MODO FOCO: classe no <body>, lembrado em localStorage. Sai por ESC ou botaozinho.
  var toggle = document.getElementById('foco-toggle');
  var estado = toggle ? toggle.querySelector('.foco-estado') : null;
  function aplicaFoco(on) {
    document.body.classList.toggle('foco', on);
    if (toggle) { toggle.classList.toggle('on', on); toggle.setAttribute('aria-pressed', on ? 'true' : 'false'); }
    if (estado) estado.textContent = on ? 'Ligado' : 'Desligado';
  }
  aplicaFoco(localStorage.getItem('jogar_foco') === '1');
  if (toggle) toggle.addEventListener('click', function () {
    var novo = !document.body.classList.contains('foco');
    aplicaFoco(novo);
    localStorage.setItem('jogar_foco', novo ? '1' : '0');
  });
  var sairFoco = document.getElementById('sair-foco');
  function saiFoco() { aplicaFoco(false); localStorage.setItem('jogar_foco', '0'); }
  if (sairFoco) sairFoco.addEventListener('click', saiFoco);
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (telaConfig && !telaConfig.classList.contains('oculto')) { voltaJogo(); return; }
    if (document.body.classList.contains('foco')) saiFoco();
  });

  // ===== GUIA: animacoes de apoio (na ENTRADA) + Demonstracao animada =====
  // reduced-motion: NAO dispara animacao nenhuma; mostra o estado final parado.
  var reduz = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var guiaPane = document.querySelector('[data-pane="guia"]');
  var demo = document.querySelector('.demo');

  function triggerGuiaAnims() {
    if (reduz || !guiaPane) return;
    guiaPane.classList.remove('go');
    void guiaPane.offsetWidth;            // reflow: reinicia as animacoes de entrada
    guiaPane.classList.add('go');
  }

  function setTxt(id, t) { var e = document.getElementById(id); if (e) e.textContent = t; }
  function resetDemo() {
    if (!demo) return;
    var ac = document.getElementById('dm-acoes');
    if (ac) ac.querySelectorAll('.g-acao').forEach(function (a) { a.className = 'g-acao on'; });
    setTxt('dmv-acoes', '4');
    var gf = document.getElementById('dm-guarda');
    if (gf) { gf.style.width = '85%'; gf.style.background = '#a8564a';
      if (gf.parentElement) gf.parentElement.classList.remove('quebrou'); }
    setTxt('dmv-guarda', '17/20');
    var tf = document.getElementById('dm-tensao'); if (tf) tf.style.width = '40%';
    setTxt('dmv-tensao', '4/10');
    var vc = document.getElementById('dm-vinc'); if (vc) vc.classList.remove('usado');
  }
  function applyStepState(i) {
    if (i === 0) {                         // golpe pesado custa 3: resta 1 acao
      var ac = document.getElementById('dm-acoes');
      if (ac) { var as = ac.querySelectorAll('.g-acao'); for (var k = 1; k < as.length; k++) as[k].className = 'g-acao spent'; }
      setTxt('dmv-acoes', '1');
    } else if (i === 5) {                  // a guarda enche e QUEBRA
      var gf = document.getElementById('dm-guarda');
      if (gf) { gf.style.width = '100%'; if (gf.parentElement) gf.parentElement.classList.add('quebrou'); }
      setTxt('dmv-guarda', 'QUEBRA');
    } else if (i === 7) {                  // vinculo gasto
      var vc = document.getElementById('dm-vinc'); if (vc) vc.classList.add('usado');
    } else if (i === 8) {                  // tensao 4 -> 5
      var tf = document.getElementById('dm-tensao'); if (tf) tf.style.width = '50%';
      setTxt('dmv-tensao', '5/10');
    }
  }
  function runDemo() {
    if (!demo) return;
    var steps = demo.querySelectorAll('.demo-passo');
    if (reduz) {   // tudo de uma vez, parado, estado final
      steps.forEach(function (s, i) { s.hidden = false; s.classList.remove('in'); applyStepState(i); });
      return;
    }
    resetDemo();
    steps.forEach(function (s) { s.hidden = true; s.classList.remove('in'); });
    var i = 0;
    (function next() {
      if (i >= steps.length) return;
      steps[i].hidden = false; steps[i].classList.add('in');
      applyStepState(i);
      i++; window.setTimeout(next, 1150);
    })();
  }
  var replay = document.getElementById('demo-replay');
  if (replay) replay.addEventListener('click', runDemo);

  // dispara quando a aba Guia abre (chamado pelo handler de abas)
  window.onGuiaShown = function () { triggerGuiaAnims(); runDemo(); };
})();
"""


_DADO_JS = """
(function () {
  if (window.__dadoWired) return;
  window.__dadoWired = true;

  var zona = document.getElementById('dado-zona');
  var btn  = document.getElementById('dado-btn');
  var d1el = document.getElementById('dado-1');
  var d2el = document.getElementById('dado-2');
  var conta = document.getElementById('dado-conta');
  var faixaEl = document.getElementById('dado-faixa');
  if (!zona || !btn) return;

  var reduz = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var rollTimer = null, resolveTimer = null;
  function setEstado(e) { zona.setAttribute('data-estado', e); }
  function limpaFagulhas() {
    var fx = document.getElementById('dado-fx');
    if (!fx) return;
    var sp = fx.querySelectorAll('.koku-spark');
    for (var i = 0; i < sp.length; i++) sp[i].remove();
  }
  function limpa() {
    zona.removeAttribute('data-faixa');
    d1el.classList.remove('rolling'); d2el.classList.remove('rolling');
    d1el.textContent = '\\u2014'; d2el.textContent = '\\u2014';
    conta.textContent = ''; faixaEl.textContent = '';
    limpaFagulhas();
  }
  // KOKUSEN: 16 fagulhas dentro do #dado-fx (palco), removidas em ~1.15s.
  function kokuFagulhas() {
    var fx = document.getElementById('dado-fx');
    if (!fx) return;
    var feitas = [];
    for (var i = 0; i < 16; i++) {
      var s = document.createElement('span');
      s.className = 'koku-spark';
      s.style.left = (32 + Math.random() * 36) + '%';
      s.style.animationDelay = (Math.random() * 0.18) + 's';
      s.style.setProperty('--dx', (Math.random() * 44 - 22) + 'px');
      fx.appendChild(s); feitas.push(s);
    }
    setTimeout(function () {
      feitas.forEach(function (s) { if (s.parentNode) s.parentNode.removeChild(s); });
    }, 1150);
  }

  // ARME: e isto que o Cronista vai chamar (hoje, no MOCK, pela tecla "d").
  window.armarDado = function () {
    if (resolveTimer) { clearTimeout(resolveTimer); resolveTimer = null; }
    if (rollTimer) { clearInterval(rollTimer); rollTimer = null; }
    limpa();
    zona.hidden = false;
    setEstado('armed');
    btn.disabled = false;
  };

  function rolling() {
    setEstado('rolling');
    btn.disabled = true;
    if (reduz) return;                 // reduced-motion: nao gira nem troca numeros
    d1el.classList.add('rolling'); d2el.classList.add('rolling');   // giro spin10
    // tempero: troca os numeros por aleatorios ate o Python responder (45ms).
    rollTimer = setInterval(function () {
      d1el.textContent = (1 + Math.floor(Math.random() * 10));
      d2el.textContent = (1 + Math.floor(Math.random() * 10));
    }, 45);
  }

  btn.addEventListener('click', function () {
    if (zona.getAttribute('data-estado') !== 'armed') return;
    rolling();
    emitEvent('rolar_dado', {});       // o Python decide e devolve por __resolverDado
  });

  // RESOLUCAO: chamada pelo Python (run_javascript) com o veredito.
  window.__resolverDado = function (d1, d2, mod, dc, faixa, rotulo) {
    if (rollTimer) { clearInterval(rollTimer); rollTimer = null; }
    d1el.classList.remove('rolling'); d2el.classList.remove('rolling');  // para o giro
    d1el.textContent = d1; d2el.textContent = d2;                        // pousa nos valores REAIS
    var tot = d1 + d2 + mod;
    var ms = (mod >= 0 ? ' + ' + mod : ' - ' + (-mod));
    conta.textContent = d1 + ' + ' + d2 + ms + ' = ' + tot + ' vs ' + dc;
    faixaEl.textContent = rotulo;
    zona.setAttribute('data-faixa', faixa);
    setEstado('resolved');
    btn.disabled = true;
    // Kokusen: as fagulhas so com movimento permitido (o flash/raio/shake sao CSS via data-faixa).
    if (faixa === 'sucesso_critico' && !reduz) { kokuFagulhas(); }
    resolveTimer = setTimeout(function () {   // ~2,6s -> volta pro dormant
      zona.hidden = true;
      setEstado('dormant');
      limpa();
      resolveTimer = null;
    }, 2600);
  };

  // MOCK: tecla "d" arma a zona (gatilho de teste; nada visivel de debug).
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'd' && e.key !== 'D') return;
    var t = (e.target && e.target.tagName) || '';
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(t)) return;   // nao rouba digitacao
    window.armarDado();
  });
})();
"""


@ui.page("/jogar")
async def pagina_jogar():
    await aguardar_conexao_websocket("Abrindo a folha...")

    historico: list[dict] = []
    ocupado = False   # trava de turno: barra acao concorrente durante o await do Cronista
    geracao = 0       # token de geracao: recomecar incrementa e invalida narrar em voo
    pressao_atual = 0
    sessao_atual = SESSAO_ID   # Tier 6: rebinda quando o lifecycle abre a proxima sessao
    modelo_atual = "claude-opus-4-8"   # seletor de modelo (UI): vale a partir do proximo turno

    ui.add_head_html(_FONTS + _CSS)
    ui.html(_BODY)
    if MODO_MOCK:
        ui.add_body_html('<div class="selo-mock">modo de teste &mdash; sem IA</div>')
    # NiceGUI 3.13 remove <script> injetado no body (sanitizacao). Injetamos pela
    # porta nao-sanitizada (run_javascript): o bundle vira um <script> REAL via
    # createElement (executa, ao contrario de innerHTML) e o atmosfera-JS roda
    # direto, sem as tags. So muda a FORMA de injetar; o conteudo e o mesmo.
    ui.run_javascript(
        "if(!document.getElementById('jogar-bundle')){"
        "var s=document.createElement('script');"
        "s.id='jogar-bundle';s.src='/static/jogar.js';"
        "document.body.appendChild(s);}"
    )
    ui.run_javascript(_ATMOSFERA_JS.replace("<script>", "").replace("</script>", ""))
    # Tier 6: liga o botao "selar sessao" ao evento NiceGUI (mesmo emitEvent que o
    # bundle usa). NAO mexe no jogar.js minificado - o handler vive aqui.
    ui.run_javascript(
        "var b=document.getElementById('encerrar-sessao');"
        "if(b && !b.dataset.wired){b.dataset.wired='1';"
        "b.addEventListener('click',function(){emitEvent('jogar_encerrar',{});});}"
    )
    # Painel de Configuracoes: abre/fecha + cards de modelo (reusam 'trocar_modelo')
    # + tamanho do texto + modo foco. Mesma porta nao-sanitizada do resto do /jogar.
    ui.run_javascript(_CONFIG_JS)
    # Zona de dados (Balde 1): arme + wiring do botao + renderer. So MOSTRA; o
    # veredito vem do Python via ui.on('rolar_dado') -> __resolverDado.
    ui.run_javascript(_DADO_JS)

    def _js(code: str) -> None:
        """Dispara JS no cliente (fire-and-forget, como o resto do monolito)."""
        ui.run_javascript(code)

    def _arrive(texto: str, *, fiador: bool = False, eco: bool = False) -> None:
        opts = "{fiador:true}" if fiador else ("{eco:true}" if eco else "{}")
        corpo = _prosa_para_html(texto) if not eco else html.escape(texto.strip())
        _js(f"window.Jogar && window.Jogar.arrive({json.dumps(corpo)}, {opts})")

    # ---- streaming: pinga a narracao num unico bloco que cresce. Espelha o
    # window.Jogar.arrive (cria .glow.show em #corpo, faz fade dos anteriores,
    # rola pra cena), mas atualizavel via id '__stream'. NAO toca o jogar.js.
    def _stream_iniciar() -> None:
        # Motor de revelacao no CLIENTE: o Python so vai setar window.__rev.target
        # (barato, ver _stream_update); um loop em requestAnimationFrame REVELA os
        # chars num ritmo calmo, acelerando pra alcancar quando o servidor adianta.
        # Isso descola a velocidade que o texto APARECE da que ele CHEGA. Sem
        # 'show'/'arrive' durante a digitacao; o scroll cola embaixo no #miolo (o
        # container real de overflow), sem scrollIntoView (que recentralizava a pagina).
        # PISO e DIV controlam a velocidade (cauda da digitacao / quanto alcanca).
        _js(
            "(function(){"
            "var PISO=3, DIV=6;"
            "var n=document.getElementById('corpo');if(!n)return;"
            "n.querySelectorAll('.glow:not(.faded)').forEach(function(s){s.classList.add('faded');});"
            "var o=document.createElement('div');o.className='glow streaming';o.id='__stream';"
            "var p=document.createElement('p');var tn=document.createTextNode('');"
            "var caret=document.createElement('span');caret.className='caret';"
            "p.appendChild(tn);p.appendChild(caret);o.appendChild(p);n.appendChild(o);"
            "var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;"
            "window.__rev={tn:tn,target:'',shown:0,raf:0,cancel:false};"
            "function scroller(){return document.getElementById('miolo')||document.scrollingElement;}"
            "function frame(){"
            "var r=window.__rev;if(!r||r.cancel)return;"
            "if(r.shown>r.target.length)r.shown=r.target.length;"
            "var pend=r.target.length-r.shown;"
            "if(pend>0){"
            "var passo=reduce?pend:Math.max(PISO,Math.ceil(pend/DIV));"
            "r.shown=Math.min(r.target.length,r.shown+passo);"
            "r.tn.nodeValue=r.target.slice(0,r.shown);"
            "var sc=scroller();"
            "if(sc){var perto=(sc.scrollHeight-sc.scrollTop-sc.clientHeight)<80;"
            "if(perto)sc.scrollTop=sc.scrollHeight;}"
            "}"
            "r.raf=requestAnimationFrame(frame);"
            "}"
            "window.__rev.raf=requestAnimationFrame(frame);"
            "})();"
        )

    def _stream_update(prosa_visivel: str) -> None:
        # SO atualiza o alvo do motor (operacao barata, nao toca o DOM nem rola). O
        # motor cliente (requestAnimationFrame) revela. prosa_visivel continua vindo
        # de parte_visivel(resposta). Mesma assinatura e mesmos pontos de chamada.
        _js(f"(function(){{if(window.__rev)window.__rev.target={json.dumps(prosa_visivel)};}})();")

    def _stream_finalizar() -> None:
        # revela o que faltar de uma vez, PARA o motor, e sela em <p> definitivos com
        # a MESMA regra do _prosa_para_html (split \n\s*\n; \n->espaco; trim; descarta
        # vazios), via textContent (seguro). Vira .glow.done (layout dos blocos
        # concluidos), tira o id, cola o scroll no fim do #miolo. Proximo turno recria.
        _js(
            "(function(){"
            "var r=window.__rev;var o=document.getElementById('__stream');"
            "var txt=r?r.target:(o?o.textContent:'');"
            "if(r){r.cancel=true;if(r.raf)cancelAnimationFrame(r.raf);}"
            "if(o){o.innerHTML='';"
            "txt.split(/\\n\\s*\\n/).forEach(function(par){"
            "par=par.replace(/\\n/g,' ').trim();if(!par)return;"
            "var pp=document.createElement('p');pp.textContent=par;o.appendChild(pp);});"
            "o.classList.remove('streaming');o.classList.add('done');o.removeAttribute('id');"
            "var sc=document.getElementById('miolo')||document.scrollingElement;"
            "if(sc)sc.scrollTop=sc.scrollHeight;}"
            "window.__rev=null;})();"
        )

    def _stream_abortar() -> None:
        # PARA o motor e descarta o alvo, depois remove o bloco parcial. Recomecar no
        # meio nao deixa o motor antigo revelando texto velho (_stream_iniciar recria
        # window.__rev do zero -> proximo turno comeca limpo, sem texto fantasma).
        _js(
            "(function(){var r=window.__rev;"
            "if(r){r.cancel=true;if(r.raf)cancelAnimationFrame(r.raf);}"
            "window.__rev=null;"
            "var o=document.getElementById('__stream');if(o)o.remove();})();"
        )

    def _pondera(on: bool) -> None:
        acao = "remove" if on else "add"
        _js(f"document.getElementById('pondera') && document.getElementById('pondera').classList.{acao}('oculto')")

    async def narrar(msg_usuario: str, mostrar_acao: bool = True):
        nonlocal pressao_atual, ocupado, geracao, sessao_atual, modelo_atual
        # trava de turno: se ja ha um turno em voo, ignora a nova acao ANTES de
        # tocar o historico - senao dois "user" seguidos quebram a alternancia.
        if ocupado:
            return
        ocupado = True
        minha_geracao = geracao   # se recomecar acontecer durante o await, muda
        historico.append({"role": "user", "content": msg_usuario})

        if mostrar_acao:
            _arrive(msg_usuario, eco=True)

        # Tier 4 - memoria (1): grava SO a fala do jogador (mostrar_acao=True). A
        # abertura (mostrar_acao=False) e diretiva de ambientacao, texto fixo: NAO
        # persiste em sessao_turnos nem vira contexto. Antes ia como papel='sistema'
        # e era re-gravada a cada "adentrar", sujando o historico com [ABERTURA]
        # repetido. Agora "adentrar" varias vezes nao cria nenhuma linha no banco.
        if mostrar_acao:
            await _gravar_turno_safe(sessao_atual, "jogador", msg_usuario)

        # Tier 4 - memoria (2): carrega o contexto da cronica (5 tiers) pra sessao.
        # query_text = a fala do jogador (ajuda full-text/trigram); na abertura, None.
        query_text = msg_usuario if mostrar_acao else None
        ctx_md = await _carregar_contexto_safe(sessao_atual, query_text)

        # canal duplo - ENTRADA + Tier 4 - memoria (3): monta a ultima mensagem com
        # [ESTADO], depois a secao de contexto (ANTES da fala; omitida se vazia) e por
        # fim a fala atual. So a ultima mensagem desta chamada e enriquecida - o
        # historico guardado fica limpo.
        msgs = [m.copy() for m in historico]
        fala = msgs[-1]["content"]
        partes = [f"[ESTADO] pressao_emocional: {pressao_atual}"]
        if ctx_md:
            partes.append(f"<contexto>\n{ctx_md}\n</contexto>")
        partes.append(fala)
        msgs[-1]["content"] = "\n\n".join(partes)

        # loga e mostra o que vai pro Cronista (criterio de validacao do Tier 4).
        print("[memoria] === prompt do Cronista (ultima mensagem) ===")
        print(msgs[-1]["content"])
        print("[memoria] === fim (contexto " + ("PRESENTE" if ctx_md else "vazio") + ") ===")

        _pondera(True)
        try:
            # STREAMING: a narracao pinga num bloco que cresce em #corpo. So a
            # camada de EXIBICAO mudou - o processamento pos-resposta (estado,
            # canon, memoria) continua identico, alimentado pelo texto completo
            # acumulado no fim do stream.
            _stream_iniciar()
            resposta = ""
            if MODO_MOCK:
                # mock: gera a resposta inteira (custo zero) e pinga em pedacos,
                # pra validar o "pingando" sem gastar API. Mesmo caminho de display.
                completa = _cronista_mock(msgs)
                passo = 18
                for i in range(0, len(completa), passo):
                    if minha_geracao != geracao:
                        _stream_abortar()
                        return
                    resposta = completa[: i + passo]
                    _stream_update(parte_visivel(resposta))
                    await asyncio.sleep(0.035)
                resposta = completa
            else:
                # Opus real via stream. MESMO modelo/max_tokens/system (com
                # cache_control) de antes; SEM temperature/top_p/top_k (dao 400).
                ultimo = 0.0  # throttle do update (~60ms) pra nao martelar o browser
                async with _get_aclient().messages.stream(
                    model=modelo_atual,
                    max_tokens=800,
                    system=[
                        {
                            "type": "text",
                            "text": CRONISTA_SYSTEM_PROMPT,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    messages=msgs,
                ) as stream:
                    async for delta in stream.text_stream:
                        # recomecou no meio do stream: para de pingar e descarta.
                        if minha_geracao != geracao:
                            _stream_abortar()
                            return
                        resposta += delta
                        agora = time.monotonic()
                        if agora - ultimo >= 0.06:
                            ultimo = agora
                            _stream_update(parte_visivel(resposta))
                    final = await stream.get_final_message()
                    resposta = "".join(
                        b.text for b in final.content
                        if getattr(b, "type", None) == "text"
                    )
            # stream terminou. Se recomecou bem no fim, abandona.
            if minha_geracao != geracao:
                _stream_abortar()
                return
            # loga o que o Cronista devolveu (criterio #3 do flip MODO_MOCK=False).
            print("[memoria] === resposta do Cronista (Opus) ===")
            print(resposta)
            print("[memoria] === fim da resposta ===")
            # guarda a resposta COMPLETA (com <estado>): reforca o formato nos
            # turnos seguintes e preserva o historico de evolucao da Pressao.
            historico.append({"role": "assistant", "content": resposta})
            # canal duplo - SAIDA: separa a prosa do bloco <estado> (oculto).
            prosa, pressao_atual, atmosfera = _separar_estado(resposta, pressao_atual)
            # Tier 4 - memoria (5): grava o turno do narrador. Conteudo = a prosa
            # limpa (sem o bloco <estado>, que e maquinaria e nao vira contexto).
            # Pula na abertura (mostrar_acao=False): o turno de abertura inteiro e
            # efemero, entao "adentrar" repetido nao deixa rastro no banco.
            if mostrar_acao:
                await _gravar_turno_safe(sessao_atual, "narrador", prosa)
            # o stream ja exibiu a prosa pingando; aqui so garantimos o texto final
            # exato (sem o <estado>) e encerramos o bloco. A exibicao da narracao
            # acontece UNICA E EXCLUSIVAMENTE por estas duas chamadas.
            _stream_update(prosa)
            _stream_finalizar()
            _js(f"window.Jogar && window.Jogar.setPressao({pressao_atual})")
            # a cena so troca de pele se o Cronista pediu uma atmosfera valida;
            # senao 'atmosfera' vem None e a pele atual se mantem.
            if atmosfera:
                _js(f"window.setAtmosfera && window.setAtmosfera({json.dumps(atmosfera)})")
        except Exception as exc:
            # recomecou durante o await: nao contamina o historico ja zerado nem
            # mostra aviso de uma cena que nao existe mais.
            if minha_geracao != geracao:
                _stream_abortar()
                return
            # erro no meio do stream (rede/API): descarta o bloco parcial, mostra
            # aviso sobrio e solta a trava (no finally). Nao derruba a pagina.
            _stream_abortar()
            # a chamada falhou: o turno do jogador ficou sem resposta. Removemos
            # ele do historico, senao o proximo turno manda dois "user" seguidos
            # e a API rejeita (mensagens precisam alternar) - travaria o jogo.
            if historico and historico[-1]["role"] == "user":
                historico.pop()
            print("[ERRO CRONISTA] === traceback completo ===")
            print(traceback.format_exc())
            print("[ERRO CRONISTA] === fim ===")
            aviso = f"o Cronista vacila - {type(exc).__name__}. Tente de novo."
            _js(f"window.Jogar && window.Jogar.arrive({json.dumps(html.escape(aviso))})")
        finally:
            # so libera a trava se EU ainda sou a geracao vigente. Se um recomecar
            # me invalidou, quem manda agora e a geracao nova - nao toco no estado
            # dela (senao destravaria no meio do turno novo).
            if minha_geracao == geracao:
                _pondera(False)
                ocupado = False

    async def ao_comecar(_=None):
        _js("window.Jogar && window.Jogar.entrar()")
        await narrar(ABERTURA_MSG, mostrar_acao=False)

    async def ao_agir(e):
        args = e.args if isinstance(e.args, dict) else {}
        texto = (args.get("text") or "").strip()
        if not texto:
            return
        await narrar(texto, mostrar_acao=True)

    async def ao_recomecar(_=None):
        # zera a cena sem reiniciar o servidor: limpa historico, Pressao e tela,
        # devolve o portal de entrada. Custo zero.
        nonlocal pressao_atual, ocupado, geracao
        # invalida qualquer turno em voo (o narrar checa a geracao apos o await e
        # se abandona) e destrava. Assim recomecar no meio de um turno nao deixa
        # prosa fantasma cair na tela limpa nem o jogo preso.
        geracao += 1
        ocupado = False
        _pondera(False)
        historico.clear()
        pressao_atual = 0
        _js("window.Jogar && window.Jogar.recomecar()")
        _js("window.Jogar && window.Jogar.setPressao(0)")
        _js("window.setAtmosfera && window.setAtmosfera('ermo', {forcar:true})")

    async def ao_encerrar(_=None):
        # Tier 6: sela a sessao atual (extrai fatos -> canon -> recap) e ABRE a
        # proxima; o /jogar rebinda pra ela. O recap desta sessao vira o
        # recap_anterior da proxima (montar_contexto_narrador), entao o primeiro
        # turno da sessao nova ja chega com "o que veio antes".
        nonlocal pressao_atual, ocupado, geracao, sessao_atual
        if ocupado:
            return  # turno em voo: nao sela no meio de uma narracao
        if not _MEMORIA_OK:
            _arrive("a cronica nao pode ser selada agora - a memoria esta indisponivel.")
            return
        ocupado = True
        geracao += 1  # invalida qualquer narrar em voo, como o recomecar
        _pondera(True)
        try:
            # MODO_MOCK: Haiku mockado (zero token). Com MODO_MOCK=False, Haiku real.
            haiku_fn = _haiku_mock_jogar if MODO_MOCK else None
            res = await encerrar_sessao(sessao_atual, haiku_fn=haiku_fn)
            nova = res.get("nova_sessao_id")
            print(f"[memoria] sessao {sessao_atual} encerrada; rebind -> {nova} "
                  f"(fatos={res.get('fatos_enfileirados')}, nao_resolvidos={len(res.get('nao_resolvidos') or [])})")
            if nova:
                sessao_atual = nova  # REBIND: a proxima abertura de turno usa a nova
        except Exception as exc:  # noqa: BLE001
            print(f"[memoria] FALHA ao encerrar sessao: {type(exc).__name__}: {exc}")
            _arrive(f"a cronica resistiu a ser selada - {type(exc).__name__}. Tente de novo.")
        finally:
            _pondera(False)
            ocupado = False
        # zera a cena pro recomeco na sessao nova (o contexto dela ja tras o recap).
        historico.clear()
        pressao_atual = 0
        _js("window.Jogar && window.Jogar.recomecar()")
        _js("window.Jogar && window.Jogar.setPressao(0)")
        _js("window.setAtmosfera && window.setAtmosfera('ermo', {forcar:true})")

    async def ao_trocar_modelo(e):
        # seletor de modelo na UI: guarda a escolha; vale a partir do proximo turno.
        # nao re-renderiza nem interrompe um turno em voo (o narrar le modelo_atual
        # so quando chama o Cronista).
        nonlocal modelo_atual
        args = e.args if isinstance(e.args, dict) else {}
        novo = args.get("modelo")
        if novo:
            modelo_atual = novo
            print(f"[modelo] Cronista trocado para: {modelo_atual} (vale do proximo turno)")

    async def ao_rolar_dado(e):
        # O CEREBRO: o Python sorteia e decide a faixa; o dado so MOSTRA. MOCK por ora
        # (valores reais de MOD/DC vem do banco no Andar 2). 2d10 + mod vs DC, com a
        # REGRA HIBRIDA do critico (natural decide os extremos; margem decide o meio).
        MOD_MOCK = 2   # MOCK: modificador (vem do personagem/pericia no Andar 2)
        DC_MOCK = 12   # MOCK: dificuldade (vem da cena no Andar 2)
        d1 = random.randint(1, 10)
        d2 = random.randint(1, 10)
        if d1 == 10 and d2 == 10:
            faixa = "sucesso_critico"          # 10+10 = critico SEMPRE (natural)
        elif d1 == 1 and d2 == 1:
            faixa = "falha_critica"            # 1+1 = falha critica SEMPRE (natural)
        else:
            margem = (d1 + d2 + MOD_MOCK) - DC_MOCK
            if margem < 0:                     # limiares 0 e 2 = MOCK
                faixa = "falha"
            elif margem <= 2:
                faixa = "sucesso_parcial"
            else:
                faixa = "sucesso"
        rotulos = {
            "sucesso_critico": "Kokusen · sucesso crítico",
            "sucesso": "Sucesso",
            "sucesso_parcial": "Sucesso — com um preço",
            "falha": "Falha",
            "falha_critica": "Falha crítica",
        }
        rotulo = rotulos[faixa]
        _js(
            "window.__resolverDado && window.__resolverDado("
            f"{d1},{d2},{MOD_MOCK},{DC_MOCK},"
            f"{json.dumps(faixa)},{json.dumps(rotulo, ensure_ascii=False)})"
        )

    ui.on("jogar_action", ao_agir)
    ui.on("jogar_comecar", ao_comecar)
    ui.on("jogar_recomecar", ao_recomecar)
    ui.on("jogar_encerrar", ao_encerrar)
    ui.on("trocar_modelo", ao_trocar_modelo)
    ui.on("rolar_dado", ao_rolar_dado)
