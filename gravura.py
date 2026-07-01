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
GUIDANCE_SCALE = 3.5             # explicito (antes ficava no default do fal). Ajuste fino depois.
# Negative prompt fixo (Causa 2b): barra o dia/cartoon/animais/rosto-nitido que vazaram do
# FLUX base quando o LoRA nao dominou. Ajuste fino depois. NOTA: FLUX.1 dev e guidance-distilled,
# entao negative_prompt/guidance tem efeito mais SUAVE que num modelo CFG puro.
NEGATIVE_PROMPT = (
    "bright daylight, cartoon, saturated colors, cheerful, animals, horse, castle, "
    "sharp focus, clear face, modern, illustration"
)

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


# Tradutor PT->EN via Haiku (o FLUX precisa de EN; a desc do Cronista vem em PT). Espelha o
# padrao de _chamar_haiku_validador (jogo.py): cliente SYNC lazy, rodado via asyncio.to_thread.
# LAZY de proposito (importar gravura NAO exige ANTHROPIC_API_KEY). NUNCA ecoa chave.
_haiku_tradutor_client = None

_TRADUTOR_SYSTEM = (
    "You translate a scene description from Portuguese to English for a text-to-image model. "
    "Output ONLY the English translation on a single line: no preamble, no quotes, no notes. "
    "Preserve the mood, lighting, framing and every detail; do not add or remove content."
)


def _chamar_haiku_tradutor(desc_pt: str) -> str:
    """Traduz a desc PT->EN via Haiku 4.5 (SINCRONO — rode via asyncio.to_thread). Cliente
    lazy: so instancia no 1o uso real. Espelha _chamar_haiku_validador do jogo.py."""
    global _haiku_tradutor_client
    if _haiku_tradutor_client is None:
        from anthropic import Anthropic
        _haiku_tradutor_client = Anthropic()
    resp = _haiku_tradutor_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=_TRADUTOR_SYSTEM,
        messages=[{"role": "user", "content": desc_pt}],
    )
    return resp.content[0].text


async def _traduzir_para_ingles(desc_pt: str) -> str:
    """desc PT -> EN pro FLUX. FAIL-OPEN: vazio/qualquer erro (inclui 401 local) -> devolve a
    desc ORIGINAL (a gravura NUNCA quebra por causa da traducao). Haiku sync via to_thread pra
    nao travar o event loop. So e chamado no cache-miss (o cache hit retorna antes -> 0 Haiku)."""
    desc_pt = " ".join((desc_pt or "").split())
    if not desc_pt:
        return desc_pt
    try:
        en = await asyncio.to_thread(_chamar_haiku_tradutor, desc_pt)
        en = " ".join((en or "").split())
        return en or desc_pt
    except Exception as exc:  # noqa: BLE001 - degrada sem quebrar
        print(f"[gravura] traducao Haiku falhou: {type(exc).__name__}: {exc}")
        return desc_pt


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
        "guidance_scale": GUIDANCE_SCALE,
        "loras": [{"path": lora_url, "scale": LORA_SCALE}],
        "negative_prompt": NEGATIVE_PROMPT,
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


async def obter_gravura(descricao: str, *, sessao_id, on_custo=None) -> "str | None":
    """Cache-first. Devolve a URL publica da gravura desta descricao, gerando UMA vez se
    ainda nao existe no R2. Devolve None quando: descricao vazia, teto de seguranca
    estourado, ou qualquer falha (a cena NUNCA quebra por causa da imagem).

    LAZY: importa r2_storage aqui (sem credencial no import do modulo).

    on_custo (Tarefa 8, opcional): callback sem args chamado UMA vez quando uma gravura
    NOVA e gerada (cache miss real). Cache hit / teto / falha -> nao chama. O chamador usa
    pra somar o custo no contador da sessao; ausencia (None) mantem o comportamento antigo."""
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
    # FLUX precisa de EN; a desc do Cronista vem em PT. Traduz SO aqui (cache-miss real);
    # a key/cache acima segue na desc PT (nao muda o cache). Fail-open -> desc original.
    desc_en = await _traduzir_para_ingles(desc)
    img = await _gerar_fal_bytes(_prompt(desc_en))
    await upload_gravura(key, img)
    # Tarefa 8: nasceu uma gravura NOVA (cache miss real). Sinaliza pro chamador somar o
    # custo no contador da sessao. O cache hit retorna la em cima (linha ~110) e NUNCA
    # chega aqui -> nao soma nada. Defensivo: o callback jamais quebra a imagem/cena.
    if on_custo is not None:
        try:
            on_custo()
        except Exception:
            pass
    return url_gravura(key)
