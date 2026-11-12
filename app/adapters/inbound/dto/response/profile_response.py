from pydantic import Field

from app.adapters.inbound.dto.response.base import ResponseModel


class PersonProfileResponse(ResponseModel):
    document_number: str = Field(description="Número de DNI", examples=["44900952"])
    full_name: str = Field(description="Nombre completo", examples=["RONALD RUIZ AUCCAPIÑA"])
    given_names: str | None = Field(description="Nombres", examples=["RONALD"])
    first_surname: str | None = Field(description="Apellido paterno", examples=["RUIZ"])
    second_surname: str | None = Field(description="Apellido materno", examples=["AUCCAPIÑA"])
    check_digit: str | None = Field(description="Dígito verificador del DNI")


class CompanyProfileResponse(ResponseModel):
    document_number: str = Field(description="Número de RUC", examples=["20607524476"])
    legal_name: str = Field(description="Razón social", examples=["INVERSIONES Y SERVICIOS HUAYNA DEL PERU E.I.R.L."])
    status: str | None = Field(description="Estado del contribuyente", examples=["BAJA DE OFICIO"])
    condition: str | None = Field(description="Condición de domicilio", examples=["HABIDO"])
    address: str | None = Field(description="Domicilio fiscal completo")
    ubigeo: str | None = Field(description="Código de ubigeo del INEI", examples=["080104"])
    department: str | None = Field(description="Departamento", examples=["CUSCO"])
    province: str | None = Field(description="Provincia", examples=["CUSCO"])
    district: str | None = Field(description="Distrito", examples=["SAN JERONIMO"])
    via_type: str | None = Field(description="Tipo de vía", examples=["CAL."])
    via_name: str | None = Field(description="Nombre de la vía")
    zone_type: str | None = Field(description="Nombre de la zona")
    zone_code: str | None = Field(description="Tipo de zona", examples=["APV."])
    number: str | None = Field(description="Número")
    lot: str | None = Field(description="Lote", examples=["H-1"])
    apartment: str | None = Field(description="Departamento o interior")
    block: str | None = Field(description="Manzana")
    kilometer: str | None = Field(description="Kilómetro")
