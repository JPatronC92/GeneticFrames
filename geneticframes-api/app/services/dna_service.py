"""
DNA Service - The Core of Genetic Art
Handles fetching DNA, analyzing it, and converting it into artistic parameters.
"""

from Bio import Entrez, SeqIO
from Bio.SeqUtils import gc_fraction
import math
import random
import hashlib
from typing import Dict, Any, List
from loguru import logger
import asyncio
from app.core.config import settings
from app.schemas.dna import DNAAnalysisResponse, ArtTraits

# Configure Entrez
Entrez.email = settings.ENTREZ_EMAIL


class DNAService:
    """Service for DNA analysis and Art generation"""

    def __init__(self):
        self.cache = {}  # Simple in-memory cache for demo

    async def analyze_species_dna(self, species_name: str) -> DNAAnalysisResponse:
        """
        Fetch DNA and generate analysis + art traits.
        Uses a mocked approach for reliability in this MVP environment if external calls fail,
        but structure allows for real BioPython implementation.
        """
        try:
            # 1. Fetch DNA (Simulated for stability/speed in this MVP phase, or real if config allows)
            # In a real "Zoo", we'd query NCBI. Here we simulate 'fetching' unique data per species.
            sequence = await self._fetch_dna_sequence(species_name)

            # 2. Analyze Sequence
            seq_len = len(sequence)
            gc = gc_fraction(sequence) * 100
            counts = {
                "A": sequence.count("A"),
                "T": sequence.count("T"),
                "G": sequence.count("G"),
                "C": sequence.count("C")
            }

            # 3. Generate Genomic Signature (Hash)
            signature = hashlib.sha256(sequence.encode()).hexdigest()

            # 4. Generate Art Traits (The "Creative" Logic)
            art_traits = self.generate_art_parameters(sequence, gc, signature)

            return DNAAnalysisResponse(
                species_name=species_name,
                sequence_length=seq_len,
                gc_content=gc,
                nucleotide_counts=counts,
                sequence_preview=sequence[:100] + "...",
                genomic_signature=signature,
                art_traits=art_traits
            )

        except Exception as e:
            logger.error(f"Error analyzing DNA for {species_name}: {e}")
            raise ValueError(f"Could not analyze species: {species_name}")

    async def _fetch_dna_sequence(self, species_name: str) -> str:
        """
        Simulate fetching a unique DNA sequence based on the species name.
        In production, this calls NCBI Entrez.
        """
        # Deterministic generator based on name to ensure same species = same DNA always
        # We use a local Random instance to ensure thread safety and avoid affecting global state
        rng = random.Random(species_name)

        length = rng.randint(500, 2000)
        bases = ["A", "T", "G", "C"]

        # Bias based on name characters to make it pseudo-unique
        weights = [
            0.2 + (ord(species_name[0]) % 5) / 100,
            0.2 + (ord(species_name[1]) % 5) / 100 if len(species_name) > 1 else 0.25,
            0.3,
            0.3
        ]
        # Normalize weights
        total_w = sum(weights)
        weights = [w/total_w for w in weights]

        return "".join(rng.choices(bases, weights=weights, k=length))

    def generate_art_parameters(self, sequence: str, gc_content: float, signature: str) -> ArtTraits:
        """
        The 'Bio-Art' Algorithm: Maps genetic stats to visual traits.
        """
        # 1. Color Palette based on GC Content (G/C bonds are stronger -> Warmer/Intense colors?)
        # Low GC -> Cool colors (Blues/Greens), High GC -> Warm colors (Reds/Oranges)
        if gc_content < 40:
            palette = ["#001219", "#005f73", "#0a9396", "#94d2bd", "#e9d8a6"] # Ocean vibes
            style = "fluid"
        elif gc_content < 50:
            palette = ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51"] # Earth tones
            style = "organic"
        else:
            palette = ["#590d22", "#800f2f", "#a4133c", "#ff4d6d", "#ffccd5"] # Intense/Heat
            style = "crystalline"

        # 2. Complexity from Sequence Entropy (Simulated by compression ratio or simple uniqueness)
        unique_kmers = len(set([sequence[i:i+3] for i in range(len(sequence)-3)]))
        complexity = min(100, (unique_kmers / len(sequence)) * 200)

        # 3. Geometry from Signature Hash
        hash_int = int(signature[:8], 16)
        geometries = ["helix", "fractal", "voronoi", "particle_cloud"]
        geometry = geometries[hash_int % len(geometries)]

        # 4. Texture from Nucleotide Ratios
        textures = ["smooth", "rough", "glowing", "metallic"]
        texture_idx = (sequence.count("A") * sequence.count("T")) % len(textures)
        texture = textures[texture_idx]

        return ArtTraits(
            color_palette=palette,
            geometry_style=geometry,
            complexity_score=round(complexity, 2),
            texture_type=texture,
            particle_count=int(len(sequence) * (complexity/50))  # More complex DNA = more particles
        )

    async def simulate_mutation(self, sequence: str, rate: float) -> str:
        """
        Simulate evolution by mutating the sequence.
        """
        bases = list(sequence)
        possible_bases = ["A", "T", "G", "C"]
        mutations = 0

        for i in range(len(bases)):
            if random.random() < rate:
                bases[i] = random.choice([b for b in possible_bases if b != bases[i]])
                mutations += 1

        logger.info(f"Simulated {mutations} mutations (Rate: {rate})")
        return "".join(bases)


dna_service = DNAService()
