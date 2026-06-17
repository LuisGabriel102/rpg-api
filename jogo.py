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

import html
import json
import random
import re
import traceback
from pathlib import Path

from nicegui import ui, run
from anthropic import Anthropic
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


_client = None


def _get_client() -> Anthropic:
    """Instancia o cliente Anthropic so quando o Opus real for usado. Assim o
    MODO_MOCK roda sem nenhuma credencial - o ponto do modo de teste."""
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


def _chamar_cronista(historico: list[dict], modelo: str = "claude-opus-4-8") -> str:
    if MODO_MOCK:
        return _cronista_mock(historico)
    # Opus real. O system vai como bloco com cache_control: o prefixo (prompt
    # do Cronista, estavel e byte-identico) fica em cache e os turnos seguintes
    # pagam uma fracao. Sampling continua omitido de proposito (Opus 4.8 rejeita).
    resp = _get_client().messages.create(
        model=modelo,
        max_tokens=800,
        system=[
            {
                "type": "text",
                "text": CRONISTA_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=historico,
    )
    return resp.content[0].text


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
/* --- resets p/ vencer o Quasar/NiceGUI --- */
body, .q-page, .q-page-container, .nicegui-content{ background: var(--ground) !important; }
.nicegui-content{ padding:0 !important; gap:0 !important; }
.nicegui-content > div{ width:100% !important; }
.oculto{ display:none !important; }

.alderyn-stage{
  width:100%; min-height:100vh; display:flex; align-items:center; justify-content:center;
  padding:5vh 20px; position:relative; overflow:hidden;
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

.alderyn-stage.atm-ermo  { --aura:rgba(178,98,46,.34);  --fallback:radial-gradient(130% 100% at 50% 72%, #241710, #130d09 58%, #0a0806); }
.alderyn-stage.atm-mata  { --aura:rgba(72,150,98,.28);  --fallback:radial-gradient(130% 100% at 50% 60%, #122017, #0c130d 58%, #070a08); }
.alderyn-stage.atm-frio  { --aura:rgba(96,152,192,.28); --fallback:radial-gradient(130% 100% at 50% 55%, #14202b, #0c1219 58%, #080b0e); }
.alderyn-stage.atm-sangue{ --aura:rgba(170,74,66,.32);  --fallback:radial-gradient(130% 100% at 50% 58%, #2a1110, #160b0a 58%, #0a0606); }
.alderyn-stage.atm-corte { --aura:rgba(192,152,72,.28); --fallback:radial-gradient(130% 100% at 50% 50%, #221a0e, #14100a 58%, #0a0806); }
.pagina{
  position:relative; z-index:1; width:100%; max-width:900px;
  background:
    radial-gradient(60% 50% at 6% 4%, rgba(60,42,20,.32), transparent 60%),
    radial-gradient(55% 45% at 96% 97%, rgba(50,35,18,.3), transparent 60%),
    linear-gradient(180deg, #19140d, #130f09);
  border:1px solid var(--regua2);
  box-shadow:inset 0 0 0 1px rgba(0,0,0,.4), 0 38px 100px -42px rgba(0,0,0,.8);
  padding:clamp(26px,4.6vw,46px); animation:rise .8s ease both;
}
.pagina::after{ content:""; position:absolute; inset:9px; border:1px solid var(--regua); pointer-events:none; }
@keyframes rise{ from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:none} }
@keyframes arrive{ from{opacity:0;transform:translateY(9px)} to{opacity:1;transform:none} }
@keyframes pulseglow{ 0%{opacity:.45} 40%{opacity:1} 100%{opacity:.85} }

.head{ display:flex; align-items:center; gap:12px; position:relative; z-index:2; }
.head .ttl{ font-family:"IM Fell English SC",serif !important; letter-spacing:.16em; font-size:14px; color:var(--osso); text-transform:lowercase; }
.head .fleur{ flex:none; opacity:.8; }
.head .ln{ flex:1; height:1px; background:var(--regua); }
.head .sair{ font-family:"IM Fell English",serif; font-style:italic; font-size:12px;
  color:var(--osso2); text-decoration:none; white-space:nowrap; opacity:.65;
  transition:opacity .3s ease; }
.head .sair:hover{ opacity:1; }
.head .selar{ font-family:"IM Fell English",serif; font-style:italic; font-size:12px;
  color:var(--osso2); background:none; border:none; padding:0; cursor:pointer;
  white-space:nowrap; opacity:.65; transition:opacity .3s ease, color .3s ease; }
.head .selar:hover{ opacity:1; color:var(--brasa); }
.head .sep{ color:var(--regua2); font-size:11px; opacity:.6; }
.head .engr{ font-family:"IM Fell English",serif; font-size:15px; line-height:1;
  color:var(--osso2); background:none; border:none; padding:0; cursor:pointer;
  white-space:nowrap; opacity:.65; transition:opacity .3s ease, color .3s ease; }
.head .engr:hover{ opacity:1; color:var(--brasa); }

/* marginalia: HOJE so a Pressao Emocional (0-10). Stats/Tensao ficam pro combate. */
.marg{ display:flex; align-items:center; justify-content:flex-end; gap:14px; flex-wrap:wrap;
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

.plate{ position:relative; z-index:2; margin:22px 0 6px; }
.plate .frame{ position:relative; border:1px solid var(--regua2); overflow:hidden; background:#0a0806; }
.plate img{ display:block; width:100%; height:clamp(216px,32vh,300px); object-fit:cover; object-position:55% 38%; filter:saturate(.92) contrast(1.02); }
.plate .frame::after{ content:""; position:absolute; inset:0; pointer-events:none; box-shadow:inset 0 0 64px 12px rgba(10,8,6,.82), inset 0 0 0 1px rgba(0,0,0,.5); }
.plate .cap{ font-family:"IM Fell English",serif !important; font-style:italic; font-size:11.5px; color:var(--osso2); text-align:center; margin-top:7px; letter-spacing:.03em; }

.corpo{ max-width:60ch; margin:22px auto 0; position:relative; z-index:2;
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
.adentrar{ margin-top:2.6rem; font-family:"IM Fell English SC",serif !important;
  letter-spacing:.22em; text-transform:lowercase; font-size:.95rem; color:var(--osso);
  background:transparent; border:1px solid var(--regua2); border-radius:2px;
  padding:.7rem 2.1rem; cursor:pointer; transition:all .35s ease; }
.adentrar:hover{ border-color:var(--brasa); color:#f0e6d2; background:rgba(198,122,51,.1);
  box-shadow:0 0 26px rgba(198,122,51,.18); }

/* a inscricao (input) - some ate Adentrar */
.scrawl{ display:flex; align-items:flex-end; gap:12px; margin-top:28px; position:relative; z-index:2;
  border-bottom:1px solid var(--regua2); padding-bottom:4px; }
.scrawl .recomecar-btn{ font-family:"IM Fell English SC",serif !important; letter-spacing:.12em;
  text-transform:lowercase; font-size:.72rem; color:var(--osso2); background:none; border:none;
  cursor:pointer; padding:4px 2px; transition:color .25s; white-space:nowrap; }
.scrawl .recomecar-btn:hover{ color:var(--brasa); }
.scrawl input{ flex:1; background:transparent !important; border:none !important; outline:none !important;
  color:var(--leitura) !important; font-family:"Spectral",serif !important; font-size:16px; padding:6px 2px; box-shadow:none !important; }
.scrawl input::placeholder{ color:var(--osso2); font-style:italic; font-family:"IM Fell English",serif; }
.scrawl.lit{ border-color:rgba(198,122,51,.55); }
.scrawl button.send-btn{ background:none !important; border:none !important; color:var(--osso2); cursor:pointer; padding:4px; transition:color .2s; }
.scrawl button.send-btn:hover{ color:var(--brasa); }

/* selo do modo mock */
.selo-mock{ position:fixed; top:.9rem; left:1rem; z-index:50;
  font-family:"IM Fell English SC",serif !important; font-size:.62rem; letter-spacing:.12em;
  text-transform:lowercase; color:var(--osso2); opacity:.6;
  border:1px dashed rgba(140,129,103,.5); border-radius:2px; padding:.2rem .55rem; background:rgba(14,11,8,.5); }

/* ===========================================================================
   PAINEL DE CONFIGURACOES (overlay) + leitura (tamanho do texto, modo foco).
   Casca CSS/JS pura, no mesmo registro da Gravura. Sem componentes ui.* novos.
   =========================================================================== */
.config-overlay{ position:fixed; inset:0; z-index:60; display:flex; align-items:center; justify-content:center;
  background:rgba(6,5,4,.72); -webkit-backdrop-filter:blur(2px); backdrop-filter:blur(2px); padding:20px; }
.config-box{ width:100%; max-width:520px; max-height:86vh; overflow-y:auto;
  background:#1b1712; border:1px solid var(--regua2);
  box-shadow:0 30px 90px -30px rgba(0,0,0,.85), inset 0 0 0 1px rgba(0,0,0,.4); padding:26px 28px; }
.config-titulo{ font-family:"IM Fell English",serif !important; font-size:22px; color:var(--osso);
  margin:0 0 18px; letter-spacing:.04em; }
.config-sec{ margin-bottom:22px; }
.config-sub{ font-family:"IM Fell English SC",serif !important; font-size:12px; letter-spacing:.18em;
  text-transform:lowercase; color:var(--osso2); margin:0 0 12px; padding-bottom:6px; border-bottom:1px solid var(--regua); }

/* cards de modelo (seletor de narracao) */
.modelo-cards{ display:flex; flex-direction:column; gap:9px; }
.mcard{ position:relative; display:block; width:100%; text-align:left; cursor:pointer;
  background:rgba(0,0,0,.22); border:1px solid var(--regua); padding:11px 34px 11px 13px;
  transition:border-color .25s ease, background .25s ease; }
.mcard:hover{ border-color:var(--osso2); }
.mcard.ativo{ border-color:var(--brasa); background:rgba(198,122,51,.08); }
.mcard-top{ display:flex; align-items:baseline; gap:9px; flex-wrap:wrap; }
.mcard-nome{ font-family:"IM Fell English",serif !important; font-size:16px; color:var(--osso); }
.mcard-custo{ font-family:"IM Fell English SC",serif !important; font-size:10.5px; letter-spacing:.1em;
  text-transform:lowercase; color:var(--osso2); }
.mcard-desc{ display:block; margin-top:4px; font-family:"Spectral",Georgia,serif !important;
  font-size:13px; color:var(--leitura); opacity:.78; line-height:1.45; }
.mcard-check{ position:absolute; top:10px; right:12px; color:var(--brasa); font-size:14px; opacity:0; transition:opacity .2s ease; }
.mcard.ativo .mcard-check{ opacity:1; }

/* linha generica: rotulo a esquerda, controle a direita */
.config-linha{ display:flex; align-items:center; justify-content:space-between; gap:14px; margin-bottom:12px; }
.config-rotulo{ font-family:"Spectral",Georgia,serif !important; font-size:14px; color:var(--leitura); opacity:.85; }

/* tamanho do texto: A- A A+ */
.txt-tam{ display:flex; gap:6px; }
.txt-tam .tbtn{ font-family:"IM Fell English",serif !important; color:var(--osso2);
  background:rgba(0,0,0,.22); border:1px solid var(--regua); cursor:pointer; padding:4px 11px; min-width:34px;
  transition:border-color .2s ease, color .2s ease, background .2s ease; }
.txt-tam .tbtn:nth-child(1){ font-size:12px; }
.txt-tam .tbtn:nth-child(2){ font-size:15px; }
.txt-tam .tbtn:nth-child(3){ font-size:18px; }
.txt-tam .tbtn:hover{ border-color:var(--osso2); color:var(--osso); }
.txt-tam .tbtn.ativo{ border-color:var(--brasa); color:var(--osso); background:rgba(198,122,51,.1); }

/* toggle do modo foco */
.foco-toggle{ font-family:"IM Fell English SC",serif !important; letter-spacing:.1em; text-transform:lowercase;
  font-size:12px; color:var(--osso2); background:rgba(0,0,0,.22); border:1px solid var(--regua); cursor:pointer;
  padding:5px 14px; transition:border-color .2s ease, color .2s ease, background .2s ease; }
.foco-toggle:hover{ border-color:var(--osso2); color:var(--osso); }
.foco-toggle.on{ border-color:var(--brasa); color:var(--osso); background:rgba(198,122,51,.1); }

/* botao Fechar do painel */
.config-fechar{ display:block; width:100%; margin-top:6px; font-family:"IM Fell English SC",serif !important;
  letter-spacing:.18em; text-transform:lowercase; font-size:.8rem; color:var(--osso);
  background:transparent; border:1px solid var(--regua2); cursor:pointer; padding:.6rem; transition:all .3s ease; }
.config-fechar:hover{ border-color:var(--brasa); color:#f0e6d2; background:rgba(198,122,51,.1); }

/* TAMANHO DO TEXTO: 3 niveis fixos aplicados ao container da narracao (#corpo).
   A classe vive no <body> (ancestral estavel), entao vence o clamp do .corpo. */
body.txt-nivel-0 .corpo{ font-size:16px; }
body.txt-nivel-1 .corpo{ font-size:19px; }
body.txt-nivel-2 .corpo{ font-size:23px; line-height:1.8; }

/* MODO FOCO: esconde o cromo (header, marginalia, estampa, selo), deixa narracao + input.
   A moldura da folha tambem some pra leitura limpa. */
body.foco .head, body.foco .marg, body.foco .plate, body.foco .selo-mock{ display:none !important; }
body.foco .pagina{ border-color:transparent; box-shadow:none; }
body.foco .pagina::after{ display:none; }
.sair-foco{ display:none; position:fixed; top:14px; right:16px; z-index:55;
  font-family:"IM Fell English SC",serif !important; letter-spacing:.12em; text-transform:lowercase; font-size:.66rem;
  color:var(--osso2); background:rgba(14,11,8,.6); border:1px solid var(--regua); cursor:pointer; padding:.3rem .7rem;
  opacity:.5; transition:opacity .25s ease, color .25s ease; }
.sair-foco:hover{ opacity:1; color:var(--brasa); }
body.foco .sair-foco{ display:block; }

@media (prefers-reduced-motion:reduce){ .pagina, .corpo .glow.show{ animation:none; } .pondera .ret span{ animation:none; } .alderyn-stage::after{ animation:none; } }
</style>
"""

_BODY = """
<div class="alderyn-stage atm-ermo">
  <div class="entrada-cena" aria-hidden="true"></div>
  <main class="pagina" aria-label="Folha do almanaque - tela de jogo">

    <div class="head">
      <svg class="fleur" width="16" height="14" viewBox="0 0 24 20" fill="none" stroke="#8c8167" stroke-width="1.1">
        <path d="M12 3c3 0 5 2 5 5s-2 7-5 9c-3-2-5-6-5-9s2-5 5-5z"/><path d="M3 10h6M15 10h6"/>
      </svg>
      <span class="ttl">vig&iacute;lia&nbsp;quebrada</span>
      <span class="ln"></span>
      <button type="button" class="selar" id="encerrar-sessao" title="Selar a sess&atilde;o e abrir a pr&oacute;xima">selar&nbsp;sess&atilde;o</button>
      <span class="sep">&middot;</span>
      <button type="button" class="engr" id="abrir-config" title="Configura&ccedil;&otilde;es" aria-label="Configura&ccedil;&otilde;es">&#9881;</button>
      <span class="sep">&middot;</span>
      <a class="sair" href="/oficina" title="Voltar a Oficina">&larr;&nbsp;oficina</a>
    </div>

    <div class="marg">
      <div class="pressao" id="pressao" title="Press&atilde;o Emocional">
        <span class="plab">press&atilde;o</span>
        <span class="bar"><i></i></span>
        <span class="num"><b id="pressao-num">0</b>&nbsp;/&nbsp;10</span>
      </div>
    </div>

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

    <div class="pondera oculto" id="pondera">o Cronista pondera<span class="ret"><span>.</span><span>.</span><span>.</span></span></div>

    <div class="scrawl oculto" id="scrawl">
      <button id="recomecar" class="recomecar-btn" title="Recome&ccedil;ar">recome&ccedil;ar</button>
      <input type="text" id="cmd" placeholder="aja, ou observe..." aria-label="Sua a&ccedil;&atilde;o">
      <button id="send" class="send-btn" aria-label="Inscrever">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 21l4-1L20 7a2 2 0 0 0-3-3L4 17l-1 4z"/><path d="M14 6l3 3"/></svg>
      </button>
    </div>

    <!-- painel de Configuracoes (overlay). Escondido por padrao via .oculto. -->
    <div class="config-overlay oculto" id="config-overlay">
      <div class="config-box" role="dialog" aria-label="Configura&ccedil;&otilde;es" aria-modal="true">
        <h2 class="config-titulo">Configura&ccedil;&otilde;es</h2>

        <section class="config-sec">
          <h3 class="config-sub">Narra&ccedil;&atilde;o</h3>
          <div class="modelo-cards" id="modelo-cards">
            <button type="button" class="mcard" data-modelo="claude-fable-5">
              <span class="mcard-top"><span class="mcard-nome">Fable 5</span><span class="mcard-custo">custo alto</span></span>
              <span class="mcard-desc">O mais profundo. Para as cenas que t&ecirc;m que ser perfeitas.</span>
              <span class="mcard-check" aria-hidden="true">&#10003;</span>
            </button>
            <button type="button" class="mcard ativo" data-modelo="claude-opus-4-8">
              <span class="mcard-top"><span class="mcard-nome">Opus 4.8</span><span class="mcard-custo">custo m&eacute;dio &middot; padr&atilde;o</span></span>
              <span class="mcard-desc">Equil&iacute;brio entre profundidade e custo.</span>
              <span class="mcard-check" aria-hidden="true">&#10003;</span>
            </button>
            <button type="button" class="mcard" data-modelo="claude-sonnet-4-6">
              <span class="mcard-top"><span class="mcard-nome">Sonnet 4.6</span><span class="mcard-custo">custo baixo</span></span>
              <span class="mcard-desc">Mais leve e r&aacute;pido. Cenas de transi&ccedil;&atilde;o.</span>
              <span class="mcard-check" aria-hidden="true">&#10003;</span>
            </button>
            <button type="button" class="mcard" data-modelo="claude-haiku-4-5-20251001">
              <span class="mcard-top"><span class="mcard-nome">Haiku 4.5</span><span class="mcard-custo">custo m&iacute;nimo</span></span>
              <span class="mcard-desc">O mais barato e veloz. Para jogar &agrave; vontade.</span>
              <span class="mcard-check" aria-hidden="true">&#10003;</span>
            </button>
          </div>
        </section>

        <section class="config-sec">
          <h3 class="config-sub">Leitura</h3>
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
        </section>

        <button type="button" class="config-fechar" id="config-fechar">Fechar</button>
      </div>
    </div>

    <!-- botao discreto pra sair do modo foco (alem do ESC). So aparece com body.foco. -->
    <button type="button" class="sair-foco" id="sair-foco" title="Sair do modo foco (ESC)">sair do foco</button>

  </main>
</div>
"""

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

  var overlay = document.getElementById('config-overlay');
  var abrir = document.getElementById('abrir-config');
  var fechar = document.getElementById('config-fechar');
  function mostra() { if (overlay) overlay.classList.remove('oculto'); }
  function esconde() { if (overlay) overlay.classList.add('oculto'); }
  if (abrir) abrir.addEventListener('click', mostra);
  if (fechar) fechar.addEventListener('click', esconde);
  // clicar no fundo escurecido (fora da caixa) fecha
  if (overlay) overlay.addEventListener('click', function (e) { if (e.target === overlay) esconde(); });

  // CARDS DE MODELO: reaproveitam o evento existente 'trocar_modelo' (string do modelo).
  var cards = document.querySelectorAll('#modelo-cards .mcard');
  cards.forEach(function (c) {
    c.addEventListener('click', function () {
      cards.forEach(function (x) { x.classList.remove('ativo'); });
      c.classList.add('ativo');
      emitEvent('trocar_modelo', { modelo: c.dataset.modelo });
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
    if (overlay && !overlay.classList.contains('oculto')) { esconde(); return; }
    if (document.body.classList.contains('foco')) saiFoco();
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

    def _js(code: str) -> None:
        """Dispara JS no cliente (fire-and-forget, como o resto do monolito)."""
        ui.run_javascript(code)

    def _arrive(texto: str, *, fiador: bool = False, eco: bool = False) -> None:
        opts = "{fiador:true}" if fiador else ("{eco:true}" if eco else "{}")
        corpo = _prosa_para_html(texto) if not eco else html.escape(texto.strip())
        _js(f"window.Jogar && window.Jogar.arrive({json.dumps(corpo)}, {opts})")

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
            resposta = await run.io_bound(_chamar_cronista, msgs, modelo_atual)
            # recomecou durante o await: abandona sem escrever prosa fantasma nem
            # tocar o historico (que o recomecar ja zerou).
            if minha_geracao != geracao:
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
            _arrive(prosa)
            _js(f"window.Jogar && window.Jogar.setPressao({pressao_atual})")
            # a cena so troca de pele se o Cronista pediu uma atmosfera valida;
            # senao 'atmosfera' vem None e a pele atual se mantem.
            if atmosfera:
                _js(f"window.setAtmosfera && window.setAtmosfera({json.dumps(atmosfera)})")
        except Exception as exc:
            # recomecou durante o await: nao contamina o historico ja zerado nem
            # mostra aviso de uma cena que nao existe mais.
            if minha_geracao != geracao:
                return
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

    ui.on("jogar_action", ao_agir)
    ui.on("jogar_comecar", ao_comecar)
    ui.on("jogar_recomecar", ao_recomecar)
    ui.on("jogar_encerrar", ao_encerrar)
    ui.on("trocar_modelo", ao_trocar_modelo)
