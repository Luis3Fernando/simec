from fastapi import APIRouter

from app.infrastructure.inbound.controller.v1 import company_controller, person_controller

api_router = APIRouter()
api_router.include_router(company_controller.router, prefix="/companies", tags=["Companies"])
api_router.include_router(person_controller.router, prefix="/persons", tags=["Persons"])
