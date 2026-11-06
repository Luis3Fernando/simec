from fastapi import APIRouter

from app.adapters.inbound.api.v1.endpoints import providers

api_router = APIRouter()
api_router.include_router(providers.router, prefix="/providers", tags=["Providers"])
