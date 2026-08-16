# RANDOMNESS SPECIFICATION: Verifiable Draw Protocol v1

## 1. Overview
The GeneticFrames Randomness Engine ensures that no entity—including the server operator, the requesting agent, or a network observer—can manipulate the organism or rarity tier received during a generation event.

---

## 2. Cryptographic Scheme

The protocol uses a deterministic commit-reveal randomness scheme based on HMAC-SHA256:

$$\text{Seed} = \text{HMAC-SHA256}(\text{Protocol Secret / Epoch Entropy}, \text{Agent Entropy} \parallel \text{Nonce} \parallel \text{Generation ID})$$

### 2.1 Inputs
1. **Epoch Seed / Block Hash ($S_{epoch}$)**: A 32-byte cryptographic commitment representing network entropy.
2. **Agent Entropy ($E_{agent}$)**: 32-byte salt provided by the generating agent.
3. **Sequence Nonce ($N$)**: Monotonic counter per agent to prevent replay attacks.
4. **Generation ID ($G_{id}$)**: Monotonic global generation event index.

### 2.2 Proof Structure
The generated manifest embeds the full randomness proof:
```json
{
  "randomness": {
    "scheme": "hmac-sha256-v1",
    "epoch": 1,
    "agent_entropy_sha256": "3a4f...",
    "composite_seed_sha256": "9b12...",
    "draw_scalar": 0.4829104812,
    "proof_signature": "0x..."
  }
}
```

---

## 3. Draw Procedure

From the composite scalar $U \in [0, 1)$:

### 3.1 Protocol Rarity Draw
The scalar $U_{tier} = \text{Scalar}_1$ is matched against the cumulative probability distribution:

| Tier | Probability | Cumulative Threshold |
| :--- | :--- | :--- |
| **Common** | 60.0% | $0.00 \le U < 0.60$ |
| **Uncommon** | 25.0% | $0.60 \le U < 0.85$ |
| **Rare** | 10.0% | $0.85 \le U < 0.95$ |
| **Epic** | 4.0% | $0.95 \le U < 0.99$ |
| **Genesis** | 1.0% | $0.99 \le U < 1.00$ |

### 3.2 Organism Selection
A secondary derived scalar $U_{species} = \text{Scalar}_2$ selects an organism from the eligible subset of `SpeciesPool v1` corresponding to the drawn tier using normalized discrete weights.
