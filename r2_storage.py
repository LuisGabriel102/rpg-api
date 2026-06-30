"""
Wrapper boto3 pra Cloudflare R2 — bucket alderyn-npcs.

DESIGN:
- boto3 e sync. Pra usar em codigo async (NiceGUI/FastAPI), envolvemos
  em asyncio.to_thread() — joga a chamada sync num thread pool sem
  bloquear o event loop.
- Cada upload gera um nome com timestamp UNICO. Versoes antigas NUNCA
  sao sobrescritas — sao apagadas explicitamente via delete_imagem().
- Validacao de tipo + tamanho aqui dentro pra falhar cedo antes de gastar
  upload bandwidth.

VARIAVEIS .env USADAS:
    R2_ACCESS_KEY_ID
    R2_SECRET_ACCESS_KEY
    R2_ENDPOINT           (https://{account_id}.r2.cloudflarestorage.com)
    R2_BUCKET             (alderyn-npcs)
    R2_PUBLIC_URL         (https://imagens.luisgabriel.uk, sem barra final)
"""

import asyncio
import os
from datetime import datetime, timezone

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, BotoCoreError
from dotenv import load_dotenv

load_dotenv()

# ====================================================================
# CONFIG — ler e validar variaveis do .env
# ====================================================================

R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_BUCKET = os.getenv("R2_BUCKET")
R2_PUBLIC_URL = (os.getenv("R2_PUBLIC_URL") or "").rstrip("/")

_VARS_OBRIGATORIAS = {
    "R2_ACCESS_KEY_ID": R2_ACCESS_KEY_ID,
    "R2_SECRET_ACCESS_KEY": R2_SECRET_ACCESS_KEY,
    "R2_ENDPOINT": R2_ENDPOINT,
    "R2_BUCKET": R2_BUCKET,
    "R2_PUBLIC_URL": R2_PUBLIC_URL,
}
_faltando = [k for k, v in _VARS_OBRIGATORIAS.items() if not v]
if _faltando:
    raise RuntimeError(
        f"Variaveis R2 faltando no .env: {_faltando}. "
        "Ver r2_storage.py pra lista completa esperada."
    )


# ====================================================================
# Validacao de upload
# ====================================================================

MIME_TIPOS_ACEITOS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
TAMANHO_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


def _validar(file_bytes: bytes, content_type: str) -> str:
    """Valida tamanho e MIME. Retorna a extensao a usar no nome do arquivo."""
    if content_type not in MIME_TIPOS_ACEITOS:
        raise ValueError(
            f"Tipo de imagem nao aceito: {content_type}. "
            f"Aceitos: {sorted(MIME_TIPOS_ACEITOS.keys())}"
        )
    tamanho = len(file_bytes)
    if tamanho > TAMANHO_MAX_BYTES:
        mb = tamanho / 1024 / 1024
        raise ValueError(
            f"Imagem tem {mb:.1f}MB. Limite e 5MB."
        )
    if tamanho < 100:
        raise ValueError("Arquivo vazio ou corrompido.")
    return MIME_TIPOS_ACEITOS[content_type]


# ====================================================================
# Cliente boto3 (singleton)
# ====================================================================

def _build_client():
    """Cria cliente S3 apontado pro R2."""
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(
            signature_version="s3v4",
            region_name="auto",  # R2 nao tem regions, mas boto3 exige algum valor
        ),
    )


_client = _build_client()


# ====================================================================
# UPLOAD
# ====================================================================

def _upload_sync(
    npc_id: int,
    file_bytes: bytes,
    content_type: str,
) -> str:
    """Upload sync — usado por asyncio.to_thread."""
    ext = _validar(file_bytes, content_type)

    # Nome unico com timestamp — multiplas versoes do mesmo NPC coexistem
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"npc_{npc_id}_{timestamp}.{ext}"

    try:
        _client.put_object(
            Bucket=R2_BUCKET,
            Key=filename,
            Body=file_bytes,
            ContentType=content_type,
            CacheControl="public, max-age=31536000, immutable",
        )
    except (ClientError, BotoCoreError) as e:
        raise RuntimeError(f"Falha ao subir pra R2: {e}") from e

    return f"{R2_PUBLIC_URL}/{filename}"


async def upload_imagem_npc(
    npc_id: int,
    file_bytes: bytes,
    content_type: str,
) -> str:
    """Faz upload de imagem de NPC pro R2 e retorna a URL publica."""
    return await asyncio.to_thread(
        _upload_sync, npc_id, file_bytes, content_type
    )


# ====================================================================
# DELETE
# ====================================================================

def _delete_sync(url: str) -> None:
    """Deleta um objeto do R2 dado sua URL publica."""
    if not url.startswith(R2_PUBLIC_URL + "/"):
        raise ValueError(f"URL nao pertence ao bucket {R2_BUCKET}: {url}")
    key = url[len(R2_PUBLIC_URL) + 1:]

    try:
        _client.delete_object(Bucket=R2_BUCKET, Key=key)
    except (ClientError, BotoCoreError) as e:
        raise RuntimeError(f"Falha ao deletar do R2: {e}") from e


async def delete_imagem(url: str) -> None:
    """Deleta uma imagem do R2 dada sua URL publica.

    Raises:
        ValueError: URL nao pertence ao bucket configurado
        RuntimeError: falha de comunicacao com R2
    """
    return await asyncio.to_thread(_delete_sync, url)


# ====================================================================
# LISTAGEM (utilitario de debug)
# ====================================================================

def _listar_versoes_sync(npc_id: int) -> list[dict]:
    """Lista todas as versoes de imagem de um NPC, mais recente primeiro."""
    prefix = f"npc_{npc_id}_"
    try:
        resp = _client.list_objects_v2(Bucket=R2_BUCKET, Prefix=prefix)
    except (ClientError, BotoCoreError) as e:
        raise RuntimeError(f"Falha ao listar R2: {e}") from e

    objetos = resp.get("Contents", [])
    return sorted(
        [
            {
                "filename": obj["Key"],
                "url": f"{R2_PUBLIC_URL}/{obj['Key']}",
                "tamanho_bytes": obj["Size"],
                "ultima_modificacao": obj["LastModified"],
            }
            for obj in objetos
        ],
        key=lambda x: x["filename"],
        reverse=True,
    )


async def listar_versoes_npc(npc_id: int) -> list[dict]:
    """Lista todas as versoes de imagem de um NPC, mais recente primeiro."""
    return await asyncio.to_thread(_listar_versoes_sync, npc_id)


# ====================================================================
# GRAVURAS (P3) — cache de imagem de cena por KEY ESTAVEL
# ====================================================================
# Diferente do upload de NPC (nome unico com timestamp), a gravura usa uma key
# ESTAVEL por conteudo (gravura.chave_gravura) pra o cache funcionar: mesma cena
# -> mesma key -> revisita = gratis. head_object confirma existencia sem baixar;
# put_object grava na key exata. Mesma credencial/cliente do upload de NPC (write).

def url_gravura(key: str) -> str:
    """URL publica da gravura dada sua key R2 (ex.: gravuras/cena/<hash>.webp)."""
    return f"{R2_PUBLIC_URL}/{key}"


def _gravura_existe_sync(key: str) -> bool:
    """True se a key ja existe no bucket (cache hit). 404 -> False. Outro erro propaga."""
    try:
        _client.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except ClientError as e:
        code = str(e.response.get("Error", {}).get("Code", ""))
        if code in ("404", "NoSuchKey", "NotFound"):
            return False
        raise
    except BotoCoreError as e:
        raise RuntimeError(f"Falha ao checar gravura no R2: {e}") from e


async def gravura_existe(key: str) -> bool:
    """Cache-first: existe a gravura dessa key no R2? (head_object, nao baixa bytes)."""
    return await asyncio.to_thread(_gravura_existe_sync, key)


def _upload_gravura_sync(key: str, file_bytes: bytes) -> str:
    """Grava a gravura (webp) na key EXATA e devolve a URL publica."""
    try:
        _client.put_object(
            Bucket=R2_BUCKET,
            Key=key,
            Body=file_bytes,
            ContentType="image/webp",
            CacheControl="public, max-age=31536000, immutable",
        )
    except (ClientError, BotoCoreError) as e:
        raise RuntimeError(f"Falha ao subir gravura pra R2: {e}") from e
    return f"{R2_PUBLIC_URL}/{key}"


async def upload_gravura(key: str, file_bytes: bytes) -> str:
    """Sobe a gravura (webp) sob a key estavel e devolve a URL publica."""
    return await asyncio.to_thread(_upload_gravura_sync, key, file_bytes)