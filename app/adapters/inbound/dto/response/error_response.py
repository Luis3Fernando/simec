from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str = Field(description="Descripción del error", examples=["Internal error while fetching company"])
