"""
Rarity Hunter Agent
Optimizes portfolio expected value by hunting high-tier protocol assets (Epic and Genesis),
sniping mispriced rare listings, and cycling common assets for continuous generation liquidity.
"""
from __future__ import annotations

from typing import Any, Dict, List
from protocol.engine import GeneticFramesProtocol
from protocol.species_pool import RarityTier
from .base_agent import AgentActionRecord, AutonomousAgent


# Target fair market valuations by tier
TIER_VALUATIONS: Dict[str, float] = {
    RarityTier.GENESIS.value: 35.0,
    RarityTier.EPIC.value: 12.0,
    RarityTier.RARE.value: 5.5,
    RarityTier.UNCOMMON.value: 2.5,
    RarityTier.COMMON.value: 1.5,
}


class RarityHunterAgent(AutonomousAgent):
    """
    Autonomous agent focused on asset rarity optimization and valuation snipes.
    """

    def __init__(
        self,
        agent_id: str,
        protocol: GeneticFramesProtocol = None,
        initial_gf: float = 30.0,
        snipe_discount_threshold: float = 0.70,  # Snipe if price <= 70% of fair valuation
    ):
        super().__init__(
            agent_id=agent_id,
            strategy_name="Rarity Hunter",
            protocol=protocol,
            initial_gf=initial_gf,
        )
        self.snipe_discount_threshold = snipe_discount_threshold

    def step(self, round_num: int) -> List[AgentActionRecord]:
        actions: List[AgentActionRecord] = []
        current_balance = self.get_balance()
        market_book = self.sdk.get_market_book()

        # Step 1: Scan market for undervalued Rare, Epic, or Genesis frames
        for listing in market_book["active_listings"]:
            if listing["seller_id"] == self.agent_id:
                continue
            frame_info = self.protocol.inspect_frame(listing["frame_id"])
            if not frame_info:
                continue

            tier_val = frame_info.tier.value
            fair_value = TIER_VALUATIONS.get(tier_val, 1.5)
            max_snipe_price = fair_value * self.snipe_discount_threshold

            # If it's a high tier at bargain price, buy immediately
            if tier_val in [RarityTier.RARE.value, RarityTier.EPIC.value, RarityTier.GENESIS.value]:
                if listing["price_gf"] <= max_snipe_price and current_balance >= listing["price_gf"]:
                    try:
                        trade = self.sdk.buy_listing(listing["listing_id"])
                        actions.append(
                            self.log_action(
                                round_num,
                                "buy_listing",
                                {
                                    "listing_id": listing["listing_id"],
                                    "frame_id": listing["frame_id"],
                                    "tier": tier_val,
                                    "price_gf": trade["price_gf"],
                                    "fair_value_est": fair_value,
                                    "discount_pct": round((1 - listing["price_gf"] / fair_value) * 100, 1),
                                },
                            )
                        )
                        current_balance = self.get_balance()
                    except Exception:
                        pass

        # Step 2: Liquidate Common/Uncommon assets to keep generation liquidity active
        my_frames = self.get_my_frames()
        for f in my_frames:
            full_frame = self.protocol.inspect_frame(f["frame_id"])
            if not full_frame:
                continue

            # Keep Epic & Genesis; sell Common & Uncommon
            if full_frame.tier in [RarityTier.COMMON, RarityTier.UNCOMMON]:
                is_listed = any(
                    l["frame_id"] == f["frame_id"] and l["status"] == "active"
                    for l in market_book["active_listings"]
                )
                if not is_listed:
                    ask_price = 1.8 if full_frame.tier == RarityTier.COMMON else 2.8
                    try:
                        self.sdk.create_ask(f["frame_id"], price_gf=ask_price)
                        actions.append(
                            self.log_action(
                                round_num,
                                "create_ask",
                                {
                                    "frame_id": f["frame_id"],
                                    "tier": full_frame.tier.value,
                                    "price_gf": ask_price,
                                    "reason": "Recycle common/uncommon for generation liquidity",
                                },
                            )
                        )
                    except Exception:
                        pass

        # Step 3: Trigger generation whenever funds allow
        if current_balance >= 1.0:
            try:
                gen_res = self.sdk.generate()
                actions.append(
                    self.log_action(
                        round_num,
                        "generate",
                        {
                            "frame_id": gen_res["frame_id"],
                            "species": gen_res["scientific_name"],
                            "tier": gen_res["tier"],
                            "is_high_tier": gen_res["tier"] in ["Rare", "Epic", "Genesis"],
                        },
                    )
                )
            except Exception:
                pass

        if not actions:
            actions.append(self.log_action(round_num, "hold", {"balance": current_balance}))

        return actions
