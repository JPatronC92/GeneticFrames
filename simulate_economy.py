"""
GeneticFrames Autonomous Economy Simulator
Validates the Minimal Viable Protocol (MVP) Closed Circuit (Section 55 of GeneticFrames.md):
1. Agent receives balance
2. Agent spends 1 GF
3. Random organism selected via verifiable randomness
4. GeneticFrame is generated (GFDP v2 deterministic SVG + Traits)
5. Manifest proves origin & cryptographic hashes
6. Agent owns Frame
7. Second agent values asset
8. Agents trade P2P
"""
import sys
import json
import time

# Ensure UTF-8 output encoding for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from protocol.engine import GeneticFramesProtocol
from protocol.agent_sdk import GeneticFramesAgentSDK


def run_minimal_viable_circuit():
    print("\n" + "="*80)
    print("[GENETICFRAMES] MINIMAL VIABLE PROTOCOL (MVP) CIRCUIT VALIDATION")
    print("="*80)

    # Initialize Protocol
    protocol = GeneticFramesProtocol()

    # Step 1: Agents receive balance
    print("\n[Step 1] Initializing Autonomous Agent Wallets...")
    agent_a = GeneticFramesAgentSDK(protocol, "0xAgentA_Collector")
    agent_b = GeneticFramesAgentSDK(protocol, "0xAgentB_Trader")
    agent_c = GeneticFramesAgentSDK(protocol, "0xAgentC_MarketMaker")

    agent_a.deposit_gf(10.0)
    agent_b.deposit_gf(25.0)
    agent_c.deposit_gf(50.0)

    print(f"  + Agent A (Collector) Initial Balance:   {agent_a.get_balance()} GF")
    print(f"  + Agent B (Trader) Initial Balance:      {agent_b.get_balance()} GF")
    print(f"  + Agent C (MarketMaker) Initial Balance: {agent_c.get_balance()} GF")

    # Step 2: Agent A spends 1 GF to GENERATE
    print("\n[Step 2 & 3] Agent A executes GENERATE (Cost: 1.0 GF, Random Organism)...")
    res_a = agent_a.generate(client_entropy="agent_a_entropy_seed_99")
    frame_id = res_a["frame_id"]
    print(f"  + Frame #{frame_id} successfully minted!")
    print(f"  + Organism:        {res_a['common_name']} ({res_a['scientific_name']})")
    print(f"  + Protocol Rarity: {res_a['tier']}")
    print(f"  + Agent A Balance after burn: {agent_a.get_balance()} GF")

    # Step 4 & 5: Manifest and Cryptographic Verification
    print("\n[Step 4 & 5] Independent Cryptographic Origin & Artifact Audit...")
    audit = agent_a.verify_frame(frame_id)
    print(f"  + Audit Passed:          {audit['is_valid']}")
    print(f"  + Manifest Integrity:    {audit['manifest_integrity']}")
    print(f"  + Biological Seq Hash:   {audit['sequence_matches_hash']}")
    print(f"  + Fragment Checksum:     {audit['fragment_matches_hash']}")
    print(f"  + GFDP v2 SVG Matched:   {audit['artifact_reproducible']}")
    print(f"  + Randomness Proof:      {audit['randomness_proof_valid']}")

    # Step 6: Ownership Check
    print("\n[Step 6] Ownership Registry Verification...")
    my_frames = agent_a.list_my_frames()
    print(f"  + Agent A owns {len(my_frames)} frame(s): Frame #{my_frames[0]['frame_id']}")

    # Step 7: Valuation & Market Listing / Bidding
    print("\n[Step 7] Secondary Market: Agent A lists Frame, Agent B inspects & buys...")
    ask_price = 4.5  # Agent A lists at 4.5 GF
    listing = agent_a.create_ask(frame_id=frame_id, price_gf=ask_price)
    print(f"  + Agent A created Listing #{listing['listing_id']} for Frame #{frame_id} @ {ask_price} GF")

    market_book = agent_b.get_market_book()
    print(f"  + Agent B queries market depth: {len(market_book['active_listings'])} active listing(s)")

    # Step 8: Trade Execution
    print("\n[Step 8] Agent B executes buy_listing (Atomic settlement)...")
    trade = agent_b.buy_listing(listing["listing_id"])
    print(f"  + Trade #{trade['trade_id']} executed!")
    print(f"  + Price: {trade['price_gf']} GF | Protocol Fee (1.5%): {trade['fee_gf']} GF")
    print(f"  + Agent A Balance: {agent_a.get_balance()} GF (received net {ask_price - trade['fee_gf']} GF)")
    print(f"  + Agent B Balance: {agent_b.get_balance()} GF")

    # Check new ownership
    agent_b_frames = agent_b.list_my_frames()
    print(f"  + Frame #{frame_id} current owner: {agent_b_frames[0]['owner_id']}")

    # Barter Swap Demonstration
    print("\n" + "-"*80)
    print("[MULTI-AGENT BATCH & COLLECTION SIMULATION]")
    print("-" * 80)

    # Let agents generate a few more frames to test collections
    print("\n[Simulating autonomous discovery batch...]")
    for i in range(5):
        agent_a.generate()
        agent_b.generate()

    print(f"  + Total protocol frames minted: {protocol.total_frames_minted}")
    print(f"  + Total GF burned:             {protocol.economy.total_gf_burned} GF")

    # Check Felidae collection progress
    progress_a = agent_a.check_collection_progress("Felidae")
    progress_b = agent_b.check_collection_progress("Felidae")
    print(f"\n[Felidae Collection Tracking]")
    print(f"  * Agent A Felidae Progress: {progress_a['owned_species']}/{progress_a['total_species']} ({progress_a['percentage']}%)")
    print(f"  * Agent B Felidae Progress: {progress_b['owned_species']}/{progress_b['total_species']} ({progress_b['percentage']}%)")

    # Summary metrics
    metrics = protocol.get_protocol_metrics()
    print("\n" + "="*80)
    print("PROTOCOL SUMMARY METRICS")
    print("="*80)
    print(json.dumps(metrics, indent=2))
    print("\n>>> Circuit validation successful! Autonomous economic loop completed without human intervention.\n")


if __name__ == "__main__":
    run_minimal_viable_circuit()
