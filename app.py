import streamlit as st
import numpy as np
import plotly.graph_objects as go
from Bio import Entrez, SeqIO
from Bio.SeqUtils import gc_fraction
import io
import math
import hashlib
import os
from animal_search import AnimalSearchEngine
from database import *
from symbolic_art_engine import SymbolicArtEngine
from species_identity_profiles import get_species_profile

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
    """Obtiene secuencia de ADN desde NCBI usando API configurada"""
    
    try:
        # Configurar Entrez con credenciales
        Entrez.email = st.secrets["ENTREZ_EMAIL"]
        
        # Funcionar sin API key - NCBI permite acceso básico
        Entrez.api_key = None
        
        organismo_limpio = limpiar_nombre_cientifico(organismo)
        clean_name = organismo_limpio.replace('"', '').replace("'", "")
        
        # Búsqueda estratégica: genoma completo primero, luego mitocondrial
        search_strategies = [
            f"{clean_name}[Organism] AND genome AND complete",
            f"{clean_name}[Organism] AND chromosome",
            f"{clean_name}[Organism] AND mitochondrion",
            f"{clean_name}[Organism] AND plastid",
            f"{clean_name}[Organism]"
        ]
        
        search_results = None
        for strategy in search_strategies:
            search_handle = Entrez.esearch(
                db="nucleotide",
                term=strategy,
                retmax=10,
                sort="length"  # Ordenar por longitud para obtener secuencias más grandes
            )
            search_results = Entrez.read(search_handle)
            search_handle.close()
            
            # Si encontramos resultados, usar esta estrategia
            if search_results.get("IdList", []):
                logger.info(f"Secuencia encontrada usando estrategia: {strategy}")
                break
        
        if not search_results.get("IdList", []):
            raise ValueError(f"No se encontraron secuencias genéticas para {organismo}")
        
        # Tomar el primer resultado
        seq_id = search_results["IdList"][0]
        
        # Obtener la secuencia
        fetch_handle = Entrez.efetch(
            db="nucleotide",
            id=seq_id,
            rettype="fasta",
            retmode="text"
        )
        
        fasta_data = fetch_handle.read()
        fetch_handle.close()
        
        if not fasta_data.strip():
            raise ValueError(f"Secuencia vacía obtenida para {organismo}")
        
        # Parsear la secuencia FASTA
        seq_record = SeqIO.read(io.StringIO(fasta_data), "fasta")
        
        # Verificar que la secuencia tenga contenido útil
        if len(seq_record.seq) < 100:
            raise ValueError(f"Secuencia demasiado corta para {organismo} (longitud: {len(seq_record.seq)})")
        
        return seq_record
        
    except Exception as e:
        error_msg = f"Error obteniendo secuencia para '{organismo}': {str(e)}"
        raise ValueError(error_msg)

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
    
    # Análisis de entropía y complejidad específica
    entropy = calcular_entropia_secuencia(secuencia)
    
    # Firma genética única basada en múltiples características
    genetic_signature = generar_firma_genetica_unica(secuencia, organism_id, dinucs, trinucs)
    
    # Análisis de periodicidad específica
    periodicities = detectar_periodicidades_especificas(secuencia)
    
    return {
        'base_ratios': {k: v/total for k, v in base_counts.items()},
        'dinuc_profile': dinucs,
        'trinuc_profile': trinucs,
        'repeat_patterns': repeat_patterns,
        'position_profile': position_profile,
        'gc_skew': gc_skew,
        'at_skew': at_skew,
        'sequence_length': len(secuencia),
        'organism_signature': hash(organism_id + secuencia[:100]) % 1000000,
        'entropy': entropy,
        'genetic_signature': genetic_signature,
        'periodicities': periodicities
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

def calcular_entropia_secuencia(secuencia):
    """Calcula la entropía de Shannon de la secuencia"""
    from collections import Counter
    import math
    
    # Contar dinucleótidos para mayor especificidad
    dinucs = []
    for i in range(len(secuencia) - 1):
        dinuc = secuencia[i:i+2]
        if all(b in 'ATCG' for b in dinuc):
            dinucs.append(dinuc)
    
    if not dinucs:
        return 0
    
    counts = Counter(dinucs)
    total = len(dinucs)
    
    entropy = 0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy

def generar_firma_genetica_unica(secuencia, organism_id, dinucs, trinucs):
    """Genera una firma genética única específica de la especie"""
    
    # Combinación de características únicas
    top_dinucs = sorted(dinucs.items(), key=lambda x: x[1], reverse=True)[:5]
    top_trinucs = sorted(trinucs.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # Crear firma basada en patrones más frecuentes
    signature_elements = []
    
    for pattern, freq in top_dinucs:
        signature_elements.append(pattern + str(freq))
    
    for pattern, freq in top_trinucs:
        signature_elements.append(pattern + str(freq))
    
    # Añadir características específicas del organismo
    gc_ratio = (secuencia.count('G') + secuencia.count('C')) / len(secuencia)
    signature_elements.append(f"GC{int(gc_ratio*100)}")
    
    # Crear hash único
    signature_string = "_".join(signature_elements) + organism_id
    return hash(signature_string) % 999999

def detectar_periodicidades_especificas(secuencia):
    """Detecta periodicidades específicas en la secuencia"""
    periodicities = {}
    
    # Analizar periodicidades de longitud 3, 6, 9 (relacionadas con codones)
    for period in [3, 6, 9, 12]:
        if len(secuencia) < period * 3:
            continue
            
        pattern_counts = {}
        for i in range(0, len(secuencia) - period, period):
            segment = secuencia[i:i+period]
            if all(b in 'ATCG' for b in segment):
                pattern_counts[segment] = pattern_counts.get(segment, 0) + 1
        
        if pattern_counts:
            most_common = max(pattern_counts.items(), key=lambda x: x[1])
            periodicities[period] = {
                'pattern': most_common[0],
                'frequency': most_common[1],
                'regularity': most_common[1] / max(1, len(pattern_counts))
            }
    
    return periodicities

def crear_arte_basado_en_perfil(secuencia, genetic_profile, theme):
    """Crea arte único basado en el perfil genético específico"""
    
    colors = COLOR_THEMES.get(theme, COLOR_THEMES['scientific'])
    
    # Usar la nueva firma genética para determinar el patrón
    genetic_signature = genetic_profile.get('genetic_signature', 0)
    entropy = genetic_profile.get('entropy', 0)
    periodicities = genetic_profile.get('periodicities', {})
    
    # Análisis mejorado de características
    gc_content = sum(genetic_profile['base_ratios'][base] for base in ['G', 'C'])
    repeat_density = len(genetic_profile['repeat_patterns'])
    skew_intensity = abs(genetic_profile['gc_skew']) + abs(genetic_profile['at_skew'])
    
    # Selección de patrón basada en firma genética única
    pattern_selector = genetic_signature % 1000
    
    if pattern_selector < 250 and gc_content > 0.55:
        # Patrón de red neural para alta complejidad
        fig = crear_patron_red_neural(secuencia, genetic_profile, colors)
    elif pattern_selector < 500 and entropy > 3.0:
        # Patrón fractal para alta entropía
        fig = crear_patron_fractal(secuencia, genetic_profile, colors)
    elif pattern_selector < 750 and len(periodicities) > 0:
        # Patrón de ondas para secuencias periódicas
        fig = crear_patron_ondas(secuencia, genetic_profile, colors)
    else:
        # Patrón de galaxia espiral único
        fig = crear_patron_galaxia(secuencia, genetic_profile, colors)
    
    return fig

def crear_patron_red_neural(secuencia, genetic_profile, colors):
    """Patrón de red neural para especies con alta complejidad genética"""
    
    fig = go.Figure()
    
    # Usar dinucleótidos como nodos
    dinucs = genetic_profile['dinuc_profile']
    top_dinucs = sorted(dinucs.items(), key=lambda x: x[1], reverse=True)[:8]
    
    # Crear nodos principales
    nodes = []
    for i, (dinuc, freq) in enumerate(top_dinucs):
        angle = (i * 45) * np.pi / 180
        radius = 60 + (freq / max(dinucs.values())) * 40
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        nodes.append((x, y, dinuc, freq))
        
        # Color basado en primer nucleótido
        color_key = dinuc[0] if dinuc[0] in colors else 'A'
        
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers',
            marker=dict(
                size=15 + freq/max(dinucs.values())*15,
                color=colors[color_key],
                symbol='circle',
                opacity=0.8,
                line=dict(color='white', width=2)
            ),
            name=dinuc,
            showlegend=False,
            hovertemplate=f"Dinucleótido: {dinuc}<br>Frecuencia: {freq}"
        ))
    
    # Crear conexiones basadas en entropía
    entropy = genetic_profile.get('entropy', 0)
    for i, node1 in enumerate(nodes):
        for j, node2 in enumerate(nodes[i+1:], i+1):
            if entropy > 2.0:  # Alta entropía = más conexiones
                connection_strength = abs(node1[3] - node2[3]) / max(dinucs.values())
                if connection_strength > 0.3:
                    fig.add_trace(go.Scatter(
                        x=[node1[0], node2[0]],
                        y=[node1[1], node2[1]],
                        mode='lines',
                        line=dict(
                            color='rgba(100,200,255,0.4)',
                            width=connection_strength * 3
                        ),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
    
    fig.update_layout(
        title=f"Red Neural Genética - Entropía: {entropy:.2f}",
        xaxis=dict(visible=False, range=[-150, 150]),
        yaxis=dict(visible=False, range=[-150, 150]),
        plot_bgcolor='black',
        paper_bgcolor='black',
        width=800,
        height=600
    )
    
    return fig

def crear_patron_fractal(secuencia, genetic_profile, colors):
    """Patrón fractal para especies con alta entropía"""
    
    fig = go.Figure()
    
    # Usar firma genética para generar fractal único
    genetic_signature = genetic_profile.get('genetic_signature', 12345)
    np.random.seed(genetic_signature % 10000)
    
    # Generar puntos fractales basados en trinucleótidos
    trinucs = genetic_profile['trinuc_profile']
    if not trinucs:
        trinucs = {'ATG': 10, 'GCA': 8, 'TAG': 6}
    
    for i, (trinuc, freq) in enumerate(list(trinucs.items())[:6]):
        # Crear fractal específico para cada trinucleótido
        iterations = min(freq // 5, 50)
        
        # Punto inicial basado en trinucleótido
        x_vals = [0]
        y_vals = [0]
        
        for _ in range(iterations):
            # Reglas fractales basadas en secuencia del trinucleótido
            dx = 0
            dy = 0
            for base in trinuc:
                if base == 'A':
                    dx += np.random.normal(0, 2)
                elif base == 'T':
                    dy += np.random.normal(0, 2)
                elif base == 'G':
                    dx += np.random.normal(0, 1)
                    dy += np.random.normal(0, 1)
                else:  # C
                    dx -= np.random.normal(0, 1)
                    dy -= np.random.normal(0, 1)
            
            x_vals.append(x_vals[-1] + dx)
            y_vals.append(y_vals[-1] + dy)
        
        # Color basado en trinucleótido
        color_key = trinuc[0] if trinuc[0] in colors else 'A'
        
        fig.add_trace(go.Scatter(
            x=x_vals, y=y_vals,
            mode='lines+markers',
            line=dict(color=colors[color_key], width=1),
            marker=dict(size=2, color=colors[color_key]),
            name=trinuc,
            showlegend=False,
            hovertemplate=f"Trinucleótido: {trinuc}<br>Frecuencia: {freq}"
        ))
    
    fig.update_layout(
        title=f"Fractal Genético - Firma: {genetic_signature}",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='black',
        paper_bgcolor='black',
        width=800,
        height=600
    )
    
    return fig

def crear_patron_ondas(secuencia, genetic_profile, colors):
    """Patrón de ondas para secuencias periódicas"""
    
    fig = go.Figure()
    
    periodicities = genetic_profile.get('periodicities', {})
    
    for i, (period, data) in enumerate(periodicities.items()):
        # Crear onda basada en periodicidad específica
        t = np.linspace(0, 4*np.pi, 200)
        
        # Frecuencia basada en período genético
        frequency = period / 3.0
        amplitude = data['frequency'] / 10
        phase = data['regularity'] * np.pi
        
        # Onda principal
        y_main = amplitude * np.sin(frequency * t + phase)
        
        # Modulación basada en patrón específico
        pattern = data['pattern']
        modulation = 0
        for j, base in enumerate(pattern):
            if base == 'A':
                modulation += 0.1 * np.cos(2 * frequency * t + j)
            elif base == 'T':
                modulation += 0.1 * np.sin(3 * frequency * t + j)
            elif base == 'G':
                modulation += 0.05 * np.cos(4 * frequency * t + j)
            else:  # C
                modulation += 0.05 * np.sin(5 * frequency * t + j)
        
        y_final = y_main + modulation + i * 20
        
        # Color basado en primer nucleótido del patrón
        color_key = pattern[0] if pattern[0] in colors else 'A'
        
        fig.add_trace(go.Scatter(
            x=t, y=y_final,
            mode='lines',
            line=dict(color=colors[color_key], width=2),
            name=f"Período {period}",
            showlegend=False,
            hovertemplate=f"Patrón: {pattern}<br>Período: {period}<br>Frecuencia: {data['frequency']}"
        ))
    
    fig.update_layout(
        title=f"Ondas Genéticas - Períodos: {list(periodicities.keys())}",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='black',
        paper_bgcolor='black',
        width=800,
        height=600
    )
    
    return fig

def crear_patron_galaxia(secuencia, genetic_profile, colors):
    """Patrón de galaxia espiral único para cada especie"""
    
    fig = go.Figure()
    
    # Usar características específicas para crear galaxia única
    genetic_signature = genetic_profile.get('genetic_signature', 12345)
    gc_content = sum(genetic_profile['base_ratios'][base] for base in ['G', 'C'])
    
    # Parámetros de galaxia basados en genética
    num_arms = int(genetic_signature % 5) + 2  # 2-6 brazos
    arm_tightness = gc_content * 2 + 0.5
    
    for arm in range(num_arms):
        # Crear brazo espiral
        t = np.linspace(0, 4*np.pi, 100)
        arm_offset = arm * 2*np.pi / num_arms
        
        # Radio basado en dinucleótidos
        dinucs = genetic_profile['dinuc_profile']
        if dinucs:
            radius_modifier = list(dinucs.values())[arm % len(dinucs)] / max(dinucs.values())
        else:
            radius_modifier = 1
        
        r = (5 + t * 8) * radius_modifier
        x = r * np.cos(arm_tightness * t + arm_offset)
        y = r * np.sin(arm_tightness * t + arm_offset)
        
        # Color único por brazo
        color_keys = list(colors.keys())
        color_key = color_keys[arm % len(color_keys)]
        
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode='lines+markers',
            line=dict(color=colors[color_key], width=2),
            marker=dict(size=3, color=colors[color_key]),
            name=f"Brazo {arm+1}",
            showlegend=False,
            hovertemplate=f"Brazo galáctico {arm+1}"
        ))
        
        # Añadir estrellas (nodos importantes)
        for i in range(0, len(x), 20):
            if i < len(x):
                fig.add_trace(go.Scatter(
                    x=[x[i]], y=[y[i]],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color=colors[color_key],
                        symbol='star',
                        opacity=0.8
                    ),
                    showlegend=False,
                    hoverinfo='skip'
                ))
    
    fig.update_layout(
        title=f"Galaxia Genética - Brazos: {num_arms}, GC: {gc_content:.1%}",
        xaxis=dict(visible=False, range=[-200, 200]),
        yaxis=dict(visible=False, range=[-200, 200]),
        plot_bgcolor='black',
        paper_bgcolor='black',
        width=800,
        height=600
    )
    
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

def determinar_categoria_taxonomica(species_name, seq_description):
    """Determina la categoría taxonómica y estilo visual apropiado"""
    name_lower = species_name.lower()
    desc_lower = seq_description.lower()
    
    # Patrones para identificar categorías
    mammal_patterns = ['panthera', 'canis', 'felis', 'homo', 'bos', 'sus', 'equus', 'ursus', 'macaca', 'rattus']
    aquatic_patterns = ['balaenoptera', 'tursiops', 'salmo', 'thunnus', 'octopus', 'cancer', 'hippocampus']
    avian_patterns = ['aquila', 'bubo', 'aptenodytes', 'falco', 'corvus', 'passer', 'gallus']
    reptile_patterns = ['python', 'crocodylus', 'iguana', 'gecko', 'chelonia', 'vipera']
    arthropod_patterns = ['drosophila', 'apis', 'theraphosa', 'latrodectus', 'aedes', 'tribolium']
    plant_patterns = ['arabidopsis', 'oryza', 'triticum', 'zea', 'solanum', 'rosa', 'quercus']
    
    if any(pattern in name_lower for pattern in mammal_patterns):
        return 'mammal'
    elif any(pattern in name_lower for pattern in aquatic_patterns):
        return 'aquatic'
    elif any(pattern in name_lower for pattern in avian_patterns):
        return 'avian'
    elif any(pattern in name_lower for pattern in reptile_patterns):
        return 'reptile'
    elif any(pattern in name_lower for pattern in arthropod_patterns):
        return 'arthropod'
    elif any(pattern in name_lower for pattern in plant_patterns):
        return 'plant'
    else:
        return 'general'

def obtener_paleta_semantica(categoria):
    """Paletas de colores específicas por categoría taxonómica"""
    paletas = {
        'mammal': {
            'primary': ['#8B4513', '#CD853F', '#DEB887', '#F4A460', '#D2691E'],  # Tierras y marrones
            'secondary': ['#FF6347', '#FFB347', '#FFCCCB', '#FFA07A', '#FA8072'],  # Cálidos
            'accent': ['#4169E1', '#6495ED', '#87CEEB', '#B0C4DE', '#E6E6FA'],    # Azules suaves
            'gradient': 'radial'
        },
        'aquatic': {
            'primary': ['#000080', '#0000CD', '#4169E1', '#6495ED', '#87CEEB'],    # Azules profundos
            'secondary': ['#20B2AA', '#48D1CC', '#40E0D0', '#AFEEEE', '#E0FFFF'], # Turquesas
            'accent': ['#FF1493', '#FF69B4', '#FFB6C1', '#FFC0CB', '#FFCCCB'],    # Corales
            'gradient': 'linear_vertical'
        },
        'avian': {
            'primary': ['#FFD700', '#FFA500', '#FF8C00', '#FF7F50', '#FF6347'],   # Dorados y naranjas
            'secondary': ['#4682B4', '#5F9EA0', '#6495ED', '#7B68EE', '#9370DB'], # Cielos
            'accent': ['#32CD32', '#90EE90', '#98FB98', '#F0FFF0', '#FFFFE0'],    # Verdes naturales
            'gradient': 'conical'
        },
        'reptile': {
            'primary': ['#228B22', '#32CD32', '#9ACD32', '#ADFF2F', '#7FFF00'],   # Verdes reptil
            'secondary': ['#8B4513', '#A0522D', '#CD853F', '#D2B48C', '#F5DEB3'], # Tierras
            'accent': ['#DC143C', '#B22222', '#FF0000', '#FF6347', '#FA8072'],    # Rojos intensos
            'gradient': 'diamond'
        },
        'arthropod': {
            'primary': ['#4B0082', '#8B008B', '#9932CC', '#BA55D3', '#DA70D6'],   # Púrpuras
            'secondary': ['#FF4500', '#FF6347', '#FF8C00', '#FFA500', '#FFD700'], # Naranjas
            'accent': ['#00CED1', '#40E0D0', '#48D1CC', '#20B2AA', '#008B8B'],    # Cianes
            'gradient': 'spiral'
        },
        'plant': {
            'primary': ['#006400', '#228B22', '#32CD32', '#90EE90', '#98FB98'],   # Verdes naturales
            'secondary': ['#8B4513', '#A0522D', '#CD853F', '#D2B48C', '#DEB887'], # Tierras
            'accent': ['#FF69B4', '#FFB6C1', '#FFC0CB', '#FFCCCB', '#F0F8FF'],    # Florales
            'gradient': 'organic'
        },
        'general': {
            'primary': ['#483D8B', '#6A5ACD', '#7B68EE', '#9370DB', '#BA55D3'],   # Púrpuras místicos
            'secondary': ['#00CED1', '#40E0D0', '#48D1CC', '#AFEEEE', '#E0FFFF'], # Cianes
            'accent': ['#FFD700', '#FFA500', '#FF8C00', '#FF7F50', '#FF6347'],    # Dorados
            'gradient': 'cosmic'
        }
    }
    return paletas.get(categoria, paletas['general'])

def crear_visualizacion_avanzada(secuencia, genetic_profile, categoria, paleta):
    """Crea visualización estéticamente rica basada en complejidad genética"""
    import numpy as np
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Análisis de complejidad para determinar densidad visual
    sequence_length = len(secuencia)
    complexity_score = genetic_profile.get('entropy', 0) * genetic_profile.get('gc_content', 50) / 50
    
    # Crear figura con múltiples capas visuales
    fig = go.Figure()
    
    # Capa 1: Base genética - estructura fundamental
    n_base_points = min(2000, sequence_length // 10)  # Más puntos para secuencias complejas
    
    # Usar patrón específico por categoría
    if categoria == 'mammal':
        pattern = crear_patron_mamifero(n_base_points, paleta, genetic_profile)
    elif categoria == 'aquatic':
        pattern = crear_patron_acuatico(n_base_points, paleta, genetic_profile)
    elif categoria == 'avian':
        pattern = crear_patron_aviario(n_base_points, paleta, genetic_profile)
    elif categoria == 'reptile':
        pattern = crear_patron_reptil(n_base_points, paleta, genetic_profile)
    elif categoria == 'arthropod':
        pattern = crear_patron_artropodo(n_base_points, paleta, genetic_profile)
    elif categoria == 'plant':
        pattern = crear_patron_botanico(n_base_points, paleta, genetic_profile)
    else:
        pattern = crear_patron_general(n_base_points, paleta, genetic_profile)
    
    # Añadir todas las trazas del patrón
    for trace in pattern:
        fig.add_trace(trace)
    
    # Capa 2: Elementos de complejidad genética
    if complexity_score > 0.5:  # Solo para secuencias complejas
        complexity_traces = crear_elementos_complejidad(genetic_profile, paleta, sequence_length)
        for trace in complexity_traces:
            fig.add_trace(trace)
    
    # Configurar layout estético avanzado
    fig.update_layout(
        title=dict(
            text=f"🧬 Genoma Artístico - {genetic_profile.get('organism_id', 'Especie Desconocida')}",
            font=dict(size=20, color=paleta['accent'][0]),
            x=0.5
        ),
        plot_bgcolor='rgba(5,5,5,1)',
        paper_bgcolor='rgba(5,5,5,1)',
        showlegend=False,
        xaxis=dict(visible=False, range=[-1.2, 1.2]),
        yaxis=dict(visible=False, range=[-1.2, 1.2]),
        height=700,
        annotations=[
            dict(
                text=f"Longitud: {sequence_length:,} bp | Entropía: {genetic_profile.get('entropy', 0):.3f} | GC: {genetic_profile.get('gc_content', 0):.1f}%",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.5, y=0.02, xanchor='center', yanchor='bottom',
                font=dict(size=10, color=paleta['secondary'][2])
            )
        ]
    )
    
    return fig

def generar_visualizacion(seq_record, style='voronoi', theme='scientific'):
    """Crea arte simbólico único basado en identidad de especies y genética real"""
    
    secuencia = str(seq_record.seq).upper()
    
    # Análisis profundo de características genéticas únicas
    genetic_profile = analizar_perfil_genetico_unico(secuencia, seq_record.id)
    
    if not genetic_profile:
        # Error en análisis genético
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(size=20, color='red')))
        fig.update_layout(title="Error: No se pudo analizar la secuencia")
        return fig, 0
    
    # Extraer información de la especie
    species_name = seq_record.description.split()[1:3] if len(seq_record.description.split()) >= 3 else [seq_record.id]
    species_scientific_name = ' '.join(species_name).lower()
    
    # Determinar categoría taxonómica y paleta semántica
    categoria = determinar_categoria_taxonomica(species_scientific_name, seq_record.description)
    paleta = obtener_paleta_semantica(categoria)
    
    # Crear visualización estéticamente avanzada
    fig = crear_visualizacion_avanzada(secuencia, genetic_profile, categoria, paleta)
    
    # Calcular GC content
    gc_content = gc_fraction(seq_record.seq) * 100
    
    return fig, gc_content

def create_animated_dna_progress(species_name="especie desconocida"):
    """Crea animación de micelio durante la generación de arte genético"""
    return f"""
    <style>
        .mycelium-container {{
            position: relative;
            width: 100%;
            height: 500px;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
            border-radius: 20px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin: 1rem 0;
            box-shadow: 0 0 30px rgba(0, 255, 150, 0.3);
        }}
        
        .species-title {{
            font-size: 24px;
            font-weight: 600;
            color: #ffffff;
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
            margin-bottom: 10px;
            text-align: center;
        }}
        
        .generation-status {{
            font-size: 16px;
            background: linear-gradient(45deg, #00ff96, #00d4ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 20px;
        }}
        
        .mycelium-canvas {{
            width: 400px;
            height: 300px;
            border-radius: 15px;
            background: #050a0f;
            position: relative;
            overflow: hidden;
            border: 2px solid rgba(0, 255, 150, 0.3);
        }}
        
        .progress-message {{
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            color: rgba(255, 255, 255, 0.8);
            font-size: 14px;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 0.5; }}
            50% {{ opacity: 1; }}
        }}
        
        .mycelium-growth {{
            position: absolute;
            top: 50%;
            left: 50%;
            width: 4px;
            height: 4px;
            background: #00ff96;
            border-radius: 50%;
            transform: translate(-50%, -50%);
        }}
        
        .growth-line {{
            position: absolute;
            background: linear-gradient(45deg, #00ff96, #00d4ff);
            border-radius: 2px;
            animation: growLine 0.8s ease-out forwards;
            opacity: 0.8;
        }}
        
        @keyframes growLine {{
            0% {{ 
                width: 0;
                height: 2px;
                opacity: 0;
            }}
            100% {{ 
                width: var(--line-length);
                height: 2px;
                opacity: 0.8;
            }}
        }}
        
        .mycelium-node {{
            position: absolute;
            width: 6px;
            height: 6px;
            background: #ffffff;
            border-radius: 50%;
            box-shadow: 0 0 10px #00ff96;
            animation: nodeGlow 2s ease-in-out infinite;
        }}
        
        @keyframes nodeGlow {{
            0%, 100% {{ 
                transform: scale(1);
                box-shadow: 0 0 10px #00ff96;
            }}
            50% {{ 
                transform: scale(1.3);
                box-shadow: 0 0 20px #00ff96;
            }}
        }}
        
        .dna-particle {{
            position: absolute;
            width: 3px;
            height: 3px;
            background: rgba(0, 255, 150, 0.7);
            border-radius: 50%;
            animation: float 4s infinite ease-in-out;
        }}
        
        @keyframes float {{
            0%, 100% {{ 
                transform: translateY(0px) translateX(0px);
                opacity: 0;
            }}
            50% {{ 
                transform: translateY(-15px) translateX(8px);
                opacity: 1;
            }}
        }}
    </style>
    
    <div class="mycelium-container">
        <div class="species-title">Generando arte para: {species_name}</div>
        <div class="generation-status">Crecimiento Genético en Progreso</div>
        
        <div class="mycelium-canvas" id="mycelium-canvas">
            <div class="mycelium-growth" id="center-node"></div>
            <!-- Partículas de ADN -->
            <div class="dna-particle" style="top: 20%; left: 30%; animation-delay: 0s;"></div>
            <div class="dna-particle" style="top: 60%; left: 70%; animation-delay: 1s;"></div>
            <div class="dna-particle" style="top: 40%; left: 50%; animation-delay: 2s;"></div>
            <div class="dna-particle" style="top: 80%; left: 20%; animation-delay: 0.5s;"></div>
            <div class="dna-particle" style="top: 10%; left: 80%; animation-delay: 1.5s;"></div>
        </div>
        
        <div class="progress-message" id="progress-msg">
            Decodificando secuencias genéticas...
        </div>
    </div>
    
    <script>
        const messages = [
            "Decodificando secuencias genéticas...",
            "Analizando patrones de ADN...",
            "Calculando firmas genéticas...",
            "Generando identidad simbólica...",
            "Creando arte único...",
            "Aplicando características de especie...",
            "Finalizando obra maestra..."
        ];
        
        let currentMsg = 0;
        const progressElement = document.getElementById('progress-msg');
        const canvas = document.getElementById('mycelium-canvas');
        
        function createMyceliumBranch(startX, startY, angle, length, generation) {{
            if (generation > 5 || length < 10) return;
            
            const endX = startX + Math.cos(angle) * length;
            const endY = startY + Math.sin(angle) * length;
            
            // Crear línea de crecimiento
            const line = document.createElement('div');
            line.className = 'growth-line';
            line.style.left = startX + 'px';
            line.style.top = startY + 'px';
            line.style.transform = `rotate(${{angle}}rad)`;
            line.style.setProperty('--line-length', length + 'px');
            line.style.animationDelay = (generation * 200) + 'ms';
            canvas.appendChild(line);
            
            // Crear nodo al final
            setTimeout(() => {{
                const node = document.createElement('div');
                node.className = 'mycelium-node';
                node.style.left = (endX - 3) + 'px';
                node.style.top = (endY - 3) + 'px';
                node.style.animationDelay = Math.random() + 's';
                canvas.appendChild(node);
                
                // Crear ramas secundarias
                if (Math.random() > 0.3) {{
                    const newAngle1 = angle + (Math.random() - 0.5) * 1.2;
                    const newAngle2 = angle + (Math.random() - 0.5) * 1.2;
                    const newLength = length * (0.6 + Math.random() * 0.3);
                    
                    setTimeout(() => {{
                        createMyceliumBranch(endX, endY, newAngle1, newLength, generation + 1);
                        if (Math.random() > 0.5) {{
                            createMyceliumBranch(endX, endY, newAngle2, newLength, generation + 1);
                        }}
                    }}, 300);
                }}
            }}, generation * 200 + 500);
        }}
        
        // Iniciar crecimiento de micelio
        setTimeout(() => {{
            const centerX = 200;
            const centerY = 150;
            
            // Crear múltiples ramas iniciales
            for (let i = 0; i < 6; i++) {{
                const angle = (i * Math.PI * 2 / 6) + (Math.random() - 0.5) * 0.5;
                const length = 30 + Math.random() * 20;
                setTimeout(() => {{
                    createMyceliumBranch(centerX, centerY, angle, length, 1);
                }}, i * 150);
            }}
        }}, 500);
        
        const updateMessage = () => {{
            if (currentMsg < messages.length && progressElement) {{
                progressElement.textContent = messages[currentMsg];
                currentMsg++;
            }}
        }};
        
        // Cambiar mensaje cada 1.2 segundos
        const interval = setInterval(updateMessage, 1200);
        
        // Limpiar intervalo después de 8 segundos
        setTimeout(() => {{
            clearInterval(interval);
            if (progressElement) {{
                progressElement.textContent = "Arte genético completado!";
            }}
        }}, 8000);
    </script>
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
        # Mostrar progreso simple y efectivo
        loading_placeholder.info("🔍 Buscando especie en base de datos...")
        
        # Buscar nombre científico usando el motor de búsqueda
        try:
            search_engine = AnimalSearchEngine()
            suggestions = search_engine.search_comprehensive(organism_input.lower())
            
            if suggestions:
                # Usar la primera sugerencia más relevante
                scientific_name = suggestions[0]['scientific_name']
                
                loading_placeholder.info(f"🧬 Conectando con NCBI GenBank: {scientific_name}")
                
                # Diagnóstico de conexión
                st.info(f"Buscando secuencias genéticas para: {scientific_name}")
                
                # Mostrar estado de la búsqueda
                with st.status("Conectando con NCBI GenBank...", expanded=True) as status:
                    st.write("Configurando credenciales...")
                    
                    # Configurar Entrez
                    Entrez.email = st.secrets["ENTREZ_EMAIL"]
                    
                    # NCBI permite acceso básico sin API key
                    Entrez.api_key = None
                    
                    st.write(f"Conectando con NCBI GenBank...")
                    st.write(f"Email registrado: {Entrez.email}")
                    
                    st.write("Realizando búsqueda en base de datos...")
                    
                    # Búsqueda simplificada sin caracteres especiales
                    clean_name = scientific_name.replace('"', '').replace("'", "")
                    
                    # Primera búsqueda: mitocondrias
                    search_handle = Entrez.esearch(
                        db="nucleotide",
                        term=f"{clean_name}[Organism] AND mitochondrion",
                        retmax=5
                    )
                    search_results = Entrez.read(search_handle)
                    search_handle.close()
                    
                    ids_found = search_results.get("IdList", [])
                    st.write(f"Búsqueda mitocondrial: {len(ids_found)} secuencias")
                    
                    if not ids_found:
                        # Segunda búsqueda: general
                        st.write("Expandiendo búsqueda...")
                        search_handle = Entrez.esearch(
                            db="nucleotide",
                            term=f"{clean_name}[Organism]",
                            retmax=10
                        )
                        search_results = Entrez.read(search_handle)
                        search_handle.close()
                        
                        ids_found = search_results.get("IdList", [])
                        st.write(f"Búsqueda general: {len(ids_found)} secuencias")
                    
                    if ids_found:
                        st.write(f"Obteniendo secuencia ID: {ids_found[0]}")
                        
                        fetch_handle = Entrez.efetch(
                            db="nucleotide",
                            id=ids_found[0],
                            rettype="fasta",
                            retmode="text"
                        )
                        fasta_data = fetch_handle.read()
                        fetch_handle.close()
                        
                        st.write(f"Datos obtenidos: {len(fasta_data)} caracteres")
                        
                        if fasta_data.strip():
                            seq_record = SeqIO.read(io.StringIO(fasta_data), "fasta")
                            st.write(f"Secuencia parseada: {len(seq_record.seq)} nucleótidos")
                            status.update(label="Secuencia obtenida exitosamente", state="complete")
                        else:
                            raise ValueError("Datos FASTA vacíos")
                    else:
                        raise ValueError(f"No se encontraron secuencias para {scientific_name}")
                
                organism_name = scientific_name
                loading_placeholder.empty()
                
            else:
                # Intentar búsqueda directa si no hay sugerencias
                loading_placeholder.info(f"🔍 Búsqueda directa en NCBI: {organism_input}")
                
                st.info(f"Buscando secuencias genéticas para: {organism_input}")
                seq_record = obtener_secuencia(organism_input)
                organism_name = organism_input
                loading_placeholder.empty()
            
        except Exception as e:
            loading_placeholder.empty()
            
            # Mostrar error detallado
            st.error(f"Error al obtener secuencias genéticas: {str(e)}")
            
            # Verificar estado de conexión
            if "No se encontraron secuencias" in str(e):
                st.warning("No hay secuencias genéticas disponibles en NCBI GenBank para este organismo.")
                st.info("Esto puede ocurrir si:")
                st.write("• El organismo no tiene su genoma secuenciado aún")
                st.write("• El nombre científico no coincide exactamente")
                st.write("• Los datos están en una base diferente")
            elif "Error de conexión" in str(e) or "HTTP" in str(e):
                st.error("Problema de conexión con NCBI GenBank")
                st.info("La API de NCBI podría estar temporalmente no disponible")
            else:
                st.error(f"Error técnico: {str(e)}")
            
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
            
            # Generar arte genético directamente
            st.markdown(f"### 🧬 Generando Arte Genético para: **{organism_name}**")
            
            # Mostrar proceso de generación simple
            import time
            with st.spinner("Analizando secuencia genética y creando visualización artística..."):
                fig, gc = generar_visualizacion(seq_record, theme='scientific')
                genetic_profile = analizar_perfil_genetico_unico(secuencia, seq_record.id)
                time.sleep(2)  # Breve pausa para efecto
            
            st.success("Arte genético completado")
            
            # Mostrar arte final con animación infinita
            st.markdown("### 🎨 Arte Genético Animado")
            
            # Crear visualización animada con loop infinito
            animated_fig = crear_visualizacion_animada(fig, genetic_profile, organism_name)
            st.plotly_chart(animated_fig, use_container_width=True)
            
            # Mostrar estadísticas
            st.markdown("### 📊 Análisis de la Secuencia")
            mostrar_estadisticas_secuencia(seq_record, gc, genetic_profile)
            
            # Marcar búsqueda como exitosa
            log_search(organism_input, successful=True, user_session=st.session_state.session_id)

def extract_art_data_for_animation(fig, genetic_profile, organism_name):
    """Extrae datos de la visualización para animación progresiva"""
    
    art_data = {
        'organism_name': organism_name,
        'traces': [],
        'genetic_signature': genetic_profile.get('genetic_signature', {}),
        'base_ratios': genetic_profile.get('base_ratios', {}),
        'entropy': genetic_profile.get('entropy', 0),
        'pattern_complexity': genetic_profile.get('pattern_complexity', 0)
    }
    
    # Extraer información de cada traza en el gráfico
    for trace in fig.data:
        trace_data = {
            'type': trace.type,
            'x': list(trace.x) if hasattr(trace, 'x') and trace.x is not None else [],
            'y': list(trace.y) if hasattr(trace, 'y') and trace.y is not None else [],
            'mode': getattr(trace, 'mode', 'markers'),
            'marker_color': getattr(trace.marker, 'color', '#00ff88') if hasattr(trace, 'marker') else '#00ff88',
            'marker_size': getattr(trace.marker, 'size', 5) if hasattr(trace, 'marker') else 5,
            'line_color': getattr(trace.line, 'color', '#00ff88') if hasattr(trace, 'line') else '#00ff88',
            'line_width': getattr(trace.line, 'width', 2) if hasattr(trace, 'line') else 2
        }
        art_data['traces'].append(trace_data)
    
    return art_data

def create_progressive_art_animation(art_data):
    """Crea animación progresiva del arte genético real"""
    organism_name = art_data['organism_name']
    canvas_id = hash(organism_name) % 10000
    
    return f"""
    <div style="background: #0a0a0a; border-radius: 15px; padding: 20px; margin: 20px 0;">
        <div style="text-align: center; color: #00ff88; font-size: 24px; margin-bottom: 20px;">
            🧬 Arte Genético Emergiendo: {organism_name}
        </div>
        
        <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.7.0/p5.min.js"></script>
        <div id="progressive-art-canvas-{canvas_id}" style="text-align: center; margin: 20px 0;"></div>
        <div id="art-progress-text-{canvas_id}" style="text-align: center; color: #cccccc; font-size: 14px; opacity: 0.8;">
            Leyendo secuencia genética...
        </div>
        
        <script>
        let progressiveArtSketch_{canvas_id} = function(p) {{
            let animDuration = 25000;
            let artElements = [];
            let totalElements = 0;
            let animationStartTime;
            let progressMessages = [
                "Leyendo secuencia genética...",
                "Aplicando codificación simbólica...",
                "Ramificando estructuras...",
                "Traduciendo bases nitrogenadas...",
                "Dibujando el alma visual del genoma...",
                "Finalizando ADN simbiótico...",
                "¡Arte Genético Generado!"
            ];
            let currentMessageIndex = 0;
            
            p.setup = function() {{
                let canvas = p.createCanvas(800, 600);
                canvas.parent('progressive-art-canvas-{canvas_id}');
                
                p.background(5, 10, 15);
                p.frameRate(60);
                
                animationStartTime = p.millis();
                prepareArtElements();
                
                setInterval(() => {{
                    updateProgressMessage_{canvas_id}();
                }}, 3500);
            }};
            
            p.draw = function() {{
                p.fill(5, 10, 15, 15);
                p.noStroke();
                p.rect(0, 0, p.width, p.height);
                
                let elapsed = p.millis() - animationStartTime;
                let progress = elapsed / animDuration;
                
                if (progress < 1) {{
                    drawProgressiveArt(progress);
                }} else {{
                    drawCompleteArt();
                }}
            }};
            
            function prepareArtElements() {{
                // Crear elementos artísticos basados en datos genéticos
                let centerX = p.width / 2;
                let centerY = p.height / 2;
                
                // Generar puntos en patrones orgánicos
                for (let i = 0; i < 500; i++) {{
                    let angle = (i * 137.5) * p.PI / 180; // Ángulo dorado para patrones naturales
                    let radius = p.sqrt(i) * 8;
                    
                    let x = centerX + p.cos(angle) * radius;
                    let y = centerY + p.sin(angle) * radius;
                    
                    artElements.push({{
                        x: x,
                        y: y,
                        originalX: x,
                        originalY: y,
                        size: p.random(1, 4),
                        hue: (i * 5) % 360,
                        birthTime: i / 500,
                        drawn: false,
                        energy: p.random(0.5, 1.0)
                    }});
                }}
                
                totalElements = artElements.length;
            }}
            
            function drawProgressiveArt(progress) {{
                let elementsToShow = Math.floor(progress * totalElements);
                
                for (let i = 0; i < elementsToShow; i++) {{
                    let element = artElements[i];
                    if (!element.drawn) {{
                        let elementAge = (elementsToShow - i) / 20;
                        let alpha = p.constrain(elementAge * 255, 0, 255);
                        
                        // Colores evolutivos basados en progreso
                        let baseProgress = i / totalElements;
                        let r = 50 + p.sin(baseProgress * p.TWO_PI + p.frameCount * 0.02) * 100;
                        let g = 100 + p.cos(baseProgress * p.TWO_PI * 1.3) * 120;
                        let b = 80 + p.sin(baseProgress * p.TWO_PI * 1.8) * 150;
                        
                        p.stroke(r, g, b, alpha);
                        p.strokeWeight(element.size);
                        
                        // Efecto de crecimiento orgánico
                        let growthFactor = p.constrain(elementAge, 0, 1);
                        let currentSize = element.size * growthFactor;
                        
                        p.strokeWeight(currentSize);
                        p.point(element.x, element.y);
                        
                        // Conexiones orgánicas entre puntos cercanos
                        if (i > 0 && p.random() < 0.08) {{
                            let prevElement = artElements[i-1];
                            let distance = p.dist(element.x, element.y, prevElement.x, prevElement.y);
                            if (distance < 80) {{
                                p.strokeWeight(0.5);
                                p.stroke(r * 0.7, g * 0.7, b * 0.7, alpha * 0.6);
                                p.line(element.x, element.y, prevElement.x, prevElement.y);
                            }}
                        }}
                        
                        element.drawn = true;
                    }}
                }}
                
                // Efectos adicionales de energía genética
                if (progress > 0.3 && p.frameCount % 60 === 0) {{
                    addGeneticEffects(progress);
                }}
            }}
            
            function addGeneticEffects(progress) {{
                p.stroke(255, 255, 255, 80);
                p.strokeWeight(0.5);
                p.noFill();
                let centerX = p.width / 2;
                let centerY = p.height / 2;
                p.circle(centerX, centerY, progress * 300);
            }}
            
            function drawCompleteArt() {{
                for (let i = 0; i < artElements.length; i++) {{
                    let element = artElements[i];
                    let baseProgress = i / totalElements;
                    let r = 50 + p.sin(baseProgress * p.TWO_PI + p.frameCount * 0.01) * 100;
                    let g = 100 + p.cos(baseProgress * p.TWO_PI * 1.3) * 120;
                    let b = 80 + p.sin(baseProgress * p.TWO_PI * 1.8) * 150;
                    
                    p.stroke(r, g, b, 255);
                    p.strokeWeight(element.size);
                    p.point(element.x, element.y);
                }}
            }}
        }};
        
        function updateProgressMessage_{canvas_id}() {{
            const progressElement = document.getElementById('art-progress-text-{canvas_id}');
            if (progressElement && currentMessageIndex < progressMessages.length) {{
                progressElement.style.opacity = '0';
                progressElement.style.transition = 'opacity 0.5s ease-in-out';
                
                setTimeout(() => {{
                    progressElement.textContent = progressMessages[currentMessageIndex];
                    
                    const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff'];
                    progressElement.style.color = colors[currentMessageIndex % colors.length];
                    progressElement.style.opacity = '1';
                    
                    currentMessageIndex++;
                    
                    if (currentMessageIndex >= progressMessages.length) {{
                        setTimeout(() => {{
                            progressElement.style.color = '#00ff88';
                            progressElement.style.fontWeight = 'bold';
                            progressElement.style.fontSize = '16px';
                        }}, 500);
                    }}
                }}, 500);
            }}
        }}
        
        new p5(progressiveArtSketch_{canvas_id});
        </script>
    </div>
    """

def crear_visualizacion_animada(fig_original, genetic_profile, organism_name):
    """Crea una visualización con animación infinita sobre la imagen terminada"""
    import plotly.graph_objects as go
    import numpy as np
    
    # Extraer datos de la figura original
    original_traces = list(fig_original.data)
    
    # Crear múltiples frames para la animación
    frames = []
    total_frames = 60  # 60 frames para animación suave
    
    for frame_num in range(total_frames):
        frame_data = []
        time_factor = frame_num / total_frames * 2 * np.pi  # Ciclo completo
        
        for trace_idx, trace in enumerate(original_traces):
            if hasattr(trace, 'x') and hasattr(trace, 'y'):
                # Efectos de animación basados en perfil genético
                
                # Efecto de pulsación (latido del ADN)
                pulse_intensity = 0.8 + 0.2 * np.sin(time_factor * 2)
                
                # Efecto de rotación de colores (evolución cromática)
                color_shift = np.sin(time_factor + trace_idx) * 0.3
                
                # Efecto de respiración (cambio de opacidad)
                breathing = 0.7 + 0.3 * np.sin(time_factor * 1.5)
                
                # Obtener propiedades seguras
                marker_size = 4
                if hasattr(trace, 'marker') and trace.marker and hasattr(trace.marker, 'size'):
                    if trace.marker.size is not None:
                        marker_size = trace.marker.size
                
                marker_color = '#00ff88'
                if hasattr(trace, 'marker') and trace.marker and hasattr(trace.marker, 'color'):
                    if trace.marker.color is not None:
                        marker_color = trace.marker.color
                
                # Crear traza animada
                animated_trace = go.Scatter(
                    x=trace.x,
                    y=trace.y,
                    mode=trace.mode,
                    marker=dict(
                        size=marker_size * pulse_intensity,
                        color=marker_color,
                        opacity=breathing,
                        line=dict(
                            color='rgba(255,255,255,0.3)',
                            width=1
                        )
                    ),
                    line=dict(
                        color=marker_color,
                        width=2 * pulse_intensity,
                        dash='solid'
                    ),
                    showlegend=False,
                    name=f"Genoma Vivo {trace_idx}"
                )
                frame_data.append(animated_trace)
        
        # Añadir efectos de partículas flotantes para genes activos
        if frame_num % 10 == 0:  # Cada 10 frames, añadir partículas especiales
            n_particles = 20
            particle_x = np.random.uniform(-0.5, 1.5, n_particles)
            particle_y = np.random.uniform(-0.5, 1.5, n_particles)
            
            particles = go.Scatter(
                x=particle_x,
                y=particle_y,
                mode='markers',
                marker=dict(
                    size=np.random.uniform(1, 3, n_particles),
                    color='rgba(255,255,255,0.4)',
                    symbol='star'
                ),
                showlegend=False,
                name="Genes Activos"
            )
            frame_data.append(particles)
        
        frames.append(go.Frame(data=frame_data, name=str(frame_num)))
    
    # Crear figura animada
    animated_fig = go.Figure(
        data=frames[0].data if frames else [],
        frames=frames
    )
    
    # Configurar animación automática infinita
    animated_fig.update_layout(
        title=f"🧬 {organism_name} - Genoma Vivo en Movimiento",
        template="plotly_dark",
        plot_bgcolor='rgba(5,10,15,1)',
        paper_bgcolor='rgba(5,10,15,1)',
        font=dict(color='white', size=14),
        xaxis=dict(
            showgrid=False, 
            zeroline=False,
            showticklabels=False,
            title=""
        ),
        yaxis=dict(
            showgrid=False, 
            zeroline=False,
            showticklabels=False,
            title=""
        ),
        height=600,
        updatemenus=[{
            "type": "buttons",
            "direction": "left",
            "pad": {"r": 10, "t": 87},
            "showactive": False,
            "x": 0.1,
            "xanchor": "right",
            "y": 0,
            "yanchor": "top",
            "buttons": [
                {
                    "label": "▶ Play",
                    "method": "animate",
                    "args": [None, {
                        "frame": {"duration": 100, "redraw": True},
                        "fromcurrent": True,
                        "transition": {"duration": 50, "easing": "quadratic-in-out"},
                        "mode": "immediate"
                    }]
                },
                {
                    "label": "⏸ Pause",
                    "method": "animate",
                    "args": [[None], {
                        "frame": {"duration": 0, "redraw": False},
                        "mode": "immediate",
                        "transition": {"duration": 0}
                    }]
                }
            ]
        }],
        annotations=[
            dict(
                text="💫 Genoma en movimiento eterno - patrones que evolucionan infinitamente",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.5, y=-0.1, xanchor='center', yanchor='bottom',
                font=dict(size=12, color='#cccccc')
            )
        ]
    )
    
    # Configurar para que inicie automáticamente
    animated_fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 100
    
    return animated_fig

def crear_patron_mamifero(n_points, paleta, genetic_profile):
    """Patrón cálido y orgánico para mamíferos"""
    import numpy as np
    import plotly.graph_objects as go
    
    traces = []
    
    # Estructura base: espiral dorada orgánica
    golden_ratio = 1.618033988749
    for layer in range(5):
        angles = np.linspace(0, 8 * np.pi, n_points // 5)
        r = np.sqrt(angles) * 0.1 * (layer + 1)
        x = r * np.cos(angles * golden_ratio) * (1 + 0.1 * np.sin(angles * 3))
        y = r * np.sin(angles * golden_ratio) * (1 + 0.1 * np.cos(angles * 3))
        
        # Color único para esta capa
        layer_color = paleta['primary'][layer % len(paleta['primary'])]
        
        traces.append(go.Scatter(
            x=x, y=y, mode='markers',
            marker=dict(
                size=np.random.uniform(2, 8, len(x)),
                color=layer_color,
                opacity=0.7,
                line=dict(color=paleta['secondary'][0], width=0.5)
            ),
            showlegend=False
        ))
    
    # Conexiones familiares (vínculos sociales)
    for i in range(20):
        x_line = np.random.uniform(-0.8, 0.8, 2)
        y_line = np.random.uniform(-0.8, 0.8, 2)
        traces.append(go.Scatter(
            x=x_line, y=y_line, mode='lines',
            line=dict(color=paleta['accent'][2], width=1, dash='dot'),
            showlegend=False
        ))
    
    return traces

def crear_patron_acuatico(n_points, paleta, genetic_profile):
    """Patrón fluido y ondulante para especies acuáticas"""
    import numpy as np
    import plotly.graph_objects as go
    
    traces = []
    
    # Ondas fluidas multicapa
    for wave in range(7):
        t = np.linspace(0, 4 * np.pi, max(10, n_points // 7))
        amplitude = 0.6 - wave * 0.08
        frequency = 2 + wave * 0.5
        
        x = t / (2 * np.pi) - 1
        y = amplitude * np.sin(frequency * t) * np.exp(-0.1 * wave * t)
        
        # Efectos de corriente
        flow_x = x + 0.1 * np.sin(t * 1.5)
        flow_y = y + 0.05 * np.cos(t * 2.3)
        
        color_cycle = wave % len(paleta['primary'])
        
        traces.append(go.Scatter(
            x=flow_x, y=flow_y, mode='lines+markers',
            line=dict(color=paleta['primary'][color_cycle], width=3),
            marker=dict(
                size=4, color=paleta['secondary'][color_cycle],
                opacity=0.8, symbol='circle'
            ),
            showlegend=False
        ))
    
    # Burbujas flotantes
    bubble_x = np.random.uniform(-1, 1, 50)
    bubble_y = np.random.uniform(-1, 1, 50)
    bubble_sizes = np.random.uniform(5, 15, 50)
    
    traces.append(go.Scatter(
        x=bubble_x, y=bubble_y, mode='markers',
        marker=dict(
            size=bubble_sizes,
            color=paleta['accent'][0],
            opacity=0.4,
            line=dict(color=paleta['secondary'][1], width=1)
        ),
        showlegend=False
    ))
    
    return traces

def crear_patron_aviario(n_points, paleta, genetic_profile):
    """Patrón elevado y radiante para aves"""
    import numpy as np
    import plotly.graph_objects as go
    
    traces = []
    
    # Plumas radiantes desde el centro
    for feather in range(12):
        angle_base = feather * 2 * np.pi / 12
        
        # Estructura de pluma
        spine_length = np.linspace(0, 0.8, 40)
        spine_x = spine_length * np.cos(angle_base)
        spine_y = spine_length * np.sin(angle_base)
        
        # Bárbulas de la pluma
        for barb in range(8):
            barb_pos = barb / 8
            barb_length = 0.1 * (1 - barb_pos)
            
            barb_angle = angle_base + np.pi/2
            barb_x = spine_x[barb * 5] + np.linspace(0, barb_length, 10) * np.cos(barb_angle)
            barb_y = spine_y[barb * 5] + np.linspace(0, barb_length, 10) * np.sin(barb_angle)
            
            color_idx = feather % len(paleta['primary'])
            
            traces.append(go.Scatter(
                x=barb_x, y=barb_y, mode='lines',
                line=dict(color=paleta['primary'][color_idx], width=2),
                showlegend=False
            ))
    
    # Patrones de vuelo
    flight_paths = 3
    for path in range(flight_paths):
        t = np.linspace(0, 2 * np.pi, 100)
        radius = 0.6 + path * 0.1
        x = radius * np.cos(t + path * np.pi/3) * (1 + 0.2 * np.sin(3 * t))
        y = radius * np.sin(t + path * np.pi/3) * (1 + 0.2 * np.cos(3 * t))
        
        traces.append(go.Scatter(
            x=x, y=y, mode='lines',
            line=dict(color=paleta['accent'][path % len(paleta['accent'])], width=1, dash='dash'),
            showlegend=False
        ))
    
    return traces

def crear_patron_reptil(n_points, paleta, genetic_profile):
    """Patrón escamoso y angular para reptiles"""
    import numpy as np
    import plotly.graph_objects as go
    
    traces = []
    
    # Estructura de escamas hexagonales simplificada
    hex_layers = 3
    for layer in range(hex_layers):
        radius = 0.3 + layer * 0.2
        n_hexagons = 6 + layer * 2
        
        color_idx = layer % len(paleta['primary'])
        
        # Círculo de escamas
        angles = np.linspace(0, 2 * np.pi, n_hexagons, endpoint=False)
        x_hex = radius * np.cos(angles)
        y_hex = radius * np.sin(angles)
        
        traces.append(go.Scatter(
            x=x_hex, y=y_hex, mode='markers',
            marker=dict(
                size=15 - layer * 3,
                color=paleta['primary'][color_idx],
                opacity=0.7,
                symbol='hexagon',
                line=dict(color=paleta['secondary'][color_idx], width=2)
            ),
            showlegend=False
        ))
    
    # Patrones de camuflaje
    for stripe in range(6):
        y_pos = -0.6 + stripe * 0.2
        x_wave = np.linspace(-0.8, 0.8, 40)
        y_wave = y_pos + 0.05 * np.sin(x_wave * 6 + stripe)
        
        stripe_color = paleta['accent'][stripe % len(paleta['accent'])]
        
        traces.append(go.Scatter(
            x=x_wave, y=y_wave, mode='lines',
            line=dict(color=stripe_color, width=3),
            showlegend=False
        ))
    
    return traces

def crear_patron_artropodo(n_points, paleta, genetic_profile):
    """Patrón segmentado y complejo para artrópodos"""
    import numpy as np
    import plotly.graph_objects as go
    
    traces = []
    
    # Estructura segmentada central
    segments = 8
    for seg in range(segments):
        y_center = -0.6 + seg * 0.15
        
        # Cuerpo del segmento
        x_body = np.linspace(-0.3, 0.3, 20)
        y_body = np.full(20, y_center)
        
        # Patas laterales
        if seg % 2 == 0:  # Segmentos con patas
            for side in [-1, 1]:
                leg_x = np.linspace(0.3 * side, 0.6 * side, 10)
                leg_y = y_center + 0.05 * np.sin(np.linspace(0, np.pi, 10))
                
                traces.append(go.Scatter(
                    x=leg_x, y=leg_y, mode='lines+markers',
                    line=dict(color=paleta['primary'][seg % len(paleta['primary'])], width=3),
                    marker=dict(size=4, color=paleta['secondary'][seg % len(paleta['secondary'])]),
                    showlegend=False
                ))
        
        color_idx = seg % len(paleta['primary'])
        traces.append(go.Scatter(
            x=x_body, y=y_body, mode='lines+markers',
            line=dict(color=paleta['primary'][color_idx], width=5),
            marker=dict(size=6, color=paleta['accent'][color_idx % len(paleta['accent'])]),
            showlegend=False
        ))
    
    # Patrones complejos tipo red neural
    web_points = 30
    web_x = np.random.uniform(-0.8, 0.8, web_points)
    web_y = np.random.uniform(-0.8, 0.8, web_points)
    
    # Conectar puntos cercanos
    for i in range(web_points):
        for j in range(i+1, web_points):
            dist = np.sqrt((web_x[i] - web_x[j])**2 + (web_y[i] - web_y[j])**2)
            if dist < 0.3:
                traces.append(go.Scatter(
                    x=[web_x[i], web_x[j]], y=[web_y[i], web_y[j]], mode='lines',
                    line=dict(color=paleta['accent'][2], width=1, dash='dot'),
                    showlegend=False
                ))
    
    return traces

def crear_patron_botanico(n_points, paleta, genetic_profile):
    """Patrón orgánico y ramificado para plantas"""
    import numpy as np
    import plotly.graph_objects as go
    
    traces = []
    
    # Sistema de raíces simplificado
    for root in range(5):
        angle = root * 2 * np.pi / 5 + np.pi  # Hacia abajo
        length = np.linspace(0, 0.6, 25)
        
        x = length * 0.8 * np.cos(angle)
        y = -0.1 + length * 0.8 * np.sin(angle)
        
        # Añadir ondulación orgánica
        x += 0.02 * np.sin(length * 8)
        y += 0.01 * np.cos(length * 12)
        
        color_idx = root % len(paleta['primary'])
        
        traces.append(go.Scatter(
            x=x, y=y, mode='lines',
            line=dict(color=paleta['primary'][color_idx], width=3),
            showlegend=False
        ))
    
    # Follaje superior simplificado
    leaf_clusters = 8
    for cluster in range(leaf_clusters):
        angle = cluster * 2 * np.pi / leaf_clusters
        radius = 0.4 + 0.15 * np.sin(cluster)
        
        center_x = radius * np.cos(angle)
        center_y = 0.2 + radius * np.sin(angle)
        
        # Forma de hoja simplificada
        t = np.linspace(0, 2 * np.pi, 15)
        x_leaf = center_x + 0.06 * np.cos(t) * (1 + 0.3 * np.cos(2*t))
        y_leaf = center_y + 0.08 * np.sin(t)
        
        leaf_color = paleta['accent'][cluster % len(paleta['accent'])]
        fill_color = paleta['secondary'][cluster % len(paleta['secondary'])]
        
        traces.append(go.Scatter(
            x=x_leaf, y=y_leaf, mode='lines',
            line=dict(color=leaf_color, width=2),
            fill='toself',
            fillcolor=fill_color,
            opacity=0.6,
            showlegend=False
        ))
    
    return traces

def crear_patron_general(n_points, paleta, genetic_profile):
    """Patrón cósmico y abstracto para especies generales"""
    import numpy as np
    import plotly.graph_objects as go
    
    traces = []
    
    # Espiral galáctica simplificada
    t = np.linspace(0, 6 * np.pi, min(n_points, 200))
    r = 0.1 * t
    x = r * np.cos(t) * np.exp(-0.1 * t)
    y = r * np.sin(t) * np.exp(-0.1 * t)
    
    # Color único para la espiral
    spiral_color = paleta['primary'][0]
    
    traces.append(go.Scatter(
        x=x, y=y, mode='markers',
        marker=dict(size=np.linspace(2, 8, len(x)), color=spiral_color, opacity=0.8),
        showlegend=False
    ))
    
    # Anillos concéntricos
    for ring in range(5):
        theta = np.linspace(0, 2 * np.pi, 60)
        radius = 0.2 + ring * 0.15
        x_ring = radius * np.cos(theta)
        y_ring = radius * np.sin(theta)
        
        ring_color = paleta['accent'][ring % len(paleta['accent'])]
        
        traces.append(go.Scatter(
            x=x_ring, y=y_ring, mode='lines',
            line=dict(color=ring_color, width=1, dash='dash'),
            showlegend=False
        ))
    
    return traces

def crear_elementos_complejidad(genetic_profile, paleta, sequence_length):
    """Añade elementos visuales basados en la complejidad genética"""
    import numpy as np
    import plotly.graph_objects as go
    
    traces = []
    
    # Nodos de alta entropía
    entropy = genetic_profile.get('entropy', 0)
    if entropy > 0.8:
        n_entropy_nodes = min(int(entropy * 15), 30)
        nodes_x = np.random.uniform(-0.9, 0.9, n_entropy_nodes)
        nodes_y = np.random.uniform(-0.9, 0.9, n_entropy_nodes)
        
        traces.append(go.Scatter(
            x=nodes_x, y=nodes_y, mode='markers',
            marker=dict(
                size=np.random.uniform(8, 15, n_entropy_nodes),
                color=paleta['accent'][0],
                opacity=0.6,
                symbol='star'
            ),
            showlegend=False
        ))
    
    # Campos de frecuencia para secuencias largas
    if sequence_length > 50000:
        field_density = min(sequence_length // 10000, 40)
        field_x = np.random.uniform(-1, 1, field_density)
        field_y = np.random.uniform(-1, 1, field_density)
        
        traces.append(go.Scatter(
            x=field_x, y=field_y, mode='markers',
            marker=dict(
                size=3,
                color=paleta['secondary'][1],
                opacity=0.3,
                symbol='diamond'
            ),
            showlegend=False
        ))
    
    return traces

if __name__ == "__main__":
    main()