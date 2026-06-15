"""
Leitura de contexto do narrador  (Alderyn / Caminho B) — formatador
====================================================================

Chama montar_contexto_narrador() no banco (junta os 5 tiers num jsonb) e
formata em markdown para o prompt do Cronista (Opus).

Princípios:
  - Seção vazia é OMITIDA — o prompt só recebe o que existe.
  - Ordem por prioridade: dívidas/pactos -> recap -> últimos turnos ->
    fatos -> boatos.
  - Os rumores entram SEM a `verdade_real` (segredo do mestre). O Cronista vê
    o boato e seu grau de confiança, nunca o que o boato esconde. É a mesma
    lógica do forbidden de leitura, do lado do prompt.

Driver: exemplo com psycopg (v3) síncrono; a lógica é idêntica em asyncpg.
"""

import json
from typing import Optional


# --- formatação pura (jsonb -> markdown) ------------------------------------
def formatar_contexto_para_prompt(ctx: dict) -> str:
    """
    Recebe o dict de montar_contexto_narrador e devolve o markdown do contexto.
    Devolve "" se não houver nada — aí o prompt do Cronista fica sem a seção.
    """
    blocos = []

    # T0 — pacto e dívida (texto já formatado pelo banco)
    pact = ctx.get("pact_ledger")
    if pact and pact.strip():
        blocos.append("## Compromissos e dívidas\n" + pact.strip())

    # recap da sessão anterior
    recap = ctx.get("recap_anterior")
    if recap:
        linhas = []
        if recap.get("titulo"):
            linhas.append(f"_Sessão anterior: {recap['titulo']}_")
        if recap.get("resumo"):
            linhas.append(recap["resumo"])
        if recap.get("pergunta_em_aberto"):
            linhas.append(f"Em aberto: {recap['pergunta_em_aberto']}")
        if recap.get("continuidade"):
            linhas.append(f"Continuidade: {recap['continuidade']}")
        dec = recap.get("decisoes") or []
        if dec:
            linhas.append("Decisões que pesaram: " + "; ".join(dec))
        rel = recap.get("relacoes_mudaram") or []
        if rel:
            linhas.append("Relações que mudaram: " + "; ".join(rel))
        if linhas:
            blocos.append("## O que veio antes\n" + "\n".join(linhas))

    # turnos recentes (curto prazo)
    turnos = ctx.get("turnos_recentes") or []
    if turnos:
        falas = [
            f"[{t.get('papel', '?')}] {(t.get('conteudo') or '').strip()}"
            for t in turnos
        ]
        blocos.append("## Os últimos instantes\n" + "\n".join(falas))

    # fatos canônicos relevantes (o que se sabe)
    fatos = ctx.get("fatos_relevantes") or []
    if fatos:
        linhas = [f"- {f['fato']}" for f in fatos if f.get("fato")]
        if linhas:
            blocos.append("## O que se sabe\n" + "\n".join(linhas))

    # rumores (boato — sem a verdade_real)
    rumores = ctx.get("rumores") or []
    if rumores:
        linhas = []
        for r in rumores:
            titulo = r.get("titulo", "")
            conteudo = (r.get("conteudo") or "").strip()
            ver = r.get("veracidade")
            sufixo = f" _({ver})_" if ver else ""
            linhas.append(f"- **{titulo}**: {conteudo}{sufixo}")
        blocos.append("## O que se diz — boatos, nem tudo é verdade\n" + "\n".join(linhas))

    return "\n\n".join(blocos)


# --- leitura ponta a ponta (banco -> markdown) ------------------------------
def carregar_contexto(
    conn,
    sessao_id: int,
    query_text: Optional[str] = None,
    query_vec: Optional[str] = None,   # embedding da fala do jogador, como '[...]' pgvector ou None
    focus_entity: Optional[str] = None,  # uuid da entidade em foco, ou None
    regiao: Optional[str] = None,
    limite_fatos: int = 8,
    limite_turnos: int = 6,
    limite_rumores: int = 5,
) -> str:
    """
    Chama montar_contexto_narrador no banco e devolve o markdown pronto pro prompt.

    query_vec: passe o embedding (768-dim) da fala do jogador como string pgvector
    '[0.1,0.2,...]'. Enquanto os fatos não tiverem embedding, deixe None — a busca
    cai automaticamente pra full-text + trigram + entidade.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT montar_contexto_narrador(%s, %s, %s::vector, %s::uuid, %s, %s, %s, %s)",
            (sessao_id, query_text, query_vec, focus_entity, regiao,
             limite_fatos, limite_turnos, limite_rumores),
        )
        ctx = cur.fetchone()[0]  # jsonb -> dict (psycopg adapta)
    return formatar_contexto_para_prompt(ctx)


# --- exemplo de uso ---------------------------------------------------------
if __name__ == "__main__":
    # import psycopg
    # conn = psycopg.connect("postgresql://...")
    #
    # contexto_md = carregar_contexto(
    #     conn,
    #     sessao_id=2,
    #     query_text="o que o jogador acabou de dizer / a cena atual",
    #     focus_entity="4147dbff-204f-44f9-9737-9ce3d1025a21",
    #     regiao="Tarelea",
    # )
    # # contexto_md entra como uma seção do prompt do Cronista (Opus).
    # print(contexto_md)
    pass
