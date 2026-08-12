"""GeneticFrames deterministic DNA-to-SVG protocol (GFDP v2.0.0)."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib, json, math, re
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple
from xml.sax.saxutils import escape

import numpy as np
try:  # SVG generation and verification do not require the UI dependency.
    import plotly.graph_objects as go
except ImportError:  # pragma: no cover - exercised in minimal verifier installs
    go = None

ALGORITHM_ID = "geneticframes-dna-svg"
ALGORITHM_VERSION = "2.0.0"
MIN_FRAGMENT_LENGTH, MAX_FRAGMENT_LENGTH = 64, 1024
DEFAULT_FRAGMENT_LENGTH, MAX_SVG_BYTES = 768, 64_000
IUPAC = frozenset("ACGTRYSWKMBDHVN")
BASES = frozenset("ACGT")


@dataclass(frozen=True)
class FragmentPolicy:
    length: int = DEFAULT_FRAGMENT_LENGTH
    mode: str = "center"

    def validate(self):
        if not MIN_FRAGMENT_LENGTH <= self.length <= MAX_FRAGMENT_LENGTH:
            raise ValueError("fragment length outside 64..1024")
        if self.mode not in {"center", "prefix", "suffix"}:
            raise ValueError("mode must be center, prefix, or suffix")


def canonicalize_dna(sequence: str) -> str:
    if not isinstance(sequence, str):
        raise TypeError("sequence must be text")
    result = re.sub(r"\s+", "", sequence).upper().replace("U", "T")
    if not result:
        raise ValueError("empty sequence")
    invalid = set(result) - IUPAC
    if invalid:
        raise ValueError(f"invalid DNA symbols: {''.join(sorted(invalid))}")
    return result


def select_fragment(sequence: str, policy=FragmentPolicy()):
    policy.validate()
    seq = canonicalize_dna(sequence)
    if len(seq) <= policy.length:
        return seq, 0
    start = 0 if policy.mode == "prefix" else len(seq) - policy.length if policy.mode == "suffix" else (len(seq) - policy.length) // 2
    return seq[start:start + policy.length], start


def compute_dna_sha256_seed(sequence: str):
    digest = hashlib.sha256(canonicalize_dna(sequence).encode("ascii")).hexdigest()
    return int(digest[:16], 16) % (2**32 - 1), digest


def _freq(sequence: str, k: int):
    counts = Counter(sequence[i:i+k] for i in range(len(sequence)-k+1) if set(sequence[i:i+k]) <= BASES)
    total = sum(counts.values()) or 1
    return {key: value / total for key, value in sorted(counts.items())}


def _entropy(values: Iterable[float]):
    return -sum(x * math.log2(x) for x in values if x > 0)


def extract_genetic_features(sequence: str):
    seq = canonicalize_dna(sequence)
    known = [x for x in seq if x in BASES]
    if len(known) < MIN_FRAGMENT_LENGTH:
        raise ValueError("at least 64 unambiguous bases are required")
    counts, n = Counter(known), len(known)
    mono = {b: counts[b] / n for b in "ACGT"}
    windows, size = [], max(1, math.ceil(len(seq) / 24))
    for start in range(0, len(seq), size):
        part = seq[start:start+size]
        clean = [x for x in part if x in BASES]
        c, d = Counter(clean), len(clean) or 1
        windows.append({
            "gc": (c["G"] + c["C"]) / d,
            "purine": (c["A"] + c["G"]) / d,
            "entropy": _entropy(c[b] / d for b in "ACGT") / 2,
        })
    return {
        "length": len(seq), "ambiguity_ratio": 1 - n / len(seq), "mono": mono,
        "gc_content": mono["G"] + mono["C"],
        "at_skew": (mono["A"]-mono["T"]) / max(mono["A"]+mono["T"], 1e-12),
        "gc_skew": (mono["G"]-mono["C"]) / max(mono["G"]+mono["C"], 1e-12),
        "entropy": _entropy(mono.values()) / 2,
        "kmers": {str(k): _freq(seq, k) for k in range(2, 6)}, "windows": windows,
    }


def genetic_distance(left: str, right: str, max_k=5):
    distances = []
    for k in range(1, max_k+1):
        a, b = _freq(canonicalize_dna(left), k), _freq(canonicalize_dna(right), k)
        keys = sorted(set(a) | set(b))
        va, vb = np.array([a.get(x, 0) for x in keys]), np.array([b.get(x, 0) for x in keys])
        denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
        distances.append(1 - float(np.dot(va, vb) / denom) if denom else 0)
    return float(np.mean(distances))


def calculate_algorithmic_rarity(features):
    gc, entropy = features["gc_content"], features["entropy"]
    dinuc, mono = features["kmers"]["2"], features["mono"]
    observed, expected = dinuc.get("CG", 0), mono["C"] * mono["G"]
    cpg_dev = min(abs(math.log2((observed+1e-6)/(expected+1e-6))), 4) / 4
    score = round(100 * (0.5*min(abs(gc-.5)/.35, 1) + .3*abs(entropy-1) + .2*cpg_dev), 2)
    return {"metric": "algorithmic_composition_rarity", "score": score,
            "tier": "singular" if score >= 70 else "uncommon" if score >= 45 else "balanced",
            "scientific_population_rarity": False}


def _hsl(h, s, l): return f"hsl({h%360:.1f},{s:.1f}%,{l:.1f}%)"


def _palette(f):
    hue = 205 + 110*f["gc_content"] + 24*f["at_skew"]
    return {"primary": _hsl(hue, 66+18*f["entropy"], 48+9*f["gc_skew"]),
            "secondary": _hsl(hue+55+18*f["gc_skew"], 72, 54),
            "accent": _hsl(hue+180+20*f["at_skew"], 82, 62),
            "background": _hsl(hue-25, 35, 7)}


def _manifest(sequence, fragment, offset, policy, organism, source, features, rarity):
    seq = canonicalize_dna(sequence)
    data = {
        "schema": "geneticframes-manifest-v1",
        "algorithm": {"id": ALGORITHM_ID, "version": ALGORITHM_VERSION},
        "canonicalization": "iupac-dna-v1", "organism_label": organism,
        "sequence": {"sha256": hashlib.sha256(seq.encode()).hexdigest(), "length": len(seq)},
        "fragment": {"sha256": hashlib.sha256(fragment.encode()).hexdigest(), "offset_zero_based": offset,
                     "length": len(fragment), "policy": {"mode": policy.mode, "requested_length": policy.length}},
        "features": {x: round(float(features[x]), 8) for x in ("gc_content", "entropy", "ambiguity_ratio")},
        "rarity": rarity, "source": dict(source or {}),
    }
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
    data["manifest_sha256"] = hashlib.sha256(payload.encode()).hexdigest()
    return data


def generate_deterministic_svg(sequence: str, organism_name: str, palette: Optional[Mapping[str, Sequence[str]]] = None,
                               *, fragment_policy=FragmentPolicy(), source=None, conservation=None):
    fragment, offset = select_fragment(sequence, fragment_policy)
    f = extract_genetic_features(fragment)
    rarity, colors = calculate_algorithmic_rarity(f), _palette(f)
    if palette:
        for key in ("primary", "secondary", "accent"):
            if palette.get(key): colors[key] = palette[key][0]
    manifest = _manifest(sequence, fragment, offset, fragment_policy, organism_name, source, f, rarity)
    if conservation: manifest["conservation_snapshot"] = dict(conservation)
    windows, cx, cy = f["windows"], 400, 400
    outer, inner = [], []
    for i, p in enumerate(windows):
        angle = 2*math.pi*i/len(windows)
        r, ri = 190+105*p["gc"]+36*p["entropy"], 92+65*p["purine"]
        outer.append(f"{cx+r*math.cos(angle):.2f},{cy+r*math.sin(angle):.2f}")
        inner.append(f"{cx+ri*math.cos(-angle):.2f},{cy+ri*math.sin(-angle):.2f}")
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" role="img"><title>{escape(organism_name)}</title>',
           f'<defs><radialGradient id="bg"><stop stop-color="{colors["background"]}"/><stop offset="1" stop-color="#020307"/></radialGradient></defs>',
           '<rect width="800" height="800" fill="url(#bg)"/>',
           f'<polygon points="{" ".join(outer)}" fill="none" stroke="{colors["primary"]}" stroke-width="3"/>',
           f'<polygon points="{" ".join(inner)}" fill="none" stroke="{colors["secondary"]}" stroke-width="2"/>']
    ranked = sorted(f["kmers"]["2"].items(), key=lambda x: (-x[1], x[0]))[:12]
    for i, (kmer, freq) in enumerate(ranked):
        a, r = 2*math.pi*i/max(len(ranked), 1), 64+115*freq
        x, y = cx+265*math.cos(a), cy+265*math.sin(a)
        svg += [f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="none" stroke="{colors["accent"]}" stroke-width="{1+8*freq:.2f}" opacity="{.25+2*freq:.3f}"/>',
                f'<text x="{x:.2f}" y="{y:.2f}" fill="#fff" font-size="9" text-anchor="middle">{kmer}</text>']
    for motif, color in (("CG", colors["accent"]), ("AT", colors["secondary"])):
        for pos in [i for i in range(len(fragment)-1) if fragment[i:i+2] == motif][:48]:
            a, r = 2*math.pi*pos/len(fragment), 330+(pos%7)
            svg.append(f'<circle cx="{cx+r*math.cos(a):.2f}" cy="{cy+r*math.sin(a):.2f}" r="2.2" fill="{color}"/>')
    svg += [f'<text x="24" y="758" fill="#aab" font-family="monospace" font-size="11">GFDP v{ALGORITHM_VERSION} | fragment:{manifest["fragment"]["sha256"][:20]}</text>',
            f'<text x="24" y="782" fill="#fff" font-size="15">{escape(organism_name)} · algorithmic rarity {rarity["score"]}</text></svg>']
    code = "".join(svg)
    if len(code.encode()) > MAX_SVG_BYTES: raise RuntimeError("SVG size budget exceeded")
    manifest["svg_sha256"], manifest["svg_bytes"] = hashlib.sha256(code.encode()).hexdigest(), len(code.encode())
    return code, manifest


def verify_artifact(sequence: str, svg_code: str, manifest: Mapping[str, object]):
    try:
        if manifest["algorithm"] != {"id": ALGORITHM_ID, "version": ALGORITHM_VERSION}: return False
        seq = canonicalize_dna(sequence)
        if hashlib.sha256(seq.encode()).hexdigest() != manifest["sequence"]["sha256"]: return False
        p = manifest["fragment"]["policy"]
        fragment, offset = select_fragment(seq, FragmentPolicy(int(p["requested_length"]), str(p["mode"])))
        return (offset == manifest["fragment"]["offset_zero_based"] and
                hashlib.sha256(fragment.encode()).hexdigest() == manifest["fragment"]["sha256"] and
                hashlib.sha256(svg_code.encode()).hexdigest() == manifest["svg_sha256"])
    except (KeyError, TypeError, ValueError): return False


def create_deterministic_nft_figure(organism_name: str, sequence: str, genetic_profile: Dict, palette: Dict):
    if go is None:
        raise RuntimeError("Plotly is required only for the interactive preview")
    svg, manifest = generate_deterministic_svg(sequence, organism_name, palette)
    fragment, _ = select_fragment(sequence)
    f = extract_genetic_features(fragment); w = f["windows"]
    theta = np.linspace(0, 360, len(w), endpoint=False); radius = np.array([1+p["gc"]*.55+p["entropy"]*.2 for p in w])
    colors = _palette(f)
    fig = go.Figure(go.Scatterpolar(r=np.append(radius, radius[0]), theta=np.append(theta, theta[0]), mode="lines+markers",
                                    line={"color": colors["primary"], "width": 3}, marker={"color": colors["secondary"]}, fill="toself"))
    fig.update_layout(title=f"GeneticFrames · {organism_name} · GFDP v{ALGORITHM_VERSION}", paper_bgcolor="#020307",
                      font={"color": "white"}, polar={"bgcolor": "#020307"}, height=720)
    return fig, svg, manifest
