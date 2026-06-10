import sys
import os

# Align path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.automation_service import AutomationProtocolService

def test_echo_protocol_generation():
    service = AutomationProtocolService(plate_type="384_well")
    cocktail = {
        "GATA4": 1.5,
        "MEF2C": 1.0,
        "TBX5": 0.5,
        "MYC": 0.0  # Excluded factor (0 dosage) should not write a row
    }
    
    csv_rows = service.generate_echo_transfer_csv("A1", cocktail)
    
    assert len(csv_rows) == 4  # Header + 3 factors
    assert csv_rows[0] == "Source Well,Destination Well,Transfer Volume (nL),Factor Name"
    
    # Check GATA4 transfer details: source reservoir A1 (standard layout), vol: 1.5 * 500 = 750 nL
    # Destination well: distributed in row B (chr(65+1) = B), col 1
    assert "A1,B1,750,GATA4" in csv_rows
    # Check MEF2C: source reservoir A2, vol: 1.0 * 500 = 500 nL, dest: B2
    assert "A2,B2,500,MEF2C" in csv_rows
    # Check TBX5: source reservoir A3, vol: 0.5 * 500 = 250 nL, dest: B3
    assert "A3,B3,250,TBX5" in csv_rows

def test_echo_protocol_rounding():
    service = AutomationProtocolService()
    # 0.005 dosage translates to 2.5 nL (which is the physical Echo transfer step)
    # E.g. 0.005 * 500 = 2.5 nL
    # 0.004 dosage rounds to 2.5 nL
    # 0.001 dosage rounds to 0 nL (omitted)
    cocktail = {
        "GATA4": 0.005,
        "MEF2C": 0.004,
        "TBX5": 0.001
    }
    
    csv_rows = service.generate_echo_transfer_csv("A1", cocktail)
    
    assert "A1,B1,2,GATA4" in csv_rows
    assert "A2,B2,2,MEF2C" in csv_rows
    assert len(csv_rows) == 3  # Header + GATA4 + MEF2C

if __name__ == "__main__":
    print("Running Automation Protocol unit tests...")
    test_echo_protocol_generation()
    test_echo_protocol_rounding()
    print("All tests passed!")
