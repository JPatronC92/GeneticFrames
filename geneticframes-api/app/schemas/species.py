"""
Species Search Schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class SpeciesResult(BaseModel):
    """Single species search result"""
    common_name: str = Field(..., description="Common name (e.g., Tiger)")
    scientific_name: str = Field(..., description="Scientific name (e.g., Panthera tigris)")
    confidence: float = Field(..., ge=0, le=1, description="Match confidence score")
    source: str = Field(default="curated_database", description="Data source")
    taxonomy: Optional[dict] = Field(default=None, description="Taxonomic classification")


class SpeciesSearchResponse(BaseModel):
    """Response for species search"""
    query: str
    results: List[SpeciesResult]
    total: int
