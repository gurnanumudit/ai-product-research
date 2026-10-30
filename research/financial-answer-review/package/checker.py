"""Source-and-arithmetic checks only. No reference answers, imports or file reads."""

import ast
from dataclasses import dataclass
from fractions import Fraction

from .numbers import bounded, canonical, number, numeric_tokens, source_number
from .schema import parse_response

ARITHMETIC_TOLERANCE = Fraction(1, 100000)  # absolute, in displayed answer units


@dataclass(frozen=True)
class CheckReport:
    id: str
    usable: bool
    confidence: float | None
    warnings: tuple[str, ...] = ()
    mandatory_reasons: tuple[str, ...] = ()

    @property
    def mandatory_abstain(self):
        return not self.usable


def evaluate(expression, values):
    """Walk a small AST, never eval/exec. Numeric literals must be named constants."""
    if not isinstance(expression, str) or not 1 <= len(expression) <= 512:
        raise ValueError("expression length")
    root = ast.parse(expression.strip(), mode="eval")
    if sum(1 for _ in ast.walk(root)) > 100:
        raise ValueError("expression node limit")
    used = set()

    def visit(node, depth=0):
        if depth > 16:
            raise ValueError("expression depth limit")
        if isinstance(node, ast.Expression):
            return visit(node.body, depth + 1)
        if isinstance(node, ast.Name) and node.id in values:
            used.add(node.id)
            return values[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand, depth + 1)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left, right = visit(node.left, depth + 1), visit(node.right, depth + 1)
            if isinstance(node.op, ast.Add):
                result = left + right
            elif isinstance(node.op, ast.Sub):
                result = left - right
            elif isinstance(node.op, ast.Mult):
                result = left * right
            else:
                if right == 0:
                    raise ValueError("division by zero")
                result = left / right
            return bounded(result)
        raise ValueError("unsupported arithmetic syntax or unknown identifier")

    result = visit(root)
    if not any(key.startswith("o") for key in used):
        raise ValueError("expression must use a source operand")
    return result, used


def check_response(item, payload):
    if (not isinstance(item, dict) or set(item) != {"id", "question", "locations"}
            or not isinstance(item["id"], str) or not item["id"]
            or not isinstance(item["question"], str) or not isinstance(item["locations"], dict)
            or not all(isinstance(k, str) and isinstance(v, str) for k, v in item["locations"].items())):
        raise ValueError("input must contain only id, question and location text")
    try:
        response = parse_response(payload)
        if response["answer"] is None:
            return CheckReport(item["id"], False, response["confidence"], mandatory_reasons=("explicit_abstention",))
        canonical(response["answer"], response["unit"], response["scale"])
        values = {o["id"]: number(o["value"]) for o in response["operands"] + response["constants"]}
        calculated, used = evaluate(response["expression"], values)
    except (ValueError, TypeError, KeyError, SyntaxError, OverflowError, RecursionError) as exc:
        return CheckReport(item["id"], False, None, mandatory_reasons=("unusable_response:" + str(exc),))
    warnings = []
    for operand in response["operands"]:
        location = item["locations"].get(operand["location_id"])
        if location is None:
            warnings.append("unknown_location:" + operand["id"])
        elif operand["quote"] not in numeric_tokens(location):
            warnings.append("source_number_not_exact:" + operand["id"])
        try:
            if source_number(operand["quote"]) != values[operand["id"]]:
                warnings.append("operand_value_mismatch:" + operand["id"])
        except ValueError:
            warnings.append("invalid_numeric_quote:" + operand["id"])
    if abs(calculated - number(response["answer"])) > ARITHMETIC_TOLERANCE:
        warnings.append("arithmetic_mismatch")
    if used != set(values):
        warnings.append("unused_declared_inputs")
    return CheckReport(item["id"], True, response["confidence"], tuple(sorted(warnings)))
