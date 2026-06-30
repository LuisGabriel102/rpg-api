"""
classificar_criaturas.py — FASE 1 (classificacao mecanica) das criaturas
importadas de D&D que viram criaturas de Alderyn.

READ-ONLY. So faz SELECT em ref_criaturas e gera um CSV de SUGESTOES
(classificacao_sugerida.csv). NAO escreve no banco. Gabriel revisa o CSV
e aplica via SQL depois.

Rodar (da raiz do projeto, com o venv):
    python classificar_criaturas.py

Reusa a conexao existente (db.py -> DATABASE_URL do .env, asyncpg/Neon).
Nenhuma credencial e hardcoded aqui.

--- COMO O dados_json FOI LIDO (decidido por peek read-only) ---
O dados_json e um JSONB com chaves: acoes, acoes_lendarias, acoes_bonus,
reacoes, tracos. Cada uma e uma lista de {nome, descricao}. O texto e
majoritariamente ingles (texto D&D original).
- legendary_actions  -> ESTRUTURADO: chave 'acoes_lendarias' presente e nao-vazia.
- lair/spellcasting/ranged/stealth/pack/subtipo devil -> TEXTO SOLTO dentro
  de nome/descricao. Por isso o match e feito num BLOB lowercase achatado de
  todo o texto das 5 listas (substring / word-boundary), nao em chave.
Linhas com dados_json vazio ({}) caem no branch default (sem enriquecimento).
"""

import asyncio
import csv
import re
import sys
from collections import Counter
from decimal import Decimal

from sqlalchemy import text

from db import get_session, engine

CSV_PATH = "classificacao_sugerida.csv"

# Listas internas do dados_json onde mora o texto (nome + descricao).
LISTAS_JSON = ("acoes", "acoes_lendarias", "acoes_bonus", "reacoes", "tracos")

# ------------------------------------------------------------------ #
# Conjuntos de keywords (tudo testado contra o BLOB lowercase).
# Substring simples, exceto onde uso regex de fronteira (range/devil).
# ------------------------------------------------------------------ #
KW_DEVIL = ("devil", "diabo", "nine hells", "infernal", "baatezu")
KW_NECRO = ("necro", "undead", "morto-vivo", "morta-viva")
KW_CORRUPT = ("corrupt", "cursed", "blight", "rot", "putrid")
KW_MAGIC = ("magic", "magical", "arcane", "enchant", "awakened", "desperto")
KW_AWAKENED = ("awakened", "desperto", "sentient")
KW_ABERRANT = ("aberr", "far realm", "alien", "psionic")
KW_ARCHFEY = ("archfey", "ancient", "hag", "primordial fey")

KW_LAIR = ("lair", "covil")
KW_LEADER = ("summon", "invoca", "conjura", "command", "comando", "buff",
             "bless", "rally", "inspir", "heal", "cura ", "ally", "allies",
             "aliado", "reinforce")
KW_SPELL = ("spellcasting", "innate spell", "spellcaster", "spell save",
            "cantrip", "truque")
KW_STEALTH = ("stealth", "furtiv", "hide ", "ambush", "emboscada", "sneak",
              "skulk")
KW_PACK = ("pack tactics", "matilha", "swarm", "enxame", "in a group",
           "in groups")

# regex de fronteira: "range"/"ranged" sem casar strange/orange/arrange
RE_RANGED = re.compile(r"\brange[d ]")

# Lista iconica (casar contra `nome`, ingles, whole-word/phrase).
LISTA_ICONICA = [
    "Beholder", "Mind Flayer", "Illithid", "Elder Brain", "Displacer Beast",
    "Owlbear", "Rust Monster", "Gelatinous Cube", "Mimic", "Carrion Crawler",
    "Bulette", "Tarrasque", "Modron", "Slaad", "Githyanki", "Githzerai",
    "Flumph", "Intellect Devourer", "Umber Hulk", "Hook Horror", "Roper",
    "Piercer", "Cloaker", "Grell",
]
RE_ICONICA = [
    (nome, re.compile(r"\b" + re.escape(nome.lower()) + r"\b"))
    for nome in LISTA_ICONICA
]


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #
def montar_blob(dados_json) -> str:
    """Achata todo o texto (nome + descricao) das listas do dados_json num
    unico blob lowercase. Robusto a dict vazio, None, ou string JSON."""
    if not dados_json:
        return ""
    if isinstance(dados_json, str):
        import json
        try:
            dados_json = json.loads(dados_json)
        except Exception:
            return dados_json.lower()
    if not isinstance(dados_json, dict):
        return ""
    partes = []
    for chave in LISTAS_JSON:
        itens = dados_json.get(chave) or []
        if isinstance(itens, list):
            for item in itens:
                if isinstance(item, dict):
                    partes.append(str(item.get("nome", "")))
                    partes.append(str(item.get("descricao", "")))
                elif isinstance(item, str):
                    partes.append(item)
    return " ".join(partes).lower()


def tem_legendary(dados_json) -> bool:
    """Chave estruturada acoes_lendarias presente e nao-vazia."""
    if isinstance(dados_json, dict):
        return bool(dados_json.get("acoes_lendarias"))
    return False


def any_kw(blob: str, kws) -> bool:
    return any(k in blob for k in kws)


def to_float(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        return float(v)
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def to_int(v, default: int = 0) -> int:
    if v is None:
        return default
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def fmt_cr(cr_f: float) -> str:
    return ("%g" % cr_f)


# ------------------------------------------------------------------ #
# Regras
# ------------------------------------------------------------------ #
def decidir_origem(tipo: str, blob: str):
    """Retorna (origem, confianca, motivo, enriquecido).

    enriquecido = a decisao de origem veio de um keyword do dados_json
    (so faz sentido nos tipos condicionais de media/baixa confianca).
    Para os tipos 'alta' (deterministicos por tipo), enriquecido = None.
    humanoide retorna origem "" (e NPC, sem origem)."""
    if tipo == "besta":
        return "Natural", "alta", "tipo besta → Natural", None
    if tipo == "gigante":
        return "Natural", "alta", "tipo gigante → Natural", None
    if tipo == "elemental":
        return "Ressonante", "alta", "tipo elemental → Ressonante", None
    if tipo == "morto-vivo":
        return "Cicatricial", "alta", "tipo morto-vivo → Cicatricial", None
    if tipo == "celestial":
        return "Cicatricial", "alta", "tipo celestial → Cicatricial", None
    if tipo == "aberração":
        return "Marginal", "alta", "tipo aberração → Marginal", None
    if tipo == "humanoide":
        return "", "alta", "humanoide → NPC (sem origem)", None

    if tipo == "demônio":
        if any_kw(blob, KW_DEVIL):
            return "Marginal", "media", "demônio devil/diabo → Marginal", True
        return "Corrompida", "media", "demônio (sem devil) → Corrompida", False

    if tipo == "constructo":
        if any_kw(blob, KW_NECRO):
            return "Cicatricial", "media", "constructo necromancy/undead → Cicatricial", True
        return "Ressonante", "media", "constructo (default) → Ressonante", False

    if tipo == "planta":
        if any_kw(blob, ("necro",) + KW_CORRUPT):
            return "Corrompida", "media", "planta necrotic/corrupted → Corrompida", True
        if any_kw(blob, KW_MAGIC + KW_AWAKENED):
            return "Ressonante", "media", "planta magic/awakened → Ressonante", True
        if any_kw(blob, KW_ABERRANT):
            return "Marginal", "media", "planta aberrant → Marginal", True
        return "Natural", "media", "planta (default) → Natural", False

    if tipo in ("gosma", "geleia"):
        if any_kw(blob, KW_MAGIC):
            return "Ressonante", "media", f"{tipo} magic → Ressonante", True
        if any_kw(blob, KW_CORRUPT):
            return "Corrompida", "media", f"{tipo} corrupted → Corrompida", True
        return "Natural", "media", f"{tipo} (default) → Natural", False

    if tipo == "monstruosidade":
        if any_kw(blob, KW_MAGIC):
            return "Ressonante", "baixa", "monstruosidade magic → Ressonante", True
        if any_kw(blob, KW_ABERRANT):
            return "Marginal", "baixa", "monstruosidade far realm/aberrant → Marginal", True
        if any_kw(blob, KW_CORRUPT):
            return "Corrompida", "baixa", "monstruosidade corrupted/cursed → Corrompida", True
        return "Natural", "baixa", "monstruosidade (default) → Natural", False

    if tipo == "fada":
        if any_kw(blob, KW_ARCHFEY):
            return "Marginal", "baixa", "fada archfey/ancient/hag → Marginal", True
        return "Natural", "baixa", "fada (default) → Natural", False

    # Defensivo: tipo fora do mapa do brief (nao deve ocorrer no recorte).
    return "Natural", "baixa", f"tipo '{tipo}' nao mapeado → Natural (default)", False


def decidir_andar(origem: str, tipo: str) -> str:
    if origem in ("Natural", "Ressonante", "Corrompida"):
        return "Superfície"
    if origem == "Cicatricial":
        if tipo == "morto-vivo":
            return "Eco"
        if tipo == "celestial":
            return "Clarão"
        return "Eco"  # Cicatricial de outra origem (ex: constructo necro) -> piso Eco
    if origem == "Marginal":
        if tipo == "fada":
            return "Antigo"
        # aberração, demônio devil, planta/monstruosidade aberrant -> Margem
        return "Margem"
    return ""  # sem origem (humanoide)


def decidir_arquetipo(cr_f, blob, dados_json, intel, dex, forca, hp):
    """Primeira condicao que bate vence."""
    legendary = tem_legendary(dados_json)
    lair = any_kw(blob, KW_LAIR)
    if cr_f >= 10 and (legendary or lair):
        return "Boss"
    if intel >= 13 and any_kw(blob, KW_LEADER):
        return "Leader"
    if hp < 30 and any_kw(blob, KW_PACK):
        return "Swarm"
    if intel >= 10 and (any_kw(blob, KW_SPELL) or RE_RANGED.search(blob)):
        return "Tactical"
    if dex > forca and any_kw(blob, KW_STEALTH):
        return "Predator"
    return "Brute"


def decidir_perigo(cr_f) -> str:
    if cr_f < 3:
        return "Ambiente"   # CR 0-2
    if cr_f < 7:
        return "Ameaça"     # CR 3-6
    return "Letal"          # CR 7+


def casa_iconica(nome: str):
    if not nome:
        return None
    n = nome.lower()
    for canonico, rx in RE_ICONICA:
        if rx.search(n):
            return canonico
    return None


def decidir_tratamento(tipo: str, nome: str):
    """Retorna (tratamento, humanoid_npc_sugerido)."""
    if tipo == "humanoide":
        return "reclassificacao_npc", True
    if casa_iconica(nome):
        return "substituicao_original", False
    return "renomeacao_profunda", False


# ------------------------------------------------------------------ #
# Main
# ------------------------------------------------------------------ #
async def main() -> None:
    sql = text("""
        SELECT id, nome, nome_ptbr, tipo, cr, hp_medio,
               forca, destreza, constituicao, inteligencia, sabedoria,
               carisma, dados_json
        FROM ref_criaturas
        WHERE merged_into IS NULL
          AND status_conversao = 'pendente'
          AND origem IS NULL
          AND tipo <> 'dragão'
        ORDER BY id
    """)

    async with get_session() as session:
        result = await session.execute(sql)
        rows = result.mappings().all()

    saida = []
    cont_origem = Counter()
    cont_confianca = Counter()
    cont_tratamento = Counter()
    cont_arquetipo = Counter()
    cont_perigo = Counter()
    # enriquecido: so conta os tipos condicionais (media/baixa). True/False.
    enriq_sim = 0
    enriq_nao = 0
    tipos_condicionais = {"demônio", "constructo", "planta", "gosma",
                          "geleia", "monstruosidade", "fada"}

    for r in rows:
        tipo = r["tipo"]
        nome = r["nome"] or ""
        dj = r["dados_json"]
        blob = montar_blob(dj)

        cr_f = to_float(r["cr"])
        hp = to_int(r["hp_medio"], default=999)  # None -> nao dispara Swarm
        intel = to_int(r["inteligencia"], default=0)
        dex = to_int(r["destreza"], default=0)
        forca = to_int(r["forca"], default=0)

        origem, confianca, motivo, enriquecido = decidir_origem(tipo, blob)
        andar = decidir_andar(origem, tipo)
        arquetipo = decidir_arquetipo(cr_f, blob, dj, intel, dex, forca, hp)
        perigo = decidir_perigo(cr_f)
        tratamento, humanoid_npc = decidir_tratamento(tipo, nome)
        morale_immune = tipo in ("morto-vivo", "constructo", "elemental")

        saida.append({
            "id": r["id"],
            "nome": nome,
            "nome_ptbr": r["nome_ptbr"] or "",
            "tipo": tipo,
            "cr": fmt_cr(cr_f),
            "origem_sugerida": origem,
            "andar_sugerido": andar,
            "arquetipo_sugerido": arquetipo,
            "perigo_sugerido": perigo,
            "tratamento_sugerido": tratamento,
            "humanoid_npc_sugerido": "true" if humanoid_npc else "false",
            "morale_immune_sugerido": "true" if morale_immune else "false",
            "confianca": confianca,
            "motivo": motivo,
        })

        cont_origem[origem or "(sem origem / NPC)"] += 1
        cont_confianca[confianca] += 1
        cont_tratamento[tratamento] += 1
        cont_arquetipo[arquetipo] += 1
        cont_perigo[perigo] += 1
        if tipo in tipos_condicionais:
            if enriquecido:
                enriq_sim += 1
            else:
                enriq_nao += 1

    # ----- escreve CSV (UTF-8 SEM BOM) -----
    campos = ["id", "nome", "nome_ptbr", "tipo", "cr", "origem_sugerida",
              "andar_sugerido", "arquetipo_sugerido", "perigo_sugerido",
              "tratamento_sugerido", "humanoid_npc_sugerido",
              "morale_immune_sugerido", "confianca", "motivo"]
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(saida)

    # ----- resumo no stdout -----
    print("=" * 64)
    print("CLASSIFICACAO DE CRIATURAS — FASE 1 (read-only, sugestoes)")
    print("=" * 64)
    print(f"Total de linhas processadas: {len(saida)}")
    print(f"CSV gerado: {CSV_PATH} (UTF-8 sem BOM)")

    def bloco(titulo, counter, ordem=None):
        print(f"\n{titulo}:")
        itens = ([(k, counter[k]) for k in ordem if k in counter]
                 if ordem else counter.most_common())
        for k, v in itens:
            print(f"  {str(k):24s} {v}")

    bloco("Por origem_sugerida", cont_origem)
    bloco("Por confianca", cont_confianca, ordem=["alta", "media", "baixa"])
    bloco("Por tratamento_sugerido", cont_tratamento)
    bloco("Por arquetipo_sugerido", cont_arquetipo,
          ordem=["Boss", "Leader", "Swarm", "Tactical", "Predator", "Brute"])
    bloco("Por perigo_sugerido", cont_perigo,
          ordem=["Ambiente", "Ameaça", "Letal"])

    n_cond = enriq_sim + enriq_nao
    print("\nEnriquecimento via dados_json (somente tipos condicionais "
          "media/baixa):")
    print(f"  tipos condicionais avaliados: {n_cond}")
    print(f"  enriquecidos (keyword virou decisao concreta): {enriq_sim}")
    print(f"  cairam no default/senão: {enriq_nao}")
    if n_cond:
        pct = 100.0 * enriq_sim / n_cond
        print(f"  taxa de enriquecimento: {pct:.1f}%")
    print("\n(Os tipos 'alta' sao deterministicos por tipo — nao dependem "
          "de enriquecimento.)")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
