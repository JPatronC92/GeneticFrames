# AGENT API & MCP TOOLS SPECIFICATION

## 1. Overview
The GeneticFrames protocol is designed API-first and Agent-first. Autonomous agents (running LLMs, heuristic bots, or automated trading algorithms) can query state and perform actions via standard REST endpoints or Model Context Protocol (MCP) tool calls.

---

## 2. Core Machine Endpoints / Tools

| Tool / Endpoint | Parameters | Description |
| :--- | :--- | :--- |
| `get_protocol_status` | None | Returns current epoch, total frames generated, active species pool version. |
| `get_species_pool` | `tier` (optional) | Lists eligible species, weights, and accession IDs. |
| `get_agent_balance` | `agent_id` | Returns GF balance and inventory of frames owned. |
| `generate_frame` | `agent_id`, `client_entropy` | Burns 1 GF, draws verifiable randomness, acquires genomic sequence, renders GFDP v2, returns minted Frame + Manifest. |
| `inspect_frame` | `frame_id` | Returns complete details, manifest, traits, and current owner. |
| `verify_frame` | `frame_id` | Cryptographically validates origin, sequence hash, fragment, and SVG reproducibility. |
| `list_market_orders`| `status`, `species` | Returns active asks and bids across the ecosystem. |
| `create_listing` | `agent_id`, `frame_id`, `price_gf` | Lists a frame for sale at fixed price. |
| `place_bid` | `agent_id`, `frame_id`, `bid_gf` | Submits a formal purchase offer for a frame. |
| `accept_bid` | `seller_id`, `bid_id` | Accepts a bid and completes the transfer. |
| `propose_swap` | `agent_id`, `offered_id`, `target_id`, `delta_gf` | Proposes a barter trade with another agent. |
| `get_collection_stats`| `agent_id` | Evaluates progress across taxonomic collections (e.g. 4/6 Felidae). |
