"""
Base class and data contracts for Autonomous AI Agents in the GeneticFrames ecosystem.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from protocol.agent_sdk import GeneticFramesAgentSDK
from protocol.engine import GeneticFramesProtocol


@dataclass
class AgentActionRecord:
    timestamp: float
    round_num: int
    agent_id: str
    action_type: str  # "generate", "buy_listing", "create_ask", "cancel_ask", "place_bid", "accept_bid", "swap", "hold"
    details: Dict[str, Any]
    balance_after: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "round_num": self.round_num,
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "details": self.details,
            "balance_after": round(self.balance_after, 4),
        }


class AutonomousAgent(ABC):
    """
    Abstract base class for autonomous economic agents.
    """

    def __init__(
        self,
        agent_id: str,
        strategy_name: str,
        protocol: GeneticFramesProtocol,
        initial_gf: float = 20.0,
    ):
        self.agent_id = agent_id
        self.strategy_name = strategy_name
        self.protocol = protocol
        self.sdk = GeneticFramesAgentSDK(protocol=protocol, agent_id=agent_id)
        if initial_gf > 0:
            self.sdk.deposit_gf(initial_gf)
        self.action_history: List[AgentActionRecord] = []

    def get_balance(self) -> float:
        return self.sdk.get_balance()

    def get_my_frames(self) -> List[Dict[str, Any]]:
        return self.sdk.list_my_frames()

    def log_action(self, round_num: int, action_type: str, details: Dict[str, Any]) -> AgentActionRecord:
        record = AgentActionRecord(
            timestamp=time.time(),
            round_num=round_num,
            agent_id=self.agent_id,
            action_type=action_type,
            details=details,
            balance_after=self.get_balance(),
        )
        self.action_history.append(record)
        return record

    @abstractmethod
    def step(self, round_num: int) -> List[AgentActionRecord]:
        """
        Executes one autonomous decision tick:
        1. Observes market state and portfolio.
        2. Evaluates strategic opportunities.
        3. Executes economic actions.
        """
        pass

    def to_summary_dict(self) -> Dict[str, Any]:
        frames = self.get_my_frames()
        return {
            "agent_id": self.agent_id,
            "strategy": self.strategy_name,
            "gf_balance": round(self.get_balance(), 4),
            "frames_owned_count": len(frames),
            "actions_executed": len(self.action_history),
            "frames": frames,
        }
