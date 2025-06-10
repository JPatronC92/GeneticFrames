"""
Animal Search System - Helps users find scientific names from common names
Uses multiple databases and APIs for comprehensive species lookup
"""
import requests
import json
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class AnimalSearchEngine:
    """Comprehensive animal search engine for scientific name lookup"""
    
    def __init__(self):
        # Base URLs for different APIs
        self.gbif_base = "https://api.gbif.org/v1"
        self.eol_base = "https://eol.org/api"
        self.itis_base = "https://www.itis.gov/ITISWebService/jsonservice"
        
        # Expanded common name to scientific name mapping
        self.common_to_scientific = {
            # Mammals
            "tiger": "Panthera tigris",
            "siberian tiger": "Panthera tigris altaica",
            "lion": "Panthera leo",
            "leopard": "Panthera pardus",
            "elephant": "Loxodonta africana",
            "african elephant": "Loxodonta africana",
            "asian elephant": "Elephas maximus",
            "blue whale": "Balaenoptera musculus",
            "humpback whale": "Megaptera novaeangliae",
            "sperm whale": "Physeter macrocephalus",
            "dolphin": "Tursiops truncatus",
            "bottlenose dolphin": "Tursiops truncatus",
            "wolf": "Canis lupus",
            "dog": "Canis lupus familiaris",
            "cat": "Felis catus",
            "horse": "Equus caballus",
            "cow": "Bos taurus",
            "pig": "Sus scrofa",
            "sheep": "Ovis aries",
            "goat": "Capra hircus",
            "bear": "Ursus americanus",
            "polar bear": "Ursus maritimus",
            "brown bear": "Ursus arctos",
            "panda": "Ailuropoda melanoleuca",
            "giant panda": "Ailuropoda melanoleuca",
            "orangutan": "Pongo pygmaeus",
            "sumatran orangutan": "Pongo abelii",
            "chimpanzee": "Pan troglodytes",
            "gorilla": "Gorilla gorilla",
            "human": "Homo sapiens",
            "rhinoceros": "Rhinoceros unicornis",
            "indian rhinoceros": "Rhinoceros unicornis",
            "white rhinoceros": "Ceratotherium simum",
            "hippopotamus": "Hippopotamus amphibius",
            "giraffe": "Giraffa camelopardalis",
            "zebra": "Equus zebra",
            "kangaroo": "Macropus rufus",
            "koala": "Phascolarctos cinereus",
            
            # Birds
            "eagle": "Aquila chrysaetos",
            "bald eagle": "Haliaeetus leucocephalus",
            "owl": "Bubo bubo",
            "penguin": "Aptenodytes forsteri",
            "emperor penguin": "Aptenodytes forsteri",
            "chicken": "Gallus gallus",
            "duck": "Anas platyrhynchos",
            "swan": "Cygnus olor",
            "flamingo": "Phoenicopterus roseus",
            "parrot": "Psittacus erithacus",
            "peacock": "Pavo cristatus",
            "ostrich": "Struthio camelus",
            "condor": "Vultur gryphus",
            "albatross": "Diomedea exulans",
            
            # Reptiles and Amphibians
            "crocodile": "Crocodylus niloticus",
            "nile crocodile": "Crocodylus niloticus",
            "alligator": "Alligator mississippiensis",
            "snake": "Python regius",
            "python": "Python reticulatus",
            "cobra": "Naja naja",
            "turtle": "Chelonia mydas",
            "sea turtle": "Chelonia mydas",
            "tortoise": "Testudo graeca",
            "iguana": "Iguana iguana",
            "gecko": "Gekko gecko",
            "lizard": "Lacerta agilis",
            "frog": "Rana temporaria",
            "toad": "Bufo bufo",
            "salamander": "Salamandra salamandra",
            "tuatara": "Sphenodon punctatus",
            
            # Fish and Marine Life
            "shark": "Carcharodon carcharias",
            "great white shark": "Carcharodon carcharias",
            "whale shark": "Rhincodon typus",
            "hammerhead shark": "Sphyrna mokarran",
            "tuna": "Thunnus thynnus",
            "salmon": "Salmo salar",
            "cod": "Gadus morhua",
            "bass": "Micropterus salmoides",
            "trout": "Oncorhynchus mykiss",
            "octopus": "Octopus vulgaris",
            "squid": "Loligo vulgaris",
            "jellyfish": "Aurelia aurita",
            "immortal jellyfish": "Turritopsis dohrnii",
            "seahorse": "Hippocampus hippocampus",
            "starfish": "Asterias rubens",
            "crab": "Cancer pagurus",
            "lobster": "Homarus gammarus",
            "shrimp": "Penaeus monodon",
            "coral": "Acropora palmata",
            "sea urchin": "Echinometra lucunter",
            "coelacanth": "Latimeria chalumnae",
            
            # Invertebrates
            "butterfly": "Danaus plexippus",
            "monarch butterfly": "Danaus plexippus",
            "bee": "Apis mellifera",
            "honeybee": "Apis mellifera",
            "ant": "Formica rufa",
            "spider": "Latrodectus hesperus",
            "black widow": "Latrodectus hesperus",
            "dragonfly": "Libellula quadrimaculata",
            "fly": "Drosophila melanogaster",
            "fruit fly": "Drosophila melanogaster",
            "mosquito": "Aedes aegypti",
            "beetle": "Tribolium castaneum",
            "flour beetle": "Tribolium castaneum",
            "ladybug": "Harmonia axyridis",
            "grasshopper": "Locusta migratoria",
            "cricket": "Acheta domesticus",
            "cockroach": "Blattella germanica",
            "german cockroach": "Blattella germanica",
            "water bear": "Hypsibius dujardini",
            "tardigrade": "Hypsibius dujardini",
            
            # Extinct species
            "tyrannosaurus": "Tyrannosaurus rex",
            "t-rex": "Tyrannosaurus rex",
            "triceratops": "Triceratops horridus",
            "velociraptor": "Velociraptor mongoliensis",
            "mammoth": "Mammuthus primigenius",
            "woolly mammoth": "Mammuthus primigenius",
            "saber tooth tiger": "Smilodon fatalis",
            "dodo": "Raphus cucullatus",
            
            # Microorganisms
            "e coli": "Escherichia coli",
            "escherichia coli": "Escherichia coli",
            "salmonella": "Salmonella enterica",
            "yeast": "Saccharomyces cerevisiae",
            "covid": "SARS-CoV-2",
            "coronavirus": "SARS-CoV-2",
            "sars": "SARS-CoV",
            "influenza": "Influenza A virus",
            "flu": "Influenza A virus",
            "malaria": "Plasmodium falciparum",
            
            # Plants (bonus)
            "rose": "Rosa rubiginosa",
            "oak": "Quercus robur",
            "pine": "Pinus sylvestris",
            "wheat": "Triticum aestivum",
            "rice": "Oryza sativa",
            "corn": "Zea mays",
            "tomato": "Solanum lycopersicum",
            "potato": "Solanum tuberosum",
            "apple": "Malus domestica",
            "banana": "Musa acuminata"
        }
    
    def search_local_database(self, query: str) -> List[Dict]:
        """Search in local common name database"""
        query_lower = query.lower().strip()
        results = []
        
        # Exact match
        if query_lower in self.common_to_scientific:
            results.append({
                "common_name": query.title(),
                "scientific_name": self.common_to_scientific[query_lower],
                "confidence": 1.0,
                "source": "curated_database",
                "type": "exact_match"
            })
        
        # Partial matches
        for common, scientific in self.common_to_scientific.items():
            if query_lower in common or common in query_lower:
                if len(results) < 10:  # Limit results
                    confidence = 0.8 if query_lower in common else 0.6
                    results.append({
                        "common_name": common.title(),
                        "scientific_name": scientific,
                        "confidence": confidence,
                        "source": "curated_database",
                        "type": "partial_match"
                    })
        
        return results
    
    def search_gbif_api(self, query: str) -> List[Dict]:
        """Search GBIF (Global Biodiversity Information Facility) API"""
        try:
            # Search for species by name
            url = f"{self.gbif_base}/species/search"
            params = {
                "q": query,
                "rank": "SPECIES",
                "status": "ACCEPTED",
                "limit": 10
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get("results", []):
                    if item.get("scientificName") and item.get("kingdom"):
                        # Filter for animals (exclude plants, fungi, etc.)
                        kingdom = item.get("kingdom", "").lower()
                        if kingdom in ["animalia", "animal"]:
                            results.append({
                                "common_name": item.get("vernacularName", query.title()),
                                "scientific_name": item.get("scientificName"),
                                "confidence": 0.9,
                                "source": "gbif_api",
                                "type": "api_result",
                                "kingdom": item.get("kingdom"),
                                "phylum": item.get("phylum"),
                                "class": item.get("class"),
                                "order": item.get("order"),
                                "family": item.get("family"),
                                "genus": item.get("genus")
                            })
                
                return results[:5]  # Limit to top 5 results
                
        except Exception as e:
            logger.warning(f"GBIF API search failed: {e}")
        
        return []
    
    def search_comprehensive(self, query: str) -> List[Dict]:
        """Comprehensive search combining all sources"""
        all_results = []
        
        # Search local database first (fastest and most curated)
        local_results = self.search_local_database(query)
        all_results.extend(local_results)
        
        # If we don't have good local results, try external APIs
        if not local_results or (local_results and local_results[0]["confidence"] < 0.9):
            try:
                gbif_results = self.search_gbif_api(query)
                all_results.extend(gbif_results)
            except Exception as e:
                logger.warning(f"External API search failed: {e}")
        
        # Remove duplicates and sort by confidence
        seen_scientific = set()
        unique_results = []
        
        for result in all_results:
            scientific = result["scientific_name"]
            if scientific not in seen_scientific:
                seen_scientific.add(scientific)
                unique_results.append(result)
        
        # Sort by confidence (highest first)
        unique_results.sort(key=lambda x: x["confidence"], reverse=True)
        
        return unique_results[:10]  # Return top 10 results
    
    def suggest_similar_names(self, query: str) -> List[str]:
        """Suggest similar animal names for typos or partial matches"""
        query_lower = query.lower()
        suggestions = []
        
        for common_name in self.common_to_scientific.keys():
            # Simple similarity check
            if (query_lower in common_name or 
                common_name in query_lower or
                abs(len(query_lower) - len(common_name)) <= 2):
                suggestions.append(common_name.title())
        
        return suggestions[:8]  # Limit suggestions
    
    def get_animal_info(self, scientific_name: str) -> Dict:
        """Get additional information about an animal by scientific name"""
        info = {
            "scientific_name": scientific_name,
            "common_names": [],
            "classification": {},
            "conservation_status": "Unknown",
            "description": ""
        }
        
        # Try to get info from GBIF
        try:
            # Search for the exact scientific name
            url = f"{self.gbif_base}/species/search"
            params = {"q": scientific_name, "limit": 1}
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if results:
                    species = results[0]
                    info["classification"] = {
                        "kingdom": species.get("kingdom"),
                        "phylum": species.get("phylum"),
                        "class": species.get("class"),
                        "order": species.get("order"),
                        "family": species.get("family"),
                        "genus": species.get("genus")
                    }
                    
                    # Get vernacular names
                    if species.get("nubKey"):
                        vernacular_url = f"{self.gbif_base}/species/{species['nubKey']}/vernacularNames"
                        vernacular_response = requests.get(vernacular_url, timeout=5)
                        if vernacular_response.status_code == 200:
                            vernacular_data = vernacular_response.json()
                            for name in vernacular_data.get("results", [])[:5]:
                                if name.get("vernacularName"):
                                    info["common_names"].append(name["vernacularName"])
        
        except Exception as e:
            logger.warning(f"Failed to get animal info: {e}")
        
        return info

# Global instance
animal_search = AnimalSearchEngine()