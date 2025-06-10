# Digital Genetic Ark - Deployment Guide

## Quick Start

1. **Configure Email for NCBI Access**
   - Add your email to environment variables: `ENTREZ_EMAIL=your@email.com`
   - Required by NCBI for API access identification

2. **Launch Application**
   - Application is ready to run at `http://localhost:5000`
   - All dependencies are installed and configured

3. **Test Core Functionality**
   - Select a species from the sidebar collections
   - Generate genetic art visualization
   - Download results in PNG or HTML format

## Environment Configuration

### Required
- `NCBI_API_KEY`: Already configured (provides 10 requests/second)
- `ENTREZ_EMAIL`: **NEEDS USER INPUT** (NCBI requirement)
- `DATABASE_URL`: Auto-configured PostgreSQL connection

### Optional (NFT Features)
- `ETH_PRIVATE_KEY`: Ethereum wallet private key
- `INFURA_API_KEY`: Ethereum RPC provider
- `NFT_CONTRACT_ADDRESS`: Smart contract for minting
- `IPFS_API_KEY` & `IPFS_API_SECRET`: IPFS storage

## Application Features

### Species Collections
- **Critically Endangered**: Siberian Tiger, Sumatran Orangutan, Indian Rhinoceros
- **Megafauna**: Blue Whale, African Elephant, Great White Shark  
- **Unique Genetics**: Immortal Jellyfish, Water Bear, Common Octopus
- **Ancient Lineages**: Coelacanth, Nile Crocodile, Tuatara

### Core Capabilities
- Real genetic sequence retrieval from NCBI GenBank
- Interactive DNA visualizations with scientific accuracy
- Conservation status and population data display
- NFT creation with IPFS metadata storage
- User favorites and search history tracking

## System Status
All core components tested and operational:
- NCBI API connection: Active
- Database: Connected and initialized
- Species catalog: 12 featured species loaded
- NFT generation: Functional (blockchain optional)
- Web interface: Responsive and running

## Usage Instructions

1. **Browse Collections**: Use sidebar to explore species by category
2. **Generate Art**: Click organism names to create genetic visualizations
3. **Download Results**: Save as PNG (print) or HTML (interactive)
4. **Create NFTs**: Use blockchain features with proper wallet configuration
5. **Track Favorites**: Save interesting species for quick access

## Production Ready
The application is fully functional for educational use, conservation awareness, and digital art creation using authentic genetic data from authoritative scientific databases.