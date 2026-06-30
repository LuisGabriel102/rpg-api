"""
Queries SQL do Ateliê — Catedral do Alderyn (Módulo 4.6.4).

Centraliza acesso ao banco pra evitar duplicação entre as 4 sub-abas.
Todas as queries usam asyncpg direto (não SQLAlchemy) pra simplicidade
e compatibilidade com Neon pooler.

CONVENÇÕES:
- Funções retornam dict ou list[dict] (nunca objetos SQLModel)
- Sempre usam statement_cache_size=0 (Neon transaction mode requer)
- Erros propagam — caller decide como tratar
"""

from __future__ import annotations

import os
import json
from typing import Optional

import asyncpg


# =============================================================================
# CONNECTION HELPER
# =============================================================================

async def _conectar() -> asyncpg.Connection:
    """Conecta ao Neon. Caller é responsável por chamar conn.close()."""
    db_url = os.environ.get("DATABASE_URL", "").replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    if not db_url:
        raise RuntimeError("DATABASE_URL não definida no .env")
    return await asyncpg.connect(db_url, statement_cache_size=0)


# =============================================================================
# NPC + APARÊNCIA
# =============================================================================

async def carregar_npc_completo(npc_id: int) -> Optional[dict]:
    """Carrega TODOS os campos do NPC + facções (texto array).

    Usado pela aba Aparência (form de edição).
    """
    conn = await _conectar()
    try:
        row = await conn.fetchrow(
            """
            SELECT id, nome, nome_curto, camada, raca, profissao,
                   facoes,
                   rosto, olhos, cabelo, corpo, pele,
                   wardrobe_padrao, iluminacao_tematica, postura_canonica,
                   wardrobe_padrao_herdado, iluminacao_tematica_herdada,
                   postura_canonica_herdada,
                   voz_descritiva, cheiro_caracteristico, tiques_e_maneirismos,
                   descricao_ancora_pt, descricao_ancora_en
            FROM npcs
            WHERE id = $1
            """,
            npc_id,
        )
        if not row:
            return None
        d = dict(row)
        # Normalizar tiques (JSONB → list[dict])
        tiques = d.get("tiques_e_maneirismos")
        if tiques is None:
            d["tiques_e_maneirismos"] = []
        elif isinstance(tiques, str):
            try:
                d["tiques_e_maneirismos"] = json.loads(tiques)
            except json.JSONDecodeError:
                d["tiques_e_maneirismos"] = []
        # facoes pode vir None se NPC nunca teve facção
        d["facoes"] = d.get("facoes") or []
        return d
    finally:
        await conn.close()


async def salvar_aparencia_npc(npc_id: int, campos: dict) -> None:
    """Atualiza campos visuais e narrativos do NPC.

    Args:
        npc_id: ID do NPC.
        campos: dict com chaves entre as 16 colunas de aparência.
            Chaves desconhecidas são ignoradas (whitelist de segurança).
    """
    # Whitelist explícita pra evitar SQL injection via chave dinâmica
    COLUNAS_PERMITIDAS = {
        "rosto", "olhos", "cabelo", "corpo", "pele",
        "wardrobe_padrao", "iluminacao_tematica", "postura_canonica",
        "wardrobe_padrao_herdado", "iluminacao_tematica_herdada",
        "postura_canonica_herdada",
        "voz_descritiva", "cheiro_caracteristico", "tiques_e_maneirismos",
        "descricao_ancora_pt", "descricao_ancora_en",
    }

    sets = []
    valores = []
    i = 1
    for k, v in campos.items():
        if k not in COLUNAS_PERMITIDAS:
            continue

        if k == "tiques_e_maneirismos":
            # JSONB requer cast explícito.
            # Se for None, manda NULL direto (sem cast — Postgres aceita).
            # Se for list/dict, serializa pra JSON string e cast pra jsonb.
            if v is None:
                sets.append(f"{k} = NULL")
                # Não incrementar i nem adicionar ao valores
                continue
            if isinstance(v, (list, dict)):
                v = json.dumps(v)
            sets.append(f"{k} = ${i}::jsonb")
        else:
            sets.append(f"{k} = ${i}")

        valores.append(v)
        i += 1

    if not sets:
        return  # nada a atualizar

    valores.append(npc_id)
    sql = f"UPDATE npcs SET {', '.join(sets)} WHERE id = ${i}"

    conn = await _conectar()
    try:
        await conn.execute(sql, *valores)
    finally:
        await conn.close()


# =============================================================================
# IMAGENS — Galeria + Promoção
# =============================================================================

async def listar_imagens_npc(npc_id: int) -> list[dict]:
    """Lista TODAS as imagens do NPC (ordenadas por status + data desc).

    Ordem: canônica primeiro, depois aprovadas, depois rascunhos,
    depois aposentadas. Dentro de cada grupo: mais recente primeiro.
    """
    conn = await _conectar()
    try:
        rows = await conn.fetch(
            """
            SELECT id, npc_id, url, r2_key, rotulo_narrativo, status,
                   modelo_ia, prompt_usado, custo_usd, duracao_ms,
                   variacao_id, e_principal, criado_em
            FROM npc_imagens
            WHERE npc_id = $1
            ORDER BY
                CASE status
                    WHEN 'canonica'   THEN 1
                    WHEN 'aprovada'   THEN 2
                    WHEN 'rascunho'   THEN 3
                    WHEN 'aposentada' THEN 4
                    ELSE 5
                END,
                criado_em DESC
            """,
            npc_id,
        )
        return [dict(r) for r in rows]
    finally:
        await conn.close()


async def buscar_canonica_atual(npc_id: int) -> Optional[dict]:
    """Retorna a imagem com status='canonica' do NPC, se houver."""
    conn = await _conectar()
    try:
        row = await conn.fetchrow(
            """
            SELECT id, url, modelo_ia, criado_em, rotulo_narrativo
            FROM npc_imagens
            WHERE npc_id = $1 AND status = 'canonica'
            ORDER BY criado_em DESC
            LIMIT 1
            """,
            npc_id,
        )
        return dict(row) if row else None
    finally:
        await conn.close()




async def inserir_imagem_upload(
    npc_id: int,
    url: str,
    rotulo_narrativo=None,
) -> int:
    """Persiste metadados de uma imagem enviada via upload (nao gerada por IA).

    A imagem ja foi subida ao R2 pelo caller. Esta funcao so registra no banco
    como status='rascunho' (usuario decide depois se promove).

    Returns:
        ID da nova linha em npc_imagens.
    """
    conn = await _conectar()
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO npc_imagens (
                npc_id, url, rotulo_narrativo, status,
                modelo_ia, prompt_usado, custo_usd, duracao_ms,
                e_principal, criado_em
            )
            VALUES ($1, $2, $3, 'rascunho', 'upload_manual', NULL, 0, 0, FALSE, NOW())
            RETURNING id
            """,
            npc_id, url, rotulo_narrativo or None,
        )
        return row["id"]
    finally:
        await conn.close()


async def atualizar_status_imagem(
    imagem_id: int, novo_status: str, npc_id: int
) -> None:
    """Atualiza status de uma imagem.

    Se promover pra 'canonica', a canônica antiga é demovida pra 'aprovada'
    automaticamente (índice único parcial garantia 1 canônica por NPC).

    Args:
        imagem_id: ID da imagem a atualizar.
        novo_status: 'rascunho' | 'aprovada' | 'canonica' | 'aposentada'.
        npc_id: redundante mas usado pra demover canônica antiga.
    """
    if novo_status not in ("rascunho", "aprovada", "canonica", "aposentada"):
        raise ValueError(f"Status inválido: {novo_status}")

    conn = await _conectar()
    try:
        async with conn.transaction():
            # Se vai virar canônica, demove a antiga (se houver)
            if novo_status == "canonica":
                await conn.execute(
                    """
                    UPDATE npc_imagens
                    SET status = 'aprovada', e_principal = FALSE
                    WHERE npc_id = $1 AND status = 'canonica' AND id != $2
                    """,
                    npc_id, imagem_id,
                )
                # Marca a nova como principal também (compat com código antigo)
                await conn.execute(
                    """
                    UPDATE npc_imagens
                    SET status = $1, e_principal = TRUE
                    WHERE id = $2
                    """,
                    novo_status, imagem_id,
                )
            else:
                # Se está demovendo a canônica atual, tira e_principal também
                await conn.execute(
                    """
                    UPDATE npc_imagens
                    SET status = $1,
                        e_principal = CASE WHEN $1 = 'canonica' THEN TRUE ELSE FALSE END
                    WHERE id = $2
                    """,
                    novo_status, imagem_id,
                )
    finally:
        await conn.close()


async def deletar_imagem(imagem_id: int) -> Optional[str]:
    """Deleta UMA imagem do banco. Retorna r2_key pra deletar do R2 também.

    NOTA: caller deve chamar r2_storage.delete_imagem() depois.
    """
    conn = await _conectar()
    try:
        row = await conn.fetchrow(
            "DELETE FROM npc_imagens WHERE id = $1 RETURNING url, r2_key",
            imagem_id,
        )
        if not row:
            return None
        return row["url"]
    finally:
        await conn.close()


# =============================================================================
# VARIAÇÕES NOMEADAS
# =============================================================================

async def listar_variacoes_npc(npc_id: int) -> list[dict]:
    """Lista todas variações nomeadas de um NPC."""
    conn = await _conectar()
    try:
        rows = await conn.fetch(
            """
            SELECT id, npc_id, nome_variacao, contexto_narrativo,
                   descricao_modificacao, wardrobe_override, iluminacao_override,
                   e_permanente, e_uso_prioritario, criado_em
            FROM npc_aparencia_variacoes
            WHERE npc_id = $1
            ORDER BY e_uso_prioritario DESC, criado_em DESC
            """,
            npc_id,
        )
        return [dict(r) for r in rows]
    finally:
        await conn.close()


async def criar_variacao(
    npc_id: int,
    nome_variacao: str,
    descricao_modificacao: str,
    contexto_narrativo: str = "",
    wardrobe_override: str = "",
    iluminacao_override: str = "",
    e_permanente: bool = False,
) -> int:
    """Cria nova variação. Retorna o ID criado.

    Raises:
        asyncpg.UniqueViolationError: se nome_variacao já existe pro NPC.
    """
    conn = await _conectar()
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO npc_aparencia_variacoes (
                npc_id, nome_variacao, contexto_narrativo,
                descricao_modificacao, wardrobe_override, iluminacao_override,
                e_permanente, e_uso_prioritario
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, FALSE)
            RETURNING id
            """,
            npc_id, nome_variacao, contexto_narrativo or None,
            descricao_modificacao,
            wardrobe_override or None,
            iluminacao_override or None,
            e_permanente,
        )
        return row["id"]
    finally:
        await conn.close()


async def atualizar_variacao(
    variacao_id: int,
    nome_variacao: str,
    descricao_modificacao: str,
    contexto_narrativo: str = "",
    wardrobe_override: str = "",
    iluminacao_override: str = "",
    e_permanente: bool = False,
) -> None:
    """Edita variação existente."""
    conn = await _conectar()
    try:
        await conn.execute(
            """
            UPDATE npc_aparencia_variacoes
            SET nome_variacao = $1,
                descricao_modificacao = $2,
                contexto_narrativo = $3,
                wardrobe_override = $4,
                iluminacao_override = $5,
                e_permanente = $6
            WHERE id = $7
            """,
            nome_variacao, descricao_modificacao,
            contexto_narrativo or None,
            wardrobe_override or None,
            iluminacao_override or None,
            e_permanente,
            variacao_id,
        )
    finally:
        await conn.close()


async def deletar_variacao(variacao_id: int) -> None:
    """Deleta variação. Imagens com esta variacao_id ficam órfãs (variacao_id=NULL)."""
    conn = await _conectar()
    try:
        await conn.execute(
            "DELETE FROM npc_aparencia_variacoes WHERE id = $1",
            variacao_id,
        )
    finally:
        await conn.close()


async def marcar_variacao_prioritaria(variacao_id: int, npc_id: int) -> None:
    """Marca uma variação como prioritária (exclusiva por NPC).

    Desmarca qualquer outra variação prioritária do mesmo NPC primeiro
    (índice único parcial idx_variacao_prioritaria_unica garante isso).
    """
    conn = await _conectar()
    try:
        async with conn.transaction():
            await conn.execute(
                """
                UPDATE npc_aparencia_variacoes
                SET e_uso_prioritario = FALSE
                WHERE npc_id = $1 AND id != $2
                """,
                npc_id, variacao_id,
            )
            await conn.execute(
                """
                UPDATE npc_aparencia_variacoes
                SET e_uso_prioritario = TRUE
                WHERE id = $1
                """,
                variacao_id,
            )
    finally:
        await conn.close()


async def desmarcar_variacao_prioritaria(npc_id: int) -> None:
    """Remove a flag prioritária de todas as variações do NPC."""
    conn = await _conectar()
    try:
        await conn.execute(
            """
            UPDATE npc_aparencia_variacoes
            SET e_uso_prioritario = FALSE
            WHERE npc_id = $1
            """,
            npc_id,
        )
    finally:
        await conn.close()


# =============================================================================
# AUDITORIA — Histórico de Prompts Gerados
# =============================================================================

async def listar_auditoria_npc(npc_id: int, limite: int = 50) -> list[dict]:
    """Lista as últimas N entradas de auditoria pra um NPC.

    Returns:
        Lista de dicts com modelo, status, custo, duração, etc.
    """
    conn = await _conectar()
    try:
        rows = await conn.fetch(
            """
            SELECT id, npc_id, variacao_id, modelo_ia, parametros, texto_prompt,
                   tamanho_prompt, custo_usd, duracao_ms, status, estagio_falha,
                   criado_em
            FROM npc_prompts_gerados
            WHERE npc_id = $1
            ORDER BY criado_em DESC
            LIMIT $2
            """,
            npc_id, limite,
        )
        return [dict(r) for r in rows]
    finally:
        await conn.close()


async def estatisticas_custo_npc(npc_id: int) -> dict:
    """Retorna estatísticas de custo do NPC.

    Returns:
        dict com total_gasto, total_geracoes, sucesso_count, falha_count.
    """
    conn = await _conectar()
    try:
        row = await conn.fetchrow(
            """
            SELECT
                COALESCE(SUM(custo_usd), 0)::float AS total_gasto,
                COUNT(*) AS total_geracoes,
                COUNT(*) FILTER (WHERE status = 'success') AS sucesso_count,
                COUNT(*) FILTER (WHERE status = 'failed')  AS falha_count
            FROM npc_prompts_gerados
            WHERE npc_id = $1
            """,
            npc_id,
        )
        return dict(row) if row else {
            "total_gasto": 0.0, "total_geracoes": 0,
            "sucesso_count": 0, "falha_count": 0,
        }
    finally:
        await conn.close()


# =============================================================================
# FACÇÕES — Template herdável
# =============================================================================

async def buscar_template_faccoes(faccoes_nomes: list[str]) -> list[dict]:
    """Dado uma lista de NOMES de facções, busca templates de aparência.

    Útil pra mostrar opção "herdar de [Casa Korven]" no form de edição.

    Returns:
        Lista de dicts com {faccao_id, faccao_nome, wardrobe_padrao,
        iluminacao_tematica, postura_canonica}.
    """
    if not faccoes_nomes:
        return []
    conn = await _conectar()
    try:
        rows = await conn.fetch(
            """
            SELECT f.id AS faccao_id, f.nome AS faccao_nome,
                   t.wardrobe_padrao, t.iluminacao_tematica, t.postura_canonica
            FROM ref_faccoes f
            JOIN faccao_aparencia_template t ON t.faccao_id = f.id
            WHERE f.nome = ANY($1::text[])
            """,
            faccoes_nomes,
        )
        return [dict(r) for r in rows]
    finally:
        await conn.close()
