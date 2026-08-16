"""
DNA Art Generator - Generador de Arte Genético
Convierte secuencias genéticas reales en arte único mediante análisis bioinformático avanzado.
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
from alphafold_engine import create_alphafold_biomorphic_3d_art
from multi_skill_engine import create_multi_skill_masterpiece_art
from deterministic_nft_engine import create_deterministic_nft_figure, generate_deterministic_svg, select_fragment
from protocol.engine import GeneticFramesProtocol
from protocol.agent_sdk import GeneticFramesAgentSDK
from protocol.species_pool import SPECIES_POOL_V1, RarityTier
from protocol.verifier import ProtocolVerifier
from agents.swarm_runner import AgentSwarmEngine
import sonification_core

import os
import scipy.io.wavfile as wavfile
import scipy.signal as signal


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
    try:
        create_tables()
    except Exception:
        pass

if 'protocol' not in st.session_state:
    st.session_state.protocol = GeneticFramesProtocol()
    st.session_state.protocol.economy.mint_gf("0xAgentA_Collector", 20.0)
    st.session_state.protocol.economy.mint_gf("0xAgentB_Trader", 30.0)


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
    
    # Entropía de Shannon para diferentes niveles
    entropy_mono = -sum(f * math.log2(f) for f in frequencies.values() if f > 0)
    
    dinuc_freq = {k: v/len(sequence) for k, v in dinucleotides.items()}
    entropy_di = -sum(f * math.log2(f) for f in dinuc_freq.values() if f > 0)
    
    # Contenido GC y análisis de ventanas
    gc_content = (base_counts['G'] + base_counts['C']) / total_bases * 100
    
    # Complejidad genética multidimensional
    complexity_score = entropy_mono * gc_content / 200
    
    return {
        'organism_id': organism_id,
        'sequence_length': len(sequence),
        'base_counts': base_counts,
        'frequencies': frequencies,
        'dinucleotides': dinucleotides,
        'trinucleotides': trinucleotides,
        'repeat_patterns': repeat_patterns,
        'gc_content': gc_content,
        'entropy_mono': entropy_mono,
        'entropy_di': entropy_di,
        'complexity_score': complexity_score,
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

# ============================================================================
# GENERADOR DE ARTE GENÉTICO UNIVERSAL
# ============================================================================

def create_genetic_art(sequence: str, genetic_profile: Dict, category: str, palette: Dict) -> go.Figure:
    """
    Algoritmo base universal para generar arte genético de cualquier animal
    Procesa ADN y crea representaciones visuales únicas basadas en características genéticas
    """
    fig = go.Figure()
    organism_name = genetic_profile.get('organism_id', 'Unknown')
    
    # Extraer parámetros genéticos universales
    gc_content = genetic_profile.get('gc_content', 50)
    entropy_mono = genetic_profile.get('entropy_mono', 1.5)
    complexity_score = genetic_profile.get('complexity_score', 0.5)
    sequence_length = genetic_profile.get('sequence_length', 1000)
    
    # Normalizar parámetros para uso visual
    gc_normalized = gc_content / 100  # 0-1
    entropy_norm = entropy_mono / 2.0  # 0-1 aproximadamente
    complexity_norm = min(1.0, complexity_score)
    
    n_points = min(2000, sequence_length // 10)
    
    # ALGORITMO BASE: Generar estructura principal
    if gc_content < 35:
        # Bajo GC: Estructuras más lineales y abiertas
        structure = create_linear_structure(n_points, complexity_norm)
    elif gc_content > 65:
        # Alto GC: Estructuras más compactas y circulares
        structure = create_circular_structure(n_points, complexity_norm)
    else:
        # GC medio: Estructuras espirales balanceadas
        structure = create_spiral_structure(n_points, complexity_norm)
    
    # Crear estructura principal
    main_trace = go.Scatter(
        x=structure['x'],
        y=structure['y'],
        mode='markers+lines',
        marker=dict(
            size=structure['sizes'],
            color=structure['colors'],
            colorscale=[[0, palette['primary'][0]], [1, palette['secondary'][0]]],
            opacity=0.8,
            line=dict(width=1, color='white')
        ),
        line=dict(
            color=palette['primary'][0],
            width=2 + complexity_norm * 3
        ),
        showlegend=False
    )
    fig.add_trace(main_trace)
    
    # Añadir elementos basados en dinucleótidos
    dinucleotides = genetic_profile.get('dinucleotides', {})
    if dinucleotides:
        sorted_dinucs = sorted(dinucleotides.items(), key=lambda x: x[1], reverse=True)[:8]
        
        for i, (dinuc, frequency) in enumerate(sorted_dinucs):
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
            
            size = 8 + 12 * (frequency / max(dinucleotides.values()))
            
            fig.add_trace(go.Scatter(
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

# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

def main():
    """Interfaz principal del generador de arte genético universal"""
    
    st.title("🧬 DNA Art Generator Universal")
    st.markdown("**Algoritmo base para generar arte genético de cualquier animal basado en secuencias de ADN reales**")
    
    # Tabs principales
    tab0, tab1, tab2, tab3 = st.tabs(["🏛️ Protocolo & Agentes", "🎨 Generador Universal", "📊 Algoritmo GFDP v2", "🖼️ Galería"])

    with tab0:
        protocol: GeneticFramesProtocol = st.session_state.protocol
        metrics = protocol.get_protocol_metrics()

        st.markdown("### 🏛️ GeneticFrames: Autonomous Asset Economy for AI Agents")
        st.caption("Protocolo de activos biológicos digitales con costo fijo de emisión (1 GF), azar verificable, GFDP v2 y mercado autónomo P2P.")

        # Protocol Metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Época Activa", f"Epoch {metrics['epoch']}")
        m2.metric("Frames Acuñados", f"{metrics['total_frames_minted']}")
        m3.metric("GF Quemados", f"{metrics['total_gf_burned']:.1f} GF")
        m4.metric("Tesorería (Fee 1.5%)", f"{metrics['treasury_gf_collected']:.4f} GF")
        m5.metric("Órdenes / Trades", f"{metrics['active_listings_count']} / {metrics['trades_count']}")

        st.divider()

        # Agent Wallet Control
        col_agent1, col_agent2, col_agent3 = st.columns([2, 2, 1])
        with col_agent1:
            agent_id = st.selectbox(
                "Identidad del Agente Activo:",
                ["0xAgentA_Collector", "0xAgentB_Trader", "0xAgentC_MarketMaker", "0xCustom_Agent"]
            )
            if agent_id == "0xCustom_Agent":
                custom_id = st.text_input("Ingrese ID de Agente personalizado:", value="0xNewAgent_01")
                agent_id = custom_id.strip()

        agent_sdk = GeneticFramesAgentSDK(protocol, agent_id)
        current_balance = agent_sdk.get_balance()

        with col_agent2:
            st.metric("Saldo Disponible", f"{current_balance:.2f} GF")
        with col_agent3:
            if st.button("💧 Faucet (+10 GF)"):
                agent_sdk.deposit_gf(10.0)
                st.rerun()

        # Sub-tabs for Protocol Operations
        p_tab1, p_tab2, p_tab3, p_tab4, p_tab5 = st.tabs([
            "⚡ Generar Frame (1 GF)",
            "🎒 Mi Inventario",
            "📈 Mercado P2P",
            "🛡️ Auditor Criptográfico",
            "🤖 Simulador Económico"
        ])

        with p_tab1:
            st.markdown("#### ⚡ Evento de Emisión: `GENERATE` (Costo Fijo: 1.0 GF)")
            st.write("El agente paga 1 GF (quemado por el protocolo). El organismo, rareza y rasgos se determinan mediante azar verificable HMAC-SHA256 y datos biológicos reales.")

            gen_col1, gen_col2 = st.columns([1, 2])
            with gen_col1:
                client_salt = st.text_input("Entropía del Agente (Opcional):", value="agent_client_seed_42")
                if st.button("🚀 GENERATE (Pagar 1.0 GF)", type="primary"):
                    if current_balance < 1.0:
                        st.error("❌ Saldo insuficiente en GF. Usa el botón Faucet arriba.")
                    else:
                        try:
                            record = protocol.generate(agent_id=agent_id, client_entropy=client_salt)
                            st.success(f"🎉 ¡Frame #{record.frame_id} acuñado exitosamente!")
                            st.session_state["last_generated_frame"] = record.frame_id
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error en generación: {e}")

            with gen_col2:
                last_fid = st.session_state.get("last_generated_frame")
                if last_fid:
                    frame = protocol.inspect_frame(last_fid)
                    if frame:
                        st.markdown(f"##### 🧬 Último Frame Acuñado: #{frame.frame_id} — {frame.common_name} (*{frame.scientific_name}*)")
                        st.write(f"• **Rareza Protocolo:** `{frame.tier.value}`")
                        st.write(f"• **Genoma Fuente:** `{frame.manifest['genome']['provider']} {frame.manifest['genome']['accession']}`")
                        st.write(f"• **Algorithmic Rarity:** `{frame.manifest['genetic_traits']['algorithmic_rarity_score']} ({frame.manifest['genetic_traits']['algorithmic_rarity_tier']})`")
                        st.image(frame.svg_code, width=320)

        with p_tab2:
            st.markdown("#### 🎒 Inventario de GeneticFrames")
            my_frames = agent_sdk.list_my_frames()
            if not my_frames:
                st.info(f"El agente {agent_id} no posee GeneticFrames actualmente. Genera uno en la pestaña anterior.")
            else:
                for f_data in my_frames:
                    with st.expander(f"Frame #{f_data['frame_id']} — {f_data['common_name']} ({f_data['tier']})", expanded=False):
                        fc1, fc2 = st.columns([1, 1])
                        with fc1:
                            st.write(f"• **Especie:** {f_data['scientific_name']}")
                            st.write(f"• **Creador:** `{f_data['creator_id']}`")
                            st.write(f"• **Propietario:** `{f_data['owner_id']}`")
                            st.write(f"• **Hash Manifiesto:** `{f_data['manifest_sha256'][:24]}...`")
                            
                            # Formulario para listar a la venta
                            with st.form(f"list_form_{f_data['frame_id']}"):
                                list_price = st.number_input("Precio de venta (GF):", min_value=0.5, value=3.0, step=0.5)
                                if st.form_submit_button("🏷️ Publicar en Mercado"):
                                    try:
                                        agent_sdk.create_ask(f_data['frame_id'], list_price)
                                        st.success(f"Frame #{f_data['frame_id']} publicado a {list_price} GF")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(str(e))
                        with fc2:
                            full_f = protocol.inspect_frame(f_data['frame_id'])
                            if full_f:
                                st.image(full_f.svg_code, width=280)

        with p_tab3:
            st.markdown("#### 📈 Mercado P2P Autónomo (Orderbook & Trades)")
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                st.markdown("##### 🏷️ Listados Activos (Asks)")
                active_listings = [l for l in protocol.economy.listings.values() if l.status.value == "active"]
                if not active_listings:
                    st.info("No hay listados activos en el mercado.")
                else:
                    for l in active_listings:
                        frame_info = protocol.inspect_frame(l.frame_id)
                        if frame_info:
                            c1, c2 = st.columns([3, 2])
                            c1.write(f"**Frame #{l.frame_id}** ({frame_info.common_name} - {frame_info.tier.value})\nVendedor: `{l.seller_id}`")
                            if l.seller_id != agent_id:
                                if c2.button(f"Comprar por {l.price_gf} GF", key=f"buy_{l.listing_id}"):
                                    try:
                                        agent_sdk.buy_listing(l.listing_id)
                                        st.success("¡Compra ejecutada exitosamente!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(str(e))
                            else:
                                if c2.button("Cancelar", key=f"cancel_{l.listing_id}"):
                                    agent_sdk.cancel_ask(l.listing_id)
                                    st.rerun()

            with m_col2:
                st.markdown("##### 🏆 Seguimiento de Colecciones Taxonómicas")
                for family_name in ["Felidae", "Delphinidae", "Balaenopteridae"]:
                    prog = agent_sdk.check_collection_progress(family_name)
                    st.write(f"**Colección {family_name}:** {prog['owned_species']}/{prog['total_species']} especies ({prog['percentage']}%)")
                    st.progress(prog['percentage'] / 100.0)

        with p_tab4:
            st.markdown("#### 🛡️ Auditor Criptográfico Independiente")
            st.write("Verifica matemáticamente que un GeneticFrame no fue manipulado, que su secuencia proviene de la fuente biológica y que el SVG es 100% determinista.")
            
            audit_fid = st.number_input("ID del Frame a Auditar:", min_value=1, value=1, step=1)
            if st.button("🔍 Auditar Frame"):
                audit_res = protocol.verify_frame(audit_fid)
                if audit_res.is_valid:
                    st.success(f"✅ Frame #{audit_fid} es 100% AUTÉNTICO y VERIFICADO")
                else:
                    st.error(f"❌ Falló la verificación de Frame #{audit_fid}")
                
                col_a1, col_a2 = st.columns(2)
                col_a1.write(f"• **Integridad del Manifiesto:** `{audit_res.manifest_integrity}`")
                col_a1.write(f"• **Hash de Secuencia Biológica:** `{audit_res.sequence_matches_hash}`")
                col_a1.write(f"• **Checksum del Fragmento:** `{audit_res.fragment_matches_hash}`")
                col_a2.write(f"• **Reproducibilidad SVG GFDP v2:** `{audit_res.artifact_reproducible}`")
                col_a2.write(f"• **Prueba de Azar Verificable:** `{audit_res.randomness_proof_valid}`")

        with p_tab5:
            st.markdown("#### 🤖 Enjambre de Agentes Autónomos (Agent Swarm)")
            st.write("Orquesta y simula un ecosistema multi-agente con 6 bots autónomos con estrategias diferenciadas (*Collector Felidae*, *Collector Cetacea*, *Hunter Genesis*, *Hunter Value*, *Market Maker* y *Arbitrageur*).")

            s_col1, s_col2, s_col3 = st.columns([1, 1, 2])
            with s_col1:
                rounds_to_run = st.slider("Rondas a Simular:", min_value=1, max_value=15, value=5)
            with s_col2:
                run_swarm_btn = st.button("🚀 Lanzar Simulación de Enjambre", type="primary")

            if 'swarm_engine' not in st.session_state:
                st.session_state.swarm_engine = AgentSwarmEngine(protocol)
                st.session_state.swarm_engine.initialize_default_swarm()

            swarm: AgentSwarmEngine = st.session_state.swarm_engine

            if run_swarm_btn:
                with st.spinner(f"Ejecutando {rounds_to_run} rondas autónomas con {len(swarm.agents)} agentes..."):
                    metrics = swarm.run_simulation(rounds_to_run)
                    st.session_state.last_swarm_metrics = metrics
                    st.success(f"✅ ¡Simulación completada! {metrics.total_actions} acciones autónomas ejecutadas en {metrics.total_rounds} rondas.")
                    st.rerun()

            last_m = st.session_state.get("last_swarm_metrics")
            if last_m:
                st.divider()
                st.markdown("##### 📊 Telemetría y Métricas de Equilibrio del Enjambre")
                sm1, sm2, sm3, sm4 = st.columns(4)
                sm1.metric("Acciones Totales", f"{last_m.total_actions}")
                sm2.metric("Generaciones (GF Burn)", f"{last_m.total_generations}")
                sm3.metric("Trades P2P", f"{last_m.total_trades}")
                sm4.metric("Volumen Negociado", f"{last_m.total_volume_gf:.2f} GF")

                tab_s1, tab_s2, tab_s3 = st.tabs(["🏆 Tabla de Riqueza y Portafolios", "🐆 Carrera de Colecciones", "⚡ Feed de Acciones"])
                with tab_s1:
                    st.dataframe(last_m.wealth_leaderboard, use_container_width=True)
                with tab_s2:
                    st.dataframe(last_m.collections_leaderboard, use_container_width=True)
                with tab_s3:
                    recent_actions = [a.to_dict() for a in reversed(swarm.all_action_logs[-25:])]
                    st.dataframe(recent_actions, use_container_width=True)


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
            - **Dinucleótidos**: Elementos hexagonales únicos
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
                        
                        st.markdown("### 🎨 Selector de Algoritmo Generativo")
                        art_style = st.radio(
                            "Elija el motor de renderizado visual:",
                            [
                                "💎 Certificado NFT Determinista & SVG (6 Principios Blockchain)",
                                "👑 Arte Maestro Tri-Skill 3D (AlphaFold + InterPro + UCSC)",
                                "🌌 Escultura Biomórfica 3D (AlphaFold DB & PDB)",
                                "🌀 Arte Genético 2D (Fórmula de Frecuencia/Entropía)"
                            ],
                            horizontal=True
                        )
                        
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
                        
                        # Variable para almacenar código SVG vectorial si aplica
                        current_svg_code = None

                        if "NFT Determinista" in art_style:
                            with st.spinner("💎 Calculando Hash SHA-256, Rareza Genética y Vectorial SVG Determinista..."):
                                fig, current_svg_code, nft_meta = create_deterministic_nft_figure(organism_name, sequence, genetic_profile, palette)
                            
                            st.markdown("### 💎 Certificado NFT Determinista (Reproducible & Certificado)")
                            
                            nft_col1, nft_col2, nft_col3, nft_col4 = st.columns(4)
                            with nft_col1:
                                st.metric("1. Reproducibilidad", "100% SHA-256")
                            with nft_col2:
                                st.metric("2. Rareza Codificada", f"{nft_meta['rarity']['tier']}")
                            with nft_col3:
                                st.metric("Puntaje Rareza", f"{nft_meta['rarity']['score']} / 100")
                            with nft_col4:
                                st.metric("Ventana ADN Muestreada", f"{nft_meta['fragment']['length']} bp")
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            st.markdown("#### 📜 Código Hash Certificador Blockchain (SHA-256)")
                            st.code(f"Manifest SHA-256: {nft_meta['manifest_sha256']}\nSecuencia SHA-256: {nft_meta['sequence']['sha256']}\nFragment SHA-256: {nft_meta['fragment']['sha256']}\nSeed (Prefix): {nft_meta['fragment']['sha256'][:16]}", language="yaml")

                        elif "Tri-Skill" in art_style:
                            with st.spinner("🧬 Ejecutando Tri-Skill Engine (AlphaFold 3D + InterPro Dominios + UCSC Conservación)..."):
                                fig, multi_metrics = create_multi_skill_masterpiece_art(organism_name, genetic_profile, palette)
                            
                            st.markdown("### 👑 Obra Maestra Tri-Skill 3D (AlphaFold + InterPro + UCSC)")
                            
                            ms_col1, ms_col2, ms_col3, ms_col4 = st.columns(4)
                            with ms_col1:
                                st.metric("1. AlphaFold pLDDT", f"{multi_metrics['avg_plddt']:.1f} / 100")
                            with ms_col2:
                                st.metric("2. InterPro Dominios", f"{multi_metrics['domains_count']} detectados")
                            with ms_col3:
                                st.metric("3. UCSC Conservación", f"{multi_metrics['conserved_ratio']:.1f}% sitios (phyloP)")
                            with ms_col4:
                                st.metric("UniProt Accession", f"{multi_metrics['uniprot_id']}")
                            
                            st.plotly_chart(fig, use_container_width=True)

                        elif "AlphaFold" in art_style:
                            with st.spinner("🧬 Consultando estructura 3D en AlphaFold DB y calculando puntuaciones pLDDT..."):
                                fig, af_metrics = create_alphafold_biomorphic_3d_art(organism_name, genetic_profile, palette)
                            
                            st.markdown("### 🌌 Escultura Biomórfica 3D (AlphaFold DB)")
                            
                            af_col1, af_col2, af_col3, af_col4 = st.columns(4)
                            with af_col1:
                                st.metric("UniProt ID", f"{af_metrics['uniprot_id']}")
                            with af_col2:
                                st.metric("pLDDT Promedio", f"{af_metrics['avg_plddt']:.1f} / 100")
                            with af_col3:
                                st.metric("Regiones Rígidas (≥70)", f"{af_metrics['high_confidence_ratio']:.1f}%")
                            with af_col4:
                                st.metric("Residuos Analizados", f"{af_metrics['total_residues']}")
                            
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            with st.spinner("🎨 Ejecutando algoritmo universal 2D..."):
                                fig = create_genetic_art(sequence, genetic_profile, category, palette)
                            
                            st.markdown("### 🌀 Arte Genético 2D Generado")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Guardar en galería
                        gallery_entry = {
                            'name': organism_name,
                            'sequence_type': sequence_type,
                            'figure': fig,
                            'gc': gc_content,
                            'length': genetic_profile['sequence_length'],
                            'complexity': complexity_score
                        }
                        if len(st.session_state.gallery) >= 5:
                            st.session_state.gallery.pop(0)
                        st.session_state.gallery.append(gallery_entry)
                        
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
                            st.write(f"• Patrones repetitivos: {len(genetic_profile.get('repeat_patterns', {}))}")
                        
                        # Opciones de exportación
                        export_col1, export_col2, export_col3 = st.columns(3)
                        
                        with export_col1:
                            st.markdown("### 💾 Exportar Vectorial")
                            if current_svg_code:
                                st.download_button(
                                    label="📥 Descargar SVG Vectorial (IPFS / Web3 Ready)",
                                    data=current_svg_code,
                                    file_name=f"{organism_name.replace(' ', '_').lower()}_nft_dna.svg",
                                    mime="image/svg+xml"
                                )
                            else:
                                svg_out, _ = generate_deterministic_svg(sequence, organism_name, palette)
                                st.download_button(
                                    label="📥 Descargar SVG Vectorial (IPFS / Web3 Ready)",
                                    data=svg_out,
                                    file_name=f"{organism_name.replace(' ', '_').lower()}_dna.svg",
                                    mime="image/svg+xml"
                                )

                        with export_col2:
                            st.markdown("### 🎵 Sonificación Genómica (Rust)")
                            audio_file = f"static/{organism_name.replace(' ', '_').lower()}_sonification.wav"
                            os.makedirs("static", exist_ok=True)
                            
                            if st.button("Generar Pista de Audio"):
                                with st.spinner("Sintetizando audio a nivel de hardware (Rust/Hound)..."):
                                    try:
                                        # Extraer solo la ventana renderizada para evitar 60 mins de audio en genomas enteros
                                        dna_fragment, _ = select_fragment(sequence)
                                        sonification_core.generate_dna_audio(dna_fragment, audio_file, 44100, 200)
                                        
                                        st.audio(audio_file, format="audio/wav")
                                        
                                        # Calcular Espectrograma
                                        sample_rate, samples = wavfile.read(audio_file)
                                        frequencies, times, spectrogram = signal.spectrogram(samples, sample_rate, nperseg=1024)
                                        
                                        # Recortar las frecuencias altas para ver mejor las notas base
                                        freq_mask = frequencies <= 800
                                        frequencies = frequencies[freq_mask]
                                        spectrogram = spectrogram[freq_mask, :]
                                        
                                        fig_spec = go.Figure(data=go.Heatmap(
                                            z=10 * np.log10(spectrogram + 1e-10),
                                            x=times,
                                            y=frequencies,
                                            colorscale='magma',
                                            showscale=False
                                        ))
                                        fig_spec.update_layout(
                                            title="Espectrograma Genómico", 
                                            xaxis_title="Tiempo (s)", 
                                            yaxis_title="Frecuencia (Hz)",
                                            height=250,
                                            margin=dict(l=20, r=20, t=30, b=20),
                                            paper_bgcolor="#020307",
                                            plot_bgcolor="#020307",
                                            font={"color": "white"}
                                        )
                                        st.plotly_chart(fig_spec, use_container_width=True)
                                        
                                        with open(audio_file, "rb") as f:
                                            st.download_button("📥 Descargar WAV", f, file_name=os.path.basename(audio_file), mime="audio/wav")
                                    except Exception as e:
                                        st.error(f"Error generando audio: {e}")
                        
                        with export_col3:
                            st.markdown("### 🔄 Verificación Certificada")
                            st.info("🔒 Los gráficos en modo NFT son 100% deterministas. La misma secuencia siempre producirá exactamente el mismo hash SHA-256 e imagen vectorial.")
                        
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
                                st.write(f"• Purinas: {genetic_profile.get('purine_content', 0):.1f}%")
                                st.write(f"• Pirimidinas: {genetic_profile.get('pyrimidine_content', 0):.1f}%")
                                st.write(f"• Firma genética: {genetic_profile.get('organism_id', 'N/A')}")
                    
                    else:
                        st.error("❌ No se pudo analizar el perfil genético")
                else:
                    st.error("❌ No se encontró información para esta especie")
                    st.info("💡 Intenta con el nombre científico o verifica la ortografía")
                    
            except Exception as e:
                st.error(f"❌ Error en el proceso: {str(e)}")
                st.info("💡 Intenta con otro animal o verifica la conexión")

if __name__ == "__main__":
    main()