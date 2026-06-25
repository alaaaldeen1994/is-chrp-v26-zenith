import sys
import os

# Add parent directory to path so we can import bridge_server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bridge_server import D2HUtility

def test_slicing():
    print("=== RUNNING D2H DOMAIN EXTENSION & SLICING UNIT TESTS ===")
    
    # 1. Mock a full-length sequence for KLF4 (canonical length is typically 479aa)
    # We will represent it as a string of 'A's followed by specific marker at the domain to verify indices
    klf4_seq = "".join([str(i % 10) for i in range(1, 501)]) # 500aa sequence, 1-based indexing represented by digits
    # KLF4 functional domain is (352, 479)
    klf4_extracted = D2HUtility.extract_domain(klf4_seq, "KLF4")
    
    expected_klf4_len = 479 - 352 + 1 # 128aa
    print(f"KLF4: Extracted length: {len(klf4_extracted)} (Expected: {expected_klf4_len})")
    assert len(klf4_extracted) == expected_klf4_len, f"Expected {expected_klf4_len}, got {len(klf4_extracted)}"
    
    # Check that the first and last residues match the indices
    # 1-based index 352 is 0-based index 351
    # 1-based index 479 is 0-based index 478
    assert klf4_extracted[0] == klf4_seq[351]
    assert klf4_extracted[-1] == klf4_seq[478]
    print("KLF4 domain slicing index check: PASS")
    
    # 2. Mock a full-length sequence for SIRT1 (canonical length is typically 747aa)
    sirt1_seq = "".join([chr(65 + (i % 26)) for i in range(1, 801)]) # 800aa sequence
    # SIRT1 deacetylase domain is (229, 498)
    sirt1_extracted = D2HUtility.extract_domain(sirt1_seq, "SIRT1")
    
    expected_sirt1_len = 498 - 229 + 1 # 270aa
    print(f"SIRT1: Extracted length: {len(sirt1_extracted)} (Expected: {expected_sirt1_len})")
    assert len(sirt1_extracted) == expected_sirt1_len, f"Expected {expected_sirt1_len}, got {len(sirt1_extracted)}"
    assert sirt1_extracted[0] == sirt1_seq[228]
    assert sirt1_extracted[-1] == sirt1_seq[497]
    print("SIRT1 domain slicing index check: PASS")
    
    # 3. Test the flexible (G4S)3 linker fusion
    fused = D2HUtility.generate_z_linker_handshake(klf4_extracted, sirt1_extracted)
    expected_fused_len = expected_klf4_len + 15 + expected_sirt1_len # 128 + 15 + 270 = 413
    print(f"FUSED: Length: {len(fused)} (Expected: {expected_fused_len})")
    assert len(fused) == expected_fused_len
    assert fused.startswith(klf4_extracted)
    assert fused.endswith(sirt1_extracted)
    assert fused[expected_klf4_len:expected_klf4_len+15] == "GGGGSGGGGSGGGGS"
    print("Flexible Z-linker handshake fusion check: PASS")
    
    # 4. Test fallback to full sequence for unknown factor
    unknown_seq = "M" + "A"*200 + "C"
    unknown_extracted = D2HUtility.extract_domain(unknown_seq, "UNKNOWN_GENE")
    print(f"UNKNOWN: Extracted length: {len(unknown_extracted)} (Expected: {len(unknown_seq)})")
    assert unknown_extracted == unknown_seq
    print("Unknown factor fallback check: PASS")

    print("\nALL UNIT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_slicing()
