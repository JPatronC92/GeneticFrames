"""
GeneticFrames Economic Layer & Marketplace Engine
Manages agent wallets, GF supply, asset provenance, orderbooks, and atomic trades.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .species_pool import SPECIES_POOL_V1, RarityTier, SpeciesEntry


class OrderStatus(str, Enum):
    ACTIVE = "active"
    FILLED = "filled"
    CANCELLED = "cancelled"


@dataclass
class AgentWallet:
    agent_id: str
    gf_balance: float = 0.0
    nonce: int = 0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "gf_balance": round(self.gf_balance, 4),
            "nonce": self.nonce,
            "created_at": self.created_at,
        }


@dataclass
class GeneticFrameRecord:
    frame_id: int
    generation_id: int
    organism_id: str
    common_name: str
    scientific_name: str
    tier: RarityTier
    creator_id: str
    owner_id: str
    manifest: Dict[str, Any]
    svg_code: str
    raw_sequence: str
    minted_at: float = field(default_factory=time.time)
    provenance_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "generation_id": self.generation_id,
            "organism_id": self.organism_id,
            "common_name": self.common_name,
            "scientific_name": self.scientific_name,
            "tier": self.tier.value,
            "creator_id": self.creator_id,
            "owner_id": self.owner_id,
            "minted_at": self.minted_at,
            "manifest_sha256": self.manifest.get("manifest_sha256", ""),
            "provenance_count": len(self.provenance_history),
        }


@dataclass
class MarketListing:
    listing_id: str
    frame_id: int
    seller_id: str
    price_gf: float
    status: OrderStatus = OrderStatus.ACTIVE
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "listing_id": self.listing_id,
            "frame_id": self.frame_id,
            "seller_id": self.seller_id,
            "price_gf": round(self.price_gf, 4),
            "status": self.status.value,
            "created_at": self.created_at,
        }


@dataclass
class MarketBid:
    bid_id: str
    frame_id: int
    bidder_id: str
    bid_amount_gf: float
    status: OrderStatus = OrderStatus.ACTIVE
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bid_id": self.bid_id,
            "frame_id": self.frame_id,
            "bidder_id": self.bidder_id,
            "bid_amount_gf": round(self.bid_amount_gf, 4),
            "status": self.status.value,
            "created_at": self.created_at,
        }


@dataclass
class MarketSwap:
    swap_id: str
    initiator_id: str
    offered_frame_id: int
    requested_frame_id: int
    delta_gf: float  # Additional GF offered by initiator (can be positive or negative)
    counterparty_id: str
    status: OrderStatus = OrderStatus.ACTIVE
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "swap_id": self.swap_id,
            "initiator_id": self.initiator_id,
            "offered_frame_id": self.offered_frame_id,
            "requested_frame_id": self.requested_frame_id,
            "delta_gf": round(self.delta_gf, 4),
            "counterparty_id": self.counterparty_id,
            "status": self.status.value,
            "created_at": self.created_at,
        }


@dataclass
class MarketTrade:
    trade_id: str
    trade_type: str  # "buy_listing", "accept_bid", "swap"
    frame_id: int
    seller_id: str
    buyer_id: str
    price_gf: float
    fee_gf: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "trade_type": self.trade_type,
            "frame_id": self.frame_id,
            "seller_id": self.seller_id,
            "buyer_id": self.buyer_id,
            "price_gf": round(self.price_gf, 4),
            "fee_gf": round(self.fee_gf, 4),
            "timestamp": self.timestamp,
        }


class EconomyLedger:
    """
    State engine for the agent economy.
    Handles wallets, asset balances, protocol burns, listings, bids, swaps, and trades.
    """
    PROTOCOL_MARKET_FEE_RATE = 0.015  # 1.5% marketplace fee

    def __init__(self):
        self.wallets: Dict[str, AgentWallet] = {}
        self.frames: Dict[int, GeneticFrameRecord] = {}
        self.listings: Dict[str, MarketListing] = {}
        self.bids: Dict[str, MarketBid] = {}
        self.swaps: Dict[str, MarketSwap] = {}
        self.trade_history: List[MarketTrade] = []
        self.total_gf_burned: float = 0.0
        self.treasury_gf_collected: float = 0.0

    # -------------------------------------------------------------------------
    # WALLET & GF OPERATIONS
    # -------------------------------------------------------------------------

    def get_or_create_wallet(self, agent_id: str, initial_balance: float = 0.0) -> AgentWallet:
        if agent_id not in self.wallets:
            self.wallets[agent_id] = AgentWallet(agent_id=agent_id, gf_balance=initial_balance)
        return self.wallets[agent_id]

    def get_balance(self, agent_id: str) -> float:
        wallet = self.wallets.get(agent_id)
        return wallet.gf_balance if wallet else 0.0

    def mint_gf(self, agent_id: str, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Mint amount must be positive")
        wallet = self.get_or_create_wallet(agent_id)
        wallet.gf_balance += amount
        return wallet.gf_balance

    def burn_gf(self, agent_id: str, amount: float = 1.0) -> bool:
        wallet = self.get_or_create_wallet(agent_id)
        if wallet.gf_balance < amount:
            raise ValueError(f"Insufficient GF balance: has {wallet.gf_balance}, requires {amount}")
        wallet.gf_balance -= amount
        wallet.nonce += 1
        self.total_gf_burned += amount
        return True

    def transfer_gf(self, from_agent_id: str, to_agent_id: str, amount: float) -> bool:
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        from_wallet = self.get_or_create_wallet(from_agent_id)
        if from_wallet.gf_balance < amount:
            raise ValueError(f"Insufficient GF: sender has {from_wallet.gf_balance}, needs {amount}")
        to_wallet = self.get_or_create_wallet(to_agent_id)

        from_wallet.gf_balance -= amount
        from_wallet.nonce += 1
        to_wallet.gf_balance += amount
        return True

    # -------------------------------------------------------------------------
    # GENETIC FRAME ASSET MANAGEMENT
    # -------------------------------------------------------------------------

    def register_minted_frame(self, record: GeneticFrameRecord) -> None:
        record.provenance_history.append({
            "event": "mint",
            "from": None,
            "to": record.creator_id,
            "timestamp": record.minted_at,
            "generation_id": record.generation_id,
        })
        self.frames[record.frame_id] = record

    def get_frame(self, frame_id: int) -> Optional[GeneticFrameRecord]:
        return self.frames.get(frame_id)

    def get_agent_frames(self, agent_id: str) -> List[GeneticFrameRecord]:
        return [f for f in self.frames.values() if f.owner_id == agent_id]

    def transfer_frame_ownership(self, frame_id: int, from_agent_id: str, to_agent_id: str, reason: str = "transfer") -> bool:
        frame = self.frames.get(frame_id)
        if not frame:
            raise ValueError(f"Frame #{frame_id} does not exist")
        if frame.owner_id != from_agent_id:
            raise ValueError(f"Agent {from_agent_id} does not own Frame #{frame_id}")

        frame.owner_id = to_agent_id
        frame.provenance_history.append({
            "event": reason,
            "from": from_agent_id,
            "to": to_agent_id,
            "timestamp": time.time(),
        })
        # Cancel any active listings for this frame
        for listing in self.listings.values():
            if listing.frame_id == frame_id and listing.status == OrderStatus.ACTIVE:
                listing.status = OrderStatus.CANCELLED
        return True

    # -------------------------------------------------------------------------
    # MARKETPLACE PRIMITIVES
    # -------------------------------------------------------------------------

    def create_listing(self, seller_id: str, frame_id: int, price_gf: float) -> MarketListing:
        if price_gf <= 0:
            raise ValueError("Listing price must be positive")
        frame = self.frames.get(frame_id)
        if not frame or frame.owner_id != seller_id:
            raise ValueError(f"Agent {seller_id} does not own Frame #{frame_id}")

        # Cancel prior active listings for same frame
        for l in self.listings.values():
            if l.frame_id == frame_id and l.status == OrderStatus.ACTIVE:
                l.status = OrderStatus.CANCELLED

        listing = MarketListing(
            listing_id=f"list_{uuid.uuid4().hex[:12]}",
            frame_id=frame_id,
            seller_id=seller_id,
            price_gf=price_gf,
        )
        self.listings[listing.listing_id] = listing
        return listing

    def cancel_listing(self, seller_id: str, listing_id: str) -> bool:
        listing = self.listings.get(listing_id)
        if not listing or listing.seller_id != seller_id:
            raise ValueError("Listing not found or caller is not seller")
        if listing.status != OrderStatus.ACTIVE:
            raise ValueError(f"Listing is not active (current: {listing.status})")
        listing.status = OrderStatus.CANCELLED
        return True

    def buy_listing(self, buyer_id: str, listing_id: str) -> MarketTrade:
        listing = self.listings.get(listing_id)
        if not listing or listing.status != OrderStatus.ACTIVE:
            raise ValueError("Listing is no longer active")
        if listing.seller_id == buyer_id:
            raise ValueError("Seller cannot buy their own listing")

        buyer_wallet = self.get_or_create_wallet(buyer_id)
        if buyer_wallet.gf_balance < listing.price_gf:
            raise ValueError(f"Buyer has insufficient GF: balance {buyer_wallet.gf_balance} < {listing.price_gf}")

        fee_gf = listing.price_gf * self.PROTOCOL_MARKET_FEE_RATE
        net_seller_gf = listing.price_gf - fee_gf

        # Settle GF transfer
        buyer_wallet.gf_balance -= listing.price_gf
        buyer_wallet.nonce += 1
        seller_wallet = self.get_or_create_wallet(listing.seller_id)
        seller_wallet.gf_balance += net_seller_gf
        self.treasury_gf_collected += fee_gf

        # Transfer asset
        self.transfer_frame_ownership(listing.frame_id, listing.seller_id, buyer_id, reason="market_buy")
        listing.status = OrderStatus.FILLED

        # Record trade
        trade = MarketTrade(
            trade_id=f"trade_{uuid.uuid4().hex[:12]}",
            trade_type="buy_listing",
            frame_id=listing.frame_id,
            seller_id=listing.seller_id,
            buyer_id=buyer_id,
            price_gf=listing.price_gf,
            fee_gf=fee_gf,
        )
        self.trade_history.append(trade)
        return trade

    def place_bid(self, bidder_id: str, frame_id: int, bid_amount_gf: float) -> MarketBid:
        if bid_amount_gf <= 0:
            raise ValueError("Bid amount must be positive")
        frame = self.frames.get(frame_id)
        if not frame:
            raise ValueError(f"Frame #{frame_id} does not exist")
        if frame.owner_id == bidder_id:
            raise ValueError("Owner cannot bid on their own frame")

        bidder_wallet = self.get_or_create_wallet(bidder_id)
        if bidder_wallet.gf_balance < bid_amount_gf:
            raise ValueError(f"Bidder has insufficient GF: {bidder_wallet.gf_balance} < {bid_amount_gf}")

        bid = MarketBid(
            bid_id=f"bid_{uuid.uuid4().hex[:12]}",
            frame_id=frame_id,
            bidder_id=bidder_id,
            bid_amount_gf=bid_amount_gf,
        )
        self.bids[bid.bid_id] = bid
        return bid

    def accept_bid(self, seller_id: str, bid_id: str) -> MarketTrade:
        bid = self.bids.get(bid_id)
        if not bid or bid.status != OrderStatus.ACTIVE:
            raise ValueError("Bid is no longer active")
        frame = self.frames.get(bid.frame_id)
        if not frame or frame.owner_id != seller_id:
            raise ValueError(f"Seller {seller_id} does not own Frame #{bid.frame_id}")

        bidder_wallet = self.get_or_create_wallet(bid.bidder_id)
        if bidder_wallet.gf_balance < bid.bid_amount_gf:
            bid.status = OrderStatus.CANCELLED
            raise ValueError("Bidder no longer has sufficient funds")

        fee_gf = bid.bid_amount_gf * self.PROTOCOL_MARKET_FEE_RATE
        net_seller_gf = bid.bid_amount_gf - fee_gf

        bidder_wallet.gf_balance -= bid.bid_amount_gf
        bidder_wallet.nonce += 1
        seller_wallet = self.get_or_create_wallet(seller_id)
        seller_wallet.gf_balance += net_seller_gf
        self.treasury_gf_collected += fee_gf

        self.transfer_frame_ownership(bid.frame_id, seller_id, bid.bidder_id, reason="bid_accepted")
        bid.status = OrderStatus.FILLED

        trade = MarketTrade(
            trade_id=f"trade_{uuid.uuid4().hex[:12]}",
            trade_type="accept_bid",
            frame_id=bid.frame_id,
            seller_id=seller_id,
            buyer_id=bid.bidder_id,
            price_gf=bid.bid_amount_gf,
            fee_gf=fee_gf,
        )
        self.trade_history.append(trade)
        return trade

    def propose_swap(
        self,
        initiator_id: str,
        offered_frame_id: int,
        requested_frame_id: int,
        delta_gf: float = 0.0
    ) -> MarketSwap:
        offered_frame = self.frames.get(offered_frame_id)
        if not offered_frame or offered_frame.owner_id != initiator_id:
            raise ValueError("Initiator does not own the offered frame")

        requested_frame = self.frames.get(requested_frame_id)
        if not requested_frame:
            raise ValueError("Requested frame does not exist")
        if requested_frame.owner_id == initiator_id:
            raise ValueError("Cannot swap with self")

        if delta_gf > 0:
            init_wallet = self.get_or_create_wallet(initiator_id)
            if init_wallet.gf_balance < delta_gf:
                raise ValueError("Initiator has insufficient GF for delta sweetener")

        swap = MarketSwap(
            swap_id=f"swap_{uuid.uuid4().hex[:12]}",
            initiator_id=initiator_id,
            offered_frame_id=offered_frame_id,
            requested_frame_id=requested_frame_id,
            delta_gf=delta_gf,
            counterparty_id=requested_frame.owner_id,
        )
        self.swaps[swap.swap_id] = swap
        return swap

    def accept_swap(self, counterparty_id: str, swap_id: str) -> Tuple[MarketTrade, MarketTrade]:
        swap = self.swaps.get(swap_id)
        if not swap or swap.status != OrderStatus.ACTIVE:
            raise ValueError("Swap is no longer active")
        if swap.counterparty_id != counterparty_id:
            raise ValueError("Counterparty mismatch")

        offered = self.frames.get(swap.offered_frame_id)
        requested = self.frames.get(swap.requested_frame_id)
        if not offered or offered.owner_id != swap.initiator_id:
            swap.status = OrderStatus.CANCELLED
            raise ValueError("Initiator no longer owns the offered frame")
        if not requested or requested.owner_id != counterparty_id:
            raise ValueError("Counterparty no longer owns the requested frame")

        # Handle delta GF
        if swap.delta_gf > 0:
            self.transfer_gf(swap.initiator_id, counterparty_id, swap.delta_gf)
        elif swap.delta_gf < 0:
            self.transfer_gf(counterparty_id, swap.initiator_id, abs(swap.delta_gf))

        # Atomic frame exchange
        self.transfer_frame_ownership(swap.offered_frame_id, swap.initiator_id, counterparty_id, reason="swap")
        self.transfer_frame_ownership(swap.requested_frame_id, counterparty_id, swap.initiator_id, reason="swap")
        swap.status = OrderStatus.FILLED

        trade_a = MarketTrade(
            trade_id=f"trade_{uuid.uuid4().hex[:12]}",
            trade_type="swap_leg_1",
            frame_id=swap.offered_frame_id,
            seller_id=swap.initiator_id,
            buyer_id=counterparty_id,
            price_gf=0.0,
            fee_gf=0.0,
        )
        trade_b = MarketTrade(
            trade_id=f"trade_{uuid.uuid4().hex[:12]}",
            trade_type="swap_leg_2",
            frame_id=swap.requested_frame_id,
            seller_id=counterparty_id,
            buyer_id=swap.initiator_id,
            price_gf=0.0,
            fee_gf=0.0,
        )
        self.trade_history.extend([trade_a, trade_b])
        return trade_a, trade_b

    # -------------------------------------------------------------------------
    # COLLECTION COMPLETION ANALYSIS
    # -------------------------------------------------------------------------

    def check_collection_completion(self, agent_id: str, family: str) -> Dict[str, Any]:
        """Calculates completion progress for a taxonomic family (e.g. Felidae)."""
        target_species = SPECIES_POOL_V1.get_family_species(family)
        if not target_species:
            return {"family": family, "total_species": 0, "owned_species": 0, "percentage": 0.0, "missing": []}

        agent_frames = self.get_agent_frames(agent_id)
        owned_org_ids = {f.organism_id for f in agent_frames}

        owned_in_family = [s for s in target_species if s.organism_id in owned_org_ids]
        missing_in_family = [s for s in target_species if s.organism_id not in owned_org_ids]

        percentage = round((len(owned_in_family) / len(target_species)) * 100.0, 1)
        return {
            "family": family,
            "total_species": len(target_species),
            "owned_species": len(owned_in_family),
            "is_complete": len(owned_in_family) == len(target_species),
            "percentage": percentage,
            "owned": [s.scientific_name for s in owned_in_family],
            "missing": [s.scientific_name for s in missing_in_family],
        }
