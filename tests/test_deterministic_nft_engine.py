import hashlib
import pytest
from deterministic_nft_engine import MAX_SVG_BYTES, FragmentPolicy, canonicalize_dna, generate_deterministic_svg, genetic_distance, select_fragment, verify_artifact

BASE = ("ACGTGCCATTAACCGG" * 64)[:768]

def test_canonicalization(): assert canonicalize_dna("acgu\nACGT") == "ACGTACGT"
def test_invalid():
    with pytest.raises(ValueError): canonicalize_dna("ACGT!")
def test_byte_identical():
    assert generate_deterministic_svg(BASE, "Species") == generate_deterministic_svg(BASE, "Species")
def test_human_label_does_not_change_certified_image():
    first, _ = generate_deterministic_svg(BASE, "Label A")
    second, _ = generate_deterministic_svg(BASE, "Label B")
    assert first == second
def test_mutation_changes_artifact():
    mutated = BASE[:400] + ("A" if BASE[400] != "A" else "C") + BASE[401:]
    a, am = generate_deterministic_svg(BASE, "Species"); b, bm = generate_deterministic_svg(mutated, "Species")
    assert a != b and am["sequence"]["sha256"] != bm["sequence"]["sha256"]
def test_relatedness():
    close = list(BASE)
    for i in range(0, len(close), 97): close[i] = "T" if close[i] != "T" else "A"
    assert genetic_distance(BASE, "".join(close)) < genetic_distance(BASE, ("GGGGCCCC"*96)[:768])
def test_bounded_fragment():
    seq = "A"*200 + BASE + "T"*200; frag, off = select_fragment(seq, FragmentPolicy(512, "center"))
    assert len(frag) == 512 and off == (len(seq)-512)//2
def test_budget_and_verification():
    svg, m = generate_deterministic_svg(BASE, "Species", source={"provider":"NCBI","accession":"TEST.1"}, conservation={"authority":"IUCN","snapshot":"2026-08-12","status":"EN"})
    assert len(svg.encode()) <= MAX_SVG_BYTES and verify_artifact(BASE, svg, m) and not verify_artifact(BASE, svg+" ", m)
    assert m["svg_sha256"] == hashlib.sha256(svg.encode()).hexdigest()
def test_short_fragment():
    seq = ("ACGTTGCA"*16)[:128]; svg, m = generate_deterministic_svg(seq, "Short")
    assert m["fragment"]["length"] == 128 and verify_artifact(seq, svg, m)
