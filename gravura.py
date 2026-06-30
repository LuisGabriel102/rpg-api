"""
Pipeline da linha 'gravura:' (P3) — Cronista pede, o backend gera UMA imagem de cena
com o LoRA de ESTILO do Alderyn (fal-ai/flux-lora), cacheia no R2 por key estavel, e
serve a URL publica. A moldura da esquerda (.interlocutor / #retrato) mostra.

DESENHO (comecar SIMPLES):
- CACHE-FIRST (protege dinheiro): key estavel por CONTEUDO da descricao. Antes de gerar,
  olha no R2; se existe, USA (zero custo). So chama o fal se NAO existe. Apos gerar,
  salva no R2 e serve pela URL publica.
- ASSINCRONO: quem chama (jogo.narrar) dispara isto em background; a prosa ja streamou.
- TETO DE SEGURANCA (protege dinheiro): no maximo N geracoes NOVAS por sessao (cache NAO
  conta). Estourou -> para de gerar (nunca gera em loop por bug).
- DEGRADA SEM QUEBRAR: qualquer falha -> None; a moldura fica no estado sobrio (a cena
  NUNCA quebra por causa da imagem).

IMPORTS LAZY de proposito: importar este modulo NAO exige FAL_KEY/R2 env (a suite coleta
sem credencial). r2_storage e fal_client so entram dentro das funcoes.

NUNCA ecoa a FAL_KEY (fal_client le do ambiente sozinho).
"""
from __future__ import annotations

import asyncio
import hashlib
import io
import os

# fal-ai/flux-lora: inference FLUX.1 [dev] + LoRA. O LoRA de estilo foi treinado em
# FLUX.1 dev, entao a inference TEM que ser FLUX.1 (a versao FLUX.2 mais barata seria
# incompativel). Custo ~US$0,035/imagem a ~1MP (arredonda pra cima por MP).
ENDPOINT = "fal-ai/flux-lora"
LORA_SCALE = 1.0
IMAGE_SIZE = "portrait_4_3"      # ~ moldura 4/5; o custo arredonda a 1MP de qualquer jeito
NUM_INFERENCE_STEPS = 28

# TETO DE SEGURANCA: maximo de geracoes NOVAS por sessao (cache nao conta). Conservador
# de proposito; ajustavel aqui. Protege dinheiro contra um bug que pedisse imagem em loop.
TETO_GERACOES_POR_SESSAO = 8
_geracoes_por_sessao: dict[str, int] = {}   # sessao_id(str) -> nº de geracoes reais


def chave_gravura(descricao: str) -> str:
    """Key R2 ESTAVEL por conteudo da descricao (normalizada: minuscula, espacos
    colapsados). Mesma descricao em qualquer sessao -> mesma key -> cache compartilhado
    (revisita = gratis). Caminho: gravuras/cena/<hash>.webp."""
    norm = " ".join((descricao or "").lower().split())
    h = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:24]
    return f"gravuras/cena/{h}.webp"


def _prompt(descricao: str) -> str:
    """Prompt de geracao = trigger do LoRA + a descricao do Cronista (ele decide o
    assunto: rosto quando ha alguem, lugar quando chega num lugar)."""
    trigger = (os.getenv("FAL_LORA_TRIGGER") or "alderyn_grimdark").strip()
    desc = " ".join((descricao or "").split())
    return f"{trigger}, {desc}" if desc else trigger


async def _gerar_fal_bytes(prompt: str) -> bytes:
    """Chama fal-ai/flux-lora com o LoRA treinado e devolve os bytes da imagem em WEBP
    (padrao do projeto). LAZY: importa fal_client/httpx/PIL aqui. Sync subscribe rodado
    num thread (asyncio.to_thread) pra nao bloquear o event loop. NUNCA ecoa FAL_KEY."""
    import fal_client
    import httpx
    from PIL import Image

    lora_url = os.environ["FAL_LORA_URL"]   # gravado no .env + prod
    args = {
        "prompt": prompt,
        "image_size": IMAGE_SIZE,
        "num_images": 1,
        "num_inference_steps": NUM_INFERENCE_STEPS,
        "loras": [{"path": lora_url, "scale": LORA_SCALE}],
        "output_format": "jpeg",
        "enable_safety_checker": True,
    }
    res = await asyncio.to_thread(fal_client.subscribe, ENDPOINT, arguments=args)
    imgs = res.get("images") or []
    url = imgs[0].get("url") if imgs else None
    if not url:
        raise RuntimeError("fal nao devolveu URL de imagem")

    async with httpx.AsyncClient(timeout=90) as cli:
        r = await cli.get(url)
        r.raise_for_status()
        raw = r.content

    im = Image.open(io.BytesIO(raw)).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=88)
    return buf.getvalue()


async def obter_gravura(descricao: str, *, sessao_id) -> "str | None":
    """Cache-first. Devolve a URL publica da gravura desta descricao, gerando UMA vez se
    ainda nao existe no R2. Devolve None quando: descricao vazia, teto de seguranca
    estourado, ou qualquer falha (a cena NUNCA quebra por causa da imagem).

    LAZY: importa r2_storage aqui (sem credencial no import do modulo)."""
    desc = " ".join((descricao or "").split())
    if not desc:
        return None

    from r2_storage import gravura_existe, upload_gravura, url_gravura

    key = chave_gravura(desc)

    # 1) CACHE-FIRST: ja existe? -> zero custo, NAO chama o fal.
    if await gravura_existe(key):
        return url_gravura(key)

    # 2) TETO DE SEGURANCA por sessao (cache nao conta; so geracoes reais).
    sid = str(sessao_id)
    if _geracoes_por_sessao.get(sid, 0) >= TETO_GERACOES_POR_SESSAO:
        return None

    # 3) gera UMA vez, salva no R2, serve a URL. Conta ANTES de gerar: uma falha tambem
    #    consome a cota (protege dinheiro contra retry as cegas em loop).
    _geracoes_por_sessao[sid] = _geracoes_por_sessao.get(sid, 0) + 1
    img = await _gerar_fal_bytes(_prompt(desc))
    await upload_gravura(key, img)
    return url_gravura(key)
