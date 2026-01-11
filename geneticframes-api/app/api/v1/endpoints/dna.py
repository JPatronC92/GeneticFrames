"""
DNA Analysis Endpoint
Fetch and analyze DNA sequences from NCBI
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from loguru import logger

from app.core.cache import cache_manager
from app.schemas.dna import DNAAnalysisResponse, DNAGenerateRequest, MutationRequest
from app.services.dna_service import dna_service

router = APIRouter()


@router.post("/analyze", response_model=DNAAnalysisResponse)
async def analyze_dna(request: DNAGenerateRequest):
    """
    Fetch and analyze DNA sequence for a species.
    Includes 'Art Traits' generation.
    """
    try:
        # Check cache first
        cache_key = f"dna:{request.species_name}:{request.mutation_rate}"
        cached = await cache_manager.get(cache_key)

        if cached:
            logger.info(f"Cache hit for {request.species_name}")
            return DNAAnalysisResponse(**cached)

        # Fetch and analyze DNA
        result = await dna_service.analyze_species_dna(request.species_name)

        # Apply mutation if requested (Simulating Evolution)
        if request.mutation_rate > 0:
            result = await dna_service.process_mutation_simulation(request.species_name, request.mutation_rate)

        # Cache the result
        await cache_manager.set(cache_key, result.dict(), ttl=3600)

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"DNA analysis error for {request.species_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze DNA: {str(e)}"
        )


@router.post("/mutate", response_model=str)
async def mutate_sequence(request: MutationRequest):
    """
    Simulate evolution: Mutate a raw DNA sequence
    """
    return await dna_service.simulate_mutation(request.sequence, request.mutation_rate)


@router.post("/generate-art")
async def generate_art(request: DNAGenerateRequest, background_tasks: BackgroundTasks):
    """
    Generate DNA art from species sequence

    Returns art parameters and visualization data
    """
    try:
        # Get DNA analysis
        analysis = await dna_service.analyze_species_dna(request.species_name)

        # Generate art parameters
        art_data = await dna_service.generate_art_parameters(analysis)

        return {
            "species": request.species_name,
            "analysis": analysis.dict(),
            "art": art_data,
            "status": "generated"
        }

    except Exception as e:
        logger.error(f"Art generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
