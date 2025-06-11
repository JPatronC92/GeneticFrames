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
    Entrez.email = "user@example.com"
    
    try:
        nombre_busqueda = limpiar_nombre_cientifico(organismo)
        
        handle = Entrez.esearch(db="nucleotide", term=f"{nombre_busqueda}[ORGN] AND complete genome", retmax=5)
        search_results = Entrez.read(handle)
        handle.close()
        
        if not search_results["IdList"]:
            handle = Entrez.esearch(db="nucleotide", term=f"{nombre_busqueda}[ORGN]", retmax=10)
            search_results = Entrez.read(handle)
            handle.close()
        
        if search_results["IdList"]:
            seq_id = search_results["IdList"][0]
            
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

def analizar_estructura_genomica(secuencia):
    """Análisis bioinformático profundo para determinar arquitectura de render"""
    
    # 1. Análisis de codones
    codones = {}
    for i in range(0, len(secuencia) - 2, 3):
        codon = secuencia[i:i+3]
        if len(codon) == 3:
            codones[codon] = codones.get(codon, 0) + 1
    
    # Diversidad de codones (Shannon entropy)
    total_codones = sum(codones.values())
    shannon_entropy = 0
    if total_codones > 0:
        for count in codones.values():
            if count > 0:
                p = count / total_codones
                shannon_entropy -= p * np.log2(p)
    
    # 2. Detección de motivos repetidos
    motivos = {}
    for length in [3, 6, 9, 12, 15]:
        for i in range(len(secuencia) - length + 1):
            motivo = secuencia[i:i+length]
            motivos[motivo] = motivos.get(motivo, 0) + 1
    
    # Calcular repetitividad
    motivos_repetidos = {k: v for k, v in motivos.items() if v >= 3}
    repetitividad = len(motivos_repetidos) / max(1, len(motivos))
    
    # 3. Análisis de composición
    gc_content = (secuencia.count('G') + secuencia.count('C')) / len(secuencia)
    at_content = (secuencia.count('A') + secuencia.count('T')) / len(secuencia)
    
    # 4. Variabilidad posicional
    variabilidad = 0
    window = 100
    if len(secuencia) > window:
        for i in range(0, len(secuencia) - window, window):
            ventana = secuencia[i:i+window]
            gc_ventana = (ventana.count('G') + ventana.count('C')) / len(ventana)
            variabilidad += abs(gc_ventana - gc_content)
        variabilidad /= max(1, (len(secuencia) // window))
    
    return {
        'shannon_entropy': shannon_entropy,
        'repetitividad': repetitividad,
        'gc_content': gc_content,
        'at_content': at_content,
        'variabilidad': variabilidad,
        'longitud': len(secuencia),
        'diversidad_codones': len(codones)
    }

def seleccionar_arquetipo_visual(analisis):
    """Selecciona arquitectura de render basada en análisis genómico"""
    
    gc = analisis['gc_content']
    repetitividad = analisis['repetitividad']
    shannon = analisis['shannon_entropy']
    variabilidad = analisis['variabilidad']
    
    # Lógica de selección de arquetipo
    if repetitividad > 0.3:
        return 'fractal'  # Alta repetición → fractales
    elif gc > 0.6:
        return 'cristal'  # GC alto → estructuras cristalinas simétricas
    elif variabilidad > 0.15:
        return 'glitch'   # Alta variación → arte caótico
    elif shannon > 3.5:
        return 'neural'   # Alta entropía → red neuronal
    else:
        return 'organico' # Por defecto → formas orgánicas

def crear_arte_fluido(secuencia, theme='scientific', genetic_seed=None):
    """Sistema de render modular basado en análisis genómico"""
    
    if not secuencia:
        return go.Figure()
    
    # Análisis bioinformático profundo
    analisis = analizar_estructura_genomica(secuencia)
    
    # Seleccionar arquitectura de render
    arquetipo = seleccionar_arquetipo_visual(analisis)
    
    # DEBUG: Mostrar análisis
    print(f"=== ANÁLISIS GENÓMICO ===")
    print(f"GC Content: {analisis['gc_content']:.3f}")
    print(f"Repetitividad: {analisis['repetitividad']:.3f}")
    print(f"Shannon Entropy: {analisis['shannon_entropy']:.3f}")
    print(f"Variabilidad: {analisis['variabilidad']:.3f}")
    print(f"ARQUETIPO SELECCIONADO: {arquetipo.upper()}")
    print("========================")
    
    # Generar paleta de colores única
    colors = generar_paleta_dinamica(genetic_seed, theme) if genetic_seed else {
        'A': '#FF6B6B', 'T': '#4ECDC4', 'C': '#45B7D1', 'G': '#96CEB4', 'N': '#FFEAA7'
    }
    
    # Ejecutar arquitectura específica
    if arquetipo == 'fractal':
        fig = render_fractal(secuencia, colors, genetic_seed)
    elif arquetipo == 'cristal':
        fig = render_cristal(secuencia, colors, genetic_seed)
    elif arquetipo == 'glitch':
        fig = render_glitch(secuencia, colors, genetic_seed)
    elif arquetipo == 'neural':
        fig = render_neural(secuencia, colors, genetic_seed)
    else:  # organico
        fig = render_organico(secuencia, colors, genetic_seed)
    
    # Configuración final
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='#000000',
        paper_bgcolor='#111111',
        xaxis=dict(visible=False),
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
    """Genera parámetros únicos usando teoremas matemáticos avanzados para diferenciar completamente cada secuencia"""
    
    if not secuencia:
        return None
    
    # 1. Análisis de secuencia de Fibonacci
    def fibonacci_encoding(seq):
        fib_signature = 0
        for i, base in enumerate(seq[:min(100, len(seq))]):
            base_val = {'A': 1, 'T': 1, 'C': 2, 'G': 3, 'N': 0}.get(base, 0)
            fib_pos = i % 20 + 1
            fib_number = 1 if fib_pos <= 2 else sum(fibonacci_sequence(fib_pos)[-2:])
            fib_signature += base_val * fib_number
        return fib_signature % 1000000
    
    def fibonacci_sequence(n):
        if n <= 0: return []
        elif n == 1: return [1]
        elif n == 2: return [1, 1]
        
        seq = [1, 1]
        for i in range(2, n):
            seq.append(seq[i-1] + seq[i-2])
        return seq
    
    # 2. Factorización de números primos única
    def prime_factorization_hash(seq):
        prime_signature = 1
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
        
        for i, base in enumerate(seq[:min(50, len(seq))]):
            base_power = {'A': 1, 'T': 2, 'C': 3, 'G': 4, 'N': 0}.get(base, 0)
            if base_power > 0:
                prime_idx = i % len(primes)
                prime_signature *= (primes[prime_idx] ** base_power)
                prime_signature = prime_signature % 1000000
        
        return prime_signature
    
    # 3. Números de Catalan aplicados a estructuras secundarias
    def catalan_analysis(seq):
        def catalan_number(n):
            if n <= 1: return 1
            catalan = [0] * (n + 1)
            catalan[0], catalan[1] = 1, 1
            
            for i in range(2, n + 1):
                for j in range(i):
                    catalan[i] += catalan[j] * catalan[i - 1 - j]
            return catalan[n]
        
        catalan_signature = 0
        gc_pairs = 0
        at_pairs = 0
        
        for i in range(0, len(seq) - 1, 2):
            if i + 1 < len(seq):
                pair = seq[i:i+2]
                if pair in ['GC', 'CG']: gc_pairs += 1
                elif pair in ['AT', 'TA']: at_pairs += 1
        
        structure_complexity = min(15, gc_pairs + at_pairs)
        catalan_signature = catalan_number(structure_complexity)
        
        return catalan_signature % 1000000
    
    # 4. Aproximación de Taylor para frecuencias de bases
    def taylor_approximation(seq):
        def factorial(n):
            return 1 if n <= 1 else n * factorial(n - 1)
        
        base_counts = {'A': 0, 'T': 0, 'C': 0, 'G': 0}
        for base in seq:
            if base in base_counts:
                base_counts[base] += 1
        
        total = sum(base_counts.values())
        if total == 0: return 123456
        
        taylor_signature = 0
        for base, count in base_counts.items():
            frequency = count / total
            # Expansión de Taylor para e^x alrededor de x=0
            terms = min(10, count // 10 + 1)
            exponential_approx = sum(
                (frequency ** n) / factorial(n) for n in range(terms)
            )
            base_multiplier = {'A': 1000, 'T': 2000, 'C': 3000, 'G': 4000}[base]
            taylor_signature += int(exponential_approx * base_multiplier)
        
        return taylor_signature % 1000000
    
    # 5. Transformada de Fourier discreta simplificada
    def fourier_transform_hash(seq):
        if len(seq) == 0: return 234567
        
        # Convertir secuencia a señal numérica
        signal = [{'A': 1, 'T': -1, 'C': 1j, 'G': -1j, 'N': 0}.get(base, 0) for base in seq[:64]]
        
        # DFT simplificada para los primeros componentes
        fourier_signature = 0
        N = len(signal)
        
        for k in range(min(8, N)):
            component = sum(
                signal[n] * np.exp(-2j * np.pi * k * n / N) 
                for n in range(N)
            )
            magnitude = abs(component)
            fourier_signature += int(magnitude * 1000)
        
        return fourier_signature % 1000000
    
    # 6. Distancias pitagóricas en espacio de características
    def pythagorean_distances(seq):
        if len(seq) < 4: return 345678
        
        # Dividir en cuartetos y calcular distancias
        quartets = [seq[i:i+4] for i in range(0, len(seq)-3, 4)]
        
        pythagorean_signature = 0
        for quartet in quartets[:20]:  # Primeros 20 cuartetos
            # Coordenadas en espacio 4D basadas en bases
            coords = []
            for base in quartet:
                coords.append({'A': 1, 'T': 2, 'C': 3, 'G': 4, 'N': 0}.get(base, 0))
            
            if len(coords) == 4:
                # Distancia euclidiana 4D
                distance = sum(coord ** 2 for coord in coords) ** 0.5
                pythagorean_signature += int(distance * 1000)
        
        return pythagorean_signature % 1000000
    
    # 7. Función totiente de Euler aplicada a motivos
    def euler_totient_analysis(seq):
        def gcd(a, b):
            while b: a, b = b, a % b
            return a
        
        def euler_totient(n):
            if n <= 1: return 1
            result = n
            p = 2
            while p * p <= n:
                if n % p == 0:
                    while n % p == 0: n //= p
                    result -= result // p
                p += 1
            if n > 1: result -= result // n
            return result
        
        # Analizar motivos de longitud 3
        motif_frequencies = {}
        for i in range(len(seq) - 2):
            motif = seq[i:i+3]
            if motif.replace('N', '') == motif:  # Excluir N's
                motif_frequencies[motif] = motif_frequencies.get(motif, 0) + 1
        
        euler_signature = 0
        for motif, freq in motif_frequencies.items():
            if freq > 1:
                euler_signature += euler_totient(freq)
        
        return euler_signature % 1000000
    
    # 8. Análisis de dimensión fractal simplificado
    def fractal_dimension_analysis(seq):
        if len(seq) < 10: return 456789
        
        # Box-counting simplificado
        fractal_signature = 0
        
        for scale in [2, 4, 8, 16]:
            if scale >= len(seq): break
            
            boxes_with_variation = 0
            for i in range(0, len(seq) - scale + 1, scale):
                segment = seq[i:i+scale]
                unique_bases = len(set(segment))
                if unique_bases > 1:
                    boxes_with_variation += 1
            
            if scale > 0:
                fractal_signature += int((boxes_with_variation / scale) * 10000)
        
        return fractal_signature % 1000000
    
    # 9. Números de Stirling de segunda especie
    def stirling_bell_analysis(seq):
        def stirling_second(n, k):
            if n == 0 and k == 0: return 1
            if n == 0 or k == 0: return 0
            if k > n: return 0
            
            # Aproximación para casos grandes
            if n > 15: return (k ** n) // (2 ** (k-1))
            
            # Recursión directa para casos pequeños
            return k * stirling_second(n-1, k) + stirling_second(n-1, k-1)
        
        # Particionar secuencia en grupos
        base_groups = {'A': [], 'T': [], 'C': [], 'G': []}
        for i, base in enumerate(seq[:min(60, len(seq))]):
            if base in base_groups:
                base_groups[base].append(i)
        
        stirling_signature = 0
        non_empty_groups = sum(1 for group in base_groups.values() if group)
        
        if non_empty_groups > 0:
            group_sizes = [len(group) for group in base_groups.values() if group]
            max_size = min(15, max(group_sizes))
            stirling_signature = stirling_second(max_size, non_empty_groups)
        
        return stirling_signature % 1000000
    
    # Calcular todas las firmas
    fibonacci_signature = fibonacci_encoding(secuencia)
    prime_signature = prime_factorization_hash(secuencia)
    catalan_signature = catalan_analysis(secuencia)
    taylor_signature = taylor_approximation(secuencia)
    fourier_signature = fourier_transform_hash(secuencia)
    pythagorean_signature = pythagorean_distances(secuencia)
    euler_signature = euler_totient_analysis(secuencia)
    fractal_signature = fractal_dimension_analysis(secuencia)
    stirling_signature = stirling_bell_analysis(secuencia)
    
    # Crear firma maestra combinando todas
    master_signature = (
        fibonacci_signature * 7 + 
        prime_signature * 11 + 
        catalan_signature * 13 + 
        taylor_signature * 17 + 
        fourier_signature * 19
    ) % 1000000
    
    # Calcular puntaje de complejidad único
    complexity_score = (
        len(set(secuencia[:100])) * 2 +
        len(secuencia) // 1000 +
        (fibonacci_signature % 100) // 10
    )
    
    return {
        'fibonacci_signature': fibonacci_signature,
        'prime_signature': prime_signature,
        'catalan_signature': catalan_signature,
        'taylor_signature': taylor_signature,
        'fourier_signature': fourier_signature,
        'pythagorean_signature': pythagorean_signature,
        'euler_signature': euler_signature,
        'fractal_signature': fractal_signature,
        'stirling_signature': stirling_signature,
        'master_signature': master_signature,
        'complexity_score': complexity_score
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
    
    # Header principal
    st.title("🧬 GeneticFrames")
    st.markdown("### *Plataforma de Arte Genético NFT Basado en Análisis Bioinformático*")
    
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
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 Generar Arte Genético")
        
        # Input de organismo
        selected_organism = st.session_state.get('selected_organism', '')
        organism_input = st.text_input(
            "Nombre científico del organismo:",
            value=selected_organism,
            placeholder="ej: Tursiops truncatus (delfín)",
            help="Introduce el nombre científico completo del organismo"
        )
        
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
    
    with col2:
        st.subheader("📋 Actividad Reciente")
        
        try:
            recent = get_recent_sequences(5)
            if recent:
                for seq in recent:
                    with st.container():
                        st.write(f"🧬 **{seq.organism_name[:30]}**")
                        st.write(f"GC: {seq.gc_content:.1f}% | Longitud: {seq.sequence_length:,}")
                        st.write(f"Accesos: {seq.accessed_count}")
                        st.divider()
            else:
                st.write("No hay secuencias recientes")
        except:
            st.write("Cargando actividad...")
        
        # Stats de la base de datos
        st.subheader("📈 Estadísticas")
        try:
            from database import get_database_stats
            stats = get_database_stats()
            st.metric("Secuencias almacenadas", stats['total_sequences'])
            st.metric("Búsquedas exitosas", stats['successful_searches'])
            st.metric("Organismos únicos", stats['unique_organisms'])
        except:
            st.write("Cargando estadísticas...")

if __name__ == "__main__":
    main()