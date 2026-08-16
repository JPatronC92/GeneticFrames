"""
GeneticFrames Autonomous Swarm CLI Runner
Runs a multi-round competitive multi-agent simulation with rich real-time terminal telemetry.
"""
import json
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from protocol.engine import GeneticFramesProtocol
from agents.swarm_runner import AgentSwarmEngine


def run_swarm():
    print("=" * 80)
    print("🤖 GENETICFRAMES: AUTONOMOUS AI AGENT SWARM SIMULATOR")
    print("=" * 80)

    protocol = GeneticFramesProtocol()
    engine = AgentSwarmEngine(protocol)
    engine.initialize_default_swarm()

    print(f"\n[Ecosystem Setup] {len(engine.agents)} Autonomous Agents Initialized:")
    for a in engine.agents:
        print(f"  • {a.agent_id:<24} | Strategy: {a.strategy_name:<32} | Balance: {a.get_balance():.1f} GF")

    total_rounds = 6
    print(f"\n[Executing {total_rounds} Autonomous Rounds...]")
    for r in range(1, total_rounds + 1):
        print(f"\n--- [ ROUND {r} ] ---")
        actions = engine.run_round()
        for act in actions:
            if act.action_type != "hold":
                print(f"  ⚡ {act.agent_id:<22} -> {act.action_type:<18} | Details: {act.details}")

    metrics = engine.get_swarm_metrics()

    print("\n" + "=" * 80)
    print("📊 SWARM TELEMETRY & ECONOMIC EQUILIBRIUM SUMMARY")
    print("=" * 80)
    print(f"  • Total Autonomous Actions:     {metrics.total_actions}")
    print(f"  • Total Generations (GF Burn): {metrics.total_generations}")
    print(f"  • Total Secondary P2P Trades:   {metrics.total_trades}")
    print(f"  • Total Market Volume:          {metrics.total_volume_gf:.2f} GF")
    print(f"  • Treasury Fees Collected:      {metrics.total_fees_collected_gf:.4f} GF")

    print("\n[Action Breakdown]")
    for act_type, count in metrics.actions_by_type.items():
        print(f"  • {act_type:<22}: {count}")

    print("\n[Wealth & Portfolio Leaderboard]")
    for i, rank in enumerate(metrics.wealth_leaderboard, 1):
        print(f"  {i}. {rank['agent_id']:<22} | GF: {rank['gf_balance']:<6.2f} | Frames: {rank['frames_count']:<2} | Est. Value: {rank['est_portfolio_val_gf']:.2f} GF")

    print("\n[Collection Race Leaderboard]")
    for c in metrics.collections_leaderboard:
        print(f"  • {c['agent_id']:<22} | Felidae: {c['felidae_completion']:<16} | Delphinidae: {c['delphinidae_completion']}")

    print("\n✅ Multi-Agent Swarm Simulation completed successfully!\n")


if __name__ == "__main__":
    run_swarm()
