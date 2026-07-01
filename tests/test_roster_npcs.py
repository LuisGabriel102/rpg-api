# -*- coding: utf-8 -*-
"""
PROVA — roster [NPCs em cena] no bloco [ESTADO].

Sem banco de producao, sem id 8: prova a logica pura (formatter) e o caminho query->linha
(via sessao FAKE). Confirma:
  - com NPCs ligados ao local -> a linha 'NPCs em cena: id=Nome, id=Nome' aparece;
  - sem NPCs -> a linha SOME (None), nao escreve rotulo vazio;
  - erro de banco -> None (o [ESTADO] nunca quebra por causa do roster).
"""
import asyncio

import jogo


# ------------------------------------------------------------- formatter puro

def test_linha_com_npcs():
    linha = jogo._linha_npcs_em_cena([{"nid": 41, "nnome": "Elara"}, {"nid": 12, "nnome": "Bruno"}])
    assert linha == "NPCs em cena: 41=Elara, 12=Bruno"


def test_linha_vazia_vira_none():
    assert jogo._linha_npcs_em_cena([]) is None
    assert jogo._linha_npcs_em_cena(None) is None


def test_linha_pula_id_ou_nome_ausente():
    linha = jogo._linha_npcs_em_cena([
        {"nid": 7, "nnome": "Kael"},
        {"nid": None, "nnome": "sem id"},   # pula
        {"nid": 9, "nnome": "   "},          # nome vazio -> pula
    ])
    assert linha == "NPCs em cena: 7=Kael"


def test_nome_com_quebra_de_linha_colapsa():
    # _uma_linha nunca deixa o nome partir o [ESTADO]
    linha = jogo._linha_npcs_em_cena([{"nid": 3, "nnome": "Doran\nda\tEstrada"}])
    assert linha == "NPCs em cena: 3=Doran da Estrada"
    assert "\n" not in linha


# ------------------------------------------------------------- query -> linha (sessao FAKE)

class _FakeResult:
    def __init__(self, rows): self._rows = rows
    def mappings(self): return self
    def all(self): return self._rows


class _FakeSession:
    def __init__(self, rows=None, erro=None):
        self._rows = rows or []
        self._erro = erro
    async def execute(self, *a, **k):
        if self._erro:
            raise self._erro
        return _FakeResult(self._rows)


def test_roster_query_com_npcs():
    s = _FakeSession(rows=[{"nid": 41, "nnome": "Elara"}, {"nid": 12, "nnome": "Bruno"}])
    linha = asyncio.run(jogo._roster_npcs_em_cena(s, 3))   # id 3 (Doran, boneco de teste)
    assert linha == "NPCs em cena: 41=Elara, 12=Bruno"


def test_roster_query_sem_npcs_some():
    s = _FakeSession(rows=[])
    assert asyncio.run(jogo._roster_npcs_em_cena(s, 3)) is None


def test_roster_query_erro_nao_quebra():
    s = _FakeSession(erro=RuntimeError("banco caiu"))
    assert asyncio.run(jogo._roster_npcs_em_cena(s, 3)) is None   # degrada -> None, sem levantar


# ------------------------------------------------------------- guarda de tabela (regressao)

def test_sql_junta_por_ref_locais_npcs_nao_location_npcs():
    """O local da campanha (campanha_estado_atual.local_atual_id) e FK de ref_locais, entao o
    roster TEM que juntar por ref_locais_npcs. location_npcs (FK locations) traria vazio/errado.
    Guarda contra reverter pra tabela errada."""
    sql = jogo._SQL_NPCS_CENA
    assert "ref_locais_npcs" in sql
    assert "location_npcs" not in sql
    assert "rln.local_id = ce.local_atual_id" in sql
    assert "n.id = rln.npc_id" in sql
