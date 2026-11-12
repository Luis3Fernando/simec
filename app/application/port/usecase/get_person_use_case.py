from abc import ABC, abstractmethod

from app.application.dto.command.get_person_command import GetPersonCommand
from app.application.dto.result.person_result import PersonResult


class GetPersonUseCase(ABC):
    @abstractmethod
    async def execute(self, command: GetPersonCommand) -> PersonResult: ...
