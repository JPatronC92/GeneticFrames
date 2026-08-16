# SPECIES POOL SPECIFICATION: SpeciesPool v1

## 1. Pool Architecture & Versioning
The `SpeciesPool v1` constitutes the immutable registry of biological species available for generation in Protocol Epoch 1.

* Any addition or alteration of organisms requires bumping the pool version (e.g. `SpeciesPool v2`).
* Historical generations maintain a strict reference to the exact pool version and hash in their manifest.

---

## 2. Species Schema & Tiers

Each species definition contains taxonomy, biological reference accessions, rarity classification, and conservation status metadata.

```json
{
  "organism_id": "SP-MAM-001",
  "common_name": "Jaguar",
  "scientific_name": "Panthera onca",
  "taxonomy": {
    "kingdom": "Animalia",
    "phylum": "Chordata",
    "class": "Mammalia",
    "order": "Carnivora",
    "family": "Felidae",
    "genus": "Panthera",
    "taxon_id": 9690
  },
  "genomic_source": {
    "provider": "NCBI",
    "database": "nucleotide",
    "accession": "NC_028684.1",
    "title": "Panthera onca mitochondrion, complete genome",
    "length": 17006,
    "sha256": "..."
  },
  "protocol_tier": "Rare",
  "draw_weight": 0.25,
  "conservation": {
    "authority": "IUCN",
    "status": "Near Threatened (NT)",
    "snapshot_date": "2026-08-15"
  }
}
```

---

## 3. Catalog Taxonomy Groups

`SpeciesPool v1` organizes organisms into curated taxonomic categories to enable collection mechanics:
* **Felidae Collection**: *Panthera onca* (Jaguar), *Panthera leo* (Lion), *Panthera tigris* (Tiger), *Panthera pardus* (Leopard), *Acinonyx jubatus* (Cheetah), *Felis catus* (Domestic Cat).
* **Cetacea Collection**: *Balaenoptera musculus* (Blue Whale), *Orcinus orca* (Killer Whale), *Delphinus delphis* (Common Dolphin).
* **Primates Collection**: *Homo sapiens* (Reference), *Pan troglodytes* (Chimpanzee), *Gorilla gorilla* (Western Gorilla).
* **Extinct & Prehistoric**: *Mammuthus primigenius* (Woolly Mammoth), *Raphus cucullatus* (Dodo), *Smilodon populator* (Saber-toothed Cat).
* **Extremophiles & Singular**: *Ambystoma mexicanum* (Axolotl), *Tardigrada* (Water Bear), *Deinococcus radiodurans*.
