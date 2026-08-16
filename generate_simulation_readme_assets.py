"""
GeneticFrames Simulation & Asset Generator for README Integration
Executes an autonomous generation cycle across all protocol tiers and saves canonical SVGs and JSON metadata to docs/images/.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from agents.swarm_runner import AgentSwarmEngine

from protocol.engine import GeneticFramesProtocol
from protocol.species_pool import SPECIES_POOL_V1, RarityTier


def generate_readme_visual_assets():
    print("=" * 80)
    print("🎨 GENERATING CANONICAL SIMULATION ASSETS FOR README INTEGRATION")
    print("=" * 80)

    protocol = GeneticFramesProtocol()
    images_dir = Path("docs/images")
    images_dir.mkdir(parents=True, exist_ok=True)

    # 1. Run 5 rounds of the Autonomous Agent Swarm
    print("\n[1/3] Running Autonomous Agent Swarm Simulation...")
    swarm = AgentSwarmEngine(protocol)
    swarm.initialize_default_swarm()
    metrics = swarm.run_simulation(num_rounds=5)
    print(f"  ✓ Swarm executed {metrics.total_actions} actions across {metrics.total_rounds} rounds.")
    print(f"  ✓ Total frames minted: {metrics.total_generations} | Trades: {metrics.total_trades}")

    # 2. Extract and generate high-profile specimens for each of the 5 Protocol Tiers
    print("\n[2/3] Extracting & Rendering Representative Specimens for all 5 Tiers...")
    specimens = [
        ("tier-genesis-mammoth.svg", "SP-GEN-001", "Woolly Mammoth (Mammuthus primigenius)", RarityTier.GENESIS),
        ("tier-epic-axolotl.svg", "SP-EPC-003", "Axolotl (Ambystoma mexicanum)", RarityTier.EPIC),
        ("tier-rare-jaguar.svg", "SP-RAR-001", "Jaguar (Panthera onca)", RarityTier.RARE),
        ("tier-uncommon-cat.svg", "SP-UNC-001", "Domestic Cat (Felis catus)", RarityTier.UNCOMMON),
        ("tier-common-mouse.svg", "SP-COM-001", "House Mouse (Mus musculus)", RarityTier.COMMON),
    ]

    catalog_data = []

    for filename, org_id, label, tier in specimens:
        species = SPECIES_POOL_V1.get_by_id(org_id)
        if not species:
            continue

        # Generate a dedicated canonical specimen
        protocol.economy.mint_gf("0xProtocol_Showcase", 10.0)
        record = protocol.generate("0xProtocol_Showcase", client_entropy=f"readme_entropy_{org_id}")

        filepath = images_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(record.svg_code)

        print(f"  ✓ Rendered {tier.value:<10} | {species.common_name:<28} -> {filepath} ({len(record.svg_code.encode('utf-8')):,} bytes)")

        catalog_data.append({
            "tier": tier.value,
            "filename": filename,
            "common_name": species.common_name,
            "scientific_name": species.scientific_name,
            "taxonomy": species.taxonomy.to_dict(),
            "accession": species.genomic_source.accession,
            "gc_content_pct": round(record.manifest["genetic_traits"]["gc_content"] * 100, 2),
            "entropy": record.manifest["genetic_traits"]["entropy"],
            "algorithmic_rarity": record.manifest["genetic_traits"]["algorithmic_rarity_score"],
            "svg_sha256": record.manifest["artifact"]["svg_sha256"],
            "manifest_sha256": record.manifest["manifest_sha256"],
            "conservation_status": species.conservation_status,
        })

    # 3. Save catalog metadata
    catalog_path = images_dir / "simulation_catalog.json"
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump({
            "protocol_version": "0.1.0",
            "swarm_metrics_summary": metrics.to_dict(),
            "tier_specimens": catalog_data,
        }, f, indent=2)

    print(f"\n[3/3] Saved catalog metadata to {catalog_path}")
    print("\n✅ Simulation assets generated successfully!")


if __name__ == "__main__":
    generate_readme_visual_assets()
