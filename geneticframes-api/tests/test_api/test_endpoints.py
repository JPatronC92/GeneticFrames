import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_species_data(client: AsyncClient):
    # Depending on the mock data, we can test for a known species
    # "Tiger" is in the mock DB in animal_search.py
    response = await client.get("/api/v1/species/search?query=tiger&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "tiger"
    assert len(data["results"]) > 0
    assert data["results"][0]["common_name"] == "Tiger"

@pytest.mark.asyncio
async def test_get_popular_species(client: AsyncClient):
    response = await client.get("/api/v1/species/popular?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 5
    assert "common_name" in data[0]

@pytest.mark.asyncio
async def test_analyze_dna(client: AsyncClient):
    # Test DNA analysis endpoint
    payload = {
      "species_name": "Tiger",
      "mutation_rate": 0
    }
    response = await client.post("/api/v1/dna/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["species_name"] == "Tiger"
    assert "genomic_signature" in data
    assert "art_traits" in data

@pytest.mark.asyncio
async def test_analyze_dna_with_mutation(client: AsyncClient):
    # Test DNA analysis endpoint with mutation
    payload = {
      "species_name": "Tiger",
      "mutation_rate": 0.1
    }
    response = await client.post("/api/v1/dna/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["species_name"] == "Tiger"
    assert "mutated" in data["genomic_signature"]
    assert "art_traits" in data
