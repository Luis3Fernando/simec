from dataclasses import dataclass

from app.domain.models.audit import AuditResult
from app.domain.models.profile import CompanyProfile
from app.domain.models.rnp import RnpRecord
from app.domain.models.seace import SeaceProviderRecord
from app.domain.models.sunat import SunatProfile


@dataclass(frozen=True, slots=True)
class CompanyResult:
    ruc: str
    profile: CompanyProfile | None = None
    seace: SeaceProviderRecord | None = None
    sunat: SunatProfile | None = None
    rnp: RnpRecord | None = None
    audit_entries: tuple[AuditResult, ...] = ()
