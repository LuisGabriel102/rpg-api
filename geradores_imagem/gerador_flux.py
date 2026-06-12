"""
Adapter FLUX Kontext (Black Forest Labs) via fal-client — Catedral do Alderyn.

Modelo recomendado pra CONSISTÊNCIA de personagem entre gerações.
Usado como modelo PRIMÁRIO no Módulo 4.6.

Endpoints:
    fal-ai/flux-pro/kontext             — image-to-image (com referência)
    fal-ai/flux-pro/kontext/text-to-image — text-to-image (sem referência)

Custo: $0.04/imagem (Pro) ou $0.08/imagem (Max)

Gotchas tratados:
    - URLs do fal.media expiram em ~7 dias → baixamos bytes IMEDIATAMENTE
    - safety_tolerance="5" liberado SÓ via API (necessário pra dark fantasy)
    - fal_client.run_async é async-nativo (NÃO usar asyncio.to_thread)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import fal_client
import httpx


@dataclass
class ResultadoFlux:
    """Resultado de uma geração FLUX Kontext."""
    bytes_imagem: bytes        # PNG/JPEG já baixado do fal.media
    content_type: str          # "image/jpeg" ou "image/png"
    largura: int
    altura: int
    seed: int
    nsfw_detectado: bool
    url_temporaria: str        # URL fal.media (expira ~7 dias — só pra debug/log)


async def gerar_flux_kontext(
    prompt: str,
    imagem_referencia_url: Optional[str] = None,
    aspecto: str = "2:3",
    seed: Optional[int] = None,
    formato: str = "jpeg",
    tolerancia_nsfw: str = "5",
    timeout_segundos: int = 90,
) -> ResultadoFlux:
    """Gera imagem via FLUX Kontext Pro.

    Args:
        prompt: Texto do prompt em inglês (preferencial).
        imagem_referencia_url: URL pública da imagem canônica (R2). Se fornecida,
            usa endpoint image-to-image pra preservar identidade do personagem.
        aspecto: "2:3" (retrato) | "3:2" (paisagem) | "1:1" (quadrado).
        seed: Pra reprodutibilidade. None = aleatório.
        formato: "jpeg" (menor, padrão) ou "png" (sem perda).
        tolerancia_nsfw: "1" (estrito) a "6" (mais permissivo). "5" pra dark fantasy.
        timeout_segundos: Timeout total da chamada (geração + download).

    Returns:
        ResultadoFlux com bytes_imagem prontos pra upload no R2.

    Raises:
        RuntimeError: se a API retornar erro de content policy ou 5xx.
        httpx.TimeoutException: se passar do timeout.

    Lê FAL_KEY do ambiente automaticamente via fal_client.
    """
    if not os.getenv("FAL_KEY"):
        raise RuntimeError("FAL_KEY não definida no ambiente. Verifique .env.")

    # Decide endpoint: tem referência → image-to-image; senão → text-to-image
    if imagem_referencia_url:
        endpoint = "fal-ai/flux-pro/kontext"
        args: dict = {
            "prompt": prompt,
            "image_url": imagem_referencia_url,
            "output_format": formato,
            "safety_tolerance": tolerancia_nsfw,
        }
    else:
        endpoint = "fal-ai/flux-pro/kontext/text-to-image"
        args = {
            "prompt": prompt,
            "aspect_ratio": aspecto,
            "output_format": formato,
            "safety_tolerance": tolerancia_nsfw,
        }

    if seed is not None:
        args["seed"] = seed

    # fal_client.run_async é async-nativo; lê FAL_KEY do env
    try:
        resultado = await fal_client.run_async(endpoint, arguments=args)
    except Exception as e:
        # fal-client não tem hierarquia de exceções rica — capturamos genérico
        msg = str(e).lower()
        if "content_policy" in msg or "violation" in msg:
            raise RuntimeError(f"FLUX rejeitou por content policy: {e}") from e
        if "balance" in msg or "credit" in msg or "402" in msg:
            raise RuntimeError(f"FLUX sem saldo na conta fal.ai: {e}") from e
        raise

    # Extrai dados da resposta
    if not resultado or not resultado.get("images"):
        raise RuntimeError(f"FLUX retornou resposta vazia: {resultado}")

    img_meta = resultado["images"][0]
    url_temp = img_meta["url"]
    largura = img_meta.get("width", 0)
    altura = img_meta.get("height", 0)
    content_type = img_meta.get("content_type", f"image/{formato}")

    # CRÍTICO: baixar bytes IMEDIATAMENTE — URL fal.media expira ~7 dias
    async with httpx.AsyncClient(timeout=timeout_segundos) as http:
        resp = await http.get(url_temp)
        resp.raise_for_status()
        bytes_img = resp.content

    return ResultadoFlux(
        bytes_imagem=bytes_img,
        content_type=content_type,
        largura=largura,
        altura=altura,
        seed=resultado.get("seed", 0),
        nsfw_detectado=bool((resultado.get("has_nsfw_concepts") or [False])[0]),
        url_temporaria=url_temp,
    )
