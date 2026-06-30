"""
Adapter GPT Image 1.5 (OpenAI) via AsyncOpenAI — Catedral do Alderyn.

Modelo TERCIÁRIO no Módulo 4.6 — edição regional com máscara + refinamento expressivo.
Sucessor do DALL-E 3 (descontinuado em Nov/2025).

Modelo: gpt-image-1.5
Custo: $0.009 (low) | $0.034 (medium, padrão) | $0.133 (high)

Gotchas tratados:
    - GPT Image SEMPRE retorna base64 (b64_json), nunca URL
    - moderation="low" SÓ funciona em /generations, NÃO em /edits
    - revised_prompt mostra o que o GPT realmente usou (após reescrita interna)
    - Cliente singleton via AsyncOpenAI()
"""

from __future__ import annotations

import base64
import io
import os
from dataclasses import dataclass
from typing import Optional

from openai import AsyncOpenAI


@dataclass
class ResultadoGPT:
    """Resultado de uma geração GPT Image 1.5."""
    bytes_imagem: bytes        # PNG/JPEG decodificado de base64
    content_type: str          # "image/png" geralmente
    tamanho: str               # "1024x1024" etc
    qualidade: str             # "low" | "medium" | "high"
    prompt_revisado: Optional[str] = None  # O que GPT realmente usou (reescrita interna)


# Cliente singleton
_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    """Retorna cliente OpenAI async singleton. Lê OPENAI_API_KEY do ambiente."""
    global _client
    if _client is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY não definida no ambiente. Verifique .env.")
        _client = AsyncOpenAI()  # Lê OPENAI_API_KEY automaticamente
    return _client


async def gerar_gpt(
    prompt: str,
    qualidade: str = "medium",
    tamanho: str = "1024x1536",  # 2:3 retrato (mais próximo do nosso framing canônico)
    formato: str = "png",
    moderacao: str = "low",
) -> ResultadoGPT:
    """Gera imagem do zero via GPT Image 1.5.

    Args:
        prompt: Texto do prompt em inglês (preferencial).
        qualidade: "low" ($0.009) | "medium" ($0.034, padrão) | "high" ($0.133).
        tamanho: "1024x1024" (1:1) | "1024x1536" (2:3 retrato) | "1536x1024" (3:2).
        formato: "png" (sem perda) ou "jpeg" (menor).
        moderacao: "low" ou "auto". "low" só funciona aqui (em /generations).

    Returns:
        ResultadoGPT com bytes_imagem decodificado.

    Raises:
        Exception: erros da OpenAI (content policy, rate limit, etc).
    """
    client = _get_client()

    resultado = await client.images.generate(
        model="gpt-image-1.5",
        prompt=prompt,
        n=1,
        size=tamanho,
        quality=qualidade,
        output_format=formato,
        moderation=moderacao,
    )

    if not resultado.data:
        raise RuntimeError(f"GPT Image retornou data vazio: {resultado}")

    img_data = resultado.data[0]
    img_b64 = img_data.b64_json
    if not img_b64:
        raise RuntimeError("GPT Image não retornou b64_json (resposta inválida)")

    bytes_img = base64.b64decode(img_b64)

    return ResultadoGPT(
        bytes_imagem=bytes_img,
        content_type=f"image/{formato}",
        tamanho=tamanho,
        qualidade=qualidade,
        prompt_revisado=getattr(img_data, "revised_prompt", None),
    )


async def editar_gpt(
    imagem_bytes: bytes,
    prompt: str,
    mascara_bytes: Optional[bytes] = None,
    tamanho: str = "1024x1536",
) -> ResultadoGPT:
    """Edita imagem existente via GPT Image 1.5.

    Casos de uso: adicionar cicatriz, mudar cor de roupa, etc preservando o resto.

    Args:
        imagem_bytes: PNG da imagem original.
        prompt: Descrição da edição em inglês.
        mascara_bytes: PNG opcional onde áreas TRANSPARENTES = áreas a editar.
            Se None, GPT decide o que editar pelo prompt.
        tamanho: tamanho de saída (mesmo do generate()).

    Returns:
        ResultadoGPT com a imagem editada.

    Raises:
        Exception: erros da OpenAI.

    NOTA: GPT Image 1.5 usa máscara como GUIA, não pixel-perfect inpainting.
    Pra edição cirúrgica perfeita, considerar workflow alternativo.
    NOTA 2: parâmetro 'moderation' NÃO é suportado em /edits — não passar.
    """
    client = _get_client()

    img_file = io.BytesIO(imagem_bytes)
    img_file.name = "image.png"

    kwargs: dict = {
        "model": "gpt-image-1.5",
        "image": img_file,
        "prompt": prompt,
        "size": tamanho,
        "n": 1,
    }

    if mascara_bytes:
        mask_file = io.BytesIO(mascara_bytes)
        mask_file.name = "mask.png"
        kwargs["mask"] = mask_file

    resultado = await client.images.edit(**kwargs)

    if not resultado.data:
        raise RuntimeError(f"GPT Image editor retornou data vazio: {resultado}")

    img_data = resultado.data[0]
    img_b64 = img_data.b64_json
    if not img_b64:
        raise RuntimeError("GPT Image editor não retornou b64_json")

    return ResultadoGPT(
        bytes_imagem=base64.b64decode(img_b64),
        content_type="image/png",
        tamanho=tamanho,
        qualidade="medium",  # /edits não tem parâmetro de qualidade
        prompt_revisado=getattr(img_data, "revised_prompt", None),
    )
