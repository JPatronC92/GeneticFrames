"""
Motor de Arte Simbólico - Genera visualizaciones que evocan la identidad de cada especie
Combina perfiles simbólicos con características genéticas reales
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from typing import Dict, List, Tuple, Optional
import math
from species_identity_profiles import SpeciesIdentityProfile, get_species_profile, enhance_profile_with_genetics

class SymbolicArtEngine:
    """Motor principal para generar arte simbólico basado en identidad de especies"""
    
    def __init__(self):
        self.color_mappings = {
            # Mapeo de colores hex a nombres para referencia
            "aggressive": ["#FF0000", "#FF4500", "#8B0000", "#DC143C"],
            "gentle": ["#90EE90", "#98FB98", "#F0FFF0", "#E0FFE0"],
            "mysterious": ["#2F4F4F", "#191970", "#483D8B", "#6A5ACD"],
            "playful": ["#FF69B4", "#FFB6C1", "#FFA500", "#FFFF00"]
        }
    
    def generate_symbolic_art(self, species_name: str, genetic_data: Dict) -> go.Figure:
        """Genera arte simbólico único para una especie específica"""
        
        # Obtener perfil de identidad de la especie
        profile = get_species_profile(species_name)
        if not profile:
            return self._create_error_visualization(species_name)
        
        # Enriquecer perfil con datos genéticos reales
        enhanced_profile = enhance_profile_with_genetics(profile, genetic_data)
        
        # Seleccionar método de visualización basado en identidad
        if enhanced_profile.base_form == "fluid":
            return self._create_fluid_identity_art(enhanced_profile, genetic_data)
        elif enhanced_profile.base_form == "angular":
            return self._create_angular_identity_art(enhanced_profile, genetic_data)
        elif enhanced_profile.base_form == "circular":
            return self._create_circular_identity_art(enhanced_profile, genetic_data)
        elif enhanced_profile.base_form == "crystalline":
            return self._create_crystalline_identity_art(enhanced_profile, genetic_data)
        else:
            return self._create_adaptive_identity_art(enhanced_profile, genetic_data)
    
    def _create_fluid_identity_art(self, profile: SpeciesIdentityProfile, genetic_data: Dict) -> go.Figure:
        """Arte fluido para especies acuáticas - evocan movimiento y gracia"""
        
        fig = go.Figure()
        
        # Parámetros basados en identidad
        flow_speed = profile.flow_intensity
        wave_complexity = profile.rhythm_complexity
        energy_amplitude = {"low": 20, "medium": 40, "high": 60, "explosive": 80}[profile.energy_level]
        
        # Crear ondas principales que representen la esencia de la especie
        t = np.linspace(0, 6*np.pi, 300)
        
        # Onda primaria - representa el movimiento principal de la especie
        primary_wave = energy_amplitude * np.sin(flow_speed * t) * (1 + 0.3 * np.sin(wave_complexity * t))
        
        # Ondas secundarias basadas en características genéticas
        genetic_signature = genetic_data.get('genetic_signature', 12345)
        secondary_phases = [(genetic_signature % 1000) / 1000 * 2 * np.pi]
        
        for i, phase in enumerate(secondary_phases):
            secondary_wave = (energy_amplitude * 0.3) * np.sin(flow_speed * 1.5 * t + phase)
            
            # Aplicar modulación emocional
            if profile.emotional_tone == "playful":
                secondary_wave += 10 * np.sin(8 * t)  # Ondulaciones juguetonas
            elif profile.emotional_tone == "mysterious":
                secondary_wave += 15 * np.sin(0.5 * t)  # Modulación lenta y profunda
            elif profile.emotional_tone == "aggressive":
                secondary_wave += 20 * np.sin(4 * t) * np.exp(-t/10)  # Picos agresivos que decaen
            
            fig.add_trace(go.Scatter(
                x=t, y=primary_wave + secondary_wave + i*30,
                mode='lines',
                line=dict(
                    color=profile.primary_colors[i % len(profile.primary_colors)],
                    width=3 - i*0.5
                ),
                name=f"Flujo {profile.common_name}",
                showlegend=False,
                hovertemplate=f"Especie: {profile.common_name}<br>Carácter: {profile.emotional_tone}"
            ))
        
        # Añadir partículas de movimiento para representar vitalidad
        if profile.energy_level in ["high", "explosive"]:
            particles_x = np.random.uniform(0, 6*np.pi, 30)
            particles_y = np.random.uniform(-50, 150, 30)
            
            fig.add_trace(go.Scatter(
                x=particles_x, y=particles_y,
                mode='markers',
                marker=dict(
                    size=np.random.uniform(3, 12, 30),
                    color=profile.secondary_colors[0],
                    opacity=0.6,
                    symbol='circle'
                ),
                name="Energía",
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Configuración específica para especies fluidas
        fig.update_layout(
            title=f"{profile.common_name} - Esencia Fluida",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor='rgba(0,20,40,0.9)',  # Fondo acuático
            paper_bgcolor='rgba(0,20,40,0.9)',
            width=800,
            height=600,
            annotations=[
                dict(
                    text=f"Carácter: {profile.emotional_tone.title()}<br>Hábitat: {profile.habitat_influence.title()}",
                    x=0.02, y=0.98,
                    xref="paper", yref="paper",
                    showarrow=False,
                    font=dict(color="white", size=12),
                    align="left"
                )
            ]
        )
        
        return fig
    
    def _create_angular_identity_art(self, profile: SpeciesIdentityProfile, genetic_data: Dict) -> go.Figure:
        """Arte angular para predadores y especies poderosas - evocan fuerza y dominio"""
        
        fig = go.Figure()
        
        # Parámetros basados en identidad del predador
        aggression_factor = {"gentle": 0.2, "mysterious": 0.5, "aggressive": 1.0, "playful": 0.3}[profile.emotional_tone]
        power_multiplier = {"apex": 2.0, "hunter": 1.5, "omnivore": 1.0, "herbivore": 0.7, "prey": 0.5}[profile.predator_type]
        
        # Crear estructura de poder - formas angulares que representen dominio
        genetic_signature = genetic_data.get('genetic_signature', 12345)
        base_angle = (genetic_signature % 360) * np.pi / 180
        
        # Generar puntos de poder basados en características genéticas
        num_power_points = int(4 + (genetic_signature % 8))  # 4-11 puntos
        
        for i in range(num_power_points):
            angle_offset = i * 2 * np.pi / num_power_points + base_angle
            
            # Radio basado en características de la especie
            base_radius = 40 + aggression_factor * 60 * power_multiplier
            genetic_modifier = 1 + (genetic_data.get('entropy', 2) / 4)  # Usar entropía genética
            radius = base_radius * genetic_modifier
            
            # Crear "garras" o "dientes" - proyecciones de poder
            angles = np.linspace(angle_offset - 0.3, angle_offset + 0.3, 10)
            radii = np.linspace(radius * 0.3, radius, 10)
            
            x_vals = radii * np.cos(angles)
            y_vals = radii * np.sin(angles)
            
            # Color basado en nivel de agresión
            color_intensity = min(aggression_factor + power_multiplier * 0.3, 1.0)
            color_index = int(color_intensity * (len(profile.primary_colors) - 1))
            color = profile.primary_colors[color_index]
            
            fig.add_trace(go.Scatter(
                x=x_vals, y=y_vals,
                mode='lines+markers',
                line=dict(color=color, width=4),
                marker=dict(size=8, color=color, symbol='triangle-up'),
                name=f"Poder {i+1}",
                showlegend=False,
                hovertemplate=f"Tipo: {profile.predator_type.title()}<br>Agresión: {aggression_factor:.1f}"
            ))
            
            # Añadir núcleo de poder en el centro
            if i == 0:
                fig.add_trace(go.Scatter(
                    x=[0], y=[0],
                    mode='markers',
                    marker=dict(
                        size=20 + power_multiplier * 10,
                        color=profile.secondary_colors[0],
                        symbol='star',
                        line=dict(color='white', width=2)
                    ),
                    name="Núcleo",
                    showlegend=False,
                    hovertemplate=f"Especie: {profile.common_name}<br>Poder: {power_multiplier:.1f}"
                ))
        
        # Añadir territorio - anillos de influencia
        if profile.predator_type in ["apex", "hunter"]:
            for ring in range(1, 4):
                circle_r = 80 + ring * 30
                circle_theta = np.linspace(0, 2*np.pi, 100)
                circle_x = circle_r * np.cos(circle_theta)
                circle_y = circle_r * np.sin(circle_theta)
                
                fig.add_trace(go.Scatter(
                    x=circle_x, y=circle_y,
                    mode='lines',
                    line=dict(
                        color=profile.secondary_colors[ring % len(profile.secondary_colors)],
                        width=2,
                        dash='dot'
                    ),
                    name=f"Territorio {ring}",
                    showlegend=False,
                    hoverinfo='skip'
                ))
        
        fig.update_layout(
            title=f"{profile.common_name} - Dominio Territorial",
            xaxis=dict(visible=False, range=[-200, 200]),
            yaxis=dict(visible=False, range=[-200, 200]),
            plot_bgcolor='rgba(20,0,0,0.9)' if aggression_factor > 0.7 else 'rgba(10,10,20,0.9)',
            paper_bgcolor='rgba(20,0,0,0.9)' if aggression_factor > 0.7 else 'rgba(10,10,20,0.9)',
            width=800,
            height=600,
            annotations=[
                dict(
                    text=f"Tipo: {profile.predator_type.title()}<br>Carácter: {profile.emotional_tone.title()}",
                    x=0.02, y=0.98,
                    xref="paper", yref="paper",
                    showarrow=False,
                    font=dict(color="white", size=12),
                    align="left"
                )
            ]
        )
        
        return fig
    
    def _create_circular_identity_art(self, profile: SpeciesIdentityProfile, genetic_data: Dict) -> go.Figure:
        """Arte circular para especies gentiles - evocan armonía y paz"""
        
        fig = go.Figure()
        
        # Parámetros de armonía basados en identidad
        gentleness = {"gentle": 1.0, "playful": 0.8, "mysterious": 0.6, "aggressive": 0.2}[profile.emotional_tone]
        harmony_level = profile.symmetry_level
        
        # Crear mandalas de armonía basados en genética
        genetic_signature = genetic_data.get('genetic_signature', 12345)
        num_harmony_rings = 3 + (genetic_signature % 5)  # 3-7 anillos
        
        for ring in range(num_harmony_rings):
            ring_radius = 30 + ring * 25
            
            # Pétalos de armonía basados en características genéticas
            petal_count = 6 + (genetic_signature % 12)  # 6-17 pétalos
            
            for petal in range(petal_count):
                petal_angle = petal * 2 * np.pi / petal_count
                
                # Forma del pétalo basada en gentileza
                petal_t = np.linspace(0, 2*np.pi, 30)
                petal_r = ring_radius * (0.8 + 0.4 * gentleness * np.sin(2 * petal_t))
                
                petal_x = petal_r * np.cos(petal_t + petal_angle)
                petal_y = petal_r * np.sin(petal_t + petal_angle)
                
                # Color basado en anillo y gentileza
                color_idx = ring % len(profile.primary_colors)
                color = profile.primary_colors[color_idx]
                
                fig.add_trace(go.Scatter(
                    x=petal_x, y=petal_y,
                    mode='lines',
                    line=dict(color=color, width=2),
                    fill='tonext' if petal == 0 else None,
                    fillcolor=f'rgba{tuple(list(px.colors.hex_to_rgb(color)) + [0.3])}',
                    name=f"Armonía {ring+1}",
                    showlegend=False,
                    hovertemplate=f"Anillo: {ring+1}<br>Gentileza: {gentleness:.1f}"
                ))
        
        # Núcleo central de paz
        center_size = 15 + gentleness * 20
        fig.add_trace(go.Scatter(
            x=[0], y=[0],
            mode='markers',
            marker=dict(
                size=center_size,
                color=profile.secondary_colors[0],
                symbol='circle',
                line=dict(color='white', width=2)
            ),
            name="Centro de Paz",
            showlegend=False,
            hovertemplate=f"Especie: {profile.common_name}<br>Armonía: {harmony_level:.1f}"
        ))
        
        # Añadir elementos de ternura si es apropiado
        if profile.emotional_tone == "gentle":
            # Pequeñas flores de ternura alrededor
            for i in range(8):
                flower_angle = i * np.pi / 4
                flower_x = 150 * np.cos(flower_angle)
                flower_y = 150 * np.sin(flower_angle)
                
                fig.add_trace(go.Scatter(
                    x=[flower_x], y=[flower_y],
                    mode='markers',
                    marker=dict(
                        size=12,
                        color=profile.secondary_colors[1],
                        symbol='star',
                        opacity=0.7
                    ),
                    name=f"Ternura {i+1}",
                    showlegend=False,
                    hoverinfo='skip'
                ))
        
        fig.update_layout(
            title=f"{profile.common_name} - Círculo de Armonía",
            xaxis=dict(visible=False, range=[-200, 200]),
            yaxis=dict(visible=False, range=[-200, 200]),
            plot_bgcolor='rgba(0,20,0,0.9)',  # Fondo natural
            paper_bgcolor='rgba(0,20,0,0.9)',
            width=800,
            height=600,
            annotations=[
                dict(
                    text=f"Carácter: {profile.emotional_tone.title()}<br>Armonía: {harmony_level:.1%}",
                    x=0.02, y=0.98,
                    xref="paper", yref="paper",
                    showarrow=False,
                    font=dict(color="white", size=12),
                    align="left"
                )
            ]
        )
        
        return fig
    
    def _create_crystalline_identity_art(self, profile: SpeciesIdentityProfile, genetic_data: Dict) -> go.Figure:
        """Arte cristalino para especies complejas - evocan inteligencia y misterio"""
        
        fig = go.Figure()
        
        # Parámetros de complejidad
        complexity = genetic_data.get('entropy', 2) / 4  # Normalizar entropía
        mystery_factor = {"mysterious": 1.0, "aggressive": 0.6, "gentle": 0.4, "playful": 0.7}[profile.emotional_tone]
        
        # Crear estructura cristalina basada en características genéticas
        genetic_signature = genetic_data.get('genetic_signature', 12345)
        
        # Generar vértices de cristal basados en genética
        num_vertices = 6 + (genetic_signature % 10)  # 6-15 vértices
        vertices = []
        
        for i in range(num_vertices):
            angle = i * 2 * np.pi / num_vertices
            
            # Radio variable basado en complejidad genética
            base_radius = 60 + complexity * 40
            radius_variation = 1 + 0.5 * mystery_factor * np.sin(3 * angle)
            radius = base_radius * radius_variation
            
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            vertices.append((x, y))
        
        # Crear conexiones inteligentes entre vértices
        for i, vertex1 in enumerate(vertices):
            for j, vertex2 in enumerate(vertices[i+1:], i+1):
                # Conectar basado en proximidad genética
                distance = np.sqrt((vertex1[0] - vertex2[0])**2 + (vertex1[1] - vertex2[1])**2)
                connection_threshold = 100 + complexity * 50
                
                if distance < connection_threshold:
                    # Grosor de línea basado en complejidad
                    line_width = 1 + complexity * 3
                    
                    fig.add_trace(go.Scatter(
                        x=[vertex1[0], vertex2[0]],
                        y=[vertex1[1], vertex2[1]],
                        mode='lines',
                        line=dict(
                            color=profile.primary_colors[i % len(profile.primary_colors)],
                            width=line_width
                        ),
                        name=f"Conexión {i}-{j}",
                        showlegend=False,
                        hovertemplate=f"Complejidad: {complexity:.2f}<br>Distancia: {distance:.1f}"
                    ))
        
        # Añadir nodos de inteligencia
        for i, vertex in enumerate(vertices):
            node_size = 8 + complexity * 12 + mystery_factor * 5
            
            fig.add_trace(go.Scatter(
                x=[vertex[0]], y=[vertex[1]],
                mode='markers',
                marker=dict(
                    size=node_size,
                    color=profile.secondary_colors[i % len(profile.secondary_colors)],
                    symbol='diamond',
                    line=dict(color='white', width=1)
                ),
                name=f"Nodo {i+1}",
                showlegend=False,
                hovertemplate=f"Nodo: {i+1}<br>Inteligencia: {mystery_factor:.1f}"
            ))
        
        # Núcleo central de consciencia
        fig.add_trace(go.Scatter(
            x=[0], y=[0],
            mode='markers',
            marker=dict(
                size=20 + complexity * 15,
                color=profile.primary_colors[0],
                symbol='hexagon',
                line=dict(color='gold', width=3)
            ),
            name="Consciencia",
            showlegend=False,
            hovertemplate=f"Especie: {profile.common_name}<br>Complejidad: {complexity:.2f}"
        ))
        
        fig.update_layout(
            title=f"{profile.common_name} - Matriz de Consciencia",
            xaxis=dict(visible=False, range=[-150, 150]),
            yaxis=dict(visible=False, range=[-150, 150]),
            plot_bgcolor='rgba(10,0,30,0.9)',  # Fondo místico
            paper_bgcolor='rgba(10,0,30,0.9)',
            width=800,
            height=600,
            annotations=[
                dict(
                    text=f"Complejidad: {complexity:.1%}<br>Misterio: {mystery_factor:.1%}",
                    x=0.02, y=0.98,
                    xref="paper", yref="paper",
                    showarrow=False,
                    font=dict(color="white", size=12),
                    align="left"
                )
            ]
        )
        
        return fig
    
    def _create_adaptive_identity_art(self, profile: SpeciesIdentityProfile, genetic_data: Dict) -> go.Figure:
        """Arte adaptativo para especies únicas - combina múltiples estilos"""
        
        # Seleccionar elementos de diferentes estilos basados en características
        if profile.habitat_influence == "aquatic":
            return self._create_fluid_identity_art(profile, genetic_data)
        elif profile.predator_type in ["apex", "hunter"]:
            return self._create_angular_identity_art(profile, genetic_data)
        elif profile.emotional_tone == "gentle":
            return self._create_circular_identity_art(profile, genetic_data)
        else:
            return self._create_crystalline_identity_art(profile, genetic_data)
    
    def _create_error_visualization(self, species_name: str) -> go.Figure:
        """Visualización de error cuando no se puede generar arte específico"""
        
        fig = go.Figure()
        
        fig.add_annotation(
            text=f"No se pudo generar arte simbólico para: {species_name}",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16, color="red")
        )
        
        fig.update_layout(
            title="Error en Generación de Arte",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor='black',
            paper_bgcolor='black',
            width=800,
            height=600
        )
        
        return fig