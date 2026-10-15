"""Bounded exact-number parsing; never infer units from numerical closeness."""

import re
from decimal import Decimal, InvalidOperation
from fractions import Fraction

DECIMAL_PATTERN = r"[+-]?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?"
SCALES = ("1", "1000", "1000000", "1000000000")
CONSTANTS = ("-1", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "12",
             "100", "1000", "1000000", "1000000000")
MAX_MAGNITUDE = Fraction(10**30)
TOKEN_RE = re.compile(
    r"(?<![\w.])(?:\(\s*)?[$£€]?\s*[+\-−]?\s*"
    r"(?:\d(?:[\d,]*\d)?(?:\.\d+)?|\.\d+)\s*%?(?:\s*\))?(?!\w|\.\d|,\d|%)"
)
SOURCE_NUMBER = re.compile(r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+")


class InvalidNumber(ValueError):
    pass


def number(value):
    """Plain signed decimal string -> exact Fraction; reject bool/NaN/exponents."""
    if not isinstance(value, str) or len(value) > 64 or not re.fullmatch(DECIMAL_PATTERN, value):
        raise InvalidNumber("expected a bounded plain decimal string")
    try:
        result = Fraction(Decimal(value))
    except (InvalidOperation, ValueError, OverflowError) as exc:
        raise InvalidNumber("invalid decimal") from exc
    return bounded(result)


def bounded(value):
    if (abs(value) > MAX_MAGNITUDE or value.numerator.bit_length() > 4096
            or value.denominator.bit_length() > 4096):
        raise InvalidNumber("arithmetic magnitude/precision limit exceeded")
    return value


def source_number(quote):
    """Interpret the displayed number only: 25% -> 25; (25) -> -25."""
    if not isinstance(quote, str) or not quote or len(quote) > 96:
        raise InvalidNumber("invalid numeric quote")
    s = quote.strip().replace("−", "-")
    parentheses = s.startswith("(") and s.endswith(")")
    if s.startswith("(") != s.endswith(")"):
        raise InvalidNumber("unpaired parentheses")
    if parentheses:
        s = s[1:-1].strip()
    if s[:1] in ("$", "£", "€"):
        s = s[1:].strip()
    sign = -1 if parentheses else 1
    if s[:1] in ("+", "-"):
        if parentheses:
            raise InvalidNumber("ambiguous double sign")
        sign = -1 if s[0] == "-" else 1
        s = s[1:].strip()
    if s.endswith("%"):
        s = s[:-1].strip()
    if not SOURCE_NUMBER.fullmatch(s):
        raise InvalidNumber("quote must contain exactly one numeric token")
    s = s.replace(",", "")
    if s.startswith("."):
        s = "0" + s
    # Source leading zeros are display formatting, not executable syntax.
    return bounded(Fraction(Decimal(s)) * sign)


def numeric_tokens(text):
    return [match.group().strip() for match in TOKEN_RE.finditer(text)]


QUOTE_SUFFIX = re.compile(r"(?:(?:thousand|million|billion|trillion)(?:\s+(?:dollars?|shares?))?|dollars?|shares?|years?|months?|days?)", re.I)


def display_quote(quote):
    """One displayed number, optionally followed by a small literal unit suffix.

    Commas, currency spacing and decimal formatting normalize; sign and percent
    do not disappear. A suffix never silently rescales the declared operand.
    """
    if not isinstance(quote, str) or not 1 <= len(quote) <= 96:
        raise InvalidNumber('invalid citation quote')
    matches = list(TOKEN_RE.finditer(quote))
    if len(matches) != 1 or quote[:matches[0].start()].strip():
        raise InvalidNumber('quote must contain exactly one numeric token')
    match = matches[0]
    token = match.group().strip()
    suffix = quote[match.end():].strip().casefold()
    if suffix and not QUOTE_SUFFIX.fullmatch(suffix):
        raise InvalidNumber('unsupported quote suffix')
    return source_number(token), '%' in token, suffix


def citation_matches(location, quote):
    """Normalized number in the exact location, not semantic fact verification."""
    value, percent, suffix = display_quote(quote)
    for match in TOKEN_RE.finditer(location):
        token = match.group().strip()
        try:
            same = source_number(token) == value and ('%' in token) == percent
        except InvalidNumber:
            continue
        if same and (not suffix or re.match(re.escape(suffix) + r'(?!\w)',
                                           location[match.end():].strip(), re.I)):
            return True
    return False


def canonical(value, unit, scale):
    if not isinstance(unit, str) or not unit.strip() or len(unit) > 64:
        raise InvalidNumber("missing unit")
    if scale not in SCALES:
        raise InvalidNumber("unsupported scale")
    normalized_unit = unit.strip().casefold()
    if normalized_unit in ("percent", "ratio") and scale != "1":
        raise InvalidNumber("ratio/percent scale must be 1")
    factor = Fraction(int(scale))
    if normalized_unit == "percent":
        normalized_unit, factor = "ratio", Fraction(1, 100)
    return normalized_unit, bounded(number(value) * factor), factor

