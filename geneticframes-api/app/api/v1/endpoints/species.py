"""
Species Search Endpoint
Search for animals by common or scientific name
"""

from typing import Dict, List

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.schemas.species import SpeciesResult, SpeciesSearchResponse
from app.services.animal_search import animal_search_service

router = APIRouter()


@router.get("/exhibits", response_model=Dict[str, List[SpeciesResult]])
async def get_zoo_exhibits():
    """
    Get all species categorized by 'Zoo Exhibit' (Zone).
    e.g., 'Deep Sea Giants', 'Apex Predators'.
    """
    return await animal_search_service.get_zoo_exhibits()


@router.get("/search", response_model=SpeciesSearchResponse)
async def search_species(
    query: str = Query(..., min_length=2, description="Animal name to search"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """
    Search for species by common or scientific name

    Supports:
    - English and Spanish common names
    - Scientific names
    - Partial matching
    """
    try:
        results = await animal_search_service.search_comprehensive(query, limit=limit)

        return SpeciesSearchResponse(
            query=query,
            results=results,
            total=len(results)
        )

    except Exception as e:
        logger.error(f"Error searching species '{query}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search species: {str(e)}"
        )


@router.get("/popular", response_model=List[SpeciesResult])
async def get_popular_species(limit: int = Query(10, ge=1, le=50)):
    """Get most popular/recently searched species"""
    try:
        return await animal_search_service.get_popular_species(limit=limit)

    except Exception as e:
        logger.error(f"Error getting popular species: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/autocomplete")
async def autocomplete_species(
    query: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20)
):
    """Fast autocomplete for species search"""
    try:
        suggestions = await animal_search_service.get_suggestions(query, limit=limit)
        return {"suggestions": suggestions}

    except Exception as e:
        logger.error(f"Autocomplete error: {e}")
        return {"suggestions": []}
