"""
DNA Analysis and Art Schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class DNAGenerateRequest(BaseModel):
    """Request to generate art from a species"""
    species_name: str = Field(..., min_length=2, description="Scientific or common name of the species")
    mutation_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Optional mutation rate to apply (0.0 - 1.0)")


class MutationRequest(BaseModel):
    """Request to simulate mutation on a sequence"""
    sequence: str = Field(..., min_length=10, description="DNA sequence to mutate")
    mutation_rate: float = Field(default=0.01, ge=0.001, le=0.5, description="Probability of mutation per base")


class ArtTraits(BaseModel):
    """Artistic traits derived from genetic data"""
    color_palette: List[str] = Field(..., description="Hex color codes generated from GC content")
    geometry_style: str = Field(..., description="Geometric style (e.g., 'spiral', 'fractal', 'helix')")
    complexity_score: float = Field(..., ge=0, le=100, description="Visual complexity based on sequence entropy")
    texture_type: str = Field(..., description="Texture style (e.g., 'smooth', 'granular', 'crystalline')")
    particle_count: int = Field(..., description="Number of particles for 3D visualization")


class DNAAnalysisResponse(BaseModel):
    """Detailed DNA analysis with art parameters"""
    species_name: str
    sequence_length: int
    gc_content: float
    nucleotide_counts: Dict[str, int]
    sequence_preview: str = Field(..., description="First 100 bases of sequence")
    genomic_signature: str = Field(..., description="Unique hash of the genetic sequence")
    art_traits: ArtTraits
    taxonomy: Optional[Dict[str, str]] = None
