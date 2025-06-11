import streamlit as st
import numpy as np
import plotly.graph_objects as go
from Bio import Entrez, SeqIO
from Bio.SeqUtils import gc_fraction
import io
import math
import hashlib
from animal_search import AnimalSearchEngine
from database import *

# Configuración de página
st.set_page_config(
    page_title="DNA Art Generator",
    page_icon="🧬",
    layout="wide"
)

# Inicializar session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = hashlib.md5(str(np.random.random()).encode()).hexdigest()

# Temas de colores
COLOR_THEMES = {
    'scientific': {
        'A': '#FF6B6B',  # Rojo
        'T': '#4ECDC4',  # Turquesa
        'C': '#45B7D1',  # Azul
        'G': '#96CEB4'   # Verde
    },
    'natural': {
        'A': '#D4A574',  # Marrón tierra
        'T': '#8FBC8F',  # Verde bosque
        'C': '#4682B4',  # Azul acero
        'G': '#DDA0DD'   # Lila
    },
    'cosmic': {
        'A': '#FF69B4',  # Rosa fuerte
        'T': '#00CED1',  # Turquesa oscuro
        'C': '#9370DB',  # Violeta medio
        'G': '#FFD700'   # Dorado
    }
}

def limpiar_nombre_cientifico(nombre):
    """Limpia nombre científico removiendo autores y años"""
    import re
    nombre_limpio = re.sub(r'\([^)]*\)', '', nombre)
    nombre_limpio = re.sub(r'\d{4}', '', nombre_limpio)
    nombre_limpio = re.sub(r'[,;].*', '', nombre_limpio)
    return nombre_limpio.strip()

def obtener_secuencia(organismo):
    """Obtiene secuencia de ADN desde NCBI"""
    Entrez.email = st.secrets.get("ENTREZ_EMAIL", "user@example.com")
    
    organismo_limpio = limpiar_nombre_cientifico(organismo)
    
    # Búsqueda en nucleotide database
    search_handle = Entrez.esearch(
        db="nucleotide",
        term=f"{organismo_limpio}[Organism] AND complete genome",
        retmax=5
    )
    search_results = Entrez.read(search_handle)
    search_handle.close()
    
    if not search_results["IdList"]:
        # Búsqueda más amplia
        search_handle = Entrez.esearch(
            db="nucleotide",
            term=f"{organismo_limpio}[Organism]",
            retmax=10
        )
        search_results = Entrez.read(search_handle)
        search_handle.close()
    
    if not search_results["IdList"]:
        raise ValueError(f"No se encontraron secuencias para {organismo}")
    
    # Obtener la primera secuencia
    seq_id = search_results["IdList"][0]
    
    fetch_handle = Entrez.efetch(
        db="nucleotide",
        id=seq_id,
        rettype="fasta",
        retmode="text"
    )
    
    seq_record = SeqIO.read(io.StringIO(fetch_handle.read()), "fasta")
    fetch_handle.close()
    
    return seq_record

def analizar_perfil_genetico_unico(secuencia, organism_id):
    """Analiza patrones genéticos únicos para generar visualizaciones distintivas"""
    
    # Análisis de frecuencias de nucleótidos
    base_counts = {'A': 0, 'T': 0, 'C': 0, 'G': 0}
    for base in secuencia:
        if base in base_counts:
            base_counts[base] += 1
    
    total = sum(base_counts.values())
    if total == 0:
        return None
    
    # Análisis de dinucleótidos - clave para diferenciación
    dinucs = {}
    for i in range(len(secuencia) - 1):
        dinuc = secuencia[i:i+2]
        if len(dinuc) == 2 and all(b in 'ATCG' for b in dinuc):
            dinucs[dinuc] = dinucs.get(dinuc, 0) + 1
    
    # Análisis de trinucleótidos para mayor especificidad
    trinucs = {}
    for i in range(len(secuencia) - 2):
        trinuc = secuencia[i:i+3]
        if len(trinuc) == 3 and all(b in 'ATCG' for b in trinuc):
            trinucs[trinuc] = trinucs.get(trinuc, 0) + 1
    
    # Patrones de repetición específicos
    repeat_patterns = detectar_patrones_repetitivos(secuencia)
    
    # Distribución posicional de bases
    position_profile = analizar_distribucion_posicional(secuencia)
    
    # Skew y bias direccional específico
    gc_skew = calcular_skew_simple(secuencia, 'GC')
    at_skew = calcular_skew_simple(secuencia, 'AT')
    
    return {
        'base_ratios': {k: v/total for k, v in base_counts.items()},
        'dinuc_profile': dinucs,
        'trinuc_profile': trinucs,
        'repeat_patterns': repeat_patterns,
        'position_profile': position_profile,
        'gc_skew': gc_skew,
        'at_skew': at_skew,
        'sequence_length': len(secuencia),
        'organism_signature': hash(organism_id + secuencia[:100]) % 1000000
    }

def detectar_patrones_repetitivos(secuencia):
    """Detecta patrones de repetición específicos"""
    patterns = {}
    
    for length in range(2, min(10, len(secuencia)//20)):
        pattern_counts = {}
        for i in range(len(secuencia) - length + 1):
            pattern = secuencia[i:i+length]
            if all(b in 'ATCG' for b in pattern):
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        significant_patterns = {k: v for k, v in pattern_counts.items() if v >= 3}
        if significant_patterns:
            patterns[f'length_{length}'] = significant_patterns
    
    return patterns

def analizar_distribucion_posicional(secuencia):
    """Analiza distribución de bases a lo largo de la secuencia"""
    
    segments = 8
    segment_size = len(secuencia) // segments
    
    distribution = []
    for i in range(segments):
        start = i * segment_size
        end = start + segment_size if i < segments - 1 else len(secuencia)
        segment = secuencia[start:end]
        
        if len(segment) > 0:
            gc_content = (segment.count('G') + segment.count('C')) / len(segment)
            at_content = (segment.count('A') + segment.count('T')) / len(segment)
            distribution.append({
                'position': i,
                'gc_content': gc_content,
                'at_content': at_content
            })
    
    return distribution

def calcular_skew_simple(secuencia, base_type):
    """Calcula el skew de bases"""
    
    if base_type == 'GC':
        g_count = secuencia.count('G')
        c_count = secuencia.count('C')
        if g_count + c_count > 0:
            return (g_count - c_count) / (g_count + c_count)
        else:
            return 0
    else:  # AT
        a_count = secuencia.count('A')
        t_count = secuencia.count('T')
        if a_count + t_count > 0:
            return (a_count - t_count) / (a_count + t_count)
        else:
            return 0

def crear_arte_basado_en_perfil(secuencia, genetic_profile, theme):
    """Crea arte único basado en el perfil genético específico"""
    
    colors = COLOR_THEMES.get(theme, COLOR_THEMES['scientific'])
    
    # Determinar tipo de visualización según características genéticas
    gc_content = sum(genetic_profile['base_ratios'][base] for base in ['G', 'C'])
    repeat_density = len(genetic_profile['repeat_patterns'])
    skew_intensity = abs(genetic_profile['gc_skew']) + abs(genetic_profile['at_skew'])
    
    if gc_content > 0.6 and skew_intensity > 0.3:
        # Especies con alto GC y skew -> Patrón cristalino
        fig = crear_patron_cristalino(secuencia, genetic_profile, colors)
    elif gc_content < 0.4 and repeat_density > 2:
        # Especies con bajo GC y repeticiones -> Patrón orgánico
        fig = crear_patron_organico(secuencia, genetic_profile, colors)
    elif repeat_density > 3:
        # Muchas repeticiones -> Patrón espiral
        fig = crear_patron_espiral(secuencia, genetic_profile, colors)
    else:
        # Patrón por defecto -> Scatter especializado
        fig = crear_patron_scatter(secuencia, genetic_profile, colors)
    
    return fig

def crear_patron_cristalino(secuencia, genetic_profile, colors):
    """Patrón cristalino para especies con alto GC"""
    
    fig = go.Figure()
    
    # Usar dinucleótidos para crear estructura cristalina
    dinucs = genetic_profile['dinuc_profile']
    if not dinucs:
        return crear_patron_scatter(secuencia, genetic_profile, colors)
    
    most_common_dinucs = sorted(dinucs.items(), key=lambda x: x[1], reverse=True)[:6]
    
    # Crear red cristalina
    points = []
    for i, (dinuc, freq) in enumerate(most_common_dinucs):
        angle_base = (i * 60) * np.pi / 180  # 6 direcciones principales
        
        for layer in range(1, min(4, freq//20 + 1)):
            angle = angle_base
            radius = layer * 40 + (freq * 0.05)
            
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            
            points.append([x, y, dinuc, freq])
    
    # Dibujar puntos cristalinos
    for x, y, dinuc, freq in points:
        color_key = dinuc[0] if dinuc[0] in colors else 'A'
        
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers',
            marker=dict(
                size=8 + min(freq//30, 15),
                color=colors[color_key],
                symbol='diamond',
                opacity=0.8,
                line=dict(color='white', width=1)
            ),
            showlegend=False,
            hovertemplate=f"Dinucleótido: {dinuc}<br>Frecuencia: {freq}"
        ))
    
    # Conectar puntos cercanos
    for i in range(len(points)):
        for j in range(i+1, len(points)):
            dist = np.sqrt((points[i][0] - points[j][0])**2 + (points[i][1] - points[j][1])**2)
            if dist < 80:
                fig.add_trace(go.Scatter(
                    x=[points[i][0], points[j][0]],
                    y=[points[i][1], points[j][1]],
                    mode='lines',
                    line=dict(color='rgba(255,255,255,0.3)', width=1),
                    showlegend=False,
                    hoverinfo='skip'
                ))
    
    fig.update_layout(
        title=f"Patrón Cristalino - GC: {sum(genetic_profile['base_ratios'][b] for b in ['G', 'C']):.1%}",
        xaxis=dict(visible=False, range=[-200, 200]),
        yaxis=dict(visible=False, range=[-200, 200]),
        showlegend=False,
        plot_bgcolor='black',
        paper_bgcolor='black',
        width=800,
        height=600
    )
    
    return fig

def crear_patron_organico(secuencia, genetic_profile, colors):
    """Patrón orgánico para especies con patrones repetitivos"""
    
    fig = go.Figure()
    
    # Usar patrones de repetición para crear formas orgánicas
    repeat_patterns = genetic_profile['repeat_patterns']
    position_profile = genetic_profile['position_profile']
    
    # Crear espirales basadas en repeticiones
    color_index = 0
    for pattern_length, patterns in repeat_patterns.items():
        if not patterns:
            continue
            
        most_common = max(patterns.items(), key=lambda x: x[1])
        pattern, frequency = most_common
        
        # Crear curva orgánica para este patrón
        t = np.linspace(0, 2*np.pi, min(frequency//2, 50))
        spiral_factor = len(pattern) * 8
        expansion = 1 + t/5
        
        x = spiral_factor * np.cos(t) * expansion + np.sin(t*3) * 10
        y = spiral_factor * np.sin(t) * expansion + np.cos(t*2) * 8
        
        # Color basado en el primer nucleótido del patrón
        color_key = pattern[0] if pattern[0] in colors else list(colors.keys())[color_index % 4]
        color_index += 1
        
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode='lines+markers',
            line=dict(color=colors[color_key], width=2),
            marker=dict(size=4, color=colors[color_key]),
            name=f"Patrón: {pattern}",
            showlegend=False,
            hovertemplate=f"Patrón: {pattern}<br>Frecuencia: {frequency}"
        ))
    
    # Agregar nodos basados en distribución posicional
    for pos_data in position_profile:
        angle = pos_data['position'] * 45 * np.pi / 180
        radius = pos_data['gc_content'] * 80 + 20
        
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers',
            marker=dict(
                size=12,
                color=colors['G'] if pos_data['gc_content'] > 0.5 else colors['A'],
                symbol='circle',
                opacity=0.7,
                line=dict(color='white', width=1)
            ),
            showlegend=False,
            hovertemplate=f"Posición: {pos_data['position']}<br>GC: {pos_data['gc_content']:.1%}"
        ))
    
    fig.update_layout(
        title=f"Patrón Orgánico - Repeticiones: {len(repeat_patterns)}",
        xaxis=dict(visible=False, range=[-150, 150]),
        yaxis=dict(visible=False, range=[-150, 150]),
        showlegend=False,
        plot_bgcolor='black',
        paper_bgcolor='black',
        width=800,
        height=600
    )
    
    return fig

def crear_patron_espiral(secuencia, genetic_profile, colors):
    """Patrón espiral para secuencias con muchas repeticiones"""
    
    fig = go.Figure()
    
    # Crear espiral doble basada en skew
    gc_skew = genetic_profile['gc_skew']
    at_skew = genetic_profile['at_skew']
    
    # Espiral principal basada en GC skew
    t1 = np.linspace(0, 6*np.pi, 200)
    r1 = 5 + t1/2 + abs(gc_skew) * 30
    x1 = r1 * np.cos(t1)
    y1 = r1 * np.sin(t1)
    
    fig.add_trace(go.Scatter(
        x=x1, y=y1,
        mode='lines+markers',
        line=dict(color=colors['G'], width=3),
        marker=dict(size=3, color=colors['G']),
        name="Espiral GC",
        showlegend=False,
        hovertemplate=f"GC Skew: {gc_skew:.3f}"
    ))
    
    # Espiral secundaria basada en AT skew
    t2 = np.linspace(0, 6*np.pi, 150)
    r2 = 3 + t2/3 + abs(at_skew) * 25
    x2 = r2 * np.cos(-t2 + np.pi/3)
    y2 = r2 * np.sin(-t2 + np.pi/3)
    
    fig.add_trace(go.Scatter(
        x=x2, y=y2,
        mode='lines+markers',
        line=dict(color=colors['A'], width=2),
        marker=dict(size=2, color=colors['A']),
        name="Espiral AT",
        showlegend=False,
        hovertemplate=f"AT Skew: {at_skew:.3f}"
    ))
    
    # Puntos de intersección destacados
    base_ratios = genetic_profile['base_ratios']
    for i, (base, ratio) in enumerate(base_ratios.items()):
        if ratio > 0.2:  # Solo bases significativas
            angle = i * np.pi/2
            radius = ratio * 100
            
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            
            fig.add_trace(go.Scatter(
                x=[x], y=[y],
                mode='markers',
                marker=dict(
                    size=15 + ratio*20,
                    color=colors[base],
                    symbol='star',
                    opacity=0.8,
                    line=dict(color='white', width=2)
                ),
                showlegend=False,
                hovertemplate=f"Base: {base}<br>Proporción: {ratio:.1%}"
            ))
    
    fig.update_layout(
        title=f"Patrón Espiral - Skew GC: {gc_skew:.3f}, AT: {at_skew:.3f}",
        xaxis=dict(visible=False, range=[-120, 120]),
        yaxis=dict(visible=False, range=[-120, 120]),
        showlegend=False,
        plot_bgcolor='black',
        paper_bgcolor='black',
        width=800,
        height=600
    )
    
    return fig

def crear_patron_scatter(secuencia, genetic_profile, colors):
    """Patrón scatter por defecto"""
    
    fig = go.Figure()
    
    # Usar trinucleótidos para scatter plot
    trinucs = genetic_profile['trinuc_profile']
    if not trinucs:
        # Fallback: usar dinucleótidos
        dinucs = genetic_profile['dinuc_profile']
        points_data = list(dinucs.items())[:8]
    else:
        points_data = list(trinucs.items())[:12]
    
    # Crear puntos scatter
    for i, (pattern, freq) in enumerate(points_data):
        # Posición basada en características del patrón
        pattern_hash = hash(pattern) % 1000
        angle = (pattern_hash % 360) * np.pi / 180
        radius = 30 + (freq * 0.3)
        
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        
        # Color basado en primer nucleótido
        color_key = pattern[0] if pattern[0] in colors else 'A'
        
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers',
            marker=dict(
                size=8 + min(freq//10, 20),
                color=colors[color_key],
                symbol='circle',
                opacity=0.7,
                line=dict(color='white', width=1)
            ),
            showlegend=False,
            hovertemplate=f"Patrón: {pattern}<br>Frecuencia: {freq}"
        ))
    
    # Conectar puntos cercanos
    if len(points_data) > 1:
        points = []
        for i, (pattern, freq) in enumerate(points_data):
            pattern_hash = hash(pattern) % 1000
            angle = (pattern_hash % 360) * np.pi / 180
            radius = 30 + (freq * 0.3)
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            points.append([x, y])
        
        for i in range(len(points)):
            for j in range(i+1, len(points)):
                dist = np.sqrt((points[i][0] - points[j][0])**2 + (points[i][1] - points[j][1])**2)
                if dist < 60:
                    fig.add_trace(go.Scatter(
                        x=[points[i][0], points[j][0]],
                        y=[points[i][1], points[j][1]],
                        mode='lines',
                        line=dict(color='rgba(255,255,255,0.2)', width=1),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
    
    sequence_length = genetic_profile['sequence_length']
    fig.update_layout(
        title=f"Mapa Genético - Longitud: {sequence_length:,} nucleótidos",
        xaxis=dict(visible=False, range=[-100, 100]),
        yaxis=dict(visible=False, range=[-100, 100]),
        showlegend=False,
        plot_bgcolor='black',
        paper_bgcolor='black',
        width=800,
        height=600
    )
    
    return fig

def generar_visualizacion(seq_record, style='voronoi', theme='scientific'):
    """Crea visualización única basada en patrones genéticos específicos"""
    
    secuencia = str(seq_record.seq).upper()
    
    # Análisis profundo de características genéticas únicas
    genetic_profile = analizar_perfil_genetico_unico(secuencia, seq_record.id)
    
    if not genetic_profile:
        # Fallback simple
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(size=20, color='red')))
        fig.update_layout(title="Error: No se pudo analizar la secuencia")
        return fig, 0
    
    # Crear visualización específica según el perfil genético
    fig = crear_arte_basado_en_perfil(secuencia, genetic_profile, theme)
    
    # Calcular GC content
    gc_content = gc_fraction(seq_record.seq) * 100
    
    return fig, gc_content

def create_custom_loading_animation(message="Generando arte genético", subtitle="Analizando secuencia de ADN"):
    """Crea una animación de carga personalizada"""
    return f"""
    <div style="text-align: center; padding: 20px;">
        <div style="color: #00ff88; font-size: 18px; margin-bottom: 10px;">{message}</div>
        <div style="color: #cccccc; font-size: 14px; margin-bottom: 20px;">{subtitle}</div>
        <div style="display: inline-block;">
            <div style="width: 40px; height: 40px; border: 4px solid #333; border-top: 4px solid #00ff88; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        </div>
        <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
    </div>
    """

def mostrar_estadisticas_secuencia(seq_record, gc_content, genetic_profile):
    """Muestra estadísticas detalladas de la secuencia"""
    
    secuencia = str(seq_record.seq)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Longitud", f"{len(secuencia):,} bp")
        st.metric("GC Content", f"{gc_content:.1f}%")
    
    with col2:
        base_ratios = genetic_profile['base_ratios']
        st.metric("Adenina (A)", f"{base_ratios['A']:.1%}")
        st.metric("Timina (T)", f"{base_ratios['T']:.1%}")
    
    with col3:
        st.metric("Citosina (C)", f"{base_ratios['C']:.1%}")
        st.metric("Guanina (G)", f"{base_ratios['G']:.1%}")
    
    # Información adicional
    st.subheader("Análisis Genético")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Patrones de Repetición:**")
        repeat_patterns = genetic_profile['repeat_patterns']
        if repeat_patterns:
            for length_key, patterns in list(repeat_patterns.items())[:3]:
                if patterns:
                    most_common = max(patterns.items(), key=lambda x: x[1])
                    st.write(f"- Patrón {length_key}: {most_common[0]} ({most_common[1]} veces)")
        else:
            st.write("No se detectaron patrones repetitivos significativos")
    
    with col2:
        st.write("**Skew Genético:**")
        st.write(f"- GC Skew: {genetic_profile['gc_skew']:.3f}")
        st.write(f"- AT Skew: {genetic_profile['at_skew']:.3f}")
        
        st.write("**Distribución Posicional:**")
        avg_gc = np.mean([p['gc_content'] for p in genetic_profile['position_profile']])
        st.write(f"- GC promedio por segmento: {avg_gc:.1%}")

def main():
    # Header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1a1a2e, #16213e, #0f3460); padding: 30px; border-radius: 15px; margin-bottom: 30px; text-align: center;">
        <h1 style="color: #00ff88; margin-bottom: 10px; font-size: 2.5em;">🧬 DNA Art Generator</h1>
        <p style="color: #cccccc; font-size: 1.2em; margin-bottom: 0;">
            Convierte secuencias genéticas reales en arte único mediante análisis bioinformático
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Contenido principal - búsqueda única
    st.markdown("### 🎯 Generador de Arte Genético")
    
    # Crear columnas para la búsqueda
    col1, col2 = st.columns([3, 1])
    
    with col1:
        organism_input = st.text_input(
            "Nombre del animal:",
            placeholder="ej: perro, gato, león, delfín, águila, tigre",
            help="Introduce el nombre común del animal en español o inglés"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Espaciado
        search_button = st.button("🔍 Buscar", type="secondary")
    
    # Mostrar sugerencias cuando se escribe
    if organism_input and len(organism_input) > 2:
        search_engine = AnimalSearchEngine()
        suggestions = search_engine.search_comprehensive(organism_input.lower())
        
        if suggestions:
            st.markdown("**Sugerencias encontradas:**")
            
            # Mostrar sugerencias en columnas
            cols = st.columns(3)
            for i, suggestion in enumerate(suggestions[:6]):
                with cols[i % 3]:
                    if st.button(
                        f"🔬 {suggestion['scientific_name']}", 
                        key=f"suggest_{i}_{suggestion['scientific_name']}"
                    ):
                        organism_input = suggestion['scientific_name']
                        st.session_state.selected_organism = suggestion['scientific_name']
                        st.rerun()
        else:
            # Buscar sugerencias similares
            similar = search_engine.suggest_similar_names(organism_input.lower())
            if similar:
                st.markdown("**¿Quisiste decir?**")
                cols = st.columns(3)
                for i, name in enumerate(similar[:3]):
                    with cols[i]:
                        if st.button(f"💡 {name}", key=f"similar_{i}_{name}"):
                            organism_input = name
                            st.session_state.selected_organism = name
                            st.rerun()
    
    # Botón de generación
    if st.button("🚀 Generar Arte Genético", type="primary", use_container_width=True) or search_button:
        if not organism_input:
            st.warning("Por favor, introduce el nombre de un animal.")
            st.stop()
        
        seq_record = None
        organism_name = ""
        
        log_search(organism_input, user_session=st.session_state.session_id)
        
        loading_placeholder = st.empty()
        loading_placeholder.markdown(
            create_custom_loading_animation(
                "Buscando animal",
                "Convirtiendo nombre común a científico"
            ),
            unsafe_allow_html=True
        )
        
        # Buscar nombre científico usando el motor de búsqueda
        try:
            search_engine = AnimalSearchEngine()
            suggestions = search_engine.search_comprehensive(organism_input.lower())
            
            if suggestions:
                # Usar la primera sugerencia más relevante
                scientific_name = suggestions[0]['scientific_name']
                
                loading_placeholder.markdown(
                    create_custom_loading_animation(
                        "Conectando con NCBI GenBank",
                        f"Obteniendo secuencia de {scientific_name}"
                    ),
                    unsafe_allow_html=True
                )
                
                seq_record = obtener_secuencia(scientific_name)
                organism_name = scientific_name
                loading_placeholder.empty()
                
                st.success(f"Encontrado: {scientific_name}")
                
            else:
                # Intentar búsqueda directa si no hay sugerencias
                loading_placeholder.markdown(
                    create_custom_loading_animation(
                        "Búsqueda directa en NCBI",
                        "Probando con el nombre proporcionado"
                    ),
                    unsafe_allow_html=True
                )
                
                seq_record = obtener_secuencia(organism_input)
                organism_name = organism_input
                loading_placeholder.empty()
            
        except Exception as e:
            loading_placeholder.empty()
            st.error(f"No se pudo encontrar el animal '{organism_input}'.")
            
            # Mostrar sugerencias de nombres similares
            try:
                search_engine = AnimalSearchEngine()
                similar = search_engine.suggest_similar_names(organism_input.lower())
                if similar:
                    st.write("¿Quisiste decir?")
                    cols = st.columns(3)
                    for i, name in enumerate(similar[:3]):
                        with cols[i]:
                            if st.button(f"{name}", key=f"error_similar_{i}_{name}"):
                                st.session_state.selected_organism = name
                                st.rerun()
            except:
                pass
            
            log_search(organism_input, successful=False, error_message=str(e), user_session=st.session_state.session_id)
            st.stop()
            
        # Procesar secuencia obtenida
        if seq_record:
            st.success(f"✅ Secuencia obtenida: {seq_record.description[:80]}...")
            
            # Guardar en base de datos
            secuencia = str(seq_record.seq).upper()
            gc_content = gc_fraction(seq_record.seq) * 100
            base_counts = {
                'A': secuencia.count('A'),
                'T': secuencia.count('T'),
                'C': secuencia.count('C'),
                'G': secuencia.count('G'),
                'N': secuencia.count('N')
            }
            
            save_dna_sequence(organism_input, seq_record, gc_content, base_counts)
            
            # Animación de carga para generación de arte
            art_loading_placeholder = st.empty()
            art_loading_placeholder.markdown(
                create_custom_loading_animation(
                    "Generando Arte Genético",
                    "Aplicando algoritmos de análisis genético"
                ), 
                unsafe_allow_html=True
            )
            
            fig, gc = generar_visualizacion(seq_record, theme='scientific')
            genetic_profile = analizar_perfil_genetico_unico(secuencia, seq_record.id)
            art_loading_placeholder.empty()
            
            # Mostrar arte generado
            st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar estadísticas
            st.markdown("### 📊 Análisis de la Secuencia")
            mostrar_estadisticas_secuencia(seq_record, gc, genetic_profile)
            
            # Marcar búsqueda como exitosa
            log_search(organism_input, successful=True, user_session=st.session_state.session_id)

if __name__ == "__main__":
    main()