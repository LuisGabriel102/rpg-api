"""
glossario_alderyn.py
─────────────────────
Trava de nomes canônicos (name-hashing) para o pipeline utilitário do Alderyn.

Esconde os nomes do mundo (Executor, Vigília Quebrada, Valdren...) atrás de
placeholders ANTES de mandar texto pro modelo barato, e restaura DEPOIS.
O modelo nunca vê o nome real — então não tem o que traduzir nem corromper.

É CÓDIGO, não pedido no prompt. Trava determinística, não promessa.

Uso em 3 linhas:
    g = Glossario()
    g.carregar_de_pares(pares_vindos_do_banco)   # uma vez, no startup
    texto_seguro = g.mascarar(texto)             # antes do modelo
    texto_final  = g.desmascarar(resposta)       # depois do modelo
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field

# Delimitadores raros em prosa pt-BR e seguros dentro de JSON.
# Se algum modelo "limpar" unicode, troque por "[[" / "]]" e recompile.
ABRE = "⟦"   # ⟦
FECHA = "⟧"  # ⟧


@dataclass
class Glossario:
    case_sensitive: bool = True
    _por_nome: dict = field(default_factory=dict)
    _por_nome_ci: dict = field(default_factory=dict)
    _por_placeholder: dict = field(default_factory=dict)
    _re_mascarar: "re.Pattern | None" = None
    _re_desmascarar: "re.Pattern | None" = None

    # ── montar o glossário ───────────────────────────────────────────
    def registrar(self, tipo, id_canonico, nome) -> None:
        """Registra um nome canônico. tipo + id viram o placeholder (ex.: ⟦NPC_44⟧)."""
        nome = (nome or "").strip()
        if len(nome) < 3:          # nomes de 1-2 letras geram ruído; ignore
            return
        ph = f"{ABRE}{tipo}_{id_canonico}{FECHA}"
        self._por_nome[nome] = ph
        self._por_nome_ci[nome.lower()] = ph
        self._por_placeholder[ph] = nome

    def carregar_de_pares(self, pares) -> None:
        """pares = iterável de (tipo, id_canonico, nome). Vem do banco."""
        for tipo, id_canonico, nome in pares:
            self.registrar(tipo, id_canonico, nome)
        self.compilar()

    def compilar(self) -> None:
        nomes = sorted(self._por_nome, key=len, reverse=True)   # longest-first
        if not nomes:
            self._re_mascarar = None
            self._re_desmascarar = None
            return
        corpo = "|".join(re.escape(n) for n in nomes)
        # (?<!\w)...(?!\w): não pega nome dentro de palavra maior (Valdren ⊄ Valdrenia)
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._re_mascarar = re.compile(rf"(?<!\w)(?:{corpo})(?!\w)", flags)
        phs = "|".join(re.escape(p) for p in self._por_placeholder)
        self._re_desmascarar = re.compile(phs)

    # ── usar ─────────────────────────────────────────────────────────
    def mascarar(self, texto: str) -> str:
        if not self._re_mascarar:
            return texto
        def troca(m):
            achado = m.group(0)
            return (self._por_nome[achado] if self.case_sensitive
                    else self._por_nome_ci[achado.lower()])
        return self._re_mascarar.sub(troca, texto)

    def desmascarar(self, texto: str) -> str:
        if not self._re_desmascarar:
            return texto
        return self._re_desmascarar.sub(lambda m: self._por_placeholder[m.group(0)], texto)

    # ── auditoria ────────────────────────────────────────────────────
    def placeholders_orfaos(self, texto: str) -> list:
        """Placeholders no texto que NÃO estão no glossário (modelo inventou/quebrou).
        Rode isso na SAÍDA do modelo. Se vier algo, logue — é sinal de corrupção."""
        achados = re.findall(rf"{re.escape(ABRE)}.*?{re.escape(FECHA)}", texto)
        return [a for a in achados if a not in self._por_placeholder]


# ─────────────────────────────────────────────────────────────────────
# LOADER DO BANCO — TEMPLATE. NÃO está pronto: faltam os nomes reais das
# colunas. Rode a query diagnóstica (no chat) primeiro, confirme as colunas,
# e só então preencha <COLUNA_NOME> de cada tabela canônica.
#
# Tabelas canônicas (entram): npcs, regions, locations, geographic_features,
#   continents, ref_vocacoes, ref_namespace_vocacoes
# Lixo D&D (NÃO entra): ref_npcs_historicos, ref_racas, ref_itens,
#   ref_criaturas, ref_backgrounds
# ─────────────────────────────────────────────────────────────────────
def carregar_do_banco(conn) -> "Glossario":
    """Exemplo de loader. Ajuste cada (tabela, coluna) após o diagnóstico."""
    fontes = [
        # (tipo,   tabela,                  coluna_nome)
        ("NPC",    "npcs",                  "<COLUNA_NOME>"),
        ("REG",    "regions",               "<COLUNA_NOME>"),
        ("LOC",    "locations",             "<COLUNA_NOME>"),
        ("GEO",    "geographic_features",   "<COLUNA_NOME>"),
        ("CONT",   "continents",            "<COLUNA_NOME>"),
        ("VOC",    "ref_vocacoes",          "<COLUNA_NOME>"),
    ]
    g = Glossario()
    pares = []
    with conn.cursor() as cur:
        for tipo, tabela, col in fontes:
            cur.execute(f'SELECT id, "{col}" FROM {tabela} WHERE "{col}" IS NOT NULL')
            for id_canonico, nome in cur.fetchall():
                pares.append((tipo, id_canonico, nome))
    g.carregar_de_pares(pares)
    return g


# ─────────────────────────────────────────────────────────────────────
# EXEMPLO — roda sozinho, sem banco. python3 glossario_alderyn.py
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    g = Glossario()
    g.carregar_de_pares([
        ("NPC",   44, "Executor"),
        ("ERA",    1, "Vigília Quebrada"),
        ("LOC",   12, "Valdren"),
        ("PILAR",  2, "Sombra"),
    ])

    original = "O Executor caçou algo na Vigília Quebrada, perto de Valdren."
    masc = g.mascarar(original)
    volta = g.desmascarar(masc)

    print("original:  ", original)
    print("mascarado: ", masc)
    print("restaurado:", volta)
    assert volta == original, "FALHA: round-trip não bateu"
    print("round-trip OK")
