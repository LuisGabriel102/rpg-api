"""Motor de rolagem de dados com random criptografico.
Usa a biblioteca d20 para parsing de notacao D&D.

d20 usa random.randint() internamente. Substituimos por
secrets.randbelow() no carregamento do modulo para garantir
dados criptograficamente aleatorios."""

import random
import secrets

# Monkey-patch random.randint com crypto ANTES de importar d20
# Seguro para RPG solo (1 usuario). d20 chama random.randint() internamente.
_original_randint = random.randint
random.randint = lambda a, b: a + secrets.randbelow(b - a + 1)

import d20


def roll(expression: str) -> dict:
    """Rola dados com notacao D&D usando random criptografico.

    Suporta: 2d6+3, 4d6kh3 (keep highest 3), 1d20+5, 8d6, 1d12+1d4, etc.
    Retorna dict com total, detalhes de cada dado e expressao original.
    """
    try:
        result = d20.roll(expression)
    except d20.errors.RollSyntaxError:
        return {
            "error": True,
            "code": "INVALID_DICE_EXPRESSION",
            "message": f"Expressao invalida: '{expression}'",
            "suggestion": "Use notacao D&D: 1d20, 2d6+3, 4d6kh3, 1d20+5",
        }

    return {
        "error": False,
        "expression": expression,
        "total": result.total,
        "result_text": str(result),
        "details": result.comment or str(result.expr),
        "crit": result.crit,
    }


def roll_ability_check(modifier: int, advantage: bool = False, disadvantage: bool = False) -> dict:
    """Rola teste de habilidade: d20 + modificador, com vantagem/desvantagem."""
    if advantage and not disadvantage:
        adv = d20.AdvType.ADV
    elif disadvantage and not advantage:
        adv = d20.AdvType.DIS
    else:
        adv = d20.AdvType.NONE

    try:
        result = d20.roll(f"1d20+{modifier}", advantage=adv)
    except d20.errors.RollSyntaxError:
        return {"error": True, "code": "INVALID_EXPRESSION", "message": "Erro ao rolar d20"}

    nat = result.total - modifier
    return {
        "error": False,
        "expression": f"1d20+{modifier}" + (" (vantagem)" if advantage else " (desvantagem)" if disadvantage else ""),
        "total": result.total,
        "natural_roll": nat,
        "critical_success": result.crit == 1,
        "critical_failure": nat == 1,
        "result_text": str(result),
    }


def roll_damage(expression: str, critical: bool = False) -> dict:
    """Rola dano. Se critico, dobra os dados (nao o modificador)."""
    if critical:
        parts = expression.split("+")
        dice_part = parts[0].strip()
        mod_part = "+".join(parts[1:]).strip() if len(parts) > 1 else ""
        if "d" in dice_part:
            num, rest = dice_part.split("d", 1)
            num = int(num) if num else 1
            dice_part = f"{num * 2}d{rest}"
        expression = dice_part + ("+" + mod_part if mod_part else "")

    result = roll(expression)
    if not result.get("error"):
        result["critical"] = critical
    return result


def roll_save(modifier: int, dc: int, advantage: bool = False, disadvantage: bool = False) -> dict:
    """Rola saving throw contra CD."""
    result = roll_ability_check(modifier, advantage, disadvantage)
    if not result.get("error"):
        result["dc"] = dc
        result["success"] = result["total"] >= dc
        result["margin"] = result["total"] - dc
    return result
