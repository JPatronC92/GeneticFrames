"""
DNA Art Generator - Generador de Arte Genético
Convierte secuencias genéticas reales en arte único mediante análisis bioinformático avanzado.
"""

# Imports consolidados
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import io
import math
import hashlib
import re
import time
from typing import Dict, List, Optional, Tuple

# Bioinformática
from Bio import Entrez, SeqIO
from Bio.SeqUtils import gc_fraction

# Módulos locales
from animal_search import AnimalSearchEngine
from database import *
from symbolic_art_engine import SymbolicArtEngine
from species_identity_profiles import get_species_profile

# ============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================================

# Configuración de página
st.set_page_config(
    page_title="DNA Art Generator",
    page_icon="🧬",
    layout="wide"
)

# Inicializar session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = hashlib.md5(str(np.random.random()).encode()).hexdigest()

# Paletas de colores semánticas optimizadas
TAXONOMIC_COLOR_PALETTES = {
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
# UTILIDADES GENÉTICAS
# ============================================================================

def clean_scientific_name(name: str) -> str:
    """Limpia y normaliza nombres científicos"""
    cleaned = re.sub(r'\([^)]*\)', '', name)
    cleaned = re.sub(r'\d{4}', '', cleaned)
    cleaned = re.sub(r'[,;].*', '', cleaned)
    return cleaned.strip()

def fetch_dna_sequence(organism: str) -> SeqIO.SeqRecord:
    """
    Obtiene secuencia de ADN desde NCBI con estrategia de búsqueda optimizada
    Prioriza: genoma completo > cromosomas > mitocondrial > plastidios
    """
    try:
        # Configurar Entrez
        Entrez.email = st.secrets["ENTREZ_EMAIL"]
        Entrez.api_key = None
        
        clean_name = clean_scientific_name(organism).replace('"', '').replace("'", "")
        
        # Estrategias de búsqueda priorizadas
        search_strategies = [
            f"{clean_name}[Organism] AND genome AND complete",
            f"{clean_name}[Organism] AND chromosome",
            f"{clean_name}[Organism] AND mitochondrion",
            f"{clean_name}[Organism] AND plastid",
            f"{clean_name}[Organism]"
        ]
        
        for strategy in search_strategies:
            search_handle = Entrez.esearch(
                db="nucleotide",
                term=strategy,
                retmax=10,
                sort="length"
            )
            search_results = Entrez.read(search_handle)
            search_handle.close()
            
            if search_results.get("IdList", []):
                seq_id = search_results["IdList"][0]
                break
        else:
            raise ValueError(f"No se encontraron secuencias para {organism}")
        
        # Obtener secuencia
        fetch_handle = Entrez.efetch(
            db="nucleotide",
            id=seq_id,
            rettype="fasta",
            retmode="text"
        )
        fasta_data = fetch_handle.read()
        fetch_handle.close()
        
        if not fasta_data.strip():
            raise ValueError(f"Secuencia vacía para {organism}")
        
        seq_record = SeqIO.read(io.StringIO(fasta_data), "fasta")
        
        if len(seq_record.seq) < 100:
            raise ValueError(f"Secuencia demasiado corta: {len(seq_record.seq)} bp")
        
        return seq_record
        
    except Exception as e:
        raise ValueError(f"Error obteniendo secuencia para '{organism}': {str(e)}")

def analyze_genetic_profile(sequence: str, organism_id: str) -> Dict:
    """Análisis completo del perfil genético para arte único"""
    
    # Conteo de bases
    base_counts = {'A': 0, 'T': 0, 'C': 0, 'G': 0}
    for base in sequence:
        if base in base_counts:
            base_counts[base] += 1
    
    total_bases = sum(base_counts.values())
    if total_bases == 0:
        return None
    
    # Frecuencias de bases
    frequencies = {base: count / total_bases for base, count in base_counts.items()}
    
    # Análisis de dinucleótidos
    dinucleotides = {}
    for i in range(len(sequence) - 1):
        dinuc = sequence[i:i+2]
        if len(dinuc) == 2 and all(b in 'ATCG' for b in dinuc):
            dinucleotides[dinuc] = dinucleotides.get(dinuc, 0) + 1
    
    # Análisis de trinucleótidos
    trinucleotides = {}
    for i in range(len(sequence) - 2):
        trinuc = sequence[i:i+3]
        if len(trinuc) == 3 and all(b in 'ATCG' for b in trinuc):
            trinucleotides[trinuc] = trinucleotides.get(trinuc, 0) + 1
    
    # Cálculo de entropía de Shannon
    entropy = -sum(f * math.log2(f) for f in frequencies.values() if f > 0)
    
    # Contenido GC
    gc_content = (base_counts['G'] + base_counts['C']) / total_bases * 100
    
    # Skew GC y AT
    gc_skew = (base_counts['G'] - base_counts['C']) / (base_counts['G'] + base_counts['C']) if (base_counts['G'] + base_counts['C']) > 0 else 0
    at_skew = (base_counts['A'] - base_counts['T']) / (base_counts['A'] + base_counts['T']) if (base_counts['A'] + base_counts['T']) > 0 else 0
    
    # Detección de patrones repetitivos
    repeat_patterns = detect_repeat_patterns(sequence)
    
    return {
        'organism_id': organism_id,
        'sequence_length': len(sequence),
        'base_counts': base_counts,
        'frequencies': frequencies,
        'dinucleotides': dinucleotides,
        'trinucleotides': trinucleotides,
        'gc_content': gc_content,
        'entropy': entropy,
        'gc_skew': gc_skew,
        'at_skew': at_skew,
        'repeat_patterns': repeat_patterns,
        'complexity_score': entropy * gc_content / 50,
        'adenine_freq': frequencies['A'],
        'thymine_freq': frequencies['T'],
        'guanine_freq': frequencies['G'],
        'cytosine_freq': frequencies['C']
    }

def detect_repeat_patterns(sequence: str, min_length: int = 3, max_length: int = 20) -> Dict:
    """Detecta patrones de repetición en la secuencia"""
    patterns = {}
    
    for length in range(min_length, min(max_length + 1, len(sequence) // 2)):
        for i in range(len(sequence) - length + 1):
            pattern = sequence[i:i+length]
            if all(b in 'ATCG' for b in pattern):
                count = sequence.count(pattern)
                if count > 1:
                    patterns[pattern] = count
    
    return patterns

# ============================================================================
# CLASIFICACIÓN TAXONÓMICA
# ============================================================================

def determine_taxonomic_category(species_name: str, description: str) -> str:
    """Determina la categoría taxonómica para selección de paleta y patrón"""
    name_lower = species_name.lower()
    desc_lower = description.lower()
    
    taxonomic_patterns = {
        'mammal': ['panthera', 'canis', 'felis', 'homo', 'bos', 'sus', 'equus', 'ursus', 'macaca', 'rattus'],
        'aquatic': ['balaenoptera', 'tursiops', 'salmo', 'thunnus', 'octopus', 'cancer', 'hippocampus'],
        'avian': ['aquila', 'bubo', 'aptenodytes', 'falco', 'corvus', 'passer', 'gallus'],
        'reptile': ['python', 'crocodylus', 'iguana', 'gecko', 'chelonia', 'vipera'],
        'arthropod': ['drosophila', 'apis', 'theraphosa', 'latrodectus', 'aedes', 'tribolium'],
        'plant': ['arabidopsis', 'oryza', 'triticum', 'zea', 'solanum', 'rosa', 'quercus']
    }
    
    for category, patterns in taxonomic_patterns.items():
        if any(pattern in name_lower for pattern in patterns):
            return category
    
    return 'general'

def get_taxonomic_palette(category: str) -> Dict:
    """Obtiene paleta de colores específica por categoría taxonómica"""
    return TAXONOMIC_COLOR_PALETTES.get(category, TAXONOMIC_COLOR_PALETTES['mammal'])

# ============================================================================
# GENERACIÓN DE PATRONES VISUALES
# ============================================================================

def create_mammalian_pattern(n_points: int, palette: Dict, genetic_profile: Dict) -> List[go.Scatter]:
    """Patrón cálido y orgánico para mamíferos"""
    traces = []
    golden_ratio = 1.618033988749
    
    for layer in range(5):
        angles = np.linspace(0, 8 * np.pi, n_points // 5)
        r = np.sqrt(angles) * 0.1 * (layer + 1)
        x = r * np.cos(angles * golden_ratio) * (1 + 0.1 * np.sin(angles * 3))
        y = r * np.sin(angles * golden_ratio) * (1 + 0.1 * np.cos(angles * 3))
        
        layer_color = palette['primary'][layer % len(palette['primary'])]
        
        traces.append(go.Scatter(
            x=x, y=y, mode='markers',
            marker=dict(
                size=np.random.uniform(2, 8, len(x)),
                color=layer_color,
                opacity=0.7,
                line=dict(color=palette['secondary'][0], width=0.5)
            ),
            showlegend=False
        ))
    
    # Conexiones familiares
    for i in range(20):
        x_line = np.random.uniform(-0.8, 0.8, 2)
        y_line = np.random.uniform(-0.8, 0.8, 2)
        traces.append(go.Scatter(
            x=x_line, y=y_line, mode='lines',
            line=dict(color=palette['accent'][2], width=1, dash='dot'),
            showlegend=False
        ))
    
    return traces

def create_aquatic_pattern(n_points: int, palette: Dict, genetic_profile: Dict) -> List[go.Scatter]:
    """Patrón fluido para especies acuáticas"""
    traces = []
    
    for wave in range(7):
        t = np.linspace(0, 4 * np.pi, max(10, n_points // 7))
        amplitude = 0.6 - wave * 0.08
        frequency = 2 + wave * 0.5
        
        x = t / (2 * np.pi) - 1
        y = amplitude * np.sin(frequency * t) * np.exp(-0.1 * wave * t)
        
        flow_x = x + 0.1 * np.sin(t * 1.5)
        flow_y = y + 0.05 * np.cos(t * 2.3)
        
        color_cycle = wave % len(palette['primary'])
        
        traces.append(go.Scatter(
            x=flow_x, y=flow_y, mode='lines+markers',
            line=dict(color=palette['primary'][color_cycle], width=3),
            marker=dict(
                size=4, color=palette['secondary'][color_cycle],
                opacity=0.8, symbol='circle'
            ),
            showlegend=False
        ))
    
    return traces

# ============================================================================
# SISTEMA DE ANIMACIÓN AVANZADO
# ============================================================================

def determine_animation_type(organism_name: str, genetic_profile: Dict) -> str:
    """Determina tipo de animación basado en organismo y perfil genético"""
    name_lower = organism_name.lower()
    gc_content = genetic_profile.get('gc_content', 50)
    sequence_length = genetic_profile.get('sequence_length', 1000)
    
    if any(word in name_lower for word in ['dolphin', 'whale', 'fish', 'shark', 'octopus', 'pulpo']):
        return 'aquatic_flow'
    elif any(word in name_lower for word in ['lion', 'tiger', 'wolf', 'bear', 'jaguar', 'lobo']):
        return 'heartbeat_mammal'
    elif any(word in name_lower for word in ['snake', 'python', 'serpiente']):
        return 'spiral_serpent'
    elif any(word in name_lower for word in ['spider', 'ant', 'bee', 'araña']):
        return 'neural_web'
    elif gc_content > 65 and sequence_length > 50000:
        return 'helix_rotation'
    else:
        return 'cosmos_stellar'

def create_dna_helix_animation(progress: float, genetic_profile: Dict) -> List[go.Scatter]:
    """Animación de doble hélice basada en ADN complejo"""
    traces = []
    
    gc_ratio = genetic_profile.get('gc_content', 50) / 100
    rotation_speed = 1 + gc_ratio
    helix_density = int(20 + genetic_profile.get('entropy', 0.5) * 30)
    
    angle_offset = progress * 4 * np.pi * rotation_speed
    
    for strand in range(2):
        t = np.linspace(0, 6 * np.pi, helix_density)
        radius = 0.25 + strand * 0.1
        
        x = radius * np.cos(t + angle_offset + strand * np.pi)
        y = t / (3 * np.pi) - 1
        z = radius * np.sin(t + angle_offset + strand * np.pi)
        
        rotation_angle = progress * 2 * np.pi
        x_proj = x * np.cos(rotation_angle) - z * np.sin(rotation_angle)
        y_proj = y
        
        color = 'rgba(50, 150, 255, 0.8)' if strand == 0 else 'rgba(255, 100, 50, 0.8)'
        
        traces.append(go.Scatter(
            x=x_proj, y=y_proj, mode='lines+markers',
            line=dict(color=color, width=3),
            marker=dict(size=3, color=color),
            showlegend=False, hoverinfo='skip'
        ))
    
    return traces

def create_heartbeat_animation(progress: float, genetic_profile: Dict) -> List[go.Scatter]:
    """Animación de latido para mamíferos"""
    traces = []
    
    sequence_length = genetic_profile.get('sequence_length', 10000)
    heartbeat_frequency = 6 if sequence_length < 50000 else 4
    
    pulse_phase = progress * heartbeat_frequency * 2 * np.pi
    pulse_intensity = 1 + 0.6 * np.sin(pulse_phase)
    
    for ring in range(5):
        theta = np.linspace(0, 2 * np.pi, 80)
        base_radius = 0.15 + ring * 0.12
        radius = base_radius * pulse_intensity * (1 - ring * 0.08)
        
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        
        red_intensity = 255 - ring * 30
        opacity = (0.8 - ring * 0.15) * (0.5 + 0.5 * np.sin(pulse_phase))
        opacity = max(0.1, min(1.0, opacity))
        
        color = f'rgba({red_intensity}, {100 + ring * 20}, 50, {opacity})'
        
        traces.append(go.Scatter(
            x=x, y=y, mode='lines',
            line=dict(color=color, width=max(1, 3 + ring - 2 * np.sin(pulse_phase))),
            showlegend=False, hoverinfo='skip'
        ))
    
    return traces

# ============================================================================
# MOTOR DE VISUALIZACIÓN PRINCIPAL
# ============================================================================

def create_advanced_visualization(sequence: str, genetic_profile: Dict, category: str, palette: Dict) -> go.Figure:
    """Crea visualización estéticamente rica basada en complejidad genética"""
    fig = go.Figure()
    
    sequence_length = len(sequence)
    complexity_score = genetic_profile.get('entropy', 0) * genetic_profile.get('gc_content', 50) / 50
    n_base_points = min(2000, sequence_length // 10)
    
    # Seleccionar patrón por categoría
    pattern_functions = {
        'mammal': create_mammalian_pattern,
        'aquatic': create_aquatic_pattern,
        # Añadir más patrones según necesidad
    }
    
    pattern_func = pattern_functions.get(category, create_mammalian_pattern)
    pattern_traces = pattern_func(n_base_points, palette, genetic_profile)
    
    for trace in pattern_traces:
        fig.add_trace(trace)
    
    # Configurar layout
    fig.update_layout(
        title=dict(
            text=f"🧬 Genoma Artístico - {genetic_profile.get('organism_id', 'Especie Desconocida')}",
            font=dict(size=20, color=palette['accent'][0]),
            x=0.5
        ),
        plot_bgcolor='rgba(5,5,5,1)',
        paper_bgcolor='rgba(5,5,5,1)',
        showlegend=False,
        xaxis=dict(visible=False, range=[-1.2, 1.2]),
        yaxis=dict(visible=False, range=[-1.2, 1.2]),
        height=700
    )
    
    return fig

def create_animated_visualization(fig_original: go.Figure, genetic_profile: Dict, organism_name: str) -> go.Figure:
    """Crea animaciones loop estilo GIF basadas en patrones de ADN"""
    original_traces = list(fig_original.data)
    animation_type = determine_animation_type(organism_name, genetic_profile)
    
    frames = []
    total_frames = 90
    
    for frame_num in range(total_frames):
        frame_data = []
        progress = frame_num / total_frames
        
        # Conservar arte base con transparencia reducida
        for trace in original_traces:
            new_trace = go.Scatter(
                x=trace.x if hasattr(trace, 'x') else [],
                y=trace.y if hasattr(trace, 'y') else [],
                mode=trace.mode if hasattr(trace, 'mode') else 'markers',
                marker=dict(
                    size=trace.marker.size if hasattr(trace, 'marker') and hasattr(trace.marker, 'size') else 5,
                    color=trace.marker.color if hasattr(trace, 'marker') and hasattr(trace.marker, 'color') else '#00ff88',
                    opacity=0.4
                ),
                showlegend=False
            )
            frame_data.append(new_trace)
        
        # Añadir animación específica
        if animation_type == 'helix_rotation':
            frame_data.extend(create_dna_helix_animation(progress, genetic_profile))
        elif animation_type == 'heartbeat_mammal':
            frame_data.extend(create_heartbeat_animation(progress, genetic_profile))
        
        frames.append(go.Frame(data=frame_data, name=str(frame_num)))
    
    # Crear figura animada
    animated_fig = go.Figure(
        data=frames[0].data if frames else [],
        frames=frames
    )
    
    # Configurar controles
    animated_fig.update_layout(
        title=f"🧬 {organism_name} - Genoma Vivo en Movimiento",
        template="plotly_dark",
        plot_bgcolor='rgba(5,10,15,1)',
        paper_bgcolor='rgba(5,10,15,1)',
        height=600,
        updatemenus=[{
            "type": "buttons",
            "showactive": False,
            "x": 0.1,
            "y": 0.02,
            "buttons": [
                {
                    "label": "▶️ Loop",
                    "method": "animate",
                    "args": [None, {
                        "frame": {"duration": 80, "redraw": True},
                        "fromcurrent": True,
                        "transition": {"duration": 40}
                    }]
                },
                {
                    "label": "⏸️ Pause",
                    "method": "animate",
                    "args": [[None], {
                        "frame": {"duration": 0, "redraw": False},
                        "mode": "immediate"
                    }]
                }
            ]
        }]
    )
    
    return animated_fig

# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

def main():
    """Interfaz principal del generador de arte genético"""
    
    # Título y descripción
    st.title("🧬 DNA Art Generator")
    st.markdown("Convierte secuencias genéticas reales en arte único mediante análisis bioinformático")
    
    # Búsqueda de animales
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🎯 Generador de Arte Genético")
        animal_input = st.text_input("Nombre del animal:", placeholder="Ej: lobo, delfín, tigre...")
    
    with col2:
        st.markdown("### ℹ️ Información")
        st.info("Ingresa el nombre común de un animal para generar arte único basado en su ADN real.")
    
    if animal_input:
        try:
            # Inicializar motor de búsqueda
            search_engine = AnimalSearchEngine()
            
            # Buscar especies
            results = search_engine.search_comprehensive(animal_input)
            
            if results:
                selected_result = results[0]
                organism_name = selected_result['scientific_name']
                
                st.success(f"Especie encontrada: {organism_name}")
                
                # Obtener secuencia
                with st.spinner("Obteniendo secuencia genética..."):
                    seq_record = fetch_dna_sequence(organism_name)
                
                # Analizar perfil genético
                sequence = str(seq_record.seq).upper()
                genetic_profile = analyze_genetic_profile(sequence, seq_record.id)
                
                if genetic_profile:
                    # Determinar categoría y paleta
                    category = determine_taxonomic_category(organism_name, seq_record.description)
                    palette = get_taxonomic_palette(category)
                    
                    # Generar visualización
                    with st.spinner("Generando arte genético..."):
                        fig = create_advanced_visualization(sequence, genetic_profile, category, palette)
                    
                    # Mostrar arte estático
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Generar animación
                    with st.spinner("Creando animación..."):
                        animated_fig = create_animated_visualization(fig, genetic_profile, organism_name)
                    
                    # Mostrar arte animado
                    st.markdown("### 🎨 Arte Genético Animado")
                    st.plotly_chart(animated_fig, use_container_width=True)
                    
                    # Mostrar estadísticas
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Longitud", f"{genetic_profile['sequence_length']:,} bp")
                    with col2:
                        st.metric("GC Content", f"{genetic_profile['gc_content']:.1f}%")
                    with col3:
                        st.metric("Entropía", f"{genetic_profile['entropy']:.3f}")
                    with col4:
                        st.metric("Categoría", category.title())
                
                else:
                    st.error("No se pudo analizar el perfil genético")
            else:
                st.error("No se encontró información para esta especie")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()