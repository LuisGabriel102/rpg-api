"""
grep_escolas.py - Auditoria complementar: busca strings de escola no codigo local.

Busca recursivamente em .py, .sql, .json, .md pelas 6 strings de escola que
vao mudar na migracao. Ignora .venv, __pycache__, .git, node_modules, e
os proprios arquivos de pesquisa/auditoria gerados por Claude.
"""
import os
import re
from pathlib import Path

# As 6 strings que vao MUDAR
ESCOLAS_QUE_MUDAM = [
    "Abjuracao",
    "Conjuracao",
    "Divinacao",
    "Adivinhacao",
    "Evocacao",
    "Ilusao",
    "Transmutacao",
]

# Extensoes a procurar
EXTENSOES = {".py", ".sql", ".json", ".md", ".txt", ".yml", ".yaml", ".toml", ".cfg", ".ini"}

# Pastas a ignorar
IGNORAR_PASTAS = {".venv", "__pycache__", ".git", "node_modules", ".mypy_cache",
                  ".pytest_cache", "dist", "build", ".idea", ".vscode"}

# Arquivos a ignorar (ruido de pesquisa/auditoria)
IGNORAR_ARQUIVOS = {
    "pesquisa_1_personagens.py", "pesquisa_2_companheiros.py",
    "pesquisa_3_npcs.py", "pesquisa_4_mapa_completo.py",
    "pesquisa_5_modo_origem.py", "pesquisa_6_vocacoes.py",
    "pesquisa_7_estrelas_veu.py", "pesquisa_14_magia.py",
    "pesquisa_15_sessoes_tempo.py",
    "pesquisa_1_personagens.json", "pesquisa_2_companheiros.json",
    "pesquisa_3_npcs.json", "pesquisa_4_mapa_completo.json",
    "pesquisa_5_modo_origem.json", "pesquisa_6_vocacoes.json",
    "pesquisa_7_estrelas_veu.json", "pesquisa_14_magia.json",
    "pesquisa_15_sessoes_tempo.json",
    "fix_bugs_consolidado.py", "verificar_fix2.py", "auditoria_escolas.py",
    "grep_escolas.py",  # este proprio arquivo
}


def buscar_em_arquivo(caminho: Path, escolas: list) -> list:
    """Retorna lista de hits por escola nesse arquivo."""
    try:
        conteudo = caminho.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    hits = []
    for i, linha in enumerate(conteudo.split("\n"), 1):
        for escola in escolas:
            # Busca a escola como string literal (entre aspas) ou isolada
            padroes = [
                f"'{escola}'",
                f'"{escola}"',
                f"={escola}",
                f" {escola} ",
                f"={escola},",
                f"={escola})",
            ]
            if any(p in linha for p in padroes):
                hits.append({
                    "escola": escola,
                    "linha_num": i,
                    "trecho": linha.strip()[:200],
                })
                break  # evita duplicata se varias na mesma linha
    return hits


def main() -> None:
    print("=" * 72)
    print("  GREP LOCAL - Bug #4 (Escolas de Magia)")
    print("  Procura em arquivos .py .sql .json .md .txt .yml .yaml .toml")
    print("=" * 72)
    print()

    raiz = Path.cwd()
    print(f"  Raiz: {raiz}")
    print(f"  Ignorando pastas: {', '.join(sorted(IGNORAR_PASTAS))}")
    print(f"  Ignorando arquivos de pesquisa/auditoria (14 arquivos)")
    print()

    total_hits_por_escola = {e: 0 for e in ESCOLAS_QUE_MUDAM}
    total_arquivos_vistoriados = 0
    arquivos_com_hit = {}  # {escola: {arquivo: [hits]}}

    for caminho in raiz.rglob("*"):
        if not caminho.is_file():
            continue
        if caminho.suffix.lower() not in EXTENSOES:
            continue
        # Checa se alguma pasta no path é pra ignorar
        if any(parte in IGNORAR_PASTAS for parte in caminho.parts):
            continue
        if caminho.name in IGNORAR_ARQUIVOS:
            continue

        total_arquivos_vistoriados += 1
        hits = buscar_em_arquivo(caminho, ESCOLAS_QUE_MUDAM)
        if not hits:
            continue

        rel = caminho.relative_to(raiz)
        for h in hits:
            total_hits_por_escola[h["escola"]] += 1
            arquivos_com_hit.setdefault(h["escola"], {}).setdefault(str(rel), []).append(h)

    print(f"  Arquivos vistoriados: {total_arquivos_vistoriados}")
    print()

    # Relatorio por escola
    total_geral = 0
    for escola in ESCOLAS_QUE_MUDAM:
        n = total_hits_por_escola[escola]
        total_geral += n
        if n == 0:
            print(f"--- {escola}: [zero hits] ---")
            continue

        print(f"--- {escola}: {n} hit(s) ---")
        for arquivo, hits in arquivos_com_hit.get(escola, {}).items():
            print(f"  {arquivo}")
            for h in hits[:5]:
                print(f"    L{h['linha_num']:4d}: {h['trecho']}")
            if len(hits) > 5:
                print(f"    ... + {len(hits) - 5} mais")
        print()

    print("=" * 72)
    print("  SUMARIO GREP LOCAL")
    print("=" * 72)
    print(f"  Arquivos vistoriados:  {total_arquivos_vistoriados}")
    print(f"  TOTAL de hits:         {total_geral}")
    print()
    if total_geral == 0:
        print("  [ZERO HITS] Codigo local esta limpo. Opcao C eh segura aqui.")
    else:
        print("  Codigo local tem referencias hardcoded. Avaliar cada uma.")
    print()
    print("  NOTA: este grep cobre APENAS o diretorio atual.")
    print("  Se ha um projeto FastAPI separado (api.luisgabriel.uk em outro")
    print("  diretorio), ele precisa ser auditado tambem antes da Opcao C.")
    print("=" * 72)


if __name__ == "__main__":
    main()