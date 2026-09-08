"""Explainable, domain-neutral normalization for common values and units."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from dateutil import parser as date_parser


@dataclass(frozen=True)
class NormalizedValue:
    value: str | None
    unit: str | None
    numeric: Decimal | None = None
    kind: str | None = None


_CURRENCY = {"$": "USD", "usd": "USD", "₹": "INR", "inr": "INR", "rs": "INR", "eur": "EUR", "€": "EUR", "gbp": "GBP", "£": "GBP"}
_SCALES = {"k": Decimal("1000"), "thousand": Decimal("1000"), "m": Decimal("1000000"), "mn": Decimal("1000000"), "million": Decimal("1000000"), "bn": Decimal("1000000000"), "billion": Decimal("1000000000"), "lakh": Decimal("100000"), "lac": Decimal("100000"), "crore": Decimal("10000000")}
_UNITS = {"km": ("m", Decimal("1000")), "kilometer": ("m", Decimal("1000")), "kilometre": ("m", Decimal("1000")), "m": ("m", Decimal("1")), "meter": ("m", Decimal("1")), "metre": ("m", Decimal("1")), "cm": ("m", Decimal("0.01")), "kg": ("kg", Decimal("1")), "g": ("kg", Decimal("0.001")), "celsius": ("C", Decimal("1")), "°c": ("C", Decimal("1")), "fahrenheit": ("F", Decimal("1")), "°f": ("F", Decimal("1"))}


def normalize_value(raw: str, supplied_unit: str | None = None) -> NormalizedValue:
    """Normalize numbers, percent, currency scale, and basic physical units; leave other values intact."""
    text = raw.strip().lower().replace(",", "")
    if re.fullmatch(r"\d+(?:\.\d+)?\s*%", text):
        number = Decimal(re.search(r"\d+(?:\.\d+)?", text).group())
        return NormalizedValue(str(number), "%", number, "percentage")
    currency = next((code for token, code in _CURRENCY.items() if token in text or (supplied_unit or "").lower() == token), None)
    match = re.search(r"(?<![\w-])(-?\d+(?:\.\d+)?)\s*(k|thousand|m|mn|million|bn|billion|lakh|lac|crore)?\b", text)
    if match:
        number = Decimal(match.group(1)) * _SCALES.get(match.group(2) or "", Decimal("1"))
        detected_unit = (supplied_unit or "").lower().strip()
        if detected_unit in _UNITS:
            canonical, multiplier = _UNITS[detected_unit]
            if canonical == "F":
                number = (number - Decimal("32")) * Decimal("5") / Decimal("9")
                canonical = "C"
            else:
                number *= multiplier
            return NormalizedValue(_decimal_string(number), canonical, number, "measurement")
        return NormalizedValue(_decimal_string(number), currency or supplied_unit, number, "number")
    try:
        parsed: date = date_parser.parse(raw, fuzzy=False).date()
        return NormalizedValue(parsed.isoformat(), "date", None, "date")
    except (ValueError, OverflowError, InvalidOperation):
        return NormalizedValue(raw.strip(), supplied_unit, None, "text")


def values_equivalent(a: NormalizedValue, b: NormalizedValue, relative_tolerance: Decimal = Decimal("0.015")) -> bool:
    if a.numeric is None or b.numeric is None or a.unit != b.unit:
        return a.value is not None and a.value.casefold() == (b.value or "").casefold()
    denominator = max(abs(a.numeric), abs(b.numeric), Decimal("1"))
    return abs(a.numeric - b.numeric) / denominator <= relative_tolerance


def _decimal_string(value: Decimal) -> str:
    rendered = format(value.normalize(), "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"
