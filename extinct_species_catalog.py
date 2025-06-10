"""
Catálogo Especial de Especies Extintas y en Peligro Crítico
Para la colección personal de NFTs del creador
"""

EXTINCT_SPECIES = {
    # Extintas recientemente (posibles secuencias disponibles)
    "Thylacinus cynocephalus": {
        "common_name": "Tigre de Tasmania",
        "extinction_year": 1936,
        "last_location": "Australia",
        "story": "El último depredador marsupial de gran tamaño, cazado hasta la extinción por considerarse amenaza para el ganado.",
        "nft_rarity": "Legendary",
        "estimated_value": "$2,000-$5,000",
        "collection_tier": "Apex Predators Lost"
    },
    "Equus quagga quagga": {
        "common_name": "Cuaga",
        "extinction_year": 1883,
        "last_location": "Sudáfrica",
        "story": "Una subespecie única de cebra con rayas solo en la parte frontal del cuerpo.",
        "nft_rarity": "Legendary",
        "estimated_value": "$1,500-$3,500",
        "collection_tier": "Vanished Stripes"
    },
    "Raphus cucullatus": {
        "common_name": "Dodo",
        "extinction_year": 1681,
        "last_location": "Mauricio",
        "story": "Ave no voladora que se convirtió en símbolo de la extinción causada por humanos.",
        "nft_rarity": "Mythical",
        "estimated_value": "$3,000-$8,000",
        "collection_tier": "Lost Flight"
    },
    "Mammuthus primigenius": {
        "common_name": "Mamut Lanudo",
        "extinction_year": -4000,
        "last_location": "Isla Wrangel",
        "story": "Gigante de la era glacial, sus restos permiten estudios genéticos avanzados.",
        "nft_rarity": "Ancient",
        "estimated_value": "$5,000-$15,000",
        "collection_tier": "Ice Age Giants"
    }
}

CRITICALLY_ENDANGERED = {
    "Panthera pardus orientalis": {
        "common_name": "Leopardo de Amur",
        "population": "~120 individuos",
        "location": "Rusia/China",
        "story": "El gran felino más raro del mundo, adaptado a los fríos extremos de Siberia.",
        "nft_rarity": "Ultra Rare",
        "estimated_value": "$800-$2,000",
        "collection_tier": "Last Stand"
    },
    "Rhinoceros sondaicus": {
        "common_name": "Rinoceronte de Java",
        "population": "~70 individuos",
        "location": "Java, Indonesia",
        "story": "Una de las especies de grandes mamíferos más amenazadas del planeta.",
        "nft_rarity": "Ultra Rare",
        "estimated_value": "$1,000-$2,500",
        "collection_tier": "Last Stand"
    },
    "Balaenoptera musculus": {
        "common_name": "Ballena Azul",
        "population": "~25,000 individuos",
        "location": "Océanos mundiales",
        "story": "El animal más grande que ha existido, lentamente recuperándose de la caza comercial.",
        "nft_rarity": "Rare",
        "estimated_value": "$600-$1,500",
        "collection_tier": "Ocean Giants"
    },
    "Ailuropoda melanoleuca": {
        "common_name": "Panda Gigante",
        "population": "~1,864 individuos",
        "location": "China",
        "story": "Símbolo de conservación mundial, ha mejorado de 'En Peligro' a 'Vulnerable'.",
        "nft_rarity": "Rare",
        "estimated_value": "$500-$1,200",
        "collection_tier": "Conservation Success"
    }
}

def get_collection_tiers():
    """Obtiene las categorías de colección organizadas"""
    tiers = {}
    
    # Procesar especies extintas
    for species, data in EXTINCT_SPECIES.items():
        tier = data['collection_tier']
        if tier not in tiers:
            tiers[tier] = {'extinct': [], 'endangered': []}
        tiers[tier]['extinct'].append({
            'scientific_name': species,
            'common_name': data['common_name'],
            'story': data['story'],
            'rarity': data['nft_rarity'],
            'estimated_value': data['estimated_value'],
            'extinction_year': data['extinction_year']
        })
    
    # Procesar especies en peligro crítico
    for species, data in CRITICALLY_ENDANGERED.items():
        tier = data['collection_tier']
        if tier not in tiers:
            tiers[tier] = {'extinct': [], 'endangered': []}
        tiers[tier]['endangered'].append({
            'scientific_name': species,
            'common_name': data['common_name'],
            'story': data['story'],
            'rarity': data['nft_rarity'],
            'estimated_value': data['estimated_value'],
            'population': data['population']
        })
    
    return tiers

def get_species_nft_data(scientific_name):
    """Obtiene datos específicos para NFT de una especie"""
    if scientific_name in EXTINCT_SPECIES:
        data = EXTINCT_SPECIES[scientific_name]
        return {
            'type': 'extinct',
            'rarity': data['nft_rarity'],
            'estimated_value': data['estimated_value'],
            'collection_tier': data['collection_tier'],
            'story': data['story'],
            'special_attributes': {
                'extinction_year': data['extinction_year'],
                'last_location': data['last_location']
            }
        }
    elif scientific_name in CRITICALLY_ENDANGERED:
        data = CRITICALLY_ENDANGERED[scientific_name]
        return {
            'type': 'critically_endangered',
            'rarity': data['nft_rarity'],
            'estimated_value': data['estimated_value'],
            'collection_tier': data['collection_tier'],
            'story': data['story'],
            'special_attributes': {
                'population': data['population'],
                'location': data['location']
            }
        }
    return None

def is_premium_collection_species(scientific_name):
    """Verifica si una especie pertenece a la colección premium"""
    return scientific_name in EXTINCT_SPECIES or scientific_name in CRITICALLY_ENDANGERED