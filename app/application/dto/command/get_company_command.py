import re
from dataclasses import dataclass
from typing import Final

RUC_PATTERN: Final = re.compile(r"[0-9]{11}")


@dataclass(frozen=True, slots=True)
class GetCompanyCommand:
    ruc: str

    def __post_init__(self) -> None:
        if not RUC_PATTERN.fullmatch(self.ruc):
            raise ValueError("RUC must have exactly 11 digits")
