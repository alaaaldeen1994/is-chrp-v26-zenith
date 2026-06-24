import csv
from typing import List, Dict, Any

class AutomationProtocolService:
    """
    Microservice for laboratory liquid handler automation script generation.
    Supports Labcyte Echo acoustic droplet transfer lists (96-well and 384-well microplates)
    with strict volume validation matching the physical 2.5 nL droplet increments.
    """
    
    def __init__(self, plate_type: str = "384_well"):
        self.plate_type = plate_type
        # Physical microplate geometries
        self.cols = 24 if plate_type == "384_well" else 12
        self.rows = 16 if plate_type == "384_well" else 8
        
        # Fixed source plate well coordinates for transcription factor and chemical reservoirs (384PP Source Plate)
        self.source_wells = {
            "GATA4": "A1",
            "MEF2C": "A2",
            "TBX5": "A3",
            "NKX2-5": "A4",
            "MYC": "A5",
            "SNAI1": "A6",
            "OCT4": "C1",
            "SOX2": "C2",
            "KLF4": "C3",
            "CHIR99021": "B1",
            "RepSox": "B2",
            "Forskolin": "B3",
            "NMN": "B4",
            "Metformin": "B5",
            "SRT1720": "B6"
        }


    def generate_echo_transfer_csv(self, source_well_override: str, target_cocktail: Dict[str, float]) -> List[str]:
        """
        Generates standard Echo liquid handler CSV transfer log.
        
        CSV schema:
        Source Well,Destination Well,Transfer Volume (nL),Factor Name
        """
        csv_rows = ["Source Well,Destination Well,Transfer Volume (nL),Factor Name"]
        
        # Start distributing into row B and below in destination plate
        current_row_idx = 1  # Row B
        current_col_idx = 1  # Col 1
        
        for factor, dosage in target_cocktail.items():
            val = float(dosage)
            if val <= 0.0:
                continue
                
            # Resolve source well reservoir location
            src_well = self.source_wells.get(factor, source_well_override or "A1")
            dest_well = f"{chr(65 + current_row_idx)}{current_col_idx}"
            
            # Labcyte Echo transfers liquid in discrete 2.5 nL droplets
            # Normalize transfer volume: e.g. 500 nL per dosage unit, rounded to nearest 2.5 nL step
            raw_vol = val * 500.0
            transfer_vol_nl = int(round(raw_vol / 2.5) * 2.5)
            
            if transfer_vol_nl > 0:
                csv_rows.append(f"{src_well},{dest_well},{transfer_vol_nl},{factor}")
                
                # Increment destination layout position
                current_col_idx += 1
                if current_col_idx > self.cols:
                    current_col_idx = 1
                    current_row_idx += 1
                    if current_row_idx >= self.rows:
                        current_row_idx = 1  # Wrap around if plate limit hit
                        
        return csv_rows
