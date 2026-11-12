from app.application.dto.command.get_person_command import GetPersonCommand
from app.application.dto.result.person_result import PersonResult
from app.application.port.out.extractor_port import ExtractorPort
from app.application.port.usecase.get_person_use_case import GetPersonUseCase
from app.application.services.source_runner import DEFAULT_TIMEOUT_S, run_sources
from app.domain.models.profile import PersonProfile
from app.domain.models.seace import SeacePersonRecord
from app.domain.models.sunat import SunatProfile


class GetPersonService(GetPersonUseCase):
    def __init__(
        self,
        profile: ExtractorPort,
        seace: ExtractorPort,
        sunat: ExtractorPort,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        self._sources = {"profile": profile, "seace": seace, "sunat": sunat}
        self._timeout_s = timeout_s

    async def execute(self, command: GetPersonCommand) -> PersonResult:
        results = await run_sources(self._sources, command.dni, self._timeout_s)
        return PersonResult(
            dni=command.dni,
            profile=results["profile"].data_as(PersonProfile),
            seace=results["seace"].data_as(SeacePersonRecord),
            sunat=results["sunat"].data_as(SunatProfile),
            audit_entries=tuple(result.audit for result in results.values()),
        )
