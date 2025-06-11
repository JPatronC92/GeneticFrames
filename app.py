import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
from datetime import datetime
import streamlit.components.v1 as components
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
import urllib.parse
import math
from scipy.spatial import Voronoi, voronoi_plot_2d
from scipy.spatial.distance import cdist
import re
from collections import Counter
import pandas as pd

# =============== FASTA PROCESSING & BIOLOGICAL ANALYSIS ===============

def parse_fasta_sequence(fasta_text):
    """Parsea texto FASTA y retorna secuencia limpia con metadatos"""
    lines = fasta_text.strip().split('\n')
    header = ""
    sequence = ""
    
    for line in lines:
        if line.startswith('>'):
            header = line[1:].strip()
        else:
            sequence += line.strip().upper()
    
    clean_sequence = re.sub(r'[^ATCGN]', '', sequence)
    
    organism_name = "Secuencia personalizada"
    gene_info = ""
    
    if header:
        parts = header.split(' ')
        if len(parts) >= 2:
            organism_name = f"{parts[0]} {parts[1]}"
        gene_info = header
    
    return {
        'sequence': clean_sequence,
        'header': header,
        'organism_name': organism_name,
        'gene_info': gene_info,
        'length': len(clean_sequence)
    }

def process_sequence_region(sequence, method, start_pos=1, length=1000):
    """Procesa región específica según método seleccionado"""
    seq_len = len(sequence)
    
    if method == "Completa":
        if seq_len > 10000:
            return sample_representative_sequence(sequence, 5000)
        return sequence
    elif method == "Primeros N bases":
        return sequence[:length]
    elif method == "Región específica":
        start_idx = max(0, start_pos - 1)
        end_idx = min(seq_len, start_idx + length)
        return sequence[start_idx:end_idx]
    elif method == "Muestreo representativo":
        return sample_representative_sequence(sequence, length)
    
    return sequence

def sample_representative_sequence(sequence, target_length):
    """Genera muestra representativa manteniendo características"""
    seq_len = len(sequence)
    if seq_len <= target_length:
        return sequence
    
    segment_size = seq_len // (target_length // 100)
    sampled = ""
    
    for i in range(0, seq_len, segment_size):
        end = min(i + 100, seq_len)
        sampled += sequence[i:end]
        if len(sampled) >= target_length:
            break
    
    return sampled[:target_length]

def analyze_sequence_biology(sequence, organism_name=""):
    """Análisis biológico avanzado de la secuencia"""
    analysis = {}
    seq_len = len(sequence)
    
    base_counts = {
        'A': sequence.count('A'),
        'T': sequence.count('T'),
        'C': sequence.count('C'),
        'G': sequence.count('G'),
        'N': sequence.count('N')
    }
    
    total_known = sum([base_counts[b] for b in 'ATCG'])
    
    if total_known > 0:
        analysis['base_composition'] = {
            'A': base_counts['A'] / total_known,
            'T': base_counts['T'] / total_known,
            'C': base_counts['C'] / total_known,
            'G': base_counts['G'] / total_known
        }
        
        analysis['gc_content'] = (base_counts['C'] + base_counts['G']) / total_known
        analysis['at_content'] = (base_counts['A'] + base_counts['T']) / total_known
        analysis['gc_skew'] = (base_counts['G'] - base_counts['C']) / (base_counts['G'] + base_counts['C']) if (base_counts['G'] + base_counts['C']) > 0 else 0
        analysis['at_skew'] = (base_counts['A'] - base_counts['T']) / (base_counts['A'] + base_counts['T']) if (base_counts['A'] + base_counts['T']) > 0 else 0
    
    analysis['length'] = seq_len
    analysis['complexity'] = calculate_sequence_complexity(sequence)
    analysis['repetitiveness'] = calculate_repetitiveness(sequence)
    analysis['dinucleotide_patterns'] = analyze_dinucleotide_patterns(sequence)
    analysis['orf_analysis'] = analyze_open_reading_frames(sequence)
    analysis['genetic_motifs'] = find_genetic_motifs(sequence)
    
    return analysis

def calculate_sequence_complexity(sequence):
    """Calcula complejidad usando entropía de Shannon"""
    if not sequence:
        return 0
    
    counts = Counter(sequence)
    total = len(sequence)
    entropy = 0
    
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy

def calculate_repetitiveness(sequence):
    """Calcula nivel de repetitividad"""
    if len(sequence) < 10:
        return 0
    
    repeat_score = 0
    window_sizes = [2, 3, 4, 5, 6]
    
    for window_size in window_sizes:
        if len(sequence) < window_size * 2:
            continue
            
        patterns = {}
        for i in range(len(sequence) - window_size + 1):
            pattern = sequence[i:i + window_size]
            patterns[pattern] = patterns.get(pattern, 0) + 1
        
        repeated = sum(1 for count in patterns.values() if count > 1)
        repeat_score += repeated / len(patterns) if patterns else 0
    
    return repeat_score / len(window_sizes)

def analyze_dinucleotide_patterns(sequence):
    """Analiza patrones de dinucleótidos"""
    dinucleotides = {}
    
    for i in range(len(sequence) - 1):
        dinuc = sequence[i:i+2]
        if len(dinuc) == 2 and all(base in 'ATCG' for base in dinuc):
            dinucleotides[dinuc] = dinucleotides.get(dinuc, 0) + 1
    
    total = sum(dinucleotides.values())
    if total > 0:
        for dinuc in dinucleotides:
            dinucleotides[dinuc] = dinucleotides[dinuc] / total
    
    return dinucleotides

def analyze_open_reading_frames(sequence):
    """Análisis básico de marcos de lectura abiertos"""
    start_codons = ['ATG']
    stop_codons = ['TAA', 'TAG', 'TGA']
    orfs = []
    
    for frame in range(3):
        i = frame
        while i < len(sequence) - 2:
            codon = sequence[i:i+3]
            
            if codon in start_codons:
                start_pos = i
                j = i + 3
                
                while j < len(sequence) - 2:
                    stop_codon = sequence[j:j+3]
                    if stop_codon in stop_codons:
                        orf_length = j - start_pos + 3
                        if orf_length >= 150:
                            orfs.append({
                                'start': start_pos,
                                'end': j + 3,
                                'length': orf_length,
                                'frame': frame + 1
                            })
                        break
                    j += 3
                
                i = j if j < len(sequence) else len(sequence)
            else:
                i += 3
    
    return orfs

def find_genetic_motifs(sequence):
    """Busca motivos genéticos comunes"""
    motifs = {}
    
    common_motifs = {
        'TATA_box': 'TATAAA',
        'Kozak_sequence': 'CCACCATGG',
        'Poly_A_signal': 'AATAAA',
        'CpG_island': 'CG',
        'CAAT_box': 'CAAT'
    }
    
    for motif_name, motif_seq in common_motifs.items():
        count = 0
        positions = []
        
        for i in range(len(sequence) - len(motif_seq) + 1):
            if sequence[i:i+len(motif_seq)] == motif_seq:
                count += 1
                positions.append(i)
        
        if count > 0:
            motifs[motif_name] = {
                'count': count,
                'positions': positions[:10],
                'frequency': count / (len(sequence) - len(motif_seq) + 1)
            }
    
    return motifs

def compare_sequences_biology(seq1, seq2, organism1, organism2):
    """Análisis comparativo completo entre dos secuencias"""
    analysis1 = analyze_sequence_biology(seq1, organism1)
    analysis2 = analyze_sequence_biology(seq2, organism2)
    
    comparison = {
        'species': [organism1, organism2],
        'sequences': [seq1, seq2],
        'individual_analysis': [analysis1, analysis2],
        'differences': {},
        'similarities': {},
        'evolutionary_insights': {}
    }
    
    # Comparar composición de bases
    if 'base_composition' in analysis1 and 'base_composition' in analysis2:
        base_diff = {}
        for base in ['A', 'T', 'C', 'G']:
            diff = abs(analysis1['base_composition'][base] - analysis2['base_composition'][base])
            base_diff[base] = {
                'difference': diff,
                'species1': analysis1['base_composition'][base],
                'species2': analysis2['base_composition'][base]
            }
        comparison['differences']['base_composition'] = base_diff
    
    # Comparar contenido GC
    gc_diff = abs(analysis1.get('gc_content', 0) - analysis2.get('gc_content', 0))
    comparison['differences']['gc_content'] = {
        'difference': gc_diff,
        'species1': analysis1.get('gc_content', 0),
        'species2': analysis2.get('gc_content', 0),
        'significance': 'Alta' if gc_diff > 0.1 else 'Media' if gc_diff > 0.05 else 'Baja'
    }
    
    # Comparar complejidad
    complexity_diff = abs(analysis1.get('complexity', 0) - analysis2.get('complexity', 0))
    comparison['differences']['complexity'] = {
        'difference': complexity_diff,
        'species1': analysis1.get('complexity', 0),
        'species2': analysis2.get('complexity', 0)
    }
    
    # Comparar patrones de dinucleótidos
    dinuc1 = analysis1.get('dinucleotide_patterns', {})
    dinuc2 = analysis2.get('dinucleotide_patterns', {})
    
    dinuc_comparison = {}
    all_dinucs = set(dinuc1.keys()) | set(dinuc2.keys())
    
    for dinuc in all_dinucs:
        freq1 = dinuc1.get(dinuc, 0)
        freq2 = dinuc2.get(dinuc, 0)
        dinuc_comparison[dinuc] = {
            'species1': freq1,
            'species2': freq2,
            'difference': abs(freq1 - freq2)
        }
    
    comparison['differences']['dinucleotide_patterns'] = dinuc_comparison
    
    # Análisis de ORFs
    orfs1 = analysis1.get('orf_analysis', [])
    orfs2 = analysis2.get('orf_analysis', [])
    
    comparison['differences']['coding_potential'] = {
        'orfs_count': [len(orfs1), len(orfs2)],
        'avg_orf_length': [
            sum(orf['length'] for orf in orfs1) / len(orfs1) if orfs1 else 0,
            sum(orf['length'] for orf in orfs2) / len(orfs2) if orfs2 else 0
        ]
    }
    
    # Motivos conservados
    motifs1 = set(analysis1.get('genetic_motifs', {}).keys())
    motifs2 = set(analysis2.get('genetic_motifs', {}).keys())
    
    comparison['similarities']['shared_motifs'] = list(motifs1 & motifs2)
    comparison['differences']['unique_motifs'] = {
        'species1_only': list(motifs1 - motifs2),
        'species2_only': list(motifs2 - motifs1)
    }
    
    # Insights evolutivos
    comparison['evolutionary_insights'] = generate_evolutionary_insights(analysis1, analysis2, organism1, organism2)
    
    return comparison

def generate_evolutionary_insights(analysis1, analysis2, organism1, organism2):
    """Genera insights evolutivos basados en diferencias genómicas"""
    insights = []
    
    gc1 = analysis1.get('gc_content', 0)
    gc2 = analysis2.get('gc_content', 0)
    
    # Análisis de contenido GC
    if abs(gc1 - gc2) > 0.05:
        if gc1 > gc2:
            insights.append(f"{organism1} muestra mayor contenido GC ({gc1:.2%} vs {gc2:.2%}), sugiriendo adaptación a ambientes de mayor estabilidad térmica")
        else:
            insights.append(f"{organism2} presenta mayor contenido GC ({gc2:.2%} vs {gc1:.2%}), indicando posible adaptación termófila")
    
    # Análisis de complejidad
    comp1 = analysis1.get('complexity', 0)
    comp2 = analysis2.get('complexity', 0)
    
    if abs(comp1 - comp2) > 0.2:
        if comp1 > comp2:
            insights.append(f"{organism1} exhibe mayor complejidad genómica (Shannon: {comp1:.3f}), sugiriendo mayor diversidad funcional")
        else:
            insights.append(f"{organism2} muestra mayor complejidad genómica (Shannon: {comp2:.3f}), indicando diversificación evolutiva")
    
    # Análisis de ORFs
    orfs1 = len(analysis1.get('orf_analysis', []))
    orfs2 = len(analysis2.get('orf_analysis', []))
    
    if abs(orfs1 - orfs2) > 2:
        if orfs1 > orfs2:
            insights.append(f"{organism1} presenta {orfs1} ORFs vs {orfs2} en {organism2}, indicando mayor densidad de regiones codificantes")
        else:
            insights.append(f"{organism2} muestra {orfs2} ORFs vs {orfs1} en {organism1}, sugiriendo región más rica en genes")
    
    # Análisis filogenético
    if "tiger" in organism1.lower() and "wolf" in organism2.lower():
        insights.append("Comparación Carnívora: Tigre (Felidae) vs Lobo (Canidae) - divergencia evolutiva ~55 millones de años")
        insights.append("Diferencias esperadas en genes de visión nocturna, estructura muscular y patrones de caza")
    elif "human" in organism1.lower() or "human" in organism2.lower():
        insights.append("Comparación con Homo sapiens: diferencias en capacidad cognitiva, metabolismo y adaptaciones específicas")
    
    return insights

def create_comparative_visualization(seq1, seq2, organism1, organism2, style='voronoi', theme='scientific'):
    """Crea visualización comparativa que resalta diferencias dramáticas entre especies"""
    
    # Análisis comparativo
    comparison = compare_sequences_biology(seq1, seq2, organism1, organism2)
    
    # Crear visualización lado a lado
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[f"🧬 {organism1}", f"🧬 {organism2}"],
        specs=[[{"type": "scatter"}, {"type": "scatter"}]]
    )
    
    colors = COLOR_THEMES.get(theme, COLOR_THEMES['scientific'])
    
    # Generar semillas genéticas para cada especie
    genetic_seed1 = crear_semilla_genetica(seq1, organism1)
    genetic_seed2 = crear_semilla_genetica(seq2, organism2)
    
    # Amplificar diferencias visuales basadas en análisis biológico
    differences = comparison['differences']
    gc_diff = differences['gc_content']['difference']
    complexity_diff = differences['complexity']['difference']
    
    # Modificar colores y patrones según diferencias genéticas
    enhanced_colors1 = enhance_colors_for_species(colors, genetic_seed1, organism1, gc_diff)
    enhanced_colors2 = enhance_colors_for_species(colors, genetic_seed2, organism2, gc_diff)
    
    # Crear visualizaciones con diferencias amplificadas
    if style == 'voronoi':
        fig1_data = create_enhanced_comparative_voronoi(seq1, enhanced_colors1, genetic_seed1, organism1, comparison)
        fig2_data = create_enhanced_comparative_voronoi(seq2, enhanced_colors2, genetic_seed2, organism2, comparison)
    elif style == 'lsystem':
        fig1_data = create_enhanced_comparative_lsystem(seq1, enhanced_colors1, genetic_seed1, organism1, comparison)
        fig2_data = create_enhanced_comparative_lsystem(seq2, enhanced_colors2, genetic_seed2, organism2, comparison)
    elif style == 'cellular':
        fig1_data = create_enhanced_comparative_cellular(seq1, enhanced_colors1, genetic_seed1, organism1, comparison)
        fig2_data = create_enhanced_comparative_cellular(seq2, enhanced_colors2, genetic_seed2, organism2, comparison)
    else:
        fig1_data = create_enhanced_comparative_scatter(seq1, enhanced_colors1, genetic_seed1, organism1, comparison)
        fig2_data = create_enhanced_comparative_scatter(seq2, enhanced_colors2, genetic_seed2, organism2, comparison)
    
    # Agregar datos a subplots
    for trace in fig1_data:
        fig.add_trace(trace, row=1, col=1)
    
    for trace in fig2_data:
        fig.add_trace(trace, row=1, col=2)
    
    # Configurar layout con título informativo
    title_text = f"Diferencias Genéticas Visualizadas: {organism1} vs {organism2}<br>"
    title_text += f"<sub>GC Diff: {gc_diff:.3f} | Complexity Diff: {complexity_diff:.3f}</sub>"
    
    fig.update_layout(
        title=title_text,
        showlegend=False,
        plot_bgcolor='#000011',
        paper_bgcolor='#000011',
        height=700,
        margin=dict(l=0, r=0, t=80, b=0)
    )
    
    # Actualizar ejes
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    
    return fig, comparison

def enhance_colors_for_species(base_colors, genetic_seed, organism, gc_diff):
    """Modifica colores según características genéticas específicas de la especie"""
    enhanced = base_colors.copy()
    
    # Modificar colores según contenido GC
    gc_content = genetic_seed.get('base_ratios', {}).get('gc_content', 0.5)
    
    # Felinos (tigers, lions) - colores más cálidos y saturados
    if 'tiger' in organism.lower() or 'panthera' in organism.lower():
        enhanced['A'] = '#FF4500'  # Naranja brillante
        enhanced['T'] = '#FFD700'  # Dorado
        enhanced['C'] = '#FF6347'  # Rojo tomate
        enhanced['G'] = '#FF8C00'  # Naranja oscuro
        
    # Cánidos (wolves, dogs) - colores más fríos y azulados
    elif 'wolf' in organism.lower() or 'canis' in organism.lower():
        enhanced['A'] = '#4169E1'  # Azul real
        enhanced['T'] = '#00CED1'  # Turquesa
        enhanced['C'] = '#1E90FF'  # Azul dodger
        enhanced['G'] = '#6495ED'  # Azul acero
        
    # Humanos - colores violetas/púrpuras
    elif 'human' in organism.lower() or 'sapiens' in organism.lower():
        enhanced['A'] = '#9370DB'  # Violeta medio
        enhanced['T'] = '#8A2BE2'  # Violeta azul
        enhanced['C'] = '#9932CC'  # Orquídea oscura
        enhanced['G'] = '#BA55D3'  # Orquídea media
        
    # Marinos - colores azul-verde
    elif 'tursiops' in organism.lower() or 'orcinus' in organism.lower():
        enhanced['A'] = '#20B2AA'  # Verde azulado claro
        enhanced['T'] = '#008B8B'  # Cian oscuro
        enhanced['C'] = '#00FFFF'  # Cian
        enhanced['G'] = '#48D1CC'  # Turquesa medio
        
    # Amplificar diferencias según GC content
    if gc_content > 0.6:  # Alto GC - colores más intensos
        for nucleotide in enhanced:
            color = enhanced[nucleotide]
            if color.startswith('#'):
                # Aumentar saturación
                enhanced[nucleotide] = color.replace('#', '#FF')[:7] if len(color) == 7 else color
    
    return enhanced

def create_enhanced_comparative_voronoi(sequence, colors, genetic_seed, organism, comparison):
    """Voronoi con diferencias amplificadas"""
    traces = []
    
    sample_size = min(300, len(sequence))
    sequence_sample = sequence[:sample_size]
    
    points = []
    nucleotide_map = {'A': 0, 'T': 1, 'C': 2, 'G': 3}
    
    # Usar características genéticas para patrones únicos
    gc_content = genetic_seed.get('base_ratios', {}).get('gc_content', 0.5)
    entropy = genetic_seed.get('entropy', 2.0)
    
    # Amplificar diferencias de posicionamiento según especie
    position_amplifier = 1.0
    if 'tiger' in organism.lower() or 'panthera' in organism.lower():
        position_amplifier = 1.5  # Patrones más dispersos (comportamiento solitario)
    elif 'wolf' in organism.lower() or 'canis' in organism.lower():
        position_amplifier = 0.8  # Patrones más agrupados (comportamiento de manada)
    
    for i in range(0, len(sequence_sample), max(1, len(sequence_sample) // 50)):
        nucleotide = sequence_sample[i]
        if nucleotide in nucleotide_map:
            # Posición base
            base_x = (i / len(sequence_sample)) * 400 - 200
            base_y = (nucleotide_map[nucleotide] * 100) - 150
            
            # Modificación específica por especie
            species_mod_x = (genetic_seed.get('pattern_signature', 0) % 1000) * 0.1 * np.sin(i * entropy * 0.1) * position_amplifier
            species_mod_y = (genetic_seed.get('positional_signature', 0) % 1000) * 0.1 * np.cos(i * gc_content * 0.1) * position_amplifier
            
            x = base_x + species_mod_x
            y = base_y + species_mod_y
            
            points.append([x, y, nucleotide])
    
    # Crear puntos con tamaños variables según importancia genética
    for point in points:
        # Tamaño basado en rareza del nucleótido en la secuencia
        nucleotide_freq = sequence_sample.count(point[2]) / len(sequence_sample)
        size = max(4, min(12, 10 * (1 - nucleotide_freq) + 6))
        
        traces.append(go.Scatter(
            x=[point[0]],
            y=[point[1]],
            mode='markers',
            marker=dict(
                color=colors[point[2]],
                size=size,
                symbol='circle',
                line=dict(color='white', width=1),
                opacity=0.9
            ),
            showlegend=False,
            hovertext=f"{organism}: {point[2]} (freq: {nucleotide_freq:.3f})"
        ))
    
    return traces

def create_enhanced_comparative_lsystem(sequence, colors, genetic_seed, organism, comparison):
    """L-System con diferencias estructurales amplificadas"""
    traces = []
    
    # Parámetros únicos según especie y análisis genético
    gc_content = genetic_seed.get('base_ratios', {}).get('gc_content', 0.5)
    entropy = genetic_seed.get('entropy', 2.0)
    
    # Reglas específicas por especie
    if 'tiger' in organism.lower() or 'panthera' in organism.lower():
        # Felinos: patrones más complejos y ramificados
        axioma = "F+F+F+F"
        reglas = {'F': 'F+F-F-F+F+F-F+F-F-F+F'}
        angulo = 60
        color_primary = colors['G']
    elif 'wolf' in organism.lower() or 'canis' in organism.lower():
        # Cánidos: patrones más lineales y organizados
        axioma = "F-F-F-F"
        reglas = {'F': 'F-F+F+F-F-F+F-F+F+F-F'}
        angulo = 90
        color_primary = colors['A']
    else:
        # Otros: patrones intermedios
        axioma = "F+F-F"
        reglas = {'F': 'F+F-F-F+F'}
        angulo = 72
        color_primary = colors['C']
    
    # Generar L-System
    secuencia_lsystem = axioma
    iteraciones = min(5, max(3, int(entropy * 1.5)))
    
    for _ in range(iteraciones):
        nueva_secuencia = ""
        for simbolo in secuencia_lsystem:
            if simbolo in reglas:
                nueva_secuencia += reglas[simbolo]
            else:
                nueva_secuencia += simbolo
        secuencia_lsystem = nueva_secuencia
    
    # Interpretar y dibujar
    x, y = 0, 0
    angulo_actual = 90
    stack = []
    puntos_x = [0]
    puntos_y = [0]
    
    longitud_base = 200 / (len(secuencia_lsystem) ** 0.4)
    
    for simbolo in secuencia_lsystem:
        if simbolo == 'F':
            x += longitud_base * np.cos(np.radians(angulo_actual))
            y += longitud_base * np.sin(np.radians(angulo_actual))
            puntos_x.append(x)
            puntos_y.append(y)
        elif simbolo == '+':
            angulo_actual += angulo
        elif simbolo == '-':
            angulo_actual -= angulo
        elif simbolo == '[':
            stack.append((x, y, angulo_actual))
        elif simbolo == ']':
            if stack:
                x, y, angulo_actual = stack.pop()
                puntos_x.append(None)
                puntos_y.append(None)
                puntos_x.append(x)
                puntos_y.append(y)
    
    traces.append(go.Scatter(
        x=puntos_x,
        y=puntos_y,
        mode='lines',
        line=dict(
            color=color_primary,
            width=3
        ),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    return traces

def create_enhanced_comparative_cellular(sequence, colors, genetic_seed, organism, comparison):
    """Autómata celular con reglas específicas por especie"""
    traces = []
    
    width = 80
    height = 40
    
    # Regla específica por especie basada en características genéticas
    base_rule = genetic_seed.get('primary_signature', 0) % 256
    
    # Modificar regla según especie
    if 'tiger' in organism.lower():
        rule_number = (base_rule + 30) % 256  # Reglas más complejas
    elif 'wolf' in organism.lower():
        rule_number = (base_rule + 110) % 256  # Reglas conocidas por generar patrones interesantes
    else:
        rule_number = base_rule
    
    rule = [(rule_number >> i) & 1 for i in range(8)]
    
    # Estado inicial específico por especie
    initial_state = [0] * width
    sample_size = min(width, len(sequence))
    
    # Mapeo específico por características genéticas
    gc_content = genetic_seed.get('base_ratios', {}).get('gc_content', 0.5)
    if gc_content > 0.6:
        nucleotide_map = {'A': 0, 'T': 1, 'C': 1, 'G': 1}  # Más activación
    else:
        nucleotide_map = {'A': 1, 'T': 0, 'C': 0, 'G': 1}  # Patrón diferente
    
    for i in range(sample_size):
        if sequence[i] in nucleotide_map:
            initial_state[i] = nucleotide_map[sequence[i]]
    
    # Generar evolución
    grid = [initial_state[:]]
    current = initial_state[:]
    
    for generation in range(height - 1):
        next_state = [0] * width
        for i in range(width):
            left = current[(i - 1) % width]
            center = current[i]
            right = current[(i + 1) % width]
            
            pattern = (left << 2) | (center << 1) | right
            next_state[i] = rule[pattern]
        
        current = next_state[:]
        grid.append(current[:])
    
    # Colorear según especie
    if 'tiger' in organism.lower():
        colorscale = [[0, '#000011'], [1, colors['G']]]
    elif 'wolf' in organism.lower():
        colorscale = [[0, '#000011'], [1, colors['A']]]
    else:
        colorscale = [[0, '#000011'], [0.5, colors['C']], [1, colors['T']]]
    
    traces.append(go.Heatmap(
        z=grid,
        colorscale=colorscale,
        showscale=False,
        hoverinfo='skip'
    ))
    
    return traces

def create_enhanced_comparative_scatter(sequence, colors, genetic_seed, organism, comparison):
    """Scatter plot con patrones únicos amplificados por especie"""
    traces = []
    
    sample_size = min(400, len(sequence))
    sequence_sample = sequence[:sample_size]
    
    # Agrupar por nucleótidos con patrones específicos
    nucleotide_positions = {'A': [], 'T': [], 'C': [], 'G': []}
    
    # Parámetros únicos por especie
    if 'tiger' in organism.lower():
        # Tigres: patrones más dispersos y agresivos
        spread_factor = 2.0
        vertical_offset = 20
    elif 'wolf' in organism.lower():
        # Lobos: patrones más agrupados y organizados
        spread_factor = 0.8
        vertical_offset = -20
    else:
        spread_factor = 1.0
        vertical_offset = 0
    
    for i, nucleotide in enumerate(sequence_sample):
        if nucleotide in nucleotide_positions:
            # Posición modulada por características genéticas y especie
            x = i + (genetic_seed.get('primary_signature', 0) % 100) * 0.02 * np.sin(i * 0.1) * spread_factor
            y = genetic_seed.get('entropy', 2.0) * 25 + np.random.normal(0, 8) + vertical_offset
            
            nucleotide_positions[nucleotide].append([x, y])
    
    # Crear trazas con tamaños y opacidades variables
    for nucleotide, positions in nucleotide_positions.items():
        if positions:
            x_vals = [pos[0] for pos in positions]
            y_vals = [pos[1] for pos in positions]
            
            # Tamaño según frecuencia del nucleótido
            freq = len(positions) / len(sequence_sample)
            size = max(3, min(8, 6 + freq * 10))
            
            traces.append(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='markers',
                marker=dict(
                    color=colors[nucleotide],
                    size=size,
                    opacity=0.8,
                    symbol='diamond' if 'tiger' in organism.lower() else 'circle'
                ),
                name=f"{nucleotide} ({organism})",
                showlegend=False,
                hovertext=f"{organism}: {nucleotide} (freq: {freq:.3f})"
            ))
    
    return traces

def create_comparative_voronoi(sequence, colors, genetic_seed, subplot_num):
    """Versión simplificada de Voronoi para comparación"""
    traces = []
    
    sample_size = min(200, len(sequence))
    sequence_sample = sequence[:sample_size]
    
    points = []
    nucleotide_map = {'A': 0, 'T': 1, 'C': 2, 'G': 3}
    
    gc_content = genetic_seed.get('base_ratios', {}).get('gc_content', 0.5)
    entropy = genetic_seed.get('entropy', 2.0)
    
    for i in range(0, len(sequence_sample), max(1, len(sequence_sample) // 30)):
        nucleotide = sequence_sample[i]
        if nucleotide in nucleotide_map:
            base_x = (i / len(sequence_sample)) * 200 - 100
            base_y = (nucleotide_map[nucleotide] * 50) - 75
            
            species_mod_x = (genetic_seed.get('pattern_signature', 0) % 1000) * 0.05 * np.sin(i * entropy * 0.1)
            species_mod_y = (genetic_seed.get('positional_signature', 0) % 1000) * 0.05 * np.cos(i * gc_content * 0.1)
            
            x = base_x + species_mod_x
            y = base_y + species_mod_y
            
            points.append([x, y, nucleotide])
    
    # Crear puntos scattered únicos por especie
    for point in points:
        traces.append(go.Scatter(
            x=[point[0]],
            y=[point[1]],
            mode='markers',
            marker=dict(
                color=colors[point[2]],
                size=6,
                symbol='circle',
                line=dict(color='white', width=0.5),
                opacity=0.8
            ),
            showlegend=False,
            hovertext=f"Nucleótido: {point[2]}"
        ))
    
    return traces

def create_comparative_scatter(sequence, colors, genetic_seed, subplot_num):
    """Visualización scatter comparativa"""
    traces = []
    
    sample_size = min(300, len(sequence))
    sequence_sample = sequence[:sample_size]
    
    # Agrupar por nucleótidos
    nucleotide_positions = {'A': [], 'T': [], 'C': [], 'G': []}
    
    for i, nucleotide in enumerate(sequence_sample):
        if nucleotide in nucleotide_positions:
            # Posición modulada por características genéticas únicas
            x = i + (genetic_seed.get('primary_signature', 0) % 100) * 0.01 * np.sin(i * 0.1)
            y = genetic_seed.get('entropy', 2.0) * 20 + np.random.normal(0, 5)
            nucleotide_positions[nucleotide].append([x, y])
    
    # Crear trazas por nucleótido
    for nucleotide, positions in nucleotide_positions.items():
        if positions:
            x_vals = [pos[0] for pos in positions]
            y_vals = [pos[1] for pos in positions]
            
            traces.append(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='markers',
                marker=dict(
                    color=colors[nucleotide],
                    size=4,
                    opacity=0.7
                ),
                name=nucleotide,
                showlegend=False
            ))
    
    return traces

def crear_voronoi_animado(secuencia, theme='scientific', genetic_seed=None):
    """Genera diagrama de Voronoi con animación de partículas"""
    
    colors = COLOR_THEMES.get(theme, COLOR_THEMES['scientific'])
    
    if not genetic_seed:
        genetic_seed = {'primary_signature': hash(secuencia) % 1000000}
    
    # Generar múltiples frames para animación
    frames = []
    sample_size = min(500, len(secuencia))
    sequence_sample = secuencia[:sample_size]
    
    # Crear 20 frames para animación suave
    for frame_idx in range(20):
        frame_data = []
        time_factor = frame_idx * 0.1
        
        # Generar puntos con movimiento
        points = []
        nucleotide_map = {'A': 0, 'T': 1, 'C': 2, 'G': 3}
        
        gc_content = genetic_seed.get('base_ratios', {}).get('gc_content', 0.5)
        entropy = genetic_seed.get('entropy', 2.0)
        
        for i in range(0, len(sequence_sample), max(1, len(sequence_sample) // 50)):
            nucleotide = sequence_sample[i]
            if nucleotide in nucleotide_map:
                # Posición base con movimiento orbital
                base_x = (i / len(sequence_sample)) * 400 - 200
                base_y = (nucleotide_map[nucleotide] * 100) - 150
                
                # Añadir movimiento circular y ondulatorio
                orbit_radius = 15 + (entropy * 5)
                rotation_speed = gc_content * 2 + 0.5
                
                animated_x = base_x + orbit_radius * np.sin(time_factor * rotation_speed + i * 0.1)
                animated_y = base_y + orbit_radius * np.cos(time_factor * rotation_speed + i * 0.1)
                
                # Añadir ondulación vertical
                wave_amplitude = 10
                animated_y += wave_amplitude * np.sin(time_factor * 3 + i * 0.2)
                
                points.append([animated_x, animated_y, nucleotide])
        
        # Crear trazas animadas para este frame
        for point in points:
            nucleotide_freq = sequence_sample.count(point[2]) / len(sequence_sample)
            size = max(4, min(12, 8 + nucleotide_freq * 20))
            
            # Pulsación de tamaño
            pulse_factor = 1 + 0.3 * np.sin(time_factor * 4 + hash(point[2]) % 100)
            animated_size = size * pulse_factor
            
            frame_data.append(go.Scatter(
                x=[point[0]],
                y=[point[1]],
                mode='markers',
                marker=dict(
                    color=colors[point[2]],
                    size=animated_size,
                    symbol='circle',
                    line=dict(color='white', width=1),
                    opacity=0.8 + 0.2 * np.sin(time_factor * 2)
                ),
                showlegend=False,
                hovertext=f"Nucleótido: {point[2]} (frame: {frame_idx})"
            ))
        
        frames.append(go.Frame(data=frame_data, name=str(frame_idx)))
    
    # Crear figura base
    fig = go.Figure(data=frames[0].data, frames=frames)
    
    # Configurar animación
    fig.update_layout(
        title=f"Voronoi Animado - Entropía: {entropy:.2f}",
        showlegend=False,
        plot_bgcolor='#000011',
        paper_bgcolor='#000011',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=600,
        margin=dict(l=0, r=0, t=30, b=0),
        updatemenus=[dict(
            type="buttons",
            buttons=[dict(label="Play",
                         method="animate",
                         args=[None, {"frame": {"duration": 100, "redraw": True},
                                    "fromcurrent": True, "transition": {"duration": 50}}]),
                    dict(label="Pause",
                         method="animate",
                         args=[[None], {"frame": {"duration": 0, "redraw": False},
                                      "mode": "immediate",
                                      "transition": {"duration": 0}}])]
        )]
    )
    
    return fig

def crear_lsystem_animado(secuencia, theme='scientific', genetic_seed=None):
    """Crea fractal L-System con crecimiento animado"""
    
    colors = COLOR_THEMES.get(theme, COLOR_THEMES['scientific'])
    
    if not genetic_seed:
        genetic_seed = {'primary_signature': hash(secuencia) % 1000000}
    
    # Generar parámetros L-System
    base_ratios = genetic_seed.get('base_ratios', {})
    gc_content = base_ratios.get('gc_content', 0.5)
    entropy = genetic_seed.get('entropy', 2.0)
    
    # Configurar L-System
    if gc_content > 0.6:
        axioma = "F+F+F+F"
        reglas = {'F': 'F+F--F+F'}
        angulo = 60
        color_primary = colors['G']
    elif gc_content < 0.4:
        axioma = "F-F-F-F"
        reglas = {'F': 'F-F++F-F'}
        angulo = 90
        color_primary = colors['A']
    else:
        axioma = "F+F-F"
        reglas = {'F': 'F+F-F-F+F'}
        angulo = 72
        color_primary = colors['C']
    
    iteraciones = min(5, max(3, int(entropy * 1.5)))
    
    # Generar secuencia L-System completa
    secuencia_lsystem = axioma
    for _ in range(iteraciones):
        nueva_secuencia = ""
        for simbolo in secuencia_lsystem:
            if simbolo in reglas:
                nueva_secuencia += reglas[simbolo]
            else:
                nueva_secuencia += simbolo
        secuencia_lsystem = nueva_secuencia
    
    # Crear frames para crecimiento progresivo
    frames = []
    total_symbols = len(secuencia_lsystem)
    
    for frame_idx in range(20):
        # Mostrar progresivamente más símbolos
        symbols_to_show = int((frame_idx + 1) / 20 * total_symbols)
        partial_sequence = secuencia_lsystem[:symbols_to_show]
        
        # Interpretar L-System
        x, y = 0, 0
        angulo_actual = 90
        stack = []
        puntos_x = [0]
        puntos_y = [0]
        
        longitud = 300 / (len(partial_sequence) ** 0.5 + 1)
        
        for simbolo in partial_sequence:
            if simbolo == 'F':
                x += longitud * np.cos(np.radians(angulo_actual))
                y += longitud * np.sin(np.radians(angulo_actual))
                puntos_x.append(x)
                puntos_y.append(y)
            elif simbolo == '+':
                angulo_actual += angulo
            elif simbolo == '-':
                angulo_actual -= angulo
            elif simbolo == '[':
                stack.append((x, y, angulo_actual))
            elif simbolo == ']':
                if stack:
                    x, y, angulo_actual = stack.pop()
                    puntos_x.append(None)
                    puntos_y.append(None)
                    puntos_x.append(x)
                    puntos_y.append(y)
        
        # Crear trazas con efecto de brillo
        opacity = 0.7 + 0.3 * np.sin(frame_idx * 0.3)
        line_width = 2 + np.sin(frame_idx * 0.2)
        
        frame_data = [go.Scatter(
            x=puntos_x,
            y=puntos_y,
            mode='lines',
            line=dict(
                color=color_primary,
                width=line_width
            ),
            opacity=opacity,
            showlegend=False,
            hoverinfo='skip'
        )]
        
        frames.append(go.Frame(data=frame_data, name=str(frame_idx)))
    
    fig = go.Figure(data=frames[0].data, frames=frames)
    
    fig.update_layout(
        title=f"L-System Animado - GC: {gc_content:.2f}",
        showlegend=False,
        plot_bgcolor='#000011',
        paper_bgcolor='#000011',
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        height=600,
        margin=dict(l=0, r=0, t=30, b=0),
        updatemenus=[dict(
            type="buttons",
            buttons=[dict(label="Grow",
                         method="animate",
                         args=[None, {"frame": {"duration": 200, "redraw": True},
                                    "fromcurrent": True}]),
                    dict(label="Reset",
                         method="animate",
                         args=[[0], {"frame": {"duration": 0, "redraw": True}}])]
        )]
    )
    
    return fig

def crear_automata_animado(secuencia, theme='scientific', genetic_seed=None):
    """Genera autómata celular con evolución temporal animada"""
    
    colors = COLOR_THEMES.get(theme, COLOR_THEMES['scientific'])
    
    if not genetic_seed:
        genetic_seed = {'primary_signature': hash(secuencia) % 1000000}
    
    width = 100
    height = 60
    
    rule_number = (genetic_seed.get('primary_signature', 0) % 256)
    rule = [(rule_number >> i) & 1 for i in range(8)]
    
    # Estado inicial
    initial_state = [0] * width
    sample_size = min(width, len(secuencia))
    nucleotide_map = {'A': 0, 'T': 1, 'C': 0, 'G': 1}
    
    for i in range(sample_size):
        if secuencia[i] in nucleotide_map:
            initial_state[i] = nucleotide_map[secuencia[i]]
    
    # Generar evolución completa
    all_generations = [initial_state[:]]
    current = initial_state[:]
    
    for generation in range(height - 1):
        next_state = [0] * width
        for i in range(width):
            left = current[(i - 1) % width]
            center = current[i]
            right = current[(i + 1) % width]
            
            pattern = (left << 2) | (center << 1) | right
            next_state[i] = rule[pattern]
        
        current = next_state[:]
        all_generations.append(current[:])
    
    # Crear frames para mostrar evolución progresiva
    frames = []
    
    for frame_idx in range(height):
        # Mostrar hasta la generación actual
        z_data = all_generations[:frame_idx + 1]
        
        # Rellenar con zeros si necesario
        while len(z_data) < height:
            z_data.append([0] * width)
        
        gc_content = genetic_seed.get('base_ratios', {}).get('gc_content', 0.5)
        if gc_content > 0.6:
            colorscale = [[0, '#000011'], [1, colors['G']]]
        elif gc_content < 0.4:
            colorscale = [[0, '#000011'], [1, colors['A']]]
        else:
            colorscale = [[0, '#000011'], [0.5, colors['C']], [1, colors['T']]]
        
        frame_data = [go.Heatmap(
            z=z_data,
            colorscale=colorscale,
            showscale=False,
            hoverinfo='skip'
        )]
        
        frames.append(go.Frame(data=frame_data, name=str(frame_idx)))
    
    fig = go.Figure(data=frames[0].data, frames=frames)
    
    fig.update_layout(
        title=f"Autómata Celular Animado - Regla: {rule_number}",
        showlegend=False,
        plot_bgcolor='#000011',
        paper_bgcolor='#000011',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=600,
        margin=dict(l=0, r=0, t=30, b=0),
        updatemenus=[dict(
            type="buttons",
            buttons=[dict(label="Evolve",
                         method="animate",
                         args=[None, {"frame": {"duration": 150, "redraw": True},
                                    "fromcurrent": True}]),
                    dict(label="Reset",
                         method="animate",
                         args=[[0], {"frame": {"duration": 0, "redraw": True}}])]
        )]
    )
    
    return fig

def crear_mapa_ruido_animado(secuencia, theme='scientific', genetic_seed=None):
    """Genera mapa de ruido con ondas dinámicas"""
    
    colors = COLOR_THEMES.get(theme, COLOR_THEMES['scientific'])
    
    if not genetic_seed:
        genetic_seed = {'primary_signature': hash(secuencia) % 1000000}
    
    seed = genetic_seed.get('primary_signature', 0) % 1000000
    np.random.seed(seed)
    
    size = 100
    scale = genetic_seed.get('entropy', 2.0) * 10
    
    # Crear frames con ondas temporales
    frames = []
    
    for frame_idx in range(20):
        time_offset = frame_idx * 0.2
        
        noise_map = np.zeros((size, size))
        for x in range(size):
            for y in range(size):
                # Ruido base con componente temporal
                noise_value = (
                    np.sin((x + time_offset * 10) / scale) * np.cos((y + time_offset * 5) / scale) +
                    0.5 * np.sin((x + time_offset * 15) / (scale * 0.5)) * np.cos((y + time_offset * 8) / (scale * 0.5)) +
                    0.25 * np.sin((x + time_offset * 20) / (scale * 0.25)) * np.cos((y + time_offset * 12) / (scale * 0.25))
                )
                noise_map[x, y] = noise_value
        
        # Normalizar
        noise_map = (noise_map - noise_map.min()) / (noise_map.max() - noise_map.min())
        
        gc_content = genetic_seed.get('base_ratios', {}).get('gc_content', 0.5)
        
        if gc_content > 0.6:
            colorscale = 'Greens'
        elif gc_content < 0.4:
            colorscale = 'Reds'
        else:
            colorscale = 'Blues'
        
        frame_data = [go.Heatmap(
            z=noise_map,
            colorscale=colorscale,
            showscale=False,
            hoverinfo='skip'
        )]
        
        frames.append(go.Frame(data=frame_data, name=str(frame_idx)))
    
    fig = go.Figure(data=frames[0].data, frames=frames)
    
    fig.update_layout(
        title=f"Mapa de Ruido Dinámico - Escala: {scale:.1f}",
        showlegend=False,
        plot_bgcolor='#000011',
        paper_bgcolor='#000011',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=600,
        margin=dict(l=0, r=0, t=30, b=0),
        updatemenus=[dict(
            type="buttons",
            buttons=[dict(label="Flow",
                         method="animate",
                         args=[None, {"frame": {"duration": 100, "redraw": True},
                                    "fromcurrent": True, "transition": {"duration": 50}}]),
                    dict(label="Pause",
                         method="animate",
                         args=[[None], {"frame": {"duration": 0, "redraw": False}}])]
        )]
    )
    
    return fig

def crear_arte_fluido_animado(secuencia, theme='scientific', genetic_seed=None):
    """Crea arte fluido con partículas en movimiento"""
    
    colors = COLOR_THEMES.get(theme, COLOR_THEMES['scientific'])
    
    if not genetic_seed:
        genetic_seed = {'primary_signature': hash(secuencia) % 1000000}
    
    sample_size = min(400, len(secuencia))
    sequence_sample = secuencia[:sample_size]
    
    frames = []
    
    for frame_idx in range(25):
        frame_data = []
        time_factor = frame_idx * 0.15
        
        # Crear partículas flotantes para cada nucleótido
        nucleotide_positions = {'A': [], 'T': [], 'C': [], 'G': []}
        
        for i, nucleotide in enumerate(sequence_sample):
            if nucleotide in nucleotide_positions:
                # Posición base con flujo dinámico
                base_x = (i / len(sequence_sample)) * 600 - 300
                base_y = np.random.normal(0, 50)
                
                # Añadir movimiento fluido
                flow_x = 100 * np.sin(time_factor + i * 0.01)
                flow_y = 50 * np.cos(time_factor * 1.5 + i * 0.02)
                
                # Turbulencia
                turb_x = 20 * np.sin(time_factor * 3 + i * 0.1)
                turb_y = 20 * np.cos(time_factor * 2.5 + i * 0.1)
                
                final_x = base_x + flow_x + turb_x
                final_y = base_y + flow_y + turb_y
                
                nucleotide_positions[nucleotide].append([final_x, final_y])
        
        # Crear trazas animadas
        for nucleotide, positions in nucleotide_positions.items():
            if positions:
                x_vals = [pos[0] for pos in positions]
                y_vals = [pos[1] for pos in positions]
                
                # Tamaño y opacidad pulsantes
                freq = len(positions) / len(sequence_sample)
                size = max(3, min(10, 6 + freq * 15))
                opacity = 0.6 + 0.4 * np.sin(time_factor * 2 + hash(nucleotide) % 10)
                
                frame_data.append(go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode='markers',
                    marker=dict(
                        color=colors[nucleotide],
                        size=size,
                        opacity=opacity,
                        symbol='circle'
                    ),
                    showlegend=False,
                    hovertext=f"Nucleótido: {nucleotide}"
                ))
                
                # Añadir conexiones fluidas entre partículas cercanas
                if len(x_vals) > 1:
                    frame_data.append(go.Scatter(
                        x=x_vals,
                        y=y_vals,
                        mode='lines',
                        line=dict(
                            color=colors[nucleotide],
                            width=1,
                            dash='dot'
                        ),
                        opacity=opacity * 0.3,
                        showlegend=False,
                        hoverinfo='skip'
                    ))
        
        frames.append(go.Frame(data=frame_data, name=str(frame_idx)))
    
    fig = go.Figure(data=frames[0].data, frames=frames)
    
    fig.update_layout(
        title="Arte Fluido Genético Animado",
        showlegend=False,
        plot_bgcolor='#000011',
        paper_bgcolor='#000011',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=600,
        margin=dict(l=0, r=0, t=30, b=0),
        updatemenus=[dict(
            type="buttons",
            buttons=[dict(label="Flow",
                         method="animate",
                         args=[None, {"frame": {"duration": 120, "redraw": True},
                                    "fromcurrent": True, "transition": {"duration": 60}}]),
                    dict(label="Pause",
                         method="animate",
                         args=[[None], {"frame": {"duration": 0, "redraw": False}}])]
        )]
    )
    
    return fig

def crear_visualizacion_clasica_animada(secuencia, seq_record, theme):
    """Visualización clásica con efectos animados"""
    
    colors = COLOR_THEMES.get(theme, COLOR_THEMES['scientific'])
    
    sample_size = min(300, len(secuencia))
    sequence_sample = secuencia[:sample_size]
    
    frames = []
    
    for frame_idx in range(15):
        frame_data = []
        time_factor = frame_idx * 0.2
        
        # Crear gráfico de barras animado
        nucleotide_counts = {'A': 0, 'T': 0, 'C': 0, 'G': 0}
        
        # Revelar progresivamente la secuencia
        reveal_length = int((frame_idx + 1) / 15 * len(sequence_sample))
        partial_sequence = sequence_sample[:reveal_length]
        
        for nucleotide in partial_sequence:
            if nucleotide in nucleotide_counts:
                nucleotide_counts[nucleotide] += 1
        
        # Añadir efecto de pulso
        pulse_factor = 1 + 0.2 * np.sin(time_factor * 4)
        
        frame_data.append(go.Bar(
            x=list(nucleotide_counts.keys()),
            y=[count * pulse_factor for count in nucleotide_counts.values()],
            marker_color=[colors[nuc] for nuc in nucleotide_counts.keys()],
            opacity=0.8,
            hovertext=[f"{nuc}: {count}" for nuc, count in nucleotide_counts.items()]
        ))
        
        frames.append(go.Frame(data=frame_data, name=str(frame_idx)))
    
    fig = go.Figure(data=frames[0].data, frames=frames)
    
    fig.update_layout(
        title="Análisis Clásico Animado",
        xaxis_title="Nucleótido",
        yaxis_title="Frecuencia",
        height=600,
        template="plotly_dark",
        updatemenus=[dict(
            type="buttons",
            buttons=[dict(label="Analyze",
                         method="animate",
                         args=[None, {"frame": {"duration": 200, "redraw": True}}]),
                    dict(label="Reset",
                         method="animate",
                         args=[[0], {"frame": {"duration": 0, "redraw": True}}])]
        )]
    )
    
    return fig

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
    
    /* Botones de redes sociales */
    .social-share-container {
        display: flex;
        gap: 10px;
        margin: 15px 0;
        justify-content: center;
        flex-wrap: wrap;
    }
    
    .social-btn {
        display: inline-flex;
        align-items: center;
        padding: 8px 16px;
        border-radius: 25px;
        text-decoration: none;
        color: white;
        font-weight: bold;
        transition: all 0.3s ease;
        border: none;
        cursor: pointer;
        font-size: 14px;
        gap: 8px;
    }
    
    .social-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
    }
    
    .social-btn.twitter {
        background: linear-gradient(45deg, #1da1f2, #0d8bd9);
    }
    
    .social-btn.facebook {
        background: linear-gradient(45deg, #4267b2, #365899);
    }
    
    .social-btn.instagram {
        background: linear-gradient(45deg, #e4405f, #833ab4, #fccc63);
    }
    
    .social-btn.linkedin {
        background: linear-gradient(45deg, #0077b5, #005885);
    }
    
    .social-btn.whatsapp {
        background: linear-gradient(45deg, #25d366, #128c7e);
    }
    
    /* Animaciones de carga */
    .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px;
        background: rgba(15, 15, 15, 0.9);
        border-radius: 15px;
        border: 1px solid rgba(0, 255, 136, 0.3);
    }
    
    .dna-loader {
        width: 80px;
        height: 80px;
        position: relative;
        margin-bottom: 20px;
    }
    
    .dna-strand {
        position: absolute;
        width: 4px;
        height: 80px;
        background: linear-gradient(180deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4);
        border-radius: 2px;
        animation: dnaRotate 2s linear infinite;
    }
    
    .dna-strand:nth-child(1) {
        left: 20px;
        animation-delay: 0s;
    }
    
    .dna-strand:nth-child(2) {
        right: 20px;
        animation-delay: 0.5s;
    }
    
    .dna-base {
        position: absolute;
        width: 40px;
        height: 2px;
        background: rgba(0, 255, 136, 0.6);
        left: 20px;
        animation: dnaConnect 2s ease-in-out infinite;
    }
    
    .dna-base:nth-child(3) { top: 10px; animation-delay: 0.1s; }
    .dna-base:nth-child(4) { top: 25px; animation-delay: 0.2s; }
    .dna-base:nth-child(5) { top: 40px; animation-delay: 0.3s; }
    .dna-base:nth-child(6) { top: 55px; animation-delay: 0.4s; }
    .dna-base:nth-child(7) { top: 70px; animation-delay: 0.5s; }
    
    @keyframes dnaRotate {
        0% { transform: rotateY(0deg); }
        100% { transform: rotateY(360deg); }
    }
    
    @keyframes dnaConnect {
        0%, 100% { opacity: 0.3; transform: scaleX(0.5); }
        50% { opacity: 1; transform: scaleX(1); }
    }
    
    .loading-text {
        color: #00ff88;
        font-size: 16px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
        animation: textPulse 2s ease-in-out infinite;
    }
    
    .loading-subtitle {
        color: #aaaaaa;
        font-size: 14px;
        text-align: center;
        animation: textPulse 2s ease-in-out infinite 0.5s;
    }
    
    @keyframes textPulse {
        0%, 100% { opacity: 0.7; }
        50% { opacity: 1; }
    }
    
    /* Animación de progreso */
    .progress-bar {
        width: 200px;
        height: 4px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 2px;
        overflow: hidden;
        margin-top: 15px;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #00ff88, #00ccaa);
        border-radius: 2px;
        animation: progressMove 3s ease-in-out infinite;
    }
    
    @keyframes progressMove {
        0% { width: 0%; }
        50% { width: 70%; }
        100% { width: 100%; }
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

def generar_visualizacion(seq_record, style='voronoi', theme='scientific'):
    """Crea visualización artística animada del ADN usando algoritmos específicos"""
    
    secuencia = str(seq_record.seq).upper()
    
    # Crear semilla genética única
    genetic_seed = crear_semilla_genetica(secuencia, seq_record.id)
    
    # Seleccionar algoritmo de visualización con animación
    if style == 'voronoi':
        fig = crear_voronoi_animado(secuencia, theme, genetic_seed)
    elif style == 'lsystem':
        fig = crear_lsystem_animado(secuencia, theme, genetic_seed)
    elif style == 'cellular':
        fig = crear_automata_animado(secuencia, theme, genetic_seed)
    elif style == 'noise':
        fig = crear_mapa_ruido_animado(secuencia, theme, genetic_seed)
    elif style == 'fluid':
        fig = crear_arte_fluido_animado(secuencia, theme, genetic_seed)
    else:
        fig = crear_visualizacion_clasica_animada(secuencia, seq_record, theme)
    
    # Calcular GC content
    gc_content = gc_fraction(seq_record.seq) * 100
    
    return fig, gc_content

def crear_semilla_genetica(secuencia, sequence_id):
    """Genera parámetros únicos basados en análisis profundo de la secuencia genética"""
    
    if not secuencia or len(secuencia) < 100:
        return None
    
    # Análisis de composición base
    base_counts = {'A': 0, 'T': 0, 'C': 0, 'G': 0}
    for base in secuencia:
        if base in base_counts:
            base_counts[base] += 1
    
    total = sum(base_counts.values())
    if total == 0:
        return None
    
    # 1. Análisis de dinucleótidos y trinucleótidos para patrones únicos
    dinucs = {}
    trinucs = {}
    for i in range(len(secuencia) - 2):
        dinuc = secuencia[i:i+2]
        trinuc = secuencia[i:i+3]
        if len(dinuc) == 2:
            dinucs[dinuc] = dinucs.get(dinuc, 0) + 1
        if len(trinuc) == 3:
            trinucs[trinuc] = trinucs.get(trinuc, 0) + 1
    
    # 2. Análisis de periodicidad y repeticiones
    sequence_length = len(secuencia)
    repetition_pattern = 0
    for window in [3, 6, 9, 12]:  # Detectar repeticiones de diferentes tamaños
        if sequence_length > window * 2:
            pattern = secuencia[:window]
            count = secuencia.count(pattern)
            repetition_pattern += count * window
    
    # 3. Skew y bias direccional
    gc_skew = (base_counts['G'] - base_counts['C']) / (base_counts['G'] + base_counts['C']) if (base_counts['G'] + base_counts['C']) > 0 else 0
    at_skew = (base_counts['A'] - base_counts['T']) / (base_counts['A'] + base_counts['T']) if (base_counts['A'] + base_counts['T']) > 0 else 0
    
    # 4. Análisis posicional - primer, medio y final de la secuencia
    third = len(secuencia) // 3
    start_gc = secuencia[:third].count('G') + secuencia[:third].count('C')
    middle_gc = secuencia[third:2*third].count('G') + secuencia[third:2*third].count('C')
    end_gc = secuencia[2*third:].count('G') + secuencia[2*third:].count('C')
    
    positional_variance = abs(start_gc - middle_gc) + abs(middle_gc - end_gc) + abs(start_gc - end_gc)
    
    # 5. Complejidad de secuencia usando entropía de Shannon
    from collections import Counter
    def shannon_entropy(sequence_part):
        counter = Counter(sequence_part)
        total = len(sequence_part)
        if total == 0:
            return 0
        entropy = 0
        for count in counter.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p) if p > 0 else 0
        return entropy
    
    entropy = shannon_entropy(secuencia[:1000])  # Primeros 1000 bases
    
    # 6. Hash único de la secuencia completa
    sequence_hash = hash(secuencia) % 2147483647  # Usar la secuencia completa, no solo el ID
    
    # 7. Análisis de codones (si es múltiplo de 3)
    codon_diversity = 0
    if len(secuencia) >= 99:  # Al menos 33 codones
        codons = set()
        for i in range(0, len(secuencia) - 2, 3):
            codon = secuencia[i:i+3]
            if len(codon) == 3:
                codons.add(codon)
        codon_diversity = len(codons)
    
    # 8. Dinucleótido más frecuente y su frecuencia relativa
    most_common_dinuc = max(dinucs.items(), key=lambda x: x[1]) if dinucs else ('AT', 1)
    dinuc_dominance = most_common_dinuc[1] / len(dinucs) if dinucs else 0
    
    # Crear firmas únicas combinando todos los análisis
    primary_signature = int(abs(sequence_hash))
    gc_signature = int((base_counts['G'] + base_counts['C']) * 10000 / total)
    skew_signature = int((gc_skew + 1) * 50000) + int((at_skew + 1) * 50000)
    complexity_signature = int(entropy * 100000)
    pattern_signature = repetition_pattern % 100000
    positional_signature = positional_variance % 50000
    codon_signature = codon_diversity * 1000
    dominance_signature = int(dinuc_dominance * 100000)
    
    return {
        'primary_signature': primary_signature,
        'gc_signature': gc_signature,
        'skew_signature': skew_signature,
        'complexity_signature': complexity_signature,
        'pattern_signature': pattern_signature,
        'positional_signature': positional_signature,
        'codon_signature': codon_signature,
        'dominance_signature': dominance_signature,
        'sequence_length': len(secuencia),
        'base_ratios': {
            'gc_content': (base_counts['G'] + base_counts['C']) / total,
            'at_content': (base_counts['A'] + base_counts['T']) / total,
            'gc_skew': gc_skew,
            'at_skew': at_skew,
            'a_ratio': base_counts['A'] / total,
            't_ratio': base_counts['T'] / total,
            'c_ratio': base_counts['C'] / total,
            'g_ratio': base_counts['G'] / total
        },
        'dinuc_profile': most_common_dinuc[0],
        'codon_diversity': codon_diversity,
        'repetition_score': repetition_pattern,
        'positional_variance': positional_variance,
        'entropy': entropy
    }

def crear_voronoi_genetico(secuencia, theme='scientific', genetic_seed=None):
    """Genera diagrama de Voronoi único basado en características genéticas"""
    
    fig = go.Figure()
    colors = COLOR_THEMES.get(theme, COLOR_THEMES['scientific'])
    
    if not genetic_seed:
        genetic_seed = {'primary_signature': hash(secuencia) % 1000000}
    
    # Generar puntos únicos basados en secuencia genética
    sample_size = min(500, len(secuencia))
    sequence_sample = secuencia[:sample_size]
    
    # Crear puntos semilla para Voronoi basados en nucleótidos
    points = []
    nucleotide_map = {'A': 0, 'T': 1, 'C': 2, 'G': 3}
    
    # Distribución basada en firmas genéticas
    gc_content = genetic_seed.get('base_ratios', {}).get('gc_content', 0.5)
    entropy = genetic_seed.get('entropy', 2.0)
    pattern_sig = genetic_seed.get('pattern_signature', 0)
    
    # Generar puntos con distribución única por especie
    for i in range(0, len(sequence_sample), max(1, len(sequence_sample) // 50)):
        nucleotide = sequence_sample[i]
        if nucleotide in nucleotide_map:
            # Posición base modulada por características genéticas
            base_x = (i / len(sequence_sample)) * 400 - 200
            base_y = (nucleotide_map[nucleotide] * 100) - 150
            
            # Variación única por especie
            species_mod_x = (pattern_sig % 1000) * 0.1 * np.sin(i * entropy * 0.1)
            species_mod_y = (genetic_seed.get('positional_signature', 0) % 1000) * 0.1 * np.cos(i * gc_content * 0.1)
            
            x = base_x + species_mod_x
            y = base_y + species_mod_y
            
            points.append([x, y, nucleotide])
    
    if len(points) < 4:
        # Fallback si muy pocos puntos
        return crear_visualizacion_clasica(sequence_sample, None, theme)
    
    # Crear diagrama de Voronoi
    point_coords = np.array([[p[0], p[1]] for p in points])
    vor = Voronoi(point_coords)
    
    # Dibujar regiones de Voronoi
    for pointidx, simplex in zip(vor.ridge_points, vor.ridge_vertices):
        if np.all(np.array(simplex) >= 0):
            # Obtener vértices de la arista
            vertices = vor.vertices[simplex]
            
            # Color basado en nucleótido dominante
            nucleotide1 = points[pointidx[0]][2]
            nucleotide2 = points[pointidx[1]][2]
            
            # Determinar color de la región
            if nucleotide1 == nucleotide2:
                color = colors[nucleotide1]
                opacity = 0.6
            else:
                # Mezcla de colores para transiciones
                color = colors[nucleotide1]
                opacity = 0.3
            
            fig.add_trace(go.Scatter(
                x=vertices[:, 0].tolist() + [vertices[0, 0]],
                y=vertices[:, 1].tolist() + [vertices[0, 1]],
                fill='toself',
                fillcolor=color,
                opacity=opacity,
                line=dict(color='rgba(255,255,255,0.2)', width=1),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Agregar puntos semilla
    for point in points:
        fig.add_trace(go.Scatter(
            x=[point[0]],
            y=[point[1]],
            mode='markers',
            marker=dict(
                color=colors[point[2]],
                size=8,
                symbol='circle',
                line=dict(color='white', width=1)
            ),
            name=point[2],
            showlegend=False,
            hovertext=f"Nucleótido: {point[2]}"
        ))
    
    fig.update_layout(
        title=f"Diagrama Voronoi - Entropía: {entropy:.2f}",
        showlegend=False,
        plot_bgcolor='#000011',
        paper_bgcolor='#000011',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=600,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig

def crear_lsystem_fractal(secuencia, theme='scientific', genetic_seed=None):
    """Crea fractal L-System único basado en secuencia genética"""
    
    fig = go.Figure()
    colors = COLOR_THEMES.get(theme, COLOR_THEMES['scientific'])
    
    if not genetic_seed:
        genetic_seed = {'primary_signature': hash(secuencia) % 1000000}
    
    # Generar parámetros L-System únicos por especie
    base_ratios = genetic_seed.get('base_ratios', {})
    gc_content = base_ratios.get('gc_content', 0.5)
    entropy = genetic_seed.get('entropy', 2.0)
    
    # Axioma basado en nucleótido dominante
    a_ratio = base_ratios.get('a_ratio', 0.25)
    dominant_nucleotide = max(['A', 'T', 'C', 'G'], 
                             key=lambda n: base_ratios.get(f'{n.lower()}_ratio', 0.25))
    
    if dominant_nucleotide == 'A':
        axioma = "F"
    elif dominant_nucleotide == 'T':
        axioma = "F+F"
    elif dominant_nucleotide == 'C':
        axioma = "F-F"
    else:
        axioma = "F+F-F"
    
    # Reglas únicas basadas en características genéticas
    if gc_content > 0.6:  # Alto GC
        reglas = {'F': 'F+F--F+F'}
        angulo = 60
    elif gc_content < 0.4:  # Alto AT
        reglas = {'F': 'F-F++F-F'}
        angulo = 90
    else:  # Balanceado
        reglas = {'F': 'F+F-F-F+F'}
        angulo = int(72 + (entropy * 10))
    
    # Iteraciones basadas en complejidad
    iteraciones = min(6, max(3, int(entropy * 2)))
    
    # Generar L-System
    secuencia_lsystem = axioma
    for _ in range(iteraciones):
        nueva_secuencia = ""
        for simbolo in secuencia_lsystem:
            if simbolo in reglas:
                nueva_secuencia += reglas[simbolo]
            else:
                nueva_secuencia += simbolo
        secuencia_lsystem = nueva_secuencia
    
    # Interpretar L-System en coordenadas
    x, y = 0, 0
    angulo_actual = 90
    stack = []
    puntos_x = [0]
    puntos_y = [0]
    
    longitud = 300 / (len(secuencia_lsystem) ** 0.5)  # Escalar según complejidad
    
    for simbolo in secuencia_lsystem:
        if simbolo == 'F':
            x += longitud * np.cos(np.radians(angulo_actual))
            y += longitud * np.sin(np.radians(angulo_actual))
            puntos_x.append(x)
            puntos_y.append(y)
        elif simbolo == '+':
            angulo_actual += angulo
        elif simbolo == '-':
            angulo_actual -= angulo
        elif simbolo == '[':
            stack.append((x, y, angulo_actual))
        elif simbolo == ']':
            if stack:
                x, y, angulo_actual = stack.pop()
                puntos_x.append(None)  # Separador para nuevas líneas
                puntos_y.append(None)
                puntos_x.append(x)
                puntos_y.append(y)
    
    # Dibujar fractal
    fig.add_trace(go.Scatter(
        x=puntos_x,
        y=puntos_y,
        mode='lines',
        line=dict(
            color=colors['G'] if gc_content > 0.5 else colors['A'],
            width=2
        ),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        title=f"L-System Fractal - GC: {gc_content:.2f}",
        showlegend=False,
        plot_bgcolor='#000011',
        paper_bgcolor='#000011',
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        height=600,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig

def crear_automata_celular(secuencia, theme='scientific', genetic_seed=None):
    """Genera autómata celular basado en secuencia genética"""
    
    fig = go.Figure()
    colors = COLOR_THEMES.get(theme, COLOR_THEMES['scientific'])
    
    if not genetic_seed:
        genetic_seed = {'primary_signature': hash(secuencia) % 1000000}
    
    # Configuración del autómata basada en características genéticas
    width = 100
    height = 50
    
    # Regla única basada en firmas genéticas
    rule_number = (genetic_seed.get('primary_signature', 0) % 256)
    rule = [(rule_number >> i) & 1 for i in range(8)]
    
    # Estado inicial basado en secuencia
    initial_state = [0] * width
    sample_size = min(width, len(secuencia))
    nucleotide_map = {'A': 0, 'T': 1, 'C': 0, 'G': 1}
    
    for i in range(sample_size):
        if secuencia[i] in nucleotide_map:
            initial_state[i] = nucleotide_map[secuencia[i]]
    
    # Generar evolución del autómata
    grid = [initial_state[:]]
    current = initial_state[:]
    
    for generation in range(height - 1):
        next_state = [0] * width
        for i in range(width):
            left = current[(i - 1) % width]
            center = current[i]
            right = current[(i + 1) % width]
            
            # Aplicar regla
            pattern = (left << 2) | (center << 1) | right
            next_state[i] = rule[pattern]
        
        current = next_state[:]
        grid.append(current[:])
    
    # Convertir a imagen
    z_data = []
    for row in grid:
        z_data.append(row)
    
    # Color basado en características genéticas
    gc_content = genetic_seed.get('base_ratios', {}).get('gc_content', 0.5)
    if gc_content > 0.6:
        colorscale = [[0, '#000011'], [1, colors['G']]]
    elif gc_content < 0.4:
        colorscale = [[0, '#000011'], [1, colors['A']]]
    else:
        colorscale = [[0, '#000011'], [0.5, colors['C']], [1, colors['T']]]
    
    fig.add_trace(go.Heatmap(
        z=z_data,
        colorscale=colorscale,
        showscale=False,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        title=f"Autómata Celular - Regla: {rule_number}",
        showlegend=False,
        plot_bgcolor='#000011',
        paper_bgcolor='#000011',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=600,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig

def crear_mapa_ruido(secuencia, theme='scientific', genetic_seed=None):
    """Genera mapa de ruido Perlin basado en secuencia genética"""
    
    fig = go.Figure()
    colors = COLOR_THEMES.get(theme, COLOR_THEMES['scientific'])
    
    if not genetic_seed:
        genetic_seed = {'primary_signature': hash(secuencia) % 1000000}
    
    # Parámetros de ruido únicos por especie
    seed = genetic_seed.get('primary_signature', 0) % 1000000
    np.random.seed(seed)
    
    size = 100
    scale = genetic_seed.get('entropy', 2.0) * 10
    octaves = min(6, max(2, genetic_seed.get('codon_diversity', 20) // 10))
    
    # Generar ruido simple (simulando Perlin)
    def simple_noise(x, y, scale):
        return np.sin(x / scale) * np.cos(y / scale) + \
               0.5 * np.sin(x / (scale * 0.5)) * np.cos(y / (scale * 0.5)) + \
               0.25 * np.sin(x / (scale * 0.25)) * np.cos(y / (scale * 0.25))
    
    # Generar mapa de altura
    noise_map = np.zeros((size, size))
    for x in range(size):
        for y in range(size):
            noise_map[x, y] = simple_noise(x, y, scale)
    
    # Normalizar
    noise_map = (noise_map - noise_map.min()) / (noise_map.max() - noise_map.min())
    
    # Aplicar características genéticas al colormap
    gc_content = genetic_seed.get('base_ratios', {}).get('gc_content', 0.5)
    
    if gc_content > 0.6:
        colorscale = 'Greens'
    elif gc_content < 0.4:
        colorscale = 'Reds'
    else:
        colorscale = 'Blues'
    
    fig.add_trace(go.Heatmap(
        z=noise_map,
        colorscale=colorscale,
        showscale=False,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        title=f"Mapa de Ruido - Escala: {scale:.1f}",
        showlegend=False,
        plot_bgcolor='#000011',
        paper_bgcolor='#000011',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=600,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig

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

def create_custom_loading_animation(message="Generando arte genético", subtitle="Analizando secuencia de ADN"):
    """Crea una animación de carga personalizada con tema ADN"""
    return f"""
    <div class="loading-container">
        <div class="dna-loader">
            <div class="dna-strand"></div>
            <div class="dna-strand"></div>
            <div class="dna-base"></div>
            <div class="dna-base"></div>
            <div class="dna-base"></div>
            <div class="dna-base"></div>
            <div class="dna-base"></div>
        </div>
        <div class="loading-text">{message}</div>
        <div class="loading-subtitle">{subtitle}</div>
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
    </div>
    """

def create_social_share_buttons(organism_name, description="Arte genético único generado desde secuencias de ADN reales"):
    """Crea botones de compartir en redes sociales"""
    base_url = "https://geneticframes.replit.app"  # URL base de la aplicación
    title = f"🧬 Arte Genético de {organism_name}"
    
    # URLs de compartir
    twitter_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(f'{title} - {description}')}&url={urllib.parse.quote(base_url)}&hashtags=GeneticArt,NFT,DNA,Bioinformatics"
    
    facebook_url = f"https://www.facebook.com/sharer/sharer.php?u={urllib.parse.quote(base_url)}&quote={urllib.parse.quote(f'{title} - {description}')}"
    
    linkedin_url = f"https://www.linkedin.com/sharing/share-offsite/?url={urllib.parse.quote(base_url)}&title={urllib.parse.quote(title)}&summary={urllib.parse.quote(description)}"
    
    whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(f'{title} - {description} {base_url}')}"
    
    instagram_text = f"📋 Texto para Instagram: {title} - {description} #GeneticArt #NFT #DNA #Bioinformatics"
    
    return f"""
    <div class="social-share-container">
        <a href="{twitter_url}" target="_blank" class="social-btn twitter">
            🐦 Twitter
        </a>
        <a href="{facebook_url}" target="_blank" class="social-btn facebook">
            📘 Facebook
        </a>
        <a href="{linkedin_url}" target="_blank" class="social-btn linkedin">
            💼 LinkedIn
        </a>
        <a href="{whatsapp_url}" target="_blank" class="social-btn whatsapp">
            💬 WhatsApp
        </a>
        <button onclick="copyInstagramText()" class="social-btn instagram">
            📸 Instagram
        </button>
    </div>
    
    <script>
    function copyInstagramText() {{
        navigator.clipboard.writeText(`{instagram_text}`).then(function() {{
            alert('✅ Texto copiado al portapapeles. Pégalo en tu post de Instagram.');
        }}, function(err) {{
            console.error('Error al copiar: ', err);
        }});
    }}
    </script>
    """

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
            ['voronoi', 'lsystem', 'cellular', 'noise', 'fluid', 'classic'],
            index=0,
            help="Algoritmo de visualización genética"
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
        st.markdown("""
        <div style="background: rgba(26, 26, 46, 0.8); padding: 20px; border-radius: 15px; margin-bottom: 20px;">
            <h3 style="color: #00ff88; margin-bottom: 15px;">🎯 Generador de Arte Genético</h3>
            <p style="color: #cccccc; margin-bottom: 0;">
                Transforma secuencias de ADN reales en arte único mediante algoritmos bioinformáticos avanzados
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Método de entrada de secuencia
        input_method = st.radio(
            "Método de entrada de secuencia:",
            ["🔍 Buscar por organismo", "📝 Pegar secuencia FASTA", "🔬 Análisis comparativo"],
            horizontal=True
        )
        
        organism_input = None
        fasta_sequence = None
        selected_species = None
        sample_method = "Completa"
        start_pos = 1
        length = 1000
        species1 = None
        species2 = None
        
        if input_method == "🔍 Buscar por organismo":
            col1, col2 = st.columns([3, 1])
            
            with col1:
                selected_organism = st.session_state.get('selected_organism', '')
                organism_input = st.text_input(
                    "Nombre científico del organismo:",
                    value=selected_organism,
                    placeholder="ej: Tursiops truncatus (delfín nariz de botella)",
                    help="Introduce el nombre científico completo del organismo"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                
        elif input_method == "📝 Pegar secuencia FASTA":
            st.markdown("### Importar Secuencia FASTA")
            fasta_sequence = st.text_area(
                "Pega tu secuencia FASTA aquí:",
                height=150,
                placeholder=">Mi_Secuencia_ADN | Organismo: Ejemplo\nATGCAGCTTGCAATCGACTGCAGCTTGCAATCGACT...",
                help="Formato FASTA estándar con encabezado (>nombre) seguido de la secuencia"
            )
            
            # Opciones de procesamiento para secuencias largas
            if fasta_sequence and len(fasta_sequence) > 100:
                st.markdown("### Opciones de Procesamiento de Secuencias Largas")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    sample_method = st.selectbox(
                        "Método de muestreo:",
                        ["Completa", "Primeros N bases", "Región específica", "Muestreo representativo"],
                        help="Completa: toda la secuencia (máx. 10k bases), Muestreo: selección representativa"
                    )
                
                with col2:
                    if sample_method in ["Primeros N bases", "Región específica"]:
                        start_pos = st.number_input("Posición inicial:", min_value=1, value=1)
                        
                with col3:
                    if sample_method in ["Primeros N bases", "Región específica", "Muestreo representativo"]:
                        length = st.number_input("Longitud (bases):", min_value=100, value=1000, max_value=10000)
                

        
        # Análisis comparativo
        if input_method == "🔬 Análisis comparativo":
            st.markdown("### 🔬 Análisis Comparativo de Especies")
            st.info("Compara patrones genéticos únicos entre diferentes especies para identificar firmas evolutivas")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Primera Especie:**")
                species1 = st.selectbox(
                    "Selecciona primera especie:",
                    ["Panthera tigris", "Canis lupus", "Homo sapiens", "Tursiops truncatus", "Orcinus orca"],
                    key="species1"
                )
                
            with col2:
                st.markdown("**Segunda Especie:**")
                species2 = st.selectbox(
                    "Selecciona segunda especie:",
                    ["Canis lupus", "Panthera tigris", "Homo sapiens", "Tursiops truncatus", "Orcinus orca"],
                    key="species2"
                )
            
            if st.button("🔬 Comparar Especies", type="primary", use_container_width=True):
                if species1 == species2:
                    st.warning("Selecciona dos especies diferentes para la comparación")
                else:
                    # Realizar análisis comparativo
                    loading_placeholder = st.empty()
                    loading_placeholder.markdown(
                        create_custom_loading_animation(
                            f"Análisis comparativo: {species1} vs {species2}",
                            "Obteniendo y comparando secuencias genéticas"
                        ),
                        unsafe_allow_html=True
                    )
                    
                    try:
                        # Obtener secuencias de ambas especies
                        seq_record1 = obtener_secuencia(species1)
                        seq_record2 = obtener_secuencia(species2)
                        
                        seq1 = str(seq_record1.seq)
                        seq2 = str(seq_record2.seq)
                        
                        loading_placeholder.empty()
                        
                        # Crear visualización comparativa
                        fig, comparison_data = create_comparative_visualization(
                            seq1, seq2, species1, species2, art_style, color_theme
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Mostrar análisis comparativo detallado
                        st.markdown("### 🔬 Análisis Comparativo Detallado")
                        
                        differences = comparison_data['differences']
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            gc_diff = differences['gc_content']
                            st.metric(
                                "Diferencia GC", 
                                f"{gc_diff['difference']:.3f}",
                                delta=f"{gc_diff['significance']} significancia"
                            )
                        
                        with col2:
                            complexity_diff = differences['complexity']
                            st.metric(
                                "Diferencia Complejidad",
                                f"{complexity_diff['difference']:.3f}",
                                delta="Shannon entropy"
                            )
                        
                        with col3:
                            coding_diff = differences['coding_potential']
                            orfs_diff = coding_diff['orfs_count'][0] - coding_diff['orfs_count'][1]
                            st.metric(
                                "Diferencia ORFs",
                                f"{abs(orfs_diff)}",
                                delta=f"{'Mayor' if orfs_diff > 0 else 'Menor'} en {species1}"
                            )
                        
                        # Insights evolutivos
                        insights = comparison_data['evolutionary_insights']
                        if insights:
                            st.markdown("### 🌳 Insights Evolutivos")
                            for insight in insights:
                                st.info(insight)
                        
                        # Guardar datos comparativos
                        st.session_state.last_comparison_data = {
                            'species': [species1, species2],
                            'sequences': [seq1, seq2],
                            'comparison': comparison_data
                        }
                        
                    except Exception as e:
                        loading_placeholder.empty()
                        st.error(f"Error en análisis comparativo: {str(e)}")
            
            st.stop()
        
        # Botón de generación optimizado
        generate_button_text = "🚀 Generar Arte Genético"
        if input_method == "📝 Pegar secuencia FASTA":
            generate_button_text = "🧬 Generar Arte desde FASTA"
            
        if st.button(generate_button_text, type="primary", use_container_width=True):
            seq_record = None
            processed_sequence = None
            organism_name = ""
            
            # Procesar según el método de entrada
            if input_method == "🔍 Buscar por organismo" and organism_input:
                # Método original de búsqueda NCBI
                log_search(organism_input, user_session=st.session_state.session_id)
                
                loading_placeholder = st.empty()
                loading_placeholder.markdown(
                    create_custom_loading_animation(
                        "Conectando con NCBI GenBank",
                        "Buscando secuencias genéticas auténticas"
                    ),
                    unsafe_allow_html=True
                )
                
                try:
                    seq_record = obtener_secuencia(organism_input)
                    organism_name = organism_input
                    loading_placeholder.empty()
                    
                except Exception as e:
                    loading_placeholder.empty()
                    st.error(f"Error al obtener secuencia: {str(e)}")
                    log_search(organism_input, successful=False, error_message=str(e), user_session=st.session_state.session_id)
                    st.stop()
                    
            elif input_method == "📝 Pegar secuencia FASTA" and fasta_sequence:
                # Procesar secuencia FASTA
                try:
                    fasta_data = parse_fasta_sequence(fasta_sequence)
                    raw_sequence = fasta_data['sequence']
                    organism_name = fasta_data['organism_name']
                    
                    if len(raw_sequence) < 50:
                        st.error("La secuencia debe tener al menos 50 nucleótidos válidos (A, T, C, G)")
                        st.stop()
                    
                    # Procesar región según método seleccionado
                    processed_sequence = process_sequence_region(raw_sequence, sample_method, start_pos, length)
                    
                    # Crear objeto SeqRecord temporal para compatibilidad
                    from Bio.Seq import Seq
                    from Bio.SeqRecord import SeqRecord
                    
                    seq_record = SeqRecord(
                        Seq(processed_sequence),
                        id=fasta_data['organism_name'].replace(' ', '_'),
                        description=fasta_data['gene_info']
                    )
                    
                    st.success(f"Secuencia FASTA procesada: {len(processed_sequence)} nucleótidos ({sample_method})")
                    
                except Exception as e:
                    st.error(f"Error al procesar secuencia FASTA: {str(e)}")
                    st.stop()
                    
            elif input_method == "📁 Especies precargadas" and selected_species:
                # Usar especie precargada (buscar en NCBI)
                organism_input = selected_species
                organism_name = selected_species
                
                loading_placeholder = st.empty()
                loading_placeholder.markdown(
                    create_custom_loading_animation(
                        f"Cargando {selected_species}",
                        "Obteniendo secuencias genómicas de referencia"
                    ),
                    unsafe_allow_html=True
                )
                
                try:
                    seq_record = obtener_secuencia(selected_species)
                    loading_placeholder.empty()
                    
                except Exception as e:
                    loading_placeholder.empty()
                    st.error(f"Error al cargar {selected_species}: {str(e)}")
                    st.stop()
                    
            elif input_method == "🔬 Análisis comparativo" and species1 and species2:
                # Análisis comparativo entre dos especies
                if species1 == species2:
                    st.warning("Selecciona dos especies diferentes para la comparación")
                    st.stop()
                
                # Extraer nombres científicos
                organism1 = species1.split("(")[1].replace(")", "")
                organism2 = species2.split("(")[1].replace(")", "")
                
                loading_placeholder = st.empty()
                loading_placeholder.markdown(
                    create_custom_loading_animation(
                        f"Análisis comparativo: {organism1} vs {organism2}",
                        "Obteniendo secuencias genéticas de ambas especies"
                    ),
                    unsafe_allow_html=True
                )
                
                try:
                    # Obtener secuencias de ambas especies
                    seq_record1 = obtener_secuencia(organism1)
                    seq_record2 = obtener_secuencia(organism2)
                    
                    loading_placeholder.empty()
                    
                    # Crear visualización comparativa
                    comparison_loading = st.empty()
                    comparison_loading.markdown(
                        create_custom_loading_animation(
                            "Generando análisis comparativo",
                            "Identificando diferencias genéticas específicas"
                        ),
                        unsafe_allow_html=True
                    )
                    
                    # Análisis comparativo
                    seq1 = str(seq_record1.seq)
                    seq2 = str(seq_record2.seq)
                    
                    # Crear visualización comparativa
                    fig, comparison_data = create_comparative_visualization(
                        seq1, seq2, organism1, organism2, art_style, color_theme
                    )
                    
                    comparison_loading.empty()
                    
                    # Mostrar visualización
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Mostrar análisis comparativo detallado
                    st.markdown("### 🔬 Análisis Comparativo Detallado")
                    
                    # Diferencias principales
                    differences = comparison_data['differences']
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        gc_diff = differences['gc_content']
                        st.metric(
                            "Diferencia GC", 
                            f"{gc_diff['difference']:.3f}",
                            delta=f"{gc_diff['significance']} significancia"
                        )
                    
                    with col2:
                        complexity_diff = differences['complexity']
                        st.metric(
                            "Diferencia Complejidad",
                            f"{complexity_diff['difference']:.3f}",
                            delta=f"Shannon entropy"
                        )
                    
                    with col3:
                        coding_diff = differences['coding_potential']
                        orfs_diff = coding_diff['orfs_count'][0] - coding_diff['orfs_count'][1]
                        st.metric(
                            "Diferencia ORFs",
                            f"{abs(orfs_diff)}",
                            delta=f"{'Mayor' if orfs_diff > 0 else 'Menor'} en {organism1}"
                        )
                    
                    # Insights evolutivos
                    insights = comparison_data['evolutionary_insights']
                    if insights:
                        st.markdown("### 🌳 Insights Evolutivos")
                        for insight in insights:
                            st.info(insight)
                    
                    # Guardar datos comparativos en sesión
                    st.session_state.last_comparison_data = {
                        'species': [organism1, organism2],
                        'sequences': [seq1, seq2],
                        'comparison': comparison_data,
                        'style': art_style,
                        'theme': color_theme
                    }
                    
                    # Salir del flujo normal
                    st.stop()
                    
                except Exception as e:
                    loading_placeholder.empty()
                    st.error(f"Error en análisis comparativo: {str(e)}")
                    st.stop()
            
            else:
                st.warning("Por favor selecciona un método de entrada válido")
                st.stop()
            
            # Continuar con la generación de arte si tenemos seq_record válido
            if seq_record:
                # Log de búsqueda
                log_search(organism_input, user_session=st.session_state.session_id)
                
                # Animación de carga personalizada para obtención de secuencia
                loading_placeholder = st.empty()
                loading_placeholder.markdown(
                    create_custom_loading_animation(
                        "Conectando con NCBI GenBank",
                        f"Obteniendo secuencia genética de {organism_input}"
                    ), 
                    unsafe_allow_html=True
                )
                
                seq_record = obtener_secuencia(organism_input)
                loading_placeholder.empty()
                
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
                            f"Aplicando algoritmos {art_style} con tema {color_theme}"
                        ), 
                        unsafe_allow_html=True
                    )
                    
                    fig, gc = generar_visualizacion(seq_record, style=art_style, theme=color_theme)
                    art_loading_placeholder.empty()
                    
                    # Mostrar arte generado
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Visualización Canvas animada
                    st.markdown("### 🎬 Visualización Canvas Animada")
                    sequence_str = str(seq_record.seq)[:200]  # Limitar para rendimiento
                    gc_percentage = int(gc)
                    entropy_value = 2.0  # Valor por defecto
                    
                    # Cargar y mostrar Canvas HTML
                    try:
                        with open('canvas_dna_animation.html', 'r', encoding='utf-8') as f:
                            canvas_html = f.read()
                        
                        # Inyectar datos de secuencia en el HTML
                        canvas_html = canvas_html.replace(
                            'let sequenceData = "ATCGATCGATCGTAGCTAGCTAGCTA";',
                            f'let sequenceData = "{sequence_str}";'
                        ).replace(
                            'let gcContent = 50;',
                            f'let gcContent = {gc_percentage};'
                        ).replace(
                            'let entropy = 2.0;',
                            f'let entropy = {entropy_value};'
                        )
                        
                        components.html(canvas_html, height=650, scrolling=False)
                    except FileNotFoundError:
                        st.warning("Canvas animation file not found. Showing Plotly animation only.")
                    
                    # Botones de compartir en redes sociales
                    st.markdown("### 🚀 Compartir tu Arte Genético")
                    social_buttons = create_social_share_buttons(
                        organism_input, 
                        f"Arte único generado desde el ADN de {organism_input} usando algoritmos bioinformáticos avanzados"
                    )
                    st.markdown(social_buttons, unsafe_allow_html=True)
                    
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
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(f"Generar", key=f"nft_{scientific}"):
                            st.session_state.selected_organism = scientific
                            st.rerun()
                    with col_btn2:
                        if st.button(f"Compartir", key=f"share_{scientific}"):
                            share_buttons = create_social_share_buttons(
                                scientific,
                                f"Descubre el arte genético único de {common} en GeneticFrames"
                            )
                            st.markdown(share_buttons, unsafe_allow_html=True)
        
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
                                col_gen, col_share = st.columns(2)
                                with col_gen:
                                    if st.button("🧬", key=f"extinct_{species}", help="Generar arte"):
                                        st.session_state.selected_organism = species
                                        st.rerun()
                                with col_share:
                                    if st.button("📤", key=f"extinct_share_{species}", help="Compartir"):
                                        extinct_share = create_social_share_buttons(
                                            species,
                                            f"Arte genético de especie extinta: {species} - Preservando la biodiversidad a través del arte"
                                        )
                                        st.markdown(extinct_share, unsafe_allow_html=True)
                        
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