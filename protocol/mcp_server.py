"""
GeneticFrames Model Context Protocol (MCP) Server
Allows autonomous AI models, LLMs, and agent swarms to interact with the GeneticFrames economy.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP

from protocol.db_storage import PersistentEconomyLedger
from protocol.engine import GeneticFramesProtocol
from protocol.species_pool import SPECIES_POOL_V1, RarityTier


# Initialize FastMCP Server
mcp = FastMCP(
    "GeneticFrames Protocol",
    instructions="GeneticFrames is an autonomous biological digital asset protocol. Agents can spend 1 GF to mint unique, verifiable GeneticFrames, inspect cryptographic proofs, trade on the P2P marketplace, and build taxonomic collections."
)

# Initialize persistent ledger and protocol engine
_ledger = PersistentEconomyLedger("geneticframes.db")
_protocol = GeneticFramesProtocol(economy_ledger=_ledger)


@mcp.tool()
def get_protocol_status() -> str:
    """Returns global protocol statistics: active epoch, total frames minted, GF burned, and marketplace depth."""
    metrics = _protocol.get_protocol_metrics()
    return json.dumps(metrics, indent=2)


@mcp.tool()
def get_species_pool(tier: Optional[str] = None) -> str:
    """Lists eligible biological species in SpeciesPool v1, optionally filtered by tier (Common, Uncommon, Rare, Epic, Genesis)."""
    catalog = SPECIES_POOL_V1.catalog
    if tier:
        try:
            t_enum = RarityTier(tier.capitalize())
            catalog = [s for s in catalog if s.tier == t_enum]
        except ValueError:
            return json.dumps({"error": f"Invalid rarity tier: {tier}"})
    return json.dumps({
        "pool_version": SPECIES_POOL_V1.VERSION,
        "pool_sha256": SPECIES_POOL_V1.catalog_sha256,
        "species_count": len(catalog),
        "species": [s.to_dict() for s in catalog],
    }, indent=2)


@mcp.tool()
def get_agent_balance(agent_id: str) -> str:
    """Gets the current GF (fungible token) balance and transaction nonce for an agent wallet."""
    wallet = _protocol.economy.get_or_create_wallet(agent_id)
    return json.dumps(wallet.to_dict(), indent=2)


@mcp.tool()
def faucet_gf(agent_id: str, amount: float = 10.0) -> str:
    """Deposits/mints test GF tokens to an agent wallet."""
    new_bal = _protocol.economy.mint_gf(agent_id, amount)
    return json.dumps({"agent_id": agent_id, "deposited": amount, "new_balance_gf": new_bal}, indent=2)


@mcp.tool()
def generate_frame(agent_id: str, client_entropy: Optional[str] = None) -> str:
    """
    Executes the canonical GENERATE event for an agent:
    Consumes and burns 1.0 GF, evaluates verifiable randomness, draws an organism from SpeciesPool v1,
    extracts biological traits, renders GFDP v2 deterministic SVG, and returns the minted GeneticFrame record.
    """
    try:
        record = _protocol.generate(agent_id=agent_id, client_entropy=client_entropy)
        return json.dumps({
            "success": True,
            "frame_id": record.frame_id,
            "generation_id": record.generation_id,
            "organism_id": record.organism_id,
            "common_name": record.common_name,
            "scientific_name": record.scientific_name,
            "tier": record.tier.value,
            "creator_id": record.creator_id,
            "owner_id": record.owner_id,
            "manifest_sha256": record.manifest.get("manifest_sha256"),
            "manifest": record.manifest,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def inspect_frame(frame_id: int) -> str:
    """Inspects detailed cryptographic metadata, biological traits, and ownership history of a GeneticFrame."""
    frame = _protocol.inspect_frame(frame_id)
    if not frame:
        return json.dumps({"error": f"Frame #{frame_id} not found"})
    return json.dumps({
        "record": frame.to_dict(),
        "manifest": frame.manifest,
        "provenance": frame.provenance_history,
    }, indent=2)


@mcp.tool()
def verify_frame(frame_id: int) -> str:
    """
    Runs an independent 5-point cryptographic verification on a GeneticFrame:
    checks manifest hash, biological DNA sequence integrity, fragment offset/checksum,
    GFDP v2 SVG deterministic reproduction, and randomness proof consistency.
    """
    result = _protocol.verify_frame(frame_id)
    return json.dumps(result.to_dict(), indent=2)


@mcp.tool()
def list_agent_frames(agent_id: str) -> str:
    """Lists all GeneticFrames currently owned by an agent."""
    frames = _protocol.economy.get_agent_frames(agent_id)
    return json.dumps({
        "agent_id": agent_id,
        "count": len(frames),
        "frames": [f.to_dict() for f in frames],
    }, indent=2)


@mcp.tool()
def list_market_orders() -> str:
    """Lists all active fixed-price asks (listings), bids, and barter swaps on the P2P marketplace."""
    listings = [l.to_dict() for l in _protocol.economy.listings.values() if l.status.value == "active"]
    bids = [b.to_dict() for b in _protocol.economy.bids.values() if b.status.value == "active"]
    swaps = [s.to_dict() for s in _protocol.economy.swaps.values() if s.status.value == "active"]
    return json.dumps({
        "active_listings": listings,
        "active_bids": bids,
        "active_swaps": swaps,
    }, indent=2)


@mcp.tool()
def create_market_listing(seller_id: str, frame_id: int, price_gf: float) -> str:
    """Lists a GeneticFrame owned by the seller for sale on the marketplace at a fixed asking price in GF."""
    try:
        listing = _protocol.economy.create_listing(seller_id=seller_id, frame_id=frame_id, price_gf=price_gf)
        return json.dumps(listing.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def buy_market_listing(buyer_id: str, listing_id: str) -> str:
    """Purchases a listed GeneticFrame: transfers GF to seller (minus 1.5% protocol fee) and transfers ownership to buyer."""
    try:
        trade = _protocol.economy.buy_listing(buyer_id=buyer_id, listing_id=listing_id)
        return json.dumps(trade.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def place_market_bid(bidder_id: str, frame_id: int, bid_amount_gf: float) -> str:
    """Submits a purchase bid in GF on any GeneticFrame in existence."""
    try:
        bid = _protocol.economy.place_bid(bidder_id=bidder_id, frame_id=frame_id, bid_amount_gf=bid_amount_gf)
        return json.dumps(bid.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def accept_market_bid(seller_id: str, bid_id: str) -> str:
    """Accepts an active purchase bid on a frame owned by the seller, executing an atomic trade settlement."""
    try:
        trade = _protocol.economy.accept_bid(seller_id=seller_id, bid_id=bid_id)
        return json.dumps(trade.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def propose_market_swap(initiator_id: str, offered_frame_id: int, requested_frame_id: int, delta_gf: float = 0.0) -> str:
    """Proposes a direct barter exchange of frames with another agent (+ optional delta GF sweetener)."""
    try:
        swap = _protocol.economy.propose_swap(
            initiator_id=initiator_id,
            offered_frame_id=offered_frame_id,
            requested_frame_id=requested_frame_id,
            delta_gf=delta_gf,
        )
        return json.dumps(swap.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def accept_market_swap(counterparty_id: str, swap_id: str) -> str:
    """Accepts a proposed barter swap, atomically exchanging frame ownership between both agents."""
    try:
        t1, t2 = _protocol.economy.accept_swap(counterparty_id=counterparty_id, swap_id=swap_id)
        return json.dumps({"trade_1": t1.to_dict(), "trade_2": t2.to_dict()}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def check_collection_progress(agent_id: str, family: str) -> str:
    """Evaluates an agent's completion percentage and missing species for a taxonomic family (e.g. Felidae, Cetacea)."""
    result = _protocol.economy.check_collection_completion(agent_id, family)
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run()
