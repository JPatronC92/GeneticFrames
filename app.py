import streamlit as st
from Bio import Entrez, SeqIO
from Bio.SeqUtils import gc_fraction
import plotly.express as px
import io
import os
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
        fig, gc = generar_visualizacion(seq_record)
        
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
