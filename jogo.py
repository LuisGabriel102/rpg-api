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
from campanha_protagonista import bloco_campanha_infancia
from ui_helpers import aguardar_conexao_websocket
from app.resolucao_2d10 import classificar_faixa, rolar_resolucao
from app.atributos import normalizar_atributo
from ficha_c import FICHA_C_CSS, FICHA_C_BODY, FICHA_C_JS

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

# ============================================================================
# FICHA_C: liga a ficha de personagem estilo C (slide-over) na rota PARALELA
# /jogar-c. O /jogar continua intocado (com_ficha=False). Aditiva: nao toca o
# motor (streaming/dado/atmosfera) nem o :root (tokens escopados em .ficha).
# ============================================================================
FICHA_C = True


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


def _faixa_vital(atual, maximo, *, recurso: str) -> "str | None":
    """Percentual -> palavra-ancora pro Cronista (ADR-008). None = nao da pra
    calcular -> formatacao cai pro numero cru. 'caido'/'vazia' e SO atual==0 exato,
    nunca por arredondamento (1/100 = por um fio, nao caido). recurso: 'vida'|'mana'."""
    if atual is None or maximo is None or maximo <= 0:
        return None
    if atual <= 0:
        return "caído" if recurso == "vida" else "vazia"
    pct = (atual / maximo) * 100
    if recurso == "vida":
        if pct >= 80: return "ileso"
        if pct >= 50: return "ferido"
        if pct >= 25: return "em sangue"
        return "por um fio"          # 1..24%
    else:  # mana
        if pct >= 80: return "plena"
        if pct >= 50: return "desgastada"
        if pct >= 25: return "rarefeita"
        return "quase seca"          # 1..24%


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


async def _resolver_sessao(personagem_id: int) -> int | None:
    """Producao (decisao ii): a sessao do /jogar nasce do PERSONAGEM carregado.
    GET-OR-CREATE: pega a sessao 'ativa' mais recente do personagem; se nao houver,
    cria uma (campanha_id herdado de personagens, numero_sessao = MAX+1, status 'ativa').
    Conserto 3: em FALHA (personagem inexistente ou banco indisponivel) retorna None.
    NUNCA cai na SESSAO_ID fixa -> nao contamina a sessao de OUTRO personagem; o caller
    mostra um aviso sobrio e nao liga os handlers de jogo. NAO toca o estado de combate."""
    try:
        from db import get_session
        from sqlalchemy import text as _t
        async with get_session() as _s:
            _r = (await _s.execute(_t(
                "SELECT id FROM sessoes WHERE personagem_id = :p AND status = 'ativa' "
                "ORDER BY numero_sessao DESC LIMIT 1"
            ), {"p": personagem_id})).mappings().first()
            if _r and _r.get("id") is not None:
                return int(_r["id"])
            # sem sessao ativa -> cria. campanha_id vem do personagem; numero_sessao = MAX+1.
            _pc = (await _s.execute(_t(
                "SELECT campanha_id FROM personagens WHERE id = :p"
            ), {"p": personagem_id})).mappings().first()
            if not _pc:
                print(f"[sessao] personagem {personagem_id} inexistente -> None (sem fallback)")
                return None
            _camp = _pc.get("campanha_id")
            _n = (await _s.execute(_t(
                "SELECT COALESCE(MAX(numero_sessao), 0) + 1 AS n FROM sessoes WHERE personagem_id = :p"
            ), {"p": personagem_id})).scalar()
            _novo = (await _s.execute(_t(
                "INSERT INTO sessoes (campanha_id, personagem_id, numero_sessao, status) "
                "VALUES (:c, :p, :n, 'ativa') RETURNING id"
            ), {"c": _camp, "p": personagem_id, "n": int(_n or 1)})).scalar()
            await _s.commit()
            print(f"[sessao] criada sessao {_novo} p/ personagem {personagem_id} (campanha {_camp}, n={_n})")
            return int(_novo)
    except Exception as _e:  # noqa: BLE001 - NAO cai na SESSAO_ID fixa (sessao de outro
        # personagem); sinaliza falha com None e o caller mostra aviso sobrio, sem escrever.
        print(f"[sessao] erro ao resolver sessao do personagem {personagem_id}: "
              f"{type(_e).__name__}: {_e} -> None (sem fallback)")
        return None


# Campanha do protagonista: personagem 8 (Gabriel Varekhor) na campanha 2 (Catedral do
# Alderyn). So essa combinacao liga o Modo Infancia (bloco no prompt + combate dormente +
# regua de crianca + ficha dormente). Qualquer outra sessao (Doran etc.) -> False, motor
# generico intacto. Best-effort: erro/banco fora -> False (degrada pro generico, nunca quebra).
INFANCIA_PERSONAGEM_ID = 8
INFANCIA_CAMPANHA_ID = 2


async def _sessao_eh_infancia(sessao_id: int | None) -> bool:
    if sessao_id is None:
        return False
    try:
        from db import get_session
        from sqlalchemy import text as _t
        async with get_session() as _s:
            _r = (await _s.execute(_t(
                "SELECT personagem_id, campanha_id FROM sessoes WHERE id = :sid"
            ), {"sid": sessao_id})).mappings().first()
        return bool(_r and _r["personagem_id"] == INFANCIA_PERSONAGEM_ID
                    and _r["campanha_id"] == INFANCIA_CAMPANHA_ID)
    except Exception as _e:  # noqa: BLE001 - degrada pro generico, nunca derruba o /jogar
        print(f"[infancia] erro ao checar sessao {sessao_id}: {type(_e).__name__}: {_e} -> False")
        return False


async def _ler_inventario(personagem_id: int) -> list[dict]:
    """Fatia inventario-EXIBICAO: le a POSSE do personagem (personagem_inventario) e
    resolve nome/descricao/raridade contra o catalogo (ref_itens) via LEFT JOIN -- cobre
    item de catalogo E item custom (COALESCE). READ-ONLY (so SELECT). Best-effort: erro
    ou personagem sem itens -> lista vazia (a ficha mostra 'Mochila vazia.'). NAO escreve."""
    try:
        from db import get_session
        from sqlalchemy import text as _t
        _sql = _t(
            "SELECT pi.id, pi.quantidade, pi.equipado, pi.slot_equipado, "
            "COALESCE(ri.nome_ptbr, pi.nome_custom)  AS nome, "
            "COALESCE(ri.descricao, pi.descricao_custom) AS descricao, "
            "ri.tipo, "
            "COALESCE(ri.raridade, 'comum')          AS raridade "
            "FROM personagem_inventario pi "
            "LEFT JOIN ref_itens ri ON ri.id = pi.item_id "
            "WHERE pi.personagem_id = :pid "
            "ORDER BY pi.equipado DESC, pi.id"
        )
        async with get_session() as _s:
            _rows = (await _s.execute(_sql, {"pid": personagem_id})).mappings().all()
    except Exception as _e:  # noqa: BLE001 - degrada sem quebrar; ficha cai pra mochila vazia
        print(f"[inventario] erro ao ler inventario do personagem {personagem_id}: "
              f"{type(_e).__name__}: {_e}")
        return []
    _itens = []
    for _r in _rows:
        _itens.append({
            "id": str(_r.get("id")),
            "nome": _r.get("nome") or "Item sem nome",
            "descricao": _r.get("descricao") or "",
            "tipo": _r.get("tipo") or "",
            "quantidade": int(_r["quantidade"]) if _r.get("quantidade") is not None else 1,
            "equipado": bool(_r.get("equipado")),
            "raridade": _r.get("raridade") or "comum",
        })
    return _itens


async def _ler_pressao(sessao_id: int) -> int:
    """Persistencia 2.6: restaura a Pressao emocional do personagem da sessao a partir
    de personagem_saude_mental.pressao_atual. Get-or-create: sem linha pro personagem ->
    cria com 0 (default da coluna) e devolve 0. Best-effort: erro -> 0 (o load nunca
    quebra por causa disto). NAO toca combate (Tensao 1-10 e outra coisa, efemera)."""
    try:
        from db import get_session
        from sqlalchemy import text as _t
        async with get_session() as _s:
            _r = (await _s.execute(_t(
                "SELECT personagem_id AS pid FROM sessoes WHERE id = :sid"
            ), {"sid": sessao_id})).mappings().first()
            if not _r or _r.get("pid") is None:
                return 0
            _pid = int(_r["pid"])
            _row = (await _s.execute(_t(
                "SELECT pressao_atual FROM personagem_saude_mental WHERE personagem_id = :pid"
            ), {"pid": _pid})).mappings().first()
            if _row and _row.get("pressao_atual") is not None:
                return int(_row["pressao_atual"])
            # sem linha ainda -> get-or-create com 0 (pressao_max/resto caem nos defaults)
            await _s.execute(_t(
                "INSERT INTO personagem_saude_mental (personagem_id, pressao_atual) "
                "VALUES (:pid, 0)"
            ), {"pid": _pid})
            await _s.commit()
            return 0
    except Exception as _e:  # noqa: BLE001 - degrada sem quebrar; load cai pra 0
        print(f"[pressao] erro ao ler pressao (sessao {sessao_id}): {type(_e).__name__}: {_e}")
        return 0


async def _gravar_pressao(sessao_id: int, valor: int) -> None:
    """Persistencia 2.6: grava a Pressao do personagem da sessao em
    personagem_saude_mental.pressao_atual. UPDATE; se nao houver linha ainda, INSERT
    (upsert manual, sem depender de constraint nomeada). Best-effort: erro -> loga e
    segue (NAO derruba o turno). UNICO write desta fatia."""
    try:
        from db import get_session
        from sqlalchemy import text as _t
        _v = int(valor)
        async with get_session() as _s:
            _r = (await _s.execute(_t(
                "SELECT personagem_id AS pid FROM sessoes WHERE id = :sid"
            ), {"sid": sessao_id})).mappings().first()
            if not _r or _r.get("pid") is None:
                return
            _pid = int(_r["pid"])
            _res = await _s.execute(_t(
                "UPDATE personagem_saude_mental SET pressao_atual = :v WHERE personagem_id = :pid"
            ), {"v": _v, "pid": _pid})
            if (_res.rowcount or 0) == 0:
                await _s.execute(_t(
                    "INSERT INTO personagem_saude_mental (personagem_id, pressao_atual) "
                    "VALUES (:pid, :v)"
                ), {"pid": _pid, "v": _v})
            await _s.commit()
    except Exception as _e:  # noqa: BLE001 - degrada sem quebrar; turno segue
        print(f"[pressao] erro ao gravar pressao (sessao {sessao_id}): {type(_e).__name__}: {_e}")


# SELECT defensivo do Bloco de Estado: tudo em UMA linha por sessao. Subqueries
# escalares (local/companheiros/combate) garantem 1 linha mesmo com 1:N. LEFT JOIN
# em personagens/personagem_mana (1:1). Campo ausente -> NULL -> some da linha.
_SQL_ESTADO = (
    "SELECT s.data_narrativa_inicio AS data, s.personagem_id AS pid, "
    "p.nome, p.classe_primaria AS classe, p.nivel, p.hp_atual, p.hp_maximo, "
    "p.status_narrativo AS status, m.mp_atual, m.mp_maximo, "
    "(SELECT ce.local_atual_desc FROM campanha_estado_atual ce "
    " WHERE ce.campanha_id = s.campanha_id LIMIT 1) AS local, "
    "(SELECT string_agg(a.nome, ', ') FROM personagem_aliados_ativos a "
    " WHERE a.sessao_id = s.id) AS companheiros, "
    "(SELECT c.estado FROM combate_ativo c WHERE c.sessao_id = s.id "
    " ORDER BY c.criado_em DESC LIMIT 1) AS combate "
    "FROM sessoes s "
    "LEFT JOIN personagens p ON p.id = s.personagem_id "
    "LEFT JOIN personagem_mana m ON m.personagem_id = s.personagem_id "
    "WHERE s.id = :sid"
)


def _uma_linha(v) -> str:
    """Texto livre do banco -> UMA linha: \\n,\\r,\\t e espacos multiplos viram um
    espaco so. Impede que um valor com quebra de linha parta o [ESTADO] ao meio
    (Correcao 2). None -> ''. """
    if v is None:
        return ""
    return " ".join(str(v).split())


async def _montar_estado_safe(sessao_id: int, pressao_atual: int, resultado_teste: str | None = None) -> str:
    """Bloco [ESTADO] do USER message: consciencia situacional do turno, puxada do
    banco (sessao -> personagem). Vai SEMPRE no USER message, nunca no system (nao
    quebra o cache do prefixo). Numeros mecanicos sao desejados aqui: o prompt (R1)
    manda o Cronista traduzir numero em efeito e nunca escreve-lo na prosa.

    Defensivo: campo ausente/null some da linha; falha total cai no bloco minimo
    (so o cabecalho [ESTADO]) = comportamento anterior. UMA info por linha; todo texto livre passa
    por _uma_linha e no fim qualquer \\n\\n e colapsado, pra nunca partir o bloco
    (senao _texto_do_jogador dividiria no meio). Labels em PT-BR (so o que
    o modelo le); o key de SAIDA do modelo segue 'pressao_emocional' (contrato/prompt)."""
    linhas = []
    if resultado_teste:
        linhas.append(f"resultado_teste: {resultado_teste}")
    try:
        from db import get_session
        from sqlalchemy import text
        async with get_session() as s:
            row = (await s.execute(text(_SQL_ESTADO), {"sid": sessao_id})).mappings().first()
            if row:
                if row["data"]:
                    linhas.append(f"data: {_uma_linha(row['data'])}")
                if row["local"]:
                    linhas.append(f"local: {_uma_linha(row['local'])}")
                if row["nome"]:
                    ident = _uma_linha(row["nome"])
                    extra = ", ".join(x for x in (
                        _uma_linha(row["classe"]) or None,
                        f"nível {row['nivel']}" if row["nivel"] is not None else None) if x)
                    if extra:
                        ident += f" ({extra})"
                    if row["status"]:
                        ident += f" — {_uma_linha(row['status'])}"
                    linhas.append(f"personagem: {ident}")
                if row["hp_atual"] is not None and row["hp_maximo"] is not None:
                    _fv = _faixa_vital(row["hp_atual"], row["hp_maximo"], recurso="vida")
                    linhas.append(f"vida: {row['hp_atual']}/{row['hp_maximo']}" + (f" ({_fv})" if _fv else ""))
                if row["mp_atual"] is not None and row["mp_maximo"] is not None:
                    _fv = _faixa_vital(row["mp_atual"], row["mp_maximo"], recurso="mana")
                    linhas.append(f"mana: {row['mp_atual']}/{row['mp_maximo']}" + (f" ({_fv})" if _fv else ""))
                linhas.append(f"companheiros: {_uma_linha(row['companheiros']) or 'nenhum'}")
                linhas.append(f"combate: {_uma_linha(row['combate']) or 'inativo'}")
                pid = row["pid"]
                if pid is not None:  # divida: RPC consultar_divida -> jsonb, guardada a parte
                    try:
                        d = (await s.execute(text("SELECT consultar_divida(:pid) AS d"),
                                             {"pid": pid})).scalar()
                        if d:
                            tier_nome = _uma_linha((d.get("tier_info") or {}).get("nome_tier"))
                            ld = f"dívida: {d.get('divida_viva', 0)} (tier {d.get('divida_tier', 0)}"
                            if tier_nome:
                                ld += f" — {tier_nome}"
                            ld += f"), convicção: {d.get('conviccao', 0)}"
                            linhas.append(ld)
                            # manifestacoes ativas: material direto da prosa (o preco na carne).
                            desc = []
                            for mf in (d.get("manifestacoes_ativas") or []):
                                if not isinstance(mf, dict):
                                    continue
                                tipo = _uma_linha(mf.get("tipo")).replace("_", " ")
                                if not tipo:
                                    continue
                                intens = mf.get("intensidade")
                                marca = tipo + (f" (int {intens})" if intens is not None else "")
                                if not mf.get("visivel", True):
                                    marca += " [oculta]"
                                desc.append(marca)
                            if desc:
                                linhas.append("manifestações ativas: " + "; ".join(desc))
                    except Exception as exc:  # noqa: BLE001
                        print(f"[estado] divida falhou: {type(exc).__name__}: {exc}")
            # TODO: campos NAO rastreados no banco (nao inventar; ficam de fora do bloco):
            #   - vigor (atual/max): nenhuma coluna no schema.
            #   - fadiga (atual/max): nenhuma coluna no schema.
            #   - clima / luz / hora do dia: nao persistido (atmosfera vem do output do narrador).
            #   - Tensao de combate (0-5, ADR-004): combate_ativo guarda estado/rodada, nao a metrica.
            #   - NPCs presentes na cena: derivavel de campanha_estado_atual.local_atual_id +
            #     location_npcs; nao ligado aqui (so 'companheiros' via personagem_aliados_ativos).
    except Exception as exc:  # noqa: BLE001
        print(f"[estado] FALHA ao montar estado: {type(exc).__name__}: {exc}")
    bloco = re.sub(r"\n{2,}", "\n", "[ESTADO]\n" + "\n".join(linhas))  # defesa final
    assert "\n\n" not in bloco, "bloco [ESTADO] tem \\n\\n interno"
    return bloco


async def _resolver_mod_atributo(sessao_id: int, atributo_cru: str) -> int:
    """Le mod_<atributo> do personagem da sessao. Fallback 0 + log se desconhecido/ausente."""
    col = normalizar_atributo(atributo_cru)
    if col is None:
        print(f"[resolver_mod] atributo desconhecido: {atributo_cru!r} -> mod 0")
        return 0
    try:
        from db import get_session
        from sqlalchemy import text
        sql = text(
            "SELECT p.mod_forca, p.mod_destreza, p.mod_constituicao, "
            "p.mod_inteligencia, p.mod_sabedoria, p.mod_carisma "
            "FROM sessoes s LEFT JOIN personagens p ON p.id = s.personagem_id "
            "WHERE s.id = :sid"
        )
        async with get_session() as s:
            row = (await s.execute(sql, {"sid": sessao_id})).mappings().first()
    except Exception as e:
        print(f"[resolver_mod] erro de banco: {e} -> mod 0")
        return 0
    if not row or row.get(col) is None:
        print(f"[resolver_mod] sem ficha/mod para sessao {sessao_id} ({col}) -> mod 0")
        return 0
    return int(row[col])


async def bonus_ataque_equipado(sessao_id: int) -> int:
    """Fatia 1 itens: soma o bonus_ataque dos itens EQUIPADOS do personagem da sessao
    (efeitos->>'bonus_ataque' de ref_itens, via personagem_inventario.equipado). So conta
    quando o valor e NUMBER no jsonb -> ignora os condicionais/formula que ficaram string.
    READ-ONLY. O combate NAO pode quebrar por item: erro ou nada equipado -> 0 (log + segue)."""
    try:
        from db import get_session
        from sqlalchemy import text as _t
        _sql = _t(
            "SELECT COALESCE(SUM((ri.efeitos->>'bonus_ataque')::int), 0) AS b "
            "FROM personagem_inventario pi "
            "JOIN ref_itens ri ON ri.id = pi.item_id "
            "JOIN sessoes s ON s.personagem_id = pi.personagem_id "
            "WHERE s.id = :sid AND pi.equipado = true "
            "AND jsonb_typeof(ri.efeitos->'bonus_ataque') = 'number'"
        )
        async with get_session() as _s:
            _b = (await _s.execute(_sql, {"sid": sessao_id})).scalar()
        return int(_b) if _b is not None else 0
    except Exception as _e:  # noqa: BLE001 - combate nao quebra por item
        print(f"[itens] erro ao somar bonus_ataque equipado: {type(_e).__name__}: {_e}")
        return 0


async def bonus_dano_equipado(sessao_id: int) -> int:
    """Fatia 1 itens (2o corte): SOMA CRUA do bonus_dano dos itens EQUIPADOS (espelho de
    bonus_ataque_equipado, so troca a chave bonus_ataque->bonus_dano). So conta NUMBER no
    jsonb -> ignora os condicionais/string. READ-ONLY. O AMORTECIMENTO nao mora aqui (ver
    _aplicar_bonus_dano); esta funcao so soma o bruto. Erro ou nada equipado -> 0 (log + segue)."""
    try:
        from db import get_session
        from sqlalchemy import text as _t
        _sql = _t(
            "SELECT COALESCE(SUM((ri.efeitos->>'bonus_dano')::int), 0) AS b "
            "FROM personagem_inventario pi "
            "JOIN ref_itens ri ON ri.id = pi.item_id "
            "JOIN sessoes s ON s.personagem_id = pi.personagem_id "
            "WHERE s.id = :sid AND pi.equipado = true "
            "AND jsonb_typeof(ri.efeitos->'bonus_dano') = 'number'"
        )
        async with get_session() as _s:
            _b = (await _s.execute(_sql, {"sid": sessao_id})).scalar()
        return int(_b) if _b is not None else 0
    except Exception as _e:  # noqa: BLE001 - combate nao quebra por item
        print(f"[itens] erro ao somar bonus_dano equipado: {type(_e).__name__}: {_e}")
        return 0


def _aplicar_bonus_dano(base: int, bruto: int) -> int:
    """Fatia 1 itens (2o corte): soma o bonus_dano AMORTECIDO ao dano-causado base. Funcao pura.
    GATE: so soma quando a faixa JA causa dano (base>0) -> item NAO ressuscita dano de falha
    nem vira acerto (isso e do bonus_ataque). Amortecido: min(3, bruto//2) -> +1->0, +2/+3->1,
    +4/+5->2, +6+->3 (teto). Aplicado ANTES do _fator_inimigo (postura/combo)."""
    if base <= 0:
        return base
    return base + min(3, bruto // 2)


# Haiku mockado pro fim de sessao enquanto MODO_MOCK=True: zero token. Devolve
# "nenhum fato duravel" - a extracao em si ja foi provada no Tier 5; aqui o foco e
# o WIRING (encerrar -> recap -> nova sessao -> rebind). Com MODO_MOCK=False, o
# encerrar_sessao usa o Haiku real (default).
def _haiku_mock_jogar(narracao: str, lista_entidades: str) -> str:
    return '{"fatos": []}'


_RE_ESTADO = re.compile(r"<estado>(.*?)</estado>", re.S | re.I)
# Fatia truncagem: fallback p/ <estado> SEM fechamento (resposta cortada no max_tokens).
# Usado SO quando o estrito falha. Captura do <estado> ate o fim do texto.
_RE_ESTADO_ABERTO = re.compile(r"<estado>(.*)$", re.S | re.I)
# aceita o label do INPUT acentuado (pressão_emocional) E o key do OUTPUT do modelo
# (pressao_emocional, ensinado pelo prompt) — sem mexer no system/contrato de saida.
_RE_PRESSAO = re.compile(r"press[aã]o_emocional\s*:\s*(\d+)", re.I)
# Combate Fatia 1 (Tensao): o Cronista acende 'combate: 1' no <estado> em briga fisica
# ativa (flag, NUNCA numero). O sistema conta a Tensao em memoria. Paralelo ao _RE_PRESSAO.
_RE_COMBATE = re.compile(r"combate\s*:\s*(1|sim|ativo)", re.I)
# Combate Fatia 3: o inimigo. O Cronista declara 'inimigo: nome | tier' (tier por perigo);
# o sistema e dono do HP (TIER_HP). Em memoria, efemero, invisivel como numero.
_RE_INIMIGO = re.compile(r"inimigo\s*:\s*(.+?)\s*\|\s*(comum|bravo|elite)", re.I)
TIER_HP = {"comum": 6, "bravo": 12, "elite": 20}
CD_TIER = {"comum": 10, "bravo": 13, "elite": 16}   # dificuldade-base por tier (fuga; arme sintetico na Fatia 2)
# Fatia 5: multiplicador do dano em VOCÊ por tier do inimigo (ponto de partida, ajustável).
TIER_DANO = {"comum": 1.0, "bravo": 1.5, "elite": 2.0}
# Fatia 10a: alvo atual escolhido pelo jogador. NAO colide com _RE_INIMIGO (que exige |tier):
# 'inimigo_alvo: nome' nao casa o regex do inimigo (sem '|'), e este exige o literal 'inimigo_alvo'.
_RE_ALVO = re.compile(r"inimigo_alvo\s*:\s*([^\n|]+)", re.I)
# Combate Fatia 4: ataque vs defesa. O Cronista marca a natureza da acao do jogador.
# defesa -> inimigo nao toma nada + dano em voce pela METADE; ataque (default) -> como antes.
_RE_ACAO = re.compile(r"acao\s*:\s*(ataque|defesa|estancar|curar|fugir)", re.I)
_RE_RECUO = re.compile(r"inimigo_recuou\s*:\s*([^\n]+)", re.I)   # Fatia 2: inimigo(s) que abandonam a luta vivos
# Fatia 8a: feridas (memoria). O Cronista nomeia UMA ferida nova so quando o sistema
# sinaliza falha_critica com inimigo. _RE_FERIDA captura o nome (uma linha).
_RE_FERIDA = re.compile(r"ferida\s*:\s*([^\n]+)", re.I)
# Fatia 6a: postura do inimigo. agressiva -> a defesa do jogador perde o desconto (custa cheio).
_RE_POSTURA = re.compile(r"postura\s*:\s*(?:([^|\n]+?)\s*\|\s*)?(neutra|agressiva|defensiva)", re.I)
# Fatia 9a: natureza do custo da acao (eixo SEPARADO da acao). OPCIONAL; ausente = fisico (caso comum).
_RE_VIA = re.compile(r"via\s*:\s*(magico|combo)", re.I)
# Corrupcao Fatia 1: o Cronista emite 'corrupcao: <peso 1-3> <sabor>' quando o jogador
# conjura magia escura. Ausente = sem corrupcao no turno. peso fora de [1-3] -> NAO casa
# (zero divida). sabor validado a parte (fora da lista -> generic). delta = peso x 5.
_RE_CORRUPCAO = re.compile(r"corrupcao\s*:\s*([1-3])\s+(\w+)", re.I)
_SABORES_CORRUPCAO = ("hemomantic", "pactomantic", "aberrant", "toxic", "fey", "generic")
# Botoes de acao (UI): o Cronista pode oferecer 'opcoes: A | B | C' no <estado> -> ate 6
# acoes clicaveis (a FASE DO FRONT desenha). Eixo SEPARADO do combate (NAO e combat-gated):
# parseado em _separar_estado, ao lado do teste_pedido. Captura o resto da linha (molde de
# linha-unica, igual _RE_FERIDA/_RE_RECUO); o split por '|' e o clamp ficam no _separar_estado.
_RE_OPCOES = re.compile(r"opcoes\s*:\s*([^\n]+)", re.I)
_MAX_OPCOES = 6   # clamp defensivo: o Cronista pode exagerar; a UI desenha no maximo 6 botoes


def _resumo_bando(inimigos):
    """Fatia 10a: resumo qualitativo do bando VIVO pro Cronista (nunca numero). Por ratio
    de hp do alvo: >0.5 inteiro; 0.25-0.5 ferido; <=0.25 cambaleando. Bando vazio -> None
    (nao injeta roster; a vitoria fala por si). Funcao pura. Substitui a tag por-alvo 'ferido'."""
    if not inimigos:
        return None
    partes = []
    for e in inimigos:
        _hpmax = e.get("hp_max") or 1
        _ratio = (e.get("hp", 0) or 0) / _hpmax
        if _ratio > 0.5:
            _cond = "inteiro"
        elif _ratio > 0.25:
            _cond = "ferido"
        else:
            _cond = "cambaleando"
        # Fatia 10b: roster mostra postura, mas SO se nao-neutra (terso; n=1-neutro fica byte-identico
        # ao 10a). Parenteses desambiguam do separador ', ' entre inimigos.
        _post = e.get("postura", "neutra")
        partes.append(f"{e['nome']} {_cond}" + (f" ({_post})" if _post != "neutra" else ""))
    return "[bando: " + ", ".join(partes) + "]"


def _atualizar_momentum(vigor_atual, vigor_maximo, inimigo):
    """Combate Fatia 7: estado de momentum (memoria, pos-roll). None se nao ha inimigo.
    momentum = ratio_jog - ratio_inim; >0.15 pressionando, <-0.15 recuando, senao equilibrado.
    limiar quando o inimigo esta a <=25% do HP (flash escuro). Funcao pura."""
    if not inimigo:
        return None
    _hpmax = inimigo.get("hp_max") or 1
    ratio_inim = (inimigo.get("hp", 0) or 0) / _hpmax
    ratio_jog = (vigor_atual or 0) / (vigor_maximo or 1)
    momentum = ratio_jog - ratio_inim
    if momentum > 0.15:
        estado = "pressionando"
    elif momentum < -0.15:
        estado = "recuando"
    else:
        estado = "equilibrado"
    return {"estado": estado, "limiar": ratio_inim <= 0.25}


# Combate Fatia 7: vignette de momentum + flash de limiar. Injetados SO no /jogar-c
# (add_head_html/add_body_html no bloco com_ficha) -> /jogar producao nao recebe nada.
_MOMENTUM_CSS = """<style>
#vignette-momentum{ position:fixed; inset:0; z-index:998; pointer-events:none; transition:opacity .6s ease; opacity:0; }
#vignette-momentum.recuando{ background:radial-gradient(ellipse at center, transparent 55%, rgba(139,0,0,.45) 100%); opacity:1; animation:vignette-pulso 2.5s ease-in-out infinite; }
#vignette-momentum.pressionando{ background:radial-gradient(ellipse at center, transparent 60%, rgba(0,0,0,.2) 100%); opacity:1; }
@keyframes vignette-pulso{ 0%,100%{opacity:.6} 50%{opacity:1} }
#flash-limiar{ position:fixed; inset:0; z-index:999; pointer-events:none; background:#000; opacity:0; animation:none; }
@keyframes flash-escuro{ 0%{opacity:0} 20%{opacity:.55} 100%{opacity:0} }
#cmd.recuando{ border-color:rgba(139,0,0,.6) !important; }
#cmd.pressionando{ border-color:rgba(60,120,60,.4) !important; }
@media (prefers-reduced-motion: reduce){ #vignette-momentum.recuando{ animation:none } }
</style>"""
_MOMENTUM_HTML = '<div id="vignette-momentum"></div><div id="flash-limiar"></div>'

# As 5 atmosferas da Gravura. O Cronista pode pedir uma trocando a pele da cena
# pelo bloco <estado> (atmosfera: X). Whitelist fechada: nome fora dela e ignorado
# (a cena mantem a atmosfera atual) - degrada sem quebrar, e blinda contra valor
# torto vindo do LLM. ESPELHA a lista no JS de window.setAtmosfera (manter juntas).
ATMOSFERAS = ("ermo", "mata", "frio", "sangue", "corte")
_RE_ATMOSFERA = re.compile(r"atmosfera\s*:\s*([a-z]+)", re.I)

# teste_pedido: o Cronista para no limiar do risco e pede o teste (Saida 1). Le
# "teste_pedido: <intencao> | <atributo> | cd <D>" do <estado> de saida. O atributo
# (forca/destreza/etc.) e cru: o codigo resolve o mod da ficha (_resolver_mod_atributo).
# O resultado da rolagem volta pro Cronista no [ESTADO] de
# entrada do proximo turno, traduzido pela tabela abaixo (linguagem, nao a key).
_RE_TESTE = re.compile(
    r"teste_pedido\s*:\s*(.+?)\s*\|\s*([A-Za-zÀ-ÿ]+)\s*\|\s*cd\s*(\d+)", re.I
)
_FAIXA_CRONISTA = {
    "sucesso_critico": "sucesso crítico",
    "sucesso": "sucesso",
    "sucesso_parcial": "sucesso parcial",
    "falha": "falha",
    "falha_critica": "falha crítica",
}


# ADR-008 3c: validador de narração via Haiku REAL. Espelha o padrão de
# narrador/memoria/fim_sessao.py (_chamar_haiku_real): cliente sync lazy global, rodado
# via asyncio.to_thread (não trava o event loop); seam haiku_fn injetável pro teste (0 token).
_VALIDADOR_PROMPT_PATH = Path(__file__).parent / "prompt_haiku_validador_narracao.md"
_VIOLACOES_NARRACAO = ("numero_cru", "moldura_esprita", "pessoa_tempo", "meta_vazado")
_haiku_validador_client = None


def _system_prompt_validador() -> str:
    """Instruções do validador = o .md até a seção '## Entrada' (a {resposta} vai no user)."""
    txt = _VALIDADOR_PROMPT_PATH.read_text(encoding="utf-8")
    idx = txt.find("## Entrada")
    return (txt[:idx] if idx != -1 else txt).strip()


def _chamar_haiku_validador(resposta: str) -> str:
    """Chama o Haiku 4.5 (SÍNCRONO — rode via asyncio.to_thread). Cliente lazy: só
    instancia no 1º uso real. Espelha _chamar_haiku_real do fim_sessao. Saída esperada:
    UMA palavra (ok | numero_cru | moldura_esprita | pessoa_tempo | meta_vazado)."""
    global _haiku_validador_client
    if _haiku_validador_client is None:
        from anthropic import Anthropic
        _haiku_validador_client = Anthropic()
    resp = _haiku_validador_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=16,
        system=_system_prompt_validador(),
        messages=[{"role": "user", "content": (
            "NARRAÇÃO A VALIDAR (valide só a prosa; ignore o bloco <estado> e tudo abaixo dele):\n"
            + resposta
        )}],
    )
    return resp.content[0].text


async def _validar_narracao(resposta: str, *, haiku_fn=None) -> "str | None":
    """ADR-008 3c: valida a PROSA via Haiku real e devolve None (limpa) ou o nome da violação
    (numero_cru | moldura_esprita | pessoa_tempo | meta_vazado). haiku_fn injetável (default =
    Haiku real, sync via to_thread); o teste passa um mock e exercita o parse sem gastar token.
    Parse FAIL-OPEN: strip().lower(); só os 4 nomes exatos viram violação; 'ok'/lixo/erro -> None
    (não dispara retry à toa)."""
    fn = haiku_fn or _chamar_haiku_validador
    try:
        raw = await asyncio.to_thread(fn, resposta)
    except Exception as _e:  # noqa: BLE001 - degrada sem quebrar; nunca trava o turno
        print(f"[validador] erro no Haiku: {type(_e).__name__}: {_e}")
        return None
    nome = (raw or "").strip().lower()
    return nome if nome in _VIOLACOES_NARRACAO else None


_CORRECAO_NARRACAO = {
    "numero_cru": "A narração anterior continha um número cru (HP, dano ou similar). Reescreva traduzindo o número em efeito sensorial — nunca o número em si.",
    "moldura_esprita": "A narração usou vocabulário proibido (alma/fantasma/espírito/demônio como ser). Reescreva usando eco, resto, Margem, Ressonância ou Cicatriz.",
    "pessoa_tempo": "A narração quebrou a voz. Reescreva em terceira pessoa, passado.",
    "meta_vazado": "A narração vazou termo de sistema (rolagem, CD, tier, nome de mecânica) na prosa. Reescreva sem nenhum termo mecânico — só o mundo.",
}


def _separar_estado(resposta: str, pressao_anterior: int) -> tuple[str, int, str | None, dict | None, list[str] | None]:
    """Separa a prosa do bloco <estado>. Devolve (prosa, nova_pressao, atmosfera, teste, opcoes).

    O bloco <estado> e maquinaria: NUNCA vai pra tela. A validacao aqui e o clamp
    0-10 da Pressao e a whitelist da atmosfera. Se o bloco faltar ou vier torto, a
    prosa passa inteira, a Pressao se mantem e a atmosfera vem None (a cena nao
    troca) - degrada sem quebrar. O 4o valor e o teste pedido pelo Cronista
    ({intencao, atributo, cd}) ou None quando a cena nao pede rolagem. O 5o valor sao
    as opcoes de acao ('opcoes: A | B | C' -> lista de ate 6 strings) ou None quando
    ausente/vazia (mesma convencao do teste: None significa "nao pediu").
    """
    m = _RE_ESTADO.search(resposta)
    if not m:
        # Fatia truncagem: <estado> pode ter vindo SEM </estado> (resposta cortada no max_tokens).
        # Tenta o fallback tolerante; so devolve "sem estado" se nem o <estado> de abertura existir.
        m = _RE_ESTADO_ABERTO.search(resposta)
    if not m:
        return resposta.strip(), pressao_anterior, None, None, None
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
    teste = None
    mt = _RE_TESTE.search(bloco)
    if mt:
        teste = {
            "intencao": mt.group(1).strip(),
            "atributo": mt.group(2).strip(),
            "cd": int(mt.group(3)),
        }
    # Botoes de acao: 'opcoes: A | B | C' -> lista de ate 6 strings. .search pega a
    # PRIMEIRA linha opcoes: (duplicata e ignorada, como teste:/corrupcao:). Split por
    # '|', strip de cada item, descarta vazios; nenhum item valido -> None (como o teste).
    opcoes = None
    mo = _RE_OPCOES.search(bloco)
    if mo:
        _itens = [o.strip() for o in mo.group(1).split("|")]
        _itens = [o for o in _itens if o]
        if _itens:
            opcoes = _itens[:_MAX_OPCOES]   # clamp defensivo no maximo 6
    return prosa, nova, atm, teste, opcoes


def _prosa_para_html(texto: str) -> str:
    """Prosa segura pra injetar via window.Jogar.arrive (vai pra innerHTML).
    Escapa HTML (a prosa vem do LLM) e converte paragrafos (linha em branco)
    em <p> separados. Quebras simples viram espaco - o corpo e justificado.
    O arrive ja envolve o todo em <p>...</p>, entao juntamos com '</p><p>'.
    """
    esc = html.escape(texto.strip())
    paras = [p.replace("\n", " ").strip() for p in re.split(r"\n\s*\n", esc)]
    return "</p><p>".join(p for p in paras if p)


async def _historico_html(sessao_id: int) -> str:
    """RESUME: repinta os turnos JA gravados (sessao_turnos, em ordem) como scrollback
    estatico, ASSADO no markup em tempo de montagem -- igual a Vida, pra sobreviver ao
    re-render do NiceGUI (injetar por JS depois seria apagado). NAO chama o Opus nem
    re-streama: so o TEXTO ja salvo.

    Formato identico ao scrollback ao vivo: jogador -> bloco 'eco' (.glow.eco / .eco-p);
    narrador/sistema -> prosa concluida (.glow.done, mesmos <p> do _prosa_para_html). A
    prosa do narrador passa pela MESMA limpeza do vivo (_separar_estado): qualquer bloco
    <estado> (maquinaria) e cortado ANTES de repintar -> nada de meta vaza pro scrollback.
    Best-effort: erro/sessao sem turnos -> '' (degrada sem quebrar, como o HUD)."""
    try:
        from db import get_session
        from sqlalchemy import text as _sa_text
        async with get_session() as _s:
            _rows = (await _s.execute(_sa_text(
                "SELECT papel, conteudo FROM sessao_turnos WHERE sessao_id = :sid "
                "ORDER BY numero_turno ASC"
            ), {"sid": sessao_id})).mappings().all()
    except Exception as _e:  # noqa: BLE001 - degrada sem quebrar, como o resto do /jogar
        print(f"[resume] erro ao ler historico da sessao {sessao_id}: {type(_e).__name__}: {_e}")
        return ""
    blocos: list[str] = []
    for _r in _rows:
        _conteudo = _r["conteudo"] or ""
        if _r["papel"] == "jogador":
            # eco do jogador: 1 linha escapada, igual ao _arrive(eco=True) + jogar.js.
            blocos.append(
                f'<div class="glow eco"><p class="eco-p">{html.escape(_conteudo.strip())}</p></div>'
            )
        else:
            # narrador/sistema: corta qualquer <estado> (defesa) e converte paragrafos.
            _prosa = _separar_estado(_conteudo, 0)[0]
            _corpo = _prosa_para_html(_prosa)
            if _corpo:
                blocos.append(f'<div class="glow done"><p>{_corpo}</p></div>')
    return "".join(blocos)


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
    # Fatia "o quadro": display=Fraunces, nav/labels=IBM Plex Mono (HUD+masthead).
    # IM Fell English/SC e JetBrains Mono PERMANECEM: a zona de leitura, a config, o
    # guia e as fichas dependem deles (grep) - removê-los quebraria fora do escopo.
    'family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400..500&'
    'family=IBM+Plex+Mono:wght@400;500;600;700&'
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
  /* Fatia "o quadro" — tokens NOVOS do HUD/masthead (paleta do mock). NAO sobrescreve
     os de leitura (--osso/--osso2/--leitura/--frio/--ground/--breu mantidos). Sem --dissol
     (mecanica morta). --osso-fraco do mock == --osso2 existente (reuso, nao duplico). */
  --painel:#1d1812; --painel2:#272017;
  --vida:#e8413a; --vida-esc:#6e1d18; --vigor:#6fae5a; --vigor-esc:#2f5524;
  --mana:#36a6e0; --mana-esc:#1a4d68; --fadiga:#9286a8; --fadiga-esc:#433a52;
  --fogo:#f0902c; --ouro:#cba94f; --ouro-viv:#e7c468; --ouro-esc:#6b521f;
  --linha:rgba(203,169,79,.22);
  /* A2: altura da gravura como FAIXA enxuta. Knob unico (o Gabriel ajusta no olho). */
  --plate-h:clamp(120px,16vh,150px);
  /* P2: largura da moldura do interlocutor (coluna ESQ do palco). Knob (ajustar no olho). */
  --col-retrato:155px;
  /* P2 ajuste: cap de altura da moldura (knob) — sem isso o aspect 4/5 vira retangulo enorme. */
  --retrato-h:clamp(180px,24vh,230px);
}
/* --- resets p/ vencer o Quasar/NiceGUI: APP-SHELL de tela cheia (pagina fixa) ---
   A pagina NAO rola: html/body/q-page travados em 100% e overflow:hidden. O
   .nicegui-content vira coluna flex de 100dvh; o wrapper que contem a cena enche
   a coluna inteira (flex:1) - sem barra de nav no topo (a navegacao virou botoes
   no card: oraculo + oficina). O scroll existe SO dentro do .miolo (e do .config-scroll). */
html, body{ height:100%; height:100dvh; margin:0; overflow:hidden; }
body, .q-page, .q-page-container, .nicegui-content{ background: var(--ground) !important; }
/* TRAVA DE ALTURA EM TODA A CADEIA (anti page-scroll, sobrevive ao re-render do NiceGUI).
   Antes a trava dependia SO do body{overflow:hidden} + a ancora 100dvh da .nicegui-content;
   os elos do meio (#app, .q-layout, .q-page, .q-page-container) ficavam overflow:visible e
   INCHAVAM se o conteudo crescesse (provado: 3869px). Aqui cada elo do topo ate o #miolo
   trava height:100% + overflow:hidden, mirado pelas classes/id que o NiceGUI/Quasar SEMPRE
   recriam no re-render. Resultado: a PAGINA nunca rola; SO o #miolo (overflow-y:auto). */
#app{ height:100%; overflow:hidden; }
.nicegui-layout, .q-layout{ height:100% !important; min-height:0 !important; overflow:hidden !important; }
.q-page-container{ min-height:0 !important; height:100%; overflow:hidden; }
.q-page{ min-height:0 !important; height:100%; overflow:hidden; }
.nicegui-content{ padding:0 !important; gap:0 !important;
  height:100vh; height:100dvh; overflow:hidden; display:flex; flex-direction:column; }
.nicegui-content > div{ width:100% !important; }
.nicegui-content > div:has(.alderyn-stage){ flex:1 1 auto; min-height:0; display:flex; flex-direction:column; }
.oculto{ display:none !important; }

.alderyn-stage{
  width:100%; flex:1 1 auto; min-height:0; display:flex; align-items:stretch; justify-content:center;
  /* Opcao B: padding VERTICAL = 0 (antes clamp(8px,1.4vh,16px), que comia ~24px do content-box
     e fazia o #tela-jogo height:100% calcular 844 em vez de 869). Agora o #tela-jogo ocupa a
     altura INTEIRA da stage; o respiro do topo vem do padding interno da propria .pagina.
     Padding HORIZONTAL mantido (margem lateral do "card"). */
  padding:0 clamp(10px,1.6vw,22px); position:relative; overflow:hidden;
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
  height:100%; min-height:0; display:flex; flex-direction:column; overflow:hidden;
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
/* B1: o turno AO VIVO assenta (tinta assentando) — fade de baixo pra cima no bloco que
   esta streamando. Comeca em .45 (nao some o texto), so o container sobe/clareia; a
   revelacao char-a-char roda por cima, intacta. O resume (.done/.eco) NAO usa isto. */
@keyframes assenta{ from{opacity:.45;transform:translateY(7px)} to{opacity:1;transform:none} }
@keyframes pulseglow{ 0%{opacity:.45} 40%{opacity:1} 100%{opacity:.85} }

.head{ display:flex; align-items:center; gap:14px; position:relative; z-index:2; flex:none; }
.head .ttl{ font-family:"Fraunces",serif !important; font-weight:600; letter-spacing:.05em; font-size:17px; color:var(--osso); text-transform:lowercase; }
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
/* Fatia "o quadro" — PELE de masthead sobre o .head existente (so visual; ids/links/.ttl
   intactos). nav/controles em IBM Plex Mono + filete dourado no rodape da barra. */
/* flex-wrap: em telas estreitas (laptop c/ escala 125-150%) os 6 controles do masthead
   nao cabem numa linha e eram CORTADOS a direita pela .pagina (overflow:hidden). Wrap
   joga a nav pra 2a linha em vez de cortar -- mesmo padrao do .head-config. O .miolo
   (flex:1) absorve a altura extra, entao nada estoura no vertical. */
.head{ column-gap:18px; row-gap:10px; flex-wrap:wrap; }
.head::after{ content:""; position:absolute; left:0; right:0; bottom:0; height:2px; pointer-events:none; z-index:0;
  background:linear-gradient(90deg,transparent,var(--ouro-esc) 20%,var(--ouro) 50%,var(--ouro-esc) 80%,transparent); }
.head .selar, .head .engr, .head .oraculo, .head .sair, .head .voltar-jogo{
  font-family:"IBM Plex Mono",monospace; text-transform:uppercase; letter-spacing:.13em; font-size:11px; }

/* ═══ HUD "o quadro" (Fatia): 4 barras + tensao + brasao + ferida. TUDO escopado sob
   .marg (nao vaza pra leitura/ficha/guia). Sem Dissolucao (.stat.d) e sem luz (fatia
   futura). Setters (window.setVida/setMana/setFerida) INTOCADOS: as barras carregam os
   mesmos seletores (.vital.vida/.mana + .bar>i + #vida-num/#vida-max + #ferida/#ferida-txt). */
.marg{ position:relative; display:flex; align-items:center; gap:clamp(12px,2.2vw,22px); flex-wrap:wrap; flex:none;
  margin-top:14px; padding:14px clamp(12px,2.4vw,22px); border-bottom:none; z-index:2;
  background:linear-gradient(180deg,var(--painel2),var(--painel)); border:1px solid var(--ouro-esc);
  box-shadow:inset 0 0 0 1px rgba(0,0,0,.5), inset 0 1px 0 rgba(231,196,104,.12), 0 8px 26px rgba(0,0,0,.45); }
.marg .canto{ position:absolute; width:11px; height:11px; border:2px solid var(--ouro); }
.marg .c1{ top:5px; left:5px; border-right:none; border-bottom:none; }
.marg .c2{ top:5px; right:5px; border-left:none; border-bottom:none; }
.marg .c3{ bottom:5px; left:5px; border-right:none; border-top:none; }
.marg .c4{ bottom:5px; right:5px; border-left:none; border-top:none; }
/* brasao: CASCA VISUAL (silhueta + rotulo). Identidade real e ficha-open = fatia futura
   (mesmo balde de Mana/Vigor/Fadiga). Sem #abreFicha aqui: FICHA_C ja monta o botao no .head. */
.marg .brasao{ display:flex; align-items:center; gap:11px; padding-right:clamp(12px,2vw,20px); border-right:1px solid var(--linha); }
.marg .retrato-mini{ position:relative; width:46px; height:46px; flex:none; }
.marg .retrato-mini .foto{ position:absolute; inset:0; border-radius:50%; overflow:hidden;
  background:radial-gradient(60% 55% at 50% 35%,#2a2118,#0e0a07 80%); border:1px solid var(--ouro-esc);
  box-shadow:0 0 0 2px rgba(0,0,0,.5), inset 0 0 12px rgba(0,0,0,.6); }
.marg .retrato-mini .foto svg{ position:absolute; bottom:-2px; left:50%; transform:translateX(-50%); width:36px; height:36px; color:#0a0806; }
.marg .quem{ display:flex; flex-direction:column; gap:3px; }
.marg .quem b{ font-family:"Fraunces",serif; font-size:15px; color:var(--osso); line-height:1; }
.marg .quem .fase{ font-family:"IBM Plex Mono",monospace; font-size:9px; letter-spacing:.2em; text-transform:uppercase; color:var(--osso2); }
/* barras */
.marg .stat{ display:flex; align-items:center; gap:9px; }
.marg .stat .ico{ width:18px; height:18px; flex:none; }
.marg .vida .ico{ color:var(--vida); filter:drop-shadow(0 0 5px rgba(232,65,58,.5)); }
.marg .vigor .ico{ color:var(--vigor); filter:drop-shadow(0 0 5px rgba(111,174,90,.5)); }
.marg .mana .ico{ color:var(--mana); filter:drop-shadow(0 0 5px rgba(54,166,224,.5)); }
.marg .fadiga .ico{ color:var(--fadiga); filter:drop-shadow(0 0 5px rgba(146,134,168,.45)); }
.marg .tensao .ico{ color:var(--fogo); filter:drop-shadow(0 0 5px rgba(240,144,44,.5)); }
/* Vigor/Fadiga sem feed nesta fatia: renderizam, marcadas como dormentes (sobrio). */
.marg .vigor, .marg .fadiga{ opacity:.6; }
.marg .bloco{ display:flex; flex-direction:column; gap:5px; }
.marg .topo{ display:flex; align-items:baseline; gap:7px; }
.marg .nm{ font-family:"IBM Plex Mono",monospace; font-size:9px; letter-spacing:.2em; text-transform:uppercase; color:var(--osso2); }
.marg .num{ font-family:"IBM Plex Mono",monospace !important; font-weight:600; font-size:13px; color:var(--osso) !important; font-variant-numeric:tabular-nums; letter-spacing:0; line-height:1; }
.marg .num small{ font-size:10px; color:var(--osso2); font-weight:400; }
.marg .bar{ width:104px; height:10px; background:#0a0806; border:1px solid var(--ouro-esc); position:relative; overflow:hidden; box-shadow:inset 0 1px 3px rgba(0,0,0,.8); }
.marg .bar>i{ position:absolute; inset:0 auto 0 0; height:100%; width:0; transition:width .7s ease; }
.marg .bar>i::after{ content:""; position:absolute; inset:0 0 55% 0; background:linear-gradient(180deg,rgba(255,255,255,.30),transparent); }
.marg .vida .bar>i{ background:linear-gradient(90deg,var(--vida-esc),var(--vida)); box-shadow:0 0 10px rgba(232,65,58,.5); }
.marg .vigor .bar>i{ background:linear-gradient(90deg,var(--vigor-esc),var(--vigor)); box-shadow:0 0 9px rgba(111,174,90,.45); }
.marg .mana .bar>i{ background:linear-gradient(90deg,var(--mana-esc),var(--mana)); box-shadow:0 0 10px rgba(54,166,224,.5); }
.marg .fadiga .bar>i{ background:linear-gradient(90deg,var(--fadiga-esc),var(--fadiga)); box-shadow:0 0 8px rgba(146,134,168,.4); }
/* .baixa (setVida/setMana mantem): so realca, nao muda o esquema */
.marg .vida.baixa .bar>i{ filter:saturate(1.25) brightness(1.1); }
.marg .vida.baixa .num{ color:var(--vida) !important; }
.marg .mana.baixa .num{ color:var(--osso2) !important; }
/* A1 — HUD dormente: vital sem valor real (—/—) sai CINZA apagado (sem cor viva). A classe
   .dormente entra no markup (Vigor/Mana/Fadiga sempre dormentes em producao; Vida condicional via
   @@VIDADORM@@) e os setters window.setVida/setMana a REMOVEM quando chega um numero real. */
.marg .stat.dormente .ico{ color:var(--osso2) !important; filter:none !important; opacity:.5; }
.marg .stat.dormente .nm{ color:var(--osso2) !important; }
.marg .stat.dormente .num{ color:var(--osso2) !important; }
.marg .stat.dormente .bar>i{ background:linear-gradient(90deg,#33302a,#514b42) !important; box-shadow:none !important; }
.marg .stat.dormente .bar>i::after{ opacity:.22; }
/* MARCO: quando um vital sai de DORMENTE -> VIVO (setVida/setMana removem .dormente), o JS
   poe .despertou NO no daquele vital por ~1.2s. Um halo de osso fraco que sobe e ASSENTA
   (a brasa que acende), sobrio, sem cor de doce, sem pulo de layout. So no vital que acordou. */
@keyframes vital-desperta{ 0%{ box-shadow:0 0 0 0 rgba(205,191,159,0); }
  28%{ box-shadow:0 0 12px 2px rgba(205,191,159,.30); }
  100%{ box-shadow:0 0 0 0 rgba(205,191,159,0); } }
.marg .stat.despertou{ animation:vital-desperta 1.1s ease both; }
@media (prefers-reduced-motion:reduce){ .marg .stat.despertou{ animation:none; } }
/* tensao — pips (vazios fora de combate, como combinado) */
.marg .tensao .pips{ display:flex; gap:5px; }
.marg .tensao .pips span{ width:12px; height:7px; background:#0a0806; border:1px solid var(--ouro-esc); }
.marg .tensao .pips span.on{ background:linear-gradient(180deg,var(--fogo),#bd6e1d); border-color:var(--fogo); box-shadow:0 0 7px rgba(240,144,44,.6); }
/* ferida nomeada — gancho do setFerida (#ferida/#ferida-txt). .oculto = global display:none. */
.marg .ferida{ margin-left:auto; display:flex; align-items:center; gap:8px; border:1px solid var(--vida-esc); background:rgba(232,65,58,.10); padding:7px 12px; }
.marg .ferida .fmark{ font-family:"IBM Plex Mono",monospace !important; font-size:11px; color:var(--vida); letter-spacing:.04em; }

/* base pronta pro combate (nao exibida hoje) */
.stamps{ display:flex; gap:15px; flex-wrap:wrap; }
.st{ display:flex; align-items:center; gap:6px; }
.tens{ display:flex; align-items:center; gap:7px; }
.tens .lab{ font-family:"IM Fell English SC",serif !important; font-size:11px; letter-spacing:.18em; color:var(--osso2); text-transform:lowercase; }
.lz{ width:9px; height:9px; transform:rotate(45deg); border:0.9px solid var(--osso2); }
.lz.on{ background:var(--brasa); border-color:var(--brasa); }

/* ───── P2: palco de 2 colunas — moldura do interlocutor | leitura ─────
   #miolo embrulha um grid: aside.interlocutor (ESQ, sticky) | article.leitura (DIR,
   contem .plate + #corpo INTACTOS). Largura da moldura = knob --col-retrato. Fora de
   combate a moldura e vazia/sobria (quadro + cantos, vinheta). Campos de combate ficam
   no markup escondidos (P3 liga). CSS portado do mock jogar_definitiva_fatia5.html. */
.palco{ display:grid; grid-template-columns:var(--col-retrato) 1fr; gap:clamp(20px,3vw,40px); align-items:start; }
.interlocutor{ position:sticky; top:8px; }
.retrato-grande{ position:relative; width:100%; aspect-ratio:4/5; max-height:var(--retrato-h); overflow:hidden;
  border:1px solid var(--ouro-esc);
  background:radial-gradient(72% 55% at 50% 36%,#2c2319,#120d08 78%),
    radial-gradient(40% 55% at 80% 26%, rgba(220,200,160,.10), transparent 60%);
  box-shadow:inset 0 0 0 1px rgba(0,0,0,.5), 0 12px 34px rgba(0,0,0,.5); }
/* marca de quadro a espera: losango ◇ fraco no centro, atras de tudo (mesmo gesto do .lz do
   cabecalho). Quando o P3 puser imagem real (z-index >=1), ela cobre a marca. */
.retrato-grande::before{ content:""; position:absolute; top:50%; left:50%; z-index:0; pointer-events:none;
  width:34px; height:34px; transform:translate(-50%,-50%) rotate(45deg);
  border:1px solid var(--osso2); opacity:.16; }
.retrato-grande::after{ content:""; position:absolute; inset:0; z-index:2; pointer-events:none;
  background:radial-gradient(82% 72% at 50% 38%, transparent 42%, rgba(0,0,0,.72)); }
.retrato-cantos span{ position:absolute; width:13px; height:13px; border:2px solid var(--ouro); z-index:4; }
.rc1{ top:6px; left:6px; border-right:none; border-bottom:none; }
.rc2{ top:6px; right:6px; border-left:none; border-bottom:none; }
.rc3{ bottom:6px; left:6px; border-right:none; border-top:none; }
.rc4{ bottom:6px; right:6px; border-left:none; border-top:none; }
.retrato-nome{ position:absolute; left:0; right:0; bottom:0; z-index:3; padding:13px 13px 11px;
  background:linear-gradient(0deg, rgba(0,0,0,.88), rgba(0,0,0,.4) 60%, transparent); }
.retrato-nome[hidden]{ display:none; }
.retrato-nome b{ display:block; font-family:"Fraunces",Georgia,serif; font-weight:600; font-size:16px; color:var(--osso); }
.retrato-nome small{ font-family:"IBM Plex Mono",monospace; font-size:9.5px; letter-spacing:.1em;
  text-transform:uppercase; color:var(--frio); }
.inimigo-vida{ height:7px; background:#0a0806; border:1px solid var(--vida-esc); margin-bottom:8px; overflow:hidden; }
.inimigo-vida[hidden]{ display:none; }
.inimigo-vida i{ display:block; height:100%; width:100%;
  background:linear-gradient(90deg,var(--vida-esc),var(--vida)); box-shadow:0 0 8px rgba(232,65,58,.5); transition:width .5s ease; }
.retrato-grande.hostil{ border-color:rgba(232,65,58,.5);
  box-shadow:inset 0 0 0 1px rgba(0,0,0,.5), inset 0 0 50px rgba(232,65,58,.2), 0 12px 34px rgba(0,0,0,.5); }
.retrato-grande.hostil .retrato-nome small{ color:var(--vida); }
.leitura{ min-width:0; }
/* estreito: 1 coluna; a moldura vira FAIXA (chip) em cima da prosa, sempre visivel. */
@media (max-width: 860px){
  .palco{ grid-template-columns:1fr; gap:18px; }
  .interlocutor{ position:static; display:flex; flex-direction:row; align-items:center; gap:16px; }
  .retrato-grande{ width:128px; flex:none; }
}

.plate{ position:relative; z-index:2; margin:0 0 6px; animation:plate-in 1.4s ease both; }
.plate .frame{ position:relative; border:1px solid var(--regua2); overflow:hidden; background:#0a0806; }
/* Ken Burns LENTISSIMO: scale 1 -> 1.04 num ciclo longo, ida e volta (transform-only,
   nao mexe no layout). O .frame ja tem overflow:hidden, entao o zoom nunca vaza. */
.plate img{ display:block; width:100%; height:var(--plate-h); object-fit:cover; object-position:55% 38%; filter:saturate(.92) contrast(1.02);
  transform-origin:52% 42%; animation:kenburns 26s ease-in-out 1s infinite alternate; will-change:transform; }
@keyframes plate-in{ from{opacity:0} to{opacity:1} }
@keyframes kenburns{ from{transform:scale(1)} to{transform:scale(1.04)} }
.plate .frame::after{ content:""; position:absolute; inset:0; pointer-events:none; box-shadow:inset 0 0 64px 12px rgba(10,8,6,.82), inset 0 0 0 1px rgba(0,0,0,.5); }
/* B2: grao levissimo (textura SVG estatica, sem asset novo) por cima da imagem — z-index
   acima do <img> estatico, abaixo da vinheta. Atmosfera, nao efeito. */
.plate .frame::before{ content:""; position:absolute; inset:0; z-index:3; pointer-events:none; opacity:.05; mix-blend-mode:overlay;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"); }
/* B2: flicker de vela — camada quente por cima cujo brilho varia MUITO pouco, devagar e
   meio irregular (so opacity, barato). Quase imperceptivel: luz tremendo de leve. */
.plate::after{ content:""; position:absolute; inset:0; z-index:3; pointer-events:none; mix-blend-mode:screen;
  background:radial-gradient(58% 50% at 50% 40%, rgba(240,170,80,.06), transparent 72%); animation:vela 7.3s ease-in-out infinite; }
@keyframes vela{ 0%{opacity:.55} 18%{opacity:.86} 32%{opacity:.62} 51%{opacity:1} 67%{opacity:.7} 83%{opacity:.92} 100%{opacity:.58} }

.corpo{ max-width:min(640px,64ch); margin:8px auto 0; padding:0 16px; position:relative; z-index:2;
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
.corpo .glow.streaming{ white-space:pre-wrap; text-align:left; hyphens:none; -webkit-hyphens:none; animation:assenta .55s ease both; }
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

/* FASE FRONT: rodape de opcoes de acao. Botoes sobrios (cinza-bruxo), iguais em qualquer
   cena - sem cor de combate/exploracao. Sao sugestao, nao trilho: o clique so preenche o
   #cmd e foca; o jogador confirma com Enter. Some quando vazio (.oculto global). */
.opcoes{ display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; position:relative; z-index:2; flex:none; }
.opcao{ font-family:"IM Fell English",serif !important; font-size:14px; letter-spacing:.01em;
  color:var(--osso2); background:rgba(140,140,140,.06); border:1px solid var(--regua2);
  border-radius:5px; cursor:pointer; min-height:38px; padding:6px 14px; text-align:left;
  transition:background .18s ease, border-color .18s ease, color .18s ease; }
.opcao:hover{ background:rgba(140,140,140,.13); border-color:var(--osso2); color:var(--osso); }
.opcao:focus-visible{ outline:2px solid var(--osso2); outline-offset:2px; }
/* TATEIS: a opcao escolhida trava (realce sobrio, cinza-bruxo) e os IRMAOS desabilitam ate o
   proximo turno redesenhar (setOpcoes). Anti-confusao: o clique so PRE-PREENCHE o #cmd; o
   envio e o Enter/send (intocado). */
.opcao.escolhida{ background:rgba(203,169,79,.14); border-color:var(--osso); color:var(--osso); }
.opcoes.travada .opcao:not(.escolhida){ opacity:.4; pointer-events:none; }

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

/* CONFORTO DE LEITURA: cluster sobrio no topo-direita da area de leitura (A- / A+ /
   modo leitura). Reusa o sistema de fonte (txt-nivel) e o modo foco; nao entra na lista
   que o foco esconde -> SOBREVIVE ao modo leitura (pra dar pra sair). pointer-events so
   nos botoes -> a faixa larga (sticky) nao bloqueia clique na prosa por baixo. */
.leitura-ctrl{ position:sticky; top:6px; z-index:6; display:flex; justify-content:flex-end; gap:5px;
  margin:0 0 4px; pointer-events:none; opacity:.32; transition:opacity .25s ease; }
.leitura-ctrl:hover, .leitura-ctrl:focus-within{ opacity:1; }
.leitura-ctrl button{ pointer-events:auto; font-family:"IM Fell English SC",serif !important;
  letter-spacing:.06em; text-transform:lowercase; font-size:.72rem; color:var(--osso2);
  background:rgba(14,11,8,.55); border:1px solid var(--regua); border-radius:5px; cursor:pointer;
  min-width:30px; min-height:30px; padding:0 8px;
  transition:color .2s ease, border-color .2s ease, background .2s ease; }
.leitura-ctrl button:hover{ color:var(--brasa); border-color:var(--brasa); }
.leitura-ctrl button:focus-visible{ outline:2px solid #f0e6d2; outline-offset:2px; }
.leitura-ctrl .lc-leitura.on{ color:var(--brasa); border-color:var(--brasa); background:rgba(198,122,51,.14); }
@media (prefers-reduced-motion: reduce){ .leitura-ctrl{ transition:none; } }

/* ===========================================================================
   ZONA DE DADOS (Balde 1): 2d10 + 2 criticos + 5 faixas. O Python e o cerebro; o
   dado so MOSTRA. Maquina: dormant(hidden) -> armed -> rolling -> resolved -> dormant.
   Paleta REAL (--brasa ambar, --t-sangue sangue, --osso osso); so transform/opacity
   nas animacoes; tom witcher-grey (lento, baixa amplitude), no espirito de plate-in/
   kenburns/arrive. Estados por data-estado; desenho do resultado por data-faixa.
   =========================================================================== */
/* card rico (porte do mock .card-dados): moldura + cantos dourados + info do teste
   (rotulo / atributo · contra CD) + mod separado + linha de resultado. Os DADOS (losango
   d10), as 5 faixas e o palco de fx (.dado-fx) seguem identicos abaixo — so a APARENCIA
   ao redor mudou; a fiacao (window.armarDado/__resolverDado/data-faixa) e a MESMA. */
.dado-zona{ position:relative; z-index:2; max-width:min(560px,94%); margin:22px auto 8px;
  display:flex; align-items:center; flex-wrap:wrap; gap:clamp(12px,2.2vw,20px);
  padding:14px clamp(16px,2.4vw,22px);
  background:linear-gradient(180deg,var(--painel2),var(--painel)); border:1px solid var(--ouro-esc);
  box-shadow:inset 0 0 0 1px rgba(0,0,0,.5), inset 0 1px 0 rgba(231,196,104,.1), 0 10px 28px rgba(0,0,0,.5);
  animation:dado-in .5s ease both; }
.dado-zona[hidden]{ display:none; }
.dado-zona .cd-cantos span{ position:absolute; width:11px; height:11px; border:2px solid var(--ouro); }
.dado-zona .cdc1{ top:5px; left:5px; border-right:none; border-bottom:none; }
.dado-zona .cdc2{ top:5px; right:5px; border-left:none; border-bottom:none; }
.dado-zona .cdc3{ bottom:5px; left:5px; border-right:none; border-top:none; }
.dado-zona .cdc4{ bottom:5px; right:5px; border-left:none; border-top:none; }
.dado-zona .cd-info{ display:flex; flex-direction:column; gap:4px; padding-right:clamp(12px,2vw,18px); border-right:1px solid var(--linha); }
.dado-zona .cd-rotulo{ font-family:"Spectral",Georgia,serif !important; font-size:15px; color:var(--osso); line-height:1.15; }
.dado-zona .cd-detalhe{ font-family:"JetBrains Mono",monospace !important; font-size:10px; letter-spacing:.12em; text-transform:uppercase; color:var(--osso2); }
.dado-zona .cd-detalhe b{ color:var(--brasa); font-weight:600; }
.dado-zona .dado-op, .dado-zona .cd-mod{ font-family:"JetBrains Mono",monospace !important; color:var(--osso2); font-size:15px; }
.dado-zona .cd-mod{ font-weight:600; color:var(--osso); }
.dado-zona .cd-resultado{ display:flex; flex-direction:column; gap:2px; min-width:0; }
.dado-zona .dado-btn{ margin-left:auto; }
.dado-par{ position:relative; display:flex; align-items:center; gap:12px; }
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

/* TELAS BAIXAS (laptop c/ zoom Windows 125-150% -> viewport vertical curto). NADA e
   cortado hoje (a coluna e flex-start: #miolo cede via min-height:0), MAS em telas
   muito baixas o masthead+HUD quebram em 2-3 linhas e a GRAVURA (piso 216px) enche o
   pouco que sobra do #miolo, espremendo a prosa a quase nada. Aqui compactamos SO o
   chrome fixo (margens/paddings) e encolhemos a gravura, devolvendo altura util ao
   #miolo. Telas altas ficam INTOCADAS. So o #miolo cede; head/marg/scrawl seguem inteiros. */
@media (max-height: 720px){
  .pagina{ padding-top:clamp(10px,1.2vw,18px); padding-bottom:clamp(10px,1.2vw,18px); }
  .marg{ margin-top:8px; padding:9px clamp(12px,2.4vw,22px); }
  .marg .retrato-mini{ width:38px; height:38px; }
  .plate{ margin:10px 0 4px; }
  .plate img{ height:clamp(110px,20vh,200px); }
  .corpo{ margin-top:12px; min-height:0; }
  .scrawl{ margin-top:10px; }
}
/* Zoom EXTREMO (150%+ -> viewport vertical ~512px): masthead+HUD ja ocupam ~2 linhas
   cada; aqui a GRAVURA daria so estorvo e empurraria a prosa toda pro scroll. Escondemos
   a estampa (mesmo gesto do modo foco, .plate ja some la) pra a prosa ter a area do
   #miolo inteira. Nada de cortar barra: head/HUD/scrawl seguem; so a decoracao sai. */
@media (max-height: 560px){
  .plate{ display:none; }
}

@media (prefers-reduced-motion:reduce){
  .pagina, .corpo .glow.show, .corpo .glow.streaming{ animation:none; }
  .caret{ animation:none; opacity:.7; }   /* o motor revela tudo de uma vez; caret estatico */
  .pondera .ret span{ animation:none; }
  .alderyn-stage::after{ animation:none; }
  /* atmosfera da tela do jogo: tudo PARADO no estado final */
  .plate, .plate img, .plate::after, .bruma{ animation:none; }
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
/* rolo da medula */
.g-medula{ display:flex; align-items:center; justify-content:center; gap:22px; padding:14px 0; margin-top:8px; color:var(--osso2); }
.g-medula i{ font-size:40px; }
.g-medula i:first-child{ color:var(--brasa); }

/* ====== GUIA: sub-secoes + O COMBATE ====== */
.g-secao{ font-family:"IM Fell English",serif !important; font-size:17px; color:var(--brasa);
  letter-spacing:.02em; margin:6px 0 12px; padding-bottom:6px; border-bottom:1px solid var(--regua2); }
.guia-grupo{ display:flex; flex-direction:column; gap:14px; margin-bottom:24px; }
.g-abertura{ font-family:"Spectral",Georgia,serif !important; font-size:13.5px; color:var(--leitura); line-height:1.55; margin:0 0 8px; }
.forno-selo{ font-family:"Spectral",Georgia,serif !important; font-style:italic; font-size:12.5px;
  color:var(--osso2); line-height:1.5; margin:0 0 14px; padding:10px 12px;
  border:1px solid rgba(173,135,68,.40); border-left:2px solid var(--t-ambar);
  border-radius:4px; background:rgba(173,135,68,.06); }
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
    txt = "Magia em Alderyn não cobra só mana. A magia que toca o proibido — sangue, pactos, o que vem da Margem — deixa uma dívida. Ela não é castigo: é cláusula. Você pediu poder, e o mundo anotou o preço. A dívida se acumula e quase nunca volta atrás. Quem entende o que assina administra o saldo; quem não entende paga sem saber, e o mundo cobra com juros. No limite, a dívida cobra tudo de uma vez — o que você invocou refaz você à imagem dele, e quem sai do outro lado já não é quem entrou."
    fecho = "Todo feitiço grande tem dois preços: o que custa agora, e o que cobra de quem você é."
    vis = ('<div class="g-medrow">'
           '<div class="g-medcol"><span class="g-medcap">a dívida sobe</span>'
           '<div class="g-divida"><i class="g-dfill"></i></div></div>'
           '<div class="g-medcol"><span class="g-medcap">o limite</span>'
           '<div class="g-dissol">vira outro</div></div></div>')
    return f'{vis}<p class="g-txt">{html.escape(txt)}</p><p class="g-fecho">{html.escape(fecho)}</p>'


def _g_tensao():
    txt = "A Tensão é o calor da luta. Sobe a cada troca de golpes e deixa todo mundo mais perigoso — você e o inimigo. Mas nasce e morre na briga: quando o combate acaba, a Tensão some. É um peso que existe só enquanto o aço está no ar."
    fecho = "A Tensão sobe enquanto a luta dura. Acabou a luta, foi-se a Tensão."
    vis = ('<div class="g-medrow">'
           '<div class="g-medcol"><span class="g-medcap" style="color:#c67a33">Tensão <i class="ti ti-arrows-vertical" aria-hidden="true"></i></span>'
           '<div class="g-med tensao"><i style="width:62%"></i></div>'
           '<span class="g-medsub">sobe e desce — some na luta</span></div></div>')
    return f'{vis}<p class="g-txt">{html.escape(txt)}</p><p class="g-fecho">{html.escape(fecho)}</p>'


def _g_medula():
    txt = "Quando sua Vida chega a zero, você não morre na hora — você rola pela própria carne. É o Rolo da Medula: o lance que decide se você se agarra à consciência ou apaga. Mas a morte em Alderyn tem memória. Cada vez que você cai e volta, fica uma dívida que nunca se paga, e o próximo Rolo da Medula vem mais difícil que o anterior. Voltar não é de graça — é um empréstimo, e os juros se acumulam. E há quem diga que, quando o último dado cai errado e tudo deveria acabar, você não fica totalmente sozinho no escuro. Mas esse é um trato pra outra hora."
    fecho = "Você pode voltar. Mas cada volta custa mais que a anterior."
    vis = ('<div class="g-medula"><i class="ti ti-dice-5" aria-hidden="true"></i>'
           '<i class="ti ti-bone" aria-hidden="true"></i></div>')
    return f'{vis}<p class="g-txt">{html.escape(txt)}</p><p class="g-fecho">{html.escape(fecho)}</p>'


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
_FORNO_SELO = ("No Forno — ainda não no jogo. O combate de Alderyn é mais fundo do que o jogo "
               "alcança hoje. Estas peças estão sendo forjadas; o guia as mostra como promessa, "
               "não como regra atual.")


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


# SECAO 1 - "Ja no Jogo": o que ja roda hoje. Ferimentos veio do combate pra ca.
_GUIA = [
    ("columns-3", "Os Cinco Pilares", "de onde vem o que você faz", _g_pilares),
    ("battery-3", "As Quatro Barras", "o que mantém você de pé", _g_barras),
    ("dice-5", "A Rolagem", "como o destino responde", _g_rolagem),
    ("flask-2", "O Custo da Magia", "poder não é de graça", _g_magia),
    ("activity", "Tensão", "o calor da luta", _g_tensao),
    ("bandage", "Ferimentos", "dano que vira história", _c_ferimentos),
]

# SECAO 2 - "No Forno": ainda nao no jogo. Medula veio do sistema pra ca.
_COMBATE = [
    ("coins", "A Economia da Luta", "ação é moeda", _c_economia),
    ("shield-bolt", "A Guarda e a Quebra", "o ritmo do combate", _c_guarda),
    ("swords", "O Ritmo das Ações", "rápida, firme ou pesada", _c_ritmo),
    ("target-arrow", "Posição e Efeito", "o risco e o tamanho", _c_posicao),
    ("heart-handshake", "Lutar Acompanhado", "alguém pra te cobrir", _c_acompanhado),
    ("bone", "O Rolo da Medula", "quando o corpo chega ao fim", _g_medula),
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
        '<h3 class="g-secao">Já no Jogo</h3>'
        f'<div class="guia-grupo">{sistema}</div>'
        '<h3 class="g-secao">No Forno</h3>'
        f'<div class="forno-selo">{html.escape(_FORNO_SELO)}</div>'
        f'<p class="g-abertura">{html.escape(_COMBATE_ABERTURA)}</p>'
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
      <a class="oraculo" href="/sistema" title="Como o sistema funciona">sistema</a>
      <a class="sair" href="/oficina" title="Voltar &agrave; oficina">&larr;&nbsp;oficina</a>
    </div>

    <div class="marg">
      <span class="canto c1"></span><span class="canto c2"></span><span class="canto c3"></span><span class="canto c4"></span>

      <div class="brasao">
        <div class="retrato-mini"><div class="foto">
          <svg viewBox="0 0 100 100" fill="currentColor" aria-hidden="true"><ellipse cx="50" cy="40" rx="16" ry="19"/><path d="M50 58 C33 58 19 70 17 100 L83 100 C81 70 67 58 50 58Z"/></svg>
        </div></div>
        <div class="quem"><b>&mdash;</b><span class="fase">vig&iacute;lia&nbsp;quebrada</span></div>
      </div>

      <div class="stat vital vida @@VIDABAIXA@@ @@VIDADORM@@" title="Vida">
        <svg class="ico" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 20.5C7 17 3.5 13.6 3.5 9.6 3.5 7 5.4 5.2 7.8 5.2c1.5 0 2.9.8 3.7 2 .8-1.2 2.2-2 3.7-2 2.4 0 4.3 1.8 4.3 4.4 0 4-3.5 7.4-8.5 10.9z"/></svg>
        <div class="bloco"><div class="topo"><span class="nm">vida</span><span class="num"><b id="vida-num">@@VIDANUM@@</b><small>/<span id="vida-max">@@VIDAMAX@@</span></small></span></div>
          <span class="bar"><i style="width:@@VIDAPCT@@%"></i></span></div>
      </div>

      <div class="stat vigor dormente" title="Vigor">
        <svg class="ico" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z"/></svg>
        <div class="bloco"><div class="topo"><span class="nm">vigor</span><span class="num">&mdash;<small>/&mdash;</small></span></div>
          <span class="bar"><i style="width:100%"></i></span></div>
      </div>

      <div class="stat vital mana dormente" title="Mana">
        <svg class="ico" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2l6 7-6 13-6-13 6-7z"/></svg>
        <div class="bloco"><div class="topo"><span class="nm">mana</span><span class="num"><b id="mana-num">&mdash;</b><small>/<span id="mana-max">&mdash;</span></small></span></div>
          <span class="bar"><i style="width:100%"></i></span></div>
      </div>

      <div class="stat fadiga dormente" title="Fadiga">
        <svg class="ico" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M6 2h12v4l-4 6 4 6v4H6v-4l4-6-4-6V2zm2.5 2.2L12 9l3.5-4.8H8.5z"/></svg>
        <div class="bloco"><div class="topo"><span class="nm">fadiga</span><span class="num">&mdash;<small>/&mdash;</small></span></div>
          <span class="bar"><i style="width:0%"></i></span></div>
      </div>

      <div class="stat tensao" title="Tens&atilde;o">
        <svg class="ico" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2c1.5 3.5 4.5 4.8 4.5 8.5a4.5 4.5 0 0 1-9 0c0-1.6.7-2.8 1.6-3.7-.2 1.8.7 2.8 1.6 3 .8-2.2-.8-4.3.3-7.8z"/></svg>
        <div class="bloco"><div class="topo"><span class="nm">tens&atilde;o</span></div>
          <div class="pips"><span></span><span></span><span></span><span></span><span></span></div></div>
      </div>

      <div class="ferida oculto" id="ferida"><span class="fmark" id="ferida-txt"></span></div>
    </div>

    <!-- MIOLO: a unica zona que rola (cena + narracao). -->
    <div class="miolo" id="miolo">
      <!-- P2: palco de 2 colunas. Moldura do interlocutor (ESQ, sticky) | leitura (DIR)
           que CONTEM .plate + #corpo INTACTOS. #corpo NAO muda (id/conteudo/stream/resume). -->
      <div class="palco">
        <aside class="interlocutor">
          <!-- moldura vazia sobria (um espaco quieto, a espera). Campos de combate prontos
               no markup mas escondidos -> P3 liga (#retratoNome/#retratoEstado/#inimigoVida/.hostil). -->
          <div class="retrato-grande" id="retrato">
            <span class="retrato-cantos"><span class="rc1"></span><span class="rc2"></span><span class="rc3"></span><span class="rc4"></span></span>
            <div class="retrato-nome" id="retrato-nome" hidden>
              <div class="inimigo-vida" id="inimigoVida" hidden><i id="ivBar" style="width:100%"></i></div>
              <b id="retratoNome"></b><small id="retratoEstado"></small>
            </div>
          </div>
        </aside>

        <article class="leitura">
          <div class="leitura-ctrl" role="group" aria-label="Conforto de leitura">
            <button type="button" id="lc-menor" aria-label="Diminuir o texto" title="Texto menor">A&minus;</button>
            <button type="button" id="lc-maior" aria-label="Aumentar o texto" title="Texto maior">A+</button>
            <button type="button" id="lc-leitura" class="lc-leitura" aria-pressed="false" aria-label="Modo leitura" title="Modo leitura (esconde o HUD)">leitura</button>
          </div>
          <figure class="plate">
            <div class="frame"><img src="/static/estampa_porta.webp" alt="Gravura: uma porta arqueada entreaberta, com uma fresta de luz e degraus de pedra"></div>
          </figure>

          <div class="corpo" id="corpo">
            <div class="portal@@PORTAL_OFF@@" id="portal">
              <div class="portal-nome">Vig&iacute;lia Quebrada</div>
              <div class="portal-traco"></div>
              <button id="adentrar" class="adentrar">adentrar</button>
            </div>
@@HISTORICO@@
          </div>
        </article>
      </div>

      <!-- ZONA DE DADOS (Balde 1): so MOSTRA; o Python decide. Comeca oculta (dormant).
           O Cronista a "arma" (window.armarDado) -> botao libera. ids estaveis (JS depende). -->
      <div class="dado-zona" id="dado-zona" data-estado="dormant" aria-live="polite" hidden>
        <span class="cd-cantos"><span class="cdc1"></span><span class="cdc2"></span><span class="cdc3"></span><span class="cdc4"></span></span>
        <div class="cd-info">
          <span class="cd-rotulo" id="dado-rotulo">o momento pede um lance</span>
          <span class="cd-detalhe"><span id="dado-atributo">&mdash;</span> &middot; contra <b id="dado-cd">&mdash;</b></span>
        </div>
        <div class="dado-par">
          <div class="dado" id="dado-1">&mdash;</div>
          <span class="dado-op">+</span>
          <div class="dado" id="dado-2">&mdash;</div>
          <span class="cd-mod" id="dado-mod">+0</span>
          <!-- palco de fx ANCORADO nos dados (.dado-par): clarao/raio do critico e sangue da
               falha critica batem onde os dados pousam, nao no card largo. -->
          <div class="dado-fx" id="dado-fx" aria-hidden="true">
            <span class="fx-clarao"></span>
            <span class="fx-raio"></span>
            <span class="fx-fio"></span>
            <span class="fx-sangue"></span>
          </div>
        </div>
        <div class="cd-resultado">
          <div class="dado-conta" id="dado-conta"></div>
          <div class="dado-faixa" id="dado-faixa"></div>
        </div>
        <button class="dado-btn" id="dado-btn" type="button" aria-label="Rolar os dados" disabled>rolar 2d10</button>
      </div>

      <div class="pondera oculto" id="pondera">o Cronista pondera<span class="ret"><span>.</span><span>.</span><span>.</span></span></div>
    </div>

    <!-- FASE FRONT: botoes de acao do turno. Preenchido por window.setOpcoes(lista);
         clique copia o texto pro #cmd e foca (NAO auto-envia). Vazio -> .oculto. -->
    <div class="opcoes oculto" id="opcoes"></div>

    <div class="scrawl@@SCRAWL_OFF@@" id="scrawl">
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
    var lcL = document.getElementById('lc-leitura');
    if (lcL) { lcL.classList.toggle('on', on); lcL.setAttribute('aria-pressed', on ? 'true' : 'false'); }
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

  // CONFORTO DE LEITURA (cluster na area de leitura): A-/A+ reusa o sistema de fonte (txt-nivel),
  // o toggle reusa o modo foco. Mesmos localStorage -> fica sincronizado com a tela de config.
  function nivelCorrente() {
    for (var i = 0; i < NIVEIS.length; i++)
      if (document.body.classList.contains('txt-nivel-' + NIVEIS[i])) return i;
    return 1;
  }
  function passoFonte(d) {
    var i = Math.max(0, Math.min(NIVEIS.length - 1, nivelCorrente() + d));
    aplicaTexto(NIVEIS[i]);
    localStorage.setItem('jogar_txt_nivel', NIVEIS[i]);
  }
  var lcMenor = document.getElementById('lc-menor');
  var lcMaior = document.getElementById('lc-maior');
  var lcLeitura = document.getElementById('lc-leitura');
  if (lcMenor) lcMenor.addEventListener('click', function () { passoFonte(-1); });
  if (lcMaior) lcMaior.addEventListener('click', function () { passoFonte(1); });
  if (lcLeitura) lcLeitura.addEventListener('click', function () {
    var novo = !document.body.classList.contains('foco');
    aplicaFoco(novo);
    localStorage.setItem('jogar_foco', novo ? '1' : '0');
  });

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
  var rotEl = document.getElementById('dado-rotulo');
  var atribEl = document.getElementById('dado-atributo');
  var cdEl = document.getElementById('dado-cd');
  var modEl = document.getElementById('dado-mod');
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
  window.armarDado = function (rotulo, atributo, cd, mod) {
    if (resolveTimer) { clearTimeout(resolveTimer); resolveTimer = null; }
    if (rollTimer) { clearInterval(rollTimer); rollTimer = null; }
    limpa();
    // PASSO 2: o ARME ja mostra o que esta em jogo (campos que JA existem em teste_pendente).
    // Defaults seguros se vier sem args (gatilho 'd' do mock / armes sinteticos antigos).
    if (rotEl) rotEl.textContent = (rotulo != null && rotulo !== '') ? rotulo : 'o momento pede um lance';
    if (atribEl) atribEl.textContent = (atributo != null && atributo !== '') ? atributo : '\\u2014';
    if (cdEl) cdEl.textContent = (cd != null) ? cd : '\\u2014';
    if (modEl) modEl.textContent = (mod != null) ? (mod >= 0 ? '+' + mod : String(mod)) : '+0';
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

  // (removido) gatilho de debug da tecla 'd': armava o card de dado de verdade na mao do
  // jogador em prod -> rolagem nao solicitada (em combate, dano gravado). O arme legitimo
  // segue pelo Cronista (server -> window.armarDado(...)); em dev, via console.
})();
"""


# JS dos vitais (Vida + Mana + Ferida) — setters globais, padrao do dado.
# Ligados pela engine no Andar 2; hoje dormentes, testaveis via console.
_VITAIS_JS = """
window.setVida = function (v, vmax) {
  v = Math.max(0, Math.round(v));
  vmax = Math.max(1, Math.round(vmax));
  var pct = Math.max(0, Math.min(100, Math.round(v / vmax * 100)));
  var barra = document.querySelector('.vital.vida .bar > i');
  if (barra) barra.style.width = pct + '%';
  var n = document.getElementById('vida-num');
  if (n) n.textContent = '' + v;
  var mx = document.getElementById('vida-max');
  if (mx) mx.textContent = '' + vmax;
  var box = document.querySelector('.vital.vida');
  if (box) {
    var ac = box.classList.contains('dormente');   // estava DORMENTE -> vai acordar AGORA
    box.classList.toggle('baixa', pct <= 30);
    box.classList.remove('dormente');
    if (ac) { box.classList.add('despertou'); setTimeout(function(){ box.classList.remove('despertou'); }, 1200); }
  }
};
window.setMana = function (v, vmax) {
  v = Math.max(0, Math.round(v));
  vmax = Math.max(1, Math.round(vmax));
  var pct = Math.max(0, Math.min(100, Math.round(v / vmax * 100)));
  var barra = document.querySelector('.vital.mana .bar > i');
  if (barra) barra.style.width = pct + '%';
  var n = document.getElementById('mana-num');
  if (n) n.textContent = '' + v;
  var mx = document.getElementById('mana-max');
  if (mx) mx.textContent = '' + vmax;
  var box = document.querySelector('.vital.mana');
  if (box) {
    var ac = box.classList.contains('dormente');   // estava DORMENTE -> vai acordar AGORA
    box.classList.toggle('baixa', pct <= 25);
    box.classList.remove('dormente');
    if (ac) { box.classList.add('despertou'); setTimeout(function(){ box.classList.remove('despertou'); }, 1200); }
  }
};
window.setFerida = function (texto) {
  var box = document.getElementById('ferida');
  var txt = document.getElementById('ferida-txt');
  var t = (texto == null) ? '' : ('' + texto).trim();
  if (txt) txt.textContent = t;
  if (box) box.classList.toggle('oculto', t === '');
};
"""


# FASE FRONT — botoes de acao. Setter GLOBAL DE TOPO window.setOpcoes(lista): desenha
# 3-6 botoes no rodape do /jogar. Clique PREENCHE #cmd (editavel) e foca; NAO auto-envia
# (o jogador confirma com Enter/send). Lista vazia/ausente -> some.
# MOLDE do _VITAIS_JS (window.setVida no topo): o bundle static/jogar.js faz
# `window.Jogar = c` (clobber total) ao carregar, mas NUNCA toca os globais window.set*.
# Por isso NAO penduramos em window.Jogar - sem clobber, sem corrida, sem reinstalacao.
_OPCOES_JS = """
window.setOpcoes = function (lista) {
  var box = document.getElementById('opcoes');
  if (!box) return;
  box.classList.remove('travada');             // novo turno redesenha -> destrava os irmaos
  box.innerHTML = '';
  if (!lista || lista.length === 0) { box.classList.add('oculto'); return; }
  lista.forEach(function (texto, i) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'opcao';
    btn.textContent = texto;
    btn.setAttribute('data-idx', i + 1);        // 1-9 para o atalho de teclado
    btn.onclick = function () {
      // ENVIO INALTERADO: o clique so PRE-PREENCHE o #cmd e foca (jogador confirma com Enter).
      var cmd = document.getElementById('cmd');
      if (cmd) { cmd.value = texto; cmd.focus(); }
      // trava visual ADITIVA: marca a escolhida + desabilita os irmaos ate o proximo setOpcoes.
      btn.classList.add('escolhida');
      box.classList.add('travada');
    };
    box.appendChild(btn);
  });
  box.classList.remove('oculto');
};

// ATALHO 1-9: dispara a Nth opcao (= MESMO clique: pre-preenche o #cmd). Guarda de input
// (nao rouba digitacao, mesma do dado) + respeita a trava (box travada/oculta ou sem opcao
// naquele numero -> nada). Sem modificadores (Ctrl/Cmd/Alt+1 = atalho do browser, deixa passar).
(function () {
  if (window.__opcoesHotkeys) return;
  window.__opcoesHotkeys = true;
  document.addEventListener('keydown', function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key < '1' || e.key > '9') return;
    var t = (e.target && e.target.tagName) || '';
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(t)) return;   // nao rouba digitacao
    var box = document.getElementById('opcoes');
    if (!box || box.classList.contains('oculto') || box.classList.contains('travada')) return;
    var btn = box.querySelector('.opcao[data-idx="' + e.key + '"]');
    if (btn) { e.preventDefault(); btn.click(); }
  });
})();
"""


class EstadoTurno:
    """Fatia 1: estado mutavel que o motor de turno narrado le e atualiza."""
    __slots__ = ("historico", "pressao_atual", "sessao_atual", "modelo_atual", "resultado_pendente", "is_infancia")

    def __init__(self, historico, pressao_atual, sessao_atual, modelo_atual, resultado_pendente, is_infancia=False):
        self.historico = historico
        self.pressao_atual = pressao_atual
        self.sessao_atual = sessao_atual
        self.modelo_atual = modelo_atual
        self.resultado_pendente = resultado_pendente
        # Campanha do protagonista (Gabriel Varekhor, id 8): liga o bloco da campanha no prompt.
        # Default False -> turno generico (Doran/harness) intacto.
        self.is_infancia = is_infancia


class ResultadoTurno:
    """Fatia 1: saida do motor de turno narrado."""
    __slots__ = ("prosa", "pressao", "atmosfera", "teste", "resposta", "vestindo", "abortado", "opcoes")

    def __init__(self, prosa, pressao, atmosfera, teste, resposta, vestindo, abortado, opcoes=None):
        self.prosa = prosa
        self.pressao = pressao
        self.atmosfera = atmosfera
        self.teste = teste
        self.resposta = resposta
        self.vestindo = vestindo
        self.abortado = abortado
        self.opcoes = opcoes   # FASE FRONT: botoes de acao (list[str]|None); o narrar os empurra pra UI


class EstadoCombate:
    """Fatia N: estado mutavel do combate, COMPARTILHADO entre o parse (no narrar) e o
    resolver_dado (na rolagem). Sao as 10 cells que eram nonlocals de _pagina_jogar; o
    handler ao_rolar_dado empacota-as aqui, chama resolver_dado, e desempacota de volta."""
    __slots__ = ("teste_pendente", "resultado_pendente", "tensao_atual", "inimigo",
                 "inimigos", "acao_atual", "via_atual", "feridas_ativas",
                 "feridas_ja_usadas", "_infeccao_pendente")

    def __init__(self, teste_pendente, resultado_pendente, tensao_atual, inimigo,
                 inimigos, acao_atual, via_atual, feridas_ativas, feridas_ja_usadas,
                 _infeccao_pendente):
        self.teste_pendente = teste_pendente
        self.resultado_pendente = resultado_pendente
        self.tensao_atual = tensao_atual
        self.inimigo = inimigo
        self.inimigos = inimigos
        self.acao_atual = acao_atual
        self.via_atual = via_atual
        self.feridas_ativas = feridas_ativas
        self.feridas_ja_usadas = feridas_ja_usadas
        self._infeccao_pendente = _infeccao_pendente


class _UITurno:
    """Callbacks de tela do turno narrado. Default = no-op (harness/headless);
    o closure /jogar injeta os _arrive/_pondera/_stream_* reais por atributo."""

    def arrive(self, *a, **k):
        pass

    def pondera(self, *a, **k):
        pass

    def stream_iniciar(self, *a, **k):
        pass

    def stream_update(self, *a, **k):
        pass

    def stream_finalizar(self, *a, **k):
        pass

    def stream_abortar(self, *a, **k):
        pass


_UI_TURNO_NOOP = _UITurno()


def _cauda_de_voz(historico, n=4):
    """Fatia A2.1: bloco anti-repeticao de abertura. Le as ultimas n RESPOSTAS do
    Cronista (role assistant) do historico, extrai a abertura limpa de cada (prosa
    sem <estado>, via _separar_estado; primeiras 8 palavras) e monta um lembrete
    CURTO e POSITIVO (substituicao positiva, nao proibicao pura). Inicio de sessao
    (0 respostas) -> so o lembrete de voz, sem lista. Funcao pura; o bloco vai so na
    copia msgs[-1], NUNCA no historico guardado."""
    aberturas = []
    for m in historico:
        if m.get("role") != "assistant":
            continue
        prosa = _separar_estado(m["content"], 0)[0]
        ab = " ".join(prosa.split()[:8])
        if ab:
            aberturas.append(ab)
    aberturas = aberturas[-n:]
    voz = "Voz: terceira pessoa, passado, prosa contida."
    positiva = ("Varie a entrada — abra por som, gesto consumado, sensação no corpo "
                "ou mudança de luz.")
    contencao = ("A contenção governa: o peso da cena decide a extensão, não um molde. "
                 "Violência de rotina é factual e breve. As palavras mais duras usam o menor número delas.")
    if not aberturas:
        return f"<cauda_de_voz>\n{voz} {positiva}\n{contencao}\n</cauda_de_voz>"
    lista = "\n".join(f'- "{a}"' for a in aberturas)
    return (f"<cauda_de_voz>\n{voz} Não reabra como as últimas respostas:\n"
            f"{lista}\n{positiva}\n{contencao}\n</cauda_de_voz>")


async def executar_turno_narrado(estado, msg_usuario, mostrar_acao=True, *,
                                 ui=_UI_TURNO_NOOP, inimigos=(), deve_abortar=lambda: False,
                                 cauda_voz=False, em_combate=False):
    """Fatia 1: motor de turno NARRADO, extraido de narrar 3097-3213 linha a linha.

    cauda_voz (Fatia A2.1): quando True, injeta um bloco <cauda_de_voz> entre o
    <contexto> e a fala (anti-repeticao de abertura). Default False = byte-identico
    ao comportamento anterior. A logica da cauda entra no Gate 2.

    Faz: append user -> _arrive -> grava jogador -> carregar contexto -> montagem (com
    _resumo_bando) -> _pondera -> stream Opus/mock -> append assistant -> abort-check ->
    _separar_estado. NAO toca combate, NAO grava narrador/pressao (o caller faz, pra
    preservar a ordem vs combate e a trava `ocupado`). MUTA `estado` (historico,
    pressao_atual, resultado_pendente) e devolve ResultadoTurno. Os helpers *_safe e
    _separar_estado/_cronista_mock sao globais de modulo (monkeypatchaveis pelo harness)."""
    estado.historico.append({"role": "user", "content": msg_usuario})

    if mostrar_acao:
        ui.arrive(msg_usuario, eco=True)

    if mostrar_acao:
        await _gravar_turno_safe(estado.sessao_atual, "jogador", msg_usuario)

    query_text = msg_usuario if mostrar_acao else None
    ctx_md = await _carregar_contexto_safe(estado.sessao_atual, query_text)

    msgs = [m.copy() for m in estado.historico]
    fala = msgs[-1]["content"]
    _estado = await _montar_estado_safe(estado.sessao_atual, estado.pressao_atual, estado.resultado_pendente)
    _roster = _resumo_bando(inimigos)
    if _roster:
        _estado = _estado + "\n" + _roster
    partes = [_estado]
    _vestindo = estado.resultado_pendente is not None
    estado.resultado_pendente = None
    if ctx_md:
        partes.append(f"<contexto>\n{ctx_md}\n</contexto>")
    if cauda_voz:
        partes.append(_cauda_de_voz(estado.historico))
    # Campanha do protagonista: SO na infancia, injeta o bloco (Modo Infancia + canon) como
    # tag propria, ANTES da fala. Fora da infancia (Doran/harness) nada muda. O texto vem do
    # arquivo do Gabriel via modulo cacheado; aqui so o envelopamos.
    if getattr(estado, "is_infancia", False):
        partes.append(f"<campanha_protagonista>\n{bloco_campanha_infancia()}\n</campanha_protagonista>")
    partes.append(fala)
    msgs[-1]["content"] = "\n\n".join(partes)

    print("[memoria] === prompt do Cronista (ultima mensagem) ===")
    print(msgs[-1]["content"])
    print("[memoria] === fim (contexto " + ("PRESENTE" if ctx_md else "vazio") + ") ===")

    ui.pondera(True)
    _abortado = ResultadoTurno(None, estado.pressao_atual, None, None, "", _vestindo, True)
    # ADR-008 peca 3 (3a): em combate, NAO pinga incremental — buffera e a finalizacao
    # (no caller: _stream_update(prosa)+_stream_finalizar) revela tudo de uma vez. Abre
    # espaco pro validador (3b) corrigir antes de exibir. Fora de combate: streaming normal.
    _buffer = em_combate

    # ADR-008 3b: a GERACAO (mock/Opus) extraida pra rodar 1x + ate 1 retry com correcao.
    # Recebe _msgs (permite injetar a correcao na 2a chamada). Fecha sobre ui/deve_abortar/
    # _buffer/estado. Devolve (resposta, abortado): abort vira ("", True) e o pai converte.
    async def _gerar(_msgs) -> "tuple[str, bool]":
        ui.stream_iniciar()
        resposta = ""
        if MODO_MOCK:
            completa = _cronista_mock(_msgs)
            passo = 18
            for i in range(0, len(completa), passo):
                if deve_abortar():
                    ui.stream_abortar()
                    return ("", True)
                resposta = completa[: i + passo]
                if not _buffer:
                    ui.stream_update(parte_visivel(resposta))
                await asyncio.sleep(0.035)
            resposta = completa
        else:
            ultimo = 0.0
            async with _get_aclient().messages.stream(
                model=estado.modelo_atual,
                max_tokens=1400,
                system=[
                    {
                        "type": "text",
                        "text": CRONISTA_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=_msgs,
            ) as stream:
                async for delta in stream.text_stream:
                    if deve_abortar():
                        ui.stream_abortar()
                        return ("", True)
                    resposta += delta
                    agora = time.monotonic()
                    if agora - ultimo >= 0.06:
                        ultimo = agora
                        if not _buffer:
                            ui.stream_update(parte_visivel(resposta))
                final = await stream.get_final_message()
                resposta = "".join(
                    b.text for b in final.content
                    if getattr(b, "type", None) == "text"
                )
        if deve_abortar():
            ui.stream_abortar()
            return ("", True)
        return (resposta, False)

    resposta, _ab = await _gerar(msgs)
    if _ab:
        return _abortado
    if _buffer:
        _v = await _validar_narracao(resposta)
        if _v is not None:
            resposta, _ab = await _gerar(msgs + [{"role": "user", "content": _CORRECAO_NARRACAO[_v]}])
            if _ab:
                return _abortado
            # 1 retry SO — usa esta resposta mesmo se ainda violar. NAO re-validar.
    print("[memoria] === resposta do Cronista (Opus) ===")
    print(resposta)
    print("[memoria] === fim da resposta ===")
    estado.historico.append({"role": "assistant", "content": resposta})
    prosa, nova_pressao, atmosfera, teste, _opcoes = _separar_estado(resposta, estado.pressao_atual)
    estado.pressao_atual = nova_pressao
    # _opcoes (botoes de acao) ja vem parseado; a FASE FRONT o encaminha pro ResultadoTurno
    # e o `narrar` o empurra pra UI (window.setOpcoes) ao fim do turno.
    return ResultadoTurno(prosa, nova_pressao, atmosfera, teste, resposta, _vestindo, False, opcoes=_opcoes)


def _armar_dado_js(tp: dict | None = None) -> str:
    """PASSO 2: monta window.armarDado(rotulo, atributo, cd, mod) com os campos que JA existem
    em teste_pendente (intencao/atributo/cd/mod). So APRESENTACAO — nao decide nada da rolagem.
    Sem tp -> arme nu (defaults no cliente). cd/mod viram numero (null se faltar; cliente trata)."""
    if not tp:
        return "window.armarDado && window.armarDado()"
    return (
        "window.armarDado && window.armarDado("
        f"{json.dumps(tp.get('intencao') or '', ensure_ascii=False)},"
        f"{json.dumps(tp.get('atributo') or '', ensure_ascii=False)},"
        f"{json.dumps(tp.get('cd'))},"
        f"{json.dumps(tp.get('mod'))})"
    )


async def resolver_dado(estado, *, modo="normal", sessao_id, com_ficha, js,
                        ler_fadiga, aplicar_dano_combate, drenar_vigor,
                        gastar_mp, ajustar_fadiga):
    """Fatia N: motor da ROLAGEM, extraido byte-identico de ao_rolar_dado. Le/MUTA o
    EstadoCombate `estado` (as 10 cells, in-place). Dependencias INJETADAS: `js` (emit
    de UI, no-op no harness/real na tela), os 5 helpers de DB do combate (ler_fadiga,
    aplicar_dano_combate, drenar_vigor, gastar_mp, ajustar_fadiga), alem de `sessao_id`
    e `com_ficha`. classificar_faixa/_atualizar_momentum/TIER_DANO/_FAIXA_CRONISTA sao
    de modulo -> uso direto. NAO grava narrador/pressao (isso e a espinha, fica no caller)."""
    MOD_MOCK = 2   # MOCK: modificador (fallback da tecla "d")
    DC_MOCK = 12   # MOCK: dificuldade (fallback da tecla "d")
    if estado.teste_pendente:
        mod = estado.teste_pendente["mod"]
        cd = estado.teste_pendente["cd"]
        intencao = estado.teste_pendente["intencao"]
    else:
        mod = MOD_MOCK
        cd = DC_MOCK
        intencao = None
    # Fatia 9b: Fadiga penaliza o 2d10 em limiares, SO em combate (/jogar-c). >=50% -> -1;
    # >=80% -> -2. Entra no `mod` ANTES de classificar_faixa -> muda a FAIXA real E o numero
    # exibido (coerencia: penalizou, o jogador ve o resultado penalizado). Leitura unica/rolagem.
    if estado.tensao_atual is not None and com_ficha:
        _fa, _fm = await ler_fadiga(sessao_id)
        if _fm > 0:
            _ratio = _fa / _fm
            _pen_fadiga = -2 if _ratio >= 0.80 else (-1 if _ratio >= 0.50 else 0)
            mod = mod + _pen_fadiga
    # rng EXPLICITO (random do namespace de jogo): preserva mocks e a byte-neutralidade
    # do Normal (2 chamadas, mesma ordem). modo default "normal" -> ao_rolar_dado intocado.
    d1, d2 = rolar_resolucao(modo, rng=random.randint)
    faixa = classificar_faixa(d1, d2, mod, cd)
    rotulos = {
        "sucesso_critico": "Kokusen · sucesso crítico",
        "sucesso": "Sucesso",
        "sucesso_parcial": "Sucesso — com um preço",
        "falha": "Falha",
        "falha_critica": "Falha crítica",
    }
    rotulo = rotulos[faixa]
    # devolve a faixa pro Cronista no proximo [ESTADO] e consome o pendente.
    if intencao is not None:
        estado.resultado_pendente = f"{intencao} — {_FAIXA_CRONISTA[faixa]}"
        estado.teste_pendente = None
    js(
        "window.__resolverDado && window.__resolverDado("
        f"{d1},{d2},{mod},{cd},"
        f"{json.dumps(faixa)},{json.dumps(rotulo, ensure_ascii=False)})"
    )
    # Combate Fatia 2: em combate (tensao ativa) E so no /jogar-c, a FAIXA aplica dano
    # num vital e ESCREVE no banco; _empurrar_vitais (dentro do helper) faz a barra mexer.
    # Fora de combate, nenhuma faixa custa vital. tensao_atual/sessao_id: leitura.
    if estado.tensao_atual is not None and com_ficha:   # Debito alinhado: com_ficha (rota), nao FICHA_C
        # Combate Fatia 4: defesa corta o dano em voce pela METADE (fator 0.5) e NAO fere
        # o inimigo; ataque (default) = fator 1.0, Fatias 2/3 exatamente como antes.
        _defesa = (estado.acao_atual == "defesa")
        _estancando = (estado.acao_atual == "estancar")   # Fatia 8a: estancar fica FORA da troca (sem faixa-dano, sem ferir)
        _fugindo = (estado.acao_atual == "fugir")
        # Fatia 5: o tier do inimigo escala o dano em VOCÊ (comum 1.0 / bravo 1.5 / elite 2.0);
        # inimigo None (perigo ambiental) -> 1.0. Compoe multiplicativo com a defesa (Fatia 4).
        _mult_tier = TIER_DANO.get(estado.inimigo["tier"], 1.0) if estado.inimigo is not None else 1.0
        # Fatia 10b: postura agressiva de QUALQUER inimigo vivo (nao so o alvo) tira o desconto da
        # defesa (0.5 -> 1.0). Binario: um agressivo basta — a QUANTIDADE e a pressao (abaixo), nao
        # aqui (sem double-dip). n=1: 'algum agressivo' == 'alvo agressivo' -> byte-identico ao 6a.
        _algum_agressivo = any(e.get("postura") == "agressiva" for e in estado.inimigos)
        _fator_defesa = 1.0 if (_defesa and _algum_agressivo) else (0.5 if _defesa else 1.0)
        # Fatia 8a: ferida INFECTADA dobra (x1.5) o dano do CRITICO em voce (so falha_critica).
        _mult_infec = 1.5 if (faixa == "falha_critica" and any(f.get("infectada") for f in estado.feridas_ativas)) else 1.0
        # Fatia 10a: PRESSAO do bando -> mais inimigos VIVOS batem mais forte em voce.
        # 1 (ou 0, ambiental) -> x1.0 (n=1 byte-identico); 2 -> x1.3; 3+ -> x1.6 (teto).
        # Entra na cadeia EXISTENTE (tier x defesa x infeccao), empilha SEM teto total.
        _n_vivos = len(estado.inimigos)
        _fator_pressao = 1.0 if _n_vivos <= 1 else (1.3 if _n_vivos == 2 else 1.6)
        if not _estancando and not _fugindo:
            await aplicar_dano_combate(sessao_id, faixa, fator=_mult_tier * _fator_defesa * _mult_infec * _fator_pressao)
        # Fatia 9a: CUSTO de agir. So ataque ofensivo paga aqui; defesa/estancar/curar NAO
        # (estancar paga Fadiga na 9b; curar ja gastou 10 MP no narrar). fisico->-1 Vigor,
        # magico->-4 MP, combo->ambos. Sem MP bastante: gastar_mp degrada (False), o golpe
        # ja saiu e o turno nao trava (Vigor do combo ainda sai). Aplicado DEPOIS da faixa-dano.
        if estado.acao_atual == "ataque":
            if estado.via_atual in ("fisico", "combo"):
                await drenar_vigor(sessao_id, 1)
            if estado.via_atual in ("magico", "combo"):
                await gastar_mp(sessao_id, 4)
        # Combate Fatia 3: o OUTRO lado da troca. Mesma faixa, mesmo roll, mesmo gate.
        # Desfecho bom fere o inimigo (memoria, sem escrita no banco); a condicao volta
        # qualitativa pro Cronista no resultado_pendente. Defesa/estancar NAO ferem o inimigo.
        if estado.inimigo is not None and not _defesa and not _estancando and not _fugindo:
            _dano_inim = {"sucesso_critico": 6, "sucesso": 4, "sucesso_parcial": 2}.get(faixa, 0)  # trava 2: chaves literais
            # Fatia 1 itens (2o corte): bonus_dano da arma equipada, AMORTECIDO (min(3, bruto//2)),
            # somado ANTES do _fator_inimigo. Gate em _aplicar_bonus_dano: so soma se _dano_inim>0
            # (faixa que ja fere) -> item nao ressuscita dano de falha nem vira acerto.
            _dano_inim = _aplicar_bonus_dano(_dano_inim, await bonus_dano_equipado(sessao_id))
            # Fatia 6b: postura defensiva -> seus golpes passam pela METADE (ele aguenta,
            # fecha a guarda). Ataque ainda fere (so reduz, nao bloqueia). round(), clamp piso 0.
            # Fatia 9a: COMBO (lamina+magia) fura a guarda -> ignora o corte x0.5 da defensiva.
            _fator_inimigo = 1.0 if estado.via_atual == "combo" else (0.5 if estado.inimigo.get("postura") == "defensiva" else 1.0)
            _dano_inim = round(_dano_inim * _fator_inimigo)
            if _dano_inim:
                estado.inimigo["hp"] = max(0, estado.inimigo["hp"] - _dano_inim)   # clamp piso 0
            _nome_inim = estado.inimigo["nome"]
            _tag = None
            if estado.inimigo["hp"] <= 0:                 # trava 3: caiu ANTES de ferido
                _tag = f"[{_nome_inim} caiu]"
                # Fatia 10a: morte SAI do bando + RE-MIRA no proximo vivo (ou None = bando vazio
                # -> vitoria pelo caminho de hoje). Substitui o 'inimigo = None' do caso unico.
                estado.inimigos.remove(estado.inimigo)
                estado.inimigo = estado.inimigos[0] if estado.inimigos else None
            # Fatia 10a: a tag por-alvo 'ferido' SAI de cena -> o RESUMO do bando (injetado no
            # [ESTADO] a cada turno) cobre a condicao de TODOS. So a MORTE continua virando tag.
            if _tag:
                # trava 1: a tag (sinal de vitoria) e SEMPRE anexada, FORA do guard de
                # intencao -> mesmo num roll sem teste, "caiu" chega ao Cronista e a luta fecha.
                estado.resultado_pendente = ((estado.resultado_pendente or "") + " " + _tag).strip()
        if _fugindo:
            # FUGA resolve em 5 faixas: sucesso (qualquer) = sai da luta; parcial = sai
            # MAS leva o corte (escapa sangrando); falha = preso + dano. Reusa o dano-em-voce
            # so nas faixas com custo. Sair e o UNICO clear legitimo com inimigo vivo.
            _escapou = faixa in ("sucesso_critico", "sucesso", "sucesso_parcial")
            if faixa in ("sucesso_parcial", "falha", "falha_critica"):
                await aplicar_dano_combate(sessao_id, faixa, fator=_mult_tier * _fator_pressao)
            if _escapou:
                estado.inimigo = None
                estado.inimigos = []
                estado.tensao_atual = None
        # Fatia 8a: NASCIMENTO de ferida. So no CRITICO (pior faixa) E com inimigo presente E fora
        # do estancar. Sinaliza ao Cronista que nomeie UMA ferida nova e injeta as ja-usadas pra ele
        # inventar nome inedito. A criacao real acontece no PROXIMO turno (narrar parseia 'ferida: <nome>').
        if faixa == "falha_critica" and estado.inimigo is not None and not _estancando:
            _ja = ", ".join(estado.feridas_ja_usadas) if estado.feridas_ja_usadas else "nenhuma"
            _sinal = f"[falha_critica: nomeie UMA ferida nova — invente um nome inedito, fora desta lista: {_ja}]"
            estado.resultado_pendente = ((estado.resultado_pendente or "") + " " + _sinal).strip()
        # Fatia 9b: falha critica cansa +1 (alem de abrir ferida na 8a). Atrela a inimigo
        # presente, igual a 8a atrela o nascimento da ferida (golpe limpo que tambem fatiga).
        if faixa == "falha_critica" and estado.inimigo is not None:
            await ajustar_fadiga(sessao_id, +1)
        # Combate Fatia 7: momentum visual (SO /jogar-c). Le vigor do banco + inimigo (memoria);
        # injeta a vignette + placeholder + flash. Sem inimigo (caiu/ambiental) -> limpa.
        if com_ficha:
            try:
                from db import get_session
                from sqlalchemy import text as _sa_text
                async with get_session() as _sm:
                    _rv = (await _sm.execute(_sa_text(
                        "SELECT p.vigor_atual, p.vigor_maximo FROM sessoes s "
                        "JOIN personagens p ON p.id = s.personagem_id WHERE s.id = :sid"
                    ), {"sid": sessao_id})).mappings().first()
            except Exception as _e:  # noqa: BLE001 - degrada sem quebrar, nao trava o roll
                _rv = None
                print(f"[momentum] erro: {type(_e).__name__}: {_e}")
            _mom = _atualizar_momentum(_rv["vigor_atual"], _rv["vigor_maximo"], estado.inimigo) if _rv else None
            if _mom:
                _ph = {"recuando": "recue ou arrisque tudo...", "pressionando": "ele está cedendo...",
                       "equilibrado": "aja, ou observe..."}[_mom["estado"]]
                _flash = ("var f=document.getElementById('flash-limiar');if(f){f.style.animation='none';"
                          "void f.offsetWidth;f.style.animation='flash-escuro 0.8s ease-out forwards';}") if _mom["limiar"] else \
                         "var f=document.getElementById('flash-limiar');if(f)f.style.animation='none';"
                js("(function(){var v=document.getElementById('vignette-momentum');"
                    f"if(v)v.className={json.dumps(_mom['estado'])};"
                    "var c=document.getElementById('cmd');if(c){"
                    f"c.className=(c.className.replace(/recuando|pressionando|equilibrado/g,'').trim()+' '+{json.dumps(_mom['estado'])}).trim();"
                    f"c.placeholder={json.dumps(_ph)};}}" + _flash + "})();")
            else:
                js("(function(){var v=document.getElementById('vignette-momentum');if(v)v.className='';"
                    "var f=document.getElementById('flash-limiar');if(f)f.style.animation='none';"
                    "var c=document.getElementById('cmd');if(c){c.classList.remove('recuando','pressionando','equilibrado');"
                    "c.placeholder='aja, ou observe...';}})();")


async def processar_combate(estado, *, resposta, teste, vestindo, com_ficha, sessao_id,
                            js, gravar_infeccao, ajustar_fadiga, gastar_mp_cura,
                            drenar_vigor, resolver_mod_atributo, registrar_divida,
                            is_infancia=False):
    """Fatia N: o PARSE de combate, extraido byte-identico do `narrar`. Le o <estado>
    DITADO na `resposta` e MUTA o EstadoCombate `estado` in-place (9 das 10 cells —
    NAO escreve resultado_pendente, quem o faz e resolver_dado). Compartilha a MESMA
    classe EstadoCombate da rolagem. Dependencias INJETADAS: `js` (emit UI) + os helpers
    de DB (gravar_infeccao, ajustar_fadiga, gastar_mp_cura, drenar_vigor,
    resolver_mod_atributo). Seams de ENTRADA da espinha: `teste` e `vestindo` (consumidos
    no arme). _RE_*/TIER_HP/CD_TIER de modulo -> uso direto. NAO grava narrador/pressao,
    NAO toca a trava ocupado nem o try/finally (isso fica no closure narrar)."""
    # Combate Fatia 1: flag 'combate: 1' no <estado> (escopado ao bloco, NAO na
    # prosa) conta a Tensao em memoria. Presente -> sobe (cap 10); ausente -> None
    # (a barra some). pressao_emocional segue parseada acima, mas vestigial na barra.
    _m_est = _RE_ESTADO.search(resposta) or _RE_ESTADO_ABERTO.search(resposta)  # Fatia truncagem: tolera <estado> sem fechamento
    _combate_on = bool(_RE_COMBATE.search(_m_est.group(1))) if _m_est else False
    # Fatia 2 - RECUO: o Cronista pode tirar inimigos VIVOS da luta (eles recuam/somem).
    # Mesma logica da morte: o nomeado sai do bando. Re-mira se era o alvo atual.
    _recuo = False
    if _m_est:
        _mr = _RE_RECUO.search(_m_est.group(1))
        if _mr:
            _recuo = True
            _saem = [n.strip().lower() for n in _mr.group(1).split(",")]
            estado.inimigos = [e for e in estado.inimigos if e["nome"].lower() not in _saem]
            if estado.inimigo is not None and estado.inimigo["nome"].lower() in _saem:
                estado.inimigo = estado.inimigos[0] if estado.inimigos else None
    # Fatia 2 - TRAVA: a prosa NAO encerra a luta enquanto houver inimigo ATIVO vivo.
    # So o dado (morte), a fuga do jogador (Fatia 1) ou o recuo (acima) terminam a briga.
    # Largou combate:1 com inimigo de pe e sem recuo -> ignoramos o fim mentiroso; a luta
    # segue (o sistema e dono do fim, nao a narracao). Override ANTES da Tensao (abaixo).
    if (not _combate_on and not _recuo
            and any(e.get("hp", 0) > 0 and e.get("estado", "ativo") == "ativo" for e in estado.inimigos)):
        _combate_on = True
    # Modo Infancia: combate DORMENTE por codigo. Override DURO apos toda a logica (flag do
    # Cronista E trava de inimigo-vivo) -> na infancia nunca instaura combate, aconteca o que
    # acontecer no <estado>. O teste 2d10 fora de combate (elif teste:, abaixo) NAO e gateado.
    if is_infancia:
        _combate_on = False
    _tensao_antes = estado.tensao_atual   # Fatia 8a: None->set detecta inicio de combate (semeia infeccao)
    estado.tensao_atual = min((estado.tensao_atual or 0) + 1, 10) if _combate_on else None
    # Combate Fatia 3: o inimigo vive junto da Tensao. Fim de luta (sem flag) limpa os
    # dois. Em combate, se o Cronista declarou um inimigo e nao ha um ativo -> SPAWN
    # (tier->hp). Guard: spawna so se None (re-declarar NAO reseta o HP de um ativo).
    if not _combate_on:
        estado.inimigo = None
        estado.inimigos = []           # Fatia 10a: fim de combate limpa o bando junto do alvo
        estado.acao_atual = "ataque"   # Fatia 4: fora de combate volta ao default
        # Opcao A: fora de combate ainda LE a via ditada (magia conjurada sem oponente) ->
        # deixa o narrar cobrar Mana. Sem via: ditado, volta ao default fisico (Fatia 9a).
        _mv_fora = _RE_VIA.search(_m_est.group(1)) if _m_est else None
        estado.via_atual = _mv_fora.group(1).lower() if _mv_fora else "fisico"
        if com_ficha:           # Fatia 7: combate acabou -> limpa a vignette de momentum
            js("(function(){var v=document.getElementById('vignette-momentum');if(v)v.className='';"
                "var c=document.getElementById('cmd');if(c){c.classList.remove('recuando','pressionando','equilibrado');"
                "c.placeholder='aja, ou observe...';}})();")
    else:
        # Fatia 10a: SPAWN do bando. findall pega TODAS as declaracoes 'inimigo: nome | tier'
        # do turno (reforco entra mid-combate). Dedup por NOME: re-mencao de um existente NAO
        # duplica nem reseta o HP (substitui o guard 'inimigo is None' do caso unico).
        for _nome_e, _tier_e in (_RE_INIMIGO.findall(_m_est.group(1)) if _m_est else []):
            _nome_e = _nome_e.strip()
            _tier_e = _tier_e.lower()   # trava 4: tier.lower()
            if _nome_e and _nome_e.lower() not in [e["nome"].lower() for e in estado.inimigos]:
                _hpmax = TIER_HP.get(_tier_e, 6)
                estado.inimigos.append({"nome": _nome_e, "hp": _hpmax, "hp_max": _hpmax, "tier": _tier_e, "postura": "neutra", "estado": "ativo"})
        # alvo atual: se nao ha (None) e o bando tem alguem, mira no primeiro vivo.
        if estado.inimigo is None and estado.inimigos:
            estado.inimigo = estado.inimigos[0]
        # Fatia 10a: MIRA explicita -> troca de alvo. GRUDENTA: sem a tag (ou alvo nao
        # encontrado por typo/morte), MANTEM o alvo atual.
        _mal = _RE_ALVO.search(_m_est.group(1)) if _m_est else None
        if _mal:
            _nome_alvo = _mal.group(1).strip().lower()
            _achado = next((e for e in estado.inimigos if e["nome"].lower() == _nome_alvo), None)
            if _achado is not None:
                estado.inimigo = _achado
        # Fatia 4: ataque|defesa do <estado>; default ataque se a flag nao vier.
        _ma = _RE_ACAO.search(_m_est.group(1)) if _m_est else None
        estado.acao_atual = _ma.group(1).lower() if _ma else "ataque"
        # Fatia 9a: via do custo (eixo separado); reset-por-turno -> fisico sem a tag.
        _mv = _RE_VIA.search(_m_est.group(1)) if _m_est else None
        estado.via_atual = _mv.group(1).lower() if _mv else "fisico"
        # Fatia 10b: postura POR inimigo + PERSISTENTE. Aceita 'postura: VALOR' (alvo atual,
        # retrocompat 6a) e 'postura: NOME | VALOR' (inimigo nomeado). findall pega varias linhas.
        # PERSISTE: so atualiza quem foi citado; nao-citado MANTEM a postura (conserta o reset
        # silencioso da 6a). Reset agora e EXPLICITO: o Cronista emite 'neutra'. Nome inexistente
        # (typo) = no-op silencioso, nunca cria inimigo.
        for _nome_p, _val_p in (_RE_POSTURA.findall(_m_est.group(1)) if _m_est else []):
            _val_p = _val_p.lower()
            _nome_p = _nome_p.strip()
            if _nome_p:
                _alvo_p = next((e for e in estado.inimigos if e["nome"].lower() == _nome_p.lower()), None)
            else:
                _alvo_p = estado.inimigo
            if _alvo_p is not None:
                _alvo_p["postura"] = _val_p
    # === Corrupcao Fatia 1: SITE UNICO (cobra no CAST, pros dois modos) ===
    # Conjurar magia escura SOMA divida via RPC registrar_divida. _m_est ja resolvido la em
    # cima; o if/else de combate convergiu aqui -> UMA cobranca por turno (sem double entre os
    # branches). Cobrada no parse (cast), independe do roll -> NAO toca resolver_dado. So
    # /jogar-c (com_ficha). Sem tag -> no-op (byte-neutro). delta = peso x 5; sabor invalido
    # -> generic. Fatia 2: no cap 100 registrar_divida bifurca o Julgamento e DEVOLVE o texto
    # do desfecho -> escrevemos em estado.resultado_pendente (canal existente, desempacotado
    # pelo narrar -> narrado na abertura do proximo turno). Sem cap -> devolve None (no-op).
    if com_ficha and _m_est:
        _mc = _RE_CORRUPCAO.search(_m_est.group(1))
        if _mc:
            _peso = int(_mc.group(1))
            _sabor = _mc.group(2).lower()
            if _sabor not in _SABORES_CORRUPCAO:
                print(f"[corrupcao] sabor desconhecido '{_sabor}' -> generic")
                _sabor = "generic"
            _desfecho_div = await registrar_divida(sessao_id, _peso, _sabor,
                                                   f"conjuração {_sabor} (peso {_peso})")
            if _desfecho_div:
                estado.resultado_pendente = _desfecho_div
    # === Combate Fatia 8a: feridas (memoria; SO /jogar-c) ===
    if com_ficha:
        if not _combate_on:
            # FIM do combate (SO na TRANSICAO combate->fora): feridas abertas viram infeccao
            # pendente (carrega p/ o proximo); feridas fechadas sao descartadas; depois zera as
            # ativas. Este bloco roda em TODO turno fora de combate -> o guard _tensao_antes is
            # not None garante a TRANSICAO: sem ele, um turno narrativo em paz re-derivaria a
            # infeccao de feridas_ativas ja vazias (apagando a pendente) e re-gravaria [] no banco.
            if _tensao_antes is not None:
                estado._infeccao_pendente = [{"nome": f["nome"], "severidade": 1} for f in estado.feridas_ativas]
                estado.feridas_ativas = []
                # Fatia 8b: persiste a infeccao da transicao (ferida aberta -> [{...}]; combate
                # limpo -> []). Sobrevive a restart.
                await gravar_infeccao(sessao_id, estado._infeccao_pendente)
                # Fatia 9b: fim de combate recupera folego -> -3 Fadiga (clamp piso 0 no helper).
                await ajustar_fadiga(sessao_id, -3)
        else:
            # INICIO do combate (None->set): semeia infeccao pendente como feridas infectadas.
            if _tensao_antes is None and estado._infeccao_pendente:
                estado.feridas_ativas = [{"nome": p["nome"], "sangrando": True, "turnos_estancada": 0, "infectada": True}
                                         for p in estado._infeccao_pendente]
                estado._infeccao_pendente = []
                # NOTA (dessincronia BENIGNA, por design): NAO gravamos o banco aqui de proposito.
                # A cell _infeccao_pendente esvazia (a infeccao virou ferida ATIVA in-memory), mas
                # personagens.ferida_infeccao_pendente fica [X] -> e o SEED DURAVEL de recuperacao.
                # feridas_ativas e viva/efemera e NAO persiste; se o processo reiniciar no meio deste
                # combate, o load relê [X] do banco e re-semeia a infeccao (ela sobrevive). Gravar []
                # aqui PERDERIA a infeccao no restart. O banco se auto-corrige no fim do combate
                # (gravar_infeccao a partir do feridas_ativas de entao). O golden test_golden_seed_infeccao
                # (p5: db sem escrita de infeccao) fotografa isto e esta CORRETO.
            # NASCIMENTO: o Cronista nomeou uma ferida (resposta ao sinal de falha_critica).
            _mfer = _RE_FERIDA.search(_m_est.group(1)) if _m_est else None
            if _mfer:
                _nome_f = _mfer.group(1).strip()
                if _nome_f and _nome_f.lower() not in [n.lower() for n in estado.feridas_ja_usadas]:
                    estado.feridas_ativas.append({"nome": _nome_f, "sangrando": True, "turnos_estancada": 0, "infectada": False})
                    estado.feridas_ja_usadas.append(_nome_f)
            # ESTANCAR: pausa TODAS as feridas abertas por 2 turnos (nao fecha).
            if estado.acao_atual == "estancar":
                for _f in estado.feridas_ativas:
                    _f["turnos_estancada"] = 2
                # Fatia 9b: estancar cansa +2 -> este e o FREIO do estancar-stall (Visao A nao
                # tem turno de inimigo; sem custo, estancar seria imune pra sempre). Cobra UMA
                # vez por turno, e SO se de fato pausou ferida (estancar vazio = no-op, nao pune).
                if estado.feridas_ativas:
                    await ajustar_fadiga(sessao_id, +2)
            # CURAR: MP>=10 E ha ferida -> gasta 10 MP, fecha a MAIS ANTIGA (cura infeccao tambem).
            elif estado.acao_atual == "curar" and estado.feridas_ativas:
                if await gastar_mp_cura(sessao_id):
                    estado.feridas_ativas.pop(0)
            # SANGRAMENTO: -1 Vigor por ferida aberta nao-estancada (clamp piso 0). Automatico.
            _drena = sum(1 for _f in estado.feridas_ativas if _f["turnos_estancada"] == 0)
            if _drena:
                await drenar_vigor(sessao_id, _drena)
            # decrementa o estancamento das feridas pausadas (>0 -> -1).
            for _f in estado.feridas_ativas:
                if _f["turnos_estancada"] > 0:
                    _f["turnos_estancada"] -= 1
    # Saida 1: o Cronista parou no limiar e pediu um teste -> arma o dado.
    # A faixa volta a ele no [ESTADO] do proximo turno (via resultado_pendente).
    if estado.acao_atual == "fugir" and estado.inimigo is not None and estado.inimigo.get("hp", 0) > 0 and not vestindo:
        # FUGA (gradiente): sair da luta exige o dado. CD pelo tier do alvo, destreza,
        # mod real da ficha. As 5 faixas decidem saida + custo no ao_rolar_dado.
        _cd_fuga = CD_TIER.get(estado.inimigo.get("tier"), 12)
        _mod_fuga = await resolver_mod_atributo(sessao_id, "destreza")
        estado.teste_pendente = {"intencao": "fugir", "atributo": "destreza", "cd": _cd_fuga, "mod": _mod_fuga}
        js(_armar_dado_js(estado.teste_pendente))
    elif teste:
        _mod_real = await resolver_mod_atributo(sessao_id, teste["atributo"])
        # Regua de crianca (Modo Infancia): a ficha adulta dorme -> o modificador do teste NAO
        # e o mod do atributo adulto, e sim um modificador pequeno, clampado a [-1,+1]. Mantem a
        # DIRECAO (agil leva leve vantagem, miudo leve desvantagem) mas encolhe a magnitude. O
        # teste CONTINUA aparecendo (teste_pendente + armarDado). Fora da infancia: mod real.
        teste["mod"] = max(-1, min(1, _mod_real)) if is_infancia else _mod_real
        estado.teste_pendente = teste
        js(_armar_dado_js(estado.teste_pendente))
    elif estado.acao_atual == "ataque" and estado.inimigo is not None and estado.inimigo.get("hp", 0) > 0 and not vestindo:
        # ARME SINTETICO (Fatia 2): atacar inimigo vivo SEM o Cronista pedir teste ->
        # o MOTOR arma o dado. Nenhum golpe resolve sem o dado; tira da IA o poder de
        # matar narrando. forca (golpe bruto), CD pelo tier. O explicito (elif teste:)
        # vence; este so dispara quando o Cronista esqueceu.
        _cd_atk = CD_TIER.get(estado.inimigo.get("tier"), 12)
        # Fatia 1 itens: forca pura + bonus_ataque da arma equipada (0 se nada/erro).
        _mod_atk = await resolver_mod_atributo(sessao_id, "forca") + await bonus_ataque_equipado(sessao_id)
        estado.teste_pendente = {"intencao": "golpe", "atributo": "forca", "cd": _cd_atk, "mod": _mod_atk}
        js(_armar_dado_js(estado.teste_pendente))


async def _pagina_jogar(com_ficha: bool = False, personagem: int | None = None):
    # Corpo unico do /jogar. com_ficha=False -> shell vivo de sempre (byte-identico).
    # com_ficha=True -> o mesmo shell + a ficha estilo C enxertada (so no /jogar-c).
    await aguardar_conexao_websocket("Abrindo a folha...")

    historico: list[dict] = []
    ocupado = False   # trava de turno: barra acao concorrente durante o await do Cronista
    geracao = 0       # token de geracao: recomecar incrementa e invalida narrar em voo
    pressao_atual = 0
    teste_pendente = None      # {intencao, mod, cd} aguardando rolagem
    resultado_pendente = None  # str "intencao — faixa" para o proximo [ESTADO]
    sessao_atual = await _resolver_sessao(personagem) if personagem is not None else SESSAO_ID   # personagem -> sessao dele; sem personagem -> SESSAO_ID (compat). Tier 6: rebinda no lifecycle.
    # Conserto 3: personagem pedido mas a sessao nao resolveu (inexistente ou banco fora)
    # -> _resolver_sessao devolve None. NUNCA jogamos na SESSAO_ID de OUTRO personagem:
    # aviso sobrio, e o `return` impede ligar qualquer handler de jogo (zero escrita).
    if personagem is not None and sessao_atual is None:
        ui.add_head_html(_FONTS + _CSS)
        ui.html(
            '<div class="alderyn-stage atm-ermo"><main class="pagina tela tela-jogo">'
            '<div class="head"><span class="ttl">vig&iacute;lia&nbsp;quebrada</span>'
            '<span class="ln"></span><a class="sair" href="/oficina">&larr;&nbsp;oficina</a></div>'
            '<div class="miolo"><div class="corpo" style="text-align:center">'
            '<p>N&atilde;o foi poss&iacute;vel abrir a sua sess&atilde;o.</p>'
            '<p style="opacity:.8">Recarregue a p&aacute;gina, ou volte &agrave; oficina e tente de novo.</p>'
            '</div></div></main></div>'
        )
        return
    # Campanha do protagonista: esta sessao e a do Gabriel Varekhor (id 8, campanha 2)?
    # So entao ligamos o Modo Infancia (bloco no prompt + combate dormente + regua de crianca
    # + ficha dormente). Computado UMA vez aqui e passado adiante (closures narrar/handlers).
    is_infancia = await _sessao_eh_infancia(sessao_atual)

    # Persistencia 2.6: a Pressao emocional restaura do banco (personagem_saude_mental)
    # em vez de comecar sempre em 0 -> fechar e reabrir preserva a tensao da sessao.
    pressao_atual = await _ler_pressao(sessao_atual)
    tensao_atual = None        # Combate Fatia 1: Tensao 1-10 EFEMERA (memoria, nao banco)
    inimigo = None             # Combate Fatia 3: ALVO ATUAL (ponteiro p/ um item de inimigos); None = sem briga
    inimigos = []              # Fatia 10a: BANDO inteiro (so vivos). inimigo aponta p/ um destes. [] = sem briga
    acao_atual = "ataque"      # Combate Fatia 4: natureza da acao do turno (ataque|defesa|estancar|curar)
    via_atual = "fisico"       # Fatia 9a: via do custo (fisico|magico|combo); default fisico (sem tag)
    feridas_ativas = []        # Fatia 8a: feridas abertas no combate atual (zera no FIM do combate)
    feridas_ja_usadas = []     # Fatia 8a: nomes ja usados (anti-repeticao); PERSISTE na sessao
    _infeccao_pendente = []    # Fatia 8a: feridas abertas que viram infeccao no proximo combate; PERSISTE
    modelo_atual = "claude-opus-4-8"   # seletor de modelo (UI): vale a partir do proximo turno

    # HUD Vida (Fatia "o quadro", 5A): assamos o hp REAL no HTML por token, em vez de
    # empurrar via setVida no load. Motivo provado: o NiceGUI re-renderiza o ui.html depois
    # que listeners mudam ("Re-rendering affected elements") e isso APAGAVA o setVida, deixando
    # a Vida no placeholder. O valor no proprio markup sobrevive ao re-render. READ-ONLY.
    # Sem dado (NULL/erro) -> "&mdash;/&mdash;" honesto, barra cheia neutra, sem realce.
    _v_num, _v_max, _v_pct, _v_baixa = "&mdash;", "&mdash;", "100", ""
    try:
        from db import get_session
        from sqlalchemy import text as _sa_text
        async with get_session() as _hud_s:
            _hud_r = (await _hud_s.execute(_sa_text(
                "SELECT p.hp_atual AS hp, p.hp_maximo AS hpx "
                "FROM sessoes s LEFT JOIN personagens p ON p.id = s.personagem_id "
                "WHERE s.id = :sid"
            ), {"sid": sessao_atual})).mappings().first()
        # Modo Infancia: a ficha ADULTA dorme -> NAO assa a Vida (fica no fallback honesto
        # &mdash;/&mdash;, como Vigor/Mana/Fadiga ja ficam; Tensao em 0). So o masthead fica.
        if not is_infancia and _hud_r and _hud_r.get("hp") is not None and _hud_r.get("hpx") is not None:
            _hp, _hpx = int(_hud_r["hp"]), max(1, int(_hud_r["hpx"]))
            _pct = max(0, min(100, round(_hp / _hpx * 100)))
            _v_num, _v_max, _v_pct = str(max(0, _hp)), str(_hpx), str(_pct)
            _v_baixa = "baixa" if _pct <= 30 else ""
    except Exception as _hud_e:  # noqa: BLE001 - degrada sem quebrar, como o resto do /jogar
        print(f"[hud] erro ao carregar Vida no load: {type(_hud_e).__name__}: {_hud_e}")
    # RESUME (repinta o scrollback): le os turnos ja gravados e assa no markup, no mesmo
    # passo da Vida (sobrevive ao re-render). Sessao nova/sem turnos -> '' (so o portal).
    _hist = await _historico_html(sessao_atual)
    # Resume direto-jogavel: COM historico, a tela cai pronta -> portal 'adentrar' escondido
    # e o input (#scrawl) ja visivel. Sao os MESMOS toggles que entrar()/ao_comecar fazem
    # (recon: entrar() so revela DOM, zero estado/Opus), assados no markup pra sobreviver ao
    # re-render. SEM historico (sessao nova) -> markup intacto: portal aparece, #scrawl oculto,
    # fluxo de primeira-vez identico ao de hoje (entrar pela 1a vez faz sentido).
    _tem_hist = bool(_hist)
    _portal_off = " oculto" if _tem_hist else ""
    _scrawl_off = "" if _tem_hist else " oculto"
    # A1: a Vida fica CINZA (dormente) quando nao tem numero real (infancia, ou sem dado).
    # Vigor/Mana/Fadiga ja entram dormente fixo no markup (sempre —/— em producao).
    _v_dorm = "" if _v_num != "&mdash;" else "dormente"
    corpo = (_BODY
             .replace("@@VIDANUM@@", _v_num)
             .replace("@@VIDAMAX@@", _v_max)
             .replace("@@VIDAPCT@@", _v_pct)
             .replace("@@VIDABAIXA@@", _v_baixa)
             .replace("@@VIDADORM@@", _v_dorm)
             .replace("@@HISTORICO@@", _hist)
             .replace("@@PORTAL_OFF@@", _portal_off)
             .replace("@@SCRAWL_OFF@@", _scrawl_off))

    ui.add_head_html(_FONTS + _CSS)
    if com_ficha and FICHA_C:
        # CSS da ficha logo APOS o _CSS atual. Escopado em .ficha -> nao mexe no :root.
        # FICHA_C_CSS vem como CSS cru (sem <style>); envelopamos aqui, igual o _CSS faz.
        ui.add_head_html(f"<style>{FICHA_C_CSS}</style>")
    ui.html(corpo)
    if com_ficha and FICHA_C:
        # BODY da ficha no nivel <body> (FORA do .alderyn-stage): o slide-over usa
        # position:fixed e precisa ser relativo a viewport, nao ao palco da cena.
        ui.add_body_html(FICHA_C_BODY)
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
    ui.run_javascript(_VITAIS_JS)
    # FASE FRONT: instala window.setOpcoes (botoes de acao no rodape).
    ui.run_javascript(_OPCOES_JS)

    # RESUME (trava d): com o historico repintado, rola o #miolo pro FIM no load -> o
    # turno mais recente fica visivel, como numa conversa. rAF por ~1s: re-cola embaixo
    # mesmo apos o re-render do NiceGUI e o layout assentar (estampa carregando). So
    # quando ha historico (_hist != ''); sessao nova fica no topo, no portal.
    if _hist:
        ui.run_javascript(
            "(function(){var n=0;function go(){var m=document.getElementById('miolo');"
            "if(m)m.scrollTop=m.scrollHeight;if(++n<60)requestAnimationFrame(go);}"
            "requestAnimationFrame(go);})();"
        )

    async def _empurrar_vitais(sessao_id: int, *, com_estaticos: bool = False) -> None:
        """Le os vitais do banco (query F unica) e empurra pra ficha. Roda no LOAD
        (com_estaticos=True -> tambem mods+identidade, que nao mudam) e ao FIM de cada
        turno (so os 5 vitais -> espelho vivo). Best-effort: erro/NULL -> degrada sem
        quebrar. O SISTEMA e dono dos numeros; a ficha espelha o BANCO (re-leitura)."""
        try:
            from db import get_session
            from sqlalchemy import text as _sa_text
            _sql = _sa_text(
                "SELECT p.mod_forca, p.mod_destreza, p.mod_constituicao, "
                "p.mod_inteligencia, p.mod_sabedoria, p.mod_carisma, "
                "p.hp_atual, p.hp_maximo, p.classe_primaria, p.nivel, p.divida_viva, "
                "p.vigor_atual, p.vigor_maximo, p.fadiga_atual, p.fadiga_maximo, "
                "m.mp_atual, m.mp_maximo "
                "FROM sessoes s LEFT JOIN personagens p ON p.id = s.personagem_id "
                "LEFT JOIN personagem_mana m ON m.personagem_id = s.personagem_id "
                "WHERE s.id = :sid"
            )
            async with get_session() as _sess:
                _row = (await _sess.execute(_sql, {"sid": sessao_id})).mappings().first()
        except Exception as _e:  # noqa: BLE001 - degrada sem quebrar, como o resto do /jogar
            print(f"[ficha_c] erro ao carregar vitais: {type(_e).__name__}: {_e}")
            return
        if not _row:
            return
        # Os 5 vitais (SEMPRE): best-effort POR CAMPO. NULL -> omite (barra fica placeholder).
        # 0 e valido (Fadiga/Dissolucao) -> is not None, NUNCA truthy.
        _vit = {}
        if _row.get("hp_atual") is not None and _row.get("hp_maximo") is not None:
            _vit["hp_atual"] = int(_row["hp_atual"])
            _vit["hp_maximo"] = int(_row["hp_maximo"])
        if _row.get("mp_atual") is not None and _row.get("mp_maximo") is not None:
            _vit["mp_atual"] = int(_row["mp_atual"])
            _vit["mp_maximo"] = int(_row["mp_maximo"])
        if _row.get("divida_viva") is not None:
            _vit["divida_viva"] = int(_row["divida_viva"])
        if _row.get("vigor_atual") is not None and _row.get("vigor_maximo") is not None:
            _vit["vigor_atual"] = int(_row["vigor_atual"])
            _vit["vigor_maximo"] = int(_row["vigor_maximo"])
        if _row.get("fadiga_atual") is not None and _row.get("fadiga_maximo") is not None:
            _vit["fadiga_atual"] = int(_row["fadiga_atual"])
            _vit["fadiga_maximo"] = int(_row["fadiga_maximo"])
        if _vit:
            ui.run_javascript(f"window.fichaSetVitais && window.fichaSetVitais({json.dumps(_vit)})")
        if not com_estaticos:
            return
        # Estaticos (SO no load): mods + identidade nao mudam por turno.
        _mapa_mods = {
            "FOR": "mod_forca", "DEX": "mod_destreza", "CON": "mod_constituicao",
            "INT": "mod_inteligencia", "SAB": "mod_sabedoria", "CHA": "mod_carisma",
        }
        _mods = {sig: int(_row[col]) for sig, col in _mapa_mods.items()
                 if _row.get(col) is not None}
        if _mods:
            ui.run_javascript(f"window.fichaSetAtributos && window.fichaSetAtributos({json.dumps(_mods)})")
        _ident = {}
        if _row.get("classe_primaria") is not None:
            _ident["classe"] = _row["classe_primaria"]
        if _row.get("nivel") is not None:
            _ident["nivel"] = int(_row["nivel"])
        if _ident:
            ui.run_javascript(
                f"window.fichaSetIdentidade && window.fichaSetIdentidade({json.dumps(_ident, ensure_ascii=False)})"
            )

    async def _empurrar_inventario(sessao_id: int) -> None:
        """Fatia inventario-EXIBICAO: resolve o personagem da sessao, le a posse (READ-ONLY)
        e empurra pra ficha (.f-inv) via fichaSetInventario -- troca os itens-semente fake
        por dados reais; lista vazia -> 'Mochila vazia.'. Best-effort: erro ao resolver ->
        nao mexe na ficha (semente fica, degrada sem quebrar). NAO escreve no banco."""
        try:
            from db import get_session
            from sqlalchemy import text as _t
            async with get_session() as _s:
                _r = (await _s.execute(_t(
                    "SELECT personagem_id AS pid FROM sessoes WHERE id = :sid"
                ), {"sid": sessao_id})).mappings().first()
            if not _r or _r.get("pid") is None:
                return
            _itens = await _ler_inventario(int(_r["pid"]))
        except Exception as _e:  # noqa: BLE001 - degrada sem quebrar, como o resto do /jogar
            print(f"[inventario] erro ao empurrar inventario: {type(_e).__name__}: {_e}")
            return
        ui.run_javascript(
            f"window.fichaSetInventario && window.fichaSetInventario({json.dumps(_itens, ensure_ascii=False)})"
        )

    async def _aplicar_dano_combate(sessao_id: int, faixa: str, fator: float = 1.0) -> None:
        """Combate Fatia 2: a FAIXA do 2d10 aplica consequencia num vital e ESCREVE no banco
        (UPDATE personagens + commit); a ficha reflete via _empurrar_vitais. A mesma faixa que
        o Cronista narra -> prosa e numero concordam. Vigor amortece, HP e o ferimento real.
        Clamp piso 0. So chamado em combate + /jogar-c (gate no caller).
        Fatia 4: fator escala o dano em voce (1.0 = ataque, byte-identico ao original;
        0.5 = defesa, dano pela metade). round() preserva os inteiros no fator 1.0."""
        if faixa in ("sucesso_critico", "sucesso"):
            return  # desfecho bom -> nenhum dano (delta zero, nada a escrever)
        try:
            import math
            from db import get_session
            from sqlalchemy import text as _sa_text
            # ATOMICO: SELECT + UPDATE na MESMA session/transacao (le e grava o mesmo estado).
            async with get_session() as _s:
                _row = (await _s.execute(_sa_text(
                    "SELECT p.id AS pid, p.hp_atual, p.hp_maximo, p.vigor_atual "
                    "FROM sessoes s JOIN personagens p ON p.id = s.personagem_id "
                    "WHERE s.id = :sid"
                ), {"sid": sessao_id})).mappings().first()
                if not _row or _row.get("hp_atual") is None or _row.get("vigor_atual") is None:
                    return  # sem ficha/vitais -> nada a aplicar
                pid = _row["pid"]
                hp = int(_row["hp_atual"])
                vig = int(_row["vigor_atual"])
                hpmax = int(_row["hp_maximo"]) if _row.get("hp_maximo") is not None else hp
                if faixa == "sucesso_parcial":
                    vig -= round(2 * fator)
                elif faixa == "falha":
                    vig -= round(4 * fator)
                    if vig < 0:        # transbordo: o deficit que o Vigor nao absorveu cai no HP
                        hp += vig       # vig negativo -> subtrai do hp
                elif faixa == "falha_critica":
                    hp -= math.ceil(hpmax * 0.15 * fator)   # golpe limpo passa a guarda; Vigor intacto
                hp = max(0, hp)        # clamp piso 0 ANTES do UPDATE (nunca grava negativo)
                vig = max(0, vig)
                await _s.execute(_sa_text(
                    "UPDATE personagens SET hp_atual = :hp, vigor_atual = :vig WHERE id = :pid"
                ), {"hp": hp, "vig": vig, "pid": pid})
                await _s.commit()
        except Exception as _e:  # noqa: BLE001 - degrada sem quebrar; nao trava a rolagem
            print(f"[combate] erro ao aplicar dano ({faixa}): {type(_e).__name__}: {_e}")
            return
        # SO depois do commit: 2a session rele o ja-gravado -> a barra mexe na hora da rolagem.
        await _empurrar_vitais(sessao_id)

    async def _drenar_vigor(sessao_id: int, n: int) -> None:
        """Fatia 8a: sangramento -> subtrai n do vigor_atual (clamp piso 0). Atomico + re-push."""
        if n <= 0:
            return
        try:
            from db import get_session
            from sqlalchemy import text as _t
            async with get_session() as _s:
                _r = (await _s.execute(_t(
                    "SELECT p.id AS pid, p.vigor_atual FROM sessoes s "
                    "JOIN personagens p ON p.id = s.personagem_id WHERE s.id = :sid"
                ), {"sid": sessao_id})).mappings().first()
                if not _r or _r.get("vigor_atual") is None:
                    return
                _v = max(0, int(_r["vigor_atual"]) - n)
                await _s.execute(_t("UPDATE personagens SET vigor_atual = :v WHERE id = :pid"),
                                 {"v": _v, "pid": _r["pid"]})
                await _s.commit()
        except Exception as _e:  # noqa: BLE001 - degrada sem quebrar
            print(f"[feridas] erro ao drenar vigor: {type(_e).__name__}: {_e}")
            return
        await _empurrar_vitais(sessao_id)

    async def _gastar_mp(sessao_id: int, n: int) -> bool:
        """Fatia 9a: gasta n de MP -> se mp_atual>=n, gasta e retorna True; senao False (sem gastar).
        Atomico. Degrada sem quebrar. Generaliza o gasto da cura (Fatia 8a) p/ qualquer custo."""
        if n <= 0:
            return True
        try:
            from db import get_session
            from sqlalchemy import text as _t
            async with get_session() as _s:
                _r = (await _s.execute(_t(
                    "SELECT m.personagem_id AS pid, m.mp_atual FROM sessoes s "
                    "JOIN personagem_mana m ON m.personagem_id = s.personagem_id WHERE s.id = :sid"
                ), {"sid": sessao_id})).mappings().first()
                if not _r or _r.get("mp_atual") is None or int(_r["mp_atual"]) < n:
                    return False
                await _s.execute(_t("UPDATE personagem_mana SET mp_atual = :m WHERE personagem_id = :pid"),
                                 {"m": int(_r["mp_atual"]) - n, "pid": _r["pid"]})
                await _s.commit()
        except Exception as _e:  # noqa: BLE001 - degrada sem quebrar
            print(f"[feridas] erro ao gastar mp: {type(_e).__name__}: {_e}")
            return False
        await _empurrar_vitais(sessao_id)
        return True

    async def _gastar_mp_cura(sessao_id: int) -> bool:
        """Fatia 8a: curar -> gasta 10 MP (delega a _gastar_mp; nao duplica a query)."""
        return await _gastar_mp(sessao_id, 10)

    async def _disparar_julgamento(pid: int, sessao_id: int):
        """Corrupcao Fatia 2: cap 100 COM veretheos -> Julgamento consciente. Chama a RPC
        disparar_julgamento (que JA grava status_narrativo e gera epilogo/d100/herdeiro) e
        DEVOLVE epilogo_narrativo (fallback mensagem_narrador) p/ virar resultado_pendente,
        narrado na abertura do proximo turno. NAO grava status_narrativo (a RPC faz). Degrada."""
        _ret = None
        try:
            from db import get_session
            from sqlalchemy import text as _t
            async with get_session() as _s:
                _ret = (await _s.execute(_t(
                    "SELECT disparar_julgamento(:pid, :sid)"
                ), {"pid": pid, "sid": sessao_id})).scalar()
                await _s.commit()
        except Exception as _e:  # noqa: BLE001 - degrada sem quebrar
            print(f"[corrupcao] erro ao disparar julgamento: {type(_e).__name__}: {_e}")
            return None
        if isinstance(_ret, str):
            try:
                _ret = json.loads(_ret)
            except Exception:  # noqa: BLE001
                _ret = None
        if isinstance(_ret, dict):
            print(f"[corrupcao] Julgamento disparado (tipo {_ret.get('tipo_julgamento')})")
            return _ret.get("epilogo_narrativo") or _ret.get("mensagem_narrador")
        print("[corrupcao] Julgamento disparado (sem epilogo no retorno)")
        return None

    async def _colapso_corrompido(pid: int, sessao_id: int, nome):
        """Corrupcao Fatia 2: cap 100 SEM veretheos -> 'Corrompido sem rosto'. Deterministico:
        UPDATE direto status_narrativo='colapsado' (valor legal do CHECK; molde _ajustar_fadiga;
        sem d100, sem herdeiro, sem epilogo com sabor). A distincao 8%/92% NAO mora no status
        (ambos -> 'colapsado'); mora na profundidade do registro (os 8% gravam epilogo/ref via
        RPC). NAO chama disparar_julgamento (a RPC recusa veretheos=false). DEVOLVE a linha SECA
        p/ resultado_pendente. Degrada."""
        try:
            from db import get_session
            from sqlalchemy import text as _t
            async with get_session() as _s:
                await _s.execute(_t(
                    "UPDATE personagens SET status_narrativo = 'colapsado' WHERE id = :pid"
                ), {"pid": pid})
                await _s.commit()
        except Exception as _e:  # noqa: BLE001 - degrada sem quebrar
            print(f"[corrupcao] erro no colapso simples: {type(_e).__name__}: {_e}")
            return None
        print("[corrupcao] Corrompido sem rosto (status colapsado)")
        _quem = nome or "O que restou"
        return (f"A Dívida encheu sem compreensão. {_quem} se perde — "
                "reescrito em mais uma coisa sem rosto, sem nome.")

    async def _registrar_divida(sessao_id: int, peso: int, sabor: str, motivo: str):
        """Corrupcao: SOMA divida via RPC registrar_divida. Espelha _gastar_mp (SQLAlchemy
        text() + commit). Resolve pid+veretheos+nome (uma query), delta = peso x 5, chama a
        RPC, atualiza a barra. Degrada sem quebrar.
        Fatia 2: cap por divida_depois>=100 bifurca o Julgamento (veretheos? consciente :
        Corrompido sem rosto) e DEVOLVE o texto do desfecho (str|None) p/ o caller pôr em
        estado.resultado_pendente. cap_atingido e TRUE em 0 OU 100 -> use divida_depois."""
        _ret = None
        _pid = _nome = None
        _veretheos = False
        try:
            from db import get_session
            from sqlalchemy import text as _t
            _delta = peso * 5
            async with get_session() as _s:
                # Fatia 2: resolve pid + veretheos + nome na MESMA ida ao banco (sem query extra).
                _r = (await _s.execute(_t(
                    "SELECT p.id AS pid, p.veretheos_comprehendido AS veretheos, p.nome AS nome "
                    "FROM sessoes s JOIN personagens p ON p.id = s.personagem_id WHERE s.id = :sid"
                ), {"sid": sessao_id})).mappings().first()
                if not _r or _r.get("pid") is None:
                    return None
                _pid = _r["pid"]
                _veretheos = bool(_r.get("veretheos"))
                _nome = _r.get("nome")
                _ret = (await _s.execute(_t(
                    "SELECT registrar_divida(:pid, :delta, :tag, 'magia', :motivo, :sid)"
                ), {"pid": _pid, "delta": _delta, "tag": sabor,
                    "motivo": motivo, "sid": sessao_id})).scalar()
                await _s.commit()
        except Exception as _e:  # noqa: BLE001 - degrada sem quebrar, como os outros helpers
            print(f"[corrupcao] erro ao registrar divida: {type(_e).__name__}: {_e}")
            return None
        # retorno jsonb: pode vir como str (json) ou dict; divida_depois decide o cap.
        if isinstance(_ret, str):
            try:
                _ret = json.loads(_ret)
            except Exception:  # noqa: BLE001
                _ret = None
        _depois = _ret.get("divida_depois") if isinstance(_ret, dict) else None
        print(f"[corrupcao] +{peso * 5} ({sabor}) -> divida {_depois}")
        # Fatia 2: cap 100 -> bifurcacao SINCRONA do Julgamento (no momento de bater 100;
        # casts seguintes em 100 fazem a RPC ERRAR -> tem de ser agora). veretheos decide o
        # rosto; o desfecho volta como texto p/ o caller pôr em estado.resultado_pendente.
        _desfecho = None
        if isinstance(_depois, int) and _depois >= 100:
            if _veretheos:
                _desfecho = await _disparar_julgamento(_pid, sessao_id)
            else:
                _desfecho = await _colapso_corrompido(_pid, sessao_id, _nome)
        await _empurrar_vitais(sessao_id)
        return _desfecho

    async def _ajustar_fadiga(sessao_id: int, delta: int) -> None:
        """Fatia 9b: soma delta a fadiga_atual (clamp 0..fadiga_maximo). Atomico + re-push.
        delta>0 cansa (estancar +2 / falha_critica +1), delta<0 recupera (fim de combate -3).
        So escreve se MUDOU (clamp no-op no piso/teto -> sem UPDATE, sem push). Degrada."""
        if delta == 0:
            return
        try:
            from db import get_session
            from sqlalchemy import text as _t
            async with get_session() as _s:
                _r = (await _s.execute(_t(
                    "SELECT p.id AS pid, p.fadiga_atual, p.fadiga_maximo FROM sessoes s "
                    "JOIN personagens p ON p.id = s.personagem_id WHERE s.id = :sid"
                ), {"sid": sessao_id})).mappings().first()
                if not _r or _r.get("fadiga_atual") is None or _r.get("fadiga_maximo") is None:
                    return
                _atual = int(_r["fadiga_atual"]); _max = int(_r["fadiga_maximo"])
                _novo = max(0, min(_max, _atual + delta))   # clamp 0..fadiga_maximo
                if _novo == _atual:
                    return  # ja no piso/teto -> nada a gravar
                await _s.execute(_t("UPDATE personagens SET fadiga_atual = :f WHERE id = :pid"),
                                 {"f": _novo, "pid": _r["pid"]})
                await _s.commit()
        except Exception as _e:  # noqa: BLE001 - degrada sem quebrar
            print(f"[fadiga] erro ao ajustar fadiga: {type(_e).__name__}: {_e}")
            return
        await _empurrar_vitais(sessao_id)

    async def _ler_fadiga(sessao_id: int):
        """Fatia 9b: le (fadiga_atual, fadiga_maximo) p/ a penalidade do 2d10. Leitura unica
        por rolagem. Degrada p/ (0, 0) sem quebrar (caller guarda _fm>0 -> penalidade vira 0)."""
        try:
            from db import get_session
            from sqlalchemy import text as _t
            async with get_session() as _s:
                _r = (await _s.execute(_t(
                    "SELECT p.fadiga_atual, p.fadiga_maximo FROM sessoes s "
                    "JOIN personagens p ON p.id = s.personagem_id WHERE s.id = :sid"
                ), {"sid": sessao_id})).mappings().first()
            if not _r or _r.get("fadiga_atual") is None or _r.get("fadiga_maximo") is None:
                return (0, 0)
            return (int(_r["fadiga_atual"]), int(_r["fadiga_maximo"]))
        except Exception as _e:  # noqa: BLE001 - degrada sem quebrar
            print(f"[fadiga] erro ao ler fadiga: {type(_e).__name__}: {_e}")
            return (0, 0)

    async def _ler_infeccao(sessao_id: int) -> list:
        """Fatia 8b: le ferida_infeccao_pendente -> lista de {nome, severidade}.
        Trata JSONB vindo como str OU ja-desserializado. Degrada p/ [] sem quebrar."""
        try:
            from db import get_session
            from sqlalchemy import text as _t
            async with get_session() as _s:
                _r = (await _s.execute(_t(
                    "SELECT p.ferida_infeccao_pendente AS fip FROM sessoes s "
                    "JOIN personagens p ON p.id = s.personagem_id WHERE s.id = :sid"
                ), {"sid": sessao_id})).mappings().first()
            if not _r:
                return []
            _v = _r.get("fip")
            if _v is None:
                return []
            if isinstance(_v, str):
                _v = json.loads(_v)
            return _v if isinstance(_v, list) else []
        except Exception as _e:  # noqa: BLE001 - degrada sem quebrar
            print(f"[feridas] erro ao ler infeccao: {type(_e).__name__}: {_e}")
            return []

    async def _gravar_infeccao(sessao_id: int, lista: list) -> None:
        """Fatia 8b: grava a lista de infeccao pendente na coluna JSONB (CAST explicito).
        Grava [] tambem (limpa). Degrada sem quebrar."""
        try:
            from db import get_session
            from sqlalchemy import text as _t
            async with get_session() as _s:
                _r = (await _s.execute(_t(
                    "SELECT personagem_id AS pid FROM sessoes WHERE id = :sid"
                ), {"sid": sessao_id})).mappings().first()
                if not _r:
                    return
                await _s.execute(_t(
                    "UPDATE personagens SET ferida_infeccao_pendente = CAST(:j AS jsonb) "
                    "WHERE id = :pid"
                ), {"j": json.dumps(lista), "pid": _r["pid"]})
                await _s.commit()
        except Exception as _e:  # noqa: BLE001 - degrada sem quebrar
            print(f"[feridas] erro ao gravar infeccao: {type(_e).__name__}: {_e}")

    # Fatia 8b (conserto de gate): a infeccao e ESTADO DE COMBATE -> gate `com_ficha`,
    # igual a escrita (fim de combate). FICHA_C so gateia a UI da ficha, nao isto.
    # _infeccao_pendente e free-var de closure (init no 8a); sessao_atual ja bindada.
    if com_ficha:
        _infeccao_pendente = await _ler_infeccao(sessao_atual)

    if com_ficha and FICHA_C:
        # FICHA_C_JS auto-monta o botao "ficha" no .head (irmao de #abrir-config), com
        # retry ate o Vue montar -- por isso nao injetamos o botao por aqui.
        ui.run_javascript(FICHA_C_JS)
        # LOAD: liga os 5 vitais + mods + identidade a partir do banco (query F unica).
        await _empurrar_vitais(sessao_atual, com_estaticos=True)
        # Inventario-EXIBICAO: troca os 6 itens-semente fake do grid .f-inv pela posse
        # real do banco (READ-ONLY). So no LOAD: a posse nao muda por turno nesta fatia.
        await _empurrar_inventario(sessao_atual)
        # Combate Fatia 1: sem combate no load -> barra de Tensao escondida.
        ui.run_javascript("window.fichaSetTensao && window.fichaSetTensao(null)")
        # Combate Fatia 7: vignette de momentum + flash (CSS + overlays), SO no /jogar-c.
        ui.add_head_html(_MOMENTUM_CSS)
        ui.add_body_html(_MOMENTUM_HTML)

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
        nonlocal pressao_atual, ocupado, geracao, sessao_atual, modelo_atual, teste_pendente, resultado_pendente, tensao_atual, inimigo, inimigos, acao_atual, via_atual, feridas_ativas, feridas_ja_usadas, _infeccao_pendente
        # trava de turno: se ja ha um turno em voo, ignora a nova acao ANTES de
        # tocar o historico - senao dois "user" seguidos quebram a alternancia.
        if ocupado:
            return
        ocupado = True
        # FASE FRONT: cada turno comeca com o rodape de opcoes LIMPO; o fim do turno
        # redesenha exatamente as opcoes desta resposta (ou nada). Sem residuo do turno anterior.
        _js("window.setOpcoes && window.setOpcoes([])")
        minha_geracao = geracao   # se recomecar acontecer durante o await, muda
        # Fatia 1: a espinha narrada (montar -> Opus -> parse) foi extraida para
        # executar_turno_narrado (modulo). A trava `ocupado`, o bloco de combate e as
        # gravacoes narrador/pressao ficam AQUI, byte-identicos. A funcao MUTA `estado`
        # (historico, pressao_atual, resultado_pendente) e devolve ResultadoTurno.
        _estado_turno = EstadoTurno(historico, pressao_atual, sessao_atual, modelo_atual, resultado_pendente, is_infancia)
        _ui_turno = _UITurno()
        _ui_turno.arrive = _arrive
        _ui_turno.pondera = _pondera
        _ui_turno.stream_iniciar = _stream_iniciar
        _ui_turno.stream_update = _stream_update
        _ui_turno.stream_finalizar = _stream_finalizar
        _ui_turno.stream_abortar = _stream_abortar
        try:
            _res = await executar_turno_narrado(
                _estado_turno, msg_usuario, mostrar_acao,
                ui=_ui_turno, inimigos=inimigos,
                deve_abortar=lambda: minha_geracao != geracao,
                cauda_voz=True,  # A2.1-flip: cauda de voz ON em producao
                em_combate=(tensao_atual is not None),  # ADR-008 3a: buffer so em combate (tensao pre-turno)
            )
            # sincroniza os nonlocals que a funcao mutou (mesma semantica do head antigo)
            pressao_atual = _estado_turno.pressao_atual
            resultado_pendente = _estado_turno.resultado_pendente
            if _res.abortado:
                return
            prosa = _res.prosa
            atmosfera = _res.atmosfera
            teste = _res.teste
            resposta = _res.resposta
            _vestindo = _res.vestindo
            # Combate Fatia 1 + parse de combate: extraido para processar_combate (modulo).
            # CASCA: empacota as 10 cells num EstadoCombate, processa, desempacota as 10.
            # _vestindo/teste sao as 2 seams de ENTRADA da espinha (consumidas no arme).
            # A trava ocupado, o try/except/finally e as gravacoes ficam FORA (no narrar).
            _ec = EstadoCombate(
                teste_pendente, resultado_pendente, tensao_atual, inimigo, inimigos,
                acao_atual, via_atual, feridas_ativas, feridas_ja_usadas, _infeccao_pendente,
            )
            await processar_combate(
                _ec,
                resposta=resposta,
                teste=teste,
                vestindo=_vestindo,
                com_ficha=com_ficha,
                sessao_id=sessao_atual,
                js=_js,
                gravar_infeccao=_gravar_infeccao,
                ajustar_fadiga=_ajustar_fadiga,
                gastar_mp_cura=_gastar_mp_cura,
                drenar_vigor=_drenar_vigor,
                resolver_mod_atributo=_resolver_mod_atributo,
                registrar_divida=_registrar_divida,
                is_infancia=is_infancia,
            )
            # desempacota as 10 cells (simetrico com a casca de resolver_dado). O parse muta 9;
            # resultado_pendente round-trips INALTERADA (o parse nao a escreve) -> desempacotar
            # as 10 e seguro e evita o erro classico de esquecer uma.
            teste_pendente = _ec.teste_pendente
            resultado_pendente = _ec.resultado_pendente
            tensao_atual = _ec.tensao_atual
            inimigo = _ec.inimigo
            inimigos = _ec.inimigos
            acao_atual = _ec.acao_atual
            via_atual = _ec.via_atual
            feridas_ativas = _ec.feridas_ativas
            feridas_ja_usadas = _ec.feridas_ja_usadas
            _infeccao_pendente = _ec._infeccao_pendente
            # Opcao A: magia conjurada FORA de combate cobra Mana (4 MP), igual ao combate.
            # SO no /jogar-c (com_ficha) e fora de combate (tensao None) com via magica ditada.
            # Em combate quem cobra e resolver_dado (no roll), gated por tensao not None -> aqui
            # o guard tensao None garante que nao ha double-charge. Sem mana, _gastar_mp degrada
            # (False) e a magia nao acontece mecanicamente, como em combate.
            if com_ficha and tensao_atual is None and via_atual in ("magico", "combo"):
                await _gastar_mp(sessao_atual, 4)
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
            # Persistencia 2.6: espelha a Pressao mostrada no HUD para o banco (mesma
            # fonte de verdade do reload). Best-effort: erro nao derruba o turno.
            await _gravar_pressao(sessao_atual, pressao_atual)
            # Combate Fatia 1: a barra da ficha mostra TENSAO (1-10) em combate, escondida
            # fora. Substitui o push de pressao na barra (pressao segue no HUD do shell acima).
            _js(f"window.fichaSetTensao && window.fichaSetTensao({json.dumps(tensao_atual)})")
            # a cena so troca de pele se o Cronista pediu uma atmosfera valida;
            # senao 'atmosfera' vem None e a pele atual se mantem.
            if atmosfera:
                _js(f"window.setAtmosfera && window.setAtmosfera({json.dumps(atmosfera)})")
            # FASE FRONT: desenha os botoes de acao desta resposta (3-6) no rodape. Lista
            # vazia/None some o bloco. Clique preenche #cmd e foca; o jogador confirma.
            _js(f"window.setOpcoes && window.setOpcoes({json.dumps(_res.opcoes or [])})")
            # Combate Fatia 0: ao FIM do turno, re-le os vitais do banco e re-empurra
            # (espelho vivo). Pressao + atmosfera acima seguem como antes. So no /jogar-c
            # (guard) -> 1 query read-only por turno aqui, zero no /jogar de producao.
            if com_ficha and FICHA_C:
                await _empurrar_vitais(sessao_atual)
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
        # ADENTRAR so faz a transicao pro modo de jogo (entrar). O jogo comeca EM
        # SILENCIO, como o Claude: NADA e narrado automaticamente e NENHUMA chamada ao
        # Opus acontece aqui. A 1a chamada ao Cronista passa a ser a 1a acao do jogador
        # (ao_agir). ABERTURA_MSG fica definida de proposito (documenta a intencao e
        # permite reverter), so deixou de ser disparada.
        _js("window.Jogar && window.Jogar.entrar()")

    async def ao_agir(e):
        args = e.args if isinstance(e.args, dict) else {}
        texto = (args.get("text") or "").strip()
        if not texto:
            return
        await narrar(texto, mostrar_acao=True)

    async def ao_recomecar(_=None):
        # zera a cena sem reiniciar o servidor: limpa historico, Pressao e tela,
        # devolve o portal de entrada. Custo zero.
        nonlocal pressao_atual, ocupado, geracao, teste_pendente, resultado_pendente, tensao_atual, inimigo, inimigos, feridas_ativas, feridas_ja_usadas, _infeccao_pendente
        # invalida qualquer turno em voo (o narrar checa a geracao apos o await e
        # se abandona) e destrava. Assim recomecar no meio de um turno nao deixa
        # prosa fantasma cair na tela limpa nem o jogo preso.
        geracao += 1
        ocupado = False
        _pondera(False)
        historico.clear()
        pressao_atual = 0
        await _gravar_pressao(sessao_atual, 0)   # Persistencia 2.6: reset zera memoria E banco
        tensao_atual = None   # Combate Fatia 1: recomecar zera a Tensao -> barra some
        inimigo = None        # Combate Fatia 3: recomecar limpa o inimigo junto
        inimigos = []         # ... e o bando junto (senao a trava 3217 ressuscita a luta)
        # Lousa limpa (decisao Gabriel): recomecar tb zera TODAS as cells efemeras de
        # combate -- ferimentos e infeccao pendente. A unica cicatriz duravel que
        # PERMANECE e a divida_viva (corrupcao), que este handler nao toca.
        feridas_ativas = []
        feridas_ja_usadas = []
        _infeccao_pendente = []
        if com_ficha:
            await _gravar_infeccao(sessao_atual, [])   # zera a infeccao duravel no banco tb
        teste_pendente = None
        resultado_pendente = None
        _js("window.Jogar && window.Jogar.recomecar()")
        _js("window.setOpcoes && window.setOpcoes([])")  # FASE FRONT: rodape de acao some no reset
        _js("window.Jogar && window.Jogar.setPressao(0)")
        _js("window.fichaSetTensao && window.fichaSetTensao(null)")
        _js("window.setAtmosfera && window.setAtmosfera('ermo', {forcar:true})")

    async def ao_encerrar(_=None):
        # Tier 6: sela a sessao atual (extrai fatos -> canon -> recap) e ABRE a
        # proxima; o /jogar rebinda pra ela. O recap desta sessao vira o
        # recap_anterior da proxima (montar_contexto_narrador), entao o primeiro
        # turno da sessao nova ja chega com "o que veio antes".
        nonlocal pressao_atual, ocupado, geracao, sessao_atual, teste_pendente, resultado_pendente, tensao_atual, inimigo, inimigos, feridas_ativas, feridas_ja_usadas, _infeccao_pendente
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
        await _gravar_pressao(sessao_atual, 0)   # Persistencia 2.6: reset zera memoria E banco
        tensao_atual = None   # Combate Fatia 1: selar a sessao zera a Tensao -> barra some
        inimigo = None        # Combate Fatia 3: selar limpa o inimigo junto
        inimigos = []         # ... e o bando junto (senao a trava 3217 ressuscita a luta)
        # Lousa limpa (decisao Gabriel): selar tb zera TODAS as cells efemeras de
        # combate -- ferimentos e infeccao pendente. A unica cicatriz duravel que
        # PERMANECE e a divida_viva (corrupcao), que este handler nao toca.
        feridas_ativas = []
        feridas_ja_usadas = []
        _infeccao_pendente = []
        if com_ficha:
            await _gravar_infeccao(sessao_atual, [])   # zera a infeccao duravel no banco tb
        teste_pendente = None
        resultado_pendente = None
        _js("window.Jogar && window.Jogar.recomecar()")
        _js("window.setOpcoes && window.setOpcoes([])")  # FASE FRONT: rodape de acao some no reset
        _js("window.Jogar && window.Jogar.setPressao(0)")
        _js("window.fichaSetTensao && window.fichaSetTensao(null)")
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
        # O dado so MOSTRA; o veredito vem do Dice Engine (app/resolucao_2d10):
        # 2d10 + mod vs CD, 5 faixas, naturais 2/20 e limiares por margem.
        # Fatia N: a logica da rolagem foi extraida para resolver_dado (modulo). Aqui o
        # handler vira CASCA: empacota as 10 cells num EstadoCombate, chama o motor com as
        # deps injetadas (_js + 5 helpers de DB), e desempacota as 10 de volta nas nonlocals
        # (estado COMPARTILHADO com o parse do narrar). A trava/ocupado fica fora (no narrar).
        nonlocal teste_pendente, resultado_pendente, tensao_atual, inimigo, inimigos
        nonlocal acao_atual, via_atual, feridas_ativas, feridas_ja_usadas, _infeccao_pendente
        # GUARDA DE SERVIDOR: so resolve se ha pedido pendente. Um emit cru de 'rolar_dado'
        # (sem o Cronista/motor ter armado) e ignorado -> sem rolagem nao solicitada, sem dano
        # nao pedido+gravado em combate. O pedido legitimo e consumido por resolver_dado
        # (estado.teste_pendente=None, desempacotado abaixo), entao um 2o emit sem novo pedido
        # tambem cai aqui -> mata o dano repetivel. So a existencia; nao toca o motor.
        if not teste_pendente:
            return
        _ec = EstadoCombate(
            teste_pendente, resultado_pendente, tensao_atual, inimigo, inimigos,
            acao_atual, via_atual, feridas_ativas, feridas_ja_usadas, _infeccao_pendente,
        )
        await resolver_dado(
            _ec,
            sessao_id=sessao_atual,
            com_ficha=com_ficha,
            js=_js,
            ler_fadiga=_ler_fadiga,
            aplicar_dano_combate=_aplicar_dano_combate,
            drenar_vigor=_drenar_vigor,
            gastar_mp=_gastar_mp,
            ajustar_fadiga=_ajustar_fadiga,
        )
        # desempacota as 10 cells (a ordem do init; nenhuma fica de fora)
        teste_pendente = _ec.teste_pendente
        resultado_pendente = _ec.resultado_pendente
        tensao_atual = _ec.tensao_atual
        inimigo = _ec.inimigo
        inimigos = _ec.inimigos
        acao_atual = _ec.acao_atual
        via_atual = _ec.via_atual
        feridas_ativas = _ec.feridas_ativas
        feridas_ja_usadas = _ec.feridas_ja_usadas
        _infeccao_pendente = _ec._infeccao_pendente

    ui.on("jogar_action", ao_agir)
    ui.on("jogar_comecar", ao_comecar)
    ui.on("jogar_recomecar", ao_recomecar)
    ui.on("jogar_encerrar", ao_encerrar)
    ui.on("trocar_modelo", ao_trocar_modelo)
    ui.on("rolar_dado", ao_rolar_dado)


@ui.page("/jogar")
async def pagina_jogar(personagem: int | None = None):
    # Rota viva. Producao (ii): a sessao nasce do personagem carregado (?personagem=N).
    # Etapa D (FUSAO): combate REAL na producao. /jogar-c segue intacto (nao deletado).
    await _pagina_jogar(com_ficha=True, personagem=personagem)


@ui.page("/jogar-c")
async def pagina_jogar_c(personagem: int | None = None):
    # Mesma casca + ficha estilo C (slide-over), atras do flag FICHA_C.
    await _pagina_jogar(com_ficha=True, personagem=personagem)
