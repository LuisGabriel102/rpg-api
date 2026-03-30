"""OpenAPI schema customizado para GPT Custom Actions.

Gera 3 schemas separados para respeitar o limite de 30 endpoints por action:
- /openapi.json          → Schema completo (para debug)
- /openapi-combat.json   → Action 1: Combate + Dados + Sessao + Magia (27 endpoints)
- /openapi-character.json → Action 2: Personagem + Inventario + Progressao (29 endpoints)
- /openapi-world.json    → Action 3: Mundo + NPC + Narrativa + SavePoints (27 endpoints)
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.config import settings


# Tags que pertencem a cada action slot
ACTION_SLOTS = {
    "combat": ["Combate", "Dados", "Sessao", "Magia"],
    "character": ["Personagem", "Inventario", "Progressao"],
    "world": ["Mundo", "NPC", "Narrativa", "SavePoints"],
}


def _clean_schema(schema: dict) -> dict:
    """Remove campos que o GPT Builder nao aceita."""
    # Remove securitySchemes
    if "components" in schema:
        schema["components"].pop("securitySchemes", None)
    schema.pop("security", None)

    # Remove security e 422 de cada operacao
    for path in schema.get("paths", {}).values():
        for operation in path.values():
            if isinstance(operation, dict):
                operation.pop("security", None)
                if "responses" in operation:
                    operation["responses"].pop("422", None)

    # Remove schemas de validacao do Pydantic
    if "components" in schema and "schemas" in schema["components"]:
        schema["components"]["schemas"].pop("HTTPValidationError", None)
        schema["components"]["schemas"].pop("ValidationError", None)

    return schema


def _filter_schema_by_tags(full_schema: dict, allowed_tags: list, server_url: str) -> dict:
    """Filtra o schema para incluir apenas paths com tags permitidas."""
    import copy
    filtered = copy.deepcopy(full_schema)

    filtered["servers"] = [{"url": server_url}]

    # Filtra paths
    filtered_paths = {}
    used_refs = set()

    for path, methods in filtered.get("paths", {}).items():
        for method, operation in methods.items():
            if not isinstance(operation, dict):
                continue
            op_tags = operation.get("tags", [])
            if any(tag in allowed_tags for tag in op_tags):
                if path not in filtered_paths:
                    filtered_paths[path] = {}
                filtered_paths[path][method] = operation

                # Coleta refs usadas
                _collect_refs(operation, used_refs)

    filtered["paths"] = filtered_paths

    # Remove schemas nao referenciados
    if "components" in filtered and "schemas" in filtered["components"]:
        filtered_schemas = {}
        for ref_name in used_refs:
            if ref_name in filtered["components"]["schemas"]:
                filtered_schemas[ref_name] = filtered["components"]["schemas"][ref_name]
        filtered["components"]["schemas"] = filtered_schemas

    return filtered


def _collect_refs(obj, refs: set):
    """Coleta todos os $ref usados recursivamente."""
    if isinstance(obj, dict):
        if "$ref" in obj:
            ref_path = obj["$ref"]
            if ref_path.startswith("#/components/schemas/"):
                refs.add(ref_path.split("/")[-1])
        for v in obj.values():
            _collect_refs(v, refs)
    elif isinstance(obj, list):
        for item in obj:
            _collect_refs(item, refs)


def custom_openapi(app: FastAPI):
    """Schema completo (para debug/docs)."""

    def generate():
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title="Nexus RPG API",
            version=settings.api_version,
            description="Backend do Sistema Nexus D&D 5e + T20. 137 tabelas, 209 RPCs, 2.126 magias.",
            routes=app.routes,
        )

        schema["servers"] = [{"url": settings.api_base_url}]
        schema = _clean_schema(schema)

        app.openapi_schema = schema
        return schema

    return generate


def get_split_schema(app: FastAPI, slot: str) -> dict:
    """Gera schema filtrado para um action slot especifico."""
    full = app.openapi()

    if slot not in ACTION_SLOTS:
        return {"error": f"Slot invalido. Use: {list(ACTION_SLOTS.keys())}"}

    tags = ACTION_SLOTS[slot]
    server_url = settings.api_base_url

    filtered = _filter_schema_by_tags(full, tags, server_url)
    filtered["info"]["title"] = f"Nexus RPG - {slot.title()}"
    filtered["info"]["description"] = f"Schema {slot} para GPT Custom Action. Tags: {', '.join(tags)}"

    return _clean_schema(filtered)
