"""Strict bounded response contract, also enforced without third-party packages."""

import json
import math
import re

from .numbers import CONSTANTS, DECIMAL_PATTERN, SCALES, number

NUMERIC = {"type": "string", "pattern": "^" + DECIMAL_PATTERN + "$", "maxLength": 64}


def obj(properties):
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


RESPONSE_SCHEMA = obj({
    "answer": {"anyOf": [NUMERIC, {"type": "null"}]},
    "unit": {"type": "string", "maxLength": 64},
    "scale": {"type": "string", "enum": list(SCALES)},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "operands": {"type": "array", "maxItems": 16, "items": obj({
        "id": {"type": "string", "pattern": "^o[1-9][0-9]?$"},
        "location_id": {"type": "string", "minLength": 1, "maxLength": 128},
        "quote": {"type": "string", "minLength": 1, "maxLength": 96},
        "value": NUMERIC,
    })},
    "constants": {"type": "array", "maxItems": 8, "items": obj({
        "id": {"type": "string", "pattern": "^c[1-9][0-9]?$"},
        "value": {"type": "string", "enum": list(CONSTANTS)},
    })},
    "expression": {"type": "string", "maxLength": 512},
})


class InvalidResponse(ValueError):
    pass


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidResponse("duplicate JSON key")
        result[key] = value
    return result


def _keys(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise InvalidResponse("missing or additional object fields")


def parse_response(payload):
    if isinstance(payload, str):
        if len(payload) > 32000:
            raise InvalidResponse("response exceeds size limit")
        try:
            payload = json.loads(payload, object_pairs_hook=_unique_object,
                                 parse_constant=lambda _: (_ for _ in ()).throw(
                                     InvalidResponse("nonfinite JSON constant")))
        except (ValueError, TypeError, RecursionError) as exc:
            raise InvalidResponse(str(exc)) from exc
    _keys(payload, RESPONSE_SCHEMA["required"])
    c = payload["confidence"]
    if isinstance(c, bool) or not isinstance(c, (int, float)) or not math.isfinite(c) or not 0 <= c <= 1:
        raise InvalidResponse("confidence must be finite in [0,1]")
    if not isinstance(payload["unit"], str) or len(payload["unit"]) > 64:
        raise InvalidResponse("invalid unit")
    if payload["scale"] not in SCALES:
        raise InvalidResponse("invalid scale")
    if not isinstance(payload["expression"], str) or len(payload["expression"]) > 512:
        raise InvalidResponse("invalid expression")
    for field, maximum in (("operands", 16), ("constants", 8)):
        if not isinstance(payload[field], list) or len(payload[field]) > maximum:
            raise InvalidResponse("invalid operand/constant list")
    ids = set()
    for operand in payload["operands"]:
        _keys(operand, ("id", "location_id", "quote", "value"))
        if not isinstance(operand["id"], str) or not re.fullmatch(r"o[1-9][0-9]?", operand["id"]):
            raise InvalidResponse("invalid operand ID")
        for key, maximum in (("location_id", 128), ("quote", 96)):
            if not isinstance(operand[key], str) or not 1 <= len(operand[key]) <= maximum:
                raise InvalidResponse("invalid citation field")
        number(operand["value"])
        if operand["id"] in ids:
            raise InvalidResponse("duplicate operand ID")
        ids.add(operand["id"])
    for constant in payload["constants"]:
        _keys(constant, ("id", "value"))
        if (not isinstance(constant["id"], str) or not re.fullmatch(r"c[1-9][0-9]?", constant["id"])
                or constant["id"] in ids or constant["value"] not in CONSTANTS):
            raise InvalidResponse("invalid constant")
        ids.add(constant["id"])
    if payload["answer"] is None:
        if payload["operands"] or payload["constants"] or payload["expression"] or payload["unit"] or payload["scale"] != "1":
            raise InvalidResponse("abstention requires empty derivation/unit and scale 1")
    else:
        number(payload["answer"])
        if not payload["operands"] or not payload["expression"].strip() or not payload["unit"].strip():
            raise InvalidResponse("numeric answer requires operands, expression and unit")
    return payload


