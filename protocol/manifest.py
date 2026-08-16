"""
GeneticFrames Manifest Builder & Canonicalizer (geneticframes-manifest-v1)
Produces cryptographic, auditable receipts for GeneticFrames.
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, Mapping

from .randomness import RandomnessProof
from .species_pool import RarityTier, SpeciesEntry, TIER_PROBABILITIES


class ManifestBuilder:
    SCHEMA_VERSION = "geneticframes-manifest-v1"
    PROTOCOL_VERSION = "1.0.0"

    @staticmethod
    def determine_era(frame_id: int) -> str:
        if frame_id <= 100_000:
            return "Genesis Era"
        elif frame_id <= 10_000_000:
            return "Emergence Era"
        return "Agent Economy Era"

    @classmethod
    def build_manifest(
        cls,
        *,
        frame_id: int,
        generation_id: int,
        creator_agent_id: str,
        current_owner_id: str,
        species: SpeciesEntry,
        protocol_tier: RarityTier,
        randomness_proof: RandomnessProof,
        sequence: str,
        fragment: str,
        fragment_offset: int,
        fragment_policy_mode: str,
        features: Dict[str, Any],
        algorithmic_rarity: Dict[str, Any],
        svg_code: str,
        timestamp: float | None = None
    ) -> Dict[str, Any]:
        """
        Builds the canonical JSON manifest and computes its SHA-256 digest.
        """
        ts = timestamp or time.time()
        era = cls.determine_era(frame_id)

        seq_sha256 = hashlib.sha256(sequence.encode("ascii")).hexdigest()
        frag_sha256 = hashlib.sha256(fragment.encode("ascii")).hexdigest()
        svg_bytes = svg_code.encode("utf-8")
        svg_sha256 = hashlib.sha256(svg_bytes).hexdigest()

        manifest_data: Dict[str, Any] = {
            "schema": cls.SCHEMA_VERSION,
            "protocol": {
                "name": "GeneticFrames",
                "version": cls.PROTOCOL_VERSION,
                "era": era,
            },
            "frame": {
                "id": frame_id,
                "generation_event_id": generation_id,
                "minted_at": ts,
            },
            "randomness": randomness_proof.to_dict(),
            "organism": {
                "organism_id": species.organism_id,
                "common_name": species.common_name,
                "scientific_name": species.scientific_name,
                "taxonomy": species.taxonomy.to_dict(),
                "conservation_status": species.conservation_status,
            },
            "genome": {
                "provider": species.genomic_source.provider,
                "database": species.genomic_source.database,
                "accession": species.genomic_source.accession,
                "sequence_length": len(sequence),
                "sequence_sha256": seq_sha256,
                "fragment_offset_zero_based": fragment_offset,
                "fragment_length": len(fragment),
                "fragment_sha256": frag_sha256,
                "fragment_policy": {
                    "mode": fragment_policy_mode,
                    "requested_length": len(fragment),
                },
            },
            "protocol_rarity": {
                "tier": protocol_tier.value,
                "draw_probability": TIER_PROBABILITIES.get(protocol_tier, 0.0),
            },
            "genetic_traits": {
                "gc_content": round(float(features.get("gc_content", 0.0)), 6),
                "at_skew": round(float(features.get("at_skew", 0.0)), 6),
                "gc_skew": round(float(features.get("gc_skew", 0.0)), 6),
                "entropy": round(float(features.get("entropy", 0.0)), 6),
                "ambiguity_ratio": round(float(features.get("ambiguity_ratio", 0.0)), 6),
                "algorithmic_rarity_score": algorithmic_rarity.get("score", 0.0),
                "algorithmic_rarity_tier": algorithmic_rarity.get("tier", "balanced"),
            },
            "artifact": {
                "renderer_id": "geneticframes-dna-svg",
                "version": "2.0.0",
                "svg_sha256": svg_sha256,
                "svg_bytes": len(svg_bytes),
            },
            "ownership": {
                "creator": creator_agent_id,
                "current_owner": current_owner_id,
            },
        }

        # Canonicalize JSON (sorted keys, compact delimiters)
        canonical_bytes = json.dumps(manifest_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        manifest_data["manifest_sha256"] = hashlib.sha256(canonical_bytes).hexdigest()

        return manifest_data

    @classmethod
    def serialize_canonical(cls, manifest: Mapping[str, Any]) -> str:
        """Returns the canonical JSON string representation."""
        data_copy = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
        return json.dumps(data_copy, sort_keys=True, separators=(",", ":"))
