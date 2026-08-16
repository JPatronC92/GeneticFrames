"""
GeneticFrames Verifiable Randomness Engine (v1.0.0)
Cryptographic commit-reveal randomness with auditable proofs.
"""
from __future__ import annotations

import hashlib
import hmac
import time
import secrets
from dataclasses import dataclass
from typing import Dict, Any, Tuple


@dataclass(frozen=True)
class RandomnessProof:
    scheme: str
    epoch: int
    generation_id: int
    epoch_seed_hash: str
    agent_entropy_hash: str
    nonce: int
    composite_seed_hash: str
    tier_scalar: float
    species_scalar: float
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scheme": self.scheme,
            "epoch": self.epoch,
            "generation_id": self.generation_id,
            "epoch_seed_hash": self.epoch_seed_hash,
            "agent_entropy_hash": self.agent_entropy_hash,
            "nonce": self.nonce,
            "composite_seed_hash": self.composite_seed_hash,
            "tier_scalar": round(self.tier_scalar, 10),
            "species_scalar": round(self.species_scalar, 10),
            "timestamp": self.timestamp,
        }


class RandomnessEngine:
    """
    Produces verifiable, deterministic pseudo-random scalars for generation events.
    Combines Epoch Master Entropy + Agent Client Entropy + Monotonic Nonce + Generation ID.
    """
    SCHEME = "hmac-sha256-v1"

    def __init__(self, epoch: int = 1, epoch_secret: str | None = None):
        self.epoch = epoch
        self.epoch_secret = (epoch_secret or secrets.token_hex(32)).encode("utf-8")
        self.epoch_seed_hash = hashlib.sha256(self.epoch_secret).hexdigest()

    def derive_draw(
        self,
        generation_id: int,
        agent_id: str,
        nonce: int,
        client_entropy: str | None = None
    ) -> Tuple[float, float, RandomnessProof]:
        """
        Derives two orthogonal scalars in [0.0, 1.0) and generates an auditable proof.
        - tier_scalar: used for protocol rarity tier selection
        - species_scalar: used for organism selection within the tier
        """
        if client_entropy is None:
            client_entropy = secrets.token_hex(16)

        agent_entropy_bytes = f"{agent_id}:{client_entropy}".encode("utf-8")
        agent_entropy_hash = hashlib.sha256(agent_entropy_bytes).hexdigest()

        # Composite message: epoch + generation_id + agent_id + nonce + client_entropy
        msg = f"{self.epoch}:{generation_id}:{agent_id}:{nonce}:{agent_entropy_hash}".encode("utf-8")
        
        # Primary HMAC digest
        digest_1 = hmac.new(self.epoch_secret, msg + b":tier", hashlib.sha256).hexdigest()
        digest_2 = hmac.new(self.epoch_secret, msg + b":species", hashlib.sha256).hexdigest()

        # Convert hex digests into floating point scalars in [0, 1)
        tier_int = int(digest_1[:14], 16)
        tier_scalar = tier_int / float(16**14)

        species_int = int(digest_2[:14], 16)
        species_scalar = species_int / float(16**14)

        composite_seed_hash = hashlib.sha256((digest_1 + digest_2).encode("utf-8")).hexdigest()

        proof = RandomnessProof(
            scheme=self.SCHEME,
            epoch=self.epoch,
            generation_id=generation_id,
            epoch_seed_hash=self.epoch_seed_hash,
            agent_entropy_hash=agent_entropy_hash,
            nonce=nonce,
            composite_seed_hash=composite_seed_hash,
            tier_scalar=tier_scalar,
            species_scalar=species_scalar,
            timestamp=time.time(),
        )

        return tier_scalar, species_scalar, proof

    @classmethod
    def verify_proof_consistency(cls, proof: RandomnessProof) -> bool:
        """
        Verifies internal mathematical bounds and format of the randomness proof.
        """
        if proof.scheme != cls.SCHEME:
            return False
        if not (0.0 <= proof.tier_scalar < 1.0):
            return False
        if not (0.0 <= proof.species_scalar < 1.0):
            return False
        if len(proof.composite_seed_hash) != 64:
            return False
        if len(proof.agent_entropy_hash) != 64:
            return False
        return True
