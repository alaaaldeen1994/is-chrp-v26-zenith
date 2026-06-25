import numpy as np

class PKPDEngine:
    # Pharmacokinetic parameters for clinical compounds
    # F: Bioavailability, ka: absorption rate (1/hr), ke: elimination rate (1/hr)
    # kin: tissue import rate (1/hr), kout: tissue clearance rate (1/hr)
    # Vd: Apparent volume of distribution (L)
    COMPOUND_PARAMS = {
        "Semaglutide": {
            "F": 0.89, "ka": 0.015, "ke": 0.0041, "kin": 0.05, "kout": 0.02, "Vd": 12.5,
            "default_dose": 1.0, "default_freq_hrs": 168.0  # Weekly
        },
        "NMN": {
            "F": 0.12, "ka": 1.2, "ke": 0.35, "kin": 0.40, "kout": 0.30, "Vd": 45.0,
            "default_dose": 500.0, "default_freq_hrs": 24.0  # Daily
        },
        "Omega3": {
            "F": 0.50, "ka": 0.40, "ke": 0.029, "kin": 0.12, "kout": 0.08, "Vd": 60.0,
            "default_dose": 1000.0, "default_freq_hrs": 24.0  # Daily
        },
        "Decitabine": {
            "F": 1.00, "ka": 5.0, "ke": 1.38, "kin": 0.80, "kout": 0.70, "Vd": 35.0,
            "default_dose": 20.0, "default_freq_hrs": 24.0  # Daily
        },
        "Ketamine": {
            "F": 0.93, "ka": 4.0, "ke": 0.28, "kin": 0.50, "kout": 0.45, "Vd": 150.0,
            "default_dose": 50.0, "default_freq_hrs": 168.0  # Weekly
        },
        "Bezisterim": {
            "F": 0.65, "ka": 0.50, "ke": 0.058, "kin": 0.18, "kout": 0.15, "Vd": 80.0,
            "default_dose": 5.0, "default_freq_hrs": 24.0  # Daily
        },
        "Pitavastatin": {
            "F": 0.51, "ka": 0.80, "ke": 0.063, "kin": 0.22, "kout": 0.18, "Vd": 95.0,
            "default_dose": 2.0, "default_freq_hrs": 24.0  # Daily
        },
        "Multivitamin": {
            "F": 0.75, "ka": 0.60, "ke": 0.115, "kin": 0.25, "kout": 0.20, "Vd": 50.0,
            "default_dose": 1.0, "default_freq_hrs": 24.0  # Daily
        },
        "Plasmapheresis": {
            "F": 1.00, "ka": 10.0, "ke": 0.001, "kin": 0.01, "kout": 0.01, "Vd": 5.0,
            "default_dose": 1.0, "default_freq_hrs": 720.0  # Monthly acute clear
        }
    }

    @classmethod
    def simulate_dosing(cls, compound_name, dose_mg, frequency_hours, duration_days=14, steps_per_hour=4):
        """
        Simulates 2-compartment PK/PD model using Euler numerical integration.
        Returns:
            spark_time: Downsampled time points (hours)
            spark_tissue: Downsampled intracellular concentration values (ug/L)
            steady_state_avg: Average intracellular concentration in the last dosing interval (ug/L)
        """
        params = cls.COMPOUND_PARAMS.get(compound_name)
        if not params:
            return [], [], 0.0

        # Extract rates
        F = params["F"]
        ka = params["ka"]
        ke = params["ke"]
        kin = params["kin"]
        kout = params["kout"]
        Vd = params["Vd"]

        total_hours = duration_days * 24.0
        dt = 1.0 / steps_per_hour
        num_steps = int(total_hours * steps_per_hour)

        # State variables
        Depot = 0.0      # Drug at absorption site (mg)
        Cp = 0.0         # Plasma concentration (mg/L or ug/mL)
        Ci = 0.0         # Intracellular/Tissue concentration (mg/L)

        # Telemetry lists
        time_points = []
        plasma_conc = []
        tissue_conc = []

        # Dosing times
        dosing_interval_steps = int(frequency_hours * steps_per_hour)

        for step in range(num_steps):
            t = step * dt
            time_points.append(t)
            
            # Apply dose at intervals
            if dosing_interval_steps > 0 and (step % dosing_interval_steps == 0) and (dose_mg > 0):
                Depot += dose_mg

            # 1. Depot absorption to Plasma
            dDepot = -ka * Depot * dt
            Depot += dDepot

            # 2. Plasma concentration dynamics (2-compartment transfer and clearance)
            # F * ka * Depot is the rate of absorption in mg/hr
            absorption_rate = F * ka * (Depot - dDepot/dt)  # approximation of absorption flux
            dCp = ((absorption_rate / Vd) - (ke * Cp) - (kin * Cp) + (kout * Ci)) * dt
            Cp += dCp

            # 3. Intracellular concentration dynamics
            dCi = ((kin * Cp) - (kout * Ci)) * dt
            Ci += dCi

            # Convert concentration to ug/L (or ppb) for higher resolution
            plasma_conc.append(max(0.0, float(Cp * 1000.0)))
            tissue_conc.append(max(0.0, float(Ci * 1000.0)))

        # Calculate steady-state average of the intracellular compartment in the last 24 hours
        last_day_steps = int(24.0 * steps_per_hour)
        if len(tissue_conc) >= last_day_steps:
            steady_state_avg = float(np.mean(tissue_conc[-last_day_steps:]))
        else:
            steady_state_avg = float(np.mean(tissue_conc))

        # Downsample telemetry for frontend sparkline (return ~30 points representing the last interval)
        interval_steps = min(len(tissue_conc), int(max(24.0, frequency_hours) * steps_per_hour))
        last_interval_tissue = tissue_conc[-interval_steps:]
        last_interval_time = time_points[-interval_steps:]
        
        # Select 30 evenly spaced points
        indices = np.linspace(0, len(last_interval_tissue) - 1, 30, dtype=int)
        spark_time = [last_interval_time[idx] for idx in indices]
        spark_tissue = [last_interval_tissue[idx] for idx in indices]

        return spark_time, spark_tissue, steady_state_avg
