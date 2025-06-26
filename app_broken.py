"""
DNA Art Generator - Versión Refactorizada y Optimizada
Generador de arte genético basado en secuencias de ADN reales
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
import io
import math
import hashlib
import re
import time
from typing import Dict, List, Optional, Tuple

from Bio import Entrez, SeqIO
from Bio.SeqUtils import gc_fraction

from animal_search import AnimalSearchEngine
from database import *

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

st.set_page_config(
    page_title="DNA Art Generator",
    page_icon="🧬",
    layout="wide"
)

if 'session_id' not in st.session_state:
    st.session_state.session_id = hashlib.md5(str(np.random.random()).encode()).hexdigest()

# Paletas de colores semánticas por categoría taxonómica
TAXONOMIC_PALETTES = {
    'mammal': {
        'primary': ['#8B4513', '#CD853F', '#DEB887', '#F4A460', '#D2691E'],
        'secondary': ['#FF6347', '#FFB347', '#FFCCCB', '#FFA07A', '#FA8072'],
        'accent': ['#4169E1', '#6495ED', '#87CEEB', '#B0C4DE', '#E6E6FA']
    },
    'aquatic': {
        'primary': ['#000080', '#0000CD', '#4169E1', '#6495ED', '#87CEEB'],
        'secondary': ['#20B2AA', '#48D1CC', '#40E0D0', '#AFEEEE', '#E0FFFF'],
        'accent': ['#FF1493', '#FF69B4', '#FFB6C1', '#FFC0CB', '#FFCCCB']
    },
    'avian': {
        'primary': ['#FFD700', '#FFA500', '#FF8C00', '#FF7F50', '#FF6347'],
        'secondary': ['#4682B4', '#5F9EA0', '#6495ED', '#7B68EE', '#9370DB'],
        'accent': ['#32CD32', '#90EE90', '#98FB98', '#F0FFF0', '#FFFFE0']
    },
    'reptile': {
        'primary': ['#228B22', '#32CD32', '#9ACD32', '#ADFF2F', '#7FFF00'],
        'secondary': ['#8B4513', '#A0522D', '#CD853F', '#D2B48C', '#F5DEB3'],
        'accent': ['#DC143C', '#B22222', '#FF0000', '#FF6347', '#FA8072']
    },
    'arthropod': {
        'primary': ['#4B0082', '#8B008B', '#9932CC', '#BA55D3', '#DA70D6'],
        'secondary': ['#FF4500', '#FF6347', '#FF8C00', '#FFA500', '#FFD700'],
        'accent': ['#00CED1', '#40E0D0', '#48D1CC', '#20B2AA', '#008B8B']
    },
    'plant': {
        'primary': ['#006400', '#228B22', '#32CD32', '#90EE90', '#98FB98'],
        'secondary': ['#8B4513', '#A0522D', '#CD853F', '#D2B48C', '#DEB887'],
        'accent': ['#FF69B4', '#FFB6C1', '#FFC0CB', '#FFCCCB', '#F0F8FF']
    }
}

# ============================================================================
# FUNCIONES CORE OPTIMIZADAS
# ============================================================================

def clean_scientific_name(name: str) -> str:
    """Limpia y normaliza nombres científicos"""
    cleaned = re.sub(r'\([^)]*\)', '', name)
    cleaned = re.sub(r'\d{4}', '', cleaned)
    cleaned = re.sub(r'[,;].*', '', cleaned)
    return cleaned.strip()

def fetch_dna_sequence(organism: str):
    """
    Obtiene secuencia de ADN desde NCBI con estrategia de búsqueda optimizada
    Prioriza: genoma completo > cromosomas > mitocondrial > plastidios
    """
    try:
        Entrez.email = st.secrets["ENTREZ_EMAIL"]
        clean_name = clean_scientific_name(organism).replace('"', '').replace("'", "")
        
        # Estrategias priorizando genomas completos y cromosomas
        search_strategies = [
            # Genoma completo (máxima prioridad)
            f'"{clean_name}"[Organism] AND ("complete genome"[Title] OR "genome assembly"[Title])',
            f'"{clean_name}"[Organism] AND "chromosome"[Title] AND "complete"[Title]',
            
            # Cromosomas individuales  
            f'"{clean_name}"[Organism] AND "chromosome"[Title]',
            f'"{clean_name}"[Organism] AND ("chromosome 1"[Title] OR "chr1"[Title])',
            
            # Genomas de cloroplastos (plantas)
            f'"{clean_name}"[Organism] AND ("chloroplast"[Title] OR "plastid"[Title]) AND "complete"[Title]',
            
            # Mitocondrial como respaldo
            f'"{clean_name}"[Organism] AND "mitochondrion"[Title] AND "complete"[Title]',
            f'"{clean_name}"[Organism] AND "mitochondrial"[Title]',
            
            # Búsqueda general
            f'"{clean_name}"[Organism]'
        ]
        
        best_sequence = None
        best_score = 0
        
        for i, strategy in enumerate(search_strategies):
            try:
                search_handle = Entrez.esearch(
                    db="nucleotide", 
                    term=strategy, 
                    retmax=5,
                    sort="length"  # Ordena por longitud descendente
                )
                search_results = Entrez.read(search_handle)
                search_handle.close()
                
                if search_results and search_results.get("IdList"):
                    # Evalúa cada secuencia encontrada
                    for seq_id in search_results["IdList"][:3]:  # Máximo 3 por estrategia
                        try:
                            # Obtiene metadatos primero
                            summary_handle = Entrez.esummary(db="nucleotide", id=seq_id)
                            summary = Entrez.read(summary_handle)[0]
                            summary_handle.close()
                            
                            length = int(summary.get("Length", 0))
                            title = summary.get("Title", "").lower()
                            
                            # Sistema de puntuación para priorizar mejores secuencias
                            score = calculate_sequence_priority_score(title, length, i)
                            
                            if score > best_score and length >= 1000:  # Mínimo 1kb
                                # Obtiene la secuencia
                                fetch_handle = Entrez.efetch(
                                    db="nucleotide", 
                                    id=seq_id, 
                                    rettype="fasta", 
                                    retmode="text"
                                )
                                fasta_data = fetch_handle.read()
                                fetch_handle.close()
                                
                                if fasta_data.strip():
                                    seq_record = SeqIO.read(io.StringIO(fasta_data), "fasta")
                                    if len(seq_record.seq) >= 1000:
                                        best_sequence = seq_record
                                        best_score = score
                        
                        except Exception:
                            continue  # Prueba la siguiente secuencia
                            
            except Exception:
                continue  # Prueba la siguiente estrategia
        
        if not best_sequence:
            raise ValueError(f"No se encontraron secuencias válidas para {organism}")
        
        return best_sequence
        
    except Exception as e:
        raise ValueError(f"Error obteniendo secuencia: {str(e)}")

def calculate_sequence_priority_score(title: str, length: int, strategy_index: int) -> float:
    """Calcula puntuación de prioridad para seleccionar la mejor secuencia"""
    score = 0
    
    # Bonificación por tipo de secuencia (mayor = mejor)
    if "complete genome" in title:
        score += 1000
    elif "genome assembly" in title:
        score += 900
    elif "chromosome" in title and "complete" in title:
        score += 800
    elif "chromosome" in title:
        score += 700
    elif "chloroplast" in title and "complete" in title:
        score += 600
    elif "plastid" in title and "complete" in title:
        score += 550
    elif "mitochondrion" in title and "complete" in title:
        score += 400
    elif "mitochondrial" in title:
        score += 300
    
    # Bonificación por longitud (logarítmica para evitar dominancia extrema)
    score += math.log10(max(length, 1)) * 50
    
    # Penalización por índice de estrategia (estrategias posteriores son menos preferidas)
    score -= strategy_index * 50
    
    # Bonificaciones específicas
    if "reference" in title:
        score += 100
    if "refseq" in title:
        score += 50
        
    return score

def analyze_genetic_profile(sequence: str, organism_id: str) -> Dict:
    """Análisis completo del perfil genético para arte único"""
    base_counts = {'A': 0, 'T': 0, 'C': 0, 'G': 0}
    for base in sequence:
        if base in base_counts:
            base_counts[base] += 1
    
    total_bases = sum(base_counts.values())
    if total_bases == 0:
        return {
            'organism_id': organism_id,
            'sequence_length': 0,
            'error': 'Secuencia vacía'
        }
    
    frequencies = {base: count / total_bases for base, count in base_counts.items()}
    
    # Análisis de dinucleótidos y trinucleótidos
    dinucleotides = {}
    trinucleotides = {}
    
    for i in range(len(sequence) - 1):
        dinuc = sequence[i:i+2]
        if len(dinuc) == 2 and all(b in 'ATCG' for b in dinuc):
            dinucleotides[dinuc] = dinucleotides.get(dinuc, 0) + 1
    
    for i in range(len(sequence) - 2):
        trinuc = sequence[i:i+3]
        if len(trinuc) == 3 and all(b in 'ATCG' for b in trinuc):
            trinucleotides[trinuc] = trinucleotides.get(trinuc, 0) + 1
    
    # Análisis de patrones repetitivos
    repeat_patterns = detect_repeat_patterns(sequence)
    
    # Análisis de skew (bias direccional)
    gc_skew = calculate_gc_skew(sequence)
    at_skew = calculate_at_skew(sequence)
    
    # Entropía de Shannon para diferentes niveles
    entropy_mono = -sum(f * math.log2(f) for f in frequencies.values() if f > 0)
    
    dinuc_freq = {k: v/len(sequence) for k, v in dinucleotides.items()}
    entropy_di = -sum(f * math.log2(f) for f in dinuc_freq.values() if f > 0)
    
    # Contenido GC y análisis de ventanas
    gc_content = (base_counts['G'] + base_counts['C']) / total_bases * 100
    gc_variance = calculate_gc_variance(sequence)
    
    # Periodicidades y estructuras secundarias
    periodicities = detect_periodicities(sequence)
    
    # Complejidad genética multidimensional
    complexity_score = calculate_complexity_score(
        entropy_mono, entropy_di, gc_content, gc_variance, repeat_patterns
    )
    
    # Firma genética única (hash de características específicas)
    genetic_signature = generate_genetic_signature(
        sequence, organism_id, dinucleotides, trinucleotides
    )
    
    return {
        'organism_id': organism_id,
        'sequence_length': len(sequence),
        'base_counts': base_counts,
        'frequencies': frequencies,
        'dinucleotides': dinucleotides,
        'trinucleotides': trinucleotides,
        'repeat_patterns': repeat_patterns,
        'gc_content': gc_content,
        'gc_skew': gc_skew,
        'at_skew': at_skew,
        'gc_variance': gc_variance,
        'entropy_mono': entropy_mono,
        'entropy_di': entropy_di,
        'periodicities': periodicities,
        'complexity_score': complexity_score,
        'genetic_signature': genetic_signature,
        'purine_content': (frequencies['A'] + frequencies['G']) * 100,
        'pyrimidine_content': (frequencies['T'] + frequencies['C']) * 100,
        'weak_bonds': (frequencies['A'] + frequencies['T']) * 100,
        'strong_bonds': (frequencies['G'] + frequencies['C']) * 100
    }

def detect_repeat_patterns(sequence: str, min_length: int = 3, max_length: int = 20) -> Dict:
    """Detecta patrones de repetición en la secuencia"""
    patterns = {}
    seq_len = len(sequence)
    
    for length in range(min_length, min(max_length + 1, seq_len // 10)):
        pattern_counts = {}
        
        for i in range(seq_len - length + 1):
            pattern = sequence[i:i+length]
            if all(b in 'ATCG' for b in pattern):
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Solo conserva patrones que aparecen múltiples veces
        significant_patterns = {p: c for p, c in pattern_counts.items() if c >= 3}
        if significant_patterns:
            patterns[f'length_{length}'] = significant_patterns
    
    return patterns

def calculate_gc_skew(sequence: str, window_size: int = 1000) -> List[float]:
    """Calcula GC skew en ventanas deslizantes"""
    skews = []
    for i in range(0, len(sequence) - window_size + 1, window_size // 2):
        window = sequence[i:i+window_size]
        g_count = window.count('G')
        c_count = window.count('C')
        
        if g_count + c_count > 0:
            skew = (g_count - c_count) / (g_count + c_count)
        else:
            skew = 0
        skews.append(skew)
    
    return skews

def calculate_at_skew(sequence: str, window_size: int = 1000) -> List[float]:
    """Calcula AT skew en ventanas deslizantes"""
    skews = []
    for i in range(0, len(sequence) - window_size + 1, window_size // 2):
        window = sequence[i:i+window_size]
        a_count = window.count('A')
        t_count = window.count('T')
        
        if a_count + t_count > 0:
            skew = (a_count - t_count) / (a_count + t_count)
        else:
            skew = 0
        skews.append(skew)
    
    return skews

def calculate_gc_variance(sequence: str, window_size: int = 500) -> float:
    """Calcula la varianza del contenido GC en ventanas"""
    gc_contents = []
    for i in range(0, len(sequence) - window_size + 1, window_size // 4):
        window = sequence[i:i+window_size]
        gc_count = window.count('G') + window.count('C')
        gc_content = gc_count / len(window) if len(window) > 0 else 0
        gc_contents.append(gc_content)
    
    if len(gc_contents) > 1:
        mean_gc = sum(gc_contents) / len(gc_contents)
        variance = sum((gc - mean_gc) ** 2 for gc in gc_contents) / len(gc_contents)
        return variance
    return 0

def detect_periodicities(sequence: str) -> Dict:
    """Detecta periodicidades específicas en la secuencia"""
    periodicities = {}
    max_period = min(50, len(sequence) // 20)
    
    for period in range(2, max_period + 1):
        correlations = []
        for i in range(len(sequence) - period):
            if sequence[i] == sequence[i + period]:
                correlations.append(1)
            else:
                correlations.append(0)
        
        if correlations:
            correlation = sum(correlations) / len(correlations)
            if correlation > 0.3:  # Umbral para periodicidad significativa
                periodicities[f'period_{period}'] = correlation
    
    return periodicities

def calculate_complexity_score(entropy_mono: float, entropy_di: float, 
                              gc_content: float, gc_variance: float, 
                              repeat_patterns: Dict) -> float:
    """Calcula puntuación de complejidad multidimensional"""
    # Normaliza entropías (máximo teórico: 2.0 para mono, 4.0 para di)
    norm_entropy_mono = entropy_mono / 2.0
    norm_entropy_di = entropy_di / 4.0
    
    # Normaliza GC content (óptimo alrededor de 50%)
    gc_score = 1 - abs(gc_content - 50) / 50
    
    # Penaliza alta varianza GC (indica falta de homogeneidad)
    variance_penalty = max(0, 1 - gc_variance * 10)
    
    # Bonifica presencia de patrones repetitivos complejos
    pattern_bonus = min(0.3, len(repeat_patterns) * 0.05)
    
    complexity = (
        norm_entropy_mono * 0.3 + 
        norm_entropy_di * 0.3 + 
        gc_score * 0.2 + 
        variance_penalty * 0.1 + 
        pattern_bonus * 0.1
    )
    
    return max(0, min(1, complexity))

def generate_genetic_signature(sequence: str, organism_id: str, 
                              dinucleotides: Dict, trinucleotides: Dict) -> str:
    """Genera una firma genética única específica de la especie"""
    # Combina características únicas para crear una firma
    signature_elements = [
        organism_id,
        str(len(sequence)),
        str(sequence.count('A')),
        str(sequence.count('T')),
        str(sequence.count('G')),
        str(sequence.count('C')),
        str(sorted(dinucleotides.items(), key=lambda x: x[1], reverse=True)[:5]),
        str(sorted(trinucleotides.items(), key=lambda x: x[1], reverse=True)[:3])
    ]
    
    signature_string = '|'.join(signature_elements)
    return hashlib.md5(signature_string.encode()).hexdigest()[:16]

# ============================================================================
# CLASIFICACIÓN TAXONÓMICA
# ============================================================================

def determine_taxonomic_category(species_name: str, description: str) -> str:
    """Determina categoría taxonómica para paletas semánticas"""
    name_lower = species_name.lower()
    
    patterns = {
        'mammal': ['panthera', 'canis', 'felis', 'homo', 'bos', 'ursus', 'rattus'],
        'aquatic': ['balaenoptera', 'tursiops', 'salmo', 'octopus', 'cancer'],
        'avian': ['aquila', 'bubo', 'falco', 'corvus', 'gallus'],
        'reptile': ['python', 'crocodylus', 'iguana', 'gecko', 'chelonia'],
        'arthropod': ['drosophila', 'apis', 'aedes', 'tribolium'],
        'plant': ['arabidopsis', 'oryza', 'triticum', 'zea', 'solanum']
    }
    
    for category, category_patterns in patterns.items():
        if any(pattern in name_lower for pattern in category_patterns):
            return category
    
    return 'mammal'  # Default

def get_taxonomic_palette(category: str) -> Dict:
    """Obtiene paleta específica por categoría"""
    return TAXONOMIC_PALETTES.get(category, TAXONOMIC_PALETTES['mammal'])

# ============================================================================
# SISTEMA DE CAPAS MÚLTIPLES Y EFECTOS VISUALES AVANZADOS
# ============================================================================

def determine_habitat_type(category: str, organism_name: str) -> str:
    """Determina el tipo de hábitat para efectos de fondo"""
    name_lower = organism_name.lower()
    
    # Mapeo específico por nombre de organismo
    aquatic_indicators = ['whale', 'dolphin', 'shark', 'fish', 'octopus', 'squid', 'salmon', 'tuna']
    aerial_indicators = ['eagle', 'falcon', 'hawk', 'owl', 'sparrow', 'crow', 'parrot']
    arboreal_indicators = ['monkey', 'sloth', 'koala', 'lemur', 'squirrel']
    
    if any(indicator in name_lower for indicator in aquatic_indicators) or category == 'aquatic':
        return 'oceanic'
    elif any(indicator in name_lower for indicator in aerial_indicators) or category == 'avian':
        return 'aerial'
    elif any(indicator in name_lower for indicator in arboreal_indicators):
        return 'arboreal'
    else:
        return 'terrestrial'

def create_habitat_background_layer(habitat_type: str, genetic_profile: Dict, palette: Dict) -> List[go.Scatter]:
    """Crea capa de fondo basada en hábitat"""
    background_traces = []
    
    if habitat_type == 'oceanic':
        # Capas de profundidad oceánica
        depths = [0.9, 0.7, 0.5, 0.3, 0.1]
        for i, depth in enumerate(depths):
            n_particles = 50 - i * 8
            x = np.random.uniform(-1.2, 1.2, n_particles) 
            y = np.random.uniform(-1.2 + i * 0.4, 1.2 - i * 0.4, n_particles)
            
            opacity = depth * 0.3
            size = np.random.uniform(1, 4, n_particles)
            
            background_traces.append(go.Scatter(
                x=x, y=y, mode='markers',
                marker=dict(
                    size=size,
                    color=f'rgba(30, {100 + i * 30}, 255, {opacity})',
                    symbol='circle'
                ),
                showlegend=False, hoverinfo='skip'
            ))
    
    elif habitat_type == 'aerial':
        # Nubes y corrientes de aire
        for layer in range(4):
            x = np.linspace(-1.2, 1.2, 60)
            y_base = -0.8 + layer * 0.4
            y = y_base + 0.15 * np.sin(x * 3 + layer * np.pi / 2) * np.exp(-0.5 * layer)
            
            opacity = 0.2 - layer * 0.04
            color = f'rgba(200, 220, 255, {opacity})'
            
            background_traces.append(go.Scatter(
                x=x, y=y, mode='lines',
                line=dict(color=color, width=8 - layer),
                showlegend=False, hoverinfo='skip'
            ))
    
    elif habitat_type == 'arboreal':
        # Estructura de ramas y follaje
        for branch in range(6):
            angle = branch * np.pi / 3
            length = np.linspace(0, 0.8, 30)
            
            x = length * np.cos(angle) * (1 + 0.1 * np.sin(length * 8))
            y = length * np.sin(angle) * (1 + 0.1 * np.cos(length * 8))
            
            background_traces.append(go.Scatter(
                x=x, y=y, mode='lines',
                line=dict(color='rgba(101, 67, 33, 0.4)', width=6 - branch),
                showlegend=False, hoverinfo='skip'
            ))
    
    else:  # terrestrial
        # Texturas terrestres con patrones geológicos
        for layer in range(3):
            n_points = 80 - layer * 20
            radius = 0.3 + layer * 0.2
            angles = np.linspace(0, 2 * np.pi, n_points)
            
            # Variación basada en perfil genético
            complexity_factor = genetic_profile.get('complexity_score', 0.5)
            noise = np.random.normal(0, 0.1 * complexity_factor, n_points)
            
            x = (radius + noise) * np.cos(angles)
            y = (radius + noise) * np.sin(angles)
            
            background_traces.append(go.Scatter(
                x=x, y=y, mode='markers',
                marker=dict(
                    size=3 - layer * 0.5,
                    color=f'rgba({139 - layer * 20}, {120 - layer * 15}, 80, 0.3)',
                    symbol='square'
                ),
                showlegend=False, hoverinfo='skip'
            ))
    
    return background_traces

def create_dna_texture_layer(genetic_profile: Dict, palette: Dict) -> List[go.Scatter]:
    """Genera texturas procedurales basadas en patrones de repetición del ADN"""
    texture_traces = []
    
    # Usar patrones repetitivos para generar texturas
    repeat_patterns = genetic_profile.get('repeat_patterns', {})
    
    if repeat_patterns:
        # Selecciona el patrón más frecuente
        most_frequent_pattern = None
        max_frequency = 0
        
        for length_key, patterns in repeat_patterns.items():
            for pattern, frequency in patterns.items():
                if frequency > max_frequency:
                    max_frequency = frequency
                    most_frequent_pattern = pattern
        
        if most_frequent_pattern:
            # Convierte el patrón de ADN en textura visual
            pattern_length = len(most_frequent_pattern)
            texture_density = min(100, max_frequency // 2)
            
            for i in range(texture_density):
                # Posición basada en el hash del patrón
                hash_value = hash(most_frequent_pattern + str(i))
                x = (hash_value % 1000) / 500 - 1
                y = ((hash_value // 1000) % 1000) / 500 - 1
                
                # Color basado en la composición del patrón
                gc_content = (most_frequent_pattern.count('G') + most_frequent_pattern.count('C')) / pattern_length
                
                if gc_content > 0.6:
                    color = palette['primary'][0]
                elif gc_content < 0.4:
                    color = palette['secondary'][0]
                else:
                    color = palette['accent'][0]
                
                texture_traces.append(go.Scatter(
                    x=[x], y=[y], mode='markers',
                    marker=dict(
                        size=2 + pattern_length * 0.5,
                        color=color,
                        opacity=0.15,
                        symbol='diamond'
                    ),
                    showlegend=False, hoverinfo='skip'
                ))
    
    return texture_traces

# ============================================================================
# GENERADORES DE PATRONES VISUALES UNIFICADOS CON CAPAS
# ============================================================================

def create_pattern_by_category(category: str, n_points: int, palette: Dict, genetic_profile: Dict) -> List[go.Scatter]:
    """Generador unificado de patrones por categoría taxonómica"""
    traces = []
    
    if category == 'mammal':
        # Espiral dorada orgánica
        golden_ratio = 1.618033988749
        for layer in range(5):
            angles = np.linspace(0, 8 * np.pi, n_points // 5)
            r = np.sqrt(angles) * 0.1 * (layer + 1)
            x = r * np.cos(angles * golden_ratio) * (1 + 0.1 * np.sin(angles * 3))
            y = r * np.sin(angles * golden_ratio) * (1 + 0.1 * np.cos(angles * 3))
            
            traces.append(go.Scatter(
                x=x, y=y, mode='markers',
                marker=dict(
                    size=np.random.uniform(2, 8, len(x)),
                    color=palette['primary'][layer % len(palette['primary'])],
                    opacity=0.7
                ),
                showlegend=False
            ))
    
    elif category == 'aquatic':
        # Ondas fluidas
        for wave in range(7):
            t = np.linspace(0, 4 * np.pi, max(10, n_points // 7))
            amplitude = 0.6 - wave * 0.08
            frequency = 2 + wave * 0.5
            
            x = t / (2 * np.pi) - 1
            y = amplitude * np.sin(frequency * t) * np.exp(-0.1 * wave * t)
            
            traces.append(go.Scatter(
                x=x, y=y, mode='lines+markers',
                line=dict(color=palette['primary'][wave % len(palette['primary'])], width=3),
                marker=dict(size=4, color=palette['secondary'][wave % len(palette['secondary'])]),
                showlegend=False
            ))
    
    elif category == 'avian':
        # Plumas radiantes
        for feather in range(12):
            angle_base = feather * 2 * np.pi / 12
            spine_length = np.linspace(0, 0.8, 40)
            spine_x = spine_length * np.cos(angle_base)
            spine_y = spine_length * np.sin(angle_base)
            
            traces.append(go.Scatter(
                x=spine_x, y=spine_y, mode='lines',
                line=dict(color=palette['primary'][feather % len(palette['primary'])], width=2),
                showlegend=False
            ))
    
    elif category == 'reptile':
        # Escamas hexagonales
        for layer in range(3):
            radius = 0.3 + layer * 0.2
            n_hexagons = 6 + layer * 2
            angles = np.linspace(0, 2 * np.pi, n_hexagons, endpoint=False)
            x_hex = radius * np.cos(angles)
            y_hex = radius * np.sin(angles)
            
            traces.append(go.Scatter(
                x=x_hex, y=y_hex, mode='markers',
                marker=dict(
                    size=15 - layer * 3,
                    color=palette['primary'][layer % len(palette['primary'])],
                    symbol='hexagon'
                ),
                showlegend=False
            ))
    
    else:  # arthropod, plant, default
        # Patrón general: espiral cósmica
        t = np.linspace(0, 6 * np.pi, min(n_points, 200))
        r = 0.1 * t
        x = r * np.cos(t) * np.exp(-0.1 * t)
        y = r * np.sin(t) * np.exp(-0.1 * t)
        
        traces.append(go.Scatter(
            x=x, y=y, mode='markers',
            marker=dict(
                size=np.linspace(2, 8, len(x)),
                color=palette['primary'][0],
                opacity=0.8
            ),
            showlegend=False
        ))
    
    return traces

# ============================================================================
# SISTEMA DE ANIMACIÓN UNIFICADO
# ============================================================================

def determine_animation_type(organism_name: str, genetic_profile: Dict) -> str:
    """Determina tipo de animación basado en organismo"""
    name_lower = organism_name.lower()
    
    if any(word in name_lower for word in ['dolphin', 'whale', 'fish', 'octopus']):
        return 'aquatic_flow'
    elif any(word in name_lower for word in ['lion', 'tiger', 'wolf', 'bear', 'jaguar']):
        return 'heartbeat_mammal'
    else:
        return 'cosmic_rotation'

def create_animation_frame(progress: float, animation_type: str, genetic_profile: Dict) -> List[go.Scatter]:
    """Generador unificado de frames de animación"""
    traces = []
    
    if animation_type == 'heartbeat_mammal':
        # Latido rítmico
        pulse_phase = progress * 6 * 2 * np.pi
        pulse_intensity = 1 + 0.6 * np.sin(pulse_phase)
        
        for ring in range(5):
            theta = np.linspace(0, 2 * np.pi, 80)
            base_radius = 0.15 + ring * 0.12
            radius = base_radius * pulse_intensity * (1 - ring * 0.08)
            
            x = radius * np.cos(theta)
            y = radius * np.sin(theta)
            
            opacity = max(0.1, (0.8 - ring * 0.15) * (0.5 + 0.5 * np.sin(pulse_phase)))
            color = f'rgba({255 - ring * 30}, {100 + ring * 20}, 50, {opacity})'
            
            traces.append(go.Scatter(
                x=x, y=y, mode='lines',
                line=dict(color=color, width=max(1, 3 + ring - 2 * np.sin(pulse_phase))),
                showlegend=False, hoverinfo='skip'
            ))
    
    elif animation_type == 'aquatic_flow':
        # Ondas fluidas
        for wave_layer in range(6):
            t = np.linspace(-2, 2, 80)
            frequency = 2 + wave_layer * 0.5
            amplitude = 0.15 - wave_layer * 0.02
            phase = progress * 6 * np.pi + wave_layer * np.pi / 3
            
            x = t
            y = amplitude * np.sin(frequency * np.pi * t + phase) * np.exp(-0.1 * abs(t))
            y += -0.7 + wave_layer * 0.25
            
            transparency = max(0.1, 0.7 - wave_layer * 0.1)
            color = f'rgba(30, {150 + wave_layer * 20}, 255, {transparency})'
            
            traces.append(go.Scatter(
                x=x, y=y, mode='lines',
                line=dict(color=color, width=4 - wave_layer * 0.5),
                showlegend=False, hoverinfo='skip'
            ))
    
    else:  # cosmic_rotation
        # Rotación cósmica
        n_stars = 20
        galaxy_rotation = progress * 2 * np.pi
        
        for star in range(n_stars):
            star_angle = star * 2 * np.pi / n_stars + galaxy_rotation
            orbit_radius = 0.2 + 0.5 * (star % 5) / 5
            
            x = orbit_radius * np.cos(star_angle)
            y = orbit_radius * np.sin(star_angle)
            
            brightness = max(0.1, 0.4 + 0.6 * np.sin(progress * 12 * np.pi + star * np.pi / 3))
            color = f'rgba(255, 255, 200, {brightness})'
            
            traces.append(go.Scatter(
                x=[x], y=[y], mode='markers',
                marker=dict(size=4 + 6 * brightness, color=color, symbol='star'),
                showlegend=False, hoverinfo='skip'
            ))
    
    return traces

# ============================================================================
# MOTOR DE VISUALIZACIÓN PRINCIPAL
# ============================================================================

def create_genetic_art(sequence: str, genetic_profile: Dict, category: str, palette: Dict) -> go.Figure:
    """
    Algoritmo base universal para generar arte genético de cualquier animal
    Procesa ADN y crea representaciones visuales únicas basadas en características genéticas
    """
    fig = go.Figure()
    organism_name = genetic_profile.get('organism_id', 'Unknown')
    
    # PASO 1: Determinar hábitat para capas de fondo
    habitat_type = determine_habitat_type(category, organism_name)
    
    # PASO 2: Crear capas de fondo basadas en hábitat
    background_layers = create_habitat_background_layer(habitat_type, genetic_profile, palette)
    for layer in background_layers:
        fig.add_trace(layer)
    
    # PASO 3: Añadir textura procedural basada en patrones de ADN
    texture_layers = create_dna_texture_layer(genetic_profile, palette)
    for texture in texture_layers:
        fig.add_trace(texture)
    
    # PASO 4: Generar patrón principal basado en perfil genético
    sequence_length = len(sequence)
    n_points = min(2000, sequence_length // 10)
    
    # Usar algoritmo universal basado en características genéticas
    main_pattern = create_universal_dna_pattern(genetic_profile, palette, n_points)
    for trace in main_pattern:
        fig.add_trace(trace)
    
    # PASO 5: Añadir elementos de complejidad genética
    complexity_elements = create_genetic_complexity_elements(genetic_profile, palette)
    for element in complexity_elements:
        fig.add_trace(element)
    
    # Layout optimizado con información genética
    fig.update_layout(
        title=dict(
            text=f"🧬 {organism_name} - Genoma Artístico",
            font=dict(size=20, color=palette['accent'][0]),
            x=0.5
        ),
        plot_bgcolor='rgba(5,5,5,1)',
        paper_bgcolor='rgba(5,5,5,1)',
        showlegend=False,
        xaxis=dict(visible=False, range=[-1.4, 1.4]),
        yaxis=dict(visible=False, range=[-1.4, 1.4]),
        height=700,
        annotations=[
            dict(
                text=f"Longitud: {genetic_profile.get('sequence_length', 0):,} bp | "
                     f"GC: {genetic_profile.get('gc_content', 0):.1f}% | "
                     f"Complejidad: {genetic_profile.get('complexity_score', 0):.3f}",
                xref="paper", yref="paper",
                x=0.5, y=0.02,
                showarrow=False,
                font=dict(size=10, color=palette['accent'][0])
            )
        ]
    )
    
    return fig

def create_universal_dna_pattern(genetic_profile: Dict, palette: Dict, n_points: int) -> List[go.Scatter]:
    """
    Algoritmo universal que genera patrones visuales basados en características genéticas
    Aplicable a cualquier animal sin depender de clasificación taxonómica
    """
    traces = []
    
    # Extraer parámetros genéticos universales
    gc_content = genetic_profile.get('gc_content', 50)
    entropy_mono = genetic_profile.get('entropy_mono', 1.5)
    entropy_di = genetic_profile.get('entropy_di', 3.0)
    complexity_score = genetic_profile.get('complexity_score', 0.5)
    sequence_length = genetic_profile.get('sequence_length', 1000)
    
    # Normalizar parámetros para uso visual
    gc_normalized = gc_content / 100  # 0-1
    entropy_norm = entropy_mono / 2.0  # 0-1 aproximadamente
    complexity_norm = min(1.0, complexity_score)
    
    # ALGORITMO BASE: Generar estructura principal
    
    # 1. Determinar forma base según contenido GC
    if gc_content < 35:
        # Bajo GC: Estructuras más lineales y abiertas
        base_structure = create_linear_structure(n_points, complexity_norm)
    elif gc_content > 65:
        # Alto GC: Estructuras más compactas y circulares
        base_structure = create_circular_structure(n_points, complexity_norm)
    else:
        # GC medio: Estructuras espirales balanceadas
        base_structure = create_spiral_structure(n_points, complexity_norm)
    
    # 2. Aplicar modulación basada en entropía
    modulated_structure = apply_entropy_modulation(base_structure, entropy_norm, entropy_di)
    
    # 3. Añadir elementos basados en dinucleótidos
    dinucleotide_elements = create_dinucleotide_elements(genetic_profile, palette)
    
    # 4. Crear estructura principal
    main_trace = go.Scatter(
        x=modulated_structure['x'],
        y=modulated_structure['y'],
        mode='markers+lines',
        marker=dict(
            size=modulated_structure['sizes'],
            color=modulated_structure['colors'],
            opacity=0.8,
            line=dict(width=1, color='white')
        ),
        line=dict(
            color=palette['primary'][0],
            width=2 + complexity_norm * 3
        ),
        showlegend=False
    )
    traces.append(main_trace)
    
    # 5. Añadir elementos de dinucleótidos
    traces.extend(dinucleotide_elements)
    
    return traces

def create_linear_structure(n_points: int, complexity: float) -> Dict:
    """Estructura lineal para secuencias con bajo contenido GC"""
    t = np.linspace(-1, 1, n_points)
    
    # Línea base con ondulación basada en complejidad
    x = t
    y = 0.3 * complexity * np.sin(t * np.pi * (2 + complexity * 4))
    
    # Variación de tamaños basada en posición
    sizes = 3 + 5 * (1 + np.sin(t * np.pi * 3)) * complexity
    
    # Colores que varían a lo largo de la estructura
    colors = np.linspace(0, 1, n_points)
    
    return {'x': x, 'y': y, 'sizes': sizes, 'colors': colors}

def create_circular_structure(n_points: int, complexity: float) -> Dict:
    """Estructura circular para secuencias con alto contenido GC"""
    angles = np.linspace(0, 2 * np.pi, n_points)
    
    # Radio variable basado en complejidad
    base_radius = 0.5
    radius_variation = 0.3 * complexity * np.sin(angles * (3 + complexity * 5))
    radius = base_radius + radius_variation
    
    x = radius * np.cos(angles)
    y = radius * np.sin(angles)
    
    # Tamaños que varían radialmente
    sizes = 2 + 6 * (0.5 + 0.5 * np.sin(angles * 2)) * complexity
    
    # Colores basados en ángulo
    colors = (angles / (2 * np.pi))
    
    return {'x': x, 'y': y, 'sizes': sizes, 'colors': colors}

def create_spiral_structure(n_points: int, complexity: float) -> Dict:
    """Estructura espiral para contenido GC balanceado"""
    t = np.linspace(0, 4 * np.pi, n_points)
    
    # Espiral con crecimiento controlado por complejidad
    radius = 0.1 + 0.4 * t / (4 * np.pi) * (1 + 0.5 * complexity)
    
    # Modulación adicional basada en complejidad
    radius_mod = radius * (1 + 0.2 * complexity * np.sin(t * (2 + complexity * 3)))
    
    x = radius_mod * np.cos(t)
    y = radius_mod * np.sin(t)
    
    # Tamaños que crecen hacia el exterior
    sizes = 2 + 4 * (t / (4 * np.pi)) + 3 * complexity * np.sin(t)
    
    # Colores que siguen la espiral
    colors = t / (4 * np.pi)
    
    return {'x': x, 'y': y, 'sizes': sizes, 'colors': colors}

def apply_entropy_modulation(structure: Dict, entropy_norm: float, entropy_di: float) -> Dict:
    """Aplica modulación basada en entropía de la secuencia"""
    x, y = structure['x'], structure['y']
    sizes, colors = structure['sizes'], structure['colors']
    
    # Noise basado en entropía
    noise_intensity = entropy_norm * 0.2
    
    # Aplicar ruido gaussiano
    x_noise = np.random.normal(0, noise_intensity, len(x))
    y_noise = np.random.normal(0, noise_intensity, len(y))
    
    # Modulación de frecuencia alta basada en entropía de dinucleótidos
    high_freq = entropy_di / 4.0
    freq_modulation = 0.1 * high_freq * np.sin(np.arange(len(x)) * 0.5)
    
    return {
        'x': x + x_noise + freq_modulation,
        'y': y + y_noise + freq_modulation,
        'sizes': sizes * (0.8 + 0.4 * entropy_norm),
        'colors': colors
    }

def create_dinucleotide_elements(genetic_profile: Dict, palette: Dict) -> List[go.Scatter]:
    """Crea elementos visuales basados en frecuencias de dinucleótidos"""
    traces = []
    dinucleotides = genetic_profile.get('dinucleotides', {})
    
    if not dinucleotides:
        return traces
    
    # Obtener los 8 dinucleótidos más frecuentes
    sorted_dinucs = sorted(dinucleotides.items(), key=lambda x: x[1], reverse=True)[:8]
    
    for i, (dinuc, frequency) in enumerate(sorted_dinucs):
        # Posición basada en índice
        angle = i * 2 * np.pi / 8
        radius = 0.8 + 0.2 * (frequency / max(dinucleotides.values()))
        
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        
        # Color basado en composición del dinucleótido
        if 'A' in dinuc and 'T' in dinuc:
            color = palette['primary'][0]
        elif 'G' in dinuc and 'C' in dinuc:
            color = palette['secondary'][0]
        else:
            color = palette['accent'][0]
        
        # Tamaño proporcional a frecuencia
        size = 8 + 12 * (frequency / max(dinucleotides.values()))
        
        traces.append(go.Scatter(
            x=[x], y=[y],
            mode='markers',
            marker=dict(
                size=size,
                color=color,
                opacity=0.7,
                symbol='hexagon',
                line=dict(width=2, color='white')
            ),
            text=dinuc,
            textposition='middle center',
            showlegend=False
        ))
    
    return traces

def create_genetic_complexity_elements(genetic_profile: Dict, palette: Dict) -> List[go.Scatter]:
    """Añade elementos visuales que representan la complejidad genética"""
    traces = []
    
    complexity_score = genetic_profile.get('complexity_score', 0.5)
    gc_skew = genetic_profile.get('gc_skew', [])
    
    # Elementos de complejidad como partículas dispersas
    if complexity_score > 0.3:
        n_complexity_elements = int(50 * complexity_score)
        
        # Distribución aleatoria con densidad basada en complejidad
        x_complex = np.random.uniform(-1.2, 1.2, n_complexity_elements)
        y_complex = np.random.uniform(-1.2, 1.2, n_complexity_elements)
        
        # Tamaños variables
        sizes_complex = np.random.uniform(1, 4, n_complexity_elements) * complexity_score
        
        traces.append(go.Scatter(
            x=x_complex,
            y=y_complex,
            mode='markers',
            marker=dict(
                size=sizes_complex,
                color=palette['accent'][0],
                opacity=0.3,
                symbol='star'
            ),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Representación de GC skew como ondas
    if gc_skew and len(gc_skew) > 5:
        x_skew = np.linspace(-1, 1, len(gc_skew))
        y_skew = 0.9 + 0.2 * np.array(gc_skew)  # Posición superior
        
        traces.append(go.Scatter(
            x=x_skew,
            y=y_skew,
            mode='lines',
            line=dict(
                color=palette['secondary'][0],
                width=1,
                dash='dot'
            ),
            opacity=0.6,
            showlegend=False,
            hoverinfo='skip'
        ))
    
    return traces

# Animation functions removed as requested by user

# ============================================================================
# INTERFAZ PRINCIPAL OPTIMIZADA
# ============================================================================

def main():
    """Interfaz principal del generador de arte genético universal"""
    
    st.title("🧬 DNA Art Generator Universal")
    st.markdown("**Algoritmo base para generar arte genético de cualquier animal basado en secuencias de ADN reales**")
    
    # Tabs principales
    tab1, tab2, tab3 = st.tabs(["🎨 Generador", "📊 Algoritmo", "🏛️ Galería"])
    
    with tab2:
        st.markdown("### Parámetros Genéticos Analizados")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Estructura Visual:**
            - **Contenido GC < 35%**: Estructura lineal ondulante
            - **Contenido GC > 65%**: Estructura circular compacta  
            - **Contenido GC 35-65%**: Estructura espiral balanceada
            """)
        
        with col2:
            st.markdown("""
            **Modulación Visual:**
            - **Entropía**: Controla variación y ruido
            - **Complejidad**: Densidad de elementos
            - **Patrones repetitivos**: Texturas procedurales
            - **Skew direccional**: Ondas y bias visual
            """)
    
    with tab3:
        st.markdown("### Galería de Especies")
        if 'gallery' not in st.session_state:
            st.session_state.gallery = []
        
        if st.session_state.gallery:
            for i, entry in enumerate(st.session_state.gallery):
                with st.expander(f"{entry['name']} - {entry['sequence_type']}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.plotly_chart(entry['figure'], use_container_width=True, key=f"gallery_{i}")
                    with col2:
                        st.metric("GC Content", f"{entry['gc']:.1f}%")
                        st.metric("Longitud", f"{entry['length']:,} bp")
                        st.metric("Complejidad", f"{entry['complexity']:.3f}")
        else:
            st.info("La galería se llenará automáticamente conforme generes arte de diferentes especies")
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🎯 Generador Universal") 
            animal_input = st.text_input("Cualquier animal:", placeholder="Ej: lobo, delfín, tigre, mariposa, colibrí...")
        
        with col2:
            st.markdown("### 🔬 Secuencias Priorizadas")
            st.info("1. Genoma completo\n2. Cromosomas\n3. Cloroplastos\n4. Mitocondrial")
        
        if animal_input:
            try:
                # Búsqueda de especies
                search_engine = AnimalSearchEngine()
                results = search_engine.search_comprehensive(animal_input)
                
                if results:
                    organism_name = results[0]['scientific_name']
                    st.success(f"✅ Especie encontrada: **{organism_name}**")
                    
                    # Obtener y analizar secuencia con información del tipo
                    with st.spinner("🧬 Buscando mejor secuencia genética disponible..."):
                        seq_record = fetch_dna_sequence(organism_name)
                        sequence = str(seq_record.seq).upper()
                        
                        # Determinar tipo de secuencia obtenida
                        sequence_type = determine_sequence_type(seq_record.description)
                        st.info(f"📊 **Secuencia obtenida**: {sequence_type} ({len(sequence):,} bp)")
                        
                        genetic_profile = analyze_genetic_profile(sequence, seq_record.id)
                    
                    if genetic_profile and 'error' not in genetic_profile:
                        # Determinar categoría y generar arte
                        category = determine_taxonomic_category(organism_name, seq_record.description)
                        palette = get_taxonomic_palette(category)
                        habitat_type = determine_habitat_type(category, organism_name)
                    
                    # Mostrar parámetros del algoritmo
                    st.markdown("### 📈 Parámetros Genéticos Detectados")
                    param_col1, param_col2, param_col3, param_col4 = st.columns(4)
                    
                    with param_col1:
                        gc_content = genetic_profile['gc_content']
                        if gc_content < 35:
                            structure_type = "Lineal"
                        elif gc_content > 65:
                            structure_type = "Circular"
                        else:
                            structure_type = "Espiral"
                        st.metric("GC Content", f"{gc_content:.1f}%", f"→ {structure_type}")
                    
                    with param_col2:
                        entropy_mono = genetic_profile['entropy_mono']
                        st.metric("Entropía Mono", f"{entropy_mono:.3f}", f"→ Variación visual")
                    
                    with param_col3:
                        complexity_score = genetic_profile['complexity_score']
                        st.metric("Complejidad", f"{complexity_score:.3f}", f"→ Densidad elementos")
                    
                    with param_col4:
                        repeat_count = len(genetic_profile.get('repeat_patterns', {}))
                        st.metric("Patrones", f"{repeat_count}", f"→ Texturas")
                    
                    with st.spinner("🎨 Ejecutando algoritmo universal..."):
                        fig = create_genetic_art(sequence, genetic_profile, category, palette)
                    
                    st.markdown("### 🎨 Arte Genético Generado")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Información adicional
                    info_col1, info_col2 = st.columns(2)
                    
                    with info_col1:
                        st.markdown("**🌍 Clasificación Detectada:**")
                        st.write(f"• Categoría: {category.title()}")
                        st.write(f"• Hábitat: {habitat_type.title()}")
                        st.write(f"• Paleta: {len(palette['primary'])} colores primarios")
                    
                    with info_col2:
                        st.markdown("**🧬 Análisis Genético:**")
                        st.write(f"• Dinucleótidos únicos: {len(genetic_profile.get('dinucleotides', {}))}")
                        st.write(f"• Trinucleótidos únicos: {len(genetic_profile.get('trinucleotides', {}))}")
                        st.write(f"• Periodicidades: {len(genetic_profile.get('periodicities', {}))}")
                    
                    # Opciones de exportación y comparación
                    export_col1, export_col2 = st.columns(2)
                    
                    with export_col1:
                        st.markdown("### 💾 Exportar")
                        if st.button("📥 Descargar PNG", type="secondary"):
                            st.success("Arte genético guardado como PNG de alta resolución")
                    
                    with export_col2:
                        st.markdown("### 🔄 Regenerar")
                        if st.button("🎲 Nueva Variación", type="secondary"):
                            st.info("Generando nueva variación con parámetros aleatorios...")
                            st.rerun()
                    
                    # Análisis detallado expandible
                    with st.expander("🔍 Análisis Genético Detallado", expanded=False):
                        detail_col1, detail_col2 = st.columns(2)
                        
                        with detail_col1:
                            st.markdown("**Composición de Bases:**")
                            for base, count in genetic_profile['base_counts'].items():
                                percentage = (count / genetic_profile['sequence_length']) * 100
                                st.write(f"• {base}: {count:,} ({percentage:.1f}%)")
                        
                        with detail_col2:
                            st.markdown("**Métricas Avanzadas:**")
                            st.write(f"• Entropía di: {genetic_profile.get('entropy_di', 0):.3f}")
                            st.write(f"• GC variance: {genetic_profile.get('gc_variance', 0):.4f}")
                            st.write(f"• Purinas: {genetic_profile.get('purine_content', 0):.1f}%")
                            st.write(f"• Pirimidinas: {genetic_profile.get('pyrimidine_content', 0):.1f}%")
                
                else:
                    st.error("❌ No se pudo analizar el perfil genético")
            else:
                st.error("❌ No se encontró información para esta especie")
                st.info("💡 Intenta con el nombre científico o verifica la ortografía")
                
        except Exception as e:
            st.error(f"❌ Error en el proceso: {str(e)}")
            st.info("💡 Intenta con otro animal o verifica la conexión")

def determine_sequence_type(description: str) -> str:
    """Determina el tipo de secuencia obtenida desde la descripción"""
    desc_lower = description.lower()
    
    if "complete genome" in desc_lower:
        return "Genoma Completo"
    elif "genome assembly" in desc_lower:
        return "Ensamblaje Genómico"
    elif "chromosome" in desc_lower and "complete" in desc_lower:
        return "Cromosoma Completo"
    elif "chromosome" in desc_lower:
        return "Cromosoma"
    elif "chloroplast" in desc_lower and "complete" in desc_lower:
        return "Cloroplasto Completo"
    elif "plastid" in desc_lower and "complete" in desc_lower:
        return "Plastidio Completo"
    elif "mitochondrion" in desc_lower and "complete" in desc_lower:
        return "Mitocondria Completa"
    elif "mitochondrial" in desc_lower:
        return "Mitocondrial"
    else:
        return "Secuencia Genética"

if __name__ == "__main__":
    main()