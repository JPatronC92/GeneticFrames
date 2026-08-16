"""
Arbitrage Agent
Continuously monitors orderbooks to detect price discrepancies between asks and bids,
executing instant risk-free triangular settlements when profitable spreads emerge.
"""
from __future__ import annotations

from typing import Any, Dict, List
from protocol.engine import GeneticFramesProtocol
from .base_agent import AgentActionRecord, AutonomousAgent


class ArbitrageAgent(AutonomousAgent):
    """
    Autonomous agent seeking risk-free or statistical arbitrage opportunities.
    """

    def __init__(
        self,
        agent_id: str,
        protocol: GeneticFramesProtocol = None,
        initial_gf: float = 30.0,
        min_net_profit_gf: float = 0.20,
    ):
        super().__init__(
            agent_id=agent_id,
            strategy_name="Arbitrageur",
            protocol=protocol,
            initial_gf=initial_gf,
        )
        self.min_net_profit_gf = min_net_profit_gf

    def step(self, round_num: int) -> List[AgentActionRecord]:
        actions: List[AgentActionRecord] = []
        market_book = self.sdk.get_market_book()
        current_balance = self.get_balance()

        # Map active bids by frame_id (find highest bid for each frame)
        highest_bids: Dict[int, Dict[str, Any]] = {}
        for b in market_book["active_bids"]:
            fid = b["frame_id"]
            if fid not in highest_bids or b["bid_amount_gf"] > highest_bids[fid]["bid_amount_gf"]:
                highest_bids[fid] = b

        # Scan active listings to see if ask < highest_bid (accounting for 1.5% fee)
        for l in market_book["active_listings"]:
            if l["seller_id"] == self.agent_id:
                continue
            fid = l["frame_id"]
            ask_price = l["price_gf"]

            if fid in highest_bids:
                best_bid = highest_bids[fid]
                if best_bid["bidder_id"] != self.agent_id:
                    bid_amount = best_bid["bid_amount_gf"]
                    net_proceeds = bid_amount * (1 - 0.015)
                    net_profit = net_proceeds - ask_price

                    if net_profit >= self.min_net_profit_gf and current_balance >= ask_price:
                        # 1. Buy listing
                        try:
                            trade_buy = self.sdk.buy_listing(l["listing_id"])
                            # 2. Immediately accept the waiting bid
                            trade_sell = self.sdk.accept_bid(best_bid["bid_id"])
                            actions.append(
                                self.log_action(
                                    round_num,
                                    "arbitrage_executed",
                                    {
                                        "frame_id": fid,
                                        "buy_price": ask_price,
                                        "sell_price": bid_amount,
                                        "net_profit_gf": round(net_profit, 4),
                                    },
                                )
                            )
                            current_balance = self.get_balance()
                        except Exception:
                            pass

        if not actions:
            actions.append(self.log_action(round_num, "hold", {"balance": current_balance, "opportunities_found": 0}))

        return actions
