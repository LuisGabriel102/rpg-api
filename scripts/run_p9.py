#!/usr/bin/env python3
"""
P9 Executor - Teste empirico de formato estrutural

Objetivo: rodar a MESMA cena canonica como user message contra 5 system prompts
identicos em conteudo mas com wrapper estrutural distinto (XML, Markdown, JSON,
YAML, Hibrido MD+XML). Gera 5 outputs pra pair-ranking manual.

Modelo: deepseek/deepseek-v3.2-exp via OpenRouter
Temperatura: 0.7
Max tokens: 800
Seed: 42

Pre-requisitos:
- Python 3.10+
- pip install requests python-dotenv
- Arquivo .env com OPENROUTER_API_KEY=sk-or-v1-...
- Os 5 arquivos variant_*.txt no mesmo diretorio do script

Uso:
    python run_p9.py

Saidas:
- output_variant_A_xml.txt
- output_variant_B_markdown.txt
- output_variant_C_json.txt
- output_variant_D_yaml.txt
- output_variant_E_hybrid.txt
- run_p9_log.txt (metadados: tokens, latencia, erros)

Custo estimado: ~$0.02-$0.05 no total (5 chamadas x ~3k tokens in + 800 out)

NOTA TECNICA: Todos os headers HTTP sao ASCII puro, por exigencia da lib
requests (headers HTTP sao latin-1 por padrao HTTP).
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# ================================================================
# CONFIGURACAO
# ================================================================

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_SLUG = "deepseek/deepseek-v3.2-exp"
TEMPERATURE = 0.7
MAX_TOKENS = 800
SEED = 42

# Cena canonica fixa - user message IDENTICA nas 5 execucoes
# NOTA: acentos aqui sao ok porque o body da request vai como JSON UTF-8
USER_MESSAGE = (
    "Doran Korven atravessa a Praca 4 Bandeiras ao entardecer. "
    "Tier 1 Euforia ativo, tag hemomantic dominante. "
    "Narre o momento em que ele cruza a praca e percebe algo fora do comum, "
    "em 300-500 palavras, 3a pessoa, registro literario PT-BR. "
    "NPCs presentes: nenhum nomeado. Clima: chuva fina."
)

VARIANTS = [
    ("A", "variant_A_xml.txt", "output_variant_A_xml.txt"),
    ("B", "variant_B_markdown.txt", "output_variant_B_markdown.txt"),
    ("C", "variant_C_json.txt", "output_variant_C_json.txt"),
    ("D", "variant_D_yaml.txt", "output_variant_D_yaml.txt"),
    ("E", "variant_E_hybrid.txt", "output_variant_E_hybrid.txt"),
]

# ================================================================
# HELPERS
# ================================================================

def load_env():
    """Carrega OPENROUTER_API_KEY do .env ou do ambiente."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("[AVISO] python-dotenv nao instalado. Tentando ambiente direto.")

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("[ERRO] OPENROUTER_API_KEY nao encontrada.")
        print("Crie um arquivo .env com: OPENROUTER_API_KEY=sk-or-v1-...")
        sys.exit(1)
    return api_key


def read_system_prompt(path: Path) -> str:
    """Le o conteudo do arquivo variant_*.txt em UTF-8."""
    if not path.exists():
        print(f"[ERRO] Arquivo nao encontrado: {path}")
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def call_openrouter(api_key: str, system_prompt: str, user_message: str) -> dict:
    """
    Chama OpenRouter com o system prompt e user message.
    Retorna dict com 'text', 'usage', 'latency', 'error' (se houver).

    IMPORTANTE: Headers HTTP sao ASCII puro. O body JSON aceita UTF-8 normalmente.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json; charset=utf-8",
        "HTTP-Referer": "https://oficina.luisgabriel.uk",
        "X-Title": "Alderyn P9 Test",
    }

    payload = {
        "model": MODEL_SLUG,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "seed": SEED,
    }

    start = time.time()
    try:
        # Forca o body a ser encodado como UTF-8 explicitamente
        body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            data=body_bytes,
            timeout=120,
        )
        latency = time.time() - start

        if response.status_code != 200:
            return {
                "text": "",
                "usage": {},
                "latency": latency,
                "error": f"HTTP {response.status_code}: {response.text[:500]}",
            }

        data = response.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return {
            "text": text,
            "usage": usage,
            "latency": latency,
            "error": None,
        }

    except requests.exceptions.Timeout:
        return {
            "text": "",
            "usage": {},
            "latency": time.time() - start,
            "error": "TIMEOUT apos 120s",
        }
    except Exception as e:
        return {
            "text": "",
            "usage": {},
            "latency": time.time() - start,
            "error": f"EXCECAO: {type(e).__name__}: {str(e)[:500]}",
        }


def run_variant(api_key: str, variant_id: str, input_path: Path, output_path: Path) -> dict:
    """Executa uma variante e salva o output. Retorna metadados."""
    print(f"\n[VARIANTE {variant_id}] Lendo {input_path.name}...")
    system_prompt = read_system_prompt(input_path)
    prompt_chars = len(system_prompt)
    print(f"[VARIANTE {variant_id}] System prompt: {prompt_chars} chars (~{prompt_chars // 4} tokens est.)")

    print(f"[VARIANTE {variant_id}] Chamando OpenRouter ({MODEL_SLUG})...")
    result = call_openrouter(api_key, system_prompt, USER_MESSAGE)

    if result["error"]:
        print(f"[VARIANTE {variant_id}] [ERRO]: {result['error']}")
        output_path.write_text(
            f"ERRO NA EXECUCAO\n\n{result['error']}\n\nLatencia: {result['latency']:.2f}s\n",
            encoding="utf-8",
        )
    else:
        print(f"[VARIANTE {variant_id}] [OK] - latencia {result['latency']:.2f}s")
        print(f"[VARIANTE {variant_id}] Usage: {json.dumps(result['usage'])}")
        output_path.write_text(result["text"], encoding="utf-8")
        print(f"[VARIANTE {variant_id}] Output salvo em {output_path.name}")

    return {
        "variant": variant_id,
        "input_file": input_path.name,
        "output_file": output_path.name,
        "prompt_chars": prompt_chars,
        "latency_seconds": result["latency"],
        "usage": result["usage"],
        "error": result["error"],
        "output_chars": len(result["text"]),
    }


# ================================================================
# MAIN
# ================================================================

def main():
    print("=" * 70)
    print("P9 Executor - Teste empirico de formato estrutural")
    print(f"Modelo: {MODEL_SLUG}")
    print(f"Temperatura: {TEMPERATURE} | Max tokens: {MAX_TOKENS} | Seed: {SEED}")
    print(f"Data: {datetime.now().isoformat(timespec='seconds')}")
    print("=" * 70)

    api_key = load_env()
    script_dir = Path(__file__).parent.resolve()

    results = []
    for variant_id, input_name, output_name in VARIANTS:
        input_path = script_dir / input_name
        output_path = script_dir / output_name
        result = run_variant(api_key, variant_id, input_path, output_path)
        results.append(result)

    # Log final
    log_path = script_dir / "run_p9_log.txt"
    with log_path.open("w", encoding="utf-8") as f:
        f.write(f"P9 Run Log - {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"Modelo: {MODEL_SLUG} | Temp: {TEMPERATURE} | Max tokens: {MAX_TOKENS} | Seed: {SEED}\n")
        f.write(f"User message: {USER_MESSAGE}\n\n")
        f.write("=" * 70 + "\n")
        f.write(f"{'Variant':<8} {'PromptChars':<12} {'OutChars':<10} {'Latency':<10} {'Usage':<30} {'Error':<20}\n")
        f.write("-" * 70 + "\n")
        for r in results:
            usage_str = f"in={r['usage'].get('prompt_tokens', '?')} out={r['usage'].get('completion_tokens', '?')}"
            err_str = r["error"][:20] if r["error"] else "OK"
            f.write(f"{r['variant']:<8} {r['prompt_chars']:<12} {r['output_chars']:<10} "
                    f"{r['latency_seconds']:<10.2f} {usage_str:<30} {err_str:<20}\n")
        f.write("\n")

        # Custo estimado
        total_in = sum(r["usage"].get("prompt_tokens", 0) for r in results)
        total_out = sum(r["usage"].get("completion_tokens", 0) for r in results)
        cost_est = (total_in * 0.27 / 1_000_000) + (total_out * 1.10 / 1_000_000)
        f.write(f"Total tokens: in={total_in} out={total_out}\n")
        f.write(f"Custo estimado: ~${cost_est:.4f}\n")

    print("\n" + "=" * 70)
    print("[CONCLUIDO]")
    print(f"Outputs em: {script_dir}")
    print(f"Log em: {log_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
