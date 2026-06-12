"""
Script de teste dos 3 adapters de geração de imagem — Parte 4.6.2
Catedral do Alderyn — Sistema Nexus

Uso:
    python testar_geradores.py            # Roda os 3 modelos
    python testar_geradores.py flux       # Só FLUX
    python testar_geradores.py gemini     # Só Gemini
    python testar_geradores.py gpt        # Só GPT

O que faz:
    1. Lê dados do Almareth (NPC id=33) DIRETO do banco Neon
    2. Monta o prompt em inglês usando a âncora de identidade
    3. Chama as 3 APIs em sequência
    4. Salva PNGs em ./almareth_<modelo>.png
    5. Mostra custo total + tempo de cada um

Pré-requisitos:
    - .env com FAL_KEY, GEMINI_API_KEY, OPENAI_API_KEY, DATABASE_URL
    - Migration 4.6 aplicada (Almareth com âncora preenchida)
    - pip install -r requirements_4_6.txt
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

# Carrega .env automaticamente (mesmo padrão dos módulos anteriores)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv não instalado. Lendo .env manualmente...")
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for linha in env_path.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                k, _, v = linha.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

# Imports locais (após carregar .env)
from gerador_prompt_imagem import (
    montar_prompt_completo,
    de_dict_npc,
)


# Custos atualizados (Pesquisa 3) — em USD
PRECO_POR_GERACAO = {
    "flux_kontext": 0.04,
    "gemini_nano":  0.067,  # 1K
    "gpt_image":    0.034,  # medium
}


# =============================================================================
# Função pra ler Almareth do banco
# =============================================================================

async def ler_almareth_do_banco() -> dict:
    """Lê dados do Almareth (id=33) diretamente do banco via asyncpg."""
    import asyncpg

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise RuntimeError("DATABASE_URL não definida no .env")

    # Converte URL do SQLAlchemy pra formato asyncpg puro
    # postgresql+asyncpg://... → postgresql://...
    db_url_pure = db_url.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(
        db_url_pure,
        statement_cache_size=0,  # Compatível com Neon pooler
    )
    try:
        row = await conn.fetchrow(
            """
            SELECT id, nome, descricao_ancora_pt, descricao_ancora_en,
                   wardrobe_padrao, iluminacao_tematica, postura_canonica
            FROM npcs
            WHERE id = 33
            """
        )
        if not row:
            raise RuntimeError("Almareth (id=33) não encontrado no banco. Migration 4.6 rodou?")
        return dict(row)
    finally:
        await conn.close()


# =============================================================================
# Função pra ler URL canônica do Almareth (pra usar como referência no FLUX)
# =============================================================================

async def ler_url_canonica_almareth() -> str | None:
    """Busca a URL da imagem canônica do Almareth no R2 (se houver)."""
    import asyncpg

    db_url = os.environ.get("DATABASE_URL", "").replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    conn = await asyncpg.connect(db_url, statement_cache_size=0)
    try:
        # Tenta primeiro a coluna `url` (4.5) e depois imagem_url (4.4)
        url = await conn.fetchval(
            """
            SELECT url FROM npc_imagens
            WHERE npc_id = 33 AND status = 'canonica'
            ORDER BY criado_em DESC
            LIMIT 1
            """
        )
        return url
    finally:
        await conn.close()


# =============================================================================
# Funções de teste de cada modelo
# =============================================================================

async def testar_flux(prompt_flux: str, url_referencia: str | None) -> tuple[bytes | None, float, str]:
    """Roda FLUX Kontext. Retorna (bytes_imagem, duracao_segundos, status_msg)."""
    from geradores_imagem.gerador_flux import gerar_flux_kontext

    print(f"\n  🎨 [FLUX] Chamando fal.ai...")
    if url_referencia:
        print(f"     Usando referência: {url_referencia[:60]}...")
    else:
        print(f"     Sem referência (text-to-image)")

    t0 = time.perf_counter()
    try:
        resultado = await gerar_flux_kontext(
            prompt=prompt_flux,
            imagem_referencia_url=url_referencia,
            aspecto="2:3",
            formato="jpeg",
        )
        duracao = time.perf_counter() - t0
        print(f"     ✅ OK em {duracao:.1f}s ({resultado.largura}x{resultado.altura})")
        if resultado.nsfw_detectado:
            print(f"     ⚠️  NSFW flag detectado pela API")
        return resultado.bytes_imagem, duracao, "ok"
    except Exception as e:
        duracao = time.perf_counter() - t0
        print(f"     ❌ FALHOU em {duracao:.1f}s: {type(e).__name__}: {e}")
        return None, duracao, str(e)


async def testar_gemini(prompt_gemini: str, ref_bytes: bytes | None) -> tuple[bytes | None, float, str]:
    """Roda Gemini Nano Banana 2."""
    from geradores_imagem.gerador_gemini import gerar_gemini

    print(f"\n  🎨 [GEMINI] Chamando Google AI...")
    if ref_bytes:
        print(f"     Usando referência: {len(ref_bytes)} bytes")
    else:
        print(f"     Sem referência (geração do zero)")

    t0 = time.perf_counter()
    try:
        resultado = await gerar_gemini(
            prompt=prompt_gemini,
            imagem_referencia_bytes=ref_bytes,
            aspecto="2:3",
            tamanho="1K",
        )
        duracao = time.perf_counter() - t0
        print(f"     ✅ OK em {duracao:.1f}s ({len(resultado.bytes_imagem)} bytes PNG)")
        if resultado.texto_resposta:
            print(f"     💬 Texto retornado: {resultado.texto_resposta[:100]}...")
        return resultado.bytes_imagem, duracao, "ok"
    except Exception as e:
        duracao = time.perf_counter() - t0
        print(f"     ❌ FALHOU em {duracao:.1f}s: {type(e).__name__}: {e}")
        return None, duracao, str(e)


async def testar_gpt(prompt_gpt: str) -> tuple[bytes | None, float, str]:
    """Roda GPT Image 1.5."""
    from geradores_imagem.gerador_gpt import gerar_gpt

    print(f"\n  🎨 [GPT] Chamando OpenAI...")
    print(f"     Geração do zero (qualidade=medium, 1024x1536)")

    t0 = time.perf_counter()
    try:
        resultado = await gerar_gpt(
            prompt=prompt_gpt,
            qualidade="medium",
            tamanho="1024x1536",  # 2:3 retrato
            formato="png",
        )
        duracao = time.perf_counter() - t0
        print(f"     ✅ OK em {duracao:.1f}s ({len(resultado.bytes_imagem)} bytes)")
        if resultado.prompt_revisado:
            print(f"     📝 GPT reescreveu o prompt (não desabilitável)")
        return resultado.bytes_imagem, duracao, "ok"
    except Exception as e:
        duracao = time.perf_counter() - t0
        print(f"     ❌ FALHOU em {duracao:.1f}s: {type(e).__name__}: {e}")
        return None, duracao, str(e)


# =============================================================================
# Main
# =============================================================================

async def main() -> int:
    # Decide quais modelos rodar
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    rodar = {
        "flux":   arg in ("all", "flux"),
        "gemini": arg in ("all", "gemini"),
        "gpt":    arg in ("all", "gpt"),
    }

    print("=" * 70)
    print("CATEDRAL DO ALDERYN — Teste de adapters de geração (Parte 4.6.2)")
    print("=" * 70)

    # 1. Ler Almareth do banco
    print("\n[1/4] Lendo Almareth (id=33) do banco...")
    try:
        npc = await ler_almareth_do_banco()
        print(f"      ✅ {npc['nome']} encontrado")
        print(f"      Âncora EN: {len(npc['descricao_ancora_en'] or '')} chars")
    except Exception as e:
        print(f"      ❌ Falhou: {e}")
        return 1

    # 2. Buscar URL canônica (se houver) — usada como referência no FLUX
    print("\n[2/4] Buscando imagem canônica do Almareth no R2...")
    try:
        url_canonica = await ler_url_canonica_almareth()
        if url_canonica:
            print(f"      ✅ Canônica encontrada: {url_canonica}")
        else:
            print(f"      ⚠️  Sem canônica — FLUX rodará text-to-image")
    except Exception as e:
        print(f"      ⚠️  Erro ao buscar canônica: {e}")
        url_canonica = None

    # 3. Montar os 3 prompts
    print("\n[3/4] Montando prompts pros 3 modelos...")
    dados = de_dict_npc(npc)
    prompts = {}
    for modelo in ("flux_kontext", "gemini_nano", "gpt_image"):
        prompts[modelo] = montar_prompt_completo(dados, modelo)
        print(f"      ✅ {modelo}: {len(prompts[modelo])} chars")

    # 4. Rodar geração nos 3 modelos
    print("\n[4/4] Rodando gerações...")
    output_dir = Path(__file__).parent
    resultados: dict = {}

    # Baixar canônica como bytes (pro Gemini que precisa em memória)
    ref_bytes: bytes | None = None
    if url_canonica and rodar["gemini"]:
        try:
            import httpx
            print(f"\n  📥 Baixando canônica pra usar como referência no Gemini...")
            async with httpx.AsyncClient(timeout=20) as http:
                resp = await http.get(url_canonica)
                resp.raise_for_status()
                ref_bytes = resp.content
                print(f"     ✅ {len(ref_bytes)} bytes baixados")
        except Exception as e:
            print(f"     ⚠️  Falhou ao baixar canônica: {e}")

    # FLUX
    if rodar["flux"]:
        bytes_img, duracao, status = await testar_flux(prompts["flux_kontext"], url_canonica)
        if bytes_img:
            out_path = output_dir / "almareth_flux.jpg"
            out_path.write_bytes(bytes_img)
            print(f"     💾 Salvo: {out_path}")
        resultados["flux_kontext"] = (status, duracao, PRECO_POR_GERACAO["flux_kontext"] if bytes_img else 0)

    # Gemini
    if rodar["gemini"]:
        bytes_img, duracao, status = await testar_gemini(prompts["gemini_nano"], ref_bytes)
        if bytes_img:
            out_path = output_dir / "almareth_gemini.png"
            out_path.write_bytes(bytes_img)
            print(f"     💾 Salvo: {out_path}")
        resultados["gemini_nano"] = (status, duracao, PRECO_POR_GERACAO["gemini_nano"] if bytes_img else 0)

    # GPT
    if rodar["gpt"]:
        bytes_img, duracao, status = await testar_gpt(prompts["gpt_image"])
        if bytes_img:
            out_path = output_dir / "almareth_gpt.png"
            out_path.write_bytes(bytes_img)
            print(f"     💾 Salvo: {out_path}")
        resultados["gpt_image"] = (status, duracao, PRECO_POR_GERACAO["gpt_image"] if bytes_img else 0)

    # Sumário final
    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)
    custo_total = 0.0
    sucessos = 0
    for modelo, (status, duracao, custo) in resultados.items():
        ok = status == "ok"
        emoji = "✅" if ok else "❌"
        print(f"  {emoji} {modelo:15} | {duracao:5.1f}s | ${custo:.3f} | {status if not ok else 'sucesso'}")
        if ok:
            sucessos += 1
        custo_total += custo

    print(f"\n  Total: {sucessos}/{len(resultados)} sucessos | Custo: ${custo_total:.3f}")
    print(f"  Imagens salvas em: {output_dir}/")
    print("=" * 70)

    return 0 if sucessos == len(resultados) else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
