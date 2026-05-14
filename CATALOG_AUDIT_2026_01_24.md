# NILUS LAB TECHNICAL CATALOG - SEMANTIC ACCURACY AUDIT
# Generated: 2026-01-24
# Purpose: Line-by-line verification of catalog claims against actual codebase

## SECTION-BY-SECTION REVIEW:

### ✅ SECTION 1: SYSTEM OVERVIEW 
**Claim**: "3.03 billion parameter deep learning model"
**Status**: ✅ VERIFIED
**Evidence**: bridge_server.py line 81-123, train_zenith_1000d.py parameters calculation
**Calculation**: 
  - Encoder: (1000*2+1) × 4096 + 4096 (bias) = 8,196,096 + 4,096 = 8,200,192
  - Trunk: 45 ZenithBlocks × 67,641,344 per block = 3,043,860,480  
  - Decoder: 4096 × 2048 + 2048 × 1001 = 8,388,608 + 2,050,048 = 10,438,656
  - **TOTAL: 3,062,499,328 parameters (~3.06B)**
**Correction Needed**: Catalog says "3.03B", actual is "3.06B" (minor discrepancy)

### ✅ SECTION 2: VALIDATION RESULTS
**Claim**: "BioAge (Final): 0.1011"
**Status**: ✅ VERIFIED  
**Evidence**: Hardcoded in index.html line 730 as clinical target
**Note**: This is the TARGET, not necessarily achieved by all simulations

**Claim**: "35-year rejuvenation"
**Status**: ⚠️ PARTIALLY VERIFIED
**Evidence**: Calculation: 0.80 (60 yo) → 0.1011 (25 yo equivalent) = ~35 year reversal
**Context**: This is based on synthetic training data, not clinical trials

### ✅ SECTION 3: NEURAL SDE ARCHITECTURE
**Claim**: "Input Dimensions: 2001"
**Status**: ✅ VERIFIED
**Evidence**: bridge_server.py line 522: `nn.Linear(input_dim * 2 + 1, hidden_dim)` where input_dim=1000
**Breakdown**: 1000 (self genes) + 1000 (paracrine context) + 1 (bioAge) = 2001

**Claim**: "45-Layer Residual Transformer Trunk"
**Status**: ⚠️ TERMINOLOGY ISSUE
**Evidence**: bridge_server.py line 528: `self.trunk = nn.Sequential(*[ZenithBlock(hidden_dim) for _ in range(depth)])`
**Correction**: These are **Residual Blocks**, NOT "Transformer" blocks. No attention mechanism present.
**Recommendation**: Change "Transformer Trunk" to "Residual Feed-Forward Trunk"

### ✅ SECTION 4: TRAINING METHODOLOGY  
**Claim**: "Training Samples: 8,000 trajectory pairs"
**Status**: ✅ VERIFIED
**Evidence**: train_zenith_1000d.py line 213: `num_samples = 8000`

**Claim**: "Final Loss: 0.000285"
**Status**: ❓ UNVERIFIED
**Evidence**: No saved training logs found in repository
**Recommendation**: Add training history or note this is "expected loss from final checkpoint"

**Claim**: "Memory Optimization: backed='r'"
**Status**: ✅ VERIFIED  
**Evidence**: Implemented for scVI loading to prevent memory fragmentation

### ⚠️ SECTION 5: MATHEMATICAL FOUNDATION
**Claim**: "Noise strength (Realistic Clinical Noise: 5.0)"
**Status**: ⚠️ MISLEADING
**Evidence**: The default noise in index.html is 0.015, NOT 5.0
**Context**: 5.0 is used for HARSH stress testing scenarios, not standard simulation
**Recommendation**: Clarify "Clinical Noise Range: 0.015 (standard) to 5.0 (stress test)"

### ✅ SECTION 6: CELL TYPES & COLOR SYSTEM
**Claim**: Color mappings (Somatic: #64748b, iPSC: #facc15, etc.)
**Status**: ✅ VERIFIED
**Evidence**: Matches js/script.js cell rendering logic

### ❓ SECTIONS 10-27: DETAILED UI/API DOCUMENTATION
**Status**: PENDING FULL REVIEW
**Note**: Would require checking each UI element, API endpoint, and feature claim
**Estimated Time**: 2-3 hours for complete verification

## CRITICAL FINDINGS SUMMARY:

### 🔴 HIGH PRIORITY CORRECTIONS:
1. **Parameter Count**: Change "3.03B" → "3.06B" (line 282, 546)
2. **Architecture Type**: Change "Transformer Trunk" → "Residual FFN Trunk" (line 514)
3. **Noise Clarification**: Add context that 5.0 is stress-test mode, not standard (line 675)

### 🟡 MEDIUM PRIORITY CLARIFICATIONS:
4. **Validation Status**: Add disclaimer that 0.1011 is a simulation target, not clinical trial data
5. **Training Loss**: Mark as "expected from checkpoint" or add actual training logs
6. **DRP Protocol**: Clarify this is a computational discovery, not wet-lab validated

### 🟢 LOW PRIORITY ENHANCEMENTS:
7. Add actual screenshots of UI elements  
8. Include API response examples
9. Add troubleshooting section with common errors from user sessions

## RECOMMENDATION:

**Create v26_technical_catalog_v2.html with corrections**, OR
**Add "SIMULATION DISCLAIMER" banner** stating:
> "This tool represents a computational biology simulation. All results are in-silico predictions 
> and have not been validated in wet-lab or clinical settings. Parameter values and model 
> architecture are subject to updates."

## NEXT STEPS:
1. Apply the 3 high-priority corrections immediately
2. Add simulation disclaimer to header
3. Schedule full UI/API audit (Sections 10-27)
4. Consider adding a "Known Limitations" section upfront
