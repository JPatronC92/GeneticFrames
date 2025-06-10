import streamlit as st
from Bio import Entrez, SeqIO
from Bio.SeqUtils import gc_fraction
import plotly.express as px
import plotly.graph_objects as go
import io
import os
import numpy as np
import math
import random
from datetime import datetime
import uuid
import json
from database import (
    create_tables, save_dna_sequence, log_search, 
    get_popular_organisms, get_recent_sequences, 
    add_favorite, get_user_favorites, get_database_stats
)
from blockchain_nft import nft_manager
from species_catalog import (
    FEATURED_SPECIES, get_species_info, get_rarity_multiplier,
    get_species_story, suggest_search_terms, is_featured_species
)
from animal_search import animal_search

# Configuración de Entrez con variables de entorno
Entrez.email = os.getenv("ENTREZ_EMAIL")
Entrez.api_key = os.getenv("NCBI_API_KEY")

def limpiar_nombre_cientifico(nombre):
    """Limpia nombre científico removiendo autores y años para búsqueda en NCBI"""
    import re
    # Remover autor y año (ej: "Dynastes grantii Horn, 1870" -> "Dynastes grantii")
    # Patrones comunes: "Autor, YYYY", "Autor YYYY", "(Autor, YYYY)", "(Autor) YYYY"
    patterns = [
        r'\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,?\s+\d{4}.*$',  # Autor, año
        r'\s+\([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,?\s*\d{4}\).*$',  # (Autor, año)
        r'\s+\([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\)\s+\d{4}.*$',  # (Autor) año
        r'\s+[A-Z][a-z]+\s+\d{4}.*$',  # Autor año
    ]
    
    nombre_limpio = nombre.strip()
    for pattern in patterns:
        nombre_limpio = re.sub(pattern, '', nombre_limpio)
    
    return nombre_limpio.strip()

# Cache para evitar repetir búsquedas
@st.cache_data(ttl=3600, show_spinner="Buscando en bases de datos genéticas...")
def obtener_secuencia(organismo):
    """Obtiene secuencia de ADN desde NCBI"""
    try:
        # Limpiar nombre científico antes de la búsqueda
        nombre_limpio = limpiar_nombre_cientifico(organismo)
        
        # Lista de términos de búsqueda a probar en orden de preferencia
        search_terms = [
            f'"{nombre_limpio}"[Organism]',  # Búsqueda exacta por organismo
            f'{nombre_limpio}[Organism]',    # Búsqueda por organismo sin comillas
            f'"{nombre_limpio}" AND complete genome',  # Genoma completo
            f'"{nombre_limpio}" AND mitochondrion',    # Mitocondrial
            f'"{nombre_limpio}" AND 16S',              # ARN ribosomal 16S
            f'"{nombre_limpio}" AND COI',              # Citocromo oxidasa I
            nombre_limpio,                             # Búsqueda general
        ]
        
        for term in search_terms:
            search = Entrez.esearch(db="nucleotide", term=term, retmax=1, idtype="acc")
            record = Entrez.read(search)
            search.close()
            
            if record["IdList"]:
                seq_id = record["IdList"][0]
                fetch = Entrez.efetch(db="nucleotide", id=seq_id, rettype="fasta", retmode="text")
                seq_record = SeqIO.read(fetch, "fasta")
                fetch.close()
                return seq_record
        
        # Si no se encuentra nada, intentar con solo el género
        genus = nombre_limpio.split()[0] if ' ' in nombre_limpio else nombre_limpio
        if genus != nombre_limpio:
            for term_suffix in ['[Organism]', ' AND complete genome', ' AND mitochondrion']:
                search = Entrez.esearch(db="nucleotide", term=f'"{genus}"{term_suffix}', retmax=1, idtype="acc")
                record = Entrez.read(search)
                search.close()
                
                if record["IdList"]:
                    seq_id = record["IdList"][0]
                    fetch = Entrez.efetch(db="nucleotide", id=seq_id, rettype="fasta", retmode="text")
                    seq_record = SeqIO.read(fetch, "fasta")
                    fetch.close()
                    return seq_record
        
        return None
        
    except Exception as e:
        st.error(f"Error al acceder a NCBI: {str(e)}")
        return None

# Mapeo científico de bases a atributos visuales mejorado
BASE_ART_MAP = {
    'A': {'color': '#FF6B6B', 'size': 12, 'symbol': 'circle', 'frequency': 440},     # Adenina - Rojo coral
    'T': {'color': '#4ECDC4', 'size': 10, 'symbol': 'circle', 'frequency': 494},    # Timina - Turquesa
    'C': {'color': '#45B7D1', 'size': 8, 'symbol': 'circle', 'frequency': 523},      # Citosina - Azul cielo
    'G': {'color': '#96CEB4', 'size': 14, 'symbol': 'circle', 'frequency': 587},       # Guanina - Verde menta
    'N': {'color': '#FECA57', 'size': 6, 'symbol': 'circle', 'frequency': 330}            # Desconocido - Amarillo dorado
}

# Paletas de colores por tema
COLOR_THEMES = {
    'scientific': {
        'A': '#E74C3C', 'T': '#3498DB', 'C': '#2ECC71', 'G': '#F39C12', 'N': '#95A5A6'
    },
    'ocean': {
        'A': '#1ABC9C', 'T': '#16A085', 'C': '#2980B9', 'G': '#3498DB', 'N': '#BDC3C7'
    },
    'forest': {
        'A': '#27AE60', 'T': '#2ECC71', 'C': '#229954', 'G': '#58D68D', 'N': '#A9DFBF'
    },
    'sunset': {
        'A': '#E74C3C', 'T': '#E67E22', 'C': '#F39C12', 'G': '#F1C40F', 'N': '#F8C471'
    },
    'cosmic': {
        'A': '#8E44AD', 'T': '#9B59B6', 'C': '#3F51B5', 'G': '#673AB7', 'N': '#B39DDB'
    }
}

def crear_arte_fluido(secuencia, theme='scientific', genetic_seed=None):
    """Crea arte fluido complejo con texturas y gradientes únicos por especie"""
    max_length = min(len(secuencia), 5000)
    sequence_segment = secuencia[:max_length]
    
    colors = COLOR_THEMES[theme]
    base_values = {'A': 1.0, 'T': 1.5, 'C': 2.0, 'G': 2.5, 'N': 0.5}
    
    # Usar semilla genética para parámetros únicos
    if genetic_seed:
        # Semilla única más agresiva para diferenciación extrema
        unique_seed = hash(genetic_seed['repeat_signature'] + genetic_seed['first_bases'] + genetic_seed['last_bases']) % 50000
        np.random.seed(unique_seed)
        random.seed(unique_seed)
        
        # Parámetros dramáticamente diferentes basados en genética
        unique_frequency_base = genetic_seed['dinuc_frequency'] * 0.5 + (unique_seed % 100) / 1000
        complexity_multiplier = genetic_seed['sequence_diversity'] / 2.0 + (unique_seed % 50) / 100
        gc_influence = genetic_seed['gc_ratio'] * 3.0 + genetic_seed['middle_gc']
        
        # Factores de variación extrema por secuencia
        color_shift = (unique_seed % 360) / 360  # Rotación de color única
        pattern_intensity = 0.5 + genetic_seed['dinuc_frequency'] * 2
        layer_count_modifier = (unique_seed % 5) + 2  # 2-6 capas variables
    else:
        unique_frequency_base = 0.05
        complexity_multiplier = 1.0
        gc_influence = 1.0
        color_shift = 0
        pattern_intensity = 1.0
        layer_count_modifier = 3
    
    # Análisis de características genéticas únicas
    gc_content = sequence_segment.count('G') + sequence_segment.count('C')
    at_content = sequence_segment.count('A') + sequence_segment.count('T')
    complexity = len(set(sequence_segment[:100]))  # Diversidad en primeras 100 bases
    
    # Parámetros únicos basados en la secuencia y semilla genética
    primary_frequency = unique_frequency_base + (gc_content / len(sequence_segment)) * 0.1 + unique_frequency_base
    secondary_frequency = 0.02 + (at_content / len(sequence_segment)) * 0.08 + (unique_frequency_base * 0.5)
    amplitude_factor = 15 + complexity * 3 * complexity_multiplier
    
    fig = go.Figure()
    
    # Crear múltiples capas con diferentes texturas
    for layer in range(6):
        x_coords = []
        y_coords = []
        colors_list = []
        sizes = []
        
        step = max(1, len(sequence_segment) // (200 + layer * 50))
        
        for i in range(0, len(sequence_segment), step):
            if i >= len(sequence_segment):
                break
                
            base = sequence_segment[i]
            value = base_values.get(base, 0.5)
            
            # Coordenadas con múltiples armónicos
            x = i * 0.8
            
            # Ondas complejas con interferencia genética única
            genetic_phase = color_shift * np.pi * 2 if genetic_seed else 0
            y_base = (
                np.sin(x * primary_frequency + value + genetic_phase) * amplitude_factor * pattern_intensity +
                np.cos(x * secondary_frequency + value * 2 + genetic_phase * 0.5) * amplitude_factor * 0.6 +
                np.sin(x * 0.01 * complexity_multiplier + value * 3) * amplitude_factor * 0.3 +
                np.cos(x * 0.15 * gc_influence + layer + genetic_phase) * amplitude_factor * 0.2
            )
            
            # Variación por capa
            y = y_base + layer * (30 + complexity * 2)
            
            # Modulación de amplitud basada en patrones locales
            local_pattern = sum(base_values.get(sequence_segment[j], 0) 
                              for j in range(max(0, i-5), min(len(sequence_segment), i+5)))
            amplitude_mod = 1 + (local_pattern / 50) * 0.5
            y *= amplitude_mod
            
            x_coords.append(x)
            y_coords.append(y)
            
            # Colores con gradientes basados en contexto genético
            base_color = colors.get(base, colors['N'])
            
            # Modificar color basado en vecinos genéticos
            if i > 0 and i < len(sequence_segment) - 1:
                prev_base = sequence_segment[i-1]
                next_base = sequence_segment[i+1]
                context_value = (base_values.get(prev_base, 0) + base_values.get(next_base, 0)) / 2
                
                # Interpolación de color basada en contexto
                r = int(base_color[1:3], 16)
                g = int(base_color[3:5], 16)
                b = int(base_color[5:7], 16)
                
                # Ajustar saturación basada en contexto genético
                saturation_factor = 0.7 + (context_value / 5) * 0.3
                r = min(255, int(r * saturation_factor))
                g = min(255, int(g * saturation_factor))
                b = min(255, int(b * saturation_factor))
                
                color_final = f"rgb({r},{g},{b})"
            else:
                color_final = base_color
                
            colors_list.append(color_final)
            sizes.append(max(2, value * 3 + layer))
        
        if len(x_coords) > 1:
            # Líneas principales con grosor variable
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='lines',
                line=dict(
                    color=colors_list[0] if colors_list else colors['A'],
                    width=max(1, 12 - layer * 1.5),
                    shape='spline',
                    smoothing=1.3
                ),
                opacity=0.8 - layer * 0.1,
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Agregar puntos de textura
            if layer < 3:  # Solo en las primeras capas
                scatter_x = x_coords[::max(1, len(x_coords)//30)]
                scatter_y = y_coords[::max(1, len(y_coords)//30)]
                scatter_colors = colors_list[::max(1, len(colors_list)//30)]
                
                fig.add_trace(go.Scatter(
                    x=scatter_x,
                    y=scatter_y,
                    mode='markers',
                    marker=dict(
                        color=scatter_colors,
                        size=[s*2 for s in sizes[::max(1, len(sizes)//30)]],
                        opacity=0.6,
                        symbol='circle'
                    ),
                    showlegend=False,
                    hoverinfo='skip'
                ))
    
    # Agregar espirales de fondo basadas en patrones repetitivos
    spiral_data = detectar_patrones_repetitivos(sequence_segment)
    if spiral_data:
        fig = agregar_espirales_geneticas(fig, spiral_data, colors, complexity)
    
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,1)',
        paper_bgcolor='rgba(0,0,0,1)',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return fig

def detectar_patrones_repetitivos(secuencia):
    """Detecta patrones repetitivos en la secuencia para crear espirales"""
    patrones = {}
    
    # Buscar patrones de diferentes longitudes
    for pattern_length in range(2, 8):
        for i in range(len(secuencia) - pattern_length + 1):
            pattern = secuencia[i:i + pattern_length]
            if pattern in patrones:
                patrones[pattern].append(i)
            else:
                patrones[pattern] = [i]
    
    # Filtrar patrones que aparecen múltiples veces
    significant_patterns = {k: v for k, v in patrones.items() if len(v) >= 3}
    
    return significant_patterns

def agregar_espirales_geneticas(fig, spiral_data, colors, complexity):
    """Agrega espirales de fondo basadas en patrones genéticos"""
    base_values = {'A': 1.0, 'T': 1.5, 'C': 2.0, 'G': 2.5, 'N': 0.5}
    
    for pattern, positions in list(spiral_data.items())[:3]:  # Máximo 3 espirales
        if len(positions) < 3:
            continue
            
        # Calcular parámetros de espiral basados en el patrón
        pattern_value = sum(base_values.get(base, 0.5) for base in pattern) / len(pattern)
        spiral_radius = 100 + pattern_value * 20
        spiral_turns = 2 + len(pattern) * 0.5
        
        # Generar puntos de espiral
        angles = np.linspace(0, spiral_turns * 2 * math.pi, len(positions) * 10)
        radii = np.linspace(spiral_radius * 0.3, spiral_radius, len(angles))
        
        x_spiral = radii * np.cos(angles) + positions[0] * 2
        y_spiral = radii * np.sin(angles) + complexity * 10
        
        # Color basado en el patrón dominante
        dominant_base = max(set(pattern), key=pattern.count)
        spiral_color = colors.get(dominant_base, colors['N'])
        
        fig.add_trace(go.Scatter(
            x=x_spiral,
            y=y_spiral,
            mode='lines',
            line=dict(
                color=spiral_color,
                width=2,
                dash='dot'
            ),
            opacity=0.4,
            showlegend=False,
            hoverinfo='skip'
        ))
    
    return fig

def crear_mandala_genetico(secuencia, theme='scientific', genetic_seed=None):
    """Crea un mandala artístico complejo con texturas fractales"""
    max_length = min(len(secuencia), 4000)
    sequence_segment = secuencia[:max_length]
    
    colors = COLOR_THEMES[theme]
    base_values = {'A': 1.2, 'T': 1.8, 'C': 2.4, 'G': 3.0, 'N': 0.6}
    
    # Usar semilla genética para variaciones únicas extremas
    if genetic_seed:
        unique_seed = hash(genetic_seed['repeat_signature'] + genetic_seed['first_bases']) % 50000
        np.random.seed(unique_seed)
        random.seed(unique_seed)
        
        ring_variation = genetic_seed['dinuc_frequency'] * 20 + (unique_seed % 100) / 50
        size_multiplier = 1 + genetic_seed['sequence_diversity'] / 5 + (unique_seed % 50) / 100
        mandala_rotation = (unique_seed % 360) / 360 * 2 * np.pi
        ring_count_modifier = (unique_seed % 4) + 3  # 3-6 anillos variables
        pattern_complexity = 0.5 + genetic_seed['middle_gc'] * 2
    else:
        ring_variation = 1.0
        size_multiplier = 1.0
        mandala_rotation = 0
        ring_count_modifier = 5
        pattern_complexity = 1.0
    
    # Análisis genético para parámetros únicos
    gc_ratio = (sequence_segment.count('G') + sequence_segment.count('C')) / len(sequence_segment)
    complexity_factor = len(set(sequence_segment[:200])) / 4  # Diversidad normalizada
    repeat_density = calcular_densidad_repeticiones(sequence_segment)
    
    fig = go.Figure()
    
    # Crear múltiples capas de anillos con diferentes patrones
    num_rings = max(6, int(8 + complexity_factor * 4))
    
    for ring in range(num_rings):
        # Aplicar rotación genética única por anillo
        ring_rotation = mandala_rotation + ring * (mandala_rotation / num_rings)
        ring_data = generar_anillo_fractal(
            sequence_segment, ring, colors, base_values, 
            gc_ratio, complexity_factor, repeat_density, 
            ring_rotation, pattern_complexity
        )
        
        if ring_data:
            # Puntos orgánicos del anillo (solo círculos)
            fig.add_trace(go.Scatter(
                x=ring_data['x_coords'],
                y=ring_data['y_coords'],
                mode='markers',
                marker=dict(
                    color=ring_data['colors'],
                    size=ring_data['sizes'],
                    opacity=ring_data['opacity'],
                    symbol='circle',
                    line=dict(width=1, color='rgba(255,255,255,0.3)')
                ),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Líneas de conexión orgánicas
            if len(ring_data['x_coords']) > 3:
                fig.add_trace(go.Scatter(
                    x=ring_data['x_smooth'],
                    y=ring_data['y_smooth'],
                    mode='lines',
                    line=dict(
                        color=ring_data['line_color'],
                        width=ring_data['line_width'],
                        shape='spline',
                        smoothing=1.2
                    ),
                    opacity=ring_data['line_opacity'],
                    showlegend=False,
                    hoverinfo='skip'
                ))
            
            # Patrones fractales secundarios
            if ring % 2 == 0 and ring < 6:  # Solo en anillos pares
                fractal_data = crear_patron_fractal(
                    ring_data, sequence_segment[ring*100:(ring+1)*100], colors
                )
                if fractal_data:
                    fig.add_trace(go.Scatter(
                        x=fractal_data['x'],
                        y=fractal_data['y'],
                        mode='markers',
                        marker=dict(
                            color=fractal_data['colors'],
                            size=fractal_data['sizes'],
                            opacity=0.4,
                            symbol='circle'
                        ),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
    
    # Agregar centro artístico basado en secuencia inicial
    centro_data = crear_centro_mandala(sequence_segment[:50], colors, complexity_factor)
    if centro_data:
        fig.add_trace(go.Scatter(
            x=centro_data['x'],
            y=centro_data['y'],
            mode='markers',
            marker=dict(
                color=centro_data['colors'],
                size=centro_data['sizes'],
                opacity=0.9,
                symbol='circle',
                line=dict(width=2, color='white')
            ),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Agregar rayos genéticos emanando del centro
    rayos_data = crear_rayos_geneticos(sequence_segment, colors, gc_ratio)
    for rayo in rayos_data:
        fig.add_trace(go.Scatter(
            x=rayo['x'],
            y=rayo['y'],
            mode='lines',
            line=dict(
                color=rayo['color'],
                width=rayo['width'],
                dash='dash'
            ),
            opacity=0.3,
            showlegend=False,
            hoverinfo='skip'
        ))
    
    max_radius = 150 + complexity_factor * 50
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,1)',
        paper_bgcolor='rgba(0,0,0,1)',
        xaxis=dict(visible=False, range=[-max_radius, max_radius]),
        yaxis=dict(visible=False, range=[-max_radius, max_radius]),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return fig

def calcular_densidad_repeticiones(secuencia):
    """Calcula la densidad de repeticiones en la secuencia"""
    repeticiones = 0
    for i in range(len(secuencia) - 3):
        triplete = secuencia[i:i+3]
        if secuencia.count(triplete) > 1:
            repeticiones += 1
    return repeticiones / len(secuencia) if len(secuencia) > 0 else 0

def generar_anillo_fractal(secuencia, ring, colors, base_values, gc_ratio, complexity_factor, repeat_density, ring_rotation=0, pattern_complexity=1.0):
    """Genera un anillo con patrones fractales únicos"""
    ring_radius = 20 + ring * (15 + complexity_factor * 5)
    points_per_ring = max(12, int(60 + ring * 8 - repeat_density * 20))
    
    if ring * 50 >= len(secuencia):
        return None
    
    segment = secuencia[ring * 50:(ring + 1) * 50]
    if not segment:
        return None
    
    x_coords, y_coords = [], []
    colors_list, sizes, symbols = [], [], []
    
    for i in range(points_per_ring):
        if i < len(segment):
            base = segment[i]
            value = base_values.get(base, 0.6)
            
            # Ángulo con perturbación genética
            angle_base = (2 * math.pi * i / points_per_ring)
            genetic_perturbation = (value - 1.5) * 0.3 + gc_ratio * 0.2
            angle = angle_base + genetic_perturbation
            
            # Radio con variaciones complejas
            radius_variation = (
                np.sin(angle * (3 + ring)) * (5 + complexity_factor * 3) +
                np.cos(angle * (2 + value)) * (3 + repeat_density * 10) +
                value * 4
            )
            radius = ring_radius + radius_variation
            
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            
            x_coords.append(x)
            y_coords.append(y)
            
            # Color contextual
            base_color = colors.get(base, colors['N'])
            colors_list.append(base_color)
            
            # Tamaño basado en posición genética
            size = max(6, 8 + value * 3 + ring * 0.5)
            sizes.append(size)
            
            # Formas abstractas orgánicas
            symbols.append('circle')  # Solo círculos para simplicidad
    
    # Crear puntos suavizados para líneas
    if len(x_coords) > 3:
        # Interpolación circular
        angles_smooth = np.linspace(0, 2 * math.pi, len(x_coords) * 3)
        x_interp = np.interp(angles_smooth, 
                           [math.atan2(y, x) for x, y in zip(x_coords, y_coords)], 
                           x_coords)
        y_interp = np.interp(angles_smooth,
                           [math.atan2(y, x) for x, y in zip(x_coords, y_coords)], 
                           y_coords)
        x_smooth = list(x_interp) + [x_interp[0]]
        y_smooth = list(y_interp) + [y_interp[0]]
    else:
        x_smooth, y_smooth = x_coords, y_coords
    
    return {
        'x_coords': x_coords,
        'y_coords': y_coords,
        'colors': colors_list,
        'sizes': sizes,
        'symbols': symbols,
        'opacity': max(0.4, 0.9 - ring * 0.08),
        'x_smooth': x_smooth,
        'y_smooth': y_smooth,
        'line_color': colors_list[0] if colors_list else colors['A'],
        'line_width': max(1, 3 - ring * 0.3),
        'line_opacity': max(0.2, 0.6 - ring * 0.05)
    }

def crear_patron_fractal(ring_data, segment, colors):
    """Crea patrones fractales secundarios"""
    if len(segment) < 10:
        return None
    
    base_values = {'A': 1.2, 'T': 1.8, 'C': 2.4, 'G': 3.0, 'N': 0.6}
    
    fractal_x, fractal_y = [], []
    fractal_colors, fractal_sizes = [], []
    
    for i, base in enumerate(segment[::2]):  # Cada segunda base
        if i < len(ring_data['x_coords']):
            # Posición base del anillo principal
            base_x = ring_data['x_coords'][i % len(ring_data['x_coords'])]
            base_y = ring_data['y_coords'][i % len(ring_data['y_coords'])]
            
            # Crear mini-fractal alrededor del punto
            value = base_values.get(base, 0.6)
            for sub_i in range(3):
                angle = (2 * math.pi * sub_i / 3) + value
                radius = 5 + value * 2
                
                fx = base_x + radius * np.cos(angle)
                fy = base_y + radius * np.sin(angle)
                
                fractal_x.append(fx)
                fractal_y.append(fy)
                fractal_colors.append(colors.get(base, colors['N']))
                fractal_sizes.append(max(2, value * 2))
    
    return {
        'x': fractal_x,
        'y': fractal_y,
        'colors': fractal_colors,
        'sizes': fractal_sizes
    }

def crear_centro_mandala(segment, colors, complexity_factor):
    """Crea el centro artístico del mandala"""
    if len(segment) < 5:
        return None
    
    base_values = {'A': 1.2, 'T': 1.8, 'C': 2.4, 'G': 3.0, 'N': 0.6}
    
    centro_x, centro_y = [], []
    centro_colors, centro_sizes = [], []
    
    # Crear estrella central basada en las primeras bases
    for i, base in enumerate(segment[:8]):
        value = base_values.get(base, 0.6)
        angle = (2 * math.pi * i / 8) + value * 0.1
        radius = 8 + complexity_factor * 3 + value * 2
        
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        
        centro_x.append(x)
        centro_y.append(y)
        centro_colors.append(colors.get(base, colors['N']))
        centro_sizes.append(15 + value * 3)
    
    return {
        'x': centro_x,
        'y': centro_y,
        'colors': centro_colors,
        'sizes': centro_sizes
    }

def crear_rayos_geneticos(secuencia, colors, gc_ratio):
    """Crea rayos emanando del centro basados en patrones genéticos"""
    base_values = {'A': 1.2, 'T': 1.8, 'C': 2.4, 'G': 3.0, 'N': 0.6}
    rayos = []
    
    # Crear rayos basados en secuencias repetitivas
    num_rayos = max(4, int(6 + gc_ratio * 8))
    
    for i in range(num_rayos):
        if i * 20 < len(secuencia):
            base = secuencia[i * 20]
            value = base_values.get(base, 0.6)
            
            angle = (2 * math.pi * i / num_rayos) + value * 0.2
            length = 80 + value * 20 + gc_ratio * 30
            
            x_rayo = [0, length * np.cos(angle)]
            y_rayo = [0, length * np.sin(angle)]
            
            rayos.append({
                'x': x_rayo,
                'y': y_rayo,
                'color': colors.get(base, colors['N']),
                'width': max(1, value)
            })
    
    return rayos

def crear_galaxia_genetica(secuencia, theme='scientific', genetic_seed=None):
    """Crea una galaxia artística compleja con múltiples estructuras cósmicas"""
    max_length = min(len(secuencia), 6000)
    sequence_segment = secuencia[:max_length]
    
    colors = COLOR_THEMES[theme]
    base_values = {'A': 1.0, 'T': 1.5, 'C': 2.0, 'G': 2.5, 'N': 0.5}
    
    # Usar semilla genética para galaxias únicas
    if genetic_seed:
        np.random.seed(genetic_seed['id_hash'] % 10000)
        random.seed(genetic_seed['id_hash'] % 10000)
        arm_count_modifier = int(genetic_seed['sequence_diversity'] / 2)
        density_modifier = genetic_seed['dinuc_frequency']
    else:
        arm_count_modifier = 0
        density_modifier = 1.0
    
    # Análisis genético para estructura galáctica única
    gc_content = sequence_segment.count('G') + sequence_segment.count('C')
    at_content = sequence_segment.count('A') + sequence_segment.count('T')
    gc_ratio = gc_content / len(sequence_segment) if len(sequence_segment) > 0 else 0.5
    
    # Detectar patrones para crear brazos espirales
    spiral_patterns = detectar_patrones_espirales(sequence_segment)
    cluster_density = calcular_clusters_geneticos(sequence_segment)
    
    fig = go.Figure()
    
    # Crear brazos espirales principales basados en patrones genéticos
    for arm_index, pattern in enumerate(spiral_patterns[:4]):  # Máximo 4 brazos
        arm_data = generar_brazo_espiral(
            sequence_segment, pattern, arm_index, colors, base_values, 
            gc_ratio, cluster_density
        )
        
        if arm_data:
            # Estrellas principales del brazo
            fig.add_trace(go.Scatter(
                x=arm_data['stars_x'],
                y=arm_data['stars_y'],
                mode='markers',
                marker=dict(
                    color=arm_data['star_colors'],
                    size=arm_data['star_sizes'],
                    opacity=arm_data['star_opacity'],
                    symbol='circle',
                    line=dict(width=0)
                ),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Nebulosas (nubes de gas genético)
            if arm_data['nebula_x']:
                fig.add_trace(go.Scatter(
                    x=arm_data['nebula_x'],
                    y=arm_data['nebula_y'],
                    mode='markers',
                    marker=dict(
                        color=arm_data['nebula_colors'],
                        size=arm_data['nebula_sizes'],
                        opacity=0.3,
                        symbol='circle'
                    ),
                    showlegend=False,
                    hoverinfo='skip'
                ))
            
            # Conectores estelares (líneas tenues entre estrellas)
            if len(arm_data['stars_x']) > 1:
                fig.add_trace(go.Scatter(
                    x=arm_data['connector_x'],
                    y=arm_data['connector_y'],
                    mode='lines',
                    line=dict(
                        color=arm_data['arm_color'],
                        width=1,
                        dash='dot'
                    ),
                    opacity=0.2,
                    showlegend=False,
                    hoverinfo='skip'
                ))
    
    # Crear centro galáctico super masivo
    centro_galactico = crear_centro_galactico(sequence_segment[:100], colors, gc_ratio)
    if centro_galactico:
        fig.add_trace(go.Scatter(
            x=centro_galactico['x'],
            y=centro_galactico['y'],
            mode='markers',
            marker=dict(
                color=centro_galactico['colors'],
                size=centro_galactico['sizes'],
                opacity=centro_galactico['opacity'],
                symbol='circle',
                line=dict(width=2, color='white')
            ),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Anillos de acreción alrededor del centro
        anillos = crear_anillos_acrecion(sequence_segment[:50], colors, gc_ratio)
        for anillo in anillos:
            fig.add_trace(go.Scatter(
                x=anillo['x'],
                y=anillo['y'],
                mode='lines',
                line=dict(
                    color=anillo['color'],
                    width=anillo['width']
                ),
                opacity=anillo['opacity'],
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Crear cúmulos estelares dispersos
    cumulos = crear_cumulos_estelares(sequence_segment, colors, cluster_density)
    for cumulo in cumulos:
        fig.add_trace(go.Scatter(
            x=cumulo['x'],
            y=cumulo['y'],
            mode='markers',
            marker=dict(
                color=cumulo['colors'],
                size=cumulo['sizes'],
                opacity=0.6,
                symbol='circle'
            ),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Agregar polvo cósmico (fondo de partículas pequeñas)
    polvo_cosmico = generar_polvo_cosmico(sequence_segment, colors, len(sequence_segment))
    if polvo_cosmico:
        fig.add_trace(go.Scatter(
            x=polvo_cosmico['x'],
            y=polvo_cosmico['y'],
            mode='markers',
            marker=dict(
                color=polvo_cosmico['colors'],
                size=[1, 2] * (len(polvo_cosmico['x']) // 2),
                opacity=0.3,
                symbol='circle'
            ),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Configurar vista galáctica
    max_extent = 200 + len(sequence_segment) * 0.05
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,1)',
        paper_bgcolor='rgba(0,0,0,1)',
        xaxis=dict(visible=False, range=[-max_extent, max_extent]),
        yaxis=dict(visible=False, range=[-max_extent, max_extent]),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return fig

def detectar_patrones_espirales(secuencia):
    """Detecta patrones que formarán brazos espirales"""
    patrones = []
    
    # Buscar secuencias repetitivas que definirán los brazos
    for length in range(3, 12):
        for i in range(len(secuencia) - length):
            pattern = secuencia[i:i + length]
            count = secuencia.count(pattern)
            if count >= 3:  # Patrón significativo
                positions = [j for j, seq in enumerate(secuencia) if secuencia[j:j+length] == pattern]
                patrones.append({
                    'pattern': pattern,
                    'positions': positions,
                    'frequency': count,
                    'length': length
                })
    
    # Ordenar por frecuencia y devolver los más significativos
    patrones.sort(key=lambda x: x['frequency'] * x['length'], reverse=True)
    return patrones[:6]

def calcular_clusters_geneticos(secuencia):
    """Calcula densidad de clusters para cúmulos estelares"""
    clusters = 0
    window_size = 20
    
    for i in range(0, len(secuencia) - window_size, window_size):
        window = secuencia[i:i + window_size]
        unique_bases = len(set(window))
        if unique_bases <= 2:  # Región homogénea = cluster
            clusters += 1
    
    return clusters / (len(secuencia) // window_size) if len(secuencia) > window_size else 0.1

def generar_brazo_espiral(secuencia, pattern_data, arm_index, colors, base_values, gc_ratio, cluster_density):
    """Genera un brazo espiral basado en un patrón genético"""
    if not pattern_data or len(pattern_data['positions']) < 3:
        return None
    
    # Parámetros del brazo basados en genética
    pattern = pattern_data['pattern']
    positions = pattern_data['positions']
    
    # Color dominante del patrón
    base_counts = {base: pattern.count(base) for base in 'ATCG'}
    dominant_base = max(base_counts, key=base_counts.get)
    arm_color = colors.get(dominant_base, colors['N'])
    
    stars_x, stars_y = [], []
    star_colors, star_sizes = [], []
    nebula_x, nebula_y = [], []
    nebula_colors, nebula_sizes = [], []
    
    # Generar espiral basada en posiciones del patrón
    for i, pos in enumerate(positions):
        # Ángulo de espiral
        base_angle = (2 * math.pi * arm_index / 4) + (pos * 0.02)  # 4 brazos máximo
        spiral_factor = 3 + gc_ratio * 2  # Apertura de espiral
        angle = base_angle + (i * spiral_factor * 0.1)
        
        # Radio creciente con variaciones
        base_radius = 30 + i * 8
        genetic_variation = sum(base_values.get(secuencia[j], 1) for j in range(max(0, pos-5), min(len(secuencia), pos+5))) / 10
        radius = base_radius + genetic_variation * 10
        
        # Posición de estrella principal
        x_star = radius * np.cos(angle)
        y_star = radius * np.sin(angle)
        
        stars_x.append(x_star)
        stars_y.append(y_star)
        star_colors.append(arm_color)
        
        # Tamaño basado en importancia del patrón
        size = max(4, 6 + pattern_data['frequency'] * 0.5 + genetic_variation)
        star_sizes.append(size)
        
        # Agregar nebulosas ocasionales
        if i % 3 == 0 and cluster_density > 0.3:
            # Nebulosa alrededor de la estrella
            for nebula_i in range(random.randint(2, 6)):
                nebula_angle = angle + random.uniform(-0.5, 0.5)
                nebula_radius = radius + random.uniform(-15, 15)
                
                nebula_x.append(nebula_radius * np.cos(nebula_angle))
                nebula_y.append(nebula_radius * np.sin(nebula_angle))
                nebula_colors.append(arm_color)
                nebula_sizes.append(random.randint(8, 20))
    
    # Crear conectores suaves entre estrellas
    connector_x, connector_y = [], []
    if len(stars_x) > 1:
        for i in range(len(stars_x)):
            connector_x.append(stars_x[i])
            connector_y.append(stars_y[i])
            
            # Agregar puntos intermedios suaves
            if i < len(stars_x) - 1:
                mid_x = (stars_x[i] + stars_x[i+1]) / 2
                mid_y = (stars_y[i] + stars_y[i+1]) / 2
                connector_x.extend([mid_x])
                connector_y.extend([mid_y])
    
    return {
        'stars_x': stars_x,
        'stars_y': stars_y,
        'star_colors': star_colors,
        'star_sizes': star_sizes,
        'star_opacity': max(0.5, 0.8 - arm_index * 0.1),
        'nebula_x': nebula_x,
        'nebula_y': nebula_y,
        'nebula_colors': nebula_colors,
        'nebula_sizes': nebula_sizes,
        'connector_x': connector_x,
        'connector_y': connector_y,
        'arm_color': arm_color
    }

def crear_centro_galactico(secuencia, colors, gc_ratio):
    """Crea el centro galáctico supermasivo"""
    if len(secuencia) < 10:
        return None
    
    base_values = {'A': 1.0, 'T': 1.5, 'C': 2.0, 'G': 2.5, 'N': 0.5}
    
    centro_x, centro_y = [], []
    centro_colors, centro_sizes = [], []
    
    # Centro principal (agujero negro)
    centro_x.append(0)
    centro_y.append(0)
    centro_colors.append('white')
    centro_sizes.append(25 + gc_ratio * 15)
    
    # Estrellas orbitando el centro
    for i, base in enumerate(secuencia[:12]):
        value = base_values.get(base, 1.0)
        angle = (2 * math.pi * i / 12) + value * 0.3
        radius = 15 + value * 5
        
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        
        centro_x.append(x)
        centro_y.append(y)
        centro_colors.append(colors.get(base, colors['N']))
        centro_sizes.append(8 + value * 3)
    
    return {
        'x': centro_x,
        'y': centro_y,
        'colors': centro_colors,
        'sizes': centro_sizes,
        'opacity': [1.0] + [0.8] * (len(centro_x) - 1)
    }

def crear_anillos_acrecion(secuencia, colors, gc_ratio):
    """Crea anillos de acreción alrededor del centro galáctico"""
    anillos = []
    
    for ring_i in range(3):
        radius = 20 + ring_i * 8 + gc_ratio * 10
        points = 36
        
        x_ring = []
        y_ring = []
        
        for i in range(points + 1):
            angle = (2 * math.pi * i / points)
            # Agregar variación basada en secuencia
            if ring_i < len(secuencia):
                base_value = {'A': 1.0, 'T': 1.5, 'C': 2.0, 'G': 2.5, 'N': 0.5}.get(secuencia[ring_i], 1.0)
                radius_var = radius + np.sin(angle * 4) * base_value
            else:
                radius_var = radius
            
            x_ring.append(radius_var * np.cos(angle))
            y_ring.append(radius_var * np.sin(angle))
        
        anillos.append({
            'x': x_ring,
            'y': y_ring,
            'color': colors['G'] if ring_i % 2 == 0 else colors['C'],
            'width': max(1, 3 - ring_i),
            'opacity': max(0.2, 0.6 - ring_i * 0.15)
        })
    
    return anillos

def crear_cumulos_estelares(secuencia, colors, cluster_density):
    """Crea cúmulos estelares dispersos"""
    cumulos = []
    base_values = {'A': 1.0, 'T': 1.5, 'C': 2.0, 'G': 2.5, 'N': 0.5}
    
    num_cumulos = max(2, int(cluster_density * 8))
    
    for cumulo_i in range(num_cumulos):
        if cumulo_i * 50 >= len(secuencia):
            break
            
        # Posición del cúmulo
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(80, 150)
        center_x = distance * np.cos(angle)
        center_y = distance * np.sin(angle)
        
        cumulo_x, cumulo_y = [], []
        cumulo_colors, cumulo_sizes = [], []
        
        # Estrellas del cúmulo
        segment = secuencia[cumulo_i * 50:(cumulo_i + 1) * 50]
        for i, base in enumerate(segment[:15]):  # Máximo 15 estrellas por cúmulo
            value = base_values.get(base, 1.0)
            
            # Distribución alrededor del centro
            local_angle = random.uniform(0, 2 * math.pi)
            local_radius = random.uniform(5, 20) + value * 3
            
            x = center_x + local_radius * np.cos(local_angle)
            y = center_y + local_radius * np.sin(local_angle)
            
            cumulo_x.append(x)
            cumulo_y.append(y)
            cumulo_colors.append(colors.get(base, colors['N']))
            cumulo_sizes.append(max(3, 4 + value * 2))
        
        if cumulo_x:
            cumulos.append({
                'x': cumulo_x,
                'y': cumulo_y,
                'colors': cumulo_colors,
                'sizes': cumulo_sizes
            })
    
    return cumulos

def generar_polvo_cosmico(secuencia, colors, sequence_length):
    """Genera polvo cósmico de fondo"""
    if sequence_length < 100:
        return None
    
    num_particles = min(200, sequence_length // 20)
    
    polvo_x, polvo_y = [], []
    polvo_colors = []
    
    for i in range(num_particles):
        # Distribución aleatoria pero concentrada hacia el centro
        angle = random.uniform(0, 2 * math.pi)
        # Distribución exponencial hacia afuera
        radius = random.expovariate(0.02) + 20
        
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        
        polvo_x.append(x)
        polvo_y.append(y)
        
        # Color basado en posición en secuencia
        base_index = i % len(secuencia)
        base = secuencia[base_index]
        polvo_colors.append(colors.get(base, colors['N']))
    
    return {
        'x': polvo_x,
        'y': polvo_y,
        'colors': polvo_colors
    }

def crear_mapa_calor_gc(secuencia, window_size=50):
    """Crea un mapa de calor del contenido GC a lo largo de la secuencia"""
    
    # Calcular contenido GC en ventanas deslizantes
    gc_content = []
    positions = []
    
    for i in range(0, len(secuencia) - window_size + 1, 10):
        window = secuencia[i:i + window_size]
        gc_count = window.count('G') + window.count('C')
        gc_percentage = (gc_count / len(window)) * 100
        gc_content.append(gc_percentage)
        positions.append(i + window_size // 2)
    
    # Crear matriz para el heatmap
    matrix = np.array(gc_content).reshape(1, -1)
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=positions,
        colorscale='Viridis',
        colorbar=dict(title="% GC Content"),
        hovertemplate="<b>Posición:</b> %{x}<br><b>Contenido GC:</b> %{z:.1f}%<extra></extra>"
    ))
    
    fig.update_layout(
        title="Mapa de Calor: Contenido GC a lo largo de la Secuencia",
        xaxis_title="Posición en la Secuencia",
        yaxis_visible=False,
        height=200,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def crear_patron_circular(secuencia, theme='scientific'):
    """Crea un patrón circular artístico del ADN"""
    
    max_length = min(len(secuencia), 2000)
    sequence_segment = secuencia[:max_length]
    
    # Crear círculo con las bases
    angles = np.linspace(0, 2 * np.pi, max_length, endpoint=False)
    
    # Radio variable según la base
    base_radii = {'A': 1.0, 'T': 1.2, 'C': 0.8, 'G': 1.4, 'N': 0.6}
    
    x_coords = []
    y_coords = []
    colors_list = []
    sizes = []
    
    colors = COLOR_THEMES[theme]
    
    for i, (angle, base) in enumerate(zip(angles, sequence_segment)):
        if base not in base_radii:
            base = 'N'
        
        radius = base_radii[base]
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        
        x_coords.append(x)
        y_coords.append(y)
        colors_list.append(colors[base])
        sizes.append(BASE_ART_MAP[base]['size'])
    
    fig = go.Figure()
    
    # Agregar puntos de bases
    for base in ['A', 'T', 'C', 'G', 'N']:
        base_x = [x for i, x in enumerate(x_coords) if sequence_segment[i] == base]
        base_y = [y for i, y in enumerate(y_coords) if sequence_segment[i] == base]
        base_sizes = [s for i, s in enumerate(sizes) if sequence_segment[i] == base]
        
        if base_x:  # Solo si hay bases de este tipo
            fig.add_trace(go.Scatter(
                x=base_x, y=base_y,
                mode='markers',
                marker=dict(
                    color=colors[base],
                    size=base_sizes,
                    opacity=0.7,
                    line=dict(width=1, color='white')
                ),
                name=f'Base {base}',
                hovertemplate=f"<b>Base:</b> {base}<extra></extra>"
            ))
    
    # Agregar líneas conectoras suaves
    fig.add_trace(go.Scatter(
        x=x_coords, y=y_coords,
        mode='lines',
        line=dict(color='rgba(255,255,255,0.2)', width=1),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        title="Patrón Circular Genético",
        xaxis=dict(visible=False, range=[-2, 2]),
        yaxis=dict(visible=False, range=[-2, 2]),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig

def generar_visualizacion(seq_record, style='fluid', theme='scientific'):
    """Crea visualización artística avanzada del ADN"""
    secuencia = str(seq_record.seq).upper()
    gc = gc_fraction(secuencia) * 100
    
    # Crear semilla única basada en el ID de la secuencia y primeras bases
    sequence_id = str(seq_record.id)
    genetic_seed = crear_semilla_genetica(secuencia, sequence_id)
    
    if style == 'fluid':
        fig = crear_arte_fluido(secuencia, theme, genetic_seed)
    elif style == 'mandala':
        fig = crear_mandala_genetico(secuencia, theme, genetic_seed)
    elif style == 'galaxy':
        fig = crear_galaxia_genetica(secuencia, theme, genetic_seed)
    elif style == 'heatmap':
        fig = crear_mapa_calor_gc(secuencia)
    else:  # classic fallback
        fig = crear_visualizacion_clasica(secuencia, seq_record, theme)
    
    return fig, gc

def crear_semilla_genetica(secuencia, sequence_id):
    """Crea una semilla única para cada secuencia genética"""
    # Combinar ID de secuencia con características genéticas únicas
    id_hash = hash(sequence_id) % 1000000
    
    # Análisis de la secuencia para parámetros únicos
    first_50 = secuencia[:50] if len(secuencia) >= 50 else secuencia
    last_50 = secuencia[-50:] if len(secuencia) >= 50 else secuencia
    
    # Calcular métricas únicas
    gc_content = (secuencia.count('G') + secuencia.count('C')) / len(secuencia)
    at_content = (secuencia.count('A') + secuencia.count('T')) / len(secuencia)
    
    # Patrón de dinucleótidos únicos
    dinucleotides = {}
    for i in range(len(secuencia) - 1):
        pair = secuencia[i:i+2]
        dinucleotides[pair] = dinucleotides.get(pair, 0) + 1
    
    most_common_dinuc = max(dinucleotides, key=dinucleotides.get) if dinucleotides else 'AT'
    dinuc_frequency = dinucleotides.get(most_common_dinuc, 1) / len(secuencia)
    
    # Patrones de repetición únicos
    repeat_pattern = detectar_patron_principal(secuencia)
    
    return {
        'id_hash': id_hash,
        'sequence_length': len(secuencia),
        'gc_ratio': gc_content,
        'at_ratio': at_content,
        'first_bases': first_50,
        'last_bases': last_50,
        'dominant_dinucleotide': most_common_dinuc,
        'dinuc_frequency': dinuc_frequency,
        'repeat_signature': repeat_pattern,
        'sequence_diversity': len(set(secuencia[:200])),  # Diversidad en primeras 200 bases
        'middle_gc': (secuencia[len(secuencia)//4:3*len(secuencia)//4].count('G') + 
                     secuencia[len(secuencia)//4:3*len(secuencia)//4].count('C')) / 
                     (len(secuencia)//2) if len(secuencia) > 4 else gc_content
    }

def detectar_patron_principal(secuencia):
    """Detecta el patrón repetitivo más significativo en la secuencia"""
    best_pattern = ""
    max_score = 0
    
    # Buscar patrones de longitud 3-8
    for length in range(3, 9):
        pattern_counts = {}
        for i in range(len(secuencia) - length):
            pattern = secuencia[i:i + length]
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        if pattern_counts:
            most_common = max(pattern_counts, key=pattern_counts.get)
            score = pattern_counts[most_common] * length
            if score > max_score:
                max_score = score
                best_pattern = most_common
    
    return best_pattern if best_pattern else secuencia[:6]

def crear_visualizacion_clasica(secuencia, seq_record, theme):
    """Visualización clásica mejorada"""
    max_length = min(len(secuencia), 1000)
    sequence_segment = secuencia[:max_length]
    
    # Preparar datos
    bases = []
    posiciones = []
    y_positions = []
    
    colors = COLOR_THEMES[theme]
    
    for i, base in enumerate(sequence_segment):
        if base not in colors:
            base = 'N'
        
        bases.append(base)
        posiciones.append(i)
        # Crear patrón ondulado basado en la base
        base_heights = {'A': 1, 'T': 2, 'C': 3, 'G': 4, 'N': 0}
        y_positions.append(base_heights[base] + np.sin(i / 20) * 0.5)
    
    fig = go.Figure()
    
    # Agregar trazas por cada tipo de base
    for base in ['A', 'T', 'C', 'G', 'N']:
        base_x = [x for i, x in enumerate(posiciones) if bases[i] == base]
        base_y = [y for i, y in enumerate(y_positions) if bases[i] == base]
        
        if base_x:
            fig.add_trace(go.Scatter(
                x=base_x, y=base_y,
                mode='markers',
                marker=dict(
                    color=colors[base],
                    size=BASE_ART_MAP[base]['size'],
                    opacity=0.8,
                    line=dict(width=1, color='white'),
                    symbol=BASE_ART_MAP[base]['symbol']
                ),
                name=f'Base {base}',
                hovertemplate=f"<b>Posición:</b> %{{x}}<br><b>Base:</b> {base}<extra></extra>"
            ))
    
    fig.update_layout(
        title=f"Arte Genético: {seq_record.id}",
        xaxis_title="Posición en Secuencia",
        yaxis_title="Estructura",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400,
        showlegend=True
    )
    
    return fig

def mostrar_estadisticas_secuencia(seq_record):
    """Muestra estadísticas detalladas de la secuencia"""
    secuencia = str(seq_record.seq).upper()
    
    # Contar bases
    conteo_bases = {
        'A': secuencia.count('A'),
        'T': secuencia.count('T'),
        'C': secuencia.count('C'),
        'G': secuencia.count('G'),
        'N': secuencia.count('N')
    }
    
    total_bases = sum(conteo_bases.values())
    
    # Mostrar métricas en columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Adenina (A)", f"{conteo_bases['A']:,}", f"{(conteo_bases['A']/total_bases*100):.1f}%")
    with col2:
        st.metric("Timina (T)", f"{conteo_bases['T']:,}", f"{(conteo_bases['T']/total_bases*100):.1f}%")
    with col3:
        st.metric("Citosina (C)", f"{conteo_bases['C']:,}", f"{(conteo_bases['C']/total_bases*100):.1f}%")
    with col4:
        st.metric("Guanina (G)", f"{conteo_bases['G']:,}", f"{(conteo_bases['G']/total_bases*100):.1f}%")
    
    return conteo_bases

# Configuración de página
st.set_page_config(
    page_title="DNA Scientific Art Generator",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar base de datos
if 'db_initialized' not in st.session_state:
    create_tables()
    st.session_state.db_initialized = True

# Inicializar session ID para tracking
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Interfaz principal
st.title("🧬 Arca Digital Genética")
st.markdown("**El primer zoológico digital del mundo - Arte NFT basado en ADN real de especies**")

# Hero section con especies destacadas
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🐅 Especies en Peligro")
    st.markdown("Tigre Siberiano, Orangután de Sumatra")
    st.markdown("*Arte genético de las especies más raras*")

with col2:
    st.markdown("### 🐋 Megafauna Icónica") 
    st.markdown("Ballena Azul, Elefante Africano")
    st.markdown("*Los gigantes genéticos del planeta*")

with col3:
    st.markdown("### 🧬 Genética Única")
    st.markdown("Medusa Inmortal, Oso de Agua")
    st.markdown("*ADN con superpoderes evolutivos*")

st.markdown("---")

# Verificar estado de credenciales NCBI
current_email = os.getenv("ENTREZ_EMAIL")
current_api_key = os.getenv("NCBI_API_KEY")

if current_email and current_api_key:
    st.success(f"🔗 Conectado a NCBI GenBank con acceso premium (10 req/sec)")
elif current_api_key:
    st.info(f"🔗 Conectado a NCBI GenBank - Configurar ENTREZ_EMAIL para funcionalidad completa")
else:
    st.warning("⚠️ Configura NCBI_API_KEY y ENTREZ_EMAIL en variables de entorno para acceso completo")

# Sidebar con configuraciones
with st.sidebar:
    st.header("🔧 Explorar el Arca")
    
    # Especies destacadas organizadas por categoría
    st.subheader("🌟 Colecciones Especiales")
    
    for category_key, category_data in FEATURED_SPECIES.items():
        with st.expander(f"{category_data['name']} (×{category_data['rarity_multiplier']})"):
            for species in category_data['species']:
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(
                        f"{species['common_name']}", 
                        key=f"feat_{species['scientific_name']}",
                        help=f"{species['conservation_status']} - {species['population']}"
                    ):
                        st.session_state.selected_organism = species['scientific_name']
                        st.rerun()
                with col2:
                    # Indicador de rareza
                    rarity_emoji = "💎" if category_data['rarity_multiplier'] >= 4 else "⭐" if category_data['rarity_multiplier'] >= 3 else "🔹"
                    st.markdown(f"{rarity_emoji}")
    
    st.markdown("---")
    
    # Sistema de búsqueda inteligente
    st.subheader("🔍 Buscador de Animales")
    
    # Opción para buscar por nombre común o científico
    search_type = st.radio(
        "Tipo de búsqueda:",
        ["Nombre común (ej: tigre, ballena)", "Nombre científico"],
        horizontal=True
    )
    
    # Initialize organismo variable with default value
    organismo = "Homo sapiens"
    
    if search_type == "Nombre común (ej: tigre, ballena)":
        # Búsqueda por nombre común
        common_name_query = st.text_input(
            "Escribe el nombre del animal:",
            placeholder="tigre, ballena, águila, serpiente...",
            help="Escribe el nombre común del animal en español o inglés"
        )
        
        if common_name_query and len(common_name_query) > 2:
            with st.spinner("Buscando nombre científico..."):
                search_results = animal_search.search_comprehensive(common_name_query)
                
                if search_results:
                    st.markdown("**Resultados encontrados:**")
                    for i, result in enumerate(search_results[:5]):
                        confidence_emoji = "🎯" if result['confidence'] > 0.9 else "✅" if result['confidence'] > 0.7 else "📝"
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if st.button(
                                f"{confidence_emoji} {result['common_name']} → *{result['scientific_name']}*",
                                key=f"search_result_{i}",
                                help=f"Confianza: {result['confidence']:.0%} | Fuente: {result['source']}"
                            ):
                                st.session_state.selected_organism = result['scientific_name']
                                st.rerun()
                        with col2:
                            st.text(f"{result['confidence']:.0%}")
                    
                    # Use the first result as the current organismo for generation
                    if search_results:
                        organismo = search_results[0]['scientific_name']
                else:
                    # Mostrar sugerencias si no hay resultados exactos
                    suggestions = animal_search.suggest_similar_names(common_name_query)
                    if suggestions:
                        st.info("**¿Quisiste decir alguno de estos?**")
                        for suggestion in suggestions[:4]:
                            if st.button(f"💡 {suggestion}", key=f"suggestion_{suggestion}"):
                                # Re-buscar con la sugerencia
                                auto_results = animal_search.search_comprehensive(suggestion)
                                if auto_results:
                                    st.session_state.selected_organism = auto_results[0]['scientific_name']
                                    st.rerun()
                    else:
                        st.warning("No se encontraron resultados. Intenta con otro nombre o usa búsqueda científica.")
        
        # Ejemplos populares
        if not common_name_query:
            st.markdown("**Ejemplos populares:**")
            example_animals = ["tigre", "ballena azul", "águila", "tiburón", "elefante", "rana"]
            cols = st.columns(3)
            for i, animal in enumerate(example_animals):
                with cols[i % 3]:
                    if st.button(f"🔸 {animal}", key=f"example_{animal}"):
                        results = animal_search.search_comprehensive(animal)
                        if results:
                            st.session_state.selected_organism = results[0]['scientific_name']
                            st.rerun()
    
    else:
        # Búsqueda directa por nombre científico
        organismo = st.text_input(
            "Nombre científico:", 
            value="Homo sapiens",
            help="Busca cualquier especie en GenBank usando nomenclatura binomial"
        )
        
        # Sugerencias de búsqueda del catálogo existente
        if organismo and len(organismo) > 2:
            suggestions = suggest_search_terms(organismo)
            if suggestions:
                st.markdown("**Sugerencias del catálogo:**")
                for suggestion in suggestions[:3]:
                    if st.button(f"🔸 {suggestion['common_name']}", key=f"sug_{suggestion['scientific_name']}"):
                        st.session_state.selected_organism = suggestion['scientific_name']
                        st.rerun()
    
    st.markdown("---")
    
    # Controles artísticos
    st.subheader("🎨 Estilo Artístico")
    
    # Selector de estilo de visualización
    art_style = st.selectbox(
        "Estilo de visualización:",
        ["fluid", "mandala", "galaxy", "heatmap", "classic"],
        format_func=lambda x: {
            "fluid": "🌊 Arte Fluido Abstracto",
            "mandala": "🔮 Mandala Genético",
            "galaxy": "✨ Galaxia de Partículas",
            "heatmap": "🔥 Mapa de Calor GC",
            "classic": "📊 Clásico Mejorado"
        }[x],
        help="Selecciona el estilo artístico para la visualización del ADN"
    )
    
    # Selector de tema de colores
    color_theme = st.selectbox(
        "Tema de colores:",
        ["scientific", "ocean", "forest", "sunset", "cosmic"],
        format_func=lambda x: {
            "scientific": "🔬 Científico",
            "ocean": "🌊 Océano",
            "forest": "🌲 Bosque",
            "sunset": "🌅 Atardecer",
            "cosmic": "🌌 Cósmico"
        }[x],
        help="Escoge la paleta de colores para tu arte genético"
    )
    
    # Previsualización de colores
    if color_theme in COLOR_THEMES:
        st.markdown("**Vista previa de colores:**")
        theme_colors = COLOR_THEMES[color_theme]
        color_preview = ""
        for base, color in theme_colors.items():
            color_preview += f'<span style="background-color: {color}; color: white; padding: 2px 8px; margin: 2px; border-radius: 3px;">{base}</span> '
        st.markdown(color_preview, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Favoritos del usuario
    st.subheader("⭐ Mis Favoritos")
    try:
        user_favorites = get_user_favorites(st.session_state.session_id)
        if user_favorites:
            for fav in user_favorites[:5]:
                if st.button(f"🧬 {fav.organism_name}", key=f"fav_{fav.id}"):
                    st.session_state.selected_organism = fav.organism_name
                    st.rerun()
        else:
            st.info("Aún no tienes favoritos")
    except Exception:
        st.info("Favoritos temporalmente no disponibles")
    
    # Recientes
    st.subheader("🕒 Recientes")
    try:
        recent_sequences = get_recent_sequences(limit=3)
        if recent_sequences:
            for seq in recent_sequences:
                if st.button(f"📊 {seq.organism_name}", key=f"rec_{seq.id}"):
                    st.session_state.selected_organism = seq.organism_name
                    st.rerun()
    except Exception:
        st.info("Historial temporalmente no disponible")
    
    # Opciones avanzadas
    with st.expander("⚙️ Opciones avanzadas"):
        max_seq_length = st.slider(
            "Máximo de bases a visualizar:",
            min_value=100,
            max_value=1000,
            value=500,
            step=50,
            help="Limita el número de bases mostradas para mejor rendimiento"
        )
        
        show_statistics = st.checkbox("Mostrar estadísticas detalladas", value=True)
        save_to_favorites = st.checkbox("Guardar en favoritos automáticamente", value=False)
    
    # Estadísticas de la base de datos
    with st.expander("📈 Estadísticas"):
        try:
            db_stats = get_database_stats()
            if db_stats:
                st.metric("Secuencias en BD", db_stats.get('total_sequences', 0))
                st.metric("Búsquedas totales", db_stats.get('total_searches', 0))
                st.metric("Tasa de éxito", f"{db_stats.get('success_rate', 0):.1f}%")
        except Exception as e:
            st.info("Base de datos temporalmente no disponible")
    
    # Configuración de NFT/Blockchain
    st.subheader("🔗 Blockchain & NFT")
    blockchain_status = nft_manager.get_blockchain_status()
    
    if blockchain_status.get("connected"):
        st.success("✅ Blockchain conectado")
        if blockchain_status.get("account_configured"):
            st.info(f"💰 Balance: {blockchain_status.get('balance', '0')} ETH")
    else:
        st.warning("⚠️ Blockchain no configurado")
    
    # Configurar credenciales blockchain
    with st.expander("🔧 Configurar Blockchain"):
        st.markdown("**Para crear NFTs necesitas:**")
        
        col1, col2 = st.columns(2)
        with col1:
            eth_rpc = st.text_input(
                "🌐 RPC URL:",
                value=os.getenv("ETH_RPC_URL", ""),
                placeholder="https://mainnet.infura.io/v3/YOUR_KEY"
            )
            
            contract_addr = st.text_input(
                "📜 Contrato NFT:",
                value=os.getenv("NFT_CONTRACT_ADDRESS", ""),
                placeholder="0x..."
            )
        
        with col2:
            private_key = st.text_input(
                "🔐 Private Key:",
                value="",
                type="password",
                placeholder="Tu private key de Ethereum"
            )
            
            infura_key = st.text_input(
                "🔑 Infura API:",
                value=os.getenv("INFURA_API_KEY", ""),
                placeholder="Tu Infura project ID"
            )
        
        if st.button("💾 Guardar configuración blockchain"):
            if private_key.strip():
                os.environ["ETH_PRIVATE_KEY"] = private_key.strip()
            if eth_rpc.strip():
                os.environ["ETH_RPC_URL"] = eth_rpc.strip()
            if contract_addr.strip():
                os.environ["NFT_CONTRACT_ADDRESS"] = contract_addr.strip()
            if infura_key.strip():
                os.environ["INFURA_API_KEY"] = infura_key.strip()
            
            # Reinicializar manager
            nft_manager._initialize_blockchain()
            st.success("✅ Configuración guardada")
            st.rerun()

# Manejar selección desde sidebar
final_organismo = organismo  # Use the organismo from the search section
if 'selected_organism' in st.session_state:
    final_organismo = st.session_state.selected_organism
    del st.session_state.selected_organism

# Área principal
if st.button("🚀 Generar Visualización", type="primary", use_container_width=True):
    if not final_organismo.strip():
        st.error("Por favor, ingrese un nombre de organismo válido.")
        st.stop()
    
    # Registrar búsqueda
    log_search(final_organismo, successful=False, user_session=st.session_state.session_id)
    
    with st.spinner(f"Obteniendo secuencia genética de {final_organismo}..."):
        seq_record = obtener_secuencia(final_organismo)
        
        if not seq_record:
            st.error(f"❌ Organismo '{final_organismo}' no encontrado en NCBI GenBank")
            st.markdown("**Sugerencias:**")
            st.markdown("- Verifique la ortografía del nombre científico")
            st.markdown("- Pruebe con nombres más específicos (ej: 'Homo sapiens mitochondrion')")
            st.markdown("- Consulte la [base de datos NCBI](https://www.ncbi.nlm.nih.gov/nuccore) para nombres válidos")
            log_search(final_organismo, successful=False, error_message="Organismo no encontrado", user_session=st.session_state.session_id)
            st.stop()
            
        # Actualizar el máximo de secuencia basado en la configuración
        BASE_ART_MAP_TEMP = BASE_ART_MAP.copy()
        
        # Generar visualización
        fig, gc = generar_visualizacion(seq_record, style=art_style, theme=color_theme)
        
        # Registrar búsqueda exitosa
        log_search(final_organismo, successful=True, user_session=st.session_state.session_id)
        
        # Guardar en base de datos y obtener conteo de bases
        conteo_bases = mostrar_estadisticas_secuencia(seq_record)
        db_record = save_dna_sequence(final_organismo, seq_record, gc, conteo_bases)
        
        # Agregar a favoritos si está habilitado
        if save_to_favorites and db_record:
            add_favorite(st.session_state.session_id, final_organismo, seq_record.id)
        
        # Mostrar información de la especie si está en el catálogo
        species_story = get_species_story(final_organismo)
        if species_story:
            st.success(f"🎨 **{species_story['title']}**")
            st.info(f"📖 {species_story['story']}")
            
            # Mostrar datos de conservación
            col1, col2, col3 = st.columns(3)
            with col1:
                status_color = "🔴" if "Crítico" in species_story['conservation'] else "🟡" if "Peligro" in species_story['conservation'] else "🟢"
                st.markdown(f"**Estado:** {status_color} {species_story['conservation']}")
            with col2:
                st.markdown(f"**Población:** {species_story['population']}")
            with col3:
                st.markdown(f"**Hábitat:** {species_story['habitat']}")
                
            # Calcular rareza aumentada para especies especiales
            rarity_multiplier = get_rarity_multiplier(organismo)
            if rarity_multiplier > 1:
                st.markdown(f"### 💎 Rareza Especial: ×{rarity_multiplier}")
        else:
            st.success(f"✅ Secuencia obtenida exitosamente: **{seq_record.id}**")
        
        # Botón para agregar a favoritos
        if not save_to_favorites:
            if st.button("⭐ Agregar a favoritos"):
                try:
                    if add_favorite(st.session_state.session_id, organismo, seq_record.id):
                        st.success("Agregado a favoritos")
                    else:
                        st.info("Ya está en favoritos")
                except Exception:
                    st.warning("Error guardando favorito")
        
        # Métricas principales
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📏 Longitud total", f"{len(seq_record.seq):,} bp")
        with col2:
            st.metric("🧬 Contenido GC", f"{gc:.2f}%")
        with col3:
            visualized_length = min(len(seq_record.seq), max_seq_length)
            st.metric("👁️ Bases visualizadas", f"{visualized_length:,}")
        
        # Mostrar visualización
        st.plotly_chart(fig, use_container_width=True)
        
        # Estadísticas detalladas si está habilitado
        if show_statistics:
            st.subheader("📊 Composición de bases")
            conteo_bases = mostrar_estadisticas_secuencia(seq_record)
            
            # Crear gráfico de composición
            bases_data = {
                'Base': list(conteo_bases.keys()),
                'Cantidad': list(conteo_bases.values()),
                'Color': [BASE_ART_MAP[base]['color'] for base in conteo_bases.keys()]
            }
            
            fig_composition = px.pie(
                values=bases_data['Cantidad'],
                names=bases_data['Base'],
                title="Distribución de nucleótidos",
                color=bases_data['Base'],
                color_discrete_map={k: v['color'] for k, v in BASE_ART_MAP.items()}
            )
            fig_composition.update_layout(height=400)
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig_composition, use_container_width=True)
            
            with col2:
                # Información adicional
                st.subheader("📋 Información técnica")
                st.write(f"**ID de acceso:** `{seq_record.id}`")
                st.write(f"**Descripción:** {seq_record.description[:100]}...")
                st.write(f"**Fecha de análisis:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Mostrar muestra de la secuencia
                sample_length = min(100, len(seq_record.seq))
                st.write(f"**Primeros {sample_length} nucleótidos:**")
                st.code(str(seq_record.seq[:sample_length]), language="text")
        
        # Sección de descarga y NFT
        st.subheader("💾 Descargar visualización")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Botón de descarga PNG
            try:
                buf = io.BytesIO()
                fig.write_image(buf, format="png", width=1200, height=600, scale=2)
                st.download_button(
                    label="📸 Descargar PNG (Alta calidad)",
                    data=buf.getvalue(),
                    file_name=f"dna_art_{seq_record.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    mime="image/png",
                    use_container_width=True
                )
            except Exception as e:
                st.warning(f"Error generando PNG: {str(e)}")
        
        with col2:
            # Botón de descarga HTML
            html_str = fig.to_html(include_plotlyjs='cdn')
            st.download_button(
                label="🌐 Descargar HTML (Interactivo)",
                data=html_str,
                file_name=f"dna_art_{seq_record.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                use_container_width=True
            )
        
        with col3:
            # Botón para crear NFT
            if st.button("🎨 Crear NFT", use_container_width=True):
                with st.spinner("Preparando NFT..."):
                    nft_package = nft_manager.prepare_nft_package(
                        seq_record, final_organismo, gc, conteo_bases, fig
                    )
                    
                    if nft_package:
                        st.session_state.nft_package = nft_package
                        st.success("✅ NFT preparado correctamente")
                    else:
                        st.error("❌ Error preparando NFT")
        
        # Mostrar información del NFT si está preparado
        if 'nft_package' in st.session_state:
            st.subheader("🎨 NFT Generado")
            nft_data = st.session_state.nft_package
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Metadatos del NFT:**")
                metadata = nft_data['metadata']
                st.json({
                    "name": metadata['name'],
                    "description": metadata['description'][:100] + "...",
                    "attributes_count": len(metadata['attributes']),
                    "rarity_score": next((attr['value'] for attr in metadata['attributes'] if attr['trait_type'] == 'Rarity Score'), 0)
                })
                
                # Descargar metadatos
                metadata_json = json.dumps(metadata, indent=2)
                st.download_button(
                    label="📄 Descargar Metadatos JSON",
                    data=metadata_json,
                    file_name=f"nft_metadata_{seq_record.id}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col2:
                st.markdown("**Mintear NFT en Blockchain:**")
                
                # Input para dirección de destino
                to_address = st.text_input(
                    "🎯 Dirección de destino:",
                    placeholder="0x...",
                    help="Dirección Ethereum donde se enviará el NFT"
                )
                
                # Botón para mintear
                if st.button("🚀 Mintear NFT", type="primary", use_container_width=True):
                    if not to_address.strip():
                        st.error("Ingresa una dirección válida")
                    elif not blockchain_status.get("connected") or not blockchain_status.get("account_configured"):
                        st.error("Configura blockchain primero")
                    else:
                        with st.spinner("Minteando NFT en blockchain..."):
                            result = nft_manager.mint_nft(to_address, nft_data['metadata_uri'])
                            
                            if result.get("success"):
                                st.success("🎉 NFT minteado exitosamente!")
                                st.info(f"Hash de transacción: {result['transaction_hash']}")
                                st.info(f"Gas usado: {result['gas_used']:,}")
                                
                                # Limpiar NFT package
                                del st.session_state.nft_package
                            else:
                                st.error(f"Error minteando NFT: {result.get('error', 'Error desconocido')}")
                
                # Información sobre costos
                st.info("💡 **Nota:** El minteo requiere ETH para gas fees")

# Información sobre la aplicación
st.markdown("---")
with st.expander("ℹ️ Acerca de esta aplicación"):
    st.markdown("""
    ### 🧬 DNA Scientific Art Generator
    
    Esta aplicación utiliza la API de NCBI GenBank para obtener secuencias genéticas reales y crear visualizaciones artísticas científicas.
    
    **Características:**
    - 🔗 Integración directa con NCBI GenBank
    - 🎨 Visualización interactiva con código de colores por nucleótido
    - 📊 Análisis de composición de bases y contenido GC
    - 💾 Descarga en formatos PNG y HTML
    - ⚡ Sistema de caché para optimizar consultas
    
    **Tecnologías utilizadas:**
    - **BioPython:** Procesamiento de datos genéticos
    - **Plotly:** Visualizaciones interactivas
    - **Streamlit:** Interfaz web
    - **NCBI Entrez API:** Acceso a bases de datos genéticas
    - **Blockchain/NFT:** Creación de NFTs únicos basados en ADN
    - **PostgreSQL:** Base de datos para historial y favoritos
    - **IPFS:** Almacenamiento descentralizado de metadatos
    
    **Código de colores:**
    - 🔴 **Adenina (A):** Rojo
    - 🟡 **Timina (T):** Amarillo  
    - 🔵 **Citosina (C):** Azul
    - 🟢 **Guanina (G):** Verde
    - ⚪ **Desconocido (N):** Gris
    """)

# Pie de página
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em;">
    Desarrollado con BioPython + Streamlit | 
    Datos genéticos proporcionados por <a href="https://www.ncbi.nlm.nih.gov/" target="_blank">NCBI GenBank</a>
</div>
""", unsafe_allow_html=True)
