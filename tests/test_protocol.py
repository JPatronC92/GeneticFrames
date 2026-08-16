"""
Comprehensive unit and integration test suite for GeneticFrames Protocol.
"""
import pytest
from deterministic_nft_engine import FragmentPolicy, canonicalize_dna
from protocol.agent_sdk import GeneticFramesAgentSDK
from protocol.economy import EconomyLedger, OrderStatus
from protocol.engine import GeneticFramesProtocol
from protocol.manifest import ManifestBuilder
from protocol.randomness import RandomnessEngine, RandomnessProof
from protocol.species_pool import (
    SPECIES_POOL_V1,
    RarityTier,
    SpeciesEntry,
    SpeciesPool,
    TIER_PROBABILITIES,
)
from protocol.verifier import ProtocolVerifier


class TestRandomnessEngine:
    def test_scalar_bounds_and_proof_structure(self):
        engine = RandomnessEngine(epoch=1, epoch_secret="test_secret_123")
        tier_scalar, species_scalar, proof = engine.derive_draw(
            generation_id=1,
            agent_id="0xTestAgent",
            nonce=0,
            client_entropy="entropy_xyz",
        )
        assert 0.0 <= tier_scalar < 1.0
        assert 0.0 <= species_scalar < 1.0
        assert proof.epoch == 1
        assert proof.generation_id == 1
        assert len(proof.composite_seed_hash) == 64
        assert RandomnessEngine.verify_proof_consistency(proof)

    def test_determinism_with_same_inputs(self):
        engine = RandomnessEngine(epoch=1, epoch_secret="constant_secret")
        t1, s1, p1 = engine.derive_draw(10, "0xAgent", 5, "entropy_abc")
        t2, s2, p2 = engine.derive_draw(10, "0xAgent", 5, "entropy_abc")
        assert t1 == t2
        assert s1 == s2
        assert p1.composite_seed_hash == p2.composite_seed_hash


class TestSpeciesPool:
    def test_tier_selection_thresholds(self):
        pool = SPECIES_POOL_V1
        assert pool.get_tier_from_scalar(0.0) == RarityTier.COMMON
        assert pool.get_tier_from_scalar(0.59) == RarityTier.COMMON
        assert pool.get_tier_from_scalar(0.60) == RarityTier.UNCOMMON
        assert pool.get_tier_from_scalar(0.84) == RarityTier.UNCOMMON
        assert pool.get_tier_from_scalar(0.85) == RarityTier.RARE
        assert pool.get_tier_from_scalar(0.94) == RarityTier.RARE
        assert pool.get_tier_from_scalar(0.95) == RarityTier.EPIC
        assert pool.get_tier_from_scalar(0.989) == RarityTier.EPIC
        assert pool.get_tier_from_scalar(0.99) == RarityTier.GENESIS
        assert pool.get_tier_from_scalar(0.9999) == RarityTier.GENESIS

    def test_species_draw_returns_valid_organism(self):
        pool = SPECIES_POOL_V1
        tier, species = pool.draw_species(tier_scalar=0.88, species_scalar=0.1)
        assert tier == RarityTier.RARE
        assert species.tier == RarityTier.RARE
        assert len(species.reference_sequence) >= 64

    def test_family_grouping(self):
        pool = SPECIES_POOL_V1
        felidae = pool.get_family_species("Felidae")
        assert len(felidae) >= 5
        names = [s.scientific_name for s in felidae]
        assert "Panthera onca" in names
        assert "Felis catus" in names


class TestManifestAndVerifier:
    def test_manifest_generation_and_full_verification(self):
        protocol = GeneticFramesProtocol()
        protocol.economy.mint_gf("0xAlice", 10.0)

        record = protocol.generate(agent_id="0xAlice")
        assert record.frame_id == 1
        assert record.owner_id == "0xAlice"
        assert record.manifest["schema"] == "geneticframes-manifest-v1"

        # Complete Verification
        res = protocol.verify_frame(record.frame_id)
        assert res.is_valid is True
        assert res.manifest_integrity is True
        assert res.sequence_matches_hash is True
        assert res.fragment_matches_hash is True
        assert res.artifact_reproducible is True
        assert res.randomness_proof_valid is True

    def test_verifier_catches_tampered_manifest(self):
        protocol = GeneticFramesProtocol()
        protocol.economy.mint_gf("0xAlice", 5.0)
        record = protocol.generate(agent_id="0xAlice")

        # Tamper with manifest
        corrupted_manifest = dict(record.manifest)
        corrupted_manifest["protocol_rarity"] = {"tier": "Genesis", "draw_probability": 0.01}

        res = ProtocolVerifier.verify_full_frame(
            sequence=record.raw_sequence,
            svg_code=record.svg_code,
            manifest=corrupted_manifest,
        )
        assert res.is_valid is False
        assert res.manifest_integrity is False

    def test_verifier_catches_mutated_sequence(self):
        protocol = GeneticFramesProtocol()
        protocol.economy.mint_gf("0xAlice", 5.0)
        record = protocol.generate(agent_id="0xAlice")

        mutated_seq = "T" + record.raw_sequence[1:]
        res = ProtocolVerifier.verify_full_frame(
            sequence=mutated_seq,
            svg_code=record.svg_code,
            manifest=record.manifest,
        )
        assert res.is_valid is False
        assert res.sequence_matches_hash is False


class TestEconomyAndMarketplace:
    def test_wallet_burn_and_transfers(self):
        ledger = EconomyLedger()
        ledger.mint_gf("0xUser1", 10.0)
        assert ledger.get_balance("0xUser1") == 10.0

        ledger.burn_gf("0xUser1", 1.0)
        assert ledger.get_balance("0xUser1") == 9.0
        assert ledger.total_gf_burned == 1.0

        ledger.transfer_gf("0xUser1", "0xUser2", 4.0)
        assert ledger.get_balance("0xUser1") == 5.0
        assert ledger.get_balance("0xUser2") == 4.0

        with pytest.raises(ValueError):
            ledger.burn_gf("0xUser1", 100.0)

    def test_market_listing_buy_settlement(self):
        protocol = GeneticFramesProtocol()
        seller = GeneticFramesAgentSDK(protocol, "0xSeller")
        buyer = GeneticFramesAgentSDK(protocol, "0xBuyer")

        seller.deposit_gf(5.0)
        buyer.deposit_gf(20.0)

        gen_res = seller.generate()
        frame_id = gen_res["frame_id"]

        # Seller lists at 8 GF
        listing = seller.create_ask(frame_id=frame_id, price_gf=8.0)
        assert listing["status"] == "active"

        # Buyer buys listing
        trade = buyer.buy_listing(listing["listing_id"])
        assert trade["price_gf"] == 8.0
        assert trade["fee_gf"] == 8.0 * 0.015

        # Check balances & ownership
        assert buyer.get_balance() == 12.0
        assert seller.get_balance() == 4.0 + (8.0 - trade["fee_gf"])
        assert buyer.list_my_frames()[0]["frame_id"] == frame_id

    def test_market_bids(self):
        protocol = GeneticFramesProtocol()
        owner = GeneticFramesAgentSDK(protocol, "0xOwner")
        bidder = GeneticFramesAgentSDK(protocol, "0xBidder")

        owner.deposit_gf(5.0)
        bidder.deposit_gf(15.0)

        gen_res = owner.generate()
        frame_id = gen_res["frame_id"]

        bid = bidder.place_bid(frame_id=frame_id, bid_amount_gf=6.0)
        assert bid["status"] == "active"

        trade = owner.accept_bid(bid["bid_id"])
        assert trade["price_gf"] == 6.0
        assert bidder.list_my_frames()[0]["frame_id"] == frame_id

    def test_market_swaps(self):
        protocol = GeneticFramesProtocol()
        agent1 = GeneticFramesAgentSDK(protocol, "0xAgent1")
        agent2 = GeneticFramesAgentSDK(protocol, "0xAgent2")

        agent1.deposit_gf(10.0)
        agent2.deposit_gf(10.0)

        f1 = agent1.generate()["frame_id"]
        f2 = agent2.generate()["frame_id"]

        swap = agent1.propose_swap(offered_frame_id=f1, requested_frame_id=f2, delta_gf=2.0)
        assert swap["status"] == "active"

        agent2.accept_swap(swap["swap_id"])
        assert agent1.list_my_frames()[0]["frame_id"] == f2
        assert agent2.list_my_frames()[0]["frame_id"] == f1
        assert agent1.get_balance() == 7.0  # 10 - 1 (burn) - 2 (delta)
        assert agent2.get_balance() == 11.0 # 10 - 1 (burn) + 2 (delta)

    def test_collection_progress(self):
        protocol = GeneticFramesProtocol()
        agent = GeneticFramesAgentSDK(protocol, "0xCollector")
        agent.deposit_gf(20.0)

        for _ in range(8):
            agent.generate()

        progress = agent.check_collection_progress("Felidae")
        assert "total_species" in progress
        assert "owned_species" in progress
        assert 0.0 <= progress["percentage"] <= 100.0
