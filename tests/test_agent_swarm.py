"""
Unit and integration tests for the Autonomous Agent Swarm engine and specialized agent strategies.
"""
import pytest
from agents.arbitrage_agent import ArbitrageAgent
from agents.collector_agent import CollectorAgent
from agents.market_maker_agent import MarketMakerAgent
from agents.rarity_hunter_agent import RarityHunterAgent
from agents.swarm_runner import AgentSwarmEngine
from protocol.engine import GeneticFramesProtocol


class TestAutonomousAgentStrategies:
    def test_collector_agent_logic(self):
        protocol = GeneticFramesProtocol()
        collector = CollectorAgent("0xTestCollector", target_family="Felidae", protocol=protocol, initial_gf=20.0)

        # Step 1: Trigger generation
        actions = collector.step(round_num=1)
        assert len(actions) >= 1
        assert actions[-1].action_type == "generate"
        assert collector.get_balance() == 19.0
        assert len(collector.get_my_frames()) == 1

    def test_rarity_hunter_logic(self):
        protocol = GeneticFramesProtocol()
        hunter = RarityHunterAgent("0xTestHunter", protocol=protocol, initial_gf=15.0)

        # Hunter executes step: generates and lists commons if any
        actions = hunter.step(round_num=1)
        assert any(a.action_type == "generate" for a in actions)
        assert hunter.get_balance() == 14.0

    def test_market_maker_orderbook_depth(self):
        protocol = GeneticFramesProtocol()
        mm = MarketMakerAgent("0xTestMM", protocol=protocol, initial_gf=50.0)

        # Generate baseline inventory
        mm.step(round_num=1)
        assert len(mm.get_my_frames()) >= 1

        # Step 2: Ensure Asks are posted for inventory
        actions2 = mm.step(round_num=2)
        assert any(a.action_type == "create_ask" for a in actions2)
        market_book = mm.sdk.get_market_book()
        assert len(market_book["active_listings"]) >= 1

    def test_arbitrageur_execution(self):
        protocol = GeneticFramesProtocol()
        arbitrageur = ArbitrageAgent("0xTestArb", protocol=protocol, initial_gf=30.0)

        # Step without opportunities should hold
        actions = arbitrageur.step(round_num=1)
        assert actions[0].action_type == "hold"

    def test_swarm_orchestration_rounds(self):
        protocol = GeneticFramesProtocol()
        swarm = AgentSwarmEngine(protocol)
        swarm.initialize_default_swarm()
        assert len(swarm.agents) == 6

        metrics = swarm.run_simulation(num_rounds=3)
        assert metrics.total_rounds == 3
        assert metrics.total_actions > 10
        assert metrics.total_generations > 0
        assert len(metrics.wealth_leaderboard) == 6
        assert len(metrics.collections_leaderboard) == 6
