"""
Sistema de Perfiles de Identidad de Especies
Combina características genéticas con identidad simbólica para arte único
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

@dataclass
class SpeciesIdentityProfile:
    """Perfil completo de identidad visual de una especie"""
    
    # Identidad básica
    common_name: str
    scientific_name: str
    taxonomic_class: str
    
    # Perfil visual simbólico
    base_form: str  # "circular", "angular", "fluid", "crystalline"
    primary_colors: List[str]
    secondary_colors: List[str]
    symmetry_level: float  # 0-1
    chaos_factor: float  # 0-1, cuánto "ruido" visual
    texture_style: str  # "smooth", "rough", "crystalline", "organic"
    energy_level: str  # "low", "medium", "high", "explosive"
    emotional_tone: str  # "aggressive", "gentle", "mysterious", "playful"
    
    # Características de movimiento
    movement_pattern: str  # "linear", "spiral", "chaotic", "wave", "pulse"
    flow_intensity: float  # 0-1
    rhythm_complexity: float  # 0-1
    
    # Atributos específicos
    size_representation: str  # "massive", "medium", "tiny", "variable"
    habitat_influence: str  # "aquatic", "terrestrial", "aerial", "mixed"
    predator_type: str  # "apex", "hunter", "prey", "omnivore", "herbivore"
    
    # Firmas genéticas (serán calculadas del ADN real)
    genetic_signatures: Dict[str, float]
    
    # Factores de amplificación visual
    drama_factor: float  # 0-1, qué tan dramática debe ser la visualización
    uniqueness_multiplier: float  # 0-3, qué tan único debe verse vs otras especies

def create_species_profiles():
    """Base de datos de perfiles de identidad por especie"""
    
    profiles = {
        # FELINOS - Elegancia y poder
        "panthera leo": SpeciesIdentityProfile(
            common_name="León",
            scientific_name="Panthera leo",
            taxonomic_class="Mammalia",
            base_form="angular",
            primary_colors=["#FFD700", "#FF8C00", "#CD853F"],  # Dorado, naranja, bronceado
            secondary_colors=["#8B4513", "#000000", "#FFFF00"],  # Marrón, negro, amarillo
            symmetry_level=0.8,
            chaos_factor=0.3,
            texture_style="rough",
            energy_level="high",
            emotional_tone="aggressive",
            movement_pattern="linear",
            flow_intensity=0.9,
            rhythm_complexity=0.7,
            size_representation="massive",
            habitat_influence="terrestrial",
            predator_type="apex",
            genetic_signatures={},
            drama_factor=0.9,
            uniqueness_multiplier=2.5
        ),
        
        "panthera tigris": SpeciesIdentityProfile(
            common_name="Tigre",
            scientific_name="Panthera tigris",
            taxonomic_class="Mammalia",
            base_form="angular",
            primary_colors=["#FF4500", "#000000", "#FFD700"],  # Naranja, negro, dorado
            secondary_colors=["#FFFFFF", "#8B0000", "#FF6347"],  # Blanco, rojo oscuro, tomate
            symmetry_level=0.9,
            chaos_factor=0.4,
            texture_style="crystalline",
            energy_level="explosive",
            emotional_tone="aggressive",
            movement_pattern="spiral",
            flow_intensity=1.0,
            rhythm_complexity=0.8,
            size_representation="massive",
            habitat_influence="terrestrial",
            predator_type="apex",
            genetic_signatures={},
            drama_factor=1.0,
            uniqueness_multiplier=3.0
        ),
        
        # MAMÍFEROS MARINOS - Fluidez y inteligencia
        "tursiops truncatus": SpeciesIdentityProfile(
            common_name="Delfín",
            scientific_name="Tursiops truncatus",
            taxonomic_class="Mammalia",
            base_form="fluid",
            primary_colors=["#00BFFF", "#4169E1", "#87CEEB"],  # Azul cielo, azul real, azul cielo claro
            secondary_colors=["#FFFFFF", "#00CED1", "#1E90FF"],  # Blanco, turquesa, azul dodger
            symmetry_level=0.9,
            chaos_factor=0.1,
            texture_style="smooth",
            energy_level="high",
            emotional_tone="playful",
            movement_pattern="wave",
            flow_intensity=0.9,
            rhythm_complexity=0.9,
            size_representation="medium",
            habitat_influence="aquatic",
            predator_type="hunter",
            genetic_signatures={},
            drama_factor=0.7,
            uniqueness_multiplier=2.2
        ),
        
        "balaenoptera musculus": SpeciesIdentityProfile(
            common_name="Ballena azul",
            scientific_name="Balaenoptera musculus",
            taxonomic_class="Mammalia",
            base_form="fluid",
            primary_colors=["#191970", "#4682B4", "#6495ED"],  # Azul medianoche, azul acero, azul cornflower
            secondary_colors=["#000080", "#483D8B", "#FFFFFF"],  # Azul marino, azul slate, blanco
            symmetry_level=0.95,
            chaos_factor=0.05,
            texture_style="smooth",
            energy_level="low",
            emotional_tone="mysterious",
            movement_pattern="wave",
            flow_intensity=0.6,
            rhythm_complexity=0.3,
            size_representation="massive",
            habitat_influence="aquatic",
            predator_type="omnivore",
            genetic_signatures={},
            drama_factor=0.8,
            uniqueness_multiplier=2.8
        ),
        
        # PRIMATES - Complejidad y expresividad
        "ailuropoda melanoleuca": SpeciesIdentityProfile(
            common_name="Panda gigante",
            scientific_name="Ailuropoda melanoleuca",
            taxonomic_class="Mammalia",
            base_form="circular",
            primary_colors=["#FFFFFF", "#000000", "#90EE90"],  # Blanco, negro, verde claro
            secondary_colors=["#228B22", "#2F4F4F", "#F5F5F5"],  # Verde bosque, gris slate, blanco humo
            symmetry_level=0.95,
            chaos_factor=0.15,
            texture_style="organic",
            energy_level="low",
            emotional_tone="gentle",
            movement_pattern="pulse",
            flow_intensity=0.3,
            rhythm_complexity=0.4,
            size_representation="massive",
            habitat_influence="terrestrial",
            predator_type="herbivore",
            genetic_signatures={},
            drama_factor=0.6,
            uniqueness_multiplier=2.0
        ),
        
        "homo sapiens": SpeciesIdentityProfile(
            common_name="Humano",
            scientific_name="Homo sapiens",
            taxonomic_class="Mammalia",
            base_form="crystalline",
            primary_colors=["#DAA520", "#CD853F", "#F4A460"],  # Dorado, bronceado, arenoso
            secondary_colors=["#FF0000", "#0000FF", "#00FF00"],  # RGB primarios
            symmetry_level=0.7,
            chaos_factor=0.6,
            texture_style="crystalline",
            energy_level="medium",
            emotional_tone="mysterious",
            movement_pattern="chaotic",
            flow_intensity=0.8,
            rhythm_complexity=1.0,
            size_representation="medium",
            habitat_influence="mixed",
            predator_type="omnivore",
            genetic_signatures={},
            drama_factor=0.9,
            uniqueness_multiplier=2.7
        ),
        
        # AVES - Ligereza y libertad
        "aquila chrysaetos": SpeciesIdentityProfile(
            common_name="Águila real",
            scientific_name="Aquila chrysaetos",
            taxonomic_class="Aves",
            base_form="angular",
            primary_colors=["#8B4513", "#DAA520", "#FFFFFF"],  # Marrón silla, dorado, blanco
            secondary_colors=["#000000", "#FFD700", "#CD853F"],  # Negro, oro, bronceado
            symmetry_level=0.85,
            chaos_factor=0.25,
            texture_style="crystalline",
            energy_level="high",
            emotional_tone="aggressive",
            movement_pattern="spiral",
            flow_intensity=0.9,
            rhythm_complexity=0.6,
            size_representation="medium",
            habitat_influence="aerial",
            predator_type="apex",
            genetic_signatures={},
            drama_factor=0.95,
            uniqueness_multiplier=2.6
        ),
        
        # REPTILES - Antigüedad y misterio
        "crocodylus niloticus": SpeciesIdentityProfile(
            common_name="Cocodrilo del Nilo",
            scientific_name="Crocodylus niloticus",
            taxonomic_class="Reptilia",
            base_form="angular",
            primary_colors=["#556B2F", "#2F4F4F", "#8FBC8F"],  # Verde oliva, gris slate, verde mar
            secondary_colors=["#000000", "#654321", "#FFFF00"],  # Negro, marrón oscuro, amarillo
            symmetry_level=0.9,
            chaos_factor=0.4,
            texture_style="rough",
            energy_level="medium",
            emotional_tone="aggressive",
            movement_pattern="linear",
            flow_intensity=0.5,
            rhythm_complexity=0.3,
            size_representation="massive",
            habitat_influence="aquatic",
            predator_type="apex",
            genetic_signatures={},
            drama_factor=0.8,
            uniqueness_multiplier=2.3
        )
    }
    
    return profiles

def get_species_profile(scientific_name: str) -> Optional[SpeciesIdentityProfile]:
    """Obtiene el perfil de identidad de una especie"""
    profiles = create_species_profiles()
    
    # Buscar por nombre científico exacto
    scientific_clean = scientific_name.lower().strip()
    if scientific_clean in profiles:
        return profiles[scientific_clean]
    
    # Buscar por género (primera palabra)
    genus = scientific_clean.split()[0] if scientific_clean else ""
    for key, profile in profiles.items():
        if key.startswith(genus) and genus:
            return profile
    
    # Perfil genérico si no se encuentra
    return create_generic_profile(scientific_name)

def create_generic_profile(scientific_name: str) -> SpeciesIdentityProfile:
    """Crea un perfil genérico basado en características inferidas"""
    
    # Usar hash del nombre para generar características consistentes
    name_hash = hash(scientific_name) % 1000000
    
    base_forms = ["circular", "angular", "fluid", "crystalline"]
    textures = ["smooth", "rough", "crystalline", "organic"]
    energy_levels = ["low", "medium", "high"]
    emotions = ["gentle", "mysterious", "aggressive", "playful"]
    movements = ["linear", "spiral", "chaotic", "wave", "pulse"]
    
    return SpeciesIdentityProfile(
        common_name=scientific_name.split()[0].capitalize(),
        scientific_name=scientific_name,
        taxonomic_class="Unknown",
        base_form=base_forms[name_hash % len(base_forms)],
        primary_colors=["#FF6B6B", "#4ECDC4", "#45B7D1"],
        secondary_colors=["#FFA07A", "#98D8C8", "#87CEEB"],
        symmetry_level=(name_hash % 100) / 100.0,
        chaos_factor=(name_hash % 50) / 100.0,
        texture_style=textures[name_hash % len(textures)],
        energy_level=energy_levels[name_hash % len(energy_levels)],
        emotional_tone=emotions[name_hash % len(emotions)],
        movement_pattern=movements[name_hash % len(movements)],
        flow_intensity=(name_hash % 80 + 20) / 100.0,
        rhythm_complexity=(name_hash % 70 + 30) / 100.0,
        size_representation="medium",
        habitat_influence="terrestrial",
        predator_type="omnivore",
        genetic_signatures={},
        drama_factor=0.5,
        uniqueness_multiplier=1.5
    )

def enhance_profile_with_genetics(profile: SpeciesIdentityProfile, genetic_data: Dict) -> SpeciesIdentityProfile:
    """Mejora el perfil con datos genéticos reales"""
    
    # Calcular firmas genéticas específicas
    genetic_signatures = {}
    
    if 'gc_content' in genetic_data:
        genetic_signatures['gc_dominance'] = genetic_data['gc_content']
    
    if 'entropy' in genetic_data:
        genetic_signatures['complexity'] = genetic_data['entropy'] / 4.0  # Normalizar
    
    if 'genetic_signature' in genetic_data:
        genetic_signatures['uniqueness'] = (genetic_data['genetic_signature'] % 1000) / 1000.0
    
    if 'dinuc_profile' in genetic_data:
        dinucs = genetic_data['dinuc_profile']
        if dinucs:
            most_common = max(dinucs.values())
            genetic_signatures['repetition_strength'] = min(most_common / sum(dinucs.values()), 1.0)
    
    # Actualizar perfil con datos genéticos
    profile.genetic_signatures = genetic_signatures
    
    # Ajustar características visuales basadas en genética
    if genetic_signatures.get('complexity', 0) > 0.8:
        profile.chaos_factor = min(profile.chaos_factor + 0.2, 1.0)
        profile.rhythm_complexity = min(profile.rhythm_complexity + 0.1, 1.0)
    
    if genetic_signatures.get('gc_dominance', 0) > 0.6:
        profile.symmetry_level = min(profile.symmetry_level + 0.1, 1.0)
        if profile.texture_style == "smooth":
            profile.texture_style = "crystalline"
    
    return profile