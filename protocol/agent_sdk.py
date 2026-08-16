"""
GeneticFrames Agent SDK
High-level programmatic client for AI agents, LLMs, trading bots, and autonomous collectors.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from .engine import GeneticFramesProtocol
from .economy import OrderStatus


class GeneticFramesAgentSDK:
    """
    Agent client interface for interacting with the GeneticFrames protocol.
    """

    def __init__(self, protocol: GeneticFramesProtocol, agent_id: str):
        self.protocol = protocol
        self.agent_id = agent_id
        # Ensure wallet exists
        self.protocol.economy.get_or_create_wallet(agent_id)

    def get_balance(self) -> float:
        """Returns current GF balance."""
        return self.protocol.economy.get_balance(self.agent_id)

    def deposit_gf(self, amount: float) -> float:
        """Faucets/mints GF to this agent's wallet (e.g. for testing / onboarding)."""
        return self.protocol.economy.mint_gf(self.agent_id, amount)

    def generate(self, client_entropy: str | None = None) -> Dict[str, Any]:
        """
        Executes a canonical GENERATE event: spends 1 GF, draws verifiable randomness,
        mints and returns the resulting GeneticFrame with manifest.
        """
        record = self.protocol.generate(agent_id=self.agent_id, client_entropy=client_entropy)
        return {
            "success": True,
            "frame_id": record.frame_id,
            "generation_id": record.generation_id,
            "organism_id": record.organism_id,
            "common_name": record.common_name,
            "scientific_name": record.scientific_name,
            "tier": record.tier.value,
            "manifest": record.manifest,
        }

    def list_my_frames(self) -> List[Dict[str, Any]]:
        """Returns all GeneticFrames owned by this agent."""
        frames = self.protocol.economy.get_agent_frames(self.agent_id)
        return [f.to_dict() for f in frames]

    def inspect_frame(self, frame_id: int) -> Optional[Dict[str, Any]]:
        """Inspects full details and manifest of any frame."""
        frame = self.protocol.inspect_frame(frame_id)
        if not frame:
            return None
        return {
            "record": frame.to_dict(),
            "manifest": frame.manifest,
            "provenance": frame.provenance_history,
        }

    def verify_frame(self, frame_id: int) -> Dict[str, Any]:
        """Runs complete cryptographic audit on a frame."""
        result = self.protocol.verify_frame(frame_id)
        return result.to_dict()

    def create_ask(self, frame_id: int, price_gf: float) -> Dict[str, Any]:
        """Lists a frame owned by this agent for sale at fixed price."""
        listing = self.protocol.economy.create_listing(self.agent_id, frame_id, price_gf)
        return listing.to_dict()

    def cancel_ask(self, listing_id: str) -> bool:
        """Cancels an active listing."""
        return self.protocol.economy.cancel_listing(self.agent_id, listing_id)

    def buy_listing(self, listing_id: str) -> Dict[str, Any]:
        """Buys a frame from the marketplace."""
        trade = self.protocol.economy.buy_listing(self.agent_id, listing_id)
        return trade.to_dict()

    def place_bid(self, frame_id: int, bid_amount_gf: float) -> Dict[str, Any]:
        """Places a purchase bid on any frame."""
        bid = self.protocol.economy.place_bid(self.agent_id, frame_id, bid_amount_gf)
        return bid.to_dict()

    def accept_bid(self, bid_id: str) -> Dict[str, Any]:
        """Accepts a bid placed on a frame owned by this agent."""
        trade = self.protocol.economy.accept_bid(self.agent_id, bid_id)
        return trade.to_dict()

    def propose_swap(self, offered_frame_id: int, requested_frame_id: int, delta_gf: float = 0.0) -> Dict[str, Any]:
        """Proposes a barter swap with another frame owner."""
        swap = self.protocol.economy.propose_swap(
            initiator_id=self.agent_id,
            offered_frame_id=offered_frame_id,
            requested_frame_id=requested_frame_id,
            delta_gf=delta_gf,
        )
        return swap.to_dict()

    def accept_swap(self, swap_id: str) -> List[Dict[str, Any]]:
        """Accepts an incoming swap proposition."""
        t1, t2 = self.protocol.economy.accept_swap(self.agent_id, swap_id)
        return [t1.to_dict(), t2.to_dict()]

    def check_collection_progress(self, family: str) -> Dict[str, Any]:
        """Calculates completion metrics for a biological family collection."""
        return self.protocol.economy.check_collection_completion(self.agent_id, family)

    def get_market_book(self) -> Dict[str, Any]:
        """Returns all active asks, bids, and recent trades."""
        active_listings = [l.to_dict() for l in self.protocol.economy.listings.values() if l.status == OrderStatus.ACTIVE]
        active_bids = [b.to_dict() for b in self.protocol.economy.bids.values() if b.status == OrderStatus.ACTIVE]
        recent_trades = [t.to_dict() for t in self.protocol.economy.trade_history[-10:]]
        return {
            "active_listings": active_listings,
            "active_bids": active_bids,
            "recent_trades": recent_trades,
        }
