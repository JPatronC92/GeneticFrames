import pytest
from app.services.dna_service import dna_service

@pytest.mark.asyncio
async def test_dna_generation_is_deterministic():
    """
    Verify that analyzing the same species name twice produces
    identical results (same sequence, same signature).
    """
    species = "Siberian Tiger"

    result1 = await dna_service.analyze_species_dna(species)
    result2 = await dna_service.analyze_species_dna(species)

    # Check Sequence match
    assert result1.sequence_preview == result2.sequence_preview

    # Check Art Traits match
    assert result1.art_traits.color_palette == result2.art_traits.color_palette
    assert result1.art_traits.geometry_style == result2.art_traits.geometry_style
    assert result1.genomic_signature == result2.genomic_signature

@pytest.mark.asyncio
async def test_different_species_produce_different_art():
    """
    Verify that two similar species produce different DNA sequences and Art.
    """
    species1 = "Siberian Tiger"
    species2 = "Jaguar"

    result1 = await dna_service.analyze_species_dna(species1)
    result2 = await dna_service.analyze_species_dna(species2)

    # Signatures must be different
    assert result1.genomic_signature != result2.genomic_signature

    # Art traits should differ (high probability, but strictly signatures must differ)
    # We check the object as a whole to ensure they are not clones
    assert result1.art_traits != result2.art_traits

@pytest.mark.asyncio
async def test_art_traits_structure():
    """
    Verify the structure of the returned ArtTraits
    """
    result = await dna_service.analyze_species_dna("Blue Whale")
    traits = result.art_traits

    assert isinstance(traits.color_palette, list)
    assert len(traits.color_palette) == 5
    assert traits.complexity_score >= 0 and traits.complexity_score <= 100
    assert traits.particle_count > 0
