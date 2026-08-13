# GeneticFrames DNA-to-SVG Protocol (GFDP) v2.0.0

GFDP converts a bounded DNA fragment into a deterministic SVG and verification
manifest. It is an art protocol, not a taxonomic classifier or population rarity model.

## Contract

Input identity is `canonical sequence + fragment policy + algorithm version + source
snapshot`. DNA is uppercase IUPAC, whitespace is removed, and U becomes T. The
default is the centered 768 bases; accepted render fragments are 64–1,024 bases.
Full genomes are hashed for provenance but never rendered.

Outputs contain SHA-256 identifiers for the complete sequence, selected fragment,
manifest and SVG. `verify_artifact()` works without network access.

## Visual grammar

- GC, nucleotide skews and entropy determine a continuous color family, so related
  fragments retain a related style.
- Local composition windows define primary geometry.
- Dinucleotide frequencies define secondary rings.
- Actual motif positions define zoom-level details.
- No pseudo-random noise participates in layout or uniqueness.

## Rarity and conservation

`algorithmic_composition_rarity` describes visual/compositional extremeness only.
It is not biological or population rarity. Conservation status is a separate,
immutable snapshot with authority, assessment/date and status.

## Limits

- Render fragment: 64–1,024 unambiguous bases; default 768.
- SVG: maximum 64 KB.
- Algorithm changes require a new version; old certificates retain their renderer.
