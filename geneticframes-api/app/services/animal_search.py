"""
Animal Search Service
Handles species lookup and "Zoo Exhibit" categorization.
"""

from typing import List, Dict
import asyncio
from app.schemas.species import SpeciesResult

class AnimalSearchService:
    """Service for searching animals and organizing exhibits"""

    # Mock database for MVP
    SPECIES_DB = [
        {"common": "Tiger", "scientific": "Panthera tigris", "group": "Apex Predators"},
        {"common": "Blue Whale", "scientific": "Balaenoptera musculus", "group": "Deep Sea Giants"},
        {"common": "Eagle", "scientific": "Aquila chrysaetos", "group": "Sky Monarchs"},
        {"common": "Clownfish", "scientific": "Amphiprioninae", "group": "Coral Reef"},
        {"common": "Axolotl", "scientific": "Ambystoma mexicanum", "group": "Strange & Rare"},
        {"common": "Pangolin", "scientific": "Manidae", "group": "Endangered Gems"},
        {"common": "Komodo Dragon", "scientific": "Varanus komodoensis", "group": "Living Fossils"},
        {"common": "Snow Leopard", "scientific": "Panthera uncia", "group": "Mountain Ghosts"},
        {"common": "Octopus", "scientific": "Octopoda", "group": "Deep Sea Giants"},
        {"common": "Wolf", "scientific": "Canis lupus", "group": "Apex Predators"},
    ]

    async def search_comprehensive(self, query: str, limit: int = 10) -> List[SpeciesResult]:
        """Search for species by name"""
        query = query.lower()
        results = []

        for sp in self.SPECIES_DB:
            if query in sp["common"].lower() or query in sp["scientific"].lower():
                results.append(SpeciesResult(
                    common_name=sp["common"],
                    scientific_name=sp["scientific"],
                    confidence=1.0,
                    source="GeneticFrames Zoo DB",
                    taxonomy={"group": sp["group"]}
                ))

        # Demo Fallback: If no exact match, allow a "Generated" result
        # This allows the demo to feel "infinite" even with a small DB
        if not results and len(query) > 2:
            results.append(SpeciesResult(
                common_name=query.title(),
                scientific_name=f"{query.capitalize()} (Gen)",
                confidence=0.8,
                source="GeneticFrames AI Generator",
                taxonomy={"group": "New Discoveries"}
            ))

        return results[:limit]

    async def get_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """Autocomplete suggestions"""
        query = query.lower()
        return [sp["common"] for sp in self.SPECIES_DB if query in sp["common"].lower()][:limit]

    async def get_zoo_exhibits(self) -> Dict[str, List[SpeciesResult]]:
        """
        Organize species into Zoo Exhibits (Zones).
        This creates the "Zoo" structure.
        """
        exhibits = {}

        for sp in self.SPECIES_DB:
            group = sp["group"]
            if group not in exhibits:
                exhibits[group] = []

            exhibits[group].append(SpeciesResult(
                common_name=sp["common"],
                scientific_name=sp["scientific"],
                confidence=1.0,
                taxonomy={"group": group}
            ))

        return exhibits

animal_search_service = AnimalSearchService()
