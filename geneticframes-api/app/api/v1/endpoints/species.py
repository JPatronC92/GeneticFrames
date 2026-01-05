"""
Species Search Endpoint
Search for animals by common or scientific name
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
from loguru import logger

from app.services.animal_search import animal_search_service
from app.schemas.species import SpeciesSearchResponse, SpeciesResult

router = APIRouter()


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
        # Return curated popular species
        popular = [
            {"common_name": "Tiger", "scientific_name": "Panthera tigris", "confidence": 1.0},
            {"common_name": "Blue Whale", "scientific_name": "Balaenoptera musculus", "confidence": 1.0},
            {"common_name": "Eagle", "scientific_name": "Aquila chrysaetos", "confidence": 1.0},
            {"common_name": "Dolphin", "scientific_name": "Tursiops truncatus", "confidence": 1.0},
            {"common_name": "Elephant", "scientific_name": "Loxodonta africana", "confidence": 1.0},
            {"common_name": "Great White Shark", "scientific_name": "Carcharodon carcharias", "confidence": 1.0},
            {"common_name": "Butterfly", "scientific_name": "Danaus plexippus", "confidence": 1.0},
            {"common_name": "Python", "scientific_name": "Python reticulatus", "confidence": 1.0},
        ]
        
        return [SpeciesResult(**sp) for sp in popular[:limit]]
    
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
