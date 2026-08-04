-- ============================================================================
-- NILUS LAB ZENITH PLATFORM — MASTER DATABASE SCHEMA
-- Relational & Graph Database Schema (SQLite / PostgreSQL / DuckDB compatible)
-- Supports Phase 1 to Phase 5 Computational Biology Engines
-- ============================================================================

-- 1. Patients & Clinical Metadata
CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(64) PRIMARY KEY,
    demographic_age FLOAT NOT NULL,
    cell_line_type VARCHAR(128) DEFAULT 'iPSC-derived cardiomyocyte',
    target_indication VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Genomic Variants (Phase 1)
CREATE TABLE IF NOT EXISTS genomic_variants (
    variant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rsid VARCHAR(32) NOT NULL,
    chromosome VARCHAR(8) NOT NULL,
    position INTEGER NOT NULL,
    ref_allele VARCHAR(255) NOT NULL,
    alt_allele VARCHAR(255) NOT NULL,
    maf FLOAT,
    gwas_effect_size FLOAT,
    gene_symbol VARCHAR(64)
);

-- 3. Polygenic Risk Score Analyses (Phase 1)
CREATE TABLE IF NOT EXISTS polygenic_risk_scores (
    prs_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id VARCHAR(64) REFERENCES patients(patient_id),
    phenotype VARCHAR(128) NOT NULL,
    additive_prs_score FLOAT NOT NULL,
    epistatic_prs_score FLOAT NOT NULL,
    population_percentile FLOAT NOT NULL,
    horvath_age_acceleration_years FLOAT NOT NULL,
    top_driver_gene VARCHAR(64),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. AlphaGenome PWM Scans (Phase 1)
CREATE TABLE IF NOT EXISTS pwm_scans (
    scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_rsid VARCHAR(32) NOT NULL,
    chromosome VARCHAR(8),
    position INTEGER,
    tf_symbol VARCHAR(32) NOT NULL,
    ref_score FLOAT NOT NULL,
    alt_score FLOAT NOT NULL,
    delta_pwm FLOAT NOT NULL,
    binding_disrupted BOOLEAN NOT NULL,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. ADMET Compound Safety Profiles (Phase 1)
CREATE TABLE IF NOT EXISTS admet_screens (
    admet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    compound_name VARCHAR(128) NOT NULL,
    smiles TEXT NOT NULL,
    molecular_weight FLOAT,
    logP FLOAT,
    psa FLOAT,
    herg_ic50_um FLOAT,
    lipinski_pass BOOLEAN,
    admet_grade VARCHAR(4) NOT NULL,
    screened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Mendelian Randomisation Causal Inference (Phase 2)
CREATE TABLE IF NOT EXISTS mendelian_randomisations (
    mr_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exposure VARCHAR(128) NOT NULL,
    outcome VARCHAR(128) NOT NULL,
    instrument_count INTEGER NOT NULL,
    mean_f_statistic FLOAT NOT NULL,
    beta_ivw FLOAT NOT NULL,
    p_value_ivw FLOAT NOT NULL,
    p_value_pleiotropy FLOAT NOT NULL,
    has_directional_pleiotropy BOOLEAN NOT NULL,
    causal_verdict VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. MOFA+ Multi-Omics Factor Loadings (Phase 2)
CREATE TABLE IF NOT EXISTS mofa_factor_loadings (
    mofa_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id VARCHAR(64) NOT NULL,
    n_factors INTEGER NOT NULL,
    dominant_factor_id VARCHAR(32) NOT NULL,
    horvath_age_delta_years FLOAT NOT NULL,
    top_target_gene VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Structural Protein-Drug Docking (Phase 3)
CREATE TABLE IF NOT EXISTS docking_simulations (
    docking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_protein VARCHAR(64) NOT NULL,
    pdb_id VARCHAR(32),
    ligand_name VARCHAR(128) NOT NULL,
    smiles TEXT NOT NULL,
    dG_bind_kcal_mol FLOAT NOT NULL,
    predicted_kd_molar FLOAT,
    predicted_ic50_molar FLOAT,
    selectivity_index FLOAT NOT NULL,
    confidence_score FLOAT NOT NULL,
    docked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Prime Editor pegRNA Designs (Phase 3)
CREATE TABLE IF NOT EXISTS prime_editor_designs (
    editor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_gene VARCHAR(64) NOT NULL,
    desired_edit VARCHAR(64) NOT NULL,
    full_pegRNA_sequence TEXT NOT NULL,
    spacer_20nt VARCHAR(32) NOT NULL,
    pbs_length_nt INTEGER NOT NULL,
    rtt_length_nt INTEGER NOT NULL,
    deepprime_efficiency_percent FLOAT NOT NULL,
    folding_dG_kcal_mol FLOAT NOT NULL,
    recommended_mode VARCHAR(32) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. LNP Delivery Formulations (Phase 3)
CREATE TABLE IF NOT EXISTS lnp_formulations (
    lnp_id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_organ VARCHAR(32) NOT NULL,
    payload_type VARCHAR(64) NOT NULL,
    sort_5th_lipid VARCHAR(128) NOT NULL,
    organ_selectivity_percent FLOAT NOT NULL,
    endosomal_escape_percent FLOAT NOT NULL,
    np_ratio FLOAT NOT NULL,
    pKa FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. AlphaZen RL Reprogramming Cocktails (Phase 4)
CREATE TABLE IF NOT EXISTS alphazen_cocktails (
    cocktail_id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_cell_line VARCHAR(128) NOT NULL,
    initial_age_years FLOAT NOT NULL,
    final_age_years FLOAT NOT NULL,
    factors_json TEXT NOT NULL,
    rl_reward FLOAT NOT NULL,
    cardiotoxicity_risk FLOAT NOT NULL,
    oncogenic_risk FLOAT NOT NULL,
    novelty_classification VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. Virtual Adaptive Clinical Trials (Phase 4)
CREATE TABLE IF NOT EXISTS virtual_clinical_trials (
    trial_id INTEGER PRIMARY KEY AUTOINCREMENT,
    intervention_name VARCHAR(255) NOT NULL,
    target_indication VARCHAR(255) NOT NULL,
    cohort_size_N INTEGER NOT NULL,
    recommended_dose_mg FLOAT NOT NULL,
    overall_responder_rate_percent FLOAT NOT NULL,
    adverse_event_rate_percent FLOAT NOT NULL,
    nnt FLOAT NOT NULL,
    nnh FLOAT NOT NULL,
    benefit_risk_ratio FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 13. End-to-End Scientific Agent Dossiers (Phase 5)
CREATE TABLE IF NOT EXISTS scientific_dossiers (
    dossier_id VARCHAR(64) PRIMARY KEY,
    patient_id VARCHAR(64) REFERENCES patients(patient_id),
    target_disease VARCHAR(128) NOT NULL,
    total_execution_time_seconds FLOAT NOT NULL,
    causal_driver_gene VARCHAR(64) NOT NULL,
    dossier_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
