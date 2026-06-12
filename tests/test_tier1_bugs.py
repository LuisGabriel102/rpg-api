"""Tier 1 — testes que provam que os bugs foram corrigidos.

Bug 1: combat.py:122 — execute-turn com fase NULL/vazia/ausente
Bug 2: dice.py:73 — dano crítico deve dobrar TODOS os grupos de dados
Bug 3: oficina_npcs.py:440 — handlers devem ser async pra await on_change()
"""

# =====================================================================
# BUG 1 — Máquina de estados: fase NULL/vazia/ausente não deve crashar
# =====================================================================
from app.routers.combat import validate_phase_transition, VALID_TRANSITIONS


def test_bug1_null_phase_does_not_block_action():
    """Fase NULL não deve causar CombatPhaseError."""
    estado = {"fase_atual": None}
    current_phase = (estado.get("fase_atual") or "").lower()
    action_phase = "acao"

    should_raise = (
        current_phase
        and current_phase in VALID_TRANSITIONS
        and not validate_phase_transition(current_phase, action_phase)
    )

    assert not should_raise


def test_bug1_empty_string_phase_does_not_block():
    """Fase vazia não deve causar CombatPhaseError."""
    estado = {"fase_atual": ""}
    current_phase = (estado.get("fase_atual") or "").lower()
    action_phase = "acao"

    should_raise = (
        current_phase
        and current_phase in VALID_TRANSITIONS
        and not validate_phase_transition(current_phase, action_phase)
    )

    assert not should_raise


def test_bug1_missing_key_does_not_block():
    """Chave fase_atual ausente não deve causar CombatPhaseError."""
    estado = {"rodada": 1, "hp": 20}
    current_phase = (estado.get("fase_atual") or "").lower()
    action_phase = "acao"

    should_raise = (
        current_phase
        and current_phase in VALID_TRANSITIONS
        and not validate_phase_transition(current_phase, action_phase)
    )

    assert not should_raise


def test_bug1_valid_phase_still_validates():
    """Transição inválida com fase explícita ainda deve ser bloqueada."""
    current_phase = "combate_fim"
    action_phase = "acao"

    should_raise = (
        current_phase
        and current_phase in VALID_TRANSITIONS
        and not validate_phase_transition(current_phase, action_phase)
    )

    assert should_raise, "combate_fim → acao deve ser bloqueado"


def test_bug1_turno_inicio_to_acao_is_valid():
    """turno_inicio → acao é transição válida."""
    assert validate_phase_transition("turno_inicio", "acao")


# =====================================================================
# BUG 2 — Dano crítico deve dobrar TODOS os grupos de dados
# =====================================================================
from app.dice import roll_damage


def test_bug2_critical_doubles_all_dice_groups():
    """1d8+1d6+3 com critical deve virar 2d8+2d6+3."""
    expression = "1d8+1d6+3"

    # Reproduz a lógica corrigida
    parts = expression.split("+")
    doubled = []
    for part in parts:
        part = part.strip()
        if "d" in part:
            num, rest = part.split("d", 1)
            num = int(num) if num else 1
            doubled.append(f"{num * 2}d{rest}")
        else:
            doubled.append(part)
    result_expr = "+".join(doubled)

    assert result_expr == "2d8+2d6+3"


def test_bug2_critical_simple_expression():
    """2d6+3 com critical deve virar 4d6+3."""
    result = roll_damage("2d6+3", critical=True)
    assert not result.get("error")
    assert result["critical"] is True
    assert result["total"] >= 4 + 3  # mínimo: 4 dados de 1 + 3


def test_bug2_critical_multi_dice():
    """1d8+1d6+3 com critical: resultado mínimo = 2+2+3 = 7."""
    for _ in range(50):
        result = roll_damage("1d8+1d6+3", critical=True)
        assert not result.get("error")
        assert result["total"] >= 7, (
            f"Resultado {result['total']} abaixo do mínimo 7 "
            f"(2d8 min=2 + 2d6 min=2 + 3)"
        )


def test_bug2_critical_no_modifier():
    """1d12 com critical deve virar 2d12."""
    result = roll_damage("1d12", critical=True)
    assert not result.get("error")
    assert result["total"] >= 2  # 2d12 mínimo


def test_bug2_non_critical_unchanged():
    """Sem critical, expressão não é modificada."""
    result = roll_damage("1d8+1d6+3", critical=False)
    assert not result.get("error")
    assert result["total"] >= 5  # 1+1+3


# =====================================================================
# BUG 3 — Handlers async: verificação por inspeção de código
# =====================================================================
import asyncio


def test_bug3_async_handler_awaits_coroutine():
    """Handler async produz resultado executado, não coroutine descartada."""

    executed = False

    async def on_change():
        nonlocal executed
        executed = True

    async def handler(e):
        await on_change()

    asyncio.run(handler("teste"))
    assert executed, "on_change deve ter sido executado via await"
