"""Testes com Hypothesis para validar formulas RPG."""

from hypothesis import given, strategies as st, assume
from app.dice import roll, roll_ability_check, roll_damage, roll_save


# === Testes de propriedade: dados nunca produzem resultados impossiveis ===

@given(sides=st.integers(min_value=1, max_value=100))
def test_single_die_in_range(sides):
    """Um dado de N lados sempre produz resultado entre 1 e N."""
    result = roll(f"1d{sides}")
    assert not result.get("error")
    assert 1 <= result["total"] <= sides


@given(num_dice=st.integers(min_value=1, max_value=20),
       sides=st.integers(min_value=1, max_value=20))
def test_multiple_dice_in_range(num_dice, sides):
    """NdS sempre produz resultado entre N e N*S."""
    result = roll(f"{num_dice}d{sides}")
    assert not result.get("error")
    assert num_dice <= result["total"] <= num_dice * sides


@given(modifier=st.integers(min_value=-10, max_value=30))
def test_d20_ability_check_range(modifier):
    """d20 + modificador sempre entre 1+mod e 20+mod."""
    result = roll_ability_check(modifier)
    assert not result.get("error")
    assert 1 + modifier <= result["total"] <= 20 + modifier


@given(modifier=st.integers(min_value=-5, max_value=20),
       dc=st.integers(min_value=1, max_value=30))
def test_save_success_logic(modifier, dc):
    """Save bem-sucedido = total >= CD."""
    result = roll_save(modifier, dc)
    assert not result.get("error")
    if result["total"] >= dc:
        assert result["success"] is True
    else:
        assert result["success"] is False
    assert result["margin"] == result["total"] - dc


@given(num=st.integers(min_value=1, max_value=10),
       sides=st.integers(min_value=4, max_value=12),
       mod=st.integers(min_value=0, max_value=10))
def test_damage_never_negative(num, sides, mod):
    """Dano total nunca eh negativo."""
    result = roll_damage(f"{num}d{sides}+{mod}")
    assert not result.get("error")
    assert result["total"] >= num + mod  # Minimo: todos os dados = 1 + mod


@given(num=st.integers(min_value=1, max_value=6),
       sides=st.integers(min_value=4, max_value=12))
def test_critical_doubles_dice(num, sides):
    """Critico dobra a quantidade de dados."""
    normal = roll_damage(f"{num}d{sides}", critical=False)
    critical = roll_damage(f"{num}d{sides}", critical=True)
    assert not normal.get("error")
    assert not critical.get("error")
    # Critico: minimo = num*2 (dobra dados), normal: minimo = num
    assert critical["total"] >= num * 2  # Pelo menos 1 por dado dobrado


def test_invalid_expression():
    """Expressao invalida retorna erro estruturado."""
    result = roll("abcdef")
    assert result["error"] is True
    assert "code" in result


def test_d20_roll():
    """1d20 funciona normalmente."""
    result = roll("1d20")
    assert not result.get("error")
    assert 1 <= result["total"] <= 20


def test_complex_expression():
    """Expressao complexa 4d6kh3 funciona."""
    result = roll("4d6kh3")
    assert not result.get("error")
    assert 3 <= result["total"] <= 18  # 3 maiores de 4d6
