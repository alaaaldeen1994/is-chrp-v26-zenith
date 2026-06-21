"""
step3_train_scvi.py
===================
Production-grade scVI foundation model training.

V29.0 UPGRADE: Scaled for 3.2M+ cardiac cells.
  - n_latent increased from 45 to 64.
  - n_hidden increased from 512 to 1024.
  - n_layers increased from 3 to 4.
  - batch_size increased from 256 to 2048 (for A100 80GB VRAM).
  - Google Drive checkpoint auto-save every 10 epochs.
  - Auto-detects GPU (CUDA) and falls back to CPU gracefully.

Architecture decisions (scientifically justified):
  - n_latent = 64:
      Scaled up from 45 to capture the finer transcriptional states
      present across 3.2M cells from multiple cardiac atlases.
      64 dimensions provide sufficient capacity for rare cell
      subtypes (e.g., Purkinje fibers, pericytes) without
      over-compressing.

  - n_hidden = 1024:
      Doubled from 512 to prevent underfitting on 3.2M cells.
      At this dataset scale, a narrow encoder bottleneck would
      lose critical non-linear gene-gene relationships.

  - n_layers = 4:
      Increased from 3. Four encoder/decoder layers allow the
      model to learn deeper compositional features across the
      expanded tissue and donor diversity.

  - gene_likelihood = "nb" (Negative Binomial):
      Gold standard for scRNA-seq count data. Unchanged from v28.0.
      Reference: Lopez et al. 2018, Nat Methods.

  - dispersion = "gene":
      Gene-specific dispersion parameters. Unchanged from v28.0.

  - encode_covariates = True:
      Injects batch covariates into the encoder to improve integration.

  - batch_key = "dataset_id":
      Primary batch = dataset of origin (most biologically meaningful
      source of technical variation in multi-study integration).

  - categorical_covariate_keys = ["suspension_type"]:
      Secondary covariate: nucleus vs cell suspension (major technical
      effect in single-nucleus vs single-cell RNA-seq).
      Note: donor_id can be added when training on GPU with sufficient
      VRAM; it significantly slows CPU training.

Training configuration (GPU-optimised for A100 80GB):
  - max_epochs = 150: Sufficient for convergence at 3.2M cells.
    Early stopping prevents overfitting.
  - batch_size = 2048: Large batch to maximise A100 throughput.
  - plan_kwargs:
      lr = 1e-3 (Adam default, appropriate for scVI)
      weight_decay = 1e-6 (mild L2 regularisation)
  - early_stopping_patience = 20: Tighter than v28.0 (was 30) because
    the larger dataset provides more stable gradients.

References:
  Lopez et al. 2018. Deep generative modeling for single-cell transcriptomics.
    Nature Methods, 15, 1053–1058.
  Gayoso et al. 2022. A Python library for probabilistic analysis of
    single-cell omics data. Nature Biotechnology, 40, 163–166.
  Luecken et al. 2022. Benchmarking atlas-level data integration in
    single-cell genomics. Nature Methods, 19, 41–50.
"""

import os
import sys
import json
import time
import datetime
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
import scanpy as sc
import scvi
import torch

# ── Configuration ─────────────────────────────────────────────────────────────
IN_FILE       = "data/foundation/cardiac_preprocessed.h5ad"
MODEL_OUT_DIR = "models/zenith_foundation_v29"
METRICS_FILE  = "data/foundation/training_metrics.json"

# Architecture (v29.0 — scaled for 3.2M cells)
N_LATENT      = 64
N_HIDDEN      = 1024
N_LAYERS      = 4
GENE_LIKELIHOOD = "nb"   # negative binomial

# Training
import argparse
parser = argparse.ArgumentParser(description="Zenith v29.0 scVI Foundation Model Training")
parser.add_argument("--epochs", type=int, default=150, help="Number of training epochs (default: 150)")
parser.add_argument("--subsample", type=int, default=0, help="Subsample cells to this count for speed (default: 0 = no subsample)")
parser.add_argument("--batch-size", type=int, default=2048, help="Training batch size (default: 2048 for A100)")
parser.add_argument("--checkpoint-dir", type=str, default="", help="Directory to save checkpoints (e.g. Google Drive path)")
args, unknown = parser.parse_known_args()

MAX_EPOCHS    = args.epochs
SUBSAMPLE     = args.subsample
BATCH_SIZE    = args.batch_size
CHECKPOINT_DIR = args.checkpoint_dir

LEARNING_RATE = 1e-3
WEIGHT_DECAY  = 1e-6
EARLY_STOP    = True if MAX_EPOCHS > 10 else False
PATIENCE      = 20

# Batch covariates
BATCH_KEY     = "dataset_id"
CAT_COVARIATES = ["suspension_type"]

# ── Detect compute device ────────────────────────────────────────────────────
def detect_device():
    """Detect the best available compute device."""
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_mem / 1e9
        print(f"  Device: GPU — {gpu_name} ({gpu_mem:.1f} GB VRAM)")
        return "cuda"
    else:
        print(f"  Device: CPU (no GPU detected)")
        return "cpu"


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    start_time = datetime.datetime.utcnow()

    print("=" * 70)
    print("  Zenith Foundation Model v29.0 — scVI Training")
    print(f"  Target: 3.2M+ Cardiac Cells | Architecture: {N_HIDDEN}h × {N_LAYERS}L × {N_LATENT}z")
    print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 70)

    device = detect_device()

    # ── 1. Load preprocessed data ──────────────────────────────────
    print(f"\n[1/5] Loading preprocessed data: {IN_FILE}")
    adata = sc.read_h5ad(IN_FILE)
    print(f"  Shape: {adata.n_obs:,} × {adata.n_vars:,}")

    # For fast integration test runs, subsample cells
    if MAX_EPOCHS <= 10 and adata.n_obs > 10_000:
        np.random.seed(42)
        idx = np.random.choice(adata.n_obs, size=10_000, replace=False)
        idx.sort()
        adata = adata[idx].copy()
        print(f"  ✓ Subsampled to 10,000 cells for fast integration test (epochs={MAX_EPOCHS})")
    elif SUBSAMPLE > 0 and adata.n_obs > SUBSAMPLE:
        np.random.seed(42)
        idx = np.random.choice(adata.n_obs, size=SUBSAMPLE, replace=False)
        idx.sort()
        adata = adata[idx].copy()
        print(f"  ✓ Subsampled to {SUBSAMPLE:,} cells (epochs={MAX_EPOCHS})")

    # Verify batch columns
    for col in [BATCH_KEY] + CAT_COVARIATES:
        if col not in adata.obs.columns:
            print(f"  WARNING: batch column '{col}' not found — adding 'unknown'")
            adata.obs[col] = "unknown"
        # Cast to categorical
        adata.obs[col] = pd.Categorical(adata.obs[col].astype(str))

    n_batches = adata.obs[BATCH_KEY].nunique()
    print(f"  Batches ({BATCH_KEY}): {n_batches}")
    print(f"  Cell types: {adata.obs.get('cell_type', pd.Series()).nunique()}")

    # ── 2. Setup scVI ──────────────────────────────────────────────
    print(f"\n[2/5] Configuring scVI model...")

    scvi.model.SCVI.setup_anndata(
        adata,
        layer="counts",                    # raw counts (required)
        batch_key=BATCH_KEY,
        categorical_covariate_keys=CAT_COVARIATES,
    )

    model = scvi.model.SCVI(
        adata,
        n_hidden=N_HIDDEN,
        n_latent=N_LATENT,
        n_layers=N_LAYERS,
        gene_likelihood=GENE_LIKELIHOOD,
        encode_covariates=True,
        deeply_inject_covariates=False,
        use_layer_norm="both",
        use_batch_norm="none",
    )

    # Print model summary
    n_params = sum(p.numel() for p in model.module.parameters())
    print(f"\n  Model architecture (v29.0):")
    print(f"    Gene likelihood:      {GENE_LIKELIHOOD} (negative binomial)")
    print(f"    Latent dimensions:    {N_LATENT}")
    print(f"    Hidden units:         {N_HIDDEN}")
    print(f"    Encoder/decoder depth:{N_LAYERS} layers")
    print(f"    Trainable parameters: {n_params:,}")
    print(f"    Batch key:            {BATCH_KEY}")
    print(f"    Categorical covars:   {CAT_COVARIATES}")
    print(f"    Device:               {device.upper()}")

    # ── 3. Configure checkpointing ─────────────────────────────────
    trainer_kwargs = {}

    if CHECKPOINT_DIR:
        from pytorch_lightning.callbacks import ModelCheckpoint
        os.makedirs(CHECKPOINT_DIR, exist_ok=True)
        checkpoint_callback = ModelCheckpoint(
            dirpath=CHECKPOINT_DIR,
            filename="zenith_v29_epoch_{epoch:03d}",
            every_n_epochs=10,
            save_top_k=-1,  # Keep all checkpoints
        )
        trainer_kwargs["callbacks"] = [checkpoint_callback]
        print(f"\n  ✓ Checkpoint auto-save enabled → {CHECKPOINT_DIR}")
        print(f"    Saving every 10 epochs to protect against session drops")

    # ── 4. Training ────────────────────────────────────────────────
    print(f"\n[3/5] Training (max {MAX_EPOCHS} epochs, batch_size={BATCH_SIZE}, "
          f"early stopping patience={PATIENCE})...")

    if device == "cuda":
        print(f"  GPU training — estimated time: 18–22 hours for 3.2M cells")
    else:
        print(f"  ⚠ CPU training — this will be VERY slow for 3.2M cells.")
        print(f"    Recommendation: Use Google Colab Pro (A100) or RunPod.")

    t_train_start = time.time()

    train_kwargs = {
        "max_epochs": MAX_EPOCHS,
        "batch_size": BATCH_SIZE,
        "early_stopping": EARLY_STOP,
        "early_stopping_patience": PATIENCE,
        "early_stopping_monitor": "elbo_validation",
        "check_val_every_n_epoch": 5,
        "train_size": 0.90,
        "plan_kwargs": {
            "lr":            LEARNING_RATE,
            "weight_decay":  WEIGHT_DECAY,
            "eps":           1e-8,
        },
    }
    if trainer_kwargs:
        train_kwargs["trainer_kwargs"] = trainer_kwargs

    model.train(**train_kwargs)

    t_train_end = time.time()
    train_elapsed_h = (t_train_end - t_train_start) / 3600
    print(f"\n  Training complete in {train_elapsed_h:.2f} hours")

    # ── 5. Extract training history ────────────────────────────────
    print(f"\n[4/5] Extracting training metrics...")
    history = model.history

    # Final ELBO values
    train_elbo_final = float(history["elbo_train"].iloc[-1, 0])
    val_elbo_final   = float(history["elbo_validation"].iloc[-1, 0]) \
        if "elbo_validation" in history and len(history["elbo_validation"]) > 0 else None

    n_epochs_trained = len(history["elbo_train"])
    print(f"  Epochs trained:          {n_epochs_trained}")
    print(f"  Final train ELBO:        {train_elbo_final:.2f}")
    if val_elbo_final:
        print(f"  Final validation ELBO:   {val_elbo_final:.2f}")

    # Save ELBO curve for monitoring
    history_dfs = []
    if "elbo_train" in history:
        history_dfs.append(history["elbo_train"])
    if "elbo_validation" in history:
        history_dfs.append(history["elbo_validation"])

    if history_dfs:
        elbo_df = pd.concat(history_dfs, axis=1)
        elbo_df.index.name = "epoch"
        elbo_df.reset_index(inplace=True)
    else:
        elbo_df = pd.DataFrame()

    elbo_out = "data/foundation/training_elbo.csv"
    elbo_df.to_csv(elbo_out, index=False)
    print(f"  ELBO curve saved → {elbo_out}")

    # ── 6. Save model ──────────────────────────────────────────────
    print(f"\n[5/5] Saving model to {MODEL_OUT_DIR}...")
    os.makedirs(MODEL_OUT_DIR, exist_ok=True)
    model.save(MODEL_OUT_DIR, overwrite=True)
    print(f"  ✓ Model weights saved")

    # Save a reference AnnData with the training var schema
    ref_adata = sc.AnnData(
        X   = np.zeros((1, adata.n_vars), dtype=np.float32),
        var = adata.var.copy(),
    )
    ref_adata.write_h5ad(os.path.join(MODEL_OUT_DIR, "var_schema.h5ad"))
    print(f"  ✓ Gene schema saved (for future dataset alignment)")

    # Also save to checkpoint dir if specified (Google Drive backup)
    if CHECKPOINT_DIR:
        backup_dir = os.path.join(CHECKPOINT_DIR, "final_model")
        os.makedirs(backup_dir, exist_ok=True)
        model.save(backup_dir, overwrite=True)
        print(f"  ✓ Final model also backed up to {backup_dir}")

    end_time = datetime.datetime.utcnow()
    total_elapsed = (end_time - start_time).total_seconds() / 3600

    # Save full training metrics
    metrics = {
        "timestamp_utc":         end_time.strftime("%Y-%m-%d %H:%M UTC"),
        "model_version":         "zenith_foundation_v29",
        "pipeline_version":      "v29.0 (3.2M Census)",
        "n_cells_trained":       int(adata.n_obs),
        "n_genes":               int(adata.n_vars),
        "n_batches":             int(n_batches),
        "architecture": {
            "n_latent":          N_LATENT,
            "n_hidden":          N_HIDDEN,
            "n_layers":          N_LAYERS,
            "gene_likelihood":   GENE_LIKELIHOOD,
        },
        "training": {
            "max_epochs":        MAX_EPOCHS,
            "epochs_trained":    int(n_epochs_trained),
            "batch_size":        BATCH_SIZE,
            "learning_rate":     LEARNING_RATE,
            "early_stopping":    EARLY_STOP,
            "patience":          PATIENCE,
            "train_val_split":   "90/10",
            "device":            device,
        },
        "performance": {
            "final_train_elbo":  train_elbo_final,
            "final_val_elbo":    val_elbo_final,
            "training_time_h":   round(train_elapsed_h, 2),
        },
        "model_dir":             MODEL_OUT_DIR,
        "ownership":             "100% property of project owner",
        "training_data_license": "CC BY 4.0 — CZI CELLxGENE Census",
        "model_license":         "Proprietary — no restrictions",
    }
    with open(METRICS_FILE, "w") as f:
        json.dump(metrics, f, indent=2)

    print("\n" + "=" * 70)
    print("  ✅  TRAINING COMPLETE (v29.0)")
    print(f"     Cells trained on:  {adata.n_obs:,}")
    print(f"     Genes:             {adata.n_vars:,}")
    print(f"     Epochs:            {n_epochs_trained}")
    print(f"     Final ELBO:        {train_elbo_final:.2f}")
    print(f"     Train time:        {train_elapsed_h:.2f} h")
    print(f"     Model saved to:    {MODEL_OUT_DIR}/")
    print(f"     Ownership:         100% YOURS — no CZI model used")
    print("=" * 70)
    print("\nNext step: python step4_validate.py")


if __name__ == "__main__":
    main()
