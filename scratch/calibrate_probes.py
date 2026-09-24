import sys
import os

sys.path.insert(0, r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative')
from services.horvath_clock import HorvathClockService

service = HorvathClockService()

def calibrate(chrono_age, rejuv_target):
    betas = {}
    coefs = service.coefficients
    intercept = service.intercept # 0.696
    
    # Horvath target linear sum:
    # For adult age > 20: F(age) = (age - 20) / 21
    target_bio_age = max(20.0, chrono_age - rejuv_target)
    target_f_age = (target_bio_age - 20.0) / 21.0
    
    # We want: intercept + sum(coef * beta) == target_f_age
    # Baseline sum with beta=0.5:
    base_sum = intercept + sum(c * 0.5 for c in coefs.values())
    needed_delta = target_f_age - base_sum
    
    # Distribute needed_delta across probes proportional to their coefficient magnitude
    sum_sq_coef = sum(c**2 for c in coefs.values())
    
    for p, c in coefs.items():
        # Beta shift
        beta = 0.50 + (needed_delta * c / (sum_sq_coef + 1e-6))
        betas[p] = max(0.0, min(1.0, float(beta)))
        
    res = service.calculate_age(betas)
    print(f"Chrono: {chrono_age}y | Target: {target_bio_age}y | Predicted: {res['predicted_biological_age']}y")
    return betas

calibrate(65.0, 0.0)
calibrate(65.0, 10.0)
calibrate(65.0, 2.0)
calibrate(65.0, 15.0)
