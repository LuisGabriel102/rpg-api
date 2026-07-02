"""
Central de Admin do Alderyn — Aba NPCs (Onda 1).

VISAO_central_admin_alderyn_v1 (Aba 1) + SPEC_gravura_imagem_mae_admin_npcs_v1 (Fase 4).

Rotas (registradas em oficina_app.py, mesmo padrao do Atelie):
  /oficina/admin/npcs            -> lista: miniatura + nome + bolinha de status
                                    (verde = tem imagem-mae / vermelho = sem retrato)
  /oficina/admin/npcs/{npc_id}   -> detalhe: mae grande + ancora (read-only) +
                                    galeria de candidatas + Subir imagem +
                                    Definir como mae

Decisoes travadas (Gabriel, Onda 1; upload atualizado no Bloco 2 da migracao):
- Upload de qualquer imagem e caminho de PRIMEIRA CLASSE (decisao 5 da SPEC):
  arquivo -> BYTES em npc_imagens.imagem_bytes (Bloco 2; antes era R2) ->
  linha status='candidata' com url='/npc-imagem/<id>' (rota do Bloco 1) ->
  so vira mae pelo botao "Definir como mae".
- "Definir como mae" ESCREVE direto no banco, blindado em codigo (shape aprovado):
  pre-check FOR UPDATE + rebaixa a canonica antiga pra 'arquivada' + promove +
  sincroniza npcs.imagem_url + post-check, tudo NUMA transacao. O indice unico
  parcial (1 canonica por npc — uq_npc_imagens_uma_canonica, ja vivo no banco)
  e a trava dura; o post-check da o erro amigavel na UI.
- Vocabulario da SPEC ('candidata'/'arquivada'): EXIGE o CHECK de
  npc_imagens.status atualizado (ALTER do Gabriel no pgAdmin) — sem o ALTER, o
  INSERT do upload falha com CheckViolation (erro visivel na UI, nada corrompe).
- Ordenacao da lista: ALFABETICA (ajuste 3 — o alvo da onda e a Elara, que e
  verde; vermelhos-no-topo fica pra Onda 2). Busca por nome a mao.
- SEM geracao de imagem nesta onda (fal/img2img e Onda 2; quando chegar:
  FLUX.1 dev -> fal-ai/flux-lora*, NUNCA FLUX.2). O jogo segue leitura pura.

Padrao de banco: asyncpg direto, espelho de pages/atelie_queries.py.
r2_storage NAO e mais chamado neste modulo (Bloco 2); o R2 legado segue
legivel pelas urls antigas ate o Bloco 3 migrar as imagens existentes.
"""

from __future__ import annotations

import os
import re
import traceback
import unicodedata
from typing import Optional

import asyncpg
from nicegui import ui

from ui_helpers import aguardar_conexao_websocket


# =============================================================================
# CONSTANTES + HELPERS PUROS (testaveis sem banco/UI)
# =============================================================================

_TIPOS_ACEITOS = {"image/jpeg", "image/png", "image/webp"}
_MAX_UPLOAD_MB = 10

# bolinha de status da lista: (cor, rotulo acessivel)
_DOT_VERDE = ("#22c55e", "tem imagem-mãe")
_DOT_VERMELHO = ("#ef4444", "sem retrato")

# rotulos PT (com acento) dos campos curtos da ancora — os DADOS ja vem do banco
# com acento; isto so conserta os labels hardcoded (polimento Onda 1, item 4).
_ROTULOS_ANCORA = {
    "rosto": "rosto",
    "olhos": "olhos",
    "cabelo": "cabelo",
    "pele": "pele",
    "wardrobe_padrao": "vestuário padrão",
    "iluminacao_tematica": "iluminação temática",
}

# ── paleta do dossiê (Onda 1): base marrom/âmbar; cor viva SÓ no tipo de
# vínculo e no status vivo/morto. Witcher-grey: nada de neon. ──
_DOURADO = "#c9a45c"   # títulos e ícones de destaque
_BRONZE = "#b8823c"    # molduras
_CHIP_BG = "rgba(166,124,61,0.15)"
_CHIP_FG = "#cbb087"
_LINK = "#bd9a52"      # reservado pra links do dossiê (ondas futuras)

# tipo de vínculo -> cor (chave = valor CRU do banco, sem acento; os 13
# DISTINCT confirmados em 2026-07-02). Witcher-grey, sem neon. Tipo futuro
# fora da lista cai no fallback sem quebrar.
_COR_TIPO_VINCULO = {
    "amor": "#d15b74",
    "amizade": "#6bb06b",
    "lealdade": "#c9a45c",
    "protecao": "#5aa39a",
    "mentoria": "#7fa86b",
    "familiar": "#6b93c4",
    "respeito": "#8a93b0",
    "divida": "#a08a5e",
    "manipulacao": "#a678d4",
    "rivalidade": "#d98a4a",
    "inimizade": "#c25a4a",
    "medo": "#8a6db0",
    "neutro": "#8a8a8a",
}
_COR_TIPO_FALLBACK = "#b8934a"

# tipo cru -> rótulo PT da pill (só 3 precisam de acento; os outros 10 já são
# palavras corretas). A COR continua vindo do tipo cru.
_ROTULO_TIPO_VINCULO = {
    "manipulacao": "manipulação",
    "protecao": "proteção",
    "divida": "dívida",
}

# stopwords da chave de dedupe dos chips (regra fechada pelo Op em 2026-07-02:
# lower, sem acento, sem pontuação, sem a/de/da/do)
_CHIP_STOPWORDS = {"a", "de", "da", "do"}
_COR_VIVO = "#6bb06b"
_COR_MORTO = "#8a8a8a"

# grau_parentesco cru do banco -> rótulo legível (fallback = valor cru;
# mae_filho resolve por sexo em _rotulo_parentesco)
_GRAU_PARENTESCO = {
    "filho_mae": "mãe",
    "filho_pai": "pai",
    "conjuges": "cônjuge",
    "irmaos": "irmão(ã)",
}

# "Ver perfil completo": rótulo PT -> coluna de npcs (nomes confirmados no
# information_schema; campo vazio não renderiza)
_CAMPOS_PERFIL = (
    ("medo principal", "medo_principal"),
    ("desejo oculto", "desejo_oculto"),
    ("linha que não cruza", "linha_que_nao_cruza"),
    ("maior arrependimento", "maior_arrependimento"),
    ("estilo de fala", "estilo_de_fala"),
    ("tensão interna", "tensao_interna"),
)
_BIG_FIVE = (
    ("abertura", "abertura"),
    ("conscienciosidade", "conscienciosidade"),
    ("extroversão", "extroversao"),
    ("amabilidade", "amabilidade"),
    ("neuroticismo", "neuroticismo"),
)


def _dot_status(tem_mae: bool) -> tuple[str, str]:
    """PURO: bolinha da lista. Verde = existe linha canonica em npc_imagens;
    vermelho = nao existe. (Fonte de verdade e npc_imagens, nao npcs.imagem_url.)"""
    return _DOT_VERDE if tem_mae else _DOT_VERMELHO


def _validar_upload(content_type: Optional[str], tamanho_bytes: int) -> Optional[str]:
    """PURO: valida um upload ANTES de gastar banda com o R2.
    Retorna a mensagem de erro (str) ou None quando o arquivo passa."""
    if not content_type or content_type.lower() not in _TIPOS_ACEITOS:
        return f"Tipo não aceito ({content_type or 'desconhecido'}). Use JPG, PNG ou WEBP."
    if tamanho_bytes <= 0:
        return "Arquivo vazio."
    if tamanho_bytes > _MAX_UPLOAD_MB * 1024 * 1024:
        return f"Arquivo grande demais ({tamanho_bytes / (1024 * 1024):.1f} MB; teto {_MAX_UPLOAD_MB} MB)."
    return None


def _r2_key_da_url(url: str) -> str:
    """PURO: a key R2 e o caminho depois do dominio publico (mesma convencao do
    pipeline_geracao: tudo na raiz do bucket -> ultimo segmento)."""
    return (url or "").rsplit("/", 1)[-1]


def _legenda_mae(nome_npc: Optional[str], npc_id: int) -> str:
    """PURO: legenda da imagem-mãe — nome do NPC + status (decisão 2 do
    Bloco 2). Uniforme pra imagem do banco E do R2 (nada de id/arquivo cru)."""
    return f"{nome_npc or f'NPC #{npc_id}'} · canônica"


def _rotulo_parentesco(grau: Optional[str], sexo_parente: Optional[str] = None) -> str:
    """PURO: grau cru do banco -> rótulo legível. mae_filho resolve 'filho'/
    'filha' pelo sexo do parente quando existir; sem sexo fica 'filho(a)'
    (não inventa). Grau desconhecido volta cru."""
    g = (grau or "").strip().lower()
    if g == "mae_filho":
        sexo = (sexo_parente or "").strip().lower()
        if sexo == "masculino":
            return "filho"
        if sexo == "feminino":
            return "filha"
        return "filho(a)"
    return _GRAU_PARENTESCO.get(g, grau or "?")


def _cor_tipo_vinculo(tipo: Optional[str]) -> str:
    """PURO: cor viva do tipo de vínculo; tipo fora do mapa cai no fallback
    âmbar (não quebra)."""
    return _COR_TIPO_VINCULO.get((tipo or "").strip().lower(), _COR_TIPO_FALLBACK)


def _rotulo_tipo_vinculo(tipo: Optional[str]) -> str:
    """PURO: rótulo PT da pill. 3 tipos ganham acento (manipulação/proteção/
    dívida); os demais conhecidos já são palavras corretas e ficam como estão;
    tipo futuro fora do mapa volta capitalizado. NÃO toca o dado."""
    t = (tipo or "").strip().lower()
    if not t:
        return ""
    if t in _ROTULO_TIPO_VINCULO:
        return _ROTULO_TIPO_VINCULO[t]
    if t in _COR_TIPO_VINCULO:
        return t
    return t.capitalize()


def _normalizar_chip(texto: str) -> str:
    """PURO: chave de dedupe dos chips — lower, sem acento, sem pontuação,
    sem stopwords (a/de/da/do). 'A Cátedra, Namiri' e 'Cátedra de Namiri'
    colidem; 'Clã Varekhor' sobrevive."""
    s = unicodedata.normalize("NFKD", (texto or "").casefold())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^\w\s]", " ", s)
    palavras = [p for p in s.split() if p not in _CHIP_STOPWORDS]
    return " ".join(palavras)


def _cor_status_parente(status: Optional[str]) -> str:
    """PURO: vivo = verde; morto (ou status desconhecido/NULL) = cinza."""
    return _COR_VIVO if (status or "").strip().lower() == "vivo" else _COR_MORTO


def _intensidade_dominante(vinculo: dict) -> Optional[tuple[str, int]]:
    """PURO: (rótulo, valor) da maior intensidade não-NULL entre confiança/
    afeição/respeito/medo. As 4 NULL -> None (vínculo sem barra)."""
    pares = (
        ("confiança", vinculo.get("confianca")),
        ("afeição", vinculo.get("afeicao")),
        ("respeito", vinculo.get("respeito")),
        ("medo", vinculo.get("medo")),
    )
    validos = [(rotulo, valor) for rotulo, valor in pares if valor is not None]
    if not validos:
        return None
    return max(validos, key=lambda par: par[1])


def _subtitulo_familia(parentes: list[dict]) -> str:
    """PURO: 'N · todos vivos' ou a contagem real de vivos/mortos."""
    total = len(parentes)
    vivos = sum(
        1 for p in parentes
        if (p.get("status_parente") or "").strip().lower() == "vivo"
    )
    if vivos == total:
        return f"{total} · todos vivos"
    return f"{total} · {vivos} vivo(s), {total - vivos} morto(s)"


def _chips_identidade(npc: dict) -> list[str]:
    """PURO: chips do card 'Quem é' — só o que tem valor, sem quase-repetidos
    (dedupe por _normalizar_chip; identidade entra antes de facção, então o
    local vence a facção homônima)."""
    chips: list[str] = []
    vistos: set[str] = set()

    def _add(texto: str) -> None:
        chave = _normalizar_chip(texto)
        if chave and chave in vistos:
            return
        vistos.add(chave)
        chips.append(texto)

    if npc.get("raca"):
        _add(str(npc["raca"]))
    if npc.get("idade_aparente") is not None:
        _add(f"{npc['idade_aparente']} anos")
    if npc.get("localizacao_atual"):
        _add(str(npc["localizacao_atual"]))
    for faccao in (npc.get("facoes") or []):
        if faccao:
            _add(str(faccao))
    if npc.get("arc_phase"):
        _add(f"arco {npc['arc_phase']}")
    return chips


def _linhas_perfil(npc: dict) -> list[tuple[str, str]]:
    """PURO: linhas (rótulo, texto real) do 'Ver perfil completo'. Campo vazio
    não entra. idade_real e localizacao_base moram aqui (decisão 4)."""
    linhas = [(rotulo, str(npc[col])) for rotulo, col in _CAMPOS_PERFIL if npc.get(col)]
    big5 = [
        f"{rotulo} {npc[col]}" for rotulo, col in _BIG_FIVE
        if npc.get(col) is not None
    ]
    if big5:
        linhas.append(("Big Five", " · ".join(big5)))
    valores = [str(v) for v in (npc.get("valores") or []) if v]
    if valores:
        linhas.append(("valores", ", ".join(valores)))
    if npc.get("o_que_so_ele_pode_fazer"):
        linhas.append(("o que só ele(a) pode fazer", str(npc["o_que_so_ele_pode_fazer"])))
    if npc.get("idade_real") is not None:
        linhas.append(("idade real", f"{npc['idade_real']} anos"))
    if npc.get("localizacao_base"):
        linhas.append(("localização base", str(npc["localizacao_base"])))
    if npc.get("backstory_completa"):
        linhas.append(("backstory", str(npc["backstory_completa"])))
    return linhas


def _nome_outro_lado(vinculo: dict) -> str:
    """PURO: nome do outro lado do vínculo — npc (nome já resolvido no JOIN) >
    'Protagonista' (personagem_alvo_id) > '(sem alvo)' (alvo duplo-NULL não
    estoura a página)."""
    if vinculo.get("nome_outro"):
        return str(vinculo["nome_outro"])
    if vinculo.get("personagem_alvo_id") is not None:
        return "Protagonista"
    return "(sem alvo)"


def _consolidar_vinculos(vinculos: list[dict]) -> list[dict]:
    """PURO: linhas do card Vínculos. Par ida+volta com o MESMO tipo vira UMA
    linha sem direção (simétrico); tipos diferentes ficam em linhas separadas
    com 'dá'/'recebe' — witcher-grey: mostra os dois lados, não suaviza.
    Intensidade do par simétrico: a da perspectiva do NPC (origem), com
    fallback pra volta. Nota curta só no vínculo com o Protagonista
    (historia_com_protagonista — decisão 3)."""
    linhas: list[dict] = []
    consumidos: set[int] = set()
    for i, v in enumerate(vinculos):
        if i in consumidos:
            continue
        nome = _nome_outro_lado(v)
        par = None
        for j in range(i + 1, len(vinculos)):
            w = vinculos[j]
            if (j not in consumidos
                    and _nome_outro_lado(w) == nome
                    and bool(w.get("eh_origem")) != bool(v.get("eh_origem"))
                    and (w.get("tipo") or "") == (v.get("tipo") or "")):
                par = j
                break
        if par is not None:
            consumidos.add(par)
            w = vinculos[par]
            origem, volta = (v, w) if v.get("eh_origem") else (w, v)
            linhas.append({
                "nome": nome,
                "tipo": v.get("tipo"),
                "direcao": None,
                "intensidade": (_intensidade_dominante(origem)
                                or _intensidade_dominante(volta)),
                "nota": (origem.get("historia_com_protagonista")
                         if nome == "Protagonista" else None),
            })
        else:
            linhas.append({
                "nome": nome,
                "tipo": v.get("tipo"),
                "direcao": "dá" if v.get("eh_origem") else "recebe",
                "intensidade": _intensidade_dominante(v),
                "nota": (v.get("historia_com_protagonista")
                         if nome == "Protagonista" else None),
            })
    return linhas


# =============================================================================
# BANCO (asyncpg direto, espelho de atelie_queries)
# =============================================================================

async def _conectar() -> asyncpg.Connection:
    """Conecta ao Neon. Caller fecha (conn.close()). statement_cache_size=0
    obrigatorio com o pooler do Neon em transaction mode."""
    db_url = os.environ.get("DATABASE_URL", "").replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    if not db_url:
        raise RuntimeError("DATABASE_URL nao definida no .env")
    return await asyncpg.connect(db_url, statement_cache_size=0)


async def _listar_npcs_com_status(busca: str = "") -> list[dict]:
    """Lista pro grid: id, nome, miniatura (npcs.imagem_url) + tem_mae (EXISTS
    canonica em npc_imagens). Alfabetica (ajuste 3). Busca via ILIKE bind param."""
    conn = await _conectar()
    try:
        sql = (
            "SELECT n.id, n.nome, n.imagem_url, "
            "EXISTS (SELECT 1 FROM npc_imagens i "
            "        WHERE i.npc_id = n.id AND i.status = 'canonica') AS tem_mae "
            "FROM npcs n "
        )
        args: list = []
        if busca.strip():
            sql += "WHERE n.nome ILIKE $1 "
            args.append(f"%{busca.strip()}%")
        sql += "ORDER BY n.nome"
        rows = await conn.fetch(sql, *args)
        return [dict(r) for r in rows]
    finally:
        await conn.close()


async def _carregar_detalhe_npc(npc_id: int) -> Optional[dict]:
    """Detalhe: dados do NPC (ancora completa) + a canonica + a galeria de
    nao-canonicas (candidatas novas E legadas 'aprovada'/'rascunho' — qualquer
    uma pode virar mae; 'arquivada'/'aposentada' ficam visiveis como historico)."""
    conn = await _conectar()
    try:
        npc = await conn.fetchrow(
            "SELECT id, nome, imagem_url, rosto, olhos, cabelo, pele, "
            "       wardrobe_padrao, iluminacao_tematica, "
            "       descricao_ancora_pt, descricao_ancora_en, "
            # dossiê 'Quem é' (leitura pura; nomes do information_schema)
            "       raca, idade_aparente, idade_real, localizacao_atual, "
            "       localizacao_base, facoes, arc_phase, "
            "       medo_principal, desejo_oculto, linha_que_nao_cruza, "
            "       maior_arrependimento, estilo_de_fala, tensao_interna, "
            "       abertura, conscienciosidade, extroversao, amabilidade, "
            "       neuroticismo, valores, backstory_completa, "
            "       momento_de_singularidade, o_que_so_ele_pode_fazer "
            "FROM npcs WHERE id = $1",
            npc_id,
        )
        if npc is None:
            return None
        canonica = await conn.fetchrow(
            "SELECT id, url, rotulo_narrativo, modelo_ia, criado_em "
            "FROM npc_imagens WHERE npc_id = $1 AND status = 'canonica' "
            "ORDER BY criado_em DESC LIMIT 1",
            npc_id,
        )
        galeria = await conn.fetch(
            "SELECT id, url, rotulo_narrativo, status, modelo_ia, criado_em "
            "FROM npc_imagens WHERE npc_id = $1 AND status <> 'canonica' "
            "ORDER BY criado_em DESC",
            npc_id,
        )
        return {
            "npc": dict(npc),
            "canonica": dict(canonica) if canonica else None,
            "galeria": [dict(r) for r in galeria],
        }
    finally:
        await conn.close()


async def _carregar_familia(npc_id: int) -> list[dict]:
    """Parentes do NPC (papel, nome, vivo/morto). LEFT JOIN em npcs pelo
    parente_id SÓ pra resolver o sexo (rótulo 'filho'/'filha' exato —
    decisão 2). Leitura pura."""
    conn = await _conectar()
    try:
        rows = await conn.fetch(
            "SELECT f.parente_nome, f.grau_parentesco, f.status_parente, "
            "       p.sexo AS sexo_parente "
            "FROM npc_family f "
            "LEFT JOIN npcs p ON p.id = f.parente_id "
            "WHERE f.npc_id = $1 "
            "ORDER BY f.id",
            npc_id,
        )
        return [dict(r) for r in rows]
    finally:
        await conn.close()


async def _carregar_vinculos(npc_id: int) -> list[dict]:
    """Relações onde o NPC é origem OU alvo, com o nome do outro lado já
    resolvido via JOIN em npcs (nada de id cru na tela). personagem_alvo_id
    vira 'Protagonista' no helper puro. Leitura pura."""
    conn = await _conectar()
    try:
        rows = await conn.fetch(
            "SELECT r.tipo, r.confianca, r.afeicao, r.respeito, r.medo, "
            "       r.personagem_alvo_id, r.historia_com_protagonista, "
            "       (r.npc_origem_id = $1) AS eh_origem, "
            "       CASE WHEN r.npc_origem_id = $1 THEN alvo.nome "
            "            ELSE origem.nome END AS nome_outro "
            "FROM npc_relationships r "
            "LEFT JOIN npcs alvo   ON alvo.id = r.npc_alvo_id "
            "LEFT JOIN npcs origem ON origem.id = r.npc_origem_id "
            "WHERE r.npc_origem_id = $1 OR r.npc_alvo_id = $1 "
            "ORDER BY r.id",
            npc_id,
        )
        return [dict(r) for r in rows]
    finally:
        await conn.close()


async def _inserir_candidata_upload(
    npc_id: int, file_bytes: bytes, content_type: str, rotulo: Optional[str]
) -> int:
    """INSERT do upload como CANDIDATA — Bloco 2 da migracao storage: os BYTES
    vao pro banco (imagem_bytes/imagem_mime), nao mais pro R2. url e NOT NULL
    e a rota interna depende do id -> duas fases na MESMA transacao: INSERT
    com placeholder RETURNING id, depois UPDATE url='/npc-imagem/<id>'.
    Commit atomico. r2_key = NULL (upload no banco nao tem key R2)."""
    conn = await _conectar()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                "INSERT INTO npc_imagens "
                "  (npc_id, url, r2_key, rotulo_narrativo, status, modelo_ia, "
                "   e_principal, custo_usd, criado_em, imagem_bytes, imagem_mime) "
                "VALUES ($1, 'pendente', NULL, $2, 'candidata', 'upload', "
                "        FALSE, 0, NOW(), $3, $4) "
                "RETURNING id",
                npc_id, (rotulo or "Upload manual"), file_bytes,
                (content_type or "").lower(),
            )
            imagem_id: int = row["id"]
            await conn.execute(
                "UPDATE npc_imagens SET url = '/npc-imagem/' || id WHERE id = $1",
                imagem_id,
            )
        return imagem_id
    finally:
        await conn.close()


async def definir_como_mae(npc_id: int, imagem_id: int) -> str:
    """A transacao 'Definir como mae' — shape aprovado por Gabriel (Onda 1).

    NUMA transacao: pre-check FOR UPDATE -> rebaixa canonica antiga pra
    'arquivada' -> promove a escolhida -> sincroniza npcs.imagem_url ->
    post-check (1 canonica exata + ponteiro batendo). Qualquer violacao levanta
    ValueError com mensagem amigavel e a transacao REVERTE inteira. A trava
    dura contra 2 maes e o indice unico parcial do banco (independente daqui).

    Retorna a URL da nova mae (pro refresh da UI)."""
    conn = await _conectar()
    try:
        async with conn.transaction():
            # PRE-CHECK: a escolhida existe, e DESTE npc e ainda nao e a mae
            alvo = await conn.fetchrow(
                "SELECT id, url FROM npc_imagens "
                "WHERE id = $1 AND npc_id = $2 AND status <> 'canonica' "
                "FOR UPDATE",
                imagem_id, npc_id,
            )
            if alvo is None:
                raise ValueError(
                    "Imagem nao encontrada pra este NPC (ou ja e a imagem-mae)."
                )
            # 1) rebaixa a mae atual (0 linhas OK: NPC ainda sem mae)
            await conn.execute(
                "UPDATE npc_imagens SET status = 'arquivada', e_principal = FALSE "
                "WHERE npc_id = $1 AND status = 'canonica'",
                npc_id,
            )
            # 2) promove a escolhida
            await conn.execute(
                "UPDATE npc_imagens SET status = 'canonica', e_principal = TRUE "
                "WHERE id = $1 AND npc_id = $2",
                imagem_id, npc_id,
            )
            # 3) sincroniza o ponteiro rapido que o jogo le (gravura.url_imagem_mae)
            await conn.execute(
                "UPDATE npcs SET imagem_url = $1 WHERE id = $2",
                alvo["url"], npc_id,
            )
            # POST-CHECK: exatamente UMA canonica e o ponteiro batendo
            n_can = await conn.fetchval(
                "SELECT COUNT(*) FROM npc_imagens "
                "WHERE npc_id = $1 AND status = 'canonica'",
                npc_id,
            )
            if n_can != 1:
                raise ValueError(
                    f"Post-check falhou: {n_can} canonicas (esperado 1). Nada foi gravado."
                )
            ptr = await conn.fetchval(
                "SELECT imagem_url FROM npcs WHERE id = $1", npc_id
            )
            if ptr != alvo["url"]:
                raise ValueError(
                    "Post-check falhou: npcs.imagem_url nao bate com a nova mae. Nada foi gravado."
                )
        return alvo["url"]
    finally:
        await conn.close()


# =============================================================================
# UI — casca da Central + paginas
# =============================================================================

def _casca_central(aba_ativa: str = "NPCs"):
    """Barra de abas minima da Central (VISAO secao 2). Nesta onda so a aba NPCs
    existe; as outras entram nas ondas delas (rotulos visiveis, desabilitados)."""
    with ui.row().classes(
        "w-full items-center gap-3 border-b border-zinc-700 pb-3 mb-2"
    ):
        ui.label("Central de Admin — Alderyn").classes(
            "text-amber-200 text-lg font-semibold mr-4"
        )
        ui.link("NPCs", "/oficina/admin/npcs").classes(
            "text-amber-300 border-b-2 border-amber-400 pb-1"
            if aba_ativa == "NPCs" else "text-zinc-500 hover:text-amber-200"
        )
        for aba_futura in ("Árvore", "Linha do tempo", "Mapa", "Segredos", "Aprovação"):
            ui.label(aba_futura).classes("text-zinc-700 cursor-not-allowed").tooltip(
                "Onda futura"
            )


def _card_dossie(titulo: str, icone: str, subtitulo: str = ""):
    """Card do dossiê: moldura bronze, título dourado. Ícones Material (o set
    ti-* não está carregado no projeto). Uso: with _card_dossie(...): ..."""
    card = ui.card().classes("w-full bg-zinc-800 gap-2 mb-2").style(
        f"border:1px solid {_BRONZE};border-radius:8px"
    )
    with card:
        with ui.row().classes("items-center gap-2"):
            ui.icon(icone, size="1.1rem").style(f"color:{_DOURADO}")
            ui.label(titulo).classes(
                "text-sm uppercase tracking-widest font-semibold"
            ).style(f"color:{_DOURADO}")
            if subtitulo:
                ui.label(subtitulo).classes("text-xs text-zinc-500")
    return card


def _chip_dossie(texto: str) -> None:
    """Chip âmbar do dossiê (identidade)."""
    ui.label(texto).classes("text-sm rounded-full px-3 py-1").style(
        f"background:{_CHIP_BG};color:{_CHIP_FG}"
    )


def _render_card_quem_e(npc: dict) -> None:
    """Card 'Quem é': chips de identidade + momento-âncora destacado + perfil
    completo (recolhido). Regra de ouro: sem nenhum dado, o card não existe."""
    chips = _chips_identidade(npc)
    momento = npc.get("momento_de_singularidade")
    perfil = _linhas_perfil(npc)
    if not (chips or momento or perfil):
        return
    with _card_dossie("Quem é", "description"):
        if chips:
            with ui.row().classes("gap-2"):
                for texto in chips:
                    _chip_dossie(texto)
        if momento:
            # destaque: surface elevado + estrela dourada, sempre visível
            with ui.row(wrap=False).classes(
                "w-full items-start gap-2 rounded p-3 bg-zinc-900"
            ).style(f"border:1px solid {_BRONZE}"):
                ui.icon("star", size="1.1rem").style(f"color:{_DOURADO}")
                with ui.column().classes("gap-1 min-w-0"):
                    ui.label("Momento-âncora").classes(
                        "text-xs uppercase tracking-widest"
                    ).style(f"color:{_DOURADO}")
                    ui.label(str(momento)).classes("text-zinc-200 text-sm italic")
        if perfil:
            with ui.expansion("Ver perfil completo").classes(
                "w-full text-zinc-300"
            ).props("dense"):
                for rotulo, texto in perfil:
                    ui.label(rotulo).classes(
                        "text-xs uppercase tracking-wide text-zinc-500 mt-2"
                    )
                    ui.label(texto).classes("text-zinc-200 text-sm")


def _render_card_familia(familia: list[dict]) -> None:
    """Card 'Família': um chip por parente com a bolinha vivo/morto. Família
    vazia = card inexistente."""
    if not familia:
        return
    with _card_dossie("Família", "home", _subtitulo_familia(familia)):
        with ui.row().classes("gap-2"):
            for parente in familia:
                cor = _cor_status_parente(parente.get("status_parente"))
                rotulo = _rotulo_parentesco(
                    parente.get("grau_parentesco"), parente.get("sexo_parente")
                )
                with ui.row(wrap=False).classes(
                    "items-center gap-2 rounded-full px-3 py-1"
                ).style(f"background:{_CHIP_BG}"):
                    ui.element("div").style(
                        f"width:8px;height:8px;border-radius:50%;"
                        f"background:{cor};flex:none;"
                    ).tooltip(parente.get("status_parente") or "status desconhecido")
                    ui.label(
                        f"{rotulo} {parente.get('parente_nome') or '?'}"
                    ).classes("text-sm").style(f"color:{_CHIP_FG}")


def _render_card_vinculos(vinculos: list[dict]) -> None:
    """Card 'Vínculos': nome do outro lado + pill do tipo (cor viva) + direção
    quando assimétrico + micro-barra da intensidade dominante na cor do tipo.
    Sem vínculos, sem card."""
    linhas = _consolidar_vinculos(vinculos)
    if not linhas:
        return
    with _card_dossie("Vínculos", "person"):
        for lv in linhas:
            cor = _cor_tipo_vinculo(lv["tipo"])
            with ui.column().classes("w-full gap-1 mb-1"):
                with ui.row(wrap=False).classes("w-full items-center gap-2"):
                    ui.label(lv["nome"]).classes("text-zinc-100 text-sm")
                    if lv["tipo"]:
                        # pill mostra o rótulo PT; a cor vem do tipo cru
                        ui.label(_rotulo_tipo_vinculo(lv["tipo"])).classes(
                            "text-xs rounded-full px-2"
                        ).style(f"background:{cor};color:#1c1917")
                    if lv["direcao"]:
                        ui.label(lv["direcao"]).classes("text-zinc-500 text-xs")
                    if lv["intensidade"]:
                        rotulo_i, valor_i = lv["intensidade"]
                        ui.label(f"{rotulo_i} {valor_i}").classes(
                            "text-zinc-400 text-xs ml-auto flex-none"
                        )
                if lv["intensidade"]:
                    _, valor_i = lv["intensidade"]
                    largura = max(0, min(100, int(valor_i)))
                    # barra curta (teto 120px) à direita, perto do número:
                    # reforço visual — o número é quem diz o valor
                    with ui.element("div").classes("rounded self-end").style(
                        "height:4px;width:120px;background:#3f3f46"
                    ):
                        ui.element("div").classes("rounded").style(
                            f"height:4px;width:{largura}%;background:{cor}"
                        )
                if lv["nota"]:
                    ui.label(lv["nota"]).classes("text-zinc-500 text-xs italic")


def _render_card_aparencia(npc: dict) -> None:
    """Card 'Aparência' (somente leitura — editor é Onda 2): campos curtos da
    âncora + 'Ver descrição completa' recolhida (só a PT; a EN fica no banco,
    query intacta). Regra de ouro: sem nenhum campo, o card não existe."""
    campos = [
        (rotulo, str(npc[campo]))
        for campo, rotulo in _ROTULOS_ANCORA.items() if npc.get(campo)
    ]
    descricao_pt = npc.get("descricao_ancora_pt")
    if not (campos or descricao_pt):
        return
    with _card_dossie("Aparência", "face", "somente leitura"):
        for rotulo, valor in campos:
            with ui.row().classes("gap-2 items-baseline"):
                ui.label(rotulo + ":").classes(
                    "text-zinc-500 text-sm w-40 flex-none"
                )
                ui.label(valor).classes("text-zinc-200 text-sm")
        if descricao_pt:
            with ui.expansion("Ver descrição completa").classes(
                "w-full text-zinc-300"
            ).props("dense"):
                ui.label(str(descricao_pt)).classes(
                    "text-zinc-300 text-sm italic"
                )


async def pagina_admin_npcs() -> None:
    """Lista de NPCs: miniatura + nome + bolinha verde/vermelha. Alfabetica,
    busca por nome. Clique -> detalhe."""
    await aguardar_conexao_websocket("Carregando Central de Admin...")

    with ui.column().classes(
        "w-full min-h-screen bg-zinc-900 text-zinc-100 p-6 gap-4 max-w-7xl mx-auto"
    ):
        _casca_central("NPCs")

        busca_input = (
            ui.input(label="Buscar NPC por nome", placeholder="ex: Elara")
            .props("outlined dense clearable color=amber-8 dark")
            .classes("w-80")
        )

        @ui.refreshable
        async def grid_npcs() -> None:
            try:
                npcs = await _listar_npcs_com_status(busca_input.value or "")
            except Exception as e:
                traceback.print_exc()
                ui.label(f"Erro ao listar NPCs: {e}").classes("text-red-400")
                return
            if not npcs:
                ui.label("Nenhum NPC encontrado.").classes("text-zinc-500")
                return
            with ui.grid(columns=4).classes("w-full gap-3"):
                for npc in npcs:
                    cor, rotulo = _dot_status(npc["tem_mae"])
                    with ui.card().tight().classes(
                        "bg-zinc-800 border border-zinc-700 hover:border-amber-400 "
                        "cursor-pointer transition-colors"
                    ).on(
                        "click",
                        lambda _, nid=npc["id"]: ui.navigate.to(
                            f"/oficina/admin/npcs/{nid}"
                        ),
                    ):
                        if npc["imagem_url"]:
                            ui.image(npc["imagem_url"]).classes(
                                "w-full h-40 object-cover"
                            )
                        else:
                            ui.element("div").classes(
                                "w-full h-40 bg-zinc-900 flex items-center "
                                "justify-center"
                            )
                        with ui.row().classes("items-center gap-2 p-3"):
                            ui.element("div").style(
                                f"width:10px;height:10px;border-radius:50%;"
                                f"background:{cor};flex:none;"
                            ).tooltip(rotulo)
                            ui.label(npc["nome"] or f"NPC #{npc['id']}").classes(
                                "text-zinc-100 truncate"
                            )

        busca_input.on("update:model-value", grid_npcs.refresh, throttle=0.5)
        await grid_npcs()


async def pagina_admin_npc_detalhe(npc_id: int) -> None:
    """Detalhe: imagem-mae grande + ancora read-only + galeria de candidatas +
    Subir imagem + Definir como mae."""
    await aguardar_conexao_websocket(f"Carregando NPC #{npc_id}...")

    with ui.column().classes(
        "w-full min-h-screen bg-zinc-900 text-zinc-100 p-6 gap-4 max-w-6xl mx-auto"
    ):
        _casca_central("NPCs")
        with ui.row().classes("items-center gap-2 text-sm"):
            ui.link("← NPCs", "/oficina/admin/npcs").classes(
                "text-zinc-500 hover:text-amber-200"
            )

        @ui.refreshable
        async def detalhe() -> None:
            try:
                dados = await _carregar_detalhe_npc(npc_id)
                familia = await _carregar_familia(npc_id) if dados else []
                vinculos = await _carregar_vinculos(npc_id) if dados else []
            except Exception as e:
                traceback.print_exc()
                ui.label(f"Erro ao carregar NPC {npc_id}: {e}").classes("text-red-400")
                return
            if dados is None:
                ui.label(f"NPC id={npc_id} não encontrado.").classes("text-zinc-400")
                return

            npc, canonica, galeria = dados["npc"], dados["canonica"], dados["galeria"]
            ui.label(npc["nome"] or f"NPC #{npc_id}").classes(
                "text-2xl text-amber-200 font-semibold"
            )

            # 2 colunas LADO A LADO no desktop: wrap=False vira style inline
            # flex-wrap:nowrap (ganha de classe — o flex-wrap anterior deixava
            # a direita cair pra baixo). min-w-0 na direita: sem ele o texto
            # longo forca overflow. SO apresentacao: queries e transacao intactas.
            with ui.row(wrap=False).classes("w-full gap-6 items-start"):
                # ── coluna ESQUERDA: a mae + legenda + upload ──
                with ui.column().classes("w-96 flex-none gap-2"):
                    ui.label("Imagem-mãe").classes(
                        "text-xs uppercase tracking-widest text-zinc-500"
                    )
                    if canonica:
                        # moldura verde dessaturada: concorda com o dot 'canonica'
                        ui.image(canonica["url"]).classes(
                            "w-full rounded border border-green-800"
                        )
                        # legenda: nome do NPC + status (some sem imagem)
                        ui.label(
                            _legenda_mae(npc.get("nome"), npc_id)
                        ).classes("text-zinc-500 text-xs")
                        # dessincronia = sintoma de integridade: mostra, nao esconde
                        if npc["imagem_url"] != canonica["url"]:
                            ui.label(
                                "npcs.imagem_url NÃO bate com a canônica — "
                                "o jogo pode estar mostrando outra imagem."
                            ).classes("text-red-400 text-xs")
                    elif npc["imagem_url"]:
                        ui.image(npc["imagem_url"]).classes(
                            "w-full rounded border border-zinc-700 opacity-70"
                        )
                        ui.label(
                            "Sem linha canônica em npc_imagens (só o ponteiro "
                            "npcs.imagem_url). Suba/defina uma mãe."
                        ).classes("text-amber-400 text-xs")
                    else:
                        ui.label("Sem retrato.").classes("text-zinc-500")
                    # item 2: o botao mora aqui, logo abaixo da imagem-mae
                    ui.button(
                        "Subir imagem",
                        on_click=lambda: _dialog_upload(npc_id, detalhe.refresh),
                    ).props("color=amber-8").classes("w-full mt-2")

                # ── coluna DIREITA: dossiê (Quem é → Família → Vínculos) +
                # aparência + galeria. Regra de ouro: card sem dado NÃO existe. ──
                with ui.column().classes("flex-1 min-w-0 gap-1"):
                    _render_card_quem_e(npc)
                    _render_card_familia(familia)
                    _render_card_vinculos(vinculos)
                    _render_card_aparencia(npc)

                    ui.label("Galeria (não-canônicas)").classes(
                        "text-xs uppercase tracking-widest text-zinc-500 mt-2"
                    )
                    if not galeria:
                        ui.label(
                            "Nenhuma candidata. Suba uma imagem pra começar."
                        ).classes("text-zinc-500")
                    with ui.grid(columns=2).classes("w-full gap-3"):
                        for img in galeria:
                            with ui.card().tight().classes(
                                "bg-zinc-800 border border-zinc-700"
                            ):
                                ui.image(img["url"]).classes("w-full h-40 object-cover")
                                with ui.column().classes("p-2 gap-1"):
                                    ui.label(
                                        f"{img['status']} — {img['rotulo_narrativo'] or img['modelo_ia'] or ''}"
                                    ).classes("text-zinc-400 text-xs truncate")
                                    ui.button(
                                        "Definir como mãe",
                                        on_click=lambda _, iid=img["id"]: _confirmar_mae(
                                            npc_id, iid, detalhe.refresh
                                        ),
                                    ).props("dense color=amber-8 outline").classes("w-full")

        await detalhe()


def _dialog_upload(npc_id: int, refresh) -> None:
    """Dialog 'Subir imagem': valida -> INSERT candidata com os BYTES no banco
    (Bloco 2 da migracao storage; o R2 nao e mais chamado) -> refresh."""
    with ui.dialog() as dialog, ui.card().classes(
        "bg-zinc-800 text-zinc-100 w-96 gap-2"
    ):
        ui.label("Subir imagem (vira candidata)").classes(
            "text-amber-200 text-lg font-semibold"
        )
        ui.label(
            f"JPG, PNG ou WEBP, até {_MAX_UPLOAD_MB} MB. Nada vira mãe sem o "
            "'Definir como mãe'."
        ).classes("text-zinc-400 text-sm")
        rotulo_input = (
            ui.input(label="Rótulo (opcional)", placeholder="ex: retrato definitivo")
            .props("outlined dense color=amber-8 dark")
            .classes("w-full")
        )
        status_label = ui.label("").classes("text-sm")

        async def _on_upload(e):
            file = e.file
            file_bytes = await file.read()
            content_type = (
                getattr(file, "content_type", None)
                or getattr(file, "mime_type", None)
                or getattr(file, "type", None)
            )
            erro = _validar_upload(content_type, len(file_bytes))
            if erro:
                status_label.text = erro
                status_label.classes(replace="text-sm text-red-400")
                return
            status_label.text = f"Enviando {len(file_bytes) / 1024:.0f} KB..."
            status_label.classes(replace="text-sm text-amber-300")
            try:
                # Bloco 2: bytes direto pro banco; o R2 nao e mais chamado aqui
                # (r2_storage segue no codigo ate o Bloco 5 — so nao e usado).
                imagem_id = await _inserir_candidata_upload(
                    npc_id, file_bytes, content_type,
                    (rotulo_input.value or "").strip() or None,
                )
                ui.notify(
                    f"Candidata #{imagem_id} adicionada.",
                    type="positive", position="top",
                )
                dialog.close()
                refresh()
            except Exception as ex:
                traceback.print_exc()
                status_label.text = f"Erro: {ex}"
                status_label.classes(replace="text-sm text-red-400")

        ui.upload(
            label="Selecionar arquivo",
            on_upload=_on_upload,
            max_file_size=_MAX_UPLOAD_MB * 1024 * 1024,
            auto_upload=True,
        ).props(
            "accept='image/jpeg,image/png,image/webp' color=amber-8 flat dense"
        ).classes("w-full")
        with ui.row().classes("w-full justify-end"):
            ui.button("Fechar", on_click=dialog.close).props("flat color=zinc-5")
    dialog.open()


def _confirmar_mae(npc_id: int, imagem_id: int, refresh) -> None:
    """Confirmacao explicita antes da transacao (trocar a mae afeta o jogo no
    turno seguinte)."""
    with ui.dialog() as dialog, ui.card().classes(
        "bg-zinc-800 text-zinc-100 gap-2"
    ):
        ui.label("Definir esta imagem como a mãe?").classes("text-amber-200")
        ui.label(
            "A mãe atual vira 'arquivada' e o jogo passa a mostrar esta no "
            "próximo turno."
        ).classes("text-zinc-400 text-sm")

        async def _executar():
            try:
                url = await definir_como_mae(npc_id, imagem_id)
                ui.notify(
                    f"Nova imagem-mãe definida ({_r2_key_da_url(url)}).",
                    type="positive", position="top",
                )
                dialog.close()
                refresh()
            except ValueError as ex:
                ui.notify(str(ex), type="negative", position="top", timeout=8000)
            except Exception as ex:
                traceback.print_exc()
                ui.notify(
                    f"Erro na transação (nada foi gravado): {ex}",
                    type="negative", position="top", timeout=8000,
                )

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancelar", on_click=dialog.close).props("flat color=zinc-5")
            ui.button("Definir como mãe", on_click=_executar).props("color=amber-8")
    dialog.open()
