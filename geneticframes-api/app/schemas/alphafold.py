"""
AlphaFold Protein Structure Schemas
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List


class ConfidenceScore(BaseModel):
    """Confidence score for protein structure prediction"""
    avg_confidence: float = Field(..., ge=0, le=100, description="Average pLDDT score")
    per_residue: Optional[List[float]] = Field(default=None, description="Per-residue confidence scores")


class ProteinStructureResponse(BaseModel):
    """AlphaFold protein structure data"""
    uniprot_id: str = Field(..., description="UniProt accession ID")
    sequence_length: int = Field(..., gt=0, description="Protein sequence length")
    pdb_url: HttpUrl = Field(..., description="URL to download PDB file")
    cif_url: Optional[HttpUrl] = Field(default=None, description="URL to download mmCIF file")
    confidence: ConfidenceScore
    visualization_url: HttpUrl = Field(..., description="AlphaFold web viewer URL")
    organism: Optional[str] = Field(default=None, description="Source organism")
    protein_name: Optional[str] = Field(default=None, description="Protein name/description")


class ProteinAvailability(BaseModel):
    """Check if protein structure is available"""
    species: str
    available: bool
    uniprot_id: Optional[str] = None
    source: str = "AlphaFold Database"
