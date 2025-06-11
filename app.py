import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from Bio import Entrez, SeqIO
from Bio.SeqUtils import gc_fraction
import io
import matplotlib.pyplot as plt
import requests
import random
from database import save_dna_sequence, log_search, get_popular_organisms, get_recent_sequences
from species_catalog import get_species_info, get_featured_categories, suggest_search_terms
from animal_search import AnimalSearchEngine
from blockchain_nft import DNANFTManager
import uuid

# Configuración inicial
st.set_page_config(
    page_title="GeneticFrames - Arte Genético NFT",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para fondo elegante y misterioso
st.markdown("""
<style>
    /* Fondo principal con gradiente animado */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a, #1a1a2e, #16213e, #0f0f0f);
        background-size: 400% 400%;
        animation: gradientShift 20s ease infinite;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Sidebar elegante */
    .css-1d391kg {
        background: linear-gradient(180deg, #0f0f0f, #1a1a1a, #0d0d0d);
        border-right: 1px solid #333;
    }
    
    /* Contenedor principal */
    .main .block-container {
        background: rgba(15, 15, 15, 0.8);
        border-radius: 15px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        padding: 2rem;
        margin-top: 1rem;
    }
    
    /* Títulos con efecto brillante */
    h1, h2, h3 {
        color: #ffffff;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
    }
    
    /* Botones con efecto hover */
    .stButton > button {
        background: linear-gradient(45deg, #1a1a2e, #16213e);
        border: 1px solid #00ff88;
        border-radius: 10px;
        color: white;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #00ff88, #16213e);
        box-shadow: 0 5px 15px rgba(0, 255, 136, 0.4);
        transform: translateY(-2px);
    }
    
    /* Métricas con fondo translúcido */
    [data-testid="metric-container"] {
        background: rgba(26, 26, 26, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 1rem;
        backdrop-filter: blur(5px);
    }
    
    /* Expanders con estilo */
    .streamlit-expanderHeader {
        background: rgba(26, 26, 26, 0.8);
        border-radius: 8px;
        border: 1px solid rgba(0, 255, 136, 0.3);
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        background: rgba(26, 26, 26, 0.8);
        border: 1px solid #00ff88;
        border-radius: 8px;
        color: white;
    }
    
    /* Selectbox */
    .stSelectbox > div > div > select {
        background: rgba(26, 26, 26, 0.8);
        border: 1px solid #00ff88;
        color: white;
    }
    
    /* Contenedor de partículas ADN */
    #dna-particles {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        pointer-events: none;
        overflow: hidden;
    }
    
    /* Partículas individuales tipo ADN */
    .dna-particle {
        position: absolute;
        width: 4px;
        height: 4px;
        background: rgba(0, 255, 136, 0.6);
        border-radius: 50%;
        animation: float 15s infinite linear;
    }
    
    .dna-particle::before {
        content: '';
        position: absolute;
        width: 2px;
        height: 20px;
        background: rgba(0, 255, 136, 0.3);
        left: 1px;
        top: -8px;
        border-radius: 1px;
    }
    
    .dna-particle.adenine {
        background: rgba(255, 68, 68, 0.6);
        box-shadow: 0 0 6px rgba(255, 68, 68, 0.4);
    }
    
    .dna-particle.thymine {
        background: rgba(68, 68, 255, 0.6);
        box-shadow: 0 0 6px rgba(68, 68, 255, 0.4);
    }
    
    .dna-particle.cytosine {
        background: rgba(68, 255, 68, 0.6);
        box-shadow: 0 0 6px rgba(68, 255, 68, 0.4);
    }
    
    .dna-particle.guanine {
        background: rgba(255, 255, 68, 0.6);
        box-shadow: 0 0 6px rgba(255, 255, 68, 0.4);
    }
    
    @keyframes float {
        from {
            transform: translateY(100vh) rotate(0deg);
            opacity: 0;
        }
        10% {
            opacity: 1;
        }
        90% {
            opacity: 1;
        }
        to {
            transform: translateY(-20px) rotate(360deg);
            opacity: 0;
        }
    }
    
    /* Conexiones entre partículas */
    .dna-connection {
        position: absolute;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 255, 136, 0.2), transparent);
        animation: pulse 3s ease-in-out infinite;
        pointer-events: none;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 0.2; }
        50% { opacity: 0.6; }
    }
</style>
""", unsafe_allow_html=True)

# Sistema de partículas ADN animadas
st.markdown("""
<div id="dna-particles"></div>

<script>
class DNAParticleSystem {
    constructor() {
        this.container = document.getElementById('dna-particles');
        this.particles = [];
        this.connections = [];
        this.nucleotides = ['adenine', 'thymine', 'cytosine', 'guanine'];
        this.maxParticles = 50;
        this.init();
    }
    
    init() {
        if (!this.container) {
            setTimeout(() => this.init(), 100);
            return;
        }
        this.createParticles();
        this.animateConnections();
    }
    
    createParticles() {
        setInterval(() => {
            if (this.particles.length < this.maxParticles) {
                this.addParticle();
            }
        }, 800);
    }
    
    addParticle() {
        const particle = document.createElement('div');
        const nucleotide = this.nucleotides[Math.floor(Math.random() * this.nucleotides.length)];
        
        particle.className = `dna-particle ${nucleotide}`;
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 5 + 's';
        particle.style.animationDuration = (12 + Math.random() * 8) + 's';
        
        this.container.appendChild(particle);
        this.particles.push(particle);
        
        // Remover partícula cuando termine la animación
        setTimeout(() => {
            if (particle.parentNode) {
                particle.parentNode.removeChild(particle);
                this.particles = this.particles.filter(p => p !== particle);
            }
        }, 20000);
    }
    
    animateConnections() {
        setInterval(() => {
            if (this.particles.length >= 2) {
                this.createConnection();
            }
        }, 2000);
    }
    
    createConnection() {
        const particle1 = this.particles[Math.floor(Math.random() * this.particles.length)];
        const particle2 = this.particles[Math.floor(Math.random() * this.particles.length)];
        
        if (particle1 === particle2) return;
        
        const rect1 = particle1.getBoundingClientRect();
        const rect2 = particle2.getBoundingClientRect();
        
        const distance = Math.sqrt(
            Math.pow(rect2.left - rect1.left, 2) + 
            Math.pow(rect2.top - rect1.top, 2)
        );
        
        if (distance < 200) {
            const connection = document.createElement('div');
            connection.className = 'dna-connection';
            
            const angle = Math.atan2(rect2.top - rect1.top, rect2.left - rect1.left);
            
            connection.style.left = rect1.left + 'px';
            connection.style.top = rect1.top + 'px';
            connection.style.width = distance + 'px';
            connection.style.transform = `rotate(${angle}rad)`;
            connection.style.transformOrigin = '0 0';
            
            this.container.appendChild(connection);
            
            setTimeout(() => {
                if (connection.parentNode) {
                    connection.parentNode.removeChild(connection);
                }
            }, 3000);
        }
    }
}

// Inicializar sistema de partículas cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    new DNAParticleSystem();
});

// También inicializar después de un delay para asegurar que Streamlit haya terminado
setTimeout(() => {
    if (!window.dnaParticleSystemInitialized) {
        new DNAParticleSystem();
        window.dnaParticleSystemInitialized = true;
    }
}, 2000);
</script>
""", unsafe_allow_html=True)

# Temas de colores predefinidos
COLOR_THEMES = {
    'scientific': {'A': '#FF6B6B', 'T': '#4ECDC4', 'C': '#45B7D1', 'G': '#96CEB4', 'N': '#FFEAA7'},
    'ocean': {'A': '#0077BE', 'T': '#00A8CC', 'C': '#87CEEB', 'G': '#4682B4', 'N': '#E0F6FF'},
    'sunset': {'A': '#FF4500', 'T': '#FF6347', 'C': '#FFB347', 'G': '#FFA07A', 'N': '#FFEFD5'},
    'forest': {'A': '#228B22', 'T': '#32CD32', 'C': '#90EE90', 'G': '#98FB98', 'N': '#F0FFF0'},
    'cosmic': {'A': '#9370DB', 'T': '#8A2BE2', 'C': '#DA70D6', 'G': '#DDA0DD', 'N': '#E6E6FA'}
}

def limpiar_nombre_cientifico(nombre):
    """Limpia nombre científico removiendo autores y años para búsqueda en NCBI"""
    import re
    nombre_limpio = re.sub(r'\s+\([^)]*\).*$', '', nombre)
    nombre_limpio = re.sub(r'\s+\d{4}.*$', '', nombre_limpio)
    return nombre_limpio.strip()

def obtener_secuencia(organismo):
    """Obtiene secuencia de ADN desde NCBI"""
    import os
    Entrez.email = os.getenv('ENTREZ_EMAIL', 'user@example.com')
    Entrez.api_key = os.getenv('NCBI_API_KEY')
    
    try:
        nombre_busqueda = limpiar_nombre_cientifico(organismo)
        
        handle = Entrez.esearch(db="nucleotide", term=f"{nombre_busqueda}[ORGN] AND complete genome", retmax=5)
        search_results = Entrez.read(handle)
        handle.close()
        
        id_list = search_results.get("IdList", []) if isinstance(search_results, dict) else []
        if not id_list:
            handle = Entrez.esearch(db="nucleotide", term=f"{nombre_busqueda}[ORGN]", retmax=10)
            search_results = Entrez.read(handle)
            handle.close()
            id_list = search_results.get("IdList", []) if isinstance(search_results, dict) else []
        
        if id_list:
            seq_id = id_list[0]
            
            handle = Entrez.efetch(db="nucleotide", id=seq_id, rettype="fasta", retmode="text")
            seq_record = SeqIO.read(io.StringIO(handle.read()), "fasta")
            handle.close()
            
            return seq_record
        else:
            return None
            
    except Exception as e:
        st.error(f"Error al obtener secuencia: {str(e)}")
        return None

def hsl_to_hex(h, s, l):
    """Convierte HSL a hexadecimal"""
    h = h / 360
    s = s / 100
    l = l / 100
    
    def hue_to_rgb(p, q, t):
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1/6: return p + (q - p) * 6 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
        return p
    
    if s == 0:
        r = g = b = l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)
    
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

def generar_paleta_dinamica(genetic_seed, base_theme):
    """Genera paleta de colores única basada en firmas genéticas"""
    if not genetic_seed:
        return COLOR_THEMES[base_theme]
    
    # Usar firmas genéticas para generar colores únicos
    fibonacci_hue = (genetic_seed.get('fibonacci_signature', 123456) % 360)
    prime_hue = (genetic_seed.get('prime_signature', 234567) % 360)
    euler_hue = (genetic_seed.get('euler_signature', 345678) % 360)
    fractal_hue = (genetic_seed.get('fractal_signature', 456789) % 360)
    
    unique_colors = {}
    base_colors = ['A', 'T', 'C', 'G', 'N']
    hues = [fibonacci_hue, prime_hue, euler_hue, fractal_hue, (fibonacci_hue + prime_hue) % 360]
    
    for i, base in enumerate(base_colors):
        saturation = 70 + (genetic_seed.get('catalan_signature', 0) % 30)
        lightness = 45 + (genetic_seed.get('taylor_signature', 0) % 25)
        hex_color = hsl_to_hex(hues[i], saturation, lightness)
        unique_colors[base] = hex_color
    
    return unique_colors

# ============ ARQUITECTURAS DE RENDER MODULARES ============

def render_fractal(secuencia, colors, genetic_seed):
    """Arquitectura fractal para secuencias con alta repetitividad"""
    fig = go.Figure()
    
    mandelbrot_iterations = (genetic_seed.get('fibonacci_signature', 100) % 50) + 20
    julia_constant = complex(
        (genetic_seed.get('prime_signature', 0) % 200 - 100) / 100,
        (genetic_seed.get('euler_signature', 0) % 200 - 100) / 100
    )
    
    x_range = np.linspace(-2, 2, 150)
    y_range = np.linspace(-2, 2, 150)
    
    fractal_data = []
    for i, x in enumerate(x_range):
        for j, y in enumerate(y_range):
            c = complex(x, y)
            z = julia_constant
            
            base_index = (i * len(y_range) + j) % len(secuencia)
            if base_index < len(secuencia):
                base = secuencia[base_index]
                iterations = {'A': 20, 'T': 30, 'C': 40, 'G': 50}.get(base, 25)
            else:
                iterations = 25
            
            escape_count = 0
            for _ in range(iterations):
                if abs(z) > 2:
                    break
                z = z*z + c
                escape_count += 1
            
            fractal_data.append([x, y, escape_count])
    
    x_vals = [d[0] for d in fractal_data]
    y_vals = [d[1] for d in fractal_data]
    z_vals = [d[2] for d in fractal_data]
    
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='markers',
        marker=dict(
            color=z_vals,
            colorscale='Viridis',
            size=1.5,
            opacity=0.8
        ),
        showlegend=False
    ))
    
    return fig

def render_cristal(secuencia, colors, genetic_seed):
    """Arquitectura cristalina para secuencias con alto GC content"""
    fig = go.Figure()
    
    simetria = (genetic_seed.get('fibonacci_signature', 0) % 8) + 4
    
    for eje in range(simetria):
        angle_base = (2 * np.pi * eje) / simetria
        
        x_coords, y_coords = [], []
        
        for i, base in enumerate(secuencia[:400]):
            distance = i * 0.8
            angle = angle_base + (i * 0.05)
            
            base_factor = {'A': 0.7, 'T': 0.9, 'C': 1.1, 'G': 1.3}.get(base, 1.0)
            
            x = np.cos(angle) * distance * base_factor
            y = np.sin(angle) * distance * base_factor
            
            x_coords.append(x)
            y_coords.append(y)
        
        color_key = list(colors.keys())[eje % len(colors)]
        fig.add_trace(go.Scatter(
            x=x_coords,
            y=y_coords,
            mode='lines+markers',
            line=dict(color=colors[color_key], width=2),
            marker=dict(size=2, symbol='diamond'),
            showlegend=False
        ))
    
    return fig

def render_glitch(secuencia, colors, genetic_seed):
    """Arquitectura glitch para secuencias con alta variabilidad"""
    fig = go.Figure()
    
    glitch_intensity = (genetic_seed.get('euler_signature', 0) % 100) / 50
    corruption_rate = max(5, (genetic_seed.get('fractal_signature', 0) % 30) + 10)
    
    for layer in range(6):
        x_coords, y_coords, colors_glitch = [], [], []
        
        for i, base in enumerate(secuencia[::corruption_rate]):
            x_base = i * 3
            y_base = layer * 60
            
            if base == 'A':
                x_glitch = x_base + (genetic_seed.get('fibonacci_signature', 0) % 40 - 20) * glitch_intensity / 50
                y_glitch = y_base + (genetic_seed.get('prime_signature', 0) % 20 - 10) * glitch_intensity / 50
                color = '#FF3366'
            elif base == 'T':
                x_glitch = x_base + (genetic_seed.get('prime_signature', 0) % 30 - 15) * glitch_intensity / 50
                y_glitch = y_base + (genetic_seed.get('euler_signature', 0) % 25 - 12) * glitch_intensity / 50
                color = '#33FF66'
            elif base == 'C':
                x_glitch = x_base + (genetic_seed.get('euler_signature', 0) % 35 - 17) * glitch_intensity / 50
                y_glitch = y_base + (genetic_seed.get('fractal_signature', 0) % 30 - 15) * glitch_intensity / 50
                color = '#3366FF'
            else:  # G
                x_glitch = x_base + (genetic_seed.get('fractal_signature', 0) % 45 - 22) * glitch_intensity / 50
                y_glitch = y_base + (genetic_seed.get('fibonacci_signature', 0) % 40 - 20) * glitch_intensity / 50
                color = '#FFFF33'
            
            x_coords.append(x_glitch)
            y_coords.append(y_glitch)
            colors_glitch.append(color)
        
        fig.add_trace(go.Scatter(
            x=x_coords,
            y=y_coords,
            mode='lines+markers',
            line=dict(width=8 - layer, color='rgba(255,255,255,0.1)'),
            marker=dict(color=colors_glitch, size=4),
            showlegend=False
        ))
    
    return fig

def render_neural(secuencia, colors, genetic_seed):
    """Arquitectura de red neuronal para alta entropía"""
    fig = go.Figure()
    
    num_neuronas = min(30, len(secuencia) // 30)
    num_capas = (genetic_seed.get('fibonacci_signature', 0) % 4) + 3
    
    neuronas = []
    for capa in range(num_capas):
        capa_neuronas = []
        for neurona in range(num_neuronas):
            x = capa * 120
            y = (neurona - num_neuronas/2) * 40
            
            seq_index = (capa * num_neuronas + neurona) % len(secuencia)
            base = secuencia[seq_index]
            activacion = {'A': 0.3, 'T': 0.5, 'C': 0.7, 'G': 0.9}.get(base, 0.5)
            
            capa_neuronas.append({'x': x, 'y': y, 'activation': activacion, 'base': base})
        neuronas.append(capa_neuronas)
    
    # Dibujar conexiones
    for i in range(len(neuronas) - 1):
        for n1 in neuronas[i]:
            for n2 in neuronas[i + 1]:
                peso = 0.15 if n1['base'] == n2['base'] else 0.05
                
                fig.add_trace(go.Scatter(
                    x=[n1['x'], n2['x']],
                    y=[n1['y'], n2['y']],
                    mode='lines',
                    line=dict(width=peso * 15, color='rgba(120,120,120,0.3)'),
                    showlegend=False
                ))
    
    # Dibujar neuronas
    for capa in neuronas:
        x_vals = [n['x'] for n in capa]
        y_vals = [n['y'] for n in capa]
        activations = [n['activation'] for n in capa]
        
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode='markers',
            marker=dict(
                size=[a * 25 + 8 for a in activations],
                color=activations,
                colorscale='Plasma',
                symbol='circle'
            ),
            showlegend=False
        ))
    
    return fig

def render_organico(secuencia, colors, genetic_seed):
    """Arquitectura orgánica por defecto - formas naturales"""
    fig = go.Figure()
    
    ramificaciones = (genetic_seed.get('prime_signature', 0) % 6) + 4
    crecimiento = (genetic_seed.get('fibonacci_signature', 0) % 100) / 200
    
    for rama in range(ramificaciones):
        angle_base = (2 * np.pi * rama) / ramificaciones
        
        x_coords, y_coords, sizes = [], [], []
        x, y = 0, 0
        
        for i, base in enumerate(secuencia[:300]):
            growth_factor = {'A': 0.9, 'T': 1.1, 'C': 1.3, 'G': 1.5}.get(base, 1.0)
            
            angle = angle_base + np.sin(i * 0.08) * 0.4
            step = growth_factor * (1.5 + crecimiento)
            
            x += np.cos(angle) * step
            y += np.sin(angle) * step
            
            x_coords.append(x)
            y_coords.append(y)
            sizes.append(growth_factor * 4)
        
        color_key = list(colors.keys())[rama % len(colors)]
        fig.add_trace(go.Scatter(
            x=x_coords,
            y=y_coords,
            mode='lines+markers',
            line=dict(
                color=colors[color_key],
                width=2.5,
                shape='spline'
            ),
            marker=dict(size=sizes, opacity=0.7),
            showlegend=False
        ))
    
    return fig

def analizar_perfil_genetico(secuencia):
    """Análisis genético para generar parámetros únicos de L-System"""
    
    # 1. Análisis de bases para axioma
    base_counts = {'A': 0, 'T': 0, 'C': 0, 'G': 0}
    for base in secuencia:
        if base in base_counts:
            base_counts[base] += 1
    
    total = sum(base_counts.values())
    if total == 0:
        return None
    
    # Proporciones de bases
    proporciones = {base: count/total for base, count in base_counts.items()}
    
    # 2. Patrones de dinucleótidos para reglas
    dinucleotidos = {}
    for i in range(len(secuencia) - 1):
        dinuc = secuencia[i:i+2]
        if len(dinuc) == 2 and all(base in 'ATCG' for base in dinuc):
            dinucleotidos[dinuc] = dinucleotidos.get(dinuc, 0) + 1
    
    # 3. Análisis de repeticiones para simetría
    repeticiones = 0
    for length in [3, 4, 5]:
        for i in range(len(secuencia) - length):
            patron = secuencia[i:i+length]
            if secuencia.count(patron) > 1:
                repeticiones += 1
    
    # 4. Variabilidad local para caos
    variabilidad = 0
    ventana = 50
    for i in range(0, len(secuencia) - ventana, ventana//2):
        segmento = secuencia[i:i+ventana]
        gc_local = (segmento.count('G') + segmento.count('C')) / len(segmento)
        variabilidad += abs(gc_local - 0.5)
    
    return {
        'proporciones': proporciones,
        'dinucleotidos': dinucleotidos,
        'repeticiones': repeticiones,
        'variabilidad': variabilidad,
        'longitud': len(secuencia)
    }

def generar_lsystem_parametros(perfil_genetico, genetic_seed):
    """Genera parámetros únicos para L-System basados en perfil genético"""
    
    props = perfil_genetico['proporciones']
    dinucs = perfil_genetico['dinucleotidos']
    repeticiones = perfil_genetico['repeticiones']
    variabilidad = perfil_genetico['variabilidad']
    
    # 1. AXIOMA: Base inicial única por especie
    axiomas_base = {
        'alta_gc': 'F[+F]F[-F]F',      # Estructuras simétricas para alto GC
        'alta_at': 'F[+F[-F]]',        # Ramificación asimétrica para alto AT
        'equilibrado': 'F[+F]F[-F][F]',  # Estructura balanceada
        'variable': 'F[++F][--F]F'     # Caótico para alta variabilidad
    }
    
    # Seleccionar axioma base
    if props['G'] + props['C'] > 0.6:
        axioma_base = axiomas_base['alta_gc']
    elif props['A'] + props['T'] > 0.6:
        axioma_base = axiomas_base['alta_at']
    elif variabilidad > 0.3:
        axioma_base = axiomas_base['variable']
    else:
        axioma_base = axiomas_base['equilibrado']
    
    # Modificar axioma con firma genética
    fibonacci_mod = genetic_seed.get('fibonacci_signature', 0) % 4
    if fibonacci_mod == 1:
        axioma = axioma_base + '[F]'
    elif fibonacci_mod == 2:
        axioma = 'F' + axioma_base
    elif fibonacci_mod == 3:
        axioma = axioma_base.replace('F', 'FF', 1)
    else:
        axioma = axioma_base
    
    # 2. REGLAS DE PRODUCCIÓN: Basadas en dinucleótidos más frecuentes
    reglas = {}
    dinucs_sorted = sorted(dinucs.items(), key=lambda x: x[1], reverse=True)
    
    # Regla principal F
    if len(dinucs_sorted) > 0:
        top_dinuc = dinucs_sorted[0][0]
        if top_dinuc in ['GC', 'CG']:
            reglas['F'] = 'FF[+F][-F]'  # Simetría para GC
        elif top_dinuc in ['AT', 'TA']:
            reglas['F'] = 'F[+F[+F]]'   # Asimetría para AT
        elif top_dinuc in ['AA', 'TT']:
            reglas['F'] = 'F[++F][F]'   # Repetición para purinas
        else:
            reglas['F'] = 'F[+F]F[-F]'  # Base balanceada
    else:
        reglas['F'] = 'F[+F]F[-F]'
    
    # Reglas adicionales basadas en otros dinucleótidos
    if len(dinucs_sorted) > 1:
        second_dinuc = dinucs_sorted[1][0]
        if 'G' in second_dinuc:
            reglas['+'] = '+F'
        if 'C' in second_dinuc:
            reglas['-'] = '-F'
    
    # 3. ÁNGULO: Basado en variabilidad y firmas genéticas
    prime_mod = genetic_seed.get('prime_signature', 0) % 180
    angulo_base = 25 + (variabilidad * 50)  # 25-75 grados base
    angulo = angulo_base + (prime_mod / 10)  # Modulación única
    
    # 4. ITERACIONES: Basado en complejidad genética
    euler_mod = genetic_seed.get('euler_signature', 0) % 6
    iteraciones = max(3, min(7, 4 + euler_mod + int(repeticiones / 100)))
    
    # 5. LONGITUD INICIAL
    fractal_mod = genetic_seed.get('fractal_signature', 0) % 50
    longitud_inicial = 20 + fractal_mod
    
    # 6. FACTOR DE REDUCCIÓN
    catalan_mod = genetic_seed.get('catalan_signature', 0) % 100
    factor_reduccion = 0.6 + (catalan_mod / 500)  # 0.6-0.8
    
    return {
        'axioma': axioma,
        'reglas': reglas,
        'angulo': angulo,
        'iteraciones': iteraciones,
        'longitud_inicial': longitud_inicial,
        'factor_reduccion': factor_reduccion,
        'perfil_tipo': f"GC:{props['G']+props['C']:.2f}_VAR:{variabilidad:.2f}"
    }

class LSystemEngine:
    """Motor L-System para generar árboles fractales únicos por especie"""
    
    def __init__(self, parametros):
        self.axioma = parametros['axioma']
        self.reglas = parametros['reglas']
        self.angulo = parametros['angulo']
        self.iteraciones = parametros['iteraciones']
        self.longitud = parametros['longitud_inicial']
        self.factor_reduccion = parametros['factor_reduccion']
        
    def generar_secuencia(self):
        """Genera la secuencia L-System aplicando las reglas"""
        secuencia = self.axioma
        
        for _ in range(self.iteraciones):
            nueva_secuencia = ""
            for simbolo in secuencia:
                if simbolo in self.reglas:
                    nueva_secuencia += self.reglas[simbolo]
                else:
                    nueva_secuencia += simbolo
            secuencia = nueva_secuencia
            
        return secuencia
    
    def interpretar_secuencia(self, secuencia_lsystem):
        """Interpreta la secuencia L-System en coordenadas de dibujo"""
        stack = []
        x, y = 0, 0
        angulo_actual = 90  # Empezar hacia arriba
        
        puntos = []
        lineas = []
        
        for simbolo in secuencia_lsystem:
            if simbolo == 'F':
                # Dibujar línea hacia adelante
                nuevo_x = x + self.longitud * np.cos(np.radians(angulo_actual))
                nuevo_y = y + self.longitud * np.sin(np.radians(angulo_actual))
                
                lineas.append({
                    'x1': x, 'y1': y,
                    'x2': nuevo_x, 'y2': nuevo_y,
                    'longitud': self.longitud
                })
                
                x, y = nuevo_x, nuevo_y
                puntos.append((x, y))
                
            elif simbolo == '+':
                # Rotar a la izquierda
                angulo_actual += self.angulo
                
            elif simbolo == '-':
                # Rotar a la derecha
                angulo_actual -= self.angulo
                
            elif simbolo == '[':
                # Guardar estado actual
                stack.append((x, y, angulo_actual, self.longitud))
                
            elif simbolo == ']':
                # Restaurar estado guardado
                if stack:
                    x, y, angulo_actual, self.longitud = stack.pop()
                    # Reducir longitud para ramas más pequeñas
                    self.longitud *= self.factor_reduccion
        
        return lineas, puntos

def crear_arte_fluido(secuencia, theme='scientific', genetic_seed=None):
    """Mapeo directo de nucleótidos a elementos gráficos únicos"""
    
    if not secuencia:
        return go.Figure()
    
    # Colores fijos para cada nucleótido
    nucleotide_colors = {
        'A': '#FF4444',  # Rojo - Adenina
        'T': '#4444FF',  # Azul - Timina  
        'C': '#44FF44',  # Verde - Citosina
        'G': '#FFFF44',  # Amarillo - Guanina
        'N': '#888888'   # Gris - Desconocido
    }
    
    # Elementos gráficos únicos por nucleótido
    nucleotide_elements = {
        'A': {'shape': 'circle', 'size': 8, 'symbol': 'circle'},
        'T': {'shape': 'triangle', 'size': 10, 'symbol': 'triangle-up'},
        'C': {'shape': 'square', 'size': 6, 'symbol': 'square'},
        'G': {'shape': 'diamond', 'size': 9, 'symbol': 'diamond'},
        'N': {'shape': 'cross', 'size': 5, 'symbol': 'x'}
    }
    
    fig = go.Figure()
    
    # Tomar muestra de la secuencia para visualización
    sample_size = min(2000, len(secuencia))
    sequence_sample = secuencia[:sample_size]
    
    # DEBUG: Mostrar composición
    composition = {base: sequence_sample.count(base) for base in 'ATCGN'}
    print(f"=== NUCLEOTIDE MAPPING ===")
    print(f"Sequence length: {len(sequence_sample)}")
    print(f"A: {composition['A']}, T: {composition['T']}")
    print(f"C: {composition['C']}, G: {composition['G']}")
    print("==========================")
    
    # MAPEO DIRECTO: cada nucleótido = posición específica
    for i, nucleotide in enumerate(sequence_sample):
        if nucleotide not in nucleotide_elements:
            continue
            
        element = nucleotide_elements[nucleotide]
        color = nucleotide_colors[nucleotide]
        
        # Posición basada en índice de la secuencia
        angle = (i * 360 / len(sequence_sample)) % 360
        
        # Radio basado en tipo de nucleótido
        radius_map = {'A': 50, 'T': 75, 'C': 100, 'G': 125, 'N': 25}
        radius = radius_map[nucleotide]
        
        # Coordenadas polares a cartesianas
        x = radius * np.cos(np.radians(angle))
        y = radius * np.sin(np.radians(angle))
        
        # Agregar elemento visual único
        fig.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='markers',
            marker=dict(
                color=color,
                size=element['size'],
                symbol=element['symbol'],
                opacity=0.7,
                line=dict(width=1, color='white')
            ),
            showlegend=False,
            hovertemplate=f'<b>{nucleotide}</b><br>Position: {i}<br>Angle: {angle:.1f}°<extra></extra>'
        ))
    
    # Conectar nucleótidos consecutivos con líneas
    for i in range(0, len(sequence_sample) - 1, 10):  # Cada 10 para no saturar
        nucleotide1 = sequence_sample[i]
        nucleotide2 = sequence_sample[i + 1] if i + 1 < len(sequence_sample) else nucleotide1
        
        if nucleotide1 in nucleotide_elements and nucleotide2 in nucleotide_elements:
            angle1 = (i * 360 / len(sequence_sample)) % 360
            angle2 = ((i + 1) * 360 / len(sequence_sample)) % 360
            
            radius1 = {'A': 50, 'T': 75, 'C': 100, 'G': 125, 'N': 25}[nucleotide1]
            radius2 = {'A': 50, 'T': 75, 'C': 100, 'G': 125, 'N': 25}[nucleotide2]
            
            x1 = radius1 * np.cos(np.radians(angle1))
            y1 = radius1 * np.sin(np.radians(angle1))
            x2 = radius2 * np.cos(np.radians(angle2))
            y2 = radius2 * np.sin(np.radians(angle2))
            
            # Color de línea basado en par de nucleótidos
            line_color = 'rgba(255,255,255,0.2)'
            if nucleotide1 == nucleotide2:
                line_color = 'rgba(255,255,255,0.4)'  # Líneas más visibles para repeticiones
            
            fig.add_trace(go.Scatter(
                x=[x1, x2],
                y=[y1, y2],
                mode='lines',
                line=dict(color=line_color, width=0.5),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Agregar círculos concéntricos para mostrar los diferentes radios
    for nucleotide, radius in [('A', 50), ('T', 75), ('C', 100), ('G', 125)]:
        theta = np.linspace(0, 2*np.pi, 100)
        x_circle = radius * np.cos(theta)
        y_circle = radius * np.sin(theta)
        
        fig.add_trace(go.Scatter(
            x=x_circle,
            y=y_circle,
            mode='lines',
            line=dict(
                color=nucleotide_colors[nucleotide],
                width=1,
                dash='dot'
            ),
            opacity=0.3,
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Configuración final
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='#000011',
        paper_bgcolor='#000011',
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return fig

def generar_visualizacion(seq_record, style='fluid', theme='scientific'):
    """Crea visualización artística avanzada del ADN"""
    
    secuencia = str(seq_record.seq).upper()
    
    # Crear semilla genética única
    genetic_seed = crear_semilla_genetica(secuencia, seq_record.id)
    
    if style == 'fluid':
        fig = crear_arte_fluido(secuencia, theme, genetic_seed)
    else:
        # Mantener visualización clásica como respaldo
        fig = crear_visualizacion_clasica(secuencia, seq_record, theme)
    
    # Calcular GC content
    gc_content = gc_fraction(seq_record.seq) * 100
    
    return fig, gc_content

def crear_semilla_genetica(secuencia, sequence_id):
    """Genera parámetros simples únicos basados en características básicas del ADN"""
    
    if not secuencia:
        return None
    
    # Análisis básico de composición
    base_counts = {'A': 0, 'T': 0, 'C': 0, 'G': 0}
    for base in secuencia:
        if base in base_counts:
            base_counts[base] += 1
    
    total = sum(base_counts.values())
    if total == 0:
        return None
    
    # Firmas simples basadas en la secuencia real
    gc_content = (base_counts['G'] + base_counts['C']) / total
    at_content = (base_counts['A'] + base_counts['T']) / total
    
    # Hash simple del sequence_id para reproducibilidad
    id_hash = hash(sequence_id) % 1000000
    
    # Análisis de dinucleótidos
    dinucs = {}
    for i in range(len(secuencia) - 1):
        dinuc = secuencia[i:i+2]
        if len(dinuc) == 2:
            dinucs[dinuc] = dinucs.get(dinuc, 0) + 1
    
    # Firma basada en el dinucleótido más común
    top_dinuc = max(dinucs.items(), key=lambda x: x[1])[0] if dinucs else 'AT'
    dinuc_signature = sum(ord(c) for c in top_dinuc) * 1000
    
    # Firmas simples
    simple_signature = int(gc_content * 1000000) + id_hash
    pattern_signature = dinuc_signature + (len(secuencia) % 10000)
    
    return {
        'fibonacci_signature': simple_signature % 1000000,
        'prime_signature': pattern_signature % 1000000,
        'catalan_signature': int(at_content * 1000000) % 1000000,
        'euler_signature': (id_hash * 7) % 1000000,
        'fractal_signature': (len(secuencia) * int(gc_content * 1000)) % 1000000,
        'complexity_score': min(10, len(set(secuencia[:100])))
    }

def crear_visualizacion_clasica(secuencia, seq_record, theme):
    """Visualización clásica mejorada"""
    fig = go.Figure()
    
    colors = COLOR_THEMES[theme]
    base_values = {'A': 1, 'T': 2, 'C': 3, 'G': 4, 'N': 0}
    
    x_coords = []
    y_coords = []
    colors_list = []
    
    for i, base in enumerate(secuencia[:1000]):
        x_coords.append(i)
        y_coords.append(base_values.get(base, 0))
        colors_list.append(colors.get(base, colors['N']))
    
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='lines+markers',
        line=dict(color='rgba(255,255,255,0.3)', width=1),
        marker=dict(color=colors_list, size=3),
        name="Secuencia ADN"
    ))
    
    fig.update_layout(
        title=f"Visualización Clásica: {seq_record.description[:50]}...",
        xaxis_title="Posición en la secuencia",
        yaxis_title="Valor de base",
        showlegend=False,
        height=500,
        template="plotly_dark"
    )
    
    return fig

def mostrar_estadisticas_secuencia(seq_record):
    """Muestra estadísticas detalladas de la secuencia"""
    secuencia = str(seq_record.seq).upper()
    
    # Contar bases
    base_counts = {
        'A': secuencia.count('A'),
        'T': secuencia.count('T'),
        'C': secuencia.count('C'),
        'G': secuencia.count('G'),
        'N': secuencia.count('N')
    }
    
    total_bases = sum(base_counts.values())
    gc_content = gc_fraction(seq_record.seq) * 100
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Longitud total", f"{total_bases:,}")
        st.metric("Contenido GC", f"{gc_content:.2f}%")
    
    with col2:
        st.metric("Adenina (A)", f"{base_counts['A']:,}")
        st.metric("Timina (T)", f"{base_counts['T']:,}")
    
    with col3:
        st.metric("Citosina (C)", f"{base_counts['C']:,}")
        st.metric("Guanina (G)", f"{base_counts['G']:,}")
    
    # Gráfico de distribución de bases
    fig_dist = go.Figure(data=[
        go.Bar(x=list(base_counts.keys()), y=list(base_counts.values()),
               marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
    ])
    
    fig_dist.update_layout(
        title="Distribución de Bases Nitrogenadas",
        xaxis_title="Base",
        yaxis_title="Cantidad",
        height=400,
        template="plotly_dark"
    )
    
    st.plotly_chart(fig_dist, use_container_width=True)
    
    return base_counts

# =============== INTERFAZ PRINCIPAL ===============

def main():
    # Configurar sesión
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    # Header principal con mejor diseño
    col_logo, col_title = st.columns([1, 4])
    
    with col_logo:
        st.markdown("""
        <div style="font-size: 4rem; text-align: center; margin-top: 10px;">
            🧬
        </div>
        """, unsafe_allow_html=True)
    
    with col_title:
        st.markdown("""
        <div style="margin-top: 15px;">
            <h1 style="margin-bottom: 0; color: #ffffff; text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);">
                GeneticFrames
            </h1>
            <p style="font-size: 1.2rem; color: #aaaaaa; margin-top: 5px; font-style: italic;">
                Plataforma de Arte Genético NFT • Análisis Bioinformático Avanzado
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Estilo de visualización
        art_style = st.selectbox(
            "Estilo de arte:",
            ['fluid', 'mandala', 'galaxy', 'classic'],
            index=0,
            help="Selecciona el algoritmo de visualización"
        )
        
        # Tema de colores
        color_theme = st.selectbox(
            "Tema de colores:",
            ['scientific', 'ocean', 'sunset', 'forest', 'cosmic'],
            help="Paleta de colores base (se modifica algorítmicamente por ADN)"
        )
        
        st.divider()
        
        # Buscador de animales
        st.subheader("🔍 Buscar Especies")
        search_engine = AnimalSearchEngine()
        
        search_query = st.text_input(
            "Nombre común del animal:",
            placeholder="ej: delfín, orca, águila"
        )
        
        if search_query:
            suggestions = search_engine.search_comprehensive(search_query)
            
            if suggestions:
                st.write("**Sugerencias encontradas:**")
                for suggestion in suggestions[:5]:
                    if st.button(f"🔬 {suggestion['scientific_name']}", key=f"suggest_{suggestion['scientific_name']}"):
                        st.session_state.selected_organism = suggestion['scientific_name']
                        st.rerun()
            else:
                st.warning("No se encontraron coincidencias exactas")
                
                # Sugerencias por similitud
                similar = search_engine.suggest_similar_names(search_query)
                if similar:
                    st.write("**¿Quisiste decir?**")
                    for name in similar[:3]:
                        if st.button(f"💡 {name}", key=f"similar_{name}"):
                            st.session_state.selected_organism = name
                            st.rerun()
        
        st.divider()
        
        # Especies destacadas
        st.subheader("⭐ Especies Destacadas")
        try:
            featured = get_featured_categories()
            
            for category, species_list in featured.items():
                with st.expander(f"🏛️ {category}"):
                    if isinstance(species_list, list):
                        for species in species_list[:3]:
                            if st.button(f"🧬 {species}", key=f"featured_{species}"):
                                st.session_state.selected_organism = species
                                st.rerun()
        except Exception as e:
            st.write("Cargando especies destacadas...")
        
        st.divider()
        
        # Organimos populares
        st.subheader("📈 Populares")
        try:
            popular = get_popular_organisms(5)
            for org in popular:
                if st.button(f"🔥 {org.organism_name}", key=f"popular_{org.organism_name}"):
                    st.session_state.selected_organism = org.organism_name
                    st.rerun()
        except:
            st.write("Cargando organismos populares...")
    
    # Main content con pestañas organizadas
    tab1, tab2, tab3 = st.tabs(["🎯 Generador", "📊 Análisis", "🏆 Galería NFT"])
    
    with tab1:
        # Input principal mejorado
        st.markdown("""
        <div style="background: rgba(26, 26, 46, 0.8); padding: 20px; border-radius: 15px; margin-bottom: 20px;">
            <h3 style="color: #00ff88; margin-bottom: 15px;">🎯 Generador de Arte Genético</h3>
            <p style="color: #cccccc; margin-bottom: 0;">
                Transforma secuencias de ADN reales en arte único mediante algoritmos bioinformáticos avanzados
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Input de organismo mejorado
            selected_organism = st.session_state.get('selected_organism', '')
            organism_input = st.text_input(
                "Nombre científico del organismo:",
                value=selected_organism,
                placeholder="ej: Tursiops truncatus (delfín nariz de botella)",
                help="Introduce el nombre científico completo del organismo"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Espaciado
        
        # Botón de generación
        if st.button("🚀 Generar Arte Genético", type="primary", use_container_width=True):
            if organism_input:
                # Log de búsqueda
                log_search(organism_input, user_session=st.session_state.session_id)
                
                with st.spinner(f"Obteniendo secuencia genética de {organism_input}..."):
                    seq_record = obtener_secuencia(organism_input)
                
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
                    
                    with st.spinner("Generando visualización artística..."):
                        fig, gc = generar_visualizacion(seq_record, style=art_style, theme=color_theme)
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Mostrar estadísticas
                    with st.expander("📊 Estadísticas de la Secuencia", expanded=False):
                        base_counts = mostrar_estadisticas_secuencia(seq_record)
                    
                    # Información de especies
                    species_info = get_species_info(organism_input)
                    if species_info:
                        with st.expander("🦎 Información de la Especie", expanded=False):
                            st.write(f"**Estado de conservación:** {species_info.get('conservation_status', 'No disponible')}")
                            st.write(f"**Historia:** {species_info.get('story', 'No disponible')}")
                    
                    # Opciones NFT
                    with st.expander("🎨 Generar NFT", expanded=False):
                        st.write("**Crear NFT exclusivo de esta visualización genética**")
                        
                        wallet_address = st.text_input("Dirección de wallet:", placeholder="0x...")
                        
                        if st.button("💎 Crear NFT"):
                            nft_manager = DNANFTManager()
                            
                            if nft_manager.get_blockchain_status()['connected']:
                                with st.spinner("Preparando NFT..."):
                                    nft_package = nft_manager.prepare_nft_package(
                                        seq_record, organism_input, gc, base_counts, fig
                                    )
                                
                                if nft_package:
                                    st.success("✅ NFT preparado exitosamente!")
                                    st.json(nft_package['metadata'])
                                    
                                    if wallet_address:
                                        result = nft_manager.mint_nft(wallet_address, nft_package['metadata_uri'])
                                        if result:
                                            st.success(f"🎉 NFT minteado! TX: {result['transaction_hash']}")
                                        else:
                                            st.error("Error al mintear NFT")
                                else:
                                    st.error("Error preparando NFT")
                            else:
                                st.warning("⚠️ Blockchain no disponible. NFT se generará cuando se configure.")
                
                else:
                    st.error("❌ No se pudo obtener la secuencia. Verifica el nombre científico.")
                    log_search(organism_input, successful=False, 
                             error_message="Secuencia no encontrada", 
                             user_session=st.session_state.session_id)
            else:
                st.warning("⚠️ Por favor, introduce el nombre de un organismo.")
    
    with tab2:
        st.markdown("""
        <div style="background: rgba(26, 26, 46, 0.8); padding: 20px; border-radius: 15px; margin-bottom: 20px;">
            <h3 style="color: #00ff88; margin-bottom: 15px;">📊 Análisis Bioinformático</h3>
            <p style="color: #cccccc; margin-bottom: 0;">
                Dashboard de análisis genómico y estadísticas de la plataforma
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Panel de control dividido
        col_stats, col_activity = st.columns([1, 1])
        
        with col_stats:
            st.subheader("📈 Estadísticas Globales")
            try:
                from database import get_database_stats
                stats = get_database_stats()
                
                # Métricas en un grid
                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.metric("Secuencias Almacenadas", f"{stats['total_sequences']:,}")
                    st.metric("Organismos Únicos", f"{stats['unique_organisms']:,}")
                with metric_col2:
                    st.metric("Búsquedas Exitosas", f"{stats['successful_searches']:,}")
                    st.metric("Tasa de Éxito", f"{stats['success_rate']:.1f}%")
                
            except Exception as e:
                st.info("Inicializando estadísticas...")
        
        with col_activity:
            st.subheader("🔬 Actividad Reciente")
            try:
                recent = get_recent_sequences(8)
                if recent:
                    for seq in recent:
                        with st.container():
                            col_name, col_metrics = st.columns([2, 1])
                            with col_name:
                                st.markdown(f"**🧬 {seq.organism_name[:35]}**")
                                st.caption(f"ID: {seq.ncbi_id}")
                            with col_metrics:
                                st.metric("GC%", f"{seq.gc_content:.1f}")
                                st.caption(f"Longitud: {seq.sequence_length:,}")
                            st.divider()
                else:
                    st.info("No hay actividad reciente")
            except Exception as e:
                st.info("Cargando actividad...")
        
        # Análisis de distribución de especies
        st.subheader("🌍 Distribución de Especies")
        try:
            popular = get_popular_organisms(10)
            if popular:
                # Crear gráfico de barras
                import plotly.express as px
                organisms = [getattr(org, 'organism_name', str(org))[:30] for org in popular]
                counts = [getattr(org, 'accessed_count', 0) for org in popular]
                
                fig_pop = px.bar(
                    x=counts, 
                    y=organisms,
                    orientation='h',
                    title="Especies Más Consultadas",
                    color=counts,
                    color_continuous_scale="Viridis"
                )
                fig_pop.update_layout(
                    height=400,
                    template="plotly_dark",
                    showlegend=False
                )
                st.plotly_chart(fig_pop, use_container_width=True)
            else:
                st.info("Generando datos de distribución...")
        except Exception as e:
            st.info("Cargando análisis de distribución...")
    
    with tab3:
        st.markdown("""
        <div style="background: rgba(26, 26, 46, 0.8); padding: 20px; border-radius: 15px; margin-bottom: 20px;">
            <h3 style="color: #00ff88; margin-bottom: 15px;">🏆 Galería NFT y Colecciones</h3>
            <p style="color: #cccccc; margin-bottom: 0;">
                Explora colecciones exclusivas y gestiona tus NFTs genéticos
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Secciones de la galería
        nft_tab1, nft_tab2, nft_tab3 = st.tabs(["🔥 Destacados", "🦕 Extintos", "⚙️ Blockchain"])
        
        with nft_tab1:
            st.subheader("Arte Genético Destacado")
            
            # Grid de especies destacadas para NFT
            featured_cols = st.columns(3)
            featured_species = [
                ("Tursiops truncatus", "Delfín Nariz de Botella", "🐬"),
                ("Panthera leo", "León Africano", "🦁"),
                ("Aquila chrysaetos", "Águila Real", "🦅")
            ]
            
            for i, (scientific, common, emoji) in enumerate(featured_species):
                with featured_cols[i % 3]:
                    st.markdown(f"""
                    <div style="background: rgba(15, 15, 15, 0.9); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid rgba(0, 255, 136, 0.3);">
                        <div style="font-size: 2rem;">{emoji}</div>
                        <h4 style="color: #00ff88; margin: 10px 0;">{common}</h4>
                        <p style="color: #aaa; font-size: 0.9rem; font-style: italic;">{scientific}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Generar NFT {common}", key=f"nft_{scientific}"):
                        st.session_state.selected_organism = scientific
                        st.switch_page("main")
        
        with nft_tab2:
            st.subheader("Colección Especies Extintas")
            
            try:
                from extinct_species_catalog import get_collection_tiers
                collection_tiers = get_collection_tiers()
                
                for tier_name, species_list in collection_tiers.items():
                    with st.expander(f"🏛️ {tier_name}"):
                        st.write(f"**{len(species_list)} especies en esta colección**")
                        
                        for species in species_list[:5]:  # Mostrar primeras 5
                            col_spec, col_btn = st.columns([3, 1])
                            with col_spec:
                                st.write(f"🦕 **{species}**")
                            with col_btn:
                                if st.button("NFT", key=f"extinct_{species}"):
                                    st.session_state.selected_organism = species
                                    st.switch_page("main")
                        
                        if len(species_list) > 5:
                            st.caption(f"... y {len(species_list) - 5} especies más")
            
            except Exception as e:
                st.info("Cargando colecciones de especies extintas...")
        
        with nft_tab3:
            st.subheader("Estado del Blockchain")
            
            try:
                nft_manager = DNANFTManager()
                status = nft_manager.get_blockchain_status()
                
                if status['connected']:
                    st.success("✅ Blockchain conectado")
                    st.write(f"**Red:** {status['network']}")
                    st.write(f"**Dirección del contrato:** `{status.get('contract_address', 'No configurado')}`")
                else:
                    st.warning("⚠️ Blockchain no configurado")
                    st.info("Para habilitar NFTs, configura las claves API de blockchain en la configuración.")
                
            except Exception as e:
                st.error("Error al verificar estado del blockchain")
            
            # Configuración rápida
            st.subheader("Configuración Rápida")
            
            st.markdown("""
            **Para habilitar funcionalidad completa de NFT:**
            1. Configura una wallet de Ethereum
            2. Obtén claves API de Infura
            3. Configura cuenta de Pinata para IPFS
            4. Despliega el contrato ERC-721
            """)
            
            if st.button("📋 Guía de Configuración Completa"):
                st.info("Consulta el archivo DEPLOYMENT_GUIDE.md para instrucciones detalladas.")

if __name__ == "__main__":
    main()