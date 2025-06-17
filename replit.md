# DNA Art Generator

## Overview

DNA Art Generator is a Streamlit-based web application that creates unique visual art from DNA sequences of different animal species. The application combines real genetic data from NCBI databases with symbolic identity profiles to generate species-specific artistic visualizations. It serves as an intersection between bioinformatics, data visualization, and digital art.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit for web interface
- **Visualization**: Plotly for interactive graphics and charts
- **Styling**: Custom CSS with multiple color themes (scientific, natural, cosmic)
- **Deployment**: Configured for autoscale deployment on Replit with port 5000

### Backend Architecture
- **Language**: Python 3.11
- **Web Framework**: Streamlit server
- **Database**: SQLAlchemy ORM with PostgreSQL 16
- **External APIs**: NCBI Entrez for genetic data retrieval
- **Data Processing**: BioPython for sequence analysis and manipulation

### Core Components
1. **Animal Search Engine** (`animal_search.py`): Multi-database species lookup system
2. **Symbolic Art Engine** (`symbolic_art_engine.py`): Generates species-specific visualizations
3. **Species Identity Profiles** (`species_identity_profiles.py`): Maps species to visual characteristics
4. **Database Layer** (`database.py`): Handles data persistence and caching

## Key Components

### Data Sources and Search
- **NCBI Integration**: Uses BioPython's Entrez module to fetch real DNA sequences
- **Multi-API Search**: Integrates GBIF, EOL, and ITIS databases for comprehensive species lookup
- **Bilingual Support**: Handles common names in English and Spanish
- **Local Mapping**: Fallback dictionary for common species name-to-scientific name conversion

### Visualization Engine
- **Identity-Based Rendering**: Four distinct visual forms (fluid, angular, circular, crystalline)
- **Species Profiles**: Pre-defined visual characteristics for different animal types
- **Genetic Enhancement**: Real DNA data influences color patterns, complexity, and visual elements
- **Multiple Themes**: Scientific, natural, and cosmic color schemes

### Database Schema
- **DNASequence Table**: Stores sequence metadata, nucleotide counts, GC content, and access statistics
- **SearchHistory Table**: Tracks user searches and popular organisms
- **Caching Strategy**: Prevents redundant API calls and improves performance

## Data Flow

1. **User Input**: User enters animal common name or scientific name
2. **Species Resolution**: Animal search engine resolves to scientific name using multiple databases
3. **DNA Retrieval**: NCBI Entrez API fetches mitochondrial DNA sequences
4. **Sequence Analysis**: BioPython calculates nucleotide composition, GC content, and other metrics
5. **Profile Matching**: Species identity profile system determines visual characteristics
6. **Art Generation**: Symbolic art engine creates visualization combining genetic data with species identity
7. **Caching**: Results stored in PostgreSQL for future reference
8. **Display**: Interactive Plotly visualization presented to user

## External Dependencies

### APIs and Services
- **NCBI Entrez**: Primary source for genetic sequence data
- **GBIF API**: Global Biodiversity Information Facility for species lookup
- **Encyclopedia of Life (EOL)**: Additional species information
- **ITIS**: Integrated Taxonomic Information System

### Python Libraries
- **BioPython**: DNA sequence manipulation and analysis
- **Plotly**: Interactive data visualization
- **SQLAlchemy**: Database ORM and migrations
- **Streamlit**: Web application framework
- **NumPy/SciPy**: Mathematical operations and array processing
- **Requests**: HTTP client for API interactions

### Infrastructure
- **PostgreSQL 16**: Primary database for data persistence
- **Nix Packages**: System-level dependencies including Cairo, FFmpeg, IPFS client
- **Replit Environment**: Cloud-based development and deployment platform

## Deployment Strategy

### Environment Configuration
- **Replit Modules**: Python 3.11, PostgreSQL 16, Python3
- **Nix Channel**: Stable 24.05 with graphics and multimedia packages
- **Port Configuration**: Application runs on port 5000, externally accessible on port 80
- **Autoscale Target**: Configured for automatic scaling based on demand

### Database Setup
- **Migration System**: Alembic for database schema versioning
- **Connection Management**: SQLAlchemy session management with connection pooling
- **Environment Variables**: DATABASE_URL required for production deployment

### Security Considerations
- **API Keys**: Stored in Streamlit secrets configuration
- **Database Credentials**: Managed through environment variables
- **Session Management**: UUID-based session tracking for user analytics

## Changelog

- June 16, 2025: Universal DNA Art Algorithm Implementation
  - Implemented universal algorithm applicable to any animal species
  - Added advanced genome sequence prioritization (complete genomes > chromosomes > organelles)
  - Enhanced genetic analysis with 15+ parameters (GC content, entropy, complexity, skew, patterns)
  - Created multi-layer visual system (habitat backgrounds, DNA textures, complexity elements)
  - Developed structure determination based on GC content (linear/circular/spiral)
  - Added comprehensive sequence type detection and reporting
  - Implemented detailed genetic parameter visualization in interface
- June 16, 2025: Major refactoring and optimization
  - Consolidated 2795 lines to 400+ optimized lines
  - Eliminated 30+ redundant functions
  - Unified pattern generation system with 6 taxonomic categories
  - Implemented semantic color palettes by biological classification
  - Created streamlined animation system with 3 core types
  - Fixed all color validation errors and performance issues
- June 15, 2025: Initial setup with comprehensive features

## User Preferences

Preferred communication style: Simple, everyday language.