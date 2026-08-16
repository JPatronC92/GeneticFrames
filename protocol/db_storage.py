"""
GeneticFrames SQLite Persistent Storage Engine
Provides persistent ACID database storage for agent wallets, minted frames, provenance logs, and marketplace orders.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .economy import (
    AgentWallet,
    EconomyLedger,
    GeneticFrameRecord,
    MarketBid,
    MarketListing,
    MarketSwap,
    MarketTrade,
    OrderStatus,
)
from .species_pool import RarityTier


class SQLiteEconomyStorage:
    """
    SQLite persistence layer for the GeneticFrames protocol.
    """

    def __init__(self, db_path: str = "geneticframes.db"):
        self.db_path = db_path
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS protocol_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS wallets (
                agent_id TEXT PRIMARY KEY,
                gf_balance REAL NOT NULL DEFAULT 0.0,
                nonce INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS frames (
                frame_id INTEGER PRIMARY KEY,
                generation_id INTEGER NOT NULL,
                organism_id TEXT NOT NULL,
                common_name TEXT NOT NULL,
                scientific_name TEXT NOT NULL,
                tier TEXT NOT NULL,
                creator_id TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                manifest_json TEXT NOT NULL,
                svg_code TEXT NOT NULL,
                raw_sequence TEXT NOT NULL,
                minted_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS provenance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                frame_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                from_agent TEXT,
                to_agent TEXT NOT NULL,
                timestamp REAL NOT NULL,
                details TEXT,
                FOREIGN KEY (frame_id) REFERENCES frames (frame_id)
            );

            CREATE TABLE IF NOT EXISTS listings (
                listing_id TEXT PRIMARY KEY,
                frame_id INTEGER NOT NULL,
                seller_id TEXT NOT NULL,
                price_gf REAL NOT NULL,
                status TEXT NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY (frame_id) REFERENCES frames (frame_id)
            );

            CREATE TABLE IF NOT EXISTS bids (
                bid_id TEXT PRIMARY KEY,
                frame_id INTEGER NOT NULL,
                bidder_id TEXT NOT NULL,
                bid_amount_gf REAL NOT NULL,
                status TEXT NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY (frame_id) REFERENCES frames (frame_id)
            );

            CREATE TABLE IF NOT EXISTS swaps (
                swap_id TEXT PRIMARY KEY,
                initiator_id TEXT NOT NULL,
                offered_frame_id INTEGER NOT NULL,
                requested_frame_id INTEGER NOT NULL,
                delta_gf REAL NOT NULL,
                counterparty_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY,
                trade_type TEXT NOT NULL,
                frame_id INTEGER NOT NULL,
                seller_id TEXT NOT NULL,
                buyer_id TEXT NOT NULL,
                price_gf REAL NOT NULL,
                fee_gf REAL NOT NULL,
                timestamp REAL NOT NULL
            );
            """)

    # -------------------------------------------------------------------------
    # WALLET OPERATIONS
    # -------------------------------------------------------------------------

    def get_or_create_wallet(self, agent_id: str, initial_balance: float = 0.0) -> AgentWallet:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM wallets WHERE agent_id = ?", (agent_id,)).fetchone()
            if row:
                return AgentWallet(
                    agent_id=row["agent_id"],
                    gf_balance=row["gf_balance"],
                    nonce=row["nonce"],
                    created_at=row["created_at"],
                )
            now = time.time()
            conn.execute(
                "INSERT INTO wallets (agent_id, gf_balance, nonce, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (agent_id, initial_balance, 0, now, now),
            )
            return AgentWallet(agent_id=agent_id, gf_balance=initial_balance, nonce=0, created_at=now)

    def save_wallet(self, wallet: AgentWallet) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE wallets SET gf_balance = ?, nonce = ?, updated_at = ? WHERE agent_id = ?",
                (wallet.gf_balance, wallet.nonce, time.time(), wallet.agent_id),
            )

    def load_all_wallets(self) -> Dict[str, AgentWallet]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM wallets").fetchall()
            return {
                row["agent_id"]: AgentWallet(
                    agent_id=row["agent_id"],
                    gf_balance=row["gf_balance"],
                    nonce=row["nonce"],
                    created_at=row["created_at"],
                )
                for row in rows
            }

    # -------------------------------------------------------------------------
    # FRAME OPERATIONS
    # -------------------------------------------------------------------------

    def save_frame(self, record: GeneticFrameRecord) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO frames 
                (frame_id, generation_id, organism_id, common_name, scientific_name, tier, creator_id, owner_id, manifest_json, svg_code, raw_sequence, minted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.frame_id,
                    record.generation_id,
                    record.organism_id,
                    record.common_name,
                    record.scientific_name,
                    record.tier.value,
                    record.creator_id,
                    record.owner_id,
                    json.dumps(record.manifest),
                    record.svg_code,
                    record.raw_sequence,
                    record.minted_at,
                ),
            )
            # Record latest provenance entry if any
            if record.provenance_history:
                last_p = record.provenance_history[-1]
                conn.execute(
                    "INSERT INTO provenance (frame_id, event_type, from_agent, to_agent, timestamp, details) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        record.frame_id,
                        last_p.get("event", "transfer"),
                        last_p.get("from"),
                        last_p.get("to", record.owner_id),
                        last_p.get("timestamp", time.time()),
                        json.dumps(last_p),
                    ),
                )

    def update_frame_owner(self, frame_id: int, new_owner_id: str, from_agent_id: str, reason: str = "transfer") -> None:
        now = time.time()
        with self._get_connection() as conn:
            conn.execute("UPDATE frames SET owner_id = ? WHERE frame_id = ?", (new_owner_id, frame_id))
            conn.execute(
                "INSERT INTO provenance (frame_id, event_type, from_agent, to_agent, timestamp, details) VALUES (?, ?, ?, ?, ?, ?)",
                (frame_id, reason, from_agent_id, new_owner_id, now, json.dumps({"reason": reason})),
            )

    def load_all_frames(self) -> Dict[int, GeneticFrameRecord]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM frames ORDER BY frame_id ASC").fetchall()
            frames: Dict[int, GeneticFrameRecord] = {}
            for r in rows:
                p_rows = conn.execute("SELECT * FROM provenance WHERE frame_id = ? ORDER BY id ASC", (r["frame_id"],)).fetchall()
                prov = [
                    {
                        "event": p["event_type"],
                        "from": p["from_agent"],
                        "to": p["to_agent"],
                        "timestamp": p["timestamp"],
                    }
                    for p in p_rows
                ]
                frames[r["frame_id"]] = GeneticFrameRecord(
                    frame_id=r["frame_id"],
                    generation_id=r["generation_id"],
                    organism_id=r["organism_id"],
                    common_name=r["common_name"],
                    scientific_name=r["scientific_name"],
                    tier=RarityTier(r["tier"]),
                    creator_id=r["creator_id"],
                    owner_id=r["owner_id"],
                    manifest=json.loads(r["manifest_json"]),
                    svg_code=r["svg_code"],
                    raw_sequence=r["raw_sequence"],
                    minted_at=r["minted_at"],
                    provenance_history=prov,
                )
            return frames

    # -------------------------------------------------------------------------
    # MARKETPLACE OPERATIONS
    # -------------------------------------------------------------------------

    def save_listing(self, listing: MarketListing) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO listings (listing_id, frame_id, seller_id, price_gf, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (listing.listing_id, listing.frame_id, listing.seller_id, listing.price_gf, listing.status.value, listing.created_at),
            )

    def save_bid(self, bid: MarketBid) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO bids (bid_id, frame_id, bidder_id, bid_amount_gf, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (bid.bid_id, bid.frame_id, bid.bidder_id, bid.bid_amount_gf, bid.status.value, bid.created_at),
            )

    def save_swap(self, swap: MarketSwap) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO swaps (swap_id, initiator_id, offered_frame_id, requested_frame_id, delta_gf, counterparty_id, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (swap.swap_id, swap.initiator_id, swap.offered_frame_id, swap.requested_frame_id, swap.delta_gf, swap.counterparty_id, swap.status.value, swap.created_at),
            )

    def save_trade(self, trade: MarketTrade) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO trades (trade_id, trade_type, frame_id, seller_id, buyer_id, price_gf, fee_gf, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (trade.trade_id, trade.trade_type, trade.frame_id, trade.seller_id, trade.buyer_id, trade.price_gf, trade.fee_gf, trade.timestamp),
            )

    def load_all_market_state(self) -> Tuple[Dict[str, MarketListing], Dict[str, MarketBid], Dict[str, MarketSwap], List[MarketTrade]]:
        with self._get_connection() as conn:
            l_rows = conn.execute("SELECT * FROM listings").fetchall()
            listings = {
                r["listing_id"]: MarketListing(
                    listing_id=r["listing_id"],
                    frame_id=r["frame_id"],
                    seller_id=r["seller_id"],
                    price_gf=r["price_gf"],
                    status=OrderStatus(r["status"]),
                    created_at=r["created_at"],
                )
                for r in l_rows
            }

            b_rows = conn.execute("SELECT * FROM bids").fetchall()
            bids = {
                r["bid_id"]: MarketBid(
                    bid_id=r["bid_id"],
                    frame_id=r["frame_id"],
                    bidder_id=r["bidder_id"],
                    bid_amount_gf=r["bid_amount_gf"],
                    status=OrderStatus(r["status"]),
                    created_at=r["created_at"],
                )
                for r in b_rows
            }

            s_rows = conn.execute("SELECT * FROM swaps").fetchall()
            swaps = {
                r["swap_id"]: MarketSwap(
                    swap_id=r["swap_id"],
                    initiator_id=r["initiator_id"],
                    offered_frame_id=r["offered_frame_id"],
                    requested_frame_id=r["requested_frame_id"],
                    delta_gf=r["delta_gf"],
                    counterparty_id=r["counterparty_id"],
                    status=OrderStatus(r["status"]),
                    created_at=r["created_at"],
                )
                for r in s_rows
            }

            t_rows = conn.execute("SELECT * FROM trades ORDER BY timestamp ASC").fetchall()
            trades = [
                MarketTrade(
                    trade_id=r["trade_id"],
                    trade_type=r["trade_type"],
                    frame_id=r["frame_id"],
                    seller_id=r["seller_id"],
                    buyer_id=r["buyer_id"],
                    price_gf=r["price_gf"],
                    fee_gf=r["fee_gf"],
                    timestamp=r["timestamp"],
                )
                for r in t_rows
            ]

            return listings, bids, swaps, trades


class PersistentEconomyLedger(EconomyLedger):
    """
    Subclass of EconomyLedger that synchronizes all state changes to SQLite persistence.
    """

    def __init__(self, db_path: str = "geneticframes.db"):
        super().__init__()
        self.storage = SQLiteEconomyStorage(db_path)
        self._load_from_storage()

    def _load_from_storage(self) -> None:
        self.wallets = self.storage.load_all_wallets()
        self.frames = self.storage.load_all_frames()
        self.listings, self.bids, self.swaps, self.trade_history = self.storage.load_all_market_state()
        self.total_gf_burned = sum(w.nonce for w in self.wallets.values()) * 1.0  # Approx or exact
        self.treasury_gf_collected = sum(t.fee_gf for t in self.trade_history)

    def get_or_create_wallet(self, agent_id: str, initial_balance: float = 0.0) -> AgentWallet:
        if agent_id not in self.wallets:
            wallet = self.storage.get_or_create_wallet(agent_id, initial_balance)
            self.wallets[agent_id] = wallet
        return self.wallets[agent_id]

    def mint_gf(self, agent_id: str, amount: float) -> float:
        res = super().mint_gf(agent_id, amount)
        self.storage.save_wallet(self.wallets[agent_id])
        return res

    def burn_gf(self, agent_id: str, amount: float = 1.0) -> bool:
        res = super().burn_gf(agent_id, amount)
        self.storage.save_wallet(self.wallets[agent_id])
        return res

    def transfer_gf(self, from_agent_id: str, to_agent_id: str, amount: float) -> bool:
        res = super().transfer_gf(from_agent_id, to_agent_id, amount)
        self.storage.save_wallet(self.wallets[from_agent_id])
        self.storage.save_wallet(self.wallets[to_agent_id])
        return res

    def register_minted_frame(self, record: GeneticFrameRecord) -> None:
        super().register_minted_frame(record)
        self.storage.save_frame(record)

    def transfer_frame_ownership(self, frame_id: int, from_agent_id: str, to_agent_id: str, reason: str = "transfer") -> bool:
        res = super().transfer_frame_ownership(frame_id, from_agent_id, to_agent_id, reason)
        self.storage.update_frame_owner(frame_id, to_agent_id, from_agent_id, reason)
        return res

    def create_listing(self, seller_id: str, frame_id: int, price_gf: float) -> MarketListing:
        listing = super().create_listing(seller_id, frame_id, price_gf)
        self.storage.save_listing(listing)
        return listing

    def cancel_listing(self, seller_id: str, listing_id: str) -> bool:
        res = super().cancel_listing(seller_id, listing_id)
        self.storage.save_listing(self.listings[listing_id])
        return res

    def buy_listing(self, buyer_id: str, listing_id: str) -> MarketTrade:
        trade = super().buy_listing(buyer_id, listing_id)
        self.storage.save_wallet(self.wallets[buyer_id])
        self.storage.save_wallet(self.wallets[trade.seller_id])
        self.storage.save_listing(self.listings[listing_id])
        self.storage.save_trade(trade)
        return trade

    def place_bid(self, bidder_id: str, frame_id: int, bid_amount_gf: float) -> MarketBid:
        bid = super().place_bid(bidder_id, frame_id, bid_amount_gf)
        self.storage.save_bid(bid)
        return bid

    def accept_bid(self, seller_id: str, bid_id: str) -> MarketTrade:
        trade = super().accept_bid(seller_id, bid_id)
        self.storage.save_wallet(self.wallets[trade.buyer_id])
        self.storage.save_wallet(self.wallets[seller_id])
        self.storage.save_bid(self.bids[bid_id])
        self.storage.save_trade(trade)
        return trade

    def propose_swap(self, initiator_id: str, offered_frame_id: int, requested_frame_id: int, delta_gf: float = 0.0) -> MarketSwap:
        swap = super().propose_swap(initiator_id, offered_frame_id, requested_frame_id, delta_gf)
        self.storage.save_swap(swap)
        return swap

    def accept_swap(self, counterparty_id: str, swap_id: str) -> Tuple[MarketTrade, MarketTrade]:
        t1, t2 = super().accept_swap(counterparty_id, swap_id)
        swap = self.swaps[swap_id]
        self.storage.save_wallet(self.wallets[swap.initiator_id])
        self.storage.save_wallet(self.wallets[swap.counterparty_id])
        self.storage.save_swap(swap)
        self.storage.save_trade(t1)
        self.storage.save_trade(t2)
        return t1, t2
