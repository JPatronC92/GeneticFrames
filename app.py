import streamlit as st
from Bio import Entrez, SeqIO
from Bio.SeqUtils import gc_fraction
import plotly.express as px
import io
import os
from datetime import datetime
import uuid
from database import (
    create_tables, save_dna_sequence, log_search, 
    get_popular_organisms, get_recent_sequences, 
    add_favorite, get_user_favorites, get_database_stats
)

# Configuración de Entrez con variables de entorno
Entrez.email = os.getenv("ENTREZ_EMAIL", "researcher@example.com")
Entrez.api_key = os.getenv("NCBI_API_KEY", None)  # Opcional para mayor límite de requests

# Cache para evitar repetir búsquedas
@st.cache_data(ttl=3600, show_spinner="Buscando en bases de datos genéticas...")
def obtener_secuencia(organismo):
    """Obtiene secuencia de ADN desde NCBI"""
    try:
        search = Entrez.esearch(db="nucleotide", term=organismo, retmax=1, idtype="acc")
        record = Entrez.read(search)
        search.close()
        
        if not record["IdList"]:
            return None
            
        seq_id = record["IdList"][0]
        fetch = Entrez.efetch(db="nucleotide", id=seq_id, rettype="fasta", retmode="text")
        seq_record = SeqIO.read(fetch, "fasta")
        fetch.close()
        
        return seq_record
        
    except Exception as e:
        st.error(f"Error al acceder a NCBI: {str(e)}")
        return None

# Mapeo científico de bases a atributos visuales (fijo)
BASE_ART_MAP = {
    'A': {'color': '#FF5555', 'size': 10, 'symbol': 'circle'},     # Adenina
    'T': {'color': '#FFFF50', 'size': 12, 'symbol': 'diamond'},    # Timina
    'C': {'color': '#5555FF', 'size': 8, 'symbol': 'square'},      # Citosina
    'G': {'color': '#55FF55', 'size': 14, 'symbol': 'star'},       # Guanina
    'N': {'color': '#AAAAAA', 'size': 6, 'symbol': 'x'}            # Desconocido
}

def generar_visualizacion(seq_record):
    """Crea visualización científica del ADN"""
    secuencia = str(seq_record.seq).upper()
    gc = gc_fraction(secuencia) * 100
    
    # Preparar datos para Plotly
    bases = []
    posiciones = []
    propiedades = []
    
    # Limitar longitud para mejor rendimiento visual
    max_length = min(len(secuencia), 500)
    
    for i, base in enumerate(secuencia[:max_length]):
        if base not in BASE_ART_MAP:
            base = 'N'  # Para bases no estándar
            
        bases.append(base)
        posiciones.append(i)
        propiedades.append(BASE_ART_MAP[base])
    
    # Crear figura científica
    fig = px.scatter(
        x=posiciones,
        y=[1]*len(posiciones),  # Linea horizontal
        color=bases,
        symbol=bases,
        color_discrete_map={k: v['color'] for k, v in BASE_ART_MAP.items()},
        symbol_map={k: v['symbol'] for k, v in BASE_ART_MAP.items()},
        size=[prop['size'] for prop in propiedades],
        title=f"Visualización Científica de: {seq_record.id}",
        hover_data={'x': posiciones, 'color': bases}
    )
    
    # Ajustes estéticos
    fig.update_layout(
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Posición en secuencia",
        yaxis_visible=False,
        hovermode="x unified",
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Agregar información de hover personalizada
    fig.update_traces(
        hovertemplate="<b>Posición:</b> %{x}<br><b>Base:</b> %{marker.color}<br><extra></extra>"
    )
    
    return fig, gc

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
st.title("🧬 DNA Scientific Art Generator")
st.markdown("**Visualización científica automática de secuencias genéticas desde NCBI GenBank**")

# Configuración de credenciales NCBI
with st.expander("🔑 Configuración de credenciales NCBI", expanded=False):
    st.markdown("**Para acceso completo a la base de datos genética:**")
    
    col1, col2 = st.columns(2)
    with col1:
        email_input = st.text_input(
            "📧 Email (requerido por NCBI):",
            value="",
            placeholder="tu_email@ejemplo.com",
            help="NCBI requiere un email válido para identificar las consultas"
        )
    
    with col2:
        api_key_input = st.text_input(
            "🔐 NCBI API Key (opcional):",
            value="",
            type="password",
            placeholder="Obtén tu clave en ncbi.nlm.nih.gov/account",
            help="Aumenta el límite de consultas de 3 a 10 por segundo"
        )
    
    if st.button("💾 Guardar credenciales"):
        if email_input.strip():
            # Actualizar variables de entorno temporalmente
            os.environ["ENTREZ_EMAIL"] = email_input.strip()
            if api_key_input.strip():
                os.environ["NCBI_API_KEY"] = api_key_input.strip()
            
            # Actualizar configuración de Entrez
            Entrez.email = email_input.strip()
            if api_key_input.strip():
                Entrez.api_key = api_key_input.strip()
            
            st.success("✅ Credenciales guardadas correctamente")
            st.info("💡 Las credenciales se mantienen activas durante esta sesión")
        else:
            st.error("❌ El email es obligatorio")
    
    # Mostrar estado actual
    current_email = os.getenv("ENTREZ_EMAIL", "No configurado")
    has_api_key = "✅ Configurada" if os.getenv("NCBI_API_KEY") else "❌ No configurada"
    
    st.markdown(f"**Estado actual:**")
    st.markdown(f"- Email: `{current_email}`")
    st.markdown(f"- API Key: {has_api_key}")
    
    st.markdown("---")
    st.markdown("🔗 **Enlaces útiles:**")
    st.markdown("- [Crear cuenta NCBI](https://www.ncbi.nlm.nih.gov/account/)")
    st.markdown("- [Obtener API Key](https://www.ncbi.nlm.nih.gov/account/settings/)")
    st.markdown("- [Documentación NCBI](https://www.ncbi.nlm.nih.gov/books/NBK25497/)")

# Sidebar con configuraciones
with st.sidebar:
    st.header("🔧 Configuración")
    
    # Input del organismo
    organismo = st.text_input(
        "🔍 Organismo (nombre científico):", 
        value="Homo sapiens",
        help="Ingrese el nombre científico del organismo (ej: Escherichia coli, Saccharomyces cerevisiae)"
    )
    
    # Organismos populares
    st.subheader("🔥 Populares")
    popular_organisms = get_popular_organisms(limit=5)
    if popular_organisms:
        for org_data in popular_organisms:
            if st.button(f"{org_data['organism']} ({org_data['count']})", key=f"pop_{org_data['organism']}"):
                st.session_state.selected_organism = org_data['organism']
                st.rerun()
    
    # Favoritos del usuario
    st.subheader("⭐ Mis Favoritos")
    user_favorites = get_user_favorites(st.session_state.session_id)
    if user_favorites:
        for fav in user_favorites[:5]:
            if st.button(f"🧬 {fav.organism_name}", key=f"fav_{fav.id}"):
                st.session_state.selected_organism = fav.organism_name
                st.rerun()
    else:
        st.info("Aún no tienes favoritos")
    
    # Recientes
    st.subheader("🕒 Recientes")
    recent_sequences = get_recent_sequences(limit=3)
    if recent_sequences:
        for seq in recent_sequences:
            if st.button(f"📊 {seq.organism_name}", key=f"rec_{seq.id}"):
                st.session_state.selected_organism = seq.organism_name
                st.rerun()
    
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
        db_stats = get_database_stats()
        if db_stats:
            st.metric("Secuencias en BD", db_stats.get('total_sequences', 0))
            st.metric("Búsquedas totales", db_stats.get('total_searches', 0))
            st.metric("Tasa de éxito", f"{db_stats.get('success_rate', 0):.1f}%")

# Manejar selección desde sidebar
if 'selected_organism' in st.session_state:
    organismo = st.session_state.selected_organism
    del st.session_state.selected_organism

# Área principal
if st.button("🚀 Generar Visualización", type="primary", use_container_width=True):
    if not organismo.strip():
        st.error("Por favor, ingrese un nombre de organismo válido.")
        st.stop()
    
    # Registrar búsqueda
    log_search(organismo, successful=False, user_session=st.session_state.session_id)
    
    with st.spinner(f"Obteniendo secuencia genética de {organismo}..."):
        seq_record = obtener_secuencia(organismo)
        
        if not seq_record:
            st.error(f"❌ Organismo '{organismo}' no encontrado en NCBI GenBank")
            st.markdown("**Sugerencias:**")
            st.markdown("- Verifique la ortografía del nombre científico")
            st.markdown("- Pruebe con nombres más específicos (ej: 'Homo sapiens mitochondrion')")
            st.markdown("- Consulte la [base de datos NCBI](https://www.ncbi.nlm.nih.gov/nuccore) para nombres válidos")
            log_search(organismo, successful=False, error_message="Organismo no encontrado", user_session=st.session_state.session_id)
            st.stop()
            
        # Actualizar el máximo de secuencia basado en la configuración
        BASE_ART_MAP_TEMP = BASE_ART_MAP.copy()
        
        # Generar visualización
        fig, gc = generar_visualizacion(seq_record)
        
        # Registrar búsqueda exitosa
        log_search(organismo, successful=True, user_session=st.session_state.session_id)
        
        # Guardar en base de datos y obtener conteo de bases
        conteo_bases = mostrar_estadisticas_secuencia(seq_record)
        db_record = save_dna_sequence(organismo, seq_record, gc, conteo_bases)
        
        # Agregar a favoritos si está habilitado
        if save_to_favorites and db_record:
            add_favorite(st.session_state.session_id, organismo, seq_record.id)
        
        # Mostrar información básica
        st.success(f"✅ Secuencia obtenida exitosamente: **{seq_record.id}**")
        
        # Botón para agregar a favoritos
        if not save_to_favorites:
            if st.button("⭐ Agregar a favoritos"):
                if add_favorite(st.session_state.session_id, organismo, seq_record.id):
                    st.success("Agregado a favoritos")
                else:
                    st.info("Ya está en favoritos")
        
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
        
        # Sección de descarga
        st.subheader("💾 Descargar visualización")
        col1, col2 = st.columns(2)
        
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
