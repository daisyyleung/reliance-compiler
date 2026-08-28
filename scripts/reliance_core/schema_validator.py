"""Small deterministic JSON-Schema subset used by the Reliance Compiler.

The project intentionally avoids a third-party validator. This module supports
the keywords used by the checked-in contracts, including local/external refs,
type, required, properties, additionalProperties, items, enum, const,
minLength, minimum/maximum, and anyOf/oneOf.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Mapping


class SchemaError(ValueError):
    """Raised only when a schema reference cannot be loaded."""


def load_schema(path: str | pathlib.Path) -> Mapping[str, Any]:
    schema_path = pathlib.Path(path)
    try:
        data = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaError(f"cannot load schema {schema_path}: {exc}") from exc
    if not isinstance(data, Mapping):
        raise SchemaError(f"schema {schema_path} must be an object")
    return data


def validate(instance: Any, schema: Mapping[str, Any], *, base_dir: str | pathlib.Path, path: str = "$", root_schema: Mapping[str, Any] | None = None) -> list[str]:
    """Return deterministic schema violations for the supported subset."""
    errors: list[str] = []
    root_schema = root_schema or schema
    if "$ref" in schema:
        ref = str(schema["$ref"])
        if ref.startswith("#/"):
            target: Any = root_schema
            for part in ref[2:].split("/"):
                target = target[part.replace("~1", "/").replace("~0", "~")]
            return validate(instance, target, base_dir=base_dir, path=path, root_schema=root_schema)
        target_path = (pathlib.Path(base_dir) / ref).resolve()
        target = load_schema(target_path)
        return validate(instance, target, base_dir=target_path.parent, path=path, root_schema=target)
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value is not in enum")
    if "anyOf" in schema:
        alternatives = [validate(instance, child, base_dir=base_dir, path=path, root_schema=root_schema) for child in schema["anyOf"]]
        if all(alternative for alternative in alternatives):
            errors.append(f"{path}: does not satisfy anyOf")
    if "oneOf" in schema:
        alternatives = [not validate(instance, child, base_dir=base_dir, path=path, root_schema=root_schema) for child in schema["oneOf"]]
        if sum(alternatives) != 1:
            errors.append(f"{path}: does not satisfy exactly one oneOf branch")
    if "type" in schema:
        expected = schema["type"]
        expected_types = expected if isinstance(expected, list) else [expected]
        if not any(_is_type(instance, type_name) for type_name in expected_types):
            errors.append(f"{path}: expected type {expected!r}")
            return errors
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < int(schema["minLength"]):
            errors.append(f"{path}: shorter than minLength")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: below minimum")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: above maximum")
    if isinstance(instance, Mapping):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{path}: missing required property {key}")
        properties = schema.get("properties", {})
        for key, value in instance.items():
            if key in properties:
                errors.extend(validate(value, properties[key], base_dir=base_dir, path=f"{path}.{key}", root_schema=root_schema))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: additional property {key}")
            elif isinstance(schema.get("additionalProperties"), Mapping):
                errors.extend(validate(value, schema["additionalProperties"], base_dir=base_dir, path=f"{path}.{key}", root_schema=root_schema))
    if isinstance(instance, list) and isinstance(schema.get("items"), Mapping):
        for index, value in enumerate(instance):
            errors.extend(validate(value, schema["items"], base_dir=base_dir, path=f"{path}[{index}]", root_schema=root_schema))
    return errors


def _is_type(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, Mapping),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, True)
