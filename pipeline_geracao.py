"""
Pipeline orquestrador de geração de imagem — Catedral do Alderyn (Parte 4.6.3).

Coordena o fluxo completo de gerar uma imagem nova de NPC:

  ┌──────────────────────────────────────────────────────────────────┐
  │  6 ESTÁGIOS                                                      │
  ├──────────────────────────────────────────────────────────────────┤
  │  1. CARREGAR    → busca dados do NPC no banco (âncora, etc)     │
  │  2. MONTAR      → constrói prompt em EN via gerador_prompt       │
  │  3. GERAR       → chama API IA (Gemini → GPT → FLUX, fallback)   │
  │  4. UPLOAD      → sobe bytes pro R2 e pega URL pública           │
  │  5. PERSISTIR   → INSERT em npc_imagens com status='rascunho'    │
  │  6. AUDITAR     → INSERT em npc_prompts_gerados (custo, duração) │
  └──────────────────────────────────────────────────────────────────┘

POLÍTICA DE FALLBACK (decidida após validação visual no fim da 4.6.2):
  Modelo primário:   Gemini Nano Banana 2  (qualidade narrativa + custo médio)
  Fallback 1:        GPT Image 1.5         (refinamento + detalhes finos)
  Fallback 2:        FLUX Kontext          (rápido + barato + reference-aware)

POLÍTICA DE RETRY (tenacity):
  - Erros transientes (timeout, 5xx, rede) → retry 3x com backoff exponencial
  - Erros 4xx (content policy, bad request) → SEM retry (vai pro próximo modelo)
  - Erros de saldo (402) → SEM retry (logado como crítico)

REGRA DE OURO: imagem chega no banco APENAS se upload R2 deu certo.
Se R2 falhar, status='rascunho' não é criado. Auditoria registra falha.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Optional, Literal

import httpx
from sqlalchemy import text
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

from gerador_prompt_imagem import (
    DadosPromptNPC,
    de_dict_npc,
    montar_prompt_completo,
    ModeloIA,
)
from geradores_imagem.gerador_gemini import gerar_gemini, ResultadoGemini
from geradores_imagem.gerador_gpt import gerar_gpt, ResultadoGPT
from geradores_imagem.gerador_flux import gerar_flux_kontext, ResultadoFlux
from r2_storage import upload_imagem_npc
from db import get_session

from config.logging_setup import get_logger

log = get_logger(__name__)


# =============================================================================
# 1) CONFIG — preços e ordem de fallback
# =============================================================================

# Custos atualizados (Pesquisa 3 + validação 4.6.2)
PRECO_POR_GERACAO: dict[ModeloIA, float] = {
    "gemini_nano":  0.067,  # 1K — primário
    "gpt_image":    0.034,  # medium quality
    "flux_kontext": 0.040,  # Pro
}

# Ordem de fallback automático (primário → secundário → terciário)
ORDEM_FALLBACK: tuple[ModeloIA, ...] = ("gemini_nano", "gpt_image", "flux_kontext")

# Timeout por chamada (lê do .env, default 90s)
TIMEOUT_SEGUNDOS = int(os.getenv("GERACAO_TIMEOUT_SEGUNDOS", "90"))
MAX_RETRIES = int(os.getenv("GERACAO_MAX_RETRIES", "3"))


# =============================================================================
# 2) RESULTADOS — dataclass pra estado completo de uma execução
# =============================================================================

EstagioFalha = Literal[
    "carregar", "montar_prompt", "gerar_imagem", "upload_r2",
    "persistir_bd", "auditar_bd",
]


@dataclass
class ResultadoPipeline:
    """Estado completo de uma execução do pipeline.

    Sucesso quando: status='success' E url_imagem != None E imagem_id != None.
    """
    npc_id: int
    status: Literal["success", "failed"] = "failed"

    # Dados do prompt
    prompt_gerado: str = ""
    modelo_usado: Optional[ModeloIA] = None
    modelos_tentados: list[ModeloIA] = field(default_factory=list)

    # Resultados de cada estágio
    bytes_imagem: Optional[bytes] = None
    content_type: str = ""
    url_imagem: Optional[str] = None
    r2_key: Optional[str] = None
    imagem_id: Optional[int] = None    # PK em npc_imagens
    prompt_log_id: Optional[int] = None  # PK em npc_prompts_gerados

    # Métricas
    custo_usd: float = 0.0
    duracao_total_ms: int = 0
    duracao_geracao_ms: int = 0
    duracao_upload_ms: int = 0

    # Falha (se houver)
    estagio_falha: Optional[EstagioFalha] = None
    mensagem_erro: str = ""


# =============================================================================
# 3) EXCEÇÕES CUSTOMIZADAS (pra controle de retry/fallback)
# =============================================================================

class ErroTransiente(Exception):
    """Erro temporário — vale retry com backoff (timeout, 5xx, rede)."""
    pass


class ErroContentPolicy(Exception):
    """Modelo bloqueou por content policy — pula pro próximo modelo, sem retry."""
    pass


class ErroSaldoInsuficiente(Exception):
    """Saldo zerou na conta da API — crítico, alerta operador."""
    pass


def _classificar_erro(exc: Exception) -> Exception:
    """Classifica exceção genérica em uma das categorias acima.

    Retorna a exceção classificada ou a original se não bater em nenhuma.
    """
    msg = str(exc).lower()

    # Saldo / billing
    if any(t in msg for t in ("balance", "credit", "insufficient_quota", "402")):
        return ErroSaldoInsuficiente(str(exc))

    # Content policy
    if any(t in msg for t in ("content_policy", "content policy", "violation",
                              "safety", "blocked", "moderat")):
        return ErroContentPolicy(str(exc))

    # Transientes (timeout, conexão, 5xx)
    if any(t in msg for t in ("timeout", "timed out", "connection", "5xx",
                              "503", "504", "502", "rate")):
        return ErroTransiente(str(exc))

    # Tipo conhecido?
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError,
                        httpx.RemoteProtocolError, asyncio_timeout_class())):
        return ErroTransiente(str(exc))

    # Padrão: tratamos como transiente (retry-eligible) por segurança
    return ErroTransiente(str(exc))


def asyncio_timeout_class():
    """Wrapper pra pegar TimeoutError sem import circular."""
    import asyncio
    return asyncio.TimeoutError


# =============================================================================
# 4) ESTÁGIO 1 — CARREGAR NPC
# =============================================================================

async def _carregar_npc(npc_id: int) -> dict:
    """Carrega dados completos do NPC pra geração de prompt.

    Returns:
        dict com nome + descricao_ancora_pt/en + iluminação + wardrobe.

    Raises:
        ValueError: NPC não existe ou sem âncora preenchida.
    """
    async with get_session() as session:
        result = await session.execute(
            text("""
                SELECT id, nome, camada, raca,
                       descricao_ancora_pt, descricao_ancora_en,
                       wardrobe_padrao, iluminacao_tematica, postura_canonica,
                       wardrobe_padrao_herdado, iluminacao_tematica_herdada
                FROM npcs
                WHERE id = :npc_id
            """),
            {"npc_id": npc_id},
        )
        row = result.mappings().fetchone()

    if not row:
        raise ValueError(f"NPC id={npc_id} não encontrado no banco.")

    npc = dict(row)
    if not (npc.get("descricao_ancora_en") or npc.get("descricao_ancora_pt")):
        raise ValueError(
            f"NPC id={npc_id} ({npc.get('nome')}) sem âncora de identidade. "
            "Preencha descricao_ancora_en ou descricao_ancora_pt antes de gerar."
        )

    return npc


async def _buscar_url_canonica(npc_id: int) -> Optional[str]:
    """Busca URL da imagem canônica do NPC no R2 (se existir).

    Returns:
        URL pública R2 ou None se não houver canônica.
    """
    async with get_session() as session:
        result = await session.execute(
            text("""
                SELECT url FROM npc_imagens
                WHERE npc_id = :npc_id AND status = 'canonica'
                ORDER BY criado_em DESC
                LIMIT 1
            """),
            {"npc_id": npc_id},
        )
        return result.scalar()


# =============================================================================
# 5) ESTÁGIO 3 — GERAR (com retry + fallback)
# =============================================================================

# Decorator de retry: retry 3x apenas pra erros transientes
_retry_transiente = retry(
    retry=retry_if_exception_type(ErroTransiente),
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
    reraise=True,
)


@_retry_transiente
async def _gerar_com_modelo(
    modelo: ModeloIA,
    prompt: str,
    referencia_url: Optional[str],
    referencia_bytes: Optional[bytes],
) -> tuple[bytes, str]:
    """Chama UM modelo específico com retry pra transientes.

    Retorna (bytes_imagem, content_type).
    Levanta ErroContentPolicy / ErroSaldoInsuficiente sem retry.
    """
    log.info("chamando_modelo", modelo=modelo)

    try:
        if modelo == "gemini_nano":
            res: ResultadoGemini = await gerar_gemini(
                prompt=prompt,
                imagem_referencia_bytes=referencia_bytes,
                aspecto="2:3",
                tamanho="1K",
            )
            return res.bytes_imagem, res.content_type

        elif modelo == "gpt_image":
            res_gpt: ResultadoGPT = await gerar_gpt(
                prompt=prompt,
                qualidade="medium",
                tamanho="1024x1536",
                formato="png",
            )
            return res_gpt.bytes_imagem, res_gpt.content_type

        elif modelo == "flux_kontext":
            res_flux: ResultadoFlux = await gerar_flux_kontext(
                prompt=prompt,
                imagem_referencia_url=referencia_url,
                aspecto="2:3",
                formato="jpeg",
                timeout_segundos=TIMEOUT_SEGUNDOS,
            )
            return res_flux.bytes_imagem, res_flux.content_type

        else:
            raise ValueError(f"Modelo desconhecido: {modelo}")

    except (ErroTransiente, ErroContentPolicy, ErroSaldoInsuficiente):
        # Já classificadas — propaga
        raise
    except Exception as e:
        # Classifica e re-levanta
        raise _classificar_erro(e) from e


async def _baixar_referencia_se_houver(url: Optional[str]) -> Optional[bytes]:
    """Baixa imagem de referência se URL fornecida. Retorna None se falhar."""
    if not url:
        return None
    try:
        async with httpx.AsyncClient(timeout=20) as http:
            resp = await http.get(url)
            resp.raise_for_status()
            log.info("referencia_baixada", url=url, bytes=len(resp.content))
            return resp.content
    except Exception as e:
        log.warning("referencia_falhou", url=url, erro=str(e))
        return None  # Continua sem referência


# =============================================================================
# 6) ESTÁGIO 5+6 — PERSISTIR BANCO
# =============================================================================

async def _persistir_imagem_e_auditoria(
    npc_id: int,
    url: str,
    r2_key: str,
    modelo: ModeloIA,
    content_type: str,
    prompt_usado: str,
    custo: float,
    duracao_ms: int,
    rotulo: str = "Geração automática",
    variacao_id: Optional[int] = None,
) -> tuple[int, int]:
    """Insere registro em npc_imagens + npc_prompts_gerados.

    Retorna (imagem_id, prompt_log_id).
    Tudo numa transação — se falhar metade, reverte tudo.
    """
    async with get_session() as session:
        # 1. INSERT em npc_imagens
        result = await session.execute(
            text("""
                INSERT INTO npc_imagens (
                    npc_id, url, r2_key, rotulo_narrativo, e_principal,
                    modelo_ia, prompt_usado, custo_usd, duracao_ms,
                    variacao_id, status, criado_em
                ) VALUES (
                    :npc_id, :url, :r2_key, :rotulo, FALSE,
                    :modelo, :prompt, :custo, :duracao,
                    :variacao_id, 'rascunho', NOW()
                )
                RETURNING id
            """),
            {
                "npc_id": npc_id,
                "url": url,
                "r2_key": r2_key,
                "rotulo": rotulo,
                "modelo": modelo,
                "prompt": prompt_usado,
                "custo": custo,
                "duracao": duracao_ms,
                "variacao_id": variacao_id,
            },
        )
        imagem_id = result.scalar_one()

        # 2. INSERT em npc_prompts_gerados (auditoria)
        result_log = await session.execute(
            text("""
                INSERT INTO npc_prompts_gerados (
                    npc_id, variacao_id, modelo_ia, parametros, texto_prompt,
                    tamanho_prompt, custo_usd, duracao_ms, status, criado_em
                ) VALUES (
                    :npc_id, :variacao_id, :modelo, :parametros, :prompt,
                    :tamanho, :custo, :duracao, 'success', NOW()
                )
                RETURNING id
            """),
            {
                "npc_id": npc_id,
                "variacao_id": variacao_id,
                "modelo": modelo,
                "parametros": '{"aspecto":"2:3","tamanho":"1K"}',
                "prompt": prompt_usado,
                "tamanho": len(prompt_usado),
                "custo": custo,
                "duracao": duracao_ms,
            },
        )
        prompt_log_id = result_log.scalar_one()

        await session.commit()

    return imagem_id, prompt_log_id


async def _registrar_falha_auditoria(
    npc_id: int,
    modelo: Optional[ModeloIA],
    prompt: str,
    estagio: EstagioFalha,
    erro_msg: str,
    duracao_ms: int,
) -> Optional[int]:
    """Registra UMA falha em npc_prompts_gerados (auditoria de erro)."""
    if not modelo:
        modelo = "gemini_nano"  # default pra log
    try:
        async with get_session() as session:
            result = await session.execute(
                text("""
                    INSERT INTO npc_prompts_gerados (
                        npc_id, modelo_ia, texto_prompt, tamanho_prompt,
                        custo_usd, duracao_ms, status, estagio_falha, criado_em
                    ) VALUES (
                        :npc_id, :modelo, :prompt, :tamanho,
                        0, :duracao, 'failed', :estagio, NOW()
                    )
                    RETURNING id
                """),
                {
                    "npc_id": npc_id,
                    "modelo": modelo,
                    "prompt": prompt[:5000],  # trunca pra não estourar texto
                    "tamanho": len(prompt),
                    "duracao": duracao_ms,
                    "estagio": estagio,
                },
            )
            log_id = result.scalar_one()
            await session.commit()
            return log_id
    except Exception as e:
        # Auditoria não pode quebrar o pipeline
        log.error("auditoria_falhou", erro=str(e), estagio_orig=estagio)
        return None


# =============================================================================
# 7) FUNÇÃO PRINCIPAL — gerar_imagem_npc()
# =============================================================================

async def gerar_imagem_npc(
    npc_id: int,
    rotulo: str = "Geração automática",
    variacao_id: Optional[int] = None,
    modelos_preferidos: Optional[tuple[ModeloIA, ...]] = None,
    cenario_override: str = "",
    iluminacao_override: str = "",
    descricao_modificacao: str = "",
    usar_referencia_canonica: bool = True,
) -> ResultadoPipeline:
    """Pipeline completo de geração de imagem pra um NPC.

    Args:
        npc_id: ID do NPC no banco.
        rotulo: rótulo narrativo da imagem (ex: "Almareth aposentado").
        variacao_id: ID de variação se aplicável.
        modelos_preferidos: ordem custom de fallback. Se None, usa ORDEM_FALLBACK
            (Gemini → GPT → FLUX).
        cenario_override: força um cenário específico (ex: "throne room").
        iluminacao_override: força iluminação específica.
        descricao_modificacao: delta da variação (ex: "+6 anos, ferido").
        usar_referencia_canonica: se True, busca canônica do NPC e passa como
            referência (Gemini/FLUX). False = gera do zero.

    Returns:
        ResultadoPipeline com tudo que aconteceu (sucesso ou falha).
    """
    inicio = time.perf_counter()
    resultado = ResultadoPipeline(npc_id=npc_id)
    modelos = modelos_preferidos or ORDEM_FALLBACK

    log.info("pipeline_iniciado", npc_id=npc_id, modelos=modelos, rotulo=rotulo)

    # =========================================================================
    # ESTÁGIO 1: Carregar NPC
    # =========================================================================
    try:
        npc = await _carregar_npc(npc_id)
        log.info("npc_carregado", npc_id=npc_id, nome=npc["nome"])
    except Exception as e:
        resultado.estagio_falha = "carregar"
        resultado.mensagem_erro = f"{type(e).__name__}: {e}"
        resultado.duracao_total_ms = int((time.perf_counter() - inicio) * 1000)
        log.error("falha_carregar", erro=resultado.mensagem_erro)
        await _registrar_falha_auditoria(
            npc_id, None, "", "carregar",
            resultado.mensagem_erro, resultado.duracao_total_ms,
        )
        return resultado

    # Buscar referência canônica (se solicitada)
    url_canonica: Optional[str] = None
    if usar_referencia_canonica:
        url_canonica = await _buscar_url_canonica(npc_id)

    # =========================================================================
    # ESTÁGIO 2: Montar prompt (uma vez só — mesmo prompt pra todos modelos)
    # =========================================================================
    # NOTA: cada modelo idealmente teria template otimizado, mas pra simplificar
    # geramos UM prompt genérico (do template do modelo primário) e usamos
    # como entrada pros 3. No 4.6.4 podemos refinar pra usar template específico
    # de cada modelo se chegar fallback.
    try:
        dados = de_dict_npc(npc)
        prompt = montar_prompt_completo(
            dados,
            modelos[0],  # template do primário
            descricao_modificacao=descricao_modificacao,
            cenario_override=cenario_override,
            iluminacao_override=iluminacao_override,
        )
        resultado.prompt_gerado = prompt
        log.info("prompt_montado", tamanho=len(prompt), modelo_template=modelos[0])
    except Exception as e:
        resultado.estagio_falha = "montar_prompt"
        resultado.mensagem_erro = f"{type(e).__name__}: {e}"
        resultado.duracao_total_ms = int((time.perf_counter() - inicio) * 1000)
        log.error("falha_montar_prompt", erro=resultado.mensagem_erro)
        await _registrar_falha_auditoria(
            npc_id, None, "", "montar_prompt",
            resultado.mensagem_erro, resultado.duracao_total_ms,
        )
        return resultado

    # =========================================================================
    # ESTÁGIO 3: GERAR — fallback automático entre modelos
    # =========================================================================
    referencia_bytes = await _baixar_referencia_se_houver(url_canonica)

    bytes_img: Optional[bytes] = None
    content_type: str = ""
    inicio_geracao = time.perf_counter()
    ultimo_erro: str = ""

    for modelo in modelos:
        resultado.modelos_tentados.append(modelo)
        try:
            bytes_img, content_type = await _gerar_com_modelo(
                modelo=modelo,
                prompt=prompt,
                referencia_url=url_canonica,
                referencia_bytes=referencia_bytes,
            )
            resultado.modelo_usado = modelo
            resultado.custo_usd = PRECO_POR_GERACAO[modelo]
            log.info("modelo_sucesso", modelo=modelo, bytes=len(bytes_img))
            break

        except ErroSaldoInsuficiente as e:
            ultimo_erro = f"[{modelo}] saldo zerado: {e}"
            log.error("saldo_zerado", modelo=modelo, erro=str(e))
            # Pula pro próximo modelo
            continue

        except ErroContentPolicy as e:
            ultimo_erro = f"[{modelo}] content policy: {e}"
            log.warning("content_policy", modelo=modelo, erro=str(e))
            continue

        except ErroTransiente as e:
            # Já fez retries internamente; aqui significa que esgotou
            ultimo_erro = f"[{modelo}] transiente após {MAX_RETRIES} retries: {e}"
            log.warning("modelo_falhou_apos_retries", modelo=modelo, erro=str(e))
            continue

        except Exception as e:
            ultimo_erro = f"[{modelo}] erro inesperado: {type(e).__name__}: {e}"
            log.error("erro_inesperado", modelo=modelo, erro=str(e))
            continue

    resultado.duracao_geracao_ms = int((time.perf_counter() - inicio_geracao) * 1000)

    if bytes_img is None:
        resultado.estagio_falha = "gerar_imagem"
        resultado.mensagem_erro = (
            f"Todos {len(modelos)} modelos falharam. Último erro: {ultimo_erro}"
        )
        resultado.duracao_total_ms = int((time.perf_counter() - inicio) * 1000)
        log.error("todos_modelos_falharam", modelos_tentados=resultado.modelos_tentados)
        await _registrar_falha_auditoria(
            npc_id, None, prompt, "gerar_imagem",
            resultado.mensagem_erro, resultado.duracao_total_ms,
        )
        return resultado

    resultado.bytes_imagem = bytes_img
    resultado.content_type = content_type

    # =========================================================================
    # ESTÁGIO 4: Upload R2
    # =========================================================================
    inicio_upload = time.perf_counter()
    try:
        url_publica = await upload_imagem_npc(
            npc_id=npc_id,
            file_bytes=bytes_img,
            content_type=content_type,
        )
        resultado.url_imagem = url_publica
        # Extrai r2_key da URL pública (depois do último /)
        resultado.r2_key = url_publica.rsplit("/", 1)[-1]
        resultado.duracao_upload_ms = int((time.perf_counter() - inicio_upload) * 1000)
        log.info("upload_r2_sucesso", url=url_publica, ms=resultado.duracao_upload_ms)
    except Exception as e:
        resultado.estagio_falha = "upload_r2"
        resultado.mensagem_erro = f"{type(e).__name__}: {e}"
        resultado.duracao_total_ms = int((time.perf_counter() - inicio) * 1000)
        log.error("upload_r2_falhou", erro=resultado.mensagem_erro)
        await _registrar_falha_auditoria(
            npc_id, resultado.modelo_usado, prompt, "upload_r2",
            resultado.mensagem_erro, resultado.duracao_total_ms,
        )
        return resultado

    # =========================================================================
    # ESTÁGIOS 5+6: Persistir + Auditar (transação)
    # =========================================================================
    try:
        imagem_id, prompt_log_id = await _persistir_imagem_e_auditoria(
            npc_id=npc_id,
            url=resultado.url_imagem,
            r2_key=resultado.r2_key,
            modelo=resultado.modelo_usado,
            content_type=content_type,
            prompt_usado=prompt,
            custo=resultado.custo_usd,
            duracao_ms=resultado.duracao_geracao_ms,
            rotulo=rotulo,
            variacao_id=variacao_id,
        )
        resultado.imagem_id = imagem_id
        resultado.prompt_log_id = prompt_log_id
        log.info(
            "persistido_no_banco",
            imagem_id=imagem_id,
            prompt_log_id=prompt_log_id,
        )
    except Exception as e:
        resultado.estagio_falha = "persistir_bd"
        resultado.mensagem_erro = f"{type(e).__name__}: {e}"
        resultado.duracao_total_ms = int((time.perf_counter() - inicio) * 1000)
        log.error("persistir_bd_falhou", erro=resultado.mensagem_erro)
        # Imagem JÁ está no R2 mas órfã — log alerta operador
        log.warning(
            "imagem_orfa_no_r2",
            url=resultado.url_imagem,
            obs="Subiu R2 mas falhou banco. Considere deletar do R2 manualmente.",
        )
        return resultado

    # =========================================================================
    # SUCESSO
    # =========================================================================
    resultado.status = "success"
    resultado.duracao_total_ms = int((time.perf_counter() - inicio) * 1000)
    log.info(
        "pipeline_sucesso",
        npc_id=npc_id,
        modelo=resultado.modelo_usado,
        imagem_id=resultado.imagem_id,
        custo=resultado.custo_usd,
        duracao_total_ms=resultado.duracao_total_ms,
    )
    return resultado
