from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AuditStatus(str, Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    NO_DATA = "NO_DATA"


@dataclass(frozen=True, slots=True)
class AuditResult:
    source_name: str
    query_parameter: str
    duration_ms: int
    status: AuditStatus
    details: str | None
    executed_at_utc: datetime
