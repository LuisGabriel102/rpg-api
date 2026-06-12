"""
Teste end-to-end do pipeline de geração — Catedral do Alderyn (Parte 4.6.3).

Uso:
    python testar_pipeline.py              # Almareth (id=33), Gemini primário
    python testar_pipeline.py 11           # Doran (id=11), Gemini primário
    python testar_pipeline.py 33 gpt       # Almareth, força GPT primário
    python testar_pipeline.py 33 flux      # Almareth, força FLUX primário

O que faz:
    1. Carrega NPC do banco
    2. Monta prompt (com Gemini template)
    3. Chama API IA (com fallback automático)
    4. Sobe pro R2 Cloudflare
    5. Persiste em npc_imagens (status='rascunho')
    6. Audita em npc_prompts_gerados
    7. Mostra resumo + URL pública pra abrir no navegador

Este teste valida o pipeline COMPLETO de produção.
Diferente do testar_geradores.py (Parte 4.6.2) que só salvava local,
este integra com R2 + banco.

Pré-requisitos:
    - .env com FAL_KEY, GEMINI_API_KEY, OPENAI_API_KEY, DATABASE_URL, R2_*
    - Migration 4.6 aplicada (status, npc_prompts_gerados, etc)
    - pip install -r requirements_4_6.txt
    - geradores_imagem/ no lugar (não solto na raiz!)
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Carrega .env automaticamente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for linha in env_path.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                k, _, v = linha.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

# Imports após carregar .env
from pipeline_geracao import (
    gerar_imagem_npc,
    ORDEM_FALLBACK,
    PRECO_POR_GERACAO,
)


# Mapa argumento CLI → ordem de modelos
ORDEM_PRESETS = {
    "gemini": ("gemini_nano", "gpt_image", "flux_kontext"),  # padrão
    "gpt":    ("gpt_image", "gemini_nano", "flux_kontext"),
    "flux":   ("flux_kontext", "gemini_nano", "gpt_image"),
}


async def main() -> int:
    # Parse args
    npc_id = 33  # Almareth default
    modelos = ORDEM_FALLBACK

    if len(sys.argv) >= 2:
        try:
            npc_id = int(sys.argv[1])
        except ValueError:
            print(f"❌ npc_id inválido: {sys.argv[1]}")
            return 1

    if len(sys.argv) >= 3:
        preset = sys.argv[2].lower()
        if preset not in ORDEM_PRESETS:
            print(f"❌ Preset inválido: {preset}. Use: {list(ORDEM_PRESETS.keys())}")
            return 1
        modelos = ORDEM_PRESETS[preset]

    print("=" * 70)
    print("CATEDRAL DO ALDERYN — Pipeline E2E (Parte 4.6.3)")
    print("=" * 70)
    print(f"  NPC id:          {npc_id}")
    print(f"  Modelos (ordem): {' → '.join(modelos)}")
    print(f"  Modelo primário: {modelos[0]} (${PRECO_POR_GERACAO[modelos[0]]:.3f})")
    print("=" * 70)
    print()

    print("⏳ Rodando pipeline (carregar → prompt → API → R2 → banco)...")
    print()

    resultado = await gerar_imagem_npc(
        npc_id=npc_id,
        rotulo="Teste E2E Parte 4.6.3",
        modelos_preferidos=modelos,
        usar_referencia_canonica=True,
    )

    # Resumo
    print()
    print("=" * 70)
    print("RESULTADO")
    print("=" * 70)

    if resultado.status == "success":
        print(f"  ✅ STATUS: SUCESSO")
        print()
        print(f"  Modelo usado:        {resultado.modelo_usado}")
        if len(resultado.modelos_tentados) > 1:
            print(f"  Modelos tentados:    {' → '.join(resultado.modelos_tentados)}")
            print(f"                       (fallback ativou)")
        print(f"  Custo:               ${resultado.custo_usd:.3f}")
        print()
        print(f"  Tempo geração:       {resultado.duracao_geracao_ms / 1000:.1f}s")
        print(f"  Tempo upload R2:     {resultado.duracao_upload_ms / 1000:.1f}s")
        print(f"  Tempo total:         {resultado.duracao_total_ms / 1000:.1f}s")
        print()
        print(f"  📦 Imagem ID (BD):   {resultado.imagem_id}")
        print(f"  📋 Prompt log ID:    {resultado.prompt_log_id}")
        print(f"  🌐 URL pública:")
        print(f"     {resultado.url_imagem}")
        print()
        print(f"  💡 Status no banco:  'rascunho'")
        print(f"     Pra promover pra canônica: UPDATE npc_imagens SET status='canonica' WHERE id={resultado.imagem_id};")
        print(f"     (mas isso vai ser feito pela UI no Ateliê — Parte 4.6.4)")

    else:
        print(f"  ❌ STATUS: FALHOU")
        print()
        print(f"  Estágio que falhou:  {resultado.estagio_falha}")
        print(f"  Mensagem:            {resultado.mensagem_erro}")
        print()
        if resultado.modelos_tentados:
            print(f"  Modelos tentados:    {' → '.join(resultado.modelos_tentados)}")
        print(f"  Tempo total:         {resultado.duracao_total_ms / 1000:.1f}s")
        print()
        print(f"  💡 Auditoria registrada em npc_prompts_gerados.")
        print(f"     Query: SELECT * FROM npc_prompts_gerados ORDER BY id DESC LIMIT 5;")

    print("=" * 70)

    return 0 if resultado.status == "success" else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
