"""
Taxonomic Collector Agent
Focuses on completing specific biological family collections (e.g. Felidae, Cetacea)
through targeted discovery, selective marketplace purchasing, and liquidating non-target assets.
"""
from __future__ import annotations

from typing import Any, Dict, List
from protocol.engine import GeneticFramesProtocol
from protocol.species_pool import SPECIES_POOL_V1
from .base_agent import AgentActionRecord, AutonomousAgent


class CollectorAgent(AutonomousAgent):
    """
    Autonomous agent driven by collection completion goals.
    """

    def __init__(
        self,
        agent_id: str,
        target_family: str = "Felidae",
        protocol: GeneticFramesProtocol = None,
        initial_gf: float = 25.0,
        max_buy_price_gf: float = 8.0,
    ):
        super().__init__(
            agent_id=agent_id,
            strategy_name=f"Taxonomic Collector ({target_family})",
            protocol=protocol,
            initial_gf=initial_gf,
        )
        self.target_family = target_family
        self.max_buy_price_gf = max_buy_price_gf

    def step(self, round_num: int) -> List[AgentActionRecord]:
        actions: List[AgentActionRecord] = []
        progress = self.sdk.check_collection_progress(self.target_family)
        missing_names = set(progress["missing"])
        current_balance = self.get_balance()

        # Step 1: Scan marketplace for missing target species
        market_book = self.sdk.get_market_book()
        for listing in market_book["active_listings"]:
            if listing["seller_id"] == self.agent_id:
                continue
            frame_info = self.protocol.inspect_frame(listing["frame_id"])
            if not frame_info:
                continue

            # Check if this frame belongs to missing target family species
            if frame_info.scientific_name in missing_names:
                if listing["price_gf"] <= self.max_buy_price_gf and current_balance >= listing["price_gf"]:
                    try:
                        trade = self.sdk.buy_listing(listing["listing_id"])
                        actions.append(
                            self.log_action(
                                round_num,
                                "buy_listing",
                                {
                                    "listing_id": listing["listing_id"],
                                    "frame_id": listing["frame_id"],
                                    "species": frame_info.scientific_name,
                                    "price_gf": trade["price_gf"],
                                    "reason": f"Target collection missing species: {frame_info.scientific_name}",
                                },
                            )
                        )
                        missing_names.discard(frame_info.scientific_name)
                        current_balance = self.get_balance()
                    except Exception:
                        pass

        # Step 2: Liquidate non-target or duplicate frames to raise GF
        my_frames = self.get_my_frames()
        owned_target_counts: Dict[str, int] = {}
        for f in my_frames:
            full_frame = self.protocol.inspect_frame(f["frame_id"])
            if not full_frame:
                continue
            s_name = full_frame.scientific_name
            is_target = full_frame.organism_id in [s.organism_id for s in SPECIES_POOL_V1.get_family_species(self.target_family)]
            
            # If non-target or duplicate, list on marketplace if not already listed
            is_already_listed = any(
                l["frame_id"] == f["frame_id"] and l["status"] == "active"
                for l in market_book["active_listings"]
            )
            if not is_already_listed:
                if not is_target:
                    # Sell non-target at fair floor price
                    try:
                        l_data = self.sdk.create_ask(f["frame_id"], price_gf=3.5)
                        actions.append(self.log_action(round_num, "create_ask", {"frame_id": f["frame_id"], "price_gf": 3.5, "reason": "Liquidate non-target asset"}))
                    except Exception:
                        pass
                else:
                    owned_target_counts[s_name] = owned_target_counts.get(s_name, 0) + 1
                    if owned_target_counts[s_name] > 1:
                        # Sell duplicate target frame
                        try:
                            l_data = self.sdk.create_ask(f["frame_id"], price_gf=6.0)
                            actions.append(self.log_action(round_num, "create_ask", {"frame_id": f["frame_id"], "price_gf": 6.0, "reason": f"Sell duplicate target species {s_name}"}))
                        except Exception:
                            pass

        # Step 3: If target collection incomplete and balance >= 1.0 GF, execute GENERATE
        if not progress["is_complete"] and current_balance >= 1.0:
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
                            "is_target_species": gen_res["scientific_name"] in missing_names,
                        },
                    )
                )
            except Exception:
                pass

        if not actions:
            actions.append(self.log_action(round_num, "hold", {"progress": progress["percentage"], "balance": current_balance}))

        return actions
