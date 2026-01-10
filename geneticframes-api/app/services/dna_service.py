"""
DNA Service - The Core of Genetic Art
Handles fetching DNA, analyzing it, and converting it into artistic parameters.
"""

from Bio import Entrez
from Bio.SeqUtils import gc_fraction
import math
import random
import hashlib
from typing import Dict, Any, List, Optional
from loguru import logger
import asyncio
import redis.asyncio as redis
from app.core.config import settings
from app.schemas.dna import DNAAnalysisResponse, ArtTraits
from app.core.exceptions import SpeciesNotFoundError, NCBIConnectionError

# Configure Entrez
Entrez.email = settings.ENTREZ_EMAIL


class DNAService:
    """Service for DNA analysis and Art generation"""

    def __init__(self):
        # Initialize Redis connection if enabled
        self.redis: Optional[redis.Redis] = None
        if settings.REDIS_ENABLED:
            try:
                self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
                logger.info("Redis initialized for DNAService")
            except Exception as e:
                logger.error(f"Failed to initialize Redis: {e}")
                self.redis = None

        self.local_cache = {}  # Fallback in-memory cache

    async def _get_cache(self, key: str) -> Optional[str]:
        """Get value from cache (Redis or local)"""
        if self.redis:
            try:
                return await self.redis.get(key)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
                return None
        return self.local_cache.get(key)

    async def _set_cache(self, key: str, value: str, ttl: int = 3600):
        """Set value in cache (Redis or local)"""
        if self.redis:
            try:
                await self.redis.set(key, value, ex=ttl)
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
        else:
            self.local_cache[key] = value

    async def analyze_species_dna(self, species_name: str) -> DNAAnalysisResponse:
        """
        Fetch DNA and generate analysis + art traits.
        Uses a mocked approach or real NCBI calls based on configuration.
        """
        try:
            # 1. Fetch DNA
            if settings.NCBI_LIVE_MODE:
                sequence = await self._fetch_dna_sequence_real(species_name)
            else:
                sequence = await self._fetch_dna_sequence_simulated(species_name)

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

        except (SpeciesNotFoundError, NCBIConnectionError):
            raise
        except Exception as e:
            logger.error(f"Error analyzing DNA for {species_name}: {e}")
            raise ValueError(f"Could not analyze species: {species_name}")

    async def _fetch_dna_sequence_simulated(self, species_name: str) -> str:
        """
        Simulate fetching a unique DNA sequence based on the species name.
        """
        # Deterministic generator based on name
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

    async def _fetch_dna_sequence_real(self, species_name: str) -> str:
        """
        Fetch real DNA sequence from NCBI Entrez.
        """
        cache_key = f"dna_seq:{species_name.lower().replace(' ', '_')}"
        cached_seq = await self._get_cache(cache_key)
        if cached_seq:
            logger.info(f"Cache hit for {species_name}")
            return cached_seq

        try:
            # 1. Search for the species
            logger.info(f"Searching NCBI for {species_name}...")
            # Run blocking Entrez calls in a thread pool
            loop = asyncio.get_running_loop()

            # ESearch: Find the ID
            # Use 'mitochondrion' in title as it's more reliable for finding manageable sequences like mtDNA
            # or fallback to just organism if needed (but that might be huge)
            search_term = f"{species_name}[Organism] AND mitochondrion[title]"

            handle_search = await loop.run_in_executor(
                None,
                lambda: Entrez.esearch(db="nucleotide", term=search_term, retmax=1)
            )
            search_record = await loop.run_in_executor(
                None,
                lambda: Entrez.read(handle_search)
            )
            handle_search.close()

            if not search_record["IdList"]:
                logger.warning(f"No DNA found for {species_name}")
                raise SpeciesNotFoundError(species_name)

            ncbi_id = search_record["IdList"][0]

            # 2. Fetch the sequence
            logger.info(f"Fetching sequence ID {ncbi_id}...")
            handle_fetch = await loop.run_in_executor(
                None,
                lambda: Entrez.efetch(db="nucleotide", id=ncbi_id, rettype="fasta", retmode="text")
            )
            data = await loop.run_in_executor(None, handle_fetch.read)
            handle_fetch.close()

            # Parse FASTA (simple parsing as we just want the sequence)
            # Biopython SeqIO usually needs a file handle, but we can iterate lines
            lines = data.strip().split('\n')
            # Skip header and join the rest
            sequence = "".join([line for line in lines if not line.startswith(">")])

            if not sequence:
                 raise ValueError("Empty sequence returned")

            # Cache the result
            await self._set_cache(cache_key, sequence, ttl=settings.CACHE_TTL_SECONDS)

            return sequence

        except SpeciesNotFoundError:
            raise
        except Exception as e:
            logger.error(f"NCBI Error: {e}")
            raise NCBIConnectionError(str(e))

    def generate_art_parameters(self, sequence: str, gc_content: float, signature: str) -> ArtTraits:
        """
        The 'Bio-Art' Algorithm: Maps genetic stats to visual traits.
        """
        # 1. Color Palette based on GC Content
        if gc_content < 40:
            palette = ["#001219", "#005f73", "#0a9396", "#94d2bd", "#e9d8a6"] # Ocean vibes
            style = "fluid"
        elif gc_content < 50:
            palette = ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51"] # Earth tones
            style = "organic"
        else:
            palette = ["#590d22", "#800f2f", "#a4133c", "#ff4d6d", "#ffccd5"] # Intense/Heat
            style = "crystalline"

        # 2. Complexity from Sequence Entropy
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
