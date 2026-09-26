"""
Test Suite: Widened Banned-Literal Scanner & CI Gate
====================================================
Scans all production files (HTML, JS, Python bridge) for fabricated,
quarantined, or uncalibrated terms and literals.

Enforces an explicit, checked-in allowlist where terms appear in legitimate
scientific citation contexts, CSS color channels, or JS load-order comments.
"""

import os
import re
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WIDENED_TERMS = [
    # Newly audited terms:
    "NL-101",
    "lead asset",
    "Lead Asset Selection",
    "0.93",
    "0.90",
    ">10,000",
    "10,000",
    "516",
    "2596",
    "conformal",
    "Conformal",
    "teratoma",
    "pluripotency risk",
    "Genomic Stability",
    "Sarkar",
    "Krolevets",
    "ranked first",
    "top of",
    "211",
    # Previously banned terms:
    "BiT Age",
    "Age Reversal",
    "age_delta_years",
    "35-Year",
    "first of 516",
    "Horvath",
    "CpG",
    "OMICmAge",
    "Ketamine",
    "Decitabine",
    "Semaglutide",
    "Plasmapheresis",
    "dual-age",
    "13.0",
    "13.00",
    "14.2",
    "12.4",
    "9.27",
    "4.99",
    "0.928",
    "0.948",
    "8.073",
    "5.759",
    "0.685",
    "52.1",
    "1.9925",
    "1.81",
    "6.0",
    "7.0",
    "0.24",
    "0.26",
    "62.4",
    "43.3",
    "28.1",
    "29.4"
]

TARGET_FILES = [
    "index.html",
    "profile.html",
    "zenith_scientific_paper.html",
    "technical_catalog.html",
    "evidence.html",
    "trials.html",
    "regulatory.html",
    "whitepaper.html",
    "scientific_qna.html",
    "colony_microscopy_demo.html",
    "about.html",
    "structure.html",
    "api.html",
    "paper.html",
    "legal.html",
    "bridge_server.py",
    "js/script.js"
]

# Explicit, checked-in allowlist with documented justifications:
ALLOWLIST_RULES = [
    # 1. CSS RGB Green Channel (52, 211, 153)
    {
        "file": "colony_microscopy_demo.html",
        "term": "211",
        "matches": lambda line: "rgba(52, 211, 153" in line or "rgba(52,211,153" in line or "211, 153" in line,
        "reason": "CSS green color channel (RGB 52, 211, 153 = #34d399) used for rendering colony microscopy canvas"
    },
    {
        "file": "js/script.js",
        "term": "211",
        "matches": lambda line: "rgba(52, 211, 153" in line or "211, 153" in line,
        "reason": "CSS green color channel (RGB 52, 211, 153) used for rendering agent particles in simulation canvas"
    },
    # 2. Source code comments
    {
        "file": "index.html",
        "term": "top of",
        "matches": lambda line: "config.js already loaded at top of file" in line,
        "reason": "JavaScript file load order dependency comment ('loaded at top of file')"
    },
    # 3. Documented technical threshold
    {
        "file": "technical_catalog.html",
        "term": "0.90",
        "matches": lambda line: "> 0.90 = aligned" in line or "&gt; 0.90 = aligned" in line,
        "reason": "Documented specification threshold for transcriptomic lineage alignment score in telemetry table"
    },
    # 4. Literature citations (Yamanaka 2006/2007)
    {
        "file": "paper.html",
        "term": "teratoma",
        "matches": lambda line: "lethal teratoma formation (4, 5)" in line,
        "reason": "Peer-reviewed literature citation to Yamanaka & Takahashi describing in vivo teratoma risk of unconstrained OSKM factors"
    },
    {
        "file": "zenith_scientific_paper.html",
        "term": "teratoma",
        "matches": lambda line: "lethal teratoma formation (4, 5)" in line,
        "reason": "Peer-reviewed literature citation to Yamanaka & Takahashi describing in vivo teratoma risk of unconstrained OSKM factors"
    },
    # 5. Client-side GRN visualization mock fixtures
    {
        "file": "js/script.js",
        "term": "0.93",
        "matches": lambda line: '"NKX2-5": 0.93' in line or "safety: 0.93" in line,
        "reason": "Test fixture weights for client-side GRN interactive network visualization graph layout"
    },
    {
        "file": "js/script.js",
        "term": "0.90",
        "matches": lambda line: '"CPT1B": 0.90' in line or '"NANOG": 0.90' in line or "weight: 0.90" in line,
        "reason": "Test fixture edge weights for client-side GRN interactive network visualization graph layout"
    }
]


def _compile_patterns():
    compiled = []
    for term in WIDENED_TERMS:
        if re.match(r"^[\d\.\>]+$", term):
            pat = re.compile(rf"(?<!\d){re.escape(term)}(?!\d)")
        else:
            pat = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        compiled.append((term, pat))
    return compiled


def _check_allowlist(fname, term, line):
    for rule in ALLOWLIST_RULES:
        if rule["file"] == fname and rule["term"] == term:
            if rule["matches"](line):
                return rule["reason"]
    return None


def test_no_unallowlisted_banned_literals():
    """Scan all production files for prohibited terms; verify only allowlisted instances occur."""
    compiled_patterns = _compile_patterns()
    violations = []
    allowlisted_hits = []

    for rel_path in TARGET_FILES:
        full_path = os.path.join(ROOT, rel_path)
        if not os.path.exists(full_path):
            continue

        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, 1):
                for term, pat in compiled_patterns:
                    for match in pat.finditer(line):
                        reason = _check_allowlist(rel_path, term, line)
                        snip = line.strip()
                        if len(snip) > 80:
                            start = max(0, match.start() - 25)
                            end = min(len(line), match.end() + 25)
                            snip = line[start:end].strip()

                        if reason:
                            allowlisted_hits.append((rel_path, line_no, term, snip, reason))
                        else:
                            violations.append((rel_path, line_no, term, snip))

    if violations:
        report_lines = [f"{f}:{l} [{term}] -> ...{s}..." for f, l, term, s in violations]
        msg = f"Found {len(violations)} banned literal violation(s):\n" + "\n".join(report_lines)
        pytest.fail(msg)

    assert len(violations) == 0
