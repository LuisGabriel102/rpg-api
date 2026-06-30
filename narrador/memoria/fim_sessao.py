"""
Fim de sessão — orquestrador (Tier 5)  ·  Alderyn / Caminho B
=============================================================

Roda o pipeline de ESCRITA quando uma sessão encerra e, em seguida, ABRE a próxima
(lifecycle single-player). Junta tudo que os primitivos do `escrita.py` (Tier 2/3) já
sabem fazer; este módulo só costura a ordem:

    juntar narração (sessao_turnos)
      -> montar prompt do Haiku ({lista_de_entidades} + {narracao})
      -> Haiku 4.5 (extrai fatos duráveis em JSON)
      -> parse_haiku_output -> processar_fatos_haiku (enfileira provisional)
      -> commit_canon(ids)  (>=0.6 canonical, <0.6 pending_review)
      -> gerar recap mínimo -> gravar_recap (sessao_resumo + sessoes.resumo)
      -> LOGAR nao_resolvidos / pulados (NUNCA engolir)
      -> abrir a próxima sessão (mesma campanha/personagem, numero_sessao+1, 'ativa')

O recap desta sessão vira o `recap_anterior` da próxima (montar_contexto_narrador lê
sessao_resumo WHERE sessao_id < atual). É assim que a memória atravessa as sessões.

Haiku injetável: `encerrar_sessao(..., haiku_fn=...)`. O default chama o Haiku real;
testes (e o MODO_MOCK) passam uma função que devolve um JSON fixo — pipeline provado
ponta-a-ponta sem gastar token. A chamada do Haiku roda em thread (asyncio.to_thread)
pra não travar o event loop com a API síncrona.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Callable, Optional

from sqlalchemy import text

from db import get_session
from narrador.memoria.escrita import (
    parse_haiku_output,
    processar_fatos_haiku,
    commit_canon,
    gravar_recap,
)

# Tipo do chamador do Haiku: (narracao, lista_entidades) -> texto bruto do modelo.
HaikuFn = Callable[[str, str], str]

_BASE = Path(__file__).resolve().parents[2]
_PROMPT_PATH = _BASE / "prompt_haiku_extracao_fatos.md"

# A narração que vai pro Haiku ignora a maquinaria: 'sistema' é a diretiva de
# abertura (Tier 4), não história. Só jogador + narrador contam o que aconteceu.
_PAPEIS_NARRACAO = ("jogador", "narrador")


# --- leitura: narração e entidades ------------------------------------------
async def juntar_narracao(sessao_id: int) -> str:
    """Concatena os conteúdos dos turnos (jogador + narrador) em ordem de turno."""
    async with get_session() as session:
        rows = (await session.execute(
            text(
                "SELECT conteudo FROM sessao_turnos "
                "WHERE sessao_id = :s AND papel = ANY(:papeis) "
                "ORDER BY numero_turno"
            ),
            {"s": sessao_id, "papeis": list(_PAPEIS_NARRACAO)},
        )).all()
    return "\n\n".join((r[0] or "").strip() for r in rows if (r[0] or "").strip())


async def listar_entidades() -> str:
    """Lista 'name — entity_type' de todas as entidades, p/ ancorar os nomes do Haiku.

    A SPEC pede `SELECT name`; incluímos `entity_type` porque o próprio prompt do
    Haiku formata 'nome — tipo' e o tipo desambigua (lugar vs pessoa vs grupo).
    """
    async with get_session() as session:
        rows = (await session.execute(
            text("SELECT name, entity_type FROM entities ORDER BY name")
        )).all()
    return "\n".join(f"{r[0]} — {r[1]}" for r in rows)


# --- prompt + chamada do Haiku ----------------------------------------------
def _system_prompt_haiku() -> str:
    """Instruções do Haiku = o .md até a seção '## Entrada' (a entrada vai no user)."""
    txt = _PROMPT_PATH.read_text(encoding="utf-8")
    idx = txt.find("## Entrada")
    return (txt[:idx] if idx != -1 else txt).strip()


def _user_prompt_haiku(narracao: str, lista_entidades: str) -> str:
    return (
        "ENTIDADES CONHECIDAS (nome — tipo):\n"
        f"{lista_entidades}\n\n"
        "NARRAÇÃO DA SESSÃO:\n"
        f"{narracao}"
    )


_haiku_client = None


def _chamar_haiku_real(narracao: str, lista_entidades: str) -> str:
    """Chama o Haiku 4.5 (SÍNCRONO — rode via asyncio.to_thread). Sem sampling
    explícito; o cliente Anthropic só é instanciado quando o Haiku real é usado."""
    global _haiku_client
    if _haiku_client is None:
        from anthropic import Anthropic
        _haiku_client = Anthropic()
    resp = _haiku_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        system=_system_prompt_haiku(),
        messages=[{"role": "user", "content": _user_prompt_haiku(narracao, lista_entidades)}],
    )
    return resp.content[0].text


# --- recap mínimo ------------------------------------------------------------
def _gerar_recap_minimo(numero_sessao: int, narracao: str) -> dict:
    """Recap mínimo e DETERMINÍSTICO (sem LLM): só o `resumo_curto` obrigatório,
    derivado do início da narração. O recap rico (resumo_completo, frase, pergunta
    em aberto via LLM) fica pra depois — este tier garante o elo de continuidade."""
    primeiro = narracao.strip().split("\n\n", 1)[0].strip() if narracao.strip() else ""
    if len(primeiro) > 300:
        primeiro = primeiro[:297].rstrip() + "..."
    resumo = primeiro or f"Sessão {numero_sessao} encerrada sem narração registrada."
    return {"titulo_sessao": f"Sessão {numero_sessao}", "resumo_curto": resumo}


# --- lifecycle: dados da sessão + abrir a próxima ---------------------------
async def _info_sessao(sessao_id: int) -> dict:
    async with get_session() as session:
        row = (await session.execute(
            text(
                "SELECT campanha_id, personagem_id, numero_sessao, status "
                "FROM sessoes WHERE id = :s"
            ),
            {"s": sessao_id},
        )).mappings().first()
    if not row:
        raise ValueError(f"sessão {sessao_id} não existe")
    return dict(row)


async def _abrir_proxima_sessao(info: dict) -> int:
    """Insere a próxima sessão (mesma campanha/personagem, numero_sessao+1, 'ativa')
    e devolve o novo id."""
    async with get_session() as session:
        novo = (await session.execute(
            text(
                "INSERT INTO sessoes (campanha_id, personagem_id, numero_sessao, status) "
                "VALUES (:c, :p, :n, 'ativa') RETURNING id"
            ),
            {"c": info["campanha_id"], "p": info["personagem_id"], "n": info["numero_sessao"] + 1},
        )).scalar()
        await session.commit()
    return int(novo)


async def _marcar_encerrada(sessao_id: int) -> None:
    async with get_session() as session:
        await session.execute(
            text("UPDATE sessoes SET status = 'encerrada' WHERE id = :s"),
            {"s": sessao_id},
        )
        await session.commit()


# --- orquestrador ------------------------------------------------------------
async def encerrar_sessao(
    sessao_id: int,
    haiku_fn: Optional[HaikuFn] = None,
    abrir_proxima: bool = True,
) -> dict:
    """
    Roda o pipeline de fim de sessão e (por padrão) abre a próxima.

    haiku_fn: (narracao, lista_entidades) -> texto bruto do Haiku. Default = Haiku
    real. Passe um mock que devolve JSON fixo pra exercitar sem gastar token.

    Devolve um resumo do que aconteceu (contagens, ids, recap_id, nova_sessao_id).
    Nunca engole nao_resolvidos / pulados: loga e devolve.
    """
    haiku_fn = haiku_fn or _chamar_haiku_real
    info = await _info_sessao(sessao_id)

    narracao = await juntar_narracao(sessao_id)
    lista = await listar_entidades()
    print(f"[fim_sessao] sessao={sessao_id} narracao={len(narracao)} chars, entidades listadas")

    # Haiku (real ou mock) em thread — não trava o event loop.
    raw = await asyncio.to_thread(haiku_fn, narracao, lista)
    # loga o JSON cru que o Haiku devolveu (criterio #3 do flip MODO_MOCK=False).
    print("[fim_sessao] === Haiku raw (JSON de fatos) ===")
    print(raw)
    print("[fim_sessao] === fim Haiku raw ===")
    haiku_json = parse_haiku_output(raw)
    n_fatos = len(haiku_json.get("fatos", []))
    print(f"[fim_sessao] Haiku devolveu {n_fatos} fato(s)")

    # resolve nomes -> uuid, enfileira como provisional
    resultado = await processar_fatos_haiku(haiku_json)
    enf = resultado["enfileirados"]
    nao_resolvidos = resultado["nao_resolvidos"]
    pulados = enf.get("pulados") or []
    ids = enf.get("ids_inseridos") or []

    # promove os desta sessão (>=0.6 canonical, <0.6 pending_review)
    promovidos = await commit_canon(ids) if ids else []
    print(f"[fim_sessao] enfileirados={enf.get('inseridos', 0)} promovidos={len(promovidos)}")

    # LOGAR o que não entrou — NUNCA engolir (curadoria manual depois).
    if nao_resolvidos:
        print(f"[fim_sessao] NAO_RESOLVIDOS ({len(nao_resolvidos)}):")
        for nr in nao_resolvidos:
            print(f"    - {nr.get('motivo')}: {nr.get('fato')}")
    if pulados:
        print(f"[fim_sessao] PULADOS no enfileirar ({len(pulados)}):")
        for p in pulados:
            print(f"    - {p.get('motivo')}: {p.get('triple')}")

    # recap (mínimo) -> sessao_resumo + sessoes.resumo
    recap = _gerar_recap_minimo(info["numero_sessao"], narracao)
    recap_id = await gravar_recap(sessao_id, recap)
    print(f"[fim_sessao] recap gravado id={recap_id}")

    # lifecycle: encerra esta e abre a próxima
    nova_sessao_id = None
    if abrir_proxima:
        await _marcar_encerrada(sessao_id)
        nova_sessao_id = await _abrir_proxima_sessao(info)
        print(f"[fim_sessao] sessao {sessao_id} encerrada; proxima aberta id={nova_sessao_id} "
              f"(numero_sessao={info['numero_sessao'] + 1})")

    return {
        "sessao_id": sessao_id,
        "narracao_chars": len(narracao),
        "fatos_haiku": n_fatos,
        "fatos_enfileirados": enf.get("inseridos", 0),
        "ids_inseridos": ids,
        "promovidos": promovidos,
        "nao_resolvidos": nao_resolvidos,
        "pulados": pulados,
        "recap_id": recap_id,
        "nova_sessao_id": nova_sessao_id,
    }
