import re
from datetime import date, datetime
from typing import Any, Final

_WHITESPACE: Final = re.compile(r"\s+")
_DATE: Final = re.compile(r"\d{2}/\d{2}/\d{4}")
_PLACEHOLDERS: Final = frozenset({"", "-"})


def clean_text(value: str | None) -> str:
    return _WHITESPACE.sub(" ", value).strip() if value else ""


def optional_text(value: Any) -> str | None:
    text = clean_text(str(value)) if value is not None else ""
    return None if text in _PLACEHOLDERS else text


def to_float(value: Any) -> float:
    try:
        return float(str(value).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def to_int(value: Any) -> int:
    return int(to_float(value))


def parse_date(value: Any) -> date | None:
    match = _DATE.search(optional_text(value) or "")
    if match is None:
        return None
    try:
        return datetime.strptime(match.group(), "%d/%m/%Y").date()
    except ValueError:
        return None
