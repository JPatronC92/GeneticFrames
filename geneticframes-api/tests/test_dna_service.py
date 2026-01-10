import pytest
import vcr
from app.services.dna_service import dna_service, DNAService
from app.core.config import settings
from app.core.exceptions import SpeciesNotFoundError

# Configure VCR
my_vcr = vcr.VCR(
    cassette_library_dir='tests/cassettes',
    record_mode='once',
    match_on=['method', 'scheme', 'host', 'port', 'path', 'query'],
    filter_headers=['authorization']
)

@pytest.mark.asyncio
async def test_dna_generation_is_deterministic():
    """
    Verify that analyzing the same species name twice produces
    identical results (same sequence, same signature).
    Tests Simulation Mode.
    """
    # Ensure live mode is off
    original_mode = settings.NCBI_LIVE_MODE
    settings.NCBI_LIVE_MODE = False

    try:
        species = "Siberian Tiger"

        result1 = await dna_service.analyze_species_dna(species)
        result2 = await dna_service.analyze_species_dna(species)

        # Check Sequence match
        assert result1.sequence_preview == result2.sequence_preview

        # Check Art Traits match
        assert result1.art_traits.color_palette == result2.art_traits.color_palette
        assert result1.art_traits.geometry_style == result2.art_traits.geometry_style
        assert result1.genomic_signature == result2.genomic_signature
    finally:
        settings.NCBI_LIVE_MODE = original_mode

@pytest.mark.asyncio
async def test_different_species_produce_different_art():
    """
    Verify that two similar species produce different DNA sequences and Art.
    Tests Simulation Mode.
    """
    original_mode = settings.NCBI_LIVE_MODE
    settings.NCBI_LIVE_MODE = False

    try:
        species1 = "Siberian Tiger"
        species2 = "Jaguar"

        result1 = await dna_service.analyze_species_dna(species1)
        result2 = await dna_service.analyze_species_dna(species2)

        # Signatures must be different
        assert result1.genomic_signature != result2.genomic_signature

        # Art traits should differ
        assert result1.art_traits != result2.art_traits
    finally:
        settings.NCBI_LIVE_MODE = original_mode

@pytest.mark.asyncio
async def test_art_traits_structure():
    """
    Verify the structure of the returned ArtTraits
    Tests Simulation Mode.
    """
    original_mode = settings.NCBI_LIVE_MODE
    settings.NCBI_LIVE_MODE = False

    try:
        result = await dna_service.analyze_species_dna("Blue Whale")
        traits = result.art_traits

        assert isinstance(traits.color_palette, list)
        assert len(traits.color_palette) == 5
        assert traits.complexity_score >= 0 and traits.complexity_score <= 100
        assert traits.particle_count > 0
    finally:
        settings.NCBI_LIVE_MODE = original_mode

@pytest.mark.asyncio
@my_vcr.use_cassette('tests/cassettes/ncbi_real_integration.yaml')
async def test_real_ncbi_mode():
    """
    Test real NCBI fetching using VCR recording.
    """
    # Ensure live mode is ON
    original_mode = settings.NCBI_LIVE_MODE
    settings.NCBI_LIVE_MODE = True

    try:
        # We search for something specific like "Homo sapiens" which should have mitochondria data
        # Use a term likely to be found
        species = "Homo sapiens"

        # This will either fetch from NCBI (and record) or replay from cassette
        result = await dna_service.analyze_species_dna(species)

        assert result.species_name == species
        assert len(result.sequence_preview) > 0
        assert result.genomic_signature is not None
        # Real DNA should have non-zero GC content
        assert result.gc_content > 0

    finally:
        settings.NCBI_LIVE_MODE = original_mode

@pytest.mark.asyncio
@my_vcr.use_cassette('tests/cassettes/ncbi_not_found.yaml')
async def test_real_ncbi_not_found():
    """
    Test error handling when species is not found in NCBI.
    """
    original_mode = settings.NCBI_LIVE_MODE
    settings.NCBI_LIVE_MODE = True

    try:
        # Search for a nonsense species
        species = "XyzAbcNonExistentSpecies123"

        with pytest.raises(SpeciesNotFoundError):
            await dna_service.analyze_species_dna(species)

    finally:
        settings.NCBI_LIVE_MODE = original_mode

@pytest.mark.asyncio
async def test_redis_caching_logic():
    """
    Test that caching logic works (mocking the redis client).
    """
    # We create a new service instance to mock its redis
    service = DNAService()

    # Mock redis client using an AsyncMock if available or simple class
    class MockRedis:
        def __init__(self):
            self.store = {}

        async def get(self, key):
            return self.store.get(key)

        async def set(self, key, value, ex=None):
            self.store[key] = value

    service.redis = MockRedis()

    # Pre-populate cache
    species = "Cached Species"
    cache_key = f"dna_seq:{species.lower().replace(' ', '_')}"
    fake_sequence = "ATGC" * 10
    await service._set_cache(cache_key, fake_sequence)

    # Force live mode to trigger `_fetch_dna_sequence_real`
    original_mode = settings.NCBI_LIVE_MODE
    settings.NCBI_LIVE_MODE = True

    try:
        # Should return cached sequence without hitting NCBI (so no VCR needed)
        # We manually verify the cache logic in `_fetch_dna_sequence_real` uses `_get_cache` first
        result_seq = await service._fetch_dna_sequence_real(species)
        assert result_seq == fake_sequence

    finally:
        settings.NCBI_LIVE_MODE = original_mode
