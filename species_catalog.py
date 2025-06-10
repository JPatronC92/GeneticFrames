"""
Species Catalog for Digital Genetic Zoo
Curated collection of species with conservation status and genetic information
"""

# Catalog of featured species organized by conservation status and appeal
FEATURED_SPECIES = {
    "critically_endangered": {
        "name": "Especies en Peligro Crítico",
        "rarity_multiplier": 5.0,
        "species": [
            {
                "scientific_name": "Panthera tigris altaica",
                "common_name": "Tigre Siberiano",
                "population": "~400 individuos",
                "habitat": "Bosques de Siberia y China",
                "conservation_status": "En Peligro Crítico",
                "genetic_interest": "Mayor de todos los felinos, adaptaciones al frío extremo",
                "ncbi_search_terms": ["Panthera tigris", "Siberian tiger mitochondrial"],
                "art_description": "Patrón genético del depredador más grande del mundo"
            },
            {
                "scientific_name": "Rhinoceros unicornis",
                "common_name": "Rinoceronte Indio",
                "population": "~3,500 individuos",
                "habitat": "Praderas de India y Nepal",
                "conservation_status": "Vulnerable",
                "genetic_interest": "Piel blindada única, evolución separada",
                "ncbi_search_terms": ["Rhinoceros unicornis", "Indian rhinoceros"],
                "art_description": "ADN de armadura viviente de la prehistoria"
            },
            {
                "scientific_name": "Pongo abelii",
                "common_name": "Orangután de Sumatra",
                "population": "~14,000 individuos",
                "habitat": "Selvas de Sumatra",
                "conservation_status": "En Peligro Crítico",
                "genetic_interest": "97% ADN compartido con humanos, inteligencia superior",
                "ncbi_search_terms": ["Pongo abelii", "Sumatran orangutan"],
                "art_description": "Espejo genético de nuestra evolución"
            }
        ]
    },
    "megafauna": {
        "name": "Megafauna Icónica",
        "rarity_multiplier": 3.0,
        "species": [
            {
                "scientific_name": "Loxodonta africana",
                "common_name": "Elefante Africano",
                "population": "~415,000 individuos",
                "habitat": "Sabanas africanas",
                "conservation_status": "En Peligro",
                "genetic_interest": "Genoma gigante, memoria excepcional, comunicación infrasonora",
                "ncbi_search_terms": ["Loxodonta africana", "African elephant"],
                "art_description": "ADN de la memoria viviente de África"
            },
            {
                "scientific_name": "Balaenoptera musculus",
                "common_name": "Ballena Azul",
                "population": "~10,000 individuos",
                "habitat": "Océanos del mundo",
                "conservation_status": "En Peligro",
                "genetic_interest": "Animal más grande que ha existido, corazón del tamaño de un auto",
                "ncbi_search_terms": ["Balaenoptera musculus", "blue whale"],
                "art_description": "Código genético del gigante más grande de la Tierra"
            },
            {
                "scientific_name": "Carcharodon carcharias",
                "common_name": "Gran Tiburón Blanco",
                "population": "~3,500 individuos",
                "habitat": "Océanos templados",
                "conservation_status": "Vulnerable",
                "genetic_interest": "Depredador apex, sistema inmune perfecto, regeneración",
                "ncbi_search_terms": ["Carcharodon carcharias", "great white shark"],
                "art_description": "Perfección evolutiva de 400 millones de años"
            }
        ]
    },
    "unique_genetics": {
        "name": "Genética Extraordinaria",
        "rarity_multiplier": 4.0,
        "species": [
            {
                "scientific_name": "Turritopsis dohrnii",
                "common_name": "Medusa Inmortal",
                "population": "Desconocida",
                "habitat": "Océanos tropicales",
                "conservation_status": "Datos Insuficientes",
                "genetic_interest": "Único animal biológicamente inmortal, reversión celular",
                "ncbi_search_terms": ["Turritopsis dohrnii", "immortal jellyfish"],
                "art_description": "El secreto genético de la inmortalidad"
            },
            {
                "scientific_name": "Tardigrada",
                "common_name": "Oso de Agua",
                "population": "Abundante",
                "habitat": "Ubicuo (desde el espacio hasta océanos profundos)",
                "conservation_status": "Preocupación Menor",
                "genetic_interest": "Superviviente extremo, resistencia espacial, criptobiosis",
                "ncbi_search_terms": ["Tardigrada", "water bear tardigrade"],
                "art_description": "ADN indestructible del superviviente cósmico"
            },
            {
                "scientific_name": "Octopus vulgaris",
                "common_name": "Pulpo Común",
                "population": "Estable",
                "habitat": "Océanos templados",
                "conservation_status": "Preocupación Menor",
                "genetic_interest": "Inteligencia alienígena, 3 corazones, sangre azul, camuflaje perfecto",
                "ncbi_search_terms": ["Octopus vulgaris", "common octopus"],
                "art_description": "Inteligencia extraterrestre en el océano terrestre"
            }
        ]
    },
    "ancient_lineages": {
        "name": "Linajes Ancestrales",
        "rarity_multiplier": 3.5,
        "species": [
            {
                "scientific_name": "Latimeria chalumnae",
                "common_name": "Celacanto",
                "population": "~500 individuos",
                "habitat": "Aguas profundas del Océano Índico",
                "conservation_status": "En Peligro Crítico",
                "genetic_interest": "Fósil viviente, eslabón perdido pez-anfibio",
                "ncbi_search_terms": ["Latimeria chalumnae", "coelacanth"],
                "art_description": "Tiempo congelado en ADN de 400 millones de años"
            },
            {
                "scientific_name": "Crocodylus niloticus",
                "common_name": "Cocodrilo del Nilo",
                "population": "~250,000 individuos",
                "habitat": "Ríos africanos",
                "conservation_status": "Preocupación Menor",
                "genetic_interest": "Dinosaurio viviente, sistema inmune perfecto, regeneración",
                "ncbi_search_terms": ["Crocodylus niloticus", "Nile crocodile"],
                "art_description": "Eco genético de la era de los dinosaurios"
            },
            {
                "scientific_name": "Sphenodon punctatus",
                "common_name": "Tuátara",
                "population": "~100,000 individuos",
                "habitat": "Islas de Nueva Zelanda",
                "conservation_status": "Vulnerable",
                "genetic_interest": "Único sobreviviente del orden Rhynchocephalia, tercer ojo",
                "ncbi_search_terms": ["Sphenodon punctatus", "tuatara"],
                "art_description": "Reliquia genética de Gondwana"
            }
        ]
    }
}

# Popular species for quick access
POPULAR_SPECIES = [
    "Homo sapiens",
    "Canis lupus",
    "Felis catus", 
    "Panthera leo",
    "Ursus maritimus",
    "Equus caballus",
    "Sus scrofa",
    "Bos taurus",
    "Drosophila melanogaster",
    "Escherichia coli"
]

def get_species_info(scientific_name):
    """Get detailed species information from catalog"""
    for category_data in FEATURED_SPECIES.values():
        for species in category_data["species"]:
            if species["scientific_name"].lower() == scientific_name.lower():
                return species
    return None

def get_rarity_multiplier(scientific_name):
    """Get rarity multiplier for species"""
    for category_name, category_data in FEATURED_SPECIES.items():
        for species in category_data["species"]:
            if species["scientific_name"].lower() == scientific_name.lower():
                return category_data["rarity_multiplier"]
    return 1.0  # Default multiplier

def get_conservation_status(scientific_name):
    """Get conservation status of species"""
    species_info = get_species_info(scientific_name)
    if species_info:
        return species_info["conservation_status"]
    return "Estado Desconocido"

def get_species_story(scientific_name):
    """Get the compelling story/description for the species"""
    species_info = get_species_info(scientific_name)
    if species_info:
        return {
            "title": f"Arte Genético: {species_info['common_name']}",
            "story": f"{species_info['art_description']}. {species_info['genetic_interest']}",
            "conservation": species_info['conservation_status'],
            "population": species_info['population'],
            "habitat": species_info['habitat']
        }
    return None

def suggest_search_terms(partial_name):
    """Suggest search terms based on partial species name"""
    suggestions = []
    partial_lower = partial_name.lower()
    
    # Search in featured species
    for category_data in FEATURED_SPECIES.values():
        for species in category_data["species"]:
            scientific = species["scientific_name"].lower()
            common = species["common_name"].lower()
            
            if partial_lower in scientific or partial_lower in common:
                suggestions.append({
                    "scientific_name": species["scientific_name"],
                    "common_name": species["common_name"],
                    "category": "featured"
                })
    
    # Search in popular species
    for species in POPULAR_SPECIES:
        if partial_lower in species.lower():
            suggestions.append({
                "scientific_name": species,
                "common_name": species,
                "category": "popular"
            })
    
    return suggestions[:10]  # Limit to 10 suggestions

def get_featured_categories():
    """Get all featured categories with their species"""
    return FEATURED_SPECIES

def is_featured_species(scientific_name):
    """Check if species is in featured catalog"""
    return get_species_info(scientific_name) is not None