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
        
        # Expanded common name to scientific name mapping (English and Spanish)
        self.common_to_scientific = {
            # Mammals - English and Spanish
            "tiger": "Panthera tigris",
            "tigre": "Panthera tigris",
            "siberian tiger": "Panthera tigris altaica",
            "tigre siberiano": "Panthera tigris altaica",
            "lion": "Panthera leo",
            "león": "Panthera leo",
            "leon": "Panthera leo",
            "leopard": "Panthera pardus",
            "leopardo": "Panthera pardus",
            "jaguar": "Panthera onca",
            "yaguar": "Panthera onca",
            "cheetah": "Acinonyx jubatus",
            "guepardo": "Acinonyx jubatus",
            "puma": "Puma concolor",
            "león de montaña": "Puma concolor",
            "leon de montana": "Puma concolor",
            "mountain lion": "Puma concolor",
            "cougar": "Puma concolor",
            "elephant": "Loxodonta africana",
            "elefante": "Loxodonta africana",
            "african elephant": "Loxodonta africana",
            "elefante africano": "Loxodonta africana",
            "asian elephant": "Elephas maximus",
            "elefante asiático": "Elephas maximus",
            "elefante asiatico": "Elephas maximus",
            "blue whale": "Balaenoptera musculus",
            "ballena azul": "Balaenoptera musculus",
            "humpback whale": "Megaptera novaeangliae",
            "ballena jorobada": "Megaptera novaeangliae",
            "sperm whale": "Physeter macrocephalus",
            "cachalote": "Physeter macrocephalus",
            "dolphin": "Tursiops truncatus",
            "delfín": "Tursiops truncatus",
            "delfin": "Tursiops truncatus",
            "bottlenose dolphin": "Tursiops truncatus",
            "delfín nariz de botella": "Tursiops truncatus",
            "wolf": "Canis lupus",
            "lobo": "Canis lupus",
            "dog": "Canis lupus familiaris",
            "perro": "Canis lupus familiaris",
            "cat": "Felis catus",
            "gato": "Felis catus",
            "horse": "Equus caballus",
            "caballo": "Equus caballus",
            "cow": "Bos taurus",
            "vaca": "Bos taurus",
            "pig": "Sus scrofa",
            "cerdo": "Sus scrofa",
            "sheep": "Ovis aries",
            "oveja": "Ovis aries",
            "goat": "Capra hircus",
            "cabra": "Capra hircus",
            "bear": "Ursus americanus",
            "oso": "Ursus americanus",
            "polar bear": "Ursus maritimus",
            "oso polar": "Ursus maritimus",
            "brown bear": "Ursus arctos",
            "oso pardo": "Ursus arctos",
            "oso marrón": "Ursus arctos",
            "oso marron": "Ursus arctos",
            "panda": "Ailuropoda melanoleuca",
            "oso panda": "Ailuropoda melanoleuca",
            "giant panda": "Ailuropoda melanoleuca",
            "oso panda gigante": "Ailuropoda melanoleuca",
            "orangutan": "Pongo pygmaeus",
            "orangután": "Pongo pygmaeus",
            "sumatran orangutan": "Pongo abelii",
            "chimpanzee": "Pan troglodytes",
            "chimpancé": "Pan troglodytes",
            "chimpance": "Pan troglodytes",
            "gorilla": "Gorilla gorilla",
            "gorila": "Gorilla gorilla",
            "human": "Homo sapiens",
            "humano": "Homo sapiens",
            "rhinoceros": "Rhinoceros unicornis",
            "rinoceronte": "Rhinoceros unicornis",
            "indian rhinoceros": "Rhinoceros unicornis",
            "rinoceronte indio": "Rhinoceros unicornis",
            "white rhinoceros": "Ceratotherium simum",
            "rinoceronte blanco": "Ceratotherium simum",
            "hippopotamus": "Hippopotamus amphibius",
            "hipopótamo": "Hippopotamus amphibius",
            "hipopotamo": "Hippopotamus amphibius",
            "giraffe": "Giraffa camelopardalis",
            "jirafa": "Giraffa camelopardalis",
            "zebra": "Equus zebra",
            "cebra": "Equus zebra",
            "kangaroo": "Macropus rufus",
            "canguro": "Macropus rufus",
            "koala": "Phascolarctos cinereus",
            
            # Birds - English and Spanish
            "eagle": "Aquila chrysaetos",
            "águila": "Aquila chrysaetos",
            "aguila": "Aquila chrysaetos",
            "bald eagle": "Haliaeetus leucocephalus",
            "águila calva": "Haliaeetus leucocephalus",
            "owl": "Bubo bubo",
            "búho": "Bubo bubo",
            "buho": "Bubo bubo",
            "lechuza": "Bubo bubo",
            "penguin": "Aptenodytes forsteri",
            "pingüino": "Aptenodytes forsteri",
            "pinguino": "Aptenodytes forsteri",
            "emperor penguin": "Aptenodytes forsteri",
            "pingüino emperador": "Aptenodytes forsteri",
            "chicken": "Gallus gallus",
            "pollo": "Gallus gallus",
            "gallina": "Gallus gallus",
            "duck": "Anas platyrhynchos",
            "pato": "Anas platyrhynchos",
            "swan": "Cygnus olor",
            "cisne": "Cygnus olor",
            "flamingo": "Phoenicopterus roseus",
            "flamenco": "Phoenicopterus roseus",
            "parrot": "Psittacus erithacus",
            "loro": "Psittacus erithacus",
            "papagayo": "Psittacus erithacus",
            "peacock": "Pavo cristatus",
            "pavo real": "Pavo cristatus",
            "ostrich": "Struthio camelus",
            "avestruz": "Struthio camelus",
            "condor": "Vultur gryphus",
            "cóndor": "Vultur gryphus",
            "albatross": "Diomedea exulans",
            "albatros": "Diomedea exulans",
            
            # Reptiles and Amphibians - English and Spanish
            "crocodile": "Crocodylus niloticus",
            "cocodrilo": "Crocodylus niloticus",
            "nile crocodile": "Crocodylus niloticus",
            "cocodrilo del nilo": "Crocodylus niloticus",
            "alligator": "Alligator mississippiensis",
            "caimán": "Alligator mississippiensis",
            "caiman": "Alligator mississippiensis",
            "snake": "Python regius",
            "serpiente": "Python regius",
            "culebra": "Python regius",
            "víbora": "Python regius",
            "vibora": "Python regius",
            "python": "Python reticulatus",
            "pitón": "Python reticulatus",
            "piton": "Python reticulatus",
            "cobra": "Naja naja",
            "turtle": "Chelonia mydas",
            "tortuga": "Chelonia mydas",
            "sea turtle": "Chelonia mydas",
            "tortuga marina": "Chelonia mydas",
            "tortoise": "Testudo graeca",
            "tortuga terrestre": "Testudo graeca",
            "iguana": "Iguana iguana",
            "gecko": "Gekko gecko",
            "geco": "Gekko gecko",
            "lizard": "Lacerta agilis",
            "lagarto": "Lacerta agilis",
            "lagartija": "Lacerta agilis",
            "frog": "Rana temporaria",
            "rana": "Rana temporaria",
            "toad": "Bufo bufo",
            "sapo": "Bufo bufo",
            "salamander": "Salamandra salamandra",
            "salamandra": "Salamandra salamandra",
            "tuatara": "Sphenodon punctatus",
            
            # Fish and Marine Life - English and Spanish
            "shark": "Carcharodon carcharias",
            "tiburón": "Carcharodon carcharias",
            "tiburon": "Carcharodon carcharias",
            "great white shark": "Carcharodon carcharias",
            "tiburón blanco": "Carcharodon carcharias",
            "whale shark": "Rhincodon typus",
            "tiburón ballena": "Rhincodon typus",
            "hammerhead shark": "Sphyrna mokarran",
            "tiburón martillo": "Sphyrna mokarran",
            "tuna": "Thunnus thynnus",
            "atún": "Thunnus thynnus",
            "atun": "Thunnus thynnus",
            "salmon": "Salmo salar",
            "salmón": "Salmo salar",
            "cod": "Gadus morhua",
            "bacalao": "Gadus morhua",
            "bass": "Micropterus salmoides",
            "lubina": "Micropterus salmoides",
            "trout": "Oncorhynchus mykiss",
            "trucha": "Oncorhynchus mykiss",
            "octopus": "Octopus vulgaris",
            "pulpo": "Octopus vulgaris",
            "squid": "Loligo vulgaris",
            "calamar": "Loligo vulgaris",
            "jellyfish": "Aurelia aurita",
            "medusa": "Aurelia aurita",
            "agua mala": "Aurelia aurita",
            "immortal jellyfish": "Turritopsis dohrnii",
            "medusa inmortal": "Turritopsis dohrnii",
            "seahorse": "Hippocampus hippocampus",
            "caballito de mar": "Hippocampus hippocampus",
            "starfish": "Asterias rubens",
            "estrella de mar": "Asterias rubens",
            "crab": "Cancer pagurus",
            "cangrejo": "Cancer pagurus",
            "lobster": "Homarus gammarus",
            "langosta": "Homarus gammarus",
            "shrimp": "Penaeus monodon",
            "camarón": "Penaeus monodon",
            "camaron": "Penaeus monodon",
            "gamba": "Penaeus monodon",
            "coral": "Acropora palmata",
            "sea urchin": "Echinometra lucunter",
            "erizo de mar": "Echinometra lucunter",
            "coelacanth": "Latimeria chalumnae",
            "celacanto": "Latimeria chalumnae",
            
            # Invertebrates - English and Spanish
            "butterfly": "Danaus plexippus",
            "mariposa": "Danaus plexippus",
            "monarch butterfly": "Danaus plexippus",
            "mariposa monarca": "Danaus plexippus",
            "bee": "Apis mellifera",
            "abeja": "Apis mellifera",
            "honeybee": "Apis mellifera",
            "abeja de miel": "Apis mellifera",
            "ant": "Formica rufa",
            "hormiga": "Formica rufa",
            "spider": "Latrodectus hesperus",
            "araña": "Latrodectus hesperus",
            "arana": "Latrodectus hesperus",
            "black widow": "Latrodectus hesperus",
            "viuda negra": "Latrodectus hesperus",
            "tarantula": "Theraphosa blondi",
            "tarántula": "Theraphosa blondi",
            "tarantula goliath": "Theraphosa blondi",
            "tarántula goliat": "Theraphosa blondi",
            "dragonfly": "Libellula quadrimaculata",
            "libélula": "Libellula quadrimaculata",
            "libelula": "Libellula quadrimaculata",
            "fly": "Drosophila melanogaster",
            "mosca": "Drosophila melanogaster",
            "fruit fly": "Drosophila melanogaster",
            "mosca de la fruta": "Drosophila melanogaster",
            "mosquito": "Aedes aegypti",
            "zancudo": "Aedes aegypti",
            "beetle": "Tribolium castaneum",
            "escarabajo": "Tribolium castaneum",
            "flour beetle": "Tribolium castaneum",
            "escarabajo de harina": "Tribolium castaneum",
            "ladybug": "Harmonia axyridis",
            "mariquita": "Harmonia axyridis",
            "catarina": "Harmonia axyridis",
            "grasshopper": "Locusta migratoria",
            "saltamontes": "Locusta migratoria",
            "chapulín": "Locusta migratoria",
            "chapulin": "Locusta migratoria",
            "cricket": "Acheta domesticus",
            "grillo": "Acheta domesticus",
            "cockroach": "Blattella germanica",
            "cucaracha": "Blattella germanica",
            "german cockroach": "Blattella germanica",
            "cucaracha alemana": "Blattella germanica",
            "water bear": "Hypsibius dujardini",
            "oso de agua": "Hypsibius dujardini",
            "tardigrade": "Hypsibius dujardini",
            "tardígrado": "Hypsibius dujardini",
            "tardigrado": "Hypsibius dujardini",
            
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
        results = []
        try:
            # First try: Direct species search
            url = f"{self.gbif_base}/species/search"
            params = {
                "q": query,
                "rank": "SPECIES",
                "status": "ACCEPTED",
                "limit": 15
            }
            
            response = requests.get(url, params=params, timeout=8)
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get("results", []):
                    scientific_name = item.get("scientificName", "")
                    kingdom = item.get("kingdom", "").lower()
                    
                    # Filter for animals and valid scientific names
                    if scientific_name and kingdom in ["animalia", "animal"]:
                        # Calculate confidence based on name match
                        query_lower = query.lower()
                        sci_lower = scientific_name.lower()
                        
                        confidence = 0.9
                        if query_lower in sci_lower or sci_lower.startswith(query_lower):
                            confidence = 0.95
                        
                        results.append({
                            "common_name": item.get("vernacularName", query.title()),
                            "scientific_name": scientific_name,
                            "confidence": confidence,
                            "source": "gbif_api",
                            "type": "api_result",
                            "kingdom": item.get("kingdom"),
                            "phylum": item.get("phylum"),
                            "class": item.get("class"),
                            "order": item.get("order"),
                            "family": item.get("family"),
                            "genus": item.get("genus")
                        })
                
                # If we have results, return them
                if results:
                    return results[:5]
            
            # Second try: Search by vernacular names if no direct species match
            url = f"{self.gbif_base}/species/suggest"
            params = {"q": query, "limit": 10}
            
            response = requests.get(url, params=params, timeout=8)
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    scientific_name = item.get("scientificName", "")
                    kingdom = item.get("kingdom", "").lower()
                    
                    if scientific_name and kingdom in ["animalia", "animal"]:
                        results.append({
                            "common_name": query.title(),
                            "scientific_name": scientific_name,
                            "confidence": 0.85,
                            "source": "gbif_suggest",
                            "type": "suggestion",
                            "kingdom": item.get("kingdom"),
                            "rank": item.get("rank")
                        })
            
            return results[:5]
                
        except requests.RequestException as e:
            logger.warning(f"GBIF API network error: {e}")
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