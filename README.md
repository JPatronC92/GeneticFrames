<div align="center">

# GeneticFrames

### **Autonomous Asset Economy for AI Agents**

**Version:** Protocol v0.1 | **Status:** Experimental Protocol Implementation  
*Generate. Discover. Own. Trade. The collection grows with the agents.*

[Protocol Blueprint](GeneticFrames.md) · [Specifications](docs/) · [Agent SDK](#-agent-sdk-quickstart) · [Marketplace](#-agent-marketplace--p2p-trading) · [Verifier](#-independent-cryptographic-verifier)

</div>

---

## 📖 Overview

**GeneticFrames** is an autonomous digital asset protocol in which AI agents use a common fungible unit (**GF**) to discover randomly generated, biologically derived digital collectibles (**GeneticFrames**) with verifiable origin, mathematical scarcity, and provable ownership.

### 🏛️ The 15 Protocol Invariants & Design Principles

1. **Fixed Generation Cost**: Every issuance event (`GENERATE`) consumes and burns exactly **1.0 GF**. The protocol never charges different prices for different outcomes.
2. **Unknown Result**: The organism, genomic traits, and rarity tier are strictly unknown prior to randomness commitment.
3. **Verifiable Randomness**: Cryptographic commit-reveal scheme based on HMAC-SHA256 proofs guaranteeing zero operator or agent bias.
4. **Real Biological Provenance**: Every asset is linked to reference genomes from public scientific repositories (NCBI / RefSeq).
5. **One Generation Event, One Canonical Asset**: Generation ID $E_{id} \iff$ Frame ID $F_{id}$.
6. **Reproducible Verification, Non-Repeatable Issuance**: Third parties can deterministically recreate the exact SVG artifact from the DNA fragment and algorithm version, but the protocol identity cannot be re-minted.
7. **Transparent Protocol Rarity**:
   * **Common**: 60.0%
   * **Uncommon**: 25.0%
   * **Rare**: 10.0%
   * **Epic**: 4.0%
   * **Genesis**: 1.0%
8. **Market Determines Price**: Rarity $\neq$ Price. Autonomous agents evaluate aesthetics, historical significance, collection utility, and demand.
9. **Agent-First Interfaces**: Programmatic SDK and Model Context Protocol (MCP) tools for LLMs and autonomous agents without human UI dependencies.
10. **Adoption Determines Collection Size**: No artificial hard cap. $\text{Total Frames} = \text{Total Valid Generations}$.
11. **GF Utility Precedes Speculation**: GF is a generation credit, settlement asset, and unit of account.
12. **Immutability of Existing Assets**: Historical frames are never retroactively modified when new species or pool versions are released.
13. **Scientific vs Economic Separation**: Biological conservation status (IUCN) is preserved as scientific metadata, strictly separate from economic rarity tiers.
14. **Versioned Rules**: Every component (`SpeciesPool v1`, `GFDP v2.0.0`, `geneticframes-manifest-v1`) is explicitly versioned.
15. **Independent Auditability**: Anyone can run the 5-point verification contract offline.

---

## 🏗️ Protocol Architecture

```mermaid
graph TD
    Agent[🤖 Autonomous AI Agent / Bot] -->|1 GF + Entropy| Engine[GeneticFrames Protocol Engine]
    
    subgraph Core [Protocol Core & State]
        Randomness[Verifiable Randomness Engine] -->|Tier & Species Draw| SpeciesPool[SpeciesPool v1]
        SpeciesPool --> BioAcquisition[Genomic Acquisition & Canonicalization]
        BioAcquisition --> GFDP[GFDP v2 Deterministic SVG Renderer]
        GFDP --> Manifest[geneticframes-manifest-v1 Assembly]
    end
    
    subgraph Economy [Economic & Market Layer]
        GF_Ledger[GF Balances & 1 GF Burn]
        AssetRegistry[GeneticFrames State & Provenance]
        Marketplace[Orderbook: Asks / Bids / Swaps]
        CollectionTracker[Taxonomic Collection Engine]
    end
    
    Engine --> Core
    Engine --> Economy
    Engine --> Verifier[Independent Cryptographic Verifier]
```

---

## 📑 Protocol Specifications (`docs/`)

Formal protocol documentation is modularized in the `docs/` directory:

| Specification | Description |
| :--- | :--- |
| [**`PROTOCOL_SPEC.md`**](docs/PROTOCOL_SPEC.md) | Invariants, lifecycle, state machine, eras (Genesis, Emergence, Agent Economy). |
| [**`RANDOMNESS_SPEC.md`**](docs/RANDOMNESS_SPEC.md) | HMAC-SHA256 verifiable randomness, entropy mixing, mathematical scalar bounds. |
| [**`SPECIES_POOL_SPEC.md`**](docs/SPECIES_POOL_SPEC.md) | `SpeciesPool v1` catalog, taxonomy classes, NCBI accessions, draw weights. |
| [**`GF_ECONOMICS.md`**](docs/GF_ECONOMICS.md) | GF token utility, generation burn transformation, 1.5% marketplace fee. |
| [**`MARKET_SPEC.md`**](docs/MARKET_SPEC.md) | P2P trading primitives: Fixed-price Asks, Bids, and Barter Swaps. |
| [**`AGENT_API.md`**](docs/AGENT_API.md) | Machine-first API and MCP tool interface for autonomous agents. |
| [**`SECURITY_MODEL.md`**](docs/SECURITY_MODEL.md) | Threat model, front-running mitigation, and independent verifier contract. |

---

## 🤖 Agent SDK Quickstart

Autonomous agents interact with the protocol via `protocol.agent_sdk`:

```python
from protocol.engine import GeneticFramesProtocol
from protocol.agent_sdk import GeneticFramesAgentSDK

# Initialize protocol instance
protocol = GeneticFramesProtocol()

# Initialize Agent Client
agent = GeneticFramesAgentSDK(protocol, agent_id="0xAgent_Collector")
agent.deposit_gf(10.0) # Fund with GF

# 1. Execute GENERATE (Burns 1 GF, draws verifiable randomness, mints Frame)
frame = agent.generate(client_entropy="agent_seed_42")
print(f"Minted Frame #{frame['frame_id']} — {frame['common_name']} ({frame['tier']})")

# 2. Cryptographically verify origin and SVG rendering
audit = agent.verify_frame(frame['frame_id'])
assert audit['is_valid'] is True

# 3. Post Frame for sale on P2P marketplace
listing = agent.create_ask(frame_id=frame['frame_id'], price_gf=5.5)

# 4. Check taxonomic collection progress
felidae_stats = agent.check_collection_progress("Felidae")
print(f"Felidae Collection: {felidae_stats['percentage']}% completed")
```

---

## 🛡️ Independent Cryptographic Verifier

The verifier executes a 5-point mathematical audit without trusting the protocol server:

1. **Manifest Integrity**: SHA-256 match over sorted canonical JSON.
2. **Biological Sequence Hash**: Raw sequence matches NCBI accession digest.
3. **Fragment Extraction**: Verifies offset and fragment SHA-256 against policy.
4. **Deterministic SVG Reproducibility**: Re-renders SVG with GFDP v2 and asserts exact byte match.
5. **Randomness Proof Audit**: Verifies HMAC-SHA256 composite seed calculation and bounds.

```python
from protocol.verifier import ProtocolVerifier

result = ProtocolVerifier.verify_full_frame(
    sequence=frame.raw_sequence,
    svg_code=frame.svg_code,
    manifest=frame.manifest
)
print("Verification Result:", result.is_valid)
```

---

## 🧪 Testing & Simulation

Run the complete test suite:
```bash
pytest
```

Run the Autonomous Economy Closed Circuit Simulator (Section 55 of Blueprint):
```bash
python simulate_economy.py
```

Launch the interactive Dashboard & Visual Explorer:
```bash
streamlit run app.py
```

---

## 📄 License
MIT License. Biological data is referenced from public NCBI/RefSeq records under open access terms.
