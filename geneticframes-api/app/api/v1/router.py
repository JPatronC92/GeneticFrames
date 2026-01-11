"""
API v1 Router - Aggregates all endpoints
"""

from fastapi import APIRouter

from app.api.v1.endpoints import alphafold, dna, species

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    species.router,
    prefix="/species",
    tags=["species"]
)

api_router.include_router(
    dna.router,
    prefix="/dna",
    tags=["dna"]
)

api_router.include_router(
    alphafold.router,
    prefix="/alphafold",
    tags=["alphafold"]
)
