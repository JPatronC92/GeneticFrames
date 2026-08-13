"""Regenerate the deterministic visual family displayed in README.md."""
from pathlib import Path
import json

from deterministic_nft_engine import generate_deterministic_svg, genetic_distance

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "images"
BASE = ("ACGTGCCATTAACCGG" * 64)[:768]


def mutate(sequence, positions, replacement):
    result = list(sequence)
    for position in positions:
        result[position] = replacement if result[position] != replacement else "A"
    return "".join(result)


SAMPLES = {
    "reference": BASE,
    "close-variant-a": mutate(BASE, range(0, len(BASE), 97), "T"),
    "close-variant-b": mutate(BASE, range(41, len(BASE), 83), "G"),
    "distant-profile": ("GGGGCCCC" * 96)[:768],
}

OUTPUT.mkdir(parents=True, exist_ok=True)
summary = {}
for name, sequence in SAMPLES.items():
    svg, manifest = generate_deterministic_svg(
        sequence,
        name,
        source={"kind": "documentation_fixture", "biological_claim": False},
    )
    (OUTPUT / f"{name}.svg").write_text(svg, encoding="utf-8", newline="\n")
    summary[name] = {
        "distance_from_reference": round(genetic_distance(BASE, sequence), 6),
        "sequence_sha256": manifest["sequence"]["sha256"],
        "svg_sha256": manifest["svg_sha256"],
        "svg_bytes": manifest["svg_bytes"],
    }

(OUTPUT / "samples.json").write_text(
    json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
)
print(json.dumps(summary, indent=2, sort_keys=True))
