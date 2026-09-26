"""
Pharmacokinetic engine specification.
Prescription drug dosing models and uncalibrated clinical compound parameters have been decommissioned.
"""

from typing import Dict, Any, Tuple, List

class PKPDEngine:
    COMPOUND_PARAMS: Dict[str, Any] = {}

    @classmethod
    def simulate_dosing(cls, compound_name: str, dose_mg: float, frequency_hours: float, duration_days: int = 14, steps_per_hour: int = 4) -> Tuple[List[float], List[float], float]:
        """
        Decommissioned dosing simulation.
        Returns empty telemetry and zero concentration.
        """
        return [], [], 0.0
