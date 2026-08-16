"""
GeneticFrames Species Pool Specification & Catalog (SpeciesPool v1)
Versioned, auditable catalog of biological species and genomic sources.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


class RarityTier(str, Enum):
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    EPIC = "Epic"
    GENESIS = "Genesis"


# Protocol Rarity Probability Table v1
TIER_PROBABILITIES: Dict[RarityTier, float] = {
    RarityTier.COMMON: 0.60,
    RarityTier.UNCOMMON: 0.25,
    RarityTier.RARE: 0.10,
    RarityTier.EPIC: 0.04,
    RarityTier.GENESIS: 0.01,
}

# Cumulative thresholds
TIER_THRESHOLDS: List[Tuple[float, RarityTier]] = [
    (0.60, RarityTier.COMMON),
    (0.85, RarityTier.UNCOMMON),
    (0.95, RarityTier.RARE),
    (0.99, RarityTier.EPIC),
    (1.00, RarityTier.GENESIS),
]


@dataclass(frozen=True)
class TaxonomyInfo:
    kingdom: str
    phylum: str
    class_name: str
    order: str
    family: str
    genus: str
    taxon_id: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kingdom": self.kingdom,
            "phylum": self.phylum,
            "class": self.class_name,
            "order": self.order,
            "family": self.family,
            "genus": self.genus,
            "taxon_id": self.taxon_id,
        }


@dataclass(frozen=True)
class GenomicSourceRef:
    provider: str
    database: str
    accession: str
    title: str
    length: int
    sequence_sha256: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "database": self.database,
            "accession": self.accession,
            "title": self.title,
            "length": self.length,
            "sequence_sha256": self.sequence_sha256,
        }


@dataclass(frozen=True)
class SpeciesEntry:
    organism_id: str
    common_name: str
    scientific_name: str
    taxonomy: TaxonomyInfo
    genomic_source: GenomicSourceRef
    tier: RarityTier
    draw_weight: float
    conservation_status: str
    reference_sequence: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "organism_id": self.organism_id,
            "common_name": self.common_name,
            "scientific_name": self.scientific_name,
            "taxonomy": self.taxonomy.to_dict(),
            "genomic_source": self.genomic_source.to_dict(),
            "protocol_tier": self.tier.value,
            "draw_weight": self.draw_weight,
            "conservation_status": self.conservation_status,
        }


# Reference sequences for reproducible offline & online execution
_SEQ_JAGUAR = ("GTACCCACCAACTCCCTGACTTTCATTACCATGACCATCATACTACTAATCATTTTAACTATTCTAATTATAC" * 12)[:768]
_SEQ_LION = ("GTACCCACCAACTCTCTGACCTTTATTACCATGACCATTATACTACTAATCATCTTAACTATCCTAATTATAC" * 12)[:768]
_SEQ_TIGER = ("GTACCCACCAACTCCCTGACTTTCATTACCATGACCATCATACTACTAATCATCTTAACTATTCTAATTATAC" * 12)[:768]
_SEQ_LEOPARD = ("GTACCCACCAACTCCCTGACTTTCATTACCATGACCATTATACTACTAATCATCTTAACTATTCTAATTATAC" * 12)[:768]
_SEQ_CHEETAH = ("GTACCCACCAACTCTCTGACTTTCATTACCATGACCATCATACTACTAATCATTTTAACTATCCTAATTATAC" * 12)[:768]
_SEQ_CAT = ("GTACCCACCAACTCCCTGACCTTCATTACCATGACCATCATACTACTAATCATTCTAACTATCCTAATTATAC" * 12)[:768]

_SEQ_BLUE_WHALE = ("ACCGTACACACCTCAGCGTCAACCCCGCCCGCCACCATGAACATTATCATTACCGCCCTAACCCTCACCATC" * 12)[:768]
_SEQ_ORCA = ("ACCGTACACACCTCAGCATCAATCCCGCCCGCCACCATGAATATTATTATTACCGCCCTAACCCTTATCACC" * 12)[:768]
_SEQ_DOLPHIN = ("ACCGTACACACCTCAGCATCAATCCCGCCCGCCACCATGAATATTATTATTACCGCCCTAACCCTCACCATC" * 12)[:768]

_SEQ_MAMMOTH = ("ATCACCAACCTAATCTCAGCCATCCCATACATCGGCACAAATCTAGTCGAATGAATCTGAGGGGGCTTCTCA" * 12)[:768]
_SEQ_DODO = ("ATGACCCCATTCCTCATGACCCTACTCCTAGTCATCTTAGCACTCCTCTTTACCCTAATCAACCATAAATTA" * 12)[:768]
_SEQ_SMILODON = ("GTACCCACCAACTCCCTGACCTTCATTACCATGACCATCATACTACTAATCATCTTAACTATCCTAACTATAC" * 12)[:768]

_SEQ_AXOLOTL = ("ATGAACCTAACCATTATCCTCCTCCTCACCATCCTCCTAGTCCTAACCTTCCTAACCATCCTACTAATAAAC" * 12)[:768]
_SEQ_TARDIGRADE = ("ATGAATATCTTTCTTTTATTTTTAGGATTTCTTTCTTCTTCTTTATTATTTTTAGGATTTCTTTCTTCTTCT" * 12)[:768]
_SEQ_DEINOCOCCUS = ("GTGCCGCTGCGCGCCCGCCGGCGCCGCGCGCTGCCCGGCGGCCCGCCGCCGGGCGCCCGCCGCGCGCTGCCG" * 12)[:768]

_SEQ_MOUSE = ("ATGACTAACATTCGAAAGTCCCACCCTCTACTAAAAATTATTAACAACTCATTCATCGACCTTCCCACCCCA" * 12)[:768]
_SEQ_BEETLE = ("ATGAATATAGTAATTAATTTTCTTTTATTTTTAGGATTTCTTTCTTCTTCTTTATTATTTTTAGGATTTCTT" * 12)[:768]
_SEQ_ZEBRAFISH = ("ATGACCAACATTCGAAACTCCCACCCCTTGTTTAAAATTATTAATAACTCCTTCATCGACCTCCCAGCACCA" * 12)[:768]
_SEQ_ARABIDOPSIS = ("ATGGCTTCCTCTATGCTCTCTTCCGCTACTATGGTTGCCTCTCCGGCTCAGGCCACTATGGTCGCTCCTCTC" * 12)[:768]


SPECIES_CATALOG: List[SpeciesEntry] = [
    # --- COMMON (60%) ---
    SpeciesEntry(
        organism_id="SP-COM-001",
        common_name="House Mouse",
        scientific_name="Mus musculus",
        taxonomy=TaxonomyInfo("Animalia", "Chordata", "Mammalia", "Rodentia", "Muridae", "Mus", 10090),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_005089.1", "Mus musculus mitochondrion", 16299, hashlib.sha256(_SEQ_MOUSE.encode()).hexdigest()),
        tier=RarityTier.COMMON,
        draw_weight=0.35,
        conservation_status="Least Concern (LC)",
        reference_sequence=_SEQ_MOUSE,
    ),
    SpeciesEntry(
        organism_id="SP-COM-002",
        common_name="Red Flour Beetle",
        scientific_name="Tribolium castaneum",
        taxonomy=TaxonomyInfo("Animalia", "Arthropoda", "Insecta", "Coleoptera", "Tenebrionidae", "Tribolium", 7070),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_003081.2", "Tribolium castaneum mitochondrion", 15884, hashlib.sha256(_SEQ_BEETLE.encode()).hexdigest()),
        tier=RarityTier.COMMON,
        draw_weight=0.35,
        conservation_status="Least Concern (LC)",
        reference_sequence=_SEQ_BEETLE,
    ),
    SpeciesEntry(
        organism_id="SP-COM-003",
        common_name="Thale Cress",
        scientific_name="Arabidopsis thaliana",
        taxonomy=TaxonomyInfo("Plantae", "Tracheophyta", "Magnoliopsida", "Brassicales", "Brassicaceae", "Arabidopsis", 3702),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_000932.1", "Arabidopsis thaliana chloroplast", 154478, hashlib.sha256(_SEQ_ARABIDOPSIS.encode()).hexdigest()),
        tier=RarityTier.COMMON,
        draw_weight=0.30,
        conservation_status="Least Concern (LC)",
        reference_sequence=_SEQ_ARABIDOPSIS,
    ),

    # --- UNCOMMON (25%) ---
    SpeciesEntry(
        organism_id="SP-UNC-001",
        common_name="Domestic Cat",
        scientific_name="Felis catus",
        taxonomy=TaxonomyInfo("Animalia", "Chordata", "Mammalia", "Carnivora", "Felidae", "Felis", 9685),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_001700.1", "Felis catus mitochondrion", 17009, hashlib.sha256(_SEQ_CAT.encode()).hexdigest()),
        tier=RarityTier.UNCOMMON,
        draw_weight=0.40,
        conservation_status="Domesticated",
        reference_sequence=_SEQ_CAT,
    ),
    SpeciesEntry(
        organism_id="SP-UNC-002",
        common_name="Zebrafish",
        scientific_name="Danio rerio",
        taxonomy=TaxonomyInfo("Animalia", "Chordata", "Actinopterygii", "Cypriniformes", "Danionidae", "Danio", 7955),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_002333.2", "Danio rerio mitochondrion", 16596, hashlib.sha256(_SEQ_ZEBRAFISH.encode()).hexdigest()),
        tier=RarityTier.UNCOMMON,
        draw_weight=0.35,
        conservation_status="Least Concern (LC)",
        reference_sequence=_SEQ_ZEBRAFISH,
    ),
    SpeciesEntry(
        organism_id="SP-UNC-003",
        common_name="Common Dolphin",
        scientific_name="Delphinus delphis",
        taxonomy=TaxonomyInfo("Animalia", "Chordata", "Mammalia", "Artiodactyla", "Delphinidae", "Delphinus", 9728),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_012061.1", "Delphinus delphis mitochondrion", 16390, hashlib.sha256(_SEQ_DOLPHIN.encode()).hexdigest()),
        tier=RarityTier.UNCOMMON,
        draw_weight=0.25,
        conservation_status="Least Concern (LC)",
        reference_sequence=_SEQ_DOLPHIN,
    ),

    # --- RARE (10%) ---
    SpeciesEntry(
        organism_id="SP-RAR-001",
        common_name="Jaguar",
        scientific_name="Panthera onca",
        taxonomy=TaxonomyInfo("Animalia", "Chordata", "Mammalia", "Carnivora", "Felidae", "Panthera", 9690),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_028684.1", "Panthera onca mitochondrion", 17006, hashlib.sha256(_SEQ_JAGUAR.encode()).hexdigest()),
        tier=RarityTier.RARE,
        draw_weight=0.30,
        conservation_status="Near Threatened (NT)",
        reference_sequence=_SEQ_JAGUAR,
    ),
    SpeciesEntry(
        organism_id="SP-RAR-002",
        common_name="Lion",
        scientific_name="Panthera leo",
        taxonomy=TaxonomyInfo("Animalia", "Chordata", "Mammalia", "Carnivora", "Felidae", "Panthera", 9689),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_028302.1", "Panthera leo mitochondrion", 16982, hashlib.sha256(_SEQ_LION.encode()).hexdigest()),
        tier=RarityTier.RARE,
        draw_weight=0.25,
        conservation_status="Vulnerable (VU)",
        reference_sequence=_SEQ_LION,
    ),
    SpeciesEntry(
        organism_id="SP-RAR-003",
        common_name="Killer Whale",
        scientific_name="Orcinus orca",
        taxonomy=TaxonomyInfo("Animalia", "Chordata", "Mammalia", "Artiodactyla", "Delphinidae", "Orcinus", 9733),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_023888.1", "Orcinus orca mitochondrion", 16390, hashlib.sha256(_SEQ_ORCA.encode()).hexdigest()),
        tier=RarityTier.RARE,
        draw_weight=0.25,
        conservation_status="Data Deficient (DD)",
        reference_sequence=_SEQ_ORCA,
    ),
    SpeciesEntry(
        organism_id="SP-RAR-004",
        common_name="Cheetah",
        scientific_name="Acinonyx jubatus",
        taxonomy=TaxonomyInfo("Animalia", "Chordata", "Mammalia", "Carnivora", "Felidae", "Acinonyx", 32536),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_005268.1", "Acinonyx jubatus mitochondrion", 17024, hashlib.sha256(_SEQ_CHEETAH.encode()).hexdigest()),
        tier=RarityTier.RARE,
        draw_weight=0.20,
        conservation_status="Vulnerable (VU)",
        reference_sequence=_SEQ_CHEETAH,
    ),

    # --- EPIC (4%) ---
    SpeciesEntry(
        organism_id="SP-EPC-001",
        common_name="Tiger",
        scientific_name="Panthera tigris",
        taxonomy=TaxonomyInfo("Animalia", "Chordata", "Mammalia", "Carnivora", "Felidae", "Panthera", 9694),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_010642.1", "Panthera tigris mitochondrion", 16990, hashlib.sha256(_SEQ_TIGER.encode()).hexdigest()),
        tier=RarityTier.EPIC,
        draw_weight=0.30,
        conservation_status="Endangered (EN)",
        reference_sequence=_SEQ_TIGER,
    ),
    SpeciesEntry(
        organism_id="SP-EPC-002",
        common_name="Blue Whale",
        scientific_name="Balaenoptera musculus",
        taxonomy=TaxonomyInfo("Animalia", "Chordata", "Mammalia", "Artiodactyla", "Balaenopteridae", "Balaenoptera", 9767),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_001601.1", "Balaenoptera musculus mitochondrion", 16402, hashlib.sha256(_SEQ_BLUE_WHALE.encode()).hexdigest()),
        tier=RarityTier.EPIC,
        draw_weight=0.25,
        conservation_status="Endangered (EN)",
        reference_sequence=_SEQ_BLUE_WHALE,
    ),
    SpeciesEntry(
        organism_id="SP-EPC-003",
        common_name="Axolotl",
        scientific_name="Ambystoma mexicanum",
        taxonomy=TaxonomyInfo("Animalia", "Chordata", "Amphibia", "Caudata", "Ambystomatidae", "Ambystoma", 8296),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_005797.1", "Ambystoma mexicanum mitochondrion", 16368, hashlib.sha256(_SEQ_AXOLOTL.encode()).hexdigest()),
        tier=RarityTier.EPIC,
        draw_weight=0.25,
        conservation_status="Critically Endangered (CR)",
        reference_sequence=_SEQ_AXOLOTL,
    ),
    SpeciesEntry(
        organism_id="SP-EPC-004",
        common_name="Water Bear (Tardigrade)",
        scientific_name="Hypsibius exemplaris",
        taxonomy=TaxonomyInfo("Animalia", "Tardigrada", "Eutardigrada", "Parachela", "Hypsibiidae", "Hypsibius", 2043360),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_034873.1", "Hypsibius exemplaris mitochondrion", 14352, hashlib.sha256(_SEQ_TARDIGRADE.encode()).hexdigest()),
        tier=RarityTier.EPIC,
        draw_weight=0.20,
        conservation_status="Extreme Extremophile",
        reference_sequence=_SEQ_TARDIGRADE,
    ),

    # --- GENESIS (1%) ---
    SpeciesEntry(
        organism_id="SP-GEN-001",
        common_name="Woolly Mammoth",
        scientific_name="Mammuthus primigenius",
        taxonomy=TaxonomyInfo("Animalia", "Chordata", "Mammalia", "Proboscidea", "Elephantidae", "Mammuthus", 37329),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_007596.2", "Mammuthus primigenius complete mitochondrion", 16842, hashlib.sha256(_SEQ_MAMMOTH.encode()).hexdigest()),
        tier=RarityTier.GENESIS,
        draw_weight=0.35,
        conservation_status="Extinct (EX)",
        reference_sequence=_SEQ_MAMMOTH,
    ),
    SpeciesEntry(
        organism_id="SP-GEN-002",
        common_name="Saber-toothed Cat",
        scientific_name="Smilodon populator",
        taxonomy=TaxonomyInfo("Animalia", "Chordata", "Mammalia", "Carnivora", "Felidae", "Smilodon", 100479),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_038162.1", "Smilodon populator complete mitochondrion", 16900, hashlib.sha256(_SEQ_SMILODON.encode()).hexdigest()),
        tier=RarityTier.GENESIS,
        draw_weight=0.35,
        conservation_status="Extinct (EX)",
        reference_sequence=_SEQ_SMILODON,
    ),
    SpeciesEntry(
        organism_id="SP-GEN-003",
        common_name="Radiation Survivor Bacterium",
        scientific_name="Deinococcus radiodurans",
        taxonomy=TaxonomyInfo("Bacteria", "Deinococcota", "Deinococci", "Deinococcales", "Deinococcaceae", "Deinococcus", 1299),
        genomic_source=GenomicSourceRef("NCBI", "nucleotide", "NC_001263.1", "Deinococcus radiodurans chromosome 1", 2648638, hashlib.sha256(_SEQ_DEINOCOCCUS.encode()).hexdigest()),
        tier=RarityTier.GENESIS,
        draw_weight=0.30,
        conservation_status="Singular Extremophile",
        reference_sequence=_SEQ_DEINOCOCCUS,
    ),
]


class SpeciesPool:
    """
    Manages SpeciesPool versioning, deterministic weighted drawing, and collection inspection.
    """
    VERSION = "1.0.0"
    NAME = "SpeciesPool v1"

    def __init__(self, catalog: List[SpeciesEntry] | None = None):
        self.catalog = catalog or SPECIES_CATALOG
        self.catalog_by_id: Dict[str, SpeciesEntry] = {s.organism_id: s for s in self.catalog}
        self.catalog_by_tier: Dict[RarityTier, List[SpeciesEntry]] = {tier: [] for tier in RarityTier}
        for entry in self.catalog:
            self.catalog_by_tier[entry.tier].append(entry)
        
        # Calculate catalog hash
        serialized = "".join(f"{s.organism_id}:{s.scientific_name}:{s.draw_weight}" for s in self.catalog)
        self.catalog_sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get_tier_from_scalar(self, scalar: float) -> RarityTier:
        """Determines rarity tier from a normalized scalar in [0, 1)."""
        for threshold, tier in TIER_THRESHOLDS:
            if scalar < threshold:
                return tier
        return RarityTier.GENESIS

    def draw_species(self, tier_scalar: float, species_scalar: float) -> Tuple[RarityTier, SpeciesEntry]:
        """
        Draws a rarity tier and an organism using two orthogonal verifiable scalars.
        """
        tier = self.get_tier_from_scalar(tier_scalar)
        candidates = self.catalog_by_tier[tier]
        if not candidates:
            # Fallback to entire catalog if tier is empty
            candidates = self.catalog

        # Weighted cumulative draw
        total_weight = sum(c.draw_weight for c in candidates)
        target = species_scalar * total_weight
        cumulative = 0.0
        selected = candidates[-1]

        for c in candidates:
            cumulative += c.draw_weight
            if target <= cumulative:
                selected = c
                break

        return tier, selected

    def get_by_id(self, organism_id: str) -> Optional[SpeciesEntry]:
        return self.catalog_by_id.get(organism_id)

    def get_by_scientific_name(self, scientific_name: str) -> Optional[SpeciesEntry]:
        clean = scientific_name.strip().lower()
        for s in self.catalog:
            if s.scientific_name.lower() == clean:
                return s
        return None

    def get_family_species(self, family: str) -> List[SpeciesEntry]:
        return [s for s in self.catalog if s.taxonomy.family.lower() == family.lower()]


SPECIES_POOL_V1 = SpeciesPool()
