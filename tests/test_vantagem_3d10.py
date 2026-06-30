"""PASSO 2 — rede de teste ANTES (vantagem/desvantagem 3d10).

Testa a FUNCAO PURA `rolar_resolucao(modo, rng)` da camada de resolucao:
  - normal      -> chama rng() 2x, retorna (d1,d2) na ORDEM de hoje (sem reordenar)
  - vantagem    -> chama rng() 3x, descarta o MENOR, retorna os 2 restantes em ordem original
  - desvantagem -> chama rng() 3x, descarta o MAIOR, retorna os 2 restantes em ordem original

Metodo (travado pelo Op): rng e injetado DIRETO (fake iterador), sem monkeypatch
de namespace. Cada caso asserta (a) o par devolvido e (b) classificar_faixa sobre
esse par (mod=0, cd=10). `classificar_faixa` ja detecta Kokusen/Refluxo sobre os 2
dados recebidos -> os criticos dos 3 modos saem sem tocar nela.

NOTA: este arquivo DEVE FALHAR contra o codigo atual (rolar_resolucao ainda nao
existe). A capacidade chega no PASSO 3.
"""
import pytest

from app.resolucao_2d10 import classificar_faixa, rolar_resolucao


def _fake_rng(*valores):
    """Devolve um callable que entrega `valores` em ordem e conta as chamadas.
    Aceita quaisquer args (espelha random.randint(1, 10)) e ignora-os."""
    it = iter(valores)

    def rng(*_args, **_kwargs):
        rng.chamadas += 1
        return next(it)

    rng.chamadas = 0
    return rng


# (modo, sequencia_rng, par_esperado, faixa_esperada)
CASOS = [
    ("normal",      (3, 7),      (3, 7),   "sucesso_parcial"),  # byte-neutro: so 2 chamadas
    ("vantagem",    (3, 7, 9),   (7, 9),   "sucesso"),
    ("desvantagem", (3, 7, 9),   (3, 7),   "sucesso_parcial"),
    ("vantagem",    (10, 10, 5), (10, 10), "sucesso_critico"),  # Kokusen
    ("vantagem",    (10, 5, 5),  (10, 5),  "sucesso"),          # so um 10 entre os escolhidos
    ("desvantagem", (1, 1, 8),   (1, 1),   "falha_critica"),    # Refluxo
    ("desvantagem", (1, 8, 8),   (1, 8),   "falha"),
    ("vantagem",    (1, 1, 1),   (1, 1),   "falha_critica"),    # borda: vantagem ainda falha feio
    ("desvantagem", (10, 10, 10),(10, 10), "sucesso_critico"),  # borda: desvantagem ainda crita
]


@pytest.mark.parametrize("modo,seq,par,faixa", CASOS)
def test_rolar_resolucao_par_e_faixa(modo, seq, par, faixa):
    rng = _fake_rng(*seq)
    d1, d2 = rolar_resolucao(modo, rng=rng)
    assert (d1, d2) == par
    assert classificar_faixa(d1, d2, 0, 10) == faixa


def test_normal_consome_rng_exatamente_2x():
    """Byte-neutralidade: 'normal' nao pode rolar um 3o dado."""
    rng = _fake_rng(3, 7)
    rolar_resolucao("normal", rng=rng)
    assert rng.chamadas == 2
