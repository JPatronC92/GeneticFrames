"""
Market Maker Agent
Provides two-sided market liquidity by maintaining continuous bid/ask spreads,
absorbing inventory from liquidity-seeking agents, and stabilizing price discovery.
"""
from __future__ import annotations

from typing import Any, Dict, List
from protocol.engine import GeneticFramesProtocol
from protocol.species_pool import RarityTier
from .base_agent import AgentActionRecord, AutonomousAgent


class MarketMakerAgent(AutonomousAgent):
    """
    Autonomous agent providing bidirectional liquidity and orderbook depth.
    """

    def __init__(
        self,
        agent_id: str,
        protocol: GeneticFramesProtocol = None,
        initial_gf: float = 60.0,
        target_spread_pct: float = 0.25,  # 25% bid-ask spread
    ):
        super().__init__(
            agent_id=agent_id,
            strategy_name="Market Maker",
            protocol=protocol,
            initial_gf=initial_gf,
        )
        self.target_spread_pct = target_spread_pct

    def step(self, round_num: int) -> List[AgentActionRecord]:
        actions: List[AgentActionRecord] = []
        market_book = self.sdk.get_market_book()
        my_frames = self.get_my_frames()
        current_balance = self.get_balance()

        # Step 1: Ensure active sell listings (Asks) for owned inventory
        for f in my_frames:
            full_frame = self.protocol.inspect_frame(f["frame_id"])
            if not full_frame:
                continue

            is_listed = any(
                l["frame_id"] == f["frame_id"] and l["status"] == "active"
                for l in market_book["active_listings"]
            )
            if not is_listed:
                base_price = 2.0 if full_frame.tier == RarityTier.COMMON else 3.5 if full_frame.tier == RarityTier.UNCOMMON else 7.0
                ask_price = round(base_price * (1 + self.target_spread_pct), 2)
                try:
                    self.sdk.create_ask(f["frame_id"], ask_price)
                    actions.append(
                        self.log_action(
                            round_num,
                            "create_ask",
                            {"frame_id": f["frame_id"], "price_gf": ask_price, "tier": full_frame.tier.value},
                        )
                    )
                except Exception:
                    pass

        # Step 2: Ensure active purchase bids on market frames
        if current_balance >= 5.0:
            for l in market_book["active_listings"]:
                if l["seller_id"] == self.agent_id:
                    continue
                # Place a conservative bid if none exists
                has_my_bid = any(
                    b["frame_id"] == l["frame_id"] and b["bidder_id"] == self.agent_id and b["status"] == "active"
                    for b in market_book["active_bids"]
                )
                if not has_my_bid and current_balance >= 2.0:
                    bid_amount = round(max(1.1, l["price_gf"] * (1 - self.target_spread_pct)), 2)
                    try:
                        self.sdk.place_bid(l["frame_id"], bid_amount)
                        actions.append(
                            self.log_action(
                                round_num,
                                "place_bid",
                                {"frame_id": l["frame_id"], "bid_amount_gf": bid_amount, "target_ask": l["price_gf"]},
                            )
                        )
                        current_balance = self.get_balance()
                    except Exception:
                        pass

        # Step 3: Maintain baseline inventory by generating when cash-rich
        if current_balance >= 25.0 and len(my_frames) < 5:
            try:
                gen_res = self.sdk.generate()
                actions.append(
                    self.log_action(
                        round_num,
                        "generate",
                        {"frame_id": gen_res["frame_id"], "tier": gen_res["tier"], "reason": "Restock inventory"},
                    )
                )
            except Exception:
                pass

        if not actions:
            actions.append(self.log_action(round_num, "hold", {"balance": current_balance, "inventory": len(my_frames)}))

        return actions
