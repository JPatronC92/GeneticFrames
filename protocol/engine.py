"""
GeneticFrames Unified Protocol Engine
Coordinates randomness, biological resolution, GFDP v2 rendering, manifests, and the agent economy.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from deterministic_nft_engine import (
    FragmentPolicy,
    calculate_algorithmic_rarity,
    canonicalize_dna,
    extract_genetic_features,
    generate_deterministic_svg,
    select_fragment,
)
from .economy import EconomyLedger, GeneticFrameRecord, MarketBid, MarketListing, MarketSwap, MarketTrade
from .manifest import ManifestBuilder
from .randomness import RandomnessEngine, RandomnessProof
from .species_pool import SPECIES_POOL_V1, RarityTier, SpeciesEntry, SpeciesPool
from .verifier import ProtocolVerifier, VerificationResult


class GeneticFramesProtocol:
    """
    Main entry point for the GeneticFrames protocol.
    """

    def __init__(
        self,
        species_pool: SpeciesPool | None = None,
        randomness_engine: RandomnessEngine | None = None,
        economy_ledger: EconomyLedger | None = None,
    ):
        self.species_pool = species_pool or SPECIES_POOL_V1
        self.randomness_engine = randomness_engine or RandomnessEngine(epoch=1)
        self.economy = economy_ledger or EconomyLedger()
        self.total_generations = 0
        self.total_frames_minted = 0

    def generate(
        self,
        agent_id: str,
        client_entropy: str | None = None,
        fragment_policy: FragmentPolicy | None = None,
    ) -> GeneticFrameRecord:
        """
        Executes the canonical GENERATE event:
        1. Burns 1 GF from agent wallet.
        2. Evaluates verifiable randomness draw.
        3. Selects tier and biological species from SpeciesPool v1.
        4. Canonicalizes DNA sequence and extracts fragment.
        5. Computes traits and algorithmic rarity.
        6. Renders deterministic GFDP v2 SVG.
        7. Builds cryptographic manifest and registers Frame in ledger.
        """
        policy = fragment_policy or FragmentPolicy(length=768, mode="center")

        # Step 1: Deduct & burn 1 GF
        self.economy.burn_gf(agent_id, amount=1.0)
        self.total_generations += 1
        generation_id = self.total_generations

        # Step 2: Randomness draw
        wallet = self.economy.get_or_create_wallet(agent_id)
        tier_scalar, species_scalar, proof = self.randomness_engine.derive_draw(
            generation_id=generation_id,
            agent_id=agent_id,
            nonce=wallet.nonce,
            client_entropy=client_entropy,
        )

        # Step 3: Draw tier and species
        tier, species = self.species_pool.draw_species(tier_scalar, species_scalar)

        # Step 4: Acquire and canonicalize sequence
        raw_sequence = canonicalize_dna(species.reference_sequence)
        fragment, fragment_offset = select_fragment(raw_sequence, policy)

        # Step 5: Extract traits and calculate algorithmic rarity
        features = extract_genetic_features(fragment)
        algo_rarity = calculate_algorithmic_rarity(features)

        # Step 6: Render GFDP v2 deterministic SVG
        svg_code, _ = generate_deterministic_svg(
            raw_sequence,
            species.scientific_name,
            fragment_policy=policy,
            source=species.genomic_source.to_dict(),
        )

        # Step 7: Build manifest
        self.total_frames_minted += 1
        frame_id = self.total_frames_minted

        manifest = ManifestBuilder.build_manifest(
            frame_id=frame_id,
            generation_id=generation_id,
            creator_agent_id=agent_id,
            current_owner_id=agent_id,
            species=species,
            protocol_tier=tier,
            randomness_proof=proof,
            sequence=raw_sequence,
            fragment=fragment,
            fragment_offset=fragment_offset,
            fragment_policy_mode=policy.mode,
            features=features,
            algorithmic_rarity=algo_rarity,
            svg_code=svg_code,
        )

        # Step 8: Register record
        record = GeneticFrameRecord(
            frame_id=frame_id,
            generation_id=generation_id,
            organism_id=species.organism_id,
            common_name=species.common_name,
            scientific_name=species.scientific_name,
            tier=tier,
            creator_id=agent_id,
            owner_id=agent_id,
            manifest=manifest,
            svg_code=svg_code,
            raw_sequence=raw_sequence,
        )
        self.economy.register_minted_frame(record)
        return record

    def inspect_frame(self, frame_id: int) -> Optional[GeneticFrameRecord]:
        return self.economy.get_frame(frame_id)

    def verify_frame(self, frame_id: int) -> VerificationResult:
        frame = self.economy.get_frame(frame_id)
        if not frame:
            return VerificationResult(
                is_valid=False,
                manifest_integrity=False,
                sequence_matches_hash=False,
                fragment_matches_hash=False,
                artifact_reproducible=False,
                randomness_proof_valid=False,
                details={"error": f"Frame #{frame_id} not found"},
            )
        return ProtocolVerifier.verify_full_frame(
            sequence=frame.raw_sequence,
            svg_code=frame.svg_code,
            manifest=frame.manifest,
        )

    def get_protocol_metrics(self) -> Dict[str, Any]:
        return {
            "epoch": self.randomness_engine.epoch,
            "species_pool_version": self.species_pool.VERSION,
            "total_generations": self.total_generations,
            "total_frames_minted": self.total_frames_minted,
            "total_gf_burned": self.economy.total_gf_burned,
            "treasury_gf_collected": self.economy.treasury_gf_collected,
            "active_listings_count": len([l for l in self.economy.listings.values() if l.status.value == "active"]),
            "active_bids_count": len([b for b in self.economy.bids.values() if b.status.value == "active"]),
            "trades_count": len(self.economy.trade_history),
        }
