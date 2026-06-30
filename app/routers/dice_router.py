"""Router de rolagem de dados com random criptografico."""

from fastapi import APIRouter, Depends, Query
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from pydantic import BaseModel, Field
from typing import Optional
from app.database import get_db
from app.auth import verify_token
from app.dice import roll, roll_ability_check, roll_damage, roll_save
from app.events import record_event

router = APIRouter()


class DiceRollRequest(BaseModel):
    expression: str = Field(..., description="Notacao D&D: 1d20, 2d6+3, 4d6kh3, 1d20+5")
    context: str = Field("", description="Contexto: ataque, dano, save, pericia, iniciativa")
    personagem_id: Optional[int] = None
    sessao_id: Optional[int] = None


class AbilityCheckRequest(BaseModel):
    modifier: int = Field(..., description="Modificador total (atributo + proficiencia + bonus)")
    advantage: bool = False
    disadvantage: bool = False
    dc: Optional[int] = Field(None, description="Classe de dificuldade (se teste contra CD)")
    context: str = Field("", description="Descricao: 'Persuasao contra o guarda', 'Furtividade'")
    personagem_id: Optional[int] = None
    sessao_id: Optional[int] = None


class DamageRollRequest(BaseModel):
    expression: str = Field(..., description="Dados de dano: 2d6+3, 1d8+4, 3d10")
    critical: bool = Field(False, description="Se verdadeiro, dobra os dados (nao o modificador)")
    damage_type: str = Field("", description="Tipo: cortante, perfurante, contundente, fogo, gelo, etc.")
    personagem_id: Optional[int] = None
    sessao_id: Optional[int] = None


class SaveRollRequest(BaseModel):
    modifier: int = Field(..., description="Modificador do save (Fortitude/Reflexos/Vontade + bonus)")
    dc: int = Field(..., description="Classe de dificuldade do save")
    save_type: str = Field("", description="fortitude, reflexos ou vontade")
    advantage: bool = False
    disadvantage: bool = False
    personagem_id: Optional[int] = None
    sessao_id: Optional[int] = None


@router.post(
    "/roll",
    operation_id="rollDice",
    summary="Rolar dados com notacao D&D",
    description="Rola dados reais com random criptografico. Suporta: 1d20, 2d6+3, 4d6kh3, 1d20+5, 8d6, etc.",
    openapi_extra={"x-openai-isConsequential": False},
)
async def roll_dice(
    payload: DiceRollRequest,
    conn: AsyncConnection = Depends(get_db),
    _token: str = Depends(verify_token),
):
    result = roll(payload.expression)

    # Registra evento se tiver sessao
    if payload.sessao_id and not result.get("error"):
        await record_event(
            conn, "dados", payload.personagem_id or 0, "DICE_ROLL",
            {"expression": payload.expression, "total": result["total"], "context": payload.context},
            sessao_id=payload.sessao_id, personagem_id=payload.personagem_id,
        )

    return result


@router.post(
    "/ability-check",
    operation_id="rollAbilityCheck",
    summary="Teste de habilidade ou pericia",
    description="Rola d20 + modificador com vantagem/desvantagem. Detecta critico (nat 20) e falha critica (nat 1).",
    openapi_extra={"x-openai-isConsequential": False},
)
async def ability_check(
    payload: AbilityCheckRequest,
    conn: AsyncConnection = Depends(get_db),
    _token: str = Depends(verify_token),
):
    result = roll_ability_check(payload.modifier, payload.advantage, payload.disadvantage)

    if payload.dc and not result.get("error"):
        result["dc"] = payload.dc
        result["success"] = result["total"] >= payload.dc
        result["margin"] = result["total"] - payload.dc

    if payload.sessao_id and not result.get("error"):
        await record_event(
            conn, "dados", payload.personagem_id or 0, "ABILITY_CHECK",
            {"total": result["total"], "context": payload.context, "dc": payload.dc, "success": result.get("success")},
            sessao_id=payload.sessao_id, personagem_id=payload.personagem_id,
        )

    return result


@router.post(
    "/damage",
    operation_id="rollDamage",
    summary="Rolar dano",
    description="Rola dados de dano. Se critical=true, dobra os dados (nao o modificador fixo).",
    openapi_extra={"x-openai-isConsequential": False},
)
async def damage_roll(
    payload: DamageRollRequest,
    conn: AsyncConnection = Depends(get_db),
    _token: str = Depends(verify_token),
):
    result = roll_damage(payload.expression, payload.critical)

    if not result.get("error"):
        result["damage_type"] = payload.damage_type

    if payload.sessao_id and not result.get("error"):
        await record_event(
            conn, "dados", payload.personagem_id or 0, "DAMAGE_ROLL",
            {"total": result["total"], "critical": payload.critical, "type": payload.damage_type},
            sessao_id=payload.sessao_id, personagem_id=payload.personagem_id,
        )

    return result


@router.post(
    "/save",
    operation_id="rollSave",
    summary="Saving throw (Fortitude/Reflexos/Vontade)",
    description="Rola saving throw contra CD. Retorna sucesso/falha e margem.",
    openapi_extra={"x-openai-isConsequential": False},
)
async def save_roll(
    payload: SaveRollRequest,
    conn: AsyncConnection = Depends(get_db),
    _token: str = Depends(verify_token),
):
    result = roll_save(payload.modifier, payload.dc, payload.advantage, payload.disadvantage)

    if not result.get("error"):
        result["save_type"] = payload.save_type

    if payload.sessao_id and not result.get("error"):
        await record_event(
            conn, "dados", payload.personagem_id or 0, "SAVE_ROLL",
            {"total": result["total"], "dc": payload.dc, "success": result["success"], "type": payload.save_type},
            sessao_id=payload.sessao_id, personagem_id=payload.personagem_id,
        )

    return result
