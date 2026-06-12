"""
Adapter Gemini Nano Banana 2 (Google) via google-genai — Catedral do Alderyn.

V3 (15/04/2026): Corrigido bug TypeError em Image.save(format=...).
  - O método as_image() do google-genai retorna wrapper customizado, não PIL.Image puro
  - Agora extraímos os bytes brutos diretamente de part.inline_data.data

Modelo SECUNDÁRIO no Módulo 4.6 — custo baixo + suporte nativo PT-BR.

Modelo: gemini-3.1-flash-image-preview (Nano Banana 2)
Custo: $0.045 (512px) | $0.067 (1K) | $0.101 (2K)

Gotchas:
    - SDK CORRETO é `google-genai` (NÃO o legado `google-generativeai`)
    - response_modalities=["IMAGE"] é OBRIGATÓRIO
    - image_size aceita "512", "1K", "2K" (maiúscula importa)
    - Cliente é singleton — não recriar a cada chamada
    - api_key passado EXPLICITAMENTE no Client(api_key=...) pra aceitar OAuth tokens
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import Optional

from google import genai
from google.genai import types


@dataclass
class ResultadoGemini:
    """Resultado de uma geração Gemini Nano Banana 2."""
    bytes_imagem: bytes
    content_type: str          # "image/png" ou o que o Gemini retornar
    texto_resposta: Optional[str] = None


# Cliente singleton — criar uma vez por processo
_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    """Retorna cliente Gemini singleton.

    Aceita ambos os formatos de credencial:
    - AIzaSy... → API key tradicional
    - AQ.Ab...  → OAuth token do AI Studio novo (formato 2025+)

    Passamos api_key EXPLICITAMENTE pra evitar que o auto-discovery
    interprete o token errado.
    """
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY (ou GOOGLE_API_KEY) não definida no ambiente. "
                "Verifique .env."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def _extrair_bytes_imagem(part) -> tuple[bytes, str]:
    """Extrai bytes brutos + mime type de um Part de imagem.

    Tenta múltiplas estratégias porque a API google-genai mudou várias vezes:
      1. part.inline_data.data (bytes brutos diretos) — formato moderno
      2. part.as_image() retornando objeto com .data ou bytes
      3. Fallback: tentar PIL.Image se for PIL puro

    Returns:
        (bytes_imagem, mime_type)
    """
    # Estratégia 1: bytes brutos diretos (mais confiável)
    if hasattr(part, "inline_data") and part.inline_data is not None:
        inline = part.inline_data
        # inline_data.data normalmente é bytes; pode ser base64-string em alguns casos
        data = getattr(inline, "data", None)
        mime = getattr(inline, "mime_type", "image/png") or "image/png"

        if isinstance(data, bytes):
            return data, mime

        if isinstance(data, str):
            # Se vier como string base64, decodifica
            import base64
            try:
                return base64.b64decode(data), mime
            except Exception:
                pass

    # Estratégia 2: as_image() — pode retornar PIL.Image OU wrapper customizado
    if hasattr(part, "as_image"):
        try:
            img_obj = part.as_image()

            # 2a: É wrapper customizado google-genai com atributo .image_bytes ou .data?
            for attr in ("image_bytes", "data", "_image_bytes"):
                if hasattr(img_obj, attr):
                    val = getattr(img_obj, attr)
                    if isinstance(val, bytes):
                        return val, "image/png"

            # 2b: Tentar .save() sem format (assinatura nova)
            buf = io.BytesIO()
            try:
                img_obj.save(buf)  # SEM format=
                return buf.getvalue(), "image/png"
            except TypeError:
                # 2c: Pode ser PIL.Image puro — tenta com format=
                buf = io.BytesIO()
                img_obj.save(buf, format="PNG")
                return buf.getvalue(), "image/png"

        except Exception as e:
            raise RuntimeError(f"Falha extraindo imagem de part.as_image(): {e}") from e

    raise RuntimeError(
        "Part de imagem não tem inline_data nem as_image() utilizável. "
        f"Atributos do part: {dir(part)}"
    )


async def gerar_gemini(
    prompt: str,
    imagem_referencia_bytes: Optional[bytes] = None,
    imagem_referencia_mime: str = "image/png",
    aspecto: str = "2:3",
    tamanho: str = "1K",
    modelo: str = "gemini-3.1-flash-image-preview",
) -> ResultadoGemini:
    """Gera imagem via Gemini Nano Banana 2.

    Args:
        prompt: Texto do prompt (PT-BR ou EN, ambos funcionam).
        imagem_referencia_bytes: Bytes da imagem canônica pra preservar identidade.
        imagem_referencia_mime: MIME type da referência ("image/png" ou "image/jpeg").
        aspecto: "2:3" (retrato padrão) | "3:2" | "1:1".
        tamanho: "512" | "1K" | "2K" (maiúscula!).
        modelo: nome do modelo. Padrão é Nano Banana 2.

    Returns:
        ResultadoGemini com bytes_imagem.

    Raises:
        RuntimeError: se modelo não gerar imagem ou bug de extração.
    """
    client = _get_client()

    # Monta lista de conteúdo: prompt + referência opcional
    conteudo: list = [prompt]
    if imagem_referencia_bytes:
        conteudo.append(
            types.Part.from_bytes(
                data=imagem_referencia_bytes,
                mime_type=imagem_referencia_mime,
            )
        )

    # response_modalities=["IMAGE"] obrigatório
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio=aspecto,
            image_size=tamanho,
        ),
    )

    response = await client.aio.models.generate_content(
        model=modelo,
        contents=conteudo,
        config=config,
    )

    # Extrai imagem da resposta
    texto_retornado: Optional[str] = None
    img_bytes: Optional[bytes] = None
    mime: str = "image/png"

    if response.parts:
        for part in response.parts:
            if part.text is not None:
                texto_retornado = part.text
            elif (
                getattr(part, "inline_data", None) is not None
                or hasattr(part, "as_image")
            ):
                try:
                    img_bytes, mime = _extrair_bytes_imagem(part)
                except RuntimeError:
                    # Continua tentando próximas parts
                    continue

    if img_bytes is None:
        finish = "UNKNOWN"
        try:
            if response.candidates:
                finish = str(getattr(response.candidates[0], "finish_reason", "UNKNOWN"))
        except Exception:
            pass
        raise RuntimeError(
            f"Gemini não gerou imagem. finish_reason={finish}. "
            f"Texto retornado: {texto_retornado or '(nenhum)'}. "
            f"Provável bloqueio de content policy — tente prefixar com "
            f"'fantasy RPG concept art' ou suavizar termos."
        )

    return ResultadoGemini(
        bytes_imagem=img_bytes,
        content_type=mime,
        texto_resposta=texto_retornado,
    )