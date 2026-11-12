from app.application.dto.command.get_company_command import GetCompanyCommand
from app.application.dto.result.company_result import CompanyResult
from app.application.port.out.extractor_port import ExtractorPort
from app.application.port.usecase.get_company_use_case import GetCompanyUseCase
from app.application.services.source_runner import DEFAULT_TIMEOUT_S, run_sources
from app.domain.models.profile import CompanyProfile
from app.domain.models.rnp import RnpRecord
from app.domain.models.seace import SeaceProviderRecord
from app.domain.models.sunat import SunatProfile


class GetCompanyService(GetCompanyUseCase):
    def __init__(
        self,
        profile: ExtractorPort,
        seace: ExtractorPort,
        sunat: ExtractorPort,
        rnp: ExtractorPort,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        self._sources = {"profile": profile, "seace": seace, "sunat": sunat, "rnp": rnp}
        self._timeout_s = timeout_s

    async def execute(self, command: GetCompanyCommand) -> CompanyResult:
        results = await run_sources(self._sources, command.ruc, self._timeout_s)
        return CompanyResult(
            ruc=command.ruc,
            profile=results["profile"].data_as(CompanyProfile),
            seace=results["seace"].data_as(SeaceProviderRecord),
            sunat=results["sunat"].data_as(SunatProfile),
            rnp=results["rnp"].data_as(RnpRecord),
            audit_entries=tuple(result.audit for result in results.values()),
        )
