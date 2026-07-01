#!/usr/bin/env python3
"""
fix_website_content.py
Fixes all known website content issues across Nilus Lab HTML pages.
"""

import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fix_file(filepath, replacements, meta_description=None):
    """
    Apply a list of (old, new) replacements to a file.
    Optionally insert a meta description after the <title> tag if not already present.
    Returns a list of change descriptions.
    """
    relpath = os.path.relpath(filepath, BASE_DIR)
    abs_path = os.path.join(BASE_DIR, filepath) if not os.path.isabs(filepath) else filepath

    if not os.path.exists(abs_path):
        return [f"  [SKIP] File not found: {relpath}"]

    with open(abs_path, 'r', encoding='utf-8') as f:
        content = f.read()

    changes = []
    original = content

    # Apply text replacements
    for old_text, new_text, desc in replacements:
        count = content.count(old_text)
        if count > 0:
            content = content.replace(old_text, new_text)
            changes.append(f"  [FIXED] {desc} ({count} occurrence(s)): '{old_text}' -> '{new_text}'")
        else:
            changes.append(f"  [SKIP]  Not found: '{old_text}'")

    # Add meta description if missing
    if meta_description:
        if 'name="description"' in content or "name='description'" in content:
            changes.append(f"  [SKIP]  Meta description already exists")
        else:
            # Insert after the </title> tag
            title_pattern = r'(</title>)'
            match = re.search(title_pattern, content, re.IGNORECASE)
            if match:
                insert_pos = match.end()
                meta_tag = f'\n    <meta name="description" content="{meta_description}">'
                content = content[:insert_pos] + meta_tag + content[insert_pos:]
                changes.append(f"  [ADDED] Meta description tag inserted after <title>")
            else:
                changes.append(f"  [WARN]  Could not find </title> tag to insert meta description")

    if content != original:
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return changes


def main():
    print("=" * 70)
    print("NILUS LAB WEBSITE CONTENT FIX SCRIPT")
    print("=" * 70)
    print()

    all_changes = {}

    # =========================================================================
    # 1. legal.html - Remove IS-CHRP codename leak + Fix parameter count
    # =========================================================================
    changes = fix_file(
        os.path.join(BASE_DIR, 'legal.html'),
        [
            ('IS-CHRP', 'Zenith',
             'Remove IS-CHRP codename leak'),
            ('~167.6M Parameter Manifolds', '~500M Parameter Manifolds',
             'Fix parameter count inconsistency'),
            # Also catch standalone 167.6M if present
            ('167.6M', '500M',
             'Fix parameter count (standalone)'),
        ],
        meta_description="Legal center for Nilus Lab Zenith. Terms of service, licensing tiers, privacy policy, and GDPR compliance documentation."
    )
    all_changes['legal.html'] = changes

    # =========================================================================
    # 2. regulatory.html - Fix version mismatch
    # =========================================================================
    changes = fix_file(
        os.path.join(BASE_DIR, 'regulatory.html'),
        [
            ('Version 26.4', 'Version 30.0',
             'Fix version mismatch'),
            ('Build 0x771A GOLD', 'Build 0x300_v30',
             'Fix build string (0x771A)'),
            ('Build 0x290_v30', 'Build 0x300_v30',
             'Fix build string (0x290)'),
        ],
        meta_description="Regulatory strategy and compliance framework for Nilus Lab Zenith. Research Use Only (RUO) classification, GDPR compliance, and ISO 13485 roadmap."
    )
    all_changes['regulatory.html'] = changes

    # =========================================================================
    # 3. whitepaper.html - Fix cell count
    # =========================================================================
    changes = fix_file(
        os.path.join(BASE_DIR, 'whitepaper.html'),
        [
            ('150,000 real single-cell observations', '486,134 real single-cell observations',
             'Fix cell count (full phrase)'),
            ('150,000+ real cardiac cells', '486,134+ real cardiac cells',
             'Fix cell count (cardiac cells)'),
            ('150,000+ Observations', '486,134+ Observations',
             'Fix cell count (table)'),
            ('150,000 observations', '486,134 observations',
             'Fix cell count (observations)'),
            ('U-150k cardiac cohort', 'U-486k cardiac cohort',
             'Fix cell count (cohort reference)'),
            ('150k+ observations', '486k+ observations',
             'Fix cell count (150k+)'),
        ],
        meta_description="Scientific whitepaper for the Zenith v30.0 foundation model. Architecture, training methodology, and validation results for computational cardiac reprogramming."
    )
    all_changes['whitepaper.html'] = changes

    # =========================================================================
    # 4. evidence.html - Fix R² inconsistency
    # =========================================================================
    changes = fix_file(
        os.path.join(BASE_DIR, 'evidence.html'),
        [
            # Round 0.9421 to 0.942
            ('<span class="text-slate-800 font-mono">0.9421</span>',
             '<span class="text-slate-800 font-mono">0.942</span> <!-- Cross-validated prediction accuracy (different metric from 0.998 manifold reconstruction fidelity) -->',
             'Fix R² rounding and add clarifying comment'),
            # Add clarifying comment near the 0.998 manifold fidelity value
            ('<div class="text-6xl font-black text-slate-900 mb-6">0.998</div>',
             '<div class="text-6xl font-black text-slate-900 mb-6">0.998</div> <!-- Manifold reconstruction fidelity R² (different metric from 0.942 cross-validated prediction accuracy) -->',
             'Add clarifying comment for 0.998 manifold fidelity R²'),
        ],
        meta_description="Scientific evidence registry for Zenith v30.0. Benchmarks, validation metrics, and reproducibility data for cardiac reprogramming trajectory models."
    )
    all_changes['evidence.html'] = changes

    # =========================================================================
    # 5. api.html - Fix wrong endpoint paths
    # =========================================================================
    changes = fix_file(
        os.path.join(BASE_DIR, 'api.html'),
        [
            ('/api/v1/discovery/factors', '/api/v1/discover/run',
             'Fix discovery endpoint'),
            ('/api/v1/trials/simulate', '/api/v1/trials/run',
             'Fix trials endpoint'),
            ('/api/v1/perturbation/predict', '/api/v1/predict/perturbation',
             'Fix perturbation endpoint'),
        ],
        meta_description="Developer API reference for Nilus Lab Zenith v30.0. REST endpoints for safety auditing, LNP optimization, protein folding, perturbation prediction, and virtual clinical trials."
    )
    all_changes['api.html'] = changes

    # =========================================================================
    # 6. Add meta descriptions to remaining pages
    # =========================================================================
    meta_only_pages = {
        'technical_catalog.html': "Zenith v30.0 GOLD institutional technical catalog. Complete architecture specification including scVI manifold, GRN inference, and epigenetic clock integration.",
        'trials.html': "Virtual clinical trial simulation platform powered by Zenith v30.0. Run digital twin cohort studies with Kaplan-Meier analysis and AI dosage optimization.",
        'about.html': "About Nilus Lab. The world's leading center for in-silico human reprogramming, building AI-powered systems biology for cardiac regeneration.",
        'contact.html': "Contact Nilus Lab engineering team. Institutional inquiries, partnership opportunities, and technical support for the Zenith platform.",
        'how_it_works.html': "How Zenith GOLD works. Step-by-step operational protocol from authentication to discovery prompting and AlphaFold 3 structural validation.",
        'scientific_qna.html': "Scientific Q&A for the Zenith foundation model. Detailed technical answers about training data, architecture, validation, and safety mechanisms.",
    }

    for filename, meta_desc in meta_only_pages.items():
        changes = fix_file(
            os.path.join(BASE_DIR, filename),
            [],  # no text replacements
            meta_description=meta_desc
        )
        all_changes[filename] = changes

    # =========================================================================
    # Print summary
    # =========================================================================
    print()
    total_fixed = 0
    total_skipped = 0
    total_added = 0

    for filename, changes in all_changes.items():
        print(f"--- {filename} ---")
        for change in changes:
            print(change)
            if '[FIXED]' in change:
                total_fixed += 1
            elif '[SKIP]' in change:
                total_skipped += 1
            elif '[ADDED]' in change:
                total_added += 1
        print()

    print("=" * 70)
    print(f"SUMMARY: {total_fixed} fixes applied, {total_added} meta tags added, {total_skipped} skipped")
    print("=" * 70)


if __name__ == '__main__':
    main()
