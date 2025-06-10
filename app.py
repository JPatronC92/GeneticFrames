import streamlit as st
from Bio import Entrez, SeqIO
from Bio.SeqUtils import gc_fraction
import plotly.express as px
import plotly.graph_objects as go
import io
import os
import numpy as np
import math
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
    'T': {'color': '#4ECDC4', 'size': 10, 'symbol': 'diamond', 'frequency': 494},    # Timina - Turquesa
    'C': {'color': '#45B7D1', 'size': 8, 'symbol': 'square', 'frequency': 523},      # Citosina - Azul cielo
    'G': {'color': '#96CEB4', 'size': 14, 'symbol': 'star', 'frequency': 587},       # Guanina - Verde menta
    'N': {'color': '#FECA57', 'size': 6, 'symbol': 'x', 'frequency': 330}            # Desconocido - Amarillo dorado
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

def crear_espiral_dna(secuencia, theme='scientific'):
    """Crea una visualización en espiral de doble hélice del ADN"""
    
    max_length = min(len(secuencia), 1000)
    sequence_segment = secuencia[:max_length]
    
    # Parámetros de la espiral
    turns = max_length / 40  # Una vuelta completa cada 40 bases
    height_per_turn = 20
    radius = 8
    
    # Generar coordenadas para las dos hebras
    angles = np.linspace(0, turns * 2 * math.pi, max_length)
    x1 = radius * np.cos(angles)
    y1 = radius * np.sin(angles)
    z1 = np.linspace(0, turns * height_per_turn, max_length)
    
    # Segunda hebra (complementaria)
    x2 = radius * np.cos(angles + math.pi)
    y2 = radius * np.sin(angles + math.pi)
    z2 = z1.copy()
    
    # Colores según el tema
    colors = COLOR_THEMES[theme]
    
    fig = go.Figure()
    
    # Primera hebra
    for i, base in enumerate(sequence_segment):
        if base not in colors:
            base = 'N'
        
        fig.add_trace(go.Scatter3d(
            x=[x1[i]], y=[y1[i]], z=[z1[i]],
            mode='markers',
            marker=dict(
                size=8,
                color=colors[base],
                opacity=0.8
            ),
            name=f'Hebra 1: {base}',
            showlegend=False,
            hovertemplate=f"<b>Posición:</b> {i}<br><b>Base:</b> {base}<extra></extra>"
        ))
    
    # Conexiones entre hebras (enlaces de hidrógeno)
    for i in range(0, max_length, 5):  # Mostrar cada 5 enlaces para claridad
        fig.add_trace(go.Scatter3d(
            x=[x1[i], x2[i]], y=[y1[i], y2[i]], z=[z1[i], z2[i]],
            mode='lines',
            line=dict(color='rgba(200,200,200,0.3)', width=2),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Segunda hebra (bases complementarias)
    complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C', 'N': 'N'}
    for i, base in enumerate(sequence_segment):
        comp_base = complement.get(base, 'N')
        
        fig.add_trace(go.Scatter3d(
            x=[x2[i]], y=[y2[i]], z=[z2[i]],
            mode='markers',
            marker=dict(
                size=8,
                color=colors[comp_base],
                opacity=0.8
            ),
            name=f'Hebra 2: {comp_base}',
            showlegend=False,
            hovertemplate=f"<b>Posición:</b> {i}<br><b>Base:</b> {comp_base}<extra></extra>"
        ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Secuencia",
            bgcolor='rgba(0,0,0,0)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
        ),
        title="Estructura de Doble Hélice del ADN",
        height=600,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

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

def generar_visualizacion(seq_record, style='spiral', theme='scientific'):
    """Crea visualización artística avanzada del ADN"""
    secuencia = str(seq_record.seq).upper()
    gc = gc_fraction(secuencia) * 100
    
    if style == 'spiral':
        fig = crear_espiral_dna(secuencia, theme)
    elif style == 'circular':
        fig = crear_patron_circular(secuencia, theme)
    elif style == 'heatmap':
        fig = crear_mapa_calor_gc(secuencia)
    else:  # classic fallback
        fig = crear_visualizacion_clasica(secuencia, seq_record, theme)
    
    return fig, gc

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
        ["spiral", "circular", "classic", "heatmap"],
        format_func=lambda x: {
            "spiral": "🧬 Espiral 3D (Doble Hélice)",
            "circular": "⭕ Patrón Circular",
            "classic": "📊 Clásico Mejorado", 
            "heatmap": "🔥 Mapa de Calor GC"
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
