from app.infrastructure.inbound.dto.response.company_response import CompanyResponse
from app.application.dto.command.get_company_command import GetCompanyCommand
from app.application.dto.result.company_result import CompanyResult


def to_command(ruc: str) -> GetCompanyCommand:
    return GetCompanyCommand(ruc=ruc)


def to_response(result: CompanyResult) -> CompanyResponse:
    return CompanyResponse.model_validate(result)
