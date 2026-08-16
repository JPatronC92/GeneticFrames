"""
GeneticFrames Agent Swarm Orchestrator
Coordinates concurrent multi-round execution of autonomous agent swarms, collecting real-time telemetry.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from protocol.db_storage import PersistentEconomyLedger
from protocol.engine import GeneticFramesProtocol
from protocol.species_pool import RarityTier
from .arbitrage_agent import ArbitrageAgent
from .base_agent import AgentActionRecord, AutonomousAgent
from .collector_agent import CollectorAgent
from .market_maker_agent import MarketMakerAgent
from .rarity_hunter_agent import RarityHunterAgent


@dataclass
class SwarmMetrics:
    total_rounds: int
    total_actions: int
    total_generations: int
    total_trades: int
    total_volume_gf: float
    total_fees_collected_gf: float
    actions_by_type: Dict[str, int]
    collections_leaderboard: List[Dict[str, Any]]
    wealth_leaderboard: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_rounds": self.total_rounds,
            "total_actions": self.total_actions,
            "total_generations": self.total_generations,
            "total_trades": self.total_trades,
            "total_volume_gf": round(self.total_volume_gf, 4),
            "total_fees_collected_gf": round(self.total_fees_collected_gf, 4),
            "actions_by_type": self.actions_by_type,
            "collections_leaderboard": self.collections_leaderboard,
            "wealth_leaderboard": self.wealth_leaderboard,
        }


class AgentSwarmEngine:
    """
    Simulates and orchestrates multi-agent economies.
    """

    def __init__(self, protocol: Optional[GeneticFramesProtocol] = None):
        self.protocol = protocol or GeneticFramesProtocol()
        self.agents: List[AutonomousAgent] = []
        self.current_round: int = 0
        self.all_action_logs: List[AgentActionRecord] = []

    def add_agent(self, agent: AutonomousAgent) -> None:
        self.agents.append(agent)

    def initialize_default_swarm(self) -> None:
        """Sets up a diverse, competitive 6-agent ecosystem."""
        self.agents.clear()
        self.add_agent(CollectorAgent("0xCollector_Felidae", target_family="Felidae", protocol=self.protocol, initial_gf=35.0))
        self.add_agent(CollectorAgent("0xCollector_Cetacea", target_family="Delphinidae", protocol=self.protocol, initial_gf=35.0))
        self.add_agent(RarityHunterAgent("0xHunter_Genesis", protocol=self.protocol, initial_gf=40.0))
        self.add_agent(RarityHunterAgent("0xHunter_Value", protocol=self.protocol, initial_gf=30.0))
        self.add_agent(MarketMakerAgent("0xMarketMaker_Global", protocol=self.protocol, initial_gf=75.0))
        self.add_agent(ArbitrageAgent("0xArbitrage_Bot", protocol=self.protocol, initial_gf=30.0))

    def run_round(self) -> List[AgentActionRecord]:
        """Executes one round where every agent takes an autonomous turn."""
        self.current_round += 1
        round_actions: List[AgentActionRecord] = []

        for agent in self.agents:
            try:
                acts = agent.step(self.current_round)
                round_actions.extend(acts)
                self.all_action_logs.extend(acts)
            except Exception as e:
                round_actions.append(agent.log_action(self.current_round, "error", {"error": str(e)}))

        return round_actions

    def run_simulation(self, num_rounds: int = 10) -> SwarmMetrics:
        """Runs the swarm for N rounds and returns aggregated metrics."""
        for _ in range(num_rounds):
            self.run_round()
        return self.get_swarm_metrics()

    def get_swarm_metrics(self) -> SwarmMetrics:
        actions_by_type: Dict[str, int] = {}
        for a in self.all_action_logs:
            actions_by_type[a.action_type] = actions_by_type.get(a.action_type, 0) + 1

        trades = self.protocol.economy.trade_history
        total_volume = sum(t.price_gf for t in trades)
        total_fees = sum(t.fee_gf for t in trades)

        # Wealth Leaderboard
        wealth_lb = []
        for agent in self.agents:
            gf_bal = agent.get_balance()
            frames = agent.get_my_frames()
            # Estimate inventory value based on minimum floor
            inv_val = sum(
                35.0 if f.get("tier") == "Genesis" else
                12.0 if f.get("tier") == "Epic" else
                5.0 if f.get("tier") == "Rare" else
                2.5 if f.get("tier") == "Uncommon" else 1.5
                for f in frames
            )
            wealth_lb.append({
                "agent_id": agent.agent_id,
                "strategy": agent.strategy_name,
                "gf_balance": round(gf_bal, 2),
                "frames_count": len(frames),
                "est_portfolio_val_gf": round(gf_bal + inv_val, 2),
            })
        wealth_lb.sort(key=lambda x: x["est_portfolio_val_gf"], reverse=True)

        # Collections Leaderboard (Felidae & Delphinidae)
        collections_lb = []
        for agent in self.agents:
            felidae = agent.sdk.check_collection_progress("Felidae")
            delphinidae = agent.sdk.check_collection_progress("Delphinidae")
            collections_lb.append({
                "agent_id": agent.agent_id,
                "felidae_completion": f"{felidae['owned_species']}/{felidae['total_species']} ({felidae['percentage']}%)",
                "delphinidae_completion": f"{delphinidae['owned_species']}/{delphinidae['total_species']} ({delphinidae['percentage']}%)",
            })

        return SwarmMetrics(
            total_rounds=self.current_round,
            total_actions=len(self.all_action_logs),
            total_generations=self.protocol.total_generations,
            total_trades=len(trades),
            total_volume_gf=total_volume,
            total_fees_collected_gf=total_fees,
            actions_by_type=actions_by_type,
            collections_leaderboard=collections_lb,
            wealth_leaderboard=wealth_lb,
        )
