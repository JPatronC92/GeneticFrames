"""
AlphaFold & PDB 3D Biomorphic Art Engine
Retrieves real 3D protein structure coordinates (or predicts biomorphic folds) 
and pLDDT confidence scores from AlphaFold DB & UniProt.
"""

import requests
import numpy as np
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple
import logging
import io

logger = logging.getLogger(__name__)

# Common UniProt reference proteins for popular species fallback
KNOWN_SPECIES_UNIPROT = {
    "homo sapiens": "P02144",       # Myoglobin
    "humano": "P02144",
    "panthera leo": "P02144",       # Myoglobin
    "león": "P02144",
    "panthera tigris": "P02144",    # Myoglobin
    "tigre": "P02144",
    "canis lupus": "P02144",
    "lobo": "P02144",
    "felis catus": "P02144",
    "gato": "P02144",
    "bos taurus": "P02144",
    "vaca": "P02144",
    "arabidopsis thaliana": "P0C1DB", # Rubisco
    "escherichia coli": "P0A6F5",     # GroEL
    "saccharomyces cerevisiae": "P00044" # Cytochrome C
}

def get_uniprot_accession(organism_name: str) -> Optional[str]:
    """Find UniProt accession ID for a given organism name"""
    clean_name = organism_name.lower().strip()
    
    # Check known cache first
    if clean_name in KNOWN_SPECIES_UNIPROT:
        return KNOWN_SPECIES_UNIPROT[clean_name]
    
    try:
        url = f"https://rest.uniprot.org/uniprotkb/search?query=organism_name:\"{clean_name}\" AND reviewed:true&format=json&size=1"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                return results[0].get("primaryAccession")
        
        # Fallback broader search
        url_fallback = f"https://rest.uniprot.org/uniprotkb/search?query=\"{clean_name}\"&format=json&size=1"
        resp_fallback = requests.get(url_fallback, timeout=5)
        if resp_fallback.status_code == 200:
            data = resp_fallback.json()
            results = data.get("results", [])
            if results:
                return results[0].get("primaryAccession")
    except Exception as e:
        logger.warning(f"Error querying UniProt API for {organism_name}: {e}")
    
    return None

def fetch_alphafold_pdb_data(uniprot_id: str) -> Optional[str]:
    """Fetch PDB text content from AlphaFold DB API for a UniProt accession"""
    try:
        url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                pdb_url = data[0].get("pdbUrl")
                if pdb_url:
                    pdb_resp = requests.get(pdb_url, timeout=8)
                    if pdb_resp.status_code == 200:
                        return pdb_resp.text
    except Exception as e:
        logger.warning(f"Error fetching AlphaFold PDB for {uniprot_id}: {e}")
    
    return None

def parse_pdb_ca_atoms(pdb_text: str) -> Dict:
    """Extract C-alpha atom 3D coordinates and pLDDT (b-factor) scores from PDB text"""
    coords_x = []
    coords_y = []
    coords_z = []
    plddt_scores = []
    residue_ids = []
    residue_names = []

    for line in pdb_text.splitlines():
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            try:
                res_name = line[17:20].strip()
                res_seq = int(line[22:26].strip())
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())
                b_factor = float(line[60:66].strip())  # AlphaFold pLDDT score

                coords_x.append(x)
                coords_y.append(y)
                coords_z.append(z)
                plddt_scores.append(b_factor)
                residue_ids.append(res_seq)
                residue_names.append(res_name)
            except ValueError:
                continue

    return {
        "x": np.array(coords_x),
        "y": np.array(coords_y),
        "z": np.array(coords_z),
        "plddt": np.array(plddt_scores),
        "residue_ids": residue_ids,
        "residue_names": residue_names,
        "is_real_alphafold": True
    }

def generate_synthetic_biomorphic_fold(n_residues: int = 180, gc_content: float = 50.0, seed: int = 42) -> Dict:
    """Generates a realistic 3D biomorphic protein backbone trajectory with synthetic pLDDT scores"""
    np.random.seed(seed % 100000)
    t = np.linspace(0, 8 * np.pi, n_residues)

    # Parametric helical and sheet-like folding dynamics
    helix_freq = 0.5 + (gc_content / 100.0) * 0.5
    x = 25 * np.cos(t) + 10 * np.sin(t * helix_freq) + np.cumsum(np.random.normal(0, 0.8, n_residues))
    y = 25 * np.sin(t) + 10 * np.cos(t * helix_freq) + np.cumsum(np.random.normal(0, 0.8, n_residues))
    z = 3.0 * t + 8 * np.sin(2 * t) + np.cumsum(np.random.normal(0, 0.5, n_residues))

    # Center coordinates
    x -= np.mean(x)
    y -= np.mean(y)
    z -= np.mean(z)

    # Synthetic pLDDT (higher in secondary structures, lower in flexible loops)
    plddt = 85.0 + 12.0 * np.sin(t * 2.5) + np.random.normal(0, 4.0, n_residues)
    plddt = np.clip(plddt, 35.0, 98.0)

    amino_acids = ['ALA', 'GLU', 'LEU', 'LYS', 'VAL', 'GLY', 'SER', 'PRO', 'THR', 'ILE']
    res_names = [amino_acids[i % len(amino_acids)] for i in range(n_residues)]

    return {
        "x": x,
        "y": y,
        "z": z,
        "plddt": plddt,
        "residue_ids": list(range(1, n_residues + 1)),
        "residue_names": res_names,
        "is_real_alphafold": False
    }

def create_alphafold_biomorphic_3d_art(organism_name: str, genetic_profile: Dict, palette: Dict) -> Tuple[go.Figure, Dict]:
    """
    Builds an interactive 3D Biomorphic Plotly visualization using AlphaFold structural data & pLDDT confidence scores.
    """
    uniprot_id = get_uniprot_accession(organism_name)
    pdb_data = None
    
    if uniprot_id:
        pdb_text = fetch_alphafold_pdb_data(uniprot_id)
        if pdb_text:
            pdb_data = parse_pdb_ca_atoms(pdb_text)
    
    if not pdb_data or len(pdb_data.get("x", [])) == 0:
        gc = genetic_profile.get("gc_content", 50.0)
        seq_len = genetic_profile.get("sequence_length", 180)
        seed = int(genetic_profile.get("genetic_signature", 12345))
        n_res = min(max(int(seq_len / 30), 80), 300)
        pdb_data = generate_synthetic_biomorphic_fold(n_residues=n_res, gc_content=gc, seed=seed)

    x, y, z = pdb_data["x"], pdb_data["y"], pdb_data["z"]
    plddt = pdb_data["plddt"]
    res_ids = pdb_data["residue_ids"]
    res_names = pdb_data["residue_names"]
    is_real = pdb_data["is_real_alphafold"]

    fig = go.Figure()

    # 1. Continuous Backbone Trace (3D Line)
    fig.add_trace(go.Scatter3d(
        x=x, y=y, z=z,
        mode='lines',
        line=dict(
            color=plddt,
            colorscale=[
                [0.0, '#FF1744'],   # <50 (Desorden / Crimson)
                [0.5, '#FF9100'],   # 50-70 (Bajo / Amber)
                [0.75, '#FFD700'],  # 70-90 (Moderado / Gold)
                [1.0, '#00E5FF']    # >90 (Muy Alto / Cyan)
            ],
            width=8,
            cmin=40,
            cmax=95
        ),
        name="Cadena Proteica 3D",
        hoverinfo="none",
        showlegend=False
    ))

    # 2. Residue Atoms (3D Markers colored by pLDDT confidence)
    hover_texts = [
        f"<b>Residuo {rid} ({rname})</b><br>"
        f"Confianza pLDDT: <b>{p:.1f}</b> / 100<br>"
        f"Estado: {'Estructura Rígida' if p >= 70 else 'Región Flexible'}<br>"
        f"Coord (X,Y,Z): ({xi:.1f}, {yi:.1f}, {zi:.1f})"
        for rid, rname, p, xi, yi, zi in zip(res_ids, res_names, plddt, x, y, z)
    ]

    fig.add_trace(go.Scatter3d(
        x=x, y=y, z=z,
        mode='markers',
        marker=dict(
            size=6,
            color=plddt,
            colorscale=[
                [0.0, '#FF1744'],
                [0.5, '#FF9100'],
                [0.75, '#FFD700'],
                [1.0, '#00E5FF']
            ],
            cmin=40,
            cmax=95,
            opacity=0.9,
            line=dict(color='white', width=0.5),
            colorbar=dict(
                title=dict(text="<b>pLDDT AlphaFold</b>", font=dict(color="white", size=12)),
                tickvals=[45, 60, 80, 92],
                ticktext=["<50 Desorden", "50-70 Baja", "70-90 Alta", ">90 Muy Alta"],
                tickfont=dict(color="white", size=10),
                len=0.6,
                x=0.9
            )
        ),
        text=hover_texts,
        hoverinfo="text",
        name="Residuos CA"
    ))

    # 3. Genomic Energy Halo (Surrounding 3D genomic particles)
    n_particles = 60
    radius = np.max(np.abs(x)) * 1.3
    theta = np.linspace(0, 4 * np.pi, n_particles)
    phi = np.linspace(-np.pi/2, np.pi/2, n_particles)

    px_coords = radius * np.cos(phi) * np.cos(theta)
    py_coords = radius * np.cos(phi) * np.sin(theta)
    pz_coords = radius * np.sin(phi)

    fig.add_trace(go.Scatter3d(
        x=px_coords, y=py_coords, z=pz_coords,
        mode='markers',
        marker=dict(
            size=3,
            color=palette.get('primary', ['#8B4513'])[0],
            opacity=0.4,
            symbol='diamond'
        ),
        hoverinfo="none",
        name="Halo Genómico"
    ))

    # 3D Layout configuration
    title_prefix = f"🧬 Escultura Biomórfica 3D AlphaFold - {organism_name}"
    if uniprot_id and is_real:
        subtitle = f"UniProt ID: <b>{uniprot_id}</b> | Plegamiento Molecular Real de AlphaFold DB"
    else:
        subtitle = f"Plegamiento Biomórfico 3D Simulado según firma GC ({genetic_profile.get('gc_content', 0):.1f}%)"

    fig.update_layout(
        title=dict(
            text=f"<b>{title_prefix}</b><br><span style='font-size:12px;color:#A0A0A0;'>{subtitle}</span>",
            font=dict(size=18, color="white"),
            x=0.5
        ),
        scene=dict(
            xaxis=dict(visible=False, backgroundcolor="black"),
            yaxis=dict(visible=False, backgroundcolor="black"),
            zaxis=dict(visible=False, backgroundcolor="black"),
            bgcolor="black",
            camera=dict(
                eye=dict(x=1.6, y=1.6, z=1.2)
            )
        ),
        paper_bgcolor="black",
        plot_bgcolor="black",
        height=750,
        margin=dict(l=0, r=0, b=0, t=60)
    )

    metrics_summary = {
        "uniprot_id": uniprot_id or "Generado (Genoma)",
        "is_real": is_real,
        "avg_plddt": float(np.mean(plddt)),
        "high_confidence_ratio": float(np.sum(plddt >= 70) / len(plddt) * 100),
        "disordered_ratio": float(np.sum(plddt < 50) / len(plddt) * 100),
        "total_residues": len(res_ids)
    }

    return fig, metrics_summary
