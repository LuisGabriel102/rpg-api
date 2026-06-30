"""
Gerador de prompts de imagem — Catedral do Alderyn (Módulo 4.6.2)

Monta prompts otimizados para 3 modelos de IA (FLUX Kontext, Gemini Nano Banana 2,
GPT Image 1.5) a partir dos dados estruturados do NPC no Postgres.

Usa a técnica de Âncora de Identidade (Pesquisa 2):
  1. Bloco IMUTÁVEL: descricao_ancora_en (geometria facial, cor olhos, marcas)
  2. Bloco de VARIAÇÃO: delta da versão (idade, ferimento, contexto)
  3. Bloco de ESTILO CANÔNICO: ALDERYN_STYLE_BLOCK (paleta, iluminação, framing)

Templates separados por modelo porque cada um responde melhor a estruturas diferentes:
  - FLUX:   prompt direto e curto (sem reescrita interna)
  - Gemini: linguagem natural com referências de câmera/lente
  - GPT:    ultra-detalhado pra minimizar reescrita interna

Comentários em PT-BR. Output do prompt em EN (perda de qualidade ~10-20% se usar
PT pra termos técnicos — descoberta da Pesquisa 2).
"""

from __future__ import annotations

from dataclasses import dataclass
from jinja2 import Environment, BaseLoader

# =============================================================================
# 1) BLOCO DE ESTILO CANÔNICO DO ALDERYN
# =============================================================================
# Reutilizado em TODOS os prompts. Define a estética witcher-grey:
# fotorrealismo cinematográfico, paleta dessaturada, iluminação Tier 1.
# =============================================================================

ALDERYN_STYLE_BLOCK = {
    "palette": "desaturated palette: charcoal-grey, night-brown, warm amber accents only",
    "lighting_base": "low-key lighting, chiaroscuro contrast, minimal fill light",
    "mood": "cinematic photorealism, analog film grain, shallow depth of field",
    "framing": "3/4 body portrait, 2:3 aspect ratio",
}

# Limite seguro pra todos os modelos (FLUX trunca >2K via T5)
MAX_PROMPT_CHARS = 2000


# =============================================================================
# 2) DICIONÁRIO PT→EN — termos RPG hardcoded (sem custo, sem latência)
# =============================================================================
# Cobre vocabulário comum do banco. Termos não encontrados são mantidos como estão
# (a função traduzir() retorna o original). Se aparecer termo novo recorrente,
# adicione aqui em vez de chamar LLM tradutor.
# =============================================================================

PT_EN: dict[str, str] = {
    # === Raças ===
    "humano": "human", "humana": "human",
    "elfo": "elf", "elfa": "elf",
    "anao": "dwarf", "anã": "dwarf", "anão": "dwarf",
    "meio-elfo": "half-elf", "meia-elfa": "half-elf",
    "tiefling": "tiefling", "orc": "orc", "halfling": "halfling",

    # === Vocações Alderyn-native ===
    "guerreiro": "warrior", "guerreira": "warrior",
    "mago": "mage", "maga": "mage",
    "curandeiro": "healer", "curandeira": "healer",
    "ladrao": "rogue", "ladrão": "rogue", "ladra": "rogue",
    "paladino": "paladin", "paladina": "paladin",
    "bardo": "bard", "barda": "bard",
    "assassino": "assassin", "assassina": "assassin",
    "necromante": "necromancer",
    "pugilista": "bareknuckle fighter",
    "cirurgiao": "battlefield surgeon", "cirurgião": "battlefield surgeon",
    "sacerdote": "priest", "sacerdotisa": "priestess",
    "copiador": "scribe-archivist",
    "colossus": "armored colossus",
    "arcanista": "arcanist",
    "espiao": "spy", "espião": "spy",
    "sombra": "shadow operative",
    "ladrao_de_almas": "soul thief", "ladrão de almas": "soul thief",
    "danarino": "war dancer", "dançarino": "war dancer", "dançarina": "war dancer",
    "ladino arcano": "arcane rogue",
    "devorador de grimorios": "grimoire devourer",

    # === Aparência — descritores ===
    "cicatriz": "scar", "cicatrizes": "scars",
    "tatuagem": "tattoo", "tatuagens": "tattoos",
    "barba": "beard", "barbado": "bearded",
    "calvo": "bald", "careca": "bald",
    "cabelo longo": "long hair", "cabelo curto": "short hair",
    "cabelo branco": "white hair", "cabelo grisalho": "grizzled hair",
    "cabelo preto": "black hair", "cabelo loiro": "blond hair",
    "olhos verdes": "green eyes", "olhos azuis": "blue eyes",
    "olhos castanhos": "brown eyes", "olhos cinza-azuis": "grey-blue eyes",
    "olhos vermelhos": "red eyes", "olhos amber": "amber eyes",
    "pele palida": "pale skin", "pele pálida": "pale skin",
    "pele oliva": "olive skin", "pele escura": "dark skin", "pele clara": "fair skin",
    "magro": "lean", "magra": "lean",
    "musculoso": "muscular", "robusto": "stocky",
    "alto": "tall", "baixo": "short",
    "queimadura": "burn scar",
    "calejadas": "calloused", "calejada": "calloused", "calejado": "calloused",

    # === Vestimenta ===
    "armadura pesada": "heavy plate armor",
    "armadura de couro": "leather armor",
    "robe": "flowing robes", "manto": "hooded cloak",
    "capa": "cloak", "tunica": "tunic", "túnica": "tunic",
    "avental": "apron", "avental de couro": "leather apron",
    "casaco": "coat", "casaco escuro": "dark coat",
    "botas": "boots", "botas de couro": "leather boots",
    "linho": "linen", "lã": "wool", "couro": "leather",

    # === Ambientes ===
    "floresta": "dark forest", "cripta": "underground crypt",
    "castelo": "ancient castle", "taverna": "dimly lit tavern",
    "ruinas": "crumbling ruins", "ruínas": "crumbling ruins",
    "trono": "throne room", "cozinha": "rustic kitchen",
    "porto": "stormy port", "doca": "weathered dock",
    "cidade velha": "old town quarter", "praça": "stone plaza",
    "catedral": "cathedral interior", "mosteiro": "monastery cloister",

    # === Mood / expressão ===
    "sombrio": "brooding", "sombria": "brooding",
    "ameacador": "menacing", "ameaçador": "menacing",
    "sereno": "serene", "serena": "serene",
    "misterioso": "enigmatic", "misteriosa": "enigmatic",
    "furioso": "wrathful", "furiosa": "wrathful",
    "cansado": "weary", "cansada": "weary",
    "vigilante": "watchful", "calmo": "calm", "calma": "calm",
}


def traduzir(termo: str) -> str:
    """Traduz um termo PT→EN. Retorna o original se não encontrar.

    Não-destrutivo: termo desconhecido passa intacto, evitando perder informação.
    """
    if not termo:
        return ""
    return PT_EN.get(termo.lower().strip(), termo)


def traduzir_lista(termos: list[str] | None, limite: int = 5) -> list[str]:
    """Traduz lista de termos, limitando ao top-N pra evitar diluição de tokens."""
    if not termos:
        return []
    return [traduzir(t) for t in termos[:limite] if t and t.strip()]


# =============================================================================
# 3) TEMPLATES JINJA2 — um por modelo
# =============================================================================
# Cada template usa a âncora de identidade (descricao_ancora_en) como bloco
# imutável + delta de variação opcional + bloco de estilo Alderyn.
#
# Diferenças entre templates:
#   FLUX:   curto, direto, sem prefixo (modelo respeita prompt literalmente)
#   Gemini: natural, com referência fotográfica (responde bem a câmera/lente)
#   GPT:    detalhado + prefixo "AS-IS" pra minimizar reescrita interna
# =============================================================================

# --- FLUX Kontext: prompt curto e direto ---
TEMPLATE_FLUX = """\
{{ ancora_en }} \
{% if variacao_modificacao %}{{ variacao_modificacao }}. {% endif %}\
{% if cenario %}Setting: {{ cenario }}. {% endif %}\
{% if iluminacao %}Lighting: {{ iluminacao }}. {% endif %}\
{{ palette }}. {{ lighting_base }}. {{ mood }}. {{ framing }}.\
"""

# --- Gemini Nano Banana 2: natural com câmera/lente ---
TEMPLATE_GEMINI = """\
Photorealistic cinematic portrait photograph of {{ ancora_en }} \
{% if variacao_modificacao %}This variation shows: {{ variacao_modificacao }}. {% endif %}\
{% if cenario %}The scene takes place in {{ cenario }}. {% endif %}\
Shot on Canon EOS R5 with 85mm f/1.4 lens, {{ framing }}. \
{% if iluminacao %}{{ iluminacao }}. {% else %}{{ lighting_base }}. {% endif %}\
{{ palette }}. {{ mood }}. \
Background softly blurred into darkness.\
"""

# --- GPT Image 1.5: ultra-detalhado, prefixo AS-IS pra minimizar reescrita ---
TEMPLATE_GPT = """\
I NEED to test how the tool works with extremely simple prompts. \
DO NOT add any detail, just use it AS-IS:

"{{ framing }} of {{ ancora_en }} \
{% if variacao_modificacao %}{{ variacao_modificacao }}. {% endif %}\
{% if cenario %}Located in {{ cenario }}. {% endif %}\
Illuminated by {% if iluminacao %}{{ iluminacao }}{% else %}{{ lighting_base }}{% endif %}. \
{{ palette }} — no bright or saturated colors, no beauty filter. \
{{ mood }}."\
"""

# Compila uma vez no import
_env = Environment(loader=BaseLoader())
_templates = {
    "flux_kontext": _env.from_string(TEMPLATE_FLUX),
    "gemini_nano":  _env.from_string(TEMPLATE_GEMINI),
    "gpt_image":    _env.from_string(TEMPLATE_GPT),
}

ModeloIA = str  # "flux_kontext" | "gemini_nano" | "gpt_image"


# =============================================================================
# 4) FUNÇÃO PRINCIPAL — montar_prompt_completo()
# =============================================================================

@dataclass
class DadosPromptNPC:
    """Snapshot dos dados do NPC necessários pra montar o prompt.

    Espelha colunas relevantes da tabela `npcs` do banco.
    Use a função `de_dict_npc()` pra construir a partir do row do Postgres.
    """
    descricao_ancora_en: str       # bloco imutável de identidade (EN)
    descricao_ancora_pt: str = ""  # versão PT-BR (fallback se EN faltar)
    iluminacao_tematica: str = ""  # campo do banco
    wardrobe_padrao: str = ""      # campo do banco
    cenario_padrao: str = ""       # opcional


def de_dict_npc(row: dict) -> DadosPromptNPC:
    """Constrói DadosPromptNPC a partir de um dict (row do banco).

    Tolerante a campos faltantes — usa defaults.
    """
    return DadosPromptNPC(
        descricao_ancora_en=row.get("descricao_ancora_en", "") or "",
        descricao_ancora_pt=row.get("descricao_ancora_pt", "") or "",
        iluminacao_tematica=row.get("iluminacao_tematica", "") or "",
        wardrobe_padrao=row.get("wardrobe_padrao", "") or "",
        cenario_padrao=row.get("cenario_padrao", "") or "",
    )


def ancora_pt_para_en(texto_pt: str) -> str:
    """Tradução simples de uma âncora PT→EN aplicando o dicionário palavra-a-palavra.

    Útil quando descricao_ancora_en está vazio mas descricao_ancora_pt existe.
    NÃO substitui tradução manual de qualidade — é fallback básico.
    """
    if not texto_pt:
        return ""
    palavras = texto_pt.split()
    traduzidas = [traduzir(p.rstrip(".,;:!?")) for p in palavras]
    return " ".join(traduzidas)


def montar_prompt_completo(
    dados: DadosPromptNPC | dict,
    modelo: ModeloIA,
    rotulo_variacao: str = "",
    descricao_modificacao: str = "",
    cenario_override: str = "",
    iluminacao_override: str = "",
) -> str:
    """Monta prompt completo pra um modelo específico.

    Args:
        dados: DadosPromptNPC ou dict-like com os campos do NPC.
        modelo: 'flux_kontext' | 'gemini_nano' | 'gpt_image'.
        rotulo_variacao: rótulo curto da variação (ex: "aposentado").
        descricao_modificacao: delta da variação (ex: "+6 anos, mais cabelo branco").
        cenario_override: substitui cenario_padrao se fornecido.
        iluminacao_override: substitui iluminacao_tematica se fornecido.

    Returns:
        Prompt em inglês pronto pra enviar à API.

    Raises:
        ValueError: se modelo não reconhecido ou âncora vazia.
    """
    if modelo not in _templates:
        raise ValueError(f"Modelo '{modelo}' inválido. Use: {list(_templates.keys())}")

    # Aceita dict ou dataclass
    if isinstance(dados, dict):
        dados = de_dict_npc(dados)

    # Resolve âncora EN — fallback pra tradução automática se EN vazio
    ancora = dados.descricao_ancora_en
    if not ancora and dados.descricao_ancora_pt:
        ancora = ancora_pt_para_en(dados.descricao_ancora_pt)
    if not ancora:
        raise ValueError(
            "NPC sem âncora de identidade (descricao_ancora_en e descricao_ancora_pt vazios). "
            "Preencha ao menos uma antes de gerar prompt."
        )

    # Resolve cenário e iluminação (override > campo do NPC)
    cenario = cenario_override or dados.cenario_padrao
    iluminacao = iluminacao_override or dados.iluminacao_tematica

    # Traduz cenário e iluminação se forem PT (assumindo PT-BR no banco)
    cenario_en = traduzir(cenario) if cenario else ""
    iluminacao_en = traduzir(iluminacao) if iluminacao else ""

    contexto = {
        "ancora_en":              ancora.strip(),
        "variacao_modificacao":   descricao_modificacao.strip(),
        "cenario":                cenario_en.strip(),
        "iluminacao":             iluminacao_en.strip(),
        "palette":                ALDERYN_STYLE_BLOCK["palette"],
        "lighting_base":          ALDERYN_STYLE_BLOCK["lighting_base"],
        "mood":                   ALDERYN_STYLE_BLOCK["mood"],
        "framing":                ALDERYN_STYLE_BLOCK["framing"],
    }

    template = _templates[modelo]
    prompt = template.render(**contexto).strip()

    # Normaliza whitespace (Jinja deixa espaços extras quando blocos opcionais somem)
    prompt = " ".join(prompt.split())

    # Trunca se exceder limite de tokens (segurança)
    if len(prompt) > MAX_PROMPT_CHARS:
        # Estratégia: remove cenário e iluminação opcionais
        contexto["cenario"] = ""
        contexto["iluminacao"] = ALDERYN_STYLE_BLOCK["lighting_base"]
        prompt = template.render(**contexto).strip()
        prompt = " ".join(prompt.split())
        # Se ainda passar, trunca brutalmente
        if len(prompt) > MAX_PROMPT_CHARS:
            prompt = prompt[:MAX_PROMPT_CHARS - 3] + "..."

    return prompt


# =============================================================================
# 5) CLI / smoke test rápido (executar com `python gerador_prompt_imagem.py`)
# =============================================================================

if __name__ == "__main__":
    # Exemplo do Almareth (id=33) — dados que estão no banco após migration 4.6
    almareth = DadosPromptNPC(
        descricao_ancora_en=(
            "64-year-old human man, face deeply lined by decades of kitchen work, "
            "calloused hands, tired but attentive brown eyes, short grizzled beard, "
            "thinning hair on top. Lean build, slightly stooped cook's posture. "
            "Worn leather apron stained with grease over rough linen tunic. "
            "Burn scar on right forearm. DOES NOT HAVE: visible tattoos, rings, marked accent."
        ),
        iluminacao_tematica="luz amber lateral de fogão a lenha, brasa fora de quadro, sombras profundas",
        wardrobe_padrao="avental de couro envelhecido manchado de gordura",
        cenario_padrao="cozinha",
    )

    for modelo in ("flux_kontext", "gemini_nano", "gpt_image"):
        print(f"\n{'=' * 70}")
        print(f"MODELO: {modelo}")
        print('=' * 70)
        prompt = montar_prompt_completo(almareth, modelo)
        print(prompt)
        print(f"\n[tamanho: {len(prompt)} chars]")
