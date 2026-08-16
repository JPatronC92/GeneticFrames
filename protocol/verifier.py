"""
GeneticFrames Independent Cryptographic Verifier
Allows any agent or validator to audit the authenticity and reproducibility of a GeneticFrame.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Tuple

from deterministic_nft_engine import (
    FragmentPolicy,
    canonicalize_dna,
    generate_deterministic_svg,
    select_fragment,
)
from .manifest import ManifestBuilder
from .randomness import RandomnessEngine, RandomnessProof


@dataclass(frozen=True)
class VerificationResult:
    is_valid: bool
    manifest_integrity: bool
    sequence_matches_hash: bool
    fragment_matches_hash: bool
    artifact_reproducible: bool
    randomness_proof_valid: bool
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "manifest_integrity": self.manifest_integrity,
            "sequence_matches_hash": self.sequence_matches_hash,
            "fragment_matches_hash": self.fragment_matches_hash,
            "artifact_reproducible": self.artifact_reproducible,
            "randomness_proof_valid": self.randomness_proof_valid,
            "details": self.details,
        }


class ProtocolVerifier:
    """
    Independent cryptographic auditor for GeneticFrames.
    """

    @staticmethod
    def verify_manifest_integrity(manifest: Mapping[str, Any]) -> bool:
        """Verifies manifest SHA-256 hash against its canonical content."""
        try:
            expected_hash = manifest.get("manifest_sha256")
            if not expected_hash:
                return False
            payload = ManifestBuilder.serialize_canonical(manifest)
            computed_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            return computed_hash == expected_hash
        except Exception:
            return False

    @staticmethod
    def verify_sequence_integrity(sequence: str, manifest: Mapping[str, Any]) -> bool:
        """Verifies that the provided raw DNA matches the manifest sequence SHA-256."""
        try:
            clean_seq = canonicalize_dna(sequence)
            computed_hash = hashlib.sha256(clean_seq.encode("ascii")).hexdigest()
            expected_hash = manifest["genome"]["sequence_sha256"]
            return computed_hash == expected_hash
        except Exception:
            return False

    @staticmethod
    def verify_fragment_selection(sequence: str, manifest: Mapping[str, Any]) -> Tuple[bool, str]:
        """Verifies fragment offset, length, and content checksum."""
        try:
            clean_seq = canonicalize_dna(sequence)
            frag_info = manifest["genome"]
            policy_info = frag_info["fragment_policy"]
            policy = FragmentPolicy(
                length=int(policy_info["requested_length"]),
                mode=str(policy_info["mode"]),
            )
            fragment, offset = select_fragment(clean_seq, policy)
            computed_frag_hash = hashlib.sha256(fragment.encode("ascii")).hexdigest()
            
            matches = (
                computed_frag_hash == frag_info["fragment_sha256"]
                and offset == frag_info["fragment_offset_zero_based"]
                and len(fragment) == frag_info["fragment_length"]
            )
            return matches, fragment
        except Exception:
            return False, ""

    @staticmethod
    def verify_svg_artifact(fragment: str, svg_code: str, manifest: Mapping[str, Any]) -> bool:
        """Verifies that the SVG matches both byte hash and algorithmic regeneration."""
        try:
            svg_bytes = svg_code.encode("utf-8")
            computed_svg_hash = hashlib.sha256(svg_bytes).hexdigest()
            expected_svg_hash = manifest["artifact"]["svg_sha256"]
            if computed_svg_hash != expected_svg_hash:
                return False

            # Verify deterministic reproduction from fragment
            species_name = manifest["organism"]["scientific_name"]
            reproduced_svg, _ = generate_deterministic_svg(
                fragment,
                species_name,
                fragment_policy=FragmentPolicy(length=len(fragment), mode="center")
            )
            reproduced_hash = hashlib.sha256(reproduced_svg.encode("utf-8")).hexdigest()
            return reproduced_hash == expected_svg_hash
        except Exception:
            return False

    @classmethod
    def verify_full_frame(
        cls,
        sequence: str,
        svg_code: str,
        manifest: Mapping[str, Any]
    ) -> VerificationResult:
        """
        Executes a complete 5-point cryptographic audit of the GeneticFrame.
        """
        details: Dict[str, Any] = {}

        # 1. Manifest integrity
        manifest_ok = cls.verify_manifest_integrity(manifest)
        details["manifest_check"] = "PASS" if manifest_ok else "FAIL"

        # 2. Sequence check
        seq_ok = cls.verify_sequence_integrity(sequence, manifest)
        details["sequence_check"] = "PASS" if seq_ok else "FAIL"

        # 3. Fragment check
        frag_ok, fragment = cls.verify_fragment_selection(sequence, manifest)
        details["fragment_check"] = "PASS" if frag_ok else "FAIL"

        # 4. Artifact check
        artifact_ok = cls.verify_svg_artifact(fragment, svg_code, manifest) if frag_ok else False
        details["artifact_check"] = "PASS" if artifact_ok else "FAIL"

        # 5. Randomness proof check
        rand_data = manifest.get("randomness", {})
        try:
            proof = RandomnessProof(
                scheme=rand_data.get("scheme", ""),
                epoch=rand_data.get("epoch", 0),
                generation_id=rand_data.get("generation_id", 0),
                epoch_seed_hash=rand_data.get("epoch_seed_hash", ""),
                agent_entropy_hash=rand_data.get("agent_entropy_hash", ""),
                nonce=rand_data.get("nonce", 0),
                composite_seed_hash=rand_data.get("composite_seed_hash", ""),
                tier_scalar=float(rand_data.get("tier_scalar", 0.0)),
                species_scalar=float(rand_data.get("species_scalar", 0.0)),
                timestamp=float(rand_data.get("timestamp", 0.0)),
            )
            rand_ok = RandomnessEngine.verify_proof_consistency(proof)
        except Exception:
            rand_ok = False
        details["randomness_check"] = "PASS" if rand_ok else "FAIL"

        is_valid = manifest_ok and seq_ok and frag_ok and artifact_ok and rand_ok
        return VerificationResult(
            is_valid=is_valid,
            manifest_integrity=manifest_ok,
            sequence_matches_hash=seq_ok,
            fragment_matches_hash=frag_ok,
            artifact_reproducible=artifact_ok,
            randomness_proof_valid=rand_ok,
            details=details,
        )
