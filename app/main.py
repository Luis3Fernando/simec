from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.inbound.controller.v1.router import api_router
from app.infrastructure.inbound.docs.openapi import API_METADATA

app = FastAPI(**API_METADATA)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
