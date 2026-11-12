from app.infrastructure.inbound.dto.response.person_response import PersonResponse
from app.application.dto.command.get_person_command import GetPersonCommand
from app.application.dto.result.person_result import PersonResult


def to_command(dni: str) -> GetPersonCommand:
    return GetPersonCommand(dni=dni)


def to_response(result: PersonResult) -> PersonResponse:
    return PersonResponse.model_validate(result)
