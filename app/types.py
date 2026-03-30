"""Tipos RPG reutilizaveis com validacao Pydantic v2."""

from typing import Annotated, Optional, List
from pydantic import BaseModel, Field, ConfigDict


# === Tipos basicos com validacao RPG ===
AbilityScore = Annotated[int, Field(ge=1, le=30, description="Valor de atributo (1-30)")]
Level = Annotated[int, Field(ge=1, le=20, description="Nivel do personagem (1-20)")]
SpellLevel = Annotated[int, Field(ge=0, le=9, description="Nivel da magia (0=cantrip, 9=maximo)")]
HitPoints = Annotated[int, Field(ge=0, description="Pontos de vida (minimo 0)")]
ManaPoints = Annotated[int, Field(ge=0, description="Pontos de mana (minimo 0)")]
ArmorClass = Annotated[int, Field(ge=0, le=30, description="Classe de armadura (0-30)")]
ChallengeRating = Annotated[float, Field(ge=0, le=30, description="CR da criatura (0-30)")]
TrustLevel = Annotated[int, Field(ge=-100, le=100, description="Nivel de confianca (-100 a 100)")]
MoralWeight = Annotated[int, Field(ge=1, le=5, description="Peso moral da decisao (1-5)")]


# === Modelo base com config padrao ===
class NexusBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# === Resposta de erro estruturada para o GPT ===
class NexusError(BaseModel):
    code: str
    message: str
    suggestion: Optional[str] = None
    valid_values: Optional[dict] = None


class NexusResponse(BaseModel):
    """Resposta padrao estruturada para o GPT narrar."""
    action_result: dict = Field(default_factory=dict, description="Dados mecanicos do resultado")
    character_state: Optional[dict] = Field(None, description="Estado atual HP/MP/condicoes")
    context: Optional[dict] = Field(None, description="Localizacao, ambiente")
    narrative_hints: Optional[dict] = Field(None, description="Tom sugerido, mood")


# === Enums como strings para OpenAPI do GPT ===
COMBAT_RESULTS = ["vitoria", "derrota", "fuga", "negociacao"]
REST_TYPES = ["descanso_curto", "descanso_longo"]
XP_SOURCES = ["combate", "missao", "roleplay", "descoberta"]
NPC_INTERACTION_TYPES = ["conversa", "troca", "combate", "ajuda", "traicao"]
ANIMA_CATEGORIES = ["dificil", "desesperada"]
MILESTONE_TYPES = ["menor", "significativo", "maior", "unico"]
DIARY_MOODS = ["neutro", "feliz", "triste", "furioso", "contemplativo", "assustado", "determinado"]
MASTERY_TYPES = [
    "pericia", "magia", "recurso_classe", "arma", "save", "ferramenta",
    "tecnica_marcial", "tecnica_arcana", "tecnica_espiritual", "tecnica_divina",
    "tecnica_sobrenatural", "tecnica_social", "tecnica_oficio",
]
ITEM_RARITIES = ["comum", "incomum", "raro", "muito raro", "epico", "lendario", "artefato"]
NPC_LAYERS = [1, 2, 3]  # 1=principal, 2=secundario, 3=figurante
DAY_PERIODS = ["manha", "tarde", "noite", "madrugada"]
