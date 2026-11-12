from abc import ABC, abstractmethod

from app.application.dto.command.get_company_command import GetCompanyCommand
from app.application.dto.result.company_result import CompanyResult


class GetCompanyUseCase(ABC):
    @abstractmethod
    async def execute(self, command: GetCompanyCommand) -> CompanyResult: ...
