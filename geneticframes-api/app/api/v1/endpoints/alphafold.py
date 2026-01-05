"""
AlphaFold Integration Endpoint
Protein structure prediction and visualization
"""

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.services.alphafold_service import alphafold_service
from app.schemas.alphafold import ProteinStructureResponse
from app.core.config import settings

router = APIRouter()


@router.get("/protein/{uniprot_id}", response_model=ProteinStructureResponse)
async def get_protein_structure(
    uniprot_id: str = Query(..., description="UniProt accession ID")
):
    """
    Get protein structure from AlphaFold Database
    
    Args:
        uniprot_id: UniProt accession (e.g., P12345)
    
    Returns:
        Protein structure data including PDB file URL, confidence scores, etc.
    """
    if not settings.ALPHAFOLD_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="AlphaFold integration is disabled"
        )
    
    try:
        structure = await alphafold_service.get_protein_structure(uniprot_id)
        
        if not structure:
            raise HTTPException(
                status_code=404,
                detail=f"No structure found for UniProt ID: {uniprot_id}"
            )
        
        return structure
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"AlphaFold API error for {uniprot_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch protein structure: {str(e)}"
        )


@router.get("/species/{scientific_name}")
async def get_species_protein(scientific_name: str):
    """
    Get protein structure for a species by scientific name
    
    Maps species → UniProt ID → AlphaFold structure
    """
    try:
        # Map species to UniProt ID
        uniprot_id = await alphafold_service.map_species_to_uniprot(scientific_name)
        
        if not uniprot_id:
            raise HTTPException(
                status_code=404,
                detail=f"No protein mapping found for {scientific_name}"
            )
        
        # Get structure
        structure = await alphafold_service.get_protein_structure(uniprot_id)
        
        return {
            "species": scientific_name,
            "uniprot_id": uniprot_id,
            "structure": structure.dict() if structure else None
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Species protein error for {scientific_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available/{species_name}")
async def check_protein_availability(species_name: str):
    """Check if protein structure is available for a species"""
    try:
        available = await alphafold_service.check_availability(species_name)
        return {
            "species": species_name,
            "available": available,
            "source": "AlphaFold Database"
        }
    
    except Exception as e:
        logger.error(f"Availability check error: {e}")
        return {
            "species": species_name,
            "available": False,
            "error": str(e)
        }
