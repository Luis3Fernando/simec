from dataclasses import dataclass

from app.domain.models.audit import AuditResult
from app.domain.models.profile import PersonProfile
from app.domain.models.seace import SeacePersonRecord
from app.domain.models.sunat import SunatProfile


@dataclass(frozen=True, slots=True)
class PersonResult:
    dni: str
    profile: PersonProfile | None = None
    seace: SeacePersonRecord | None = None
    sunat: SunatProfile | None = None
    audit_entries: tuple[AuditResult, ...] = ()
