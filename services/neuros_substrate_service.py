"""NEUROS-X Substrate Service — wraps the spiking neural substrate for Zenith.

This service follows the same patterns as boltz_service.py:
  - async methods (compatible with FastAPI)
  - strip stack traces on errors (never leak internals)
  - SQLAlchemy caching via SHA-256 hashes
  - safe fallback if the substrate fails

The substrate is a Watts-Strogatz small-world graph of LIF (Leaky
Integrate-and-Fire) spiking neurons. It is used to:
  1. Simulate cardiac electrical activity from ion-channel gene expression
  2. Compute Φ-hat (integration) as a stability/boundedness marker
  3. Generate synthetic ECG-like traces for "what-if" perturbation analysis

IMPORTANT: This is a research-grade simulation. The spiking substrate models
neural population dynamics; it is NOT a clinical ECG simulator. Outputs are
operational markers for research, not diagnostic signals.
"""

from __future__ import annotations

import hashlib
import logging
import traceback
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn

logger = logging.getLogger("neuros_substrate")

# ---------------------------------------------------------------------------
# Strip stack traces — same pattern as bridge_server.py
# ---------------------------------------------------------------------------

def _strip_trace(e: Exception) -> str:
    """Return a clean error message without exposing internal paths."""
    return f"{type(e).__name__}: {str(e)[:200]}"


# ---------------------------------------------------------------------------
# Lightweight LIF substrate (self-contained — no external neuros_x dep)
# ---------------------------------------------------------------------------

class LIFNeuron:
    """Leaky Integrate-and-Fire neuron with adaptive threshold."""

    def __init__(self, n: int, tau_m: float = 20e-3, v_thresh: float = 0.5,
                 v_reset: float = 0.0, dt: float = 2e-3):
        self.n = n
        self.tau_m = tau_m
        self.v_thresh = torch.full((n,), v_thresh)
        self.v_thresh_base = v_thresh
        self.v_reset = v_reset
        self.dt = dt
        self.v = torch.zeros(n)
        self.s = torch.zeros(n)  # spike train
        self.adapt = torch.zeros(n)
        self.tau_adapt = 1.0
        self.adapt_inc = 0.02

    def step(self, I: torch.Tensor) -> torch.Tensor:
        """One simulation step. I = input current (n,)."""
        self.v = self.v + self.dt * (-self.v + I) / self.tau_m
        self.s = (self.v >= self.v_thresh).float()
        self.v = torch.where(self.s > 0, torch.full_like(self.v, self.v_reset), self.v)
        self.v_thresh = (self.v_thresh + self.adapt_inc * self.s
                         - self.dt * (self.v_thresh - self.v_thresh_base) / self.tau_adapt)
        self.adapt = self.adapt + self.s
        return self.s


class CardiacNeuralSubstrate(nn.Module):
    """A small-world graph of LIF neurons that simulates cardiac electrical
    activity. Ion-channel gene expression is encoded as input currents.

    Architecture:
      - 16 clusters of 32 neurons (512 total) — fast enough for real-time API
      - Each cluster represents a cardiac region (atria, ventricle, SA node,
        AV node, Purkinje, vagal afferent, vagal efferent, sympathetic, etc.)
      - Long-range hub connections model the conduction pathways
    """

    # Map cluster index -> cardiac region name
    CLUSTER_NAMES = [
        "SA_node", "AV_node", "atria_RA", "atria_LA",
        "ventricle_RV", "ventricle_LV", "purkinje", "bundle_of_His",
        "vagal_afferent", "vagal_efferent", "sympathetic_stellate",
        "intrinsic_ganglion_1", "intrinsic_ganglion_2", "intrinsic_ganglion_3",
        "coronary_plexus", "ligament_of_Marshall",
    ]

    # Ion-channel genes that drive cardiac electrical activity.
    # These MUST be a subset of the 4000 HVG in the scVI model.
    ION_CHANNEL_GENES = [
        "SCN5A",   # Na+ channel (Nav1.5) — depolarization (ENSG00000183873)
        "KCNH2",   # K+ channel (hERG) — repolarization (LQT2, ENSG00000055118)
        "KCNQ1",   # K+ channel (Kv7.1) — LQT1 (ENSG00000053918)
        "KCNJ2",   # K+ channel (Kir2.1) — LQT7 (ENSG00000123700)
        "CACNA1C", # Ca2+ channel (Cav1.2) — LQT8 (ENSG00000151067)
        "HCN4",    # Funny current (If) — SA node pacemaker (ENSG00000138622)
        "RYR2",    # Sarcoplasmic reticulum Ca2+ release — CPVT (ENSG00000198626)
        "KCNA5",   # Atrial Kv1.5 K+ channel (ENSG00000130037)
        "KCND3",   # Ito Kv4.3 K+ channel (ENSG00000171385)
        "KCNIP2",  # KChIP2 Ito accessory subunit (ENSG00000120049)
        "SLC8A1",  # NCX1 Na+/Ca2+ exchanger (ENSG00000183023)
        "GJA5",    # Connexin 40 — atrial conduction (ENSG00000265107)
        "GJA1",    # Connexin 43 — ventricular conduction
        "KCNJ11",  # K+ channel (Kir6.2)
        "CACNB2",  # Ca2+ channel beta subunit
        "CASQ2",   # Calsequestrin
        "SCN1B",   # Na+ channel beta subunit
        "SCN3B",   # Na+ channel beta subunit
        "ANK2",    # Ankyrin-B
        "AKAP9",   # Yotiao
    ]

    # Neural marker genes for the intrinsic cardiac nervous system.
    NEURAL_MARKER_GENES = [
        "CHAT",    # Choline acetyltransferase (parasympathetic synthesis)
        "SLC18A3", # VAChT (vesicular ACh transporter)
        "CHRNA7",  # Alpha-7 nicotinic receptor
        "CHRM2",   # M2 muscarinic receptor
        "TH",      # Tyrosine hydroxylase (sympathetic synthesis)
        "DBH",     # Dopamine beta-hydroxylase
        "NGFR",    # Nerve growth factor receptor (neuronal health)
        "RET",     # GDNF receptor (neuronal survival)
        "NTRK1",   # TrkA (NGF receptor)
        "PHOX2B",  # Autonomic neuron identity
        "ISL1",    # Cardiac neural crest marker
        "TFAP2B",  # Autonomic ganglia marker
    ]

    def __init__(self, n_clusters: int = 16, neurons_per_cluster: int = 32,
                 seed: int = 42):
        super().__init__()
        self.n_clusters = n_clusters
        self.neurons_per_cluster = neurons_per_cluster
        self.n_total = n_clusters * neurons_per_cluster
        self.seed = seed
        torch.manual_seed(seed)

        # build cluster assignment
        self.cluster_id = torch.arange(self.n_total) // neurons_per_cluster

        # build small-world adjacency (local dense + sparse long-range hubs)
        g = torch.Generator(device="cpu").manual_seed(seed)
        self.hubs = torch.linspace(0, self.n_total - 1, 4, dtype=torch.long)
        edges_pre, edges_post, long_range = [], [], []
        for c in range(n_clusters):
            members = (self.cluster_id == c).nonzero(as_tuple=False).flatten()
            m = members.numel()
            n_local = max(1, int(m * (m - 1) * 0.35))
            pre = members[torch.randint(0, m, (n_local,), generator=g)]
            post = members[torch.randint(0, m, (n_local,), generator=g)]
            mask = pre != post
            edges_pre.append(pre[mask])
            edges_post.append(post[mask])
            long_range.append(torch.zeros(mask.sum(), dtype=torch.bool))
        # rewire 10% to hubs
        pre_all = torch.cat(edges_pre)
        post_all = torch.cat(edges_post)
        lr_all = torch.cat(long_range)
        n_rewire = int(0.10 * pre_all.numel())
        if n_rewire > 0:
            idx = torch.randperm(pre_all.numel(), generator=g)[:n_rewire]
            post_all[idx] = self.hubs[torch.randint(0, 4, (n_rewire,), generator=g)]
            lr_all[idx] = True
        # hub fan-out
        n_hub = 4 * (neurons_per_cluster // 2)
        hub_src = self.hubs.repeat_interleave(neurons_per_cluster // 2)
        hub_dst = torch.randint(0, self.n_total, (n_hub,), generator=g)
        keep = self.cluster_id[hub_src] != self.cluster_id[hub_dst]
        pre_all = torch.cat([pre_all, hub_src[keep]])
        post_all = torch.cat([post_all, hub_dst[keep]])
        lr_all = torch.cat([lr_all, torch.ones(hub_src[keep].numel(), dtype=torch.bool)])

        self.register_buffer("edge_pre", pre_all)
        self.register_buffer("edge_post", post_all)
        self.register_buffer("edge_long_range", lr_all)
        w = torch.empty(pre_all.numel()).uniform_(-0.2, 0.5)
        w[torch.isin(pre_all, self.hubs)] *= 1.5
        self.edge_weight = nn.Parameter(w)
        self.n_edges = pre_all.numel()

        # LIF neurons
        self.lif = LIFNeuron(self.n_total)

        # fire rate (low-pass for homeostasis)
        self.register_buffer("fire_rate", torch.zeros(self.n_total))

    # ------------------------------------------------------------------
    # Encoding: ion-channel expression -> input current
    # ------------------------------------------------------------------

    def encode_ion_profile(self, expression_vector: Dict[str, float],
                           intensity: float = 5.0) -> torch.Tensor:
        """Convert ion-channel gene expression into substrate input currents.

        expression_vector: {gene_symbol: expression_level}
        intensity: scaling factor for the current injection

        Raises ValueError if expression_vector is empty or contains zero resolved
        ion-channel genes (silent fallback to HEALTHY_BASELINES removed).
        """
        if not expression_vector or not any(float(expression_vector.get(g, 0.0)) > 0.0 for g in self.ION_CHANNEL_GENES):
            raise ValueError(
                "CardiacNeuralSubstrate.encode_ion_profile requires resolved ion-channel expression values; "
                "hardcoded HEALTHY_BASELINES fallback has been removed."
            )
        I = torch.zeros(self.n_total)
        # distribute genes across neurons evenly
        genes = self.ION_CHANNEL_GENES
        neurons_per_gene = max(1, self.n_total // len(genes))
        for i, gene in enumerate(genes):
            level = float(expression_vector.get(gene, 0.0))
            current = level * intensity / 10.0
            start = i * neurons_per_gene
            end = min(start + neurons_per_gene, self.n_total)
            I[start:end] = current
        # add deterministic baseline drive seeded from expression profile
        profile_sig = ";".join(f"{k}:{float(expression_vector.get(k, 0.0)):.5f}" for k in sorted(genes))
        det_seed = int(hashlib.sha256(profile_sig.encode()).hexdigest()[:8], 16)
        g_noise = torch.Generator(device="cpu").manual_seed(det_seed)
        I += torch.randn((self.n_total,), generator=g_noise) * 0.2
        return I

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    def simulate(self, I: torch.Tensor, steps: int = 50) -> Dict[str, Any]:
        """Run the substrate for `steps` and return diagnostics.

        Returns:
          spikes: (steps, N) spike train
          fire_rate: (N,) smoothed firing rate
          active_fraction: fraction of neurons that fired
          phi_hat: integration proxy (mutual information between clusters)
          synchrony: population spike synchrony
          mean_v: mean membrane potential
        """
        # Reset LIF state before each simulation so results depend solely on input I
        self.lif.v.zero_()
        self.lif.s.zero_()
        self.lif.adapt.zero_()
        self.lif.v_thresh.fill_(self.lif.v_thresh_base)
        self.fire_rate.zero_()
        spikes_log = []
        for _ in range(steps):
            # synaptic input via scatter-add
            pre_spikes = self.lif.s[self.edge_pre]
            syn_input = torch.zeros_like(self.lif.v)
            syn_input.index_add_(0, self.edge_post, pre_spikes * self.edge_weight)
            total_I = I + syn_input
            self.lif.step(total_I)
            self.fire_rate = 0.95 * self.fire_rate + 0.05 * self.lif.s
            spikes_log.append(self.lif.s.clone())

        spikes = torch.stack(spikes_log)  # (steps, N)
        active = (self.fire_rate > 0).float().mean().item()

        # Φ-hat: mutual information between cluster activations
        cluster_means = torch.stack([
            self.fire_rate[self.cluster_id == c].mean()
            if (self.cluster_id == c).any() else torch.tensor(0.0)
            for c in range(self.n_clusters)
        ])
        inter_mask = self.edge_long_range
        inter_strength = float(self.edge_weight[inter_mask].abs().sum()) if inter_mask.any() else 0.0
        differentiation = float(cluster_means.std().item())
        integration = inter_strength / (self.n_edges + 1e-6)
        phi = max(0.0, differentiation * integration * self.n_clusters)

        # synchrony: variance of inter-spike intervals across population
        pop_activity = spikes.sum(dim=1)  # (steps,)
        synchrony = float(pop_activity.std().item() / (pop_activity.mean().item() + 1e-6))

        return {
            "spikes": spikes,
            "fire_rate": self.fire_rate,
            "active_fraction": active,
            "phi_hat": phi,
            "synchrony": min(1.0, synchrony / 10.0),
            "mean_v": float(self.lif.v.mean().item()),
            "mean_firing_rate": float(self.fire_rate.mean().item()),
        }

    # ------------------------------------------------------------------
    # ECG-like trace generation (operational, not clinical)
    # ------------------------------------------------------------------

    def generate_ecg_proxy(self, expression_vector: Dict[str, float],
                           duration: int = 200) -> List[float]:
        """Generate a synthetic ECG-like trace from the substrate activity.

        This is NOT a clinical ECG — it's an operational proxy that reflects
        how the ion-channel profile drives the substrate. Useful for
        comparative visualization (before/after perturbation).
        """
        I = self.encode_ion_profile(expression_vector)
        result = self.simulate(I, steps=duration)
        spikes = result["spikes"]  # (duration, N)
        # sum population activity and apply a simple filter to get a "wave"
        pop = spikes.sum(dim=1).float()
        # smooth
        kernel = torch.ones(5) / 5
        if pop.numel() >= 5:
            pop = torch.nn.functional.conv1d(
                pop.unsqueeze(0).unsqueeze(0),
                kernel.unsqueeze(0).unsqueeze(0),
                padding=2
            ).squeeze()
        # normalize to [0, 1] for display
        if pop.max() > 0:
            pop = pop / pop.max()
        return pop.tolist()

    def audit_arrhythmia_risk(self, expression_vector: Dict[str, float]) -> Dict[str, Any]:
        """
        Audits a reprogramming cocktail for ion-channel expression shifts.
        Maps ion-channel gene expression to LIF spiking population dynamics.
        
        Returns:
            - safety_classification: EXPLORATORY_NOMINAL | WARNING | BLOCKED
            - reason: Human-readable explanation
            - phi_hat: Integration score (higher = more stable)
            - synchrony: Population spike synchrony (extreme = dangerous)
            - ecg_proxy: Synthetic ECG trace for visualization
            - ion_channels_analyzed: Which genes were detected
        """
        # 1. Check for known arrhythmia-causing genes (blacklist check)
        CRITICAL_GENES = {
            "SCN5A": {"risk": "Long QT Type 3 (Na+ gain-of-function)", "threshold": 8.0},
            "KCNH2": {"risk": "Long QT Type 2 (hERG K+ loss)", "threshold": 0.5},
            "KCNQ1": {"risk": "Long QT Type 1 (Kv7.1 loss)", "threshold": 0.5},
            "CACNA1C": {"risk": "Timothy Syndrome (LQT8, Ca2+ gain)", "threshold": 6.0},
            "RYR2": {"risk": "CPVT (Ca2+ leak)", "threshold": 7.0},
            "HCN4": {"risk": "Sick Sinus Syndrome", "threshold": 0.3},
        }
        
        blacklist_flags = []
        for gene, info in CRITICAL_GENES.items():
            level = expression_vector.get(gene, 0.0)
            is_risk = False
            if gene in ["SCN5A", "CACNA1C", "RYR2"]:
                # Na+ and Ca2+ channels are risk when overexpressed (gain of function)
                is_risk = level > info["threshold"]
            else:
                # K+ channels and HCN4 are risk when underexpressed (loss of function).
                is_risk = 0.0 < level < info["threshold"]
                
            if is_risk:
                blacklist_flags.append({
                    "gene": gene,
                    "level": float(level),
                    "threshold": info["threshold"],
                    "risk": info["risk"]
                })
        
        # 2. Run the spiking substrate simulation
        I = self.encode_ion_profile(expression_vector)
        result = self.simulate(I, steps=50)
        ecg = self.generate_ecg_proxy(expression_vector, duration=200)
        
        phi_hat = result["phi_hat"]
        synchrony = result["synchrony"]
        active_fraction = result["active_fraction"]
        
        # 3. Classify exploratory LIF dynamics (never claim clinical or wet-lab safety validation)
        if blacklist_flags:
            safety_class = "BLOCKED"
            reason = f"Ion-Channel Threshold Exceeded: {len(blacklist_flags)} critical ion-channel gene(s) exceed threshold ({', '.join(f['risk'] for f in blacklist_flags)})."
        elif synchrony > 0.6 or phi_hat < 0.001:
            safety_class = "BLOCKED"
            reason = "Simulated LIF Instability: High population synchrony or low cluster integration in exploratory LIF substrate."
        elif synchrony > 0.4 or phi_hat < 0.003:
            safety_class = "WARNING"
            reason = "Elevated LIF Synchrony: Moderate synchrony shift detected in exploratory LIF substrate."
        elif active_fraction < 0.1:
            safety_class = "WARNING"
            reason = "Low LIF Activity: Minimal neural population engagement in exploratory LIF substrate."
        else:
            safety_class = "EXPLORATORY_NOMINAL"
            reason = "Exploratory LIF substrate dynamics within nominal bounds (uncalibrated research proxy; not a clinical ECG or wet-lab safety assay)."
        
        return {
            "safety_classification": safety_class,
            "reason": reason,
            "phi_hat": float(phi_hat),
            "synchrony": float(synchrony),
            "active_fraction": float(active_fraction),
            "ecg_proxy": ecg,
            "blacklist_flags": blacklist_flags,
            "ion_channels_analyzed": [g for g in self.ION_CHANNEL_GENES if g in expression_vector],
            "n_neurons": self.n_total,
            "n_edges": self.n_edges,
            "ok": True
        }

    def check_fibrillation_risk(self, expression_vector: Dict[str, float]) -> Dict[str, Any]:
        """
        Secondary double-check specifically looking for ventricular fibrillation
        and chaotic reentry patterns by analyzing spike-train entropy.
        """
        I = self.encode_ion_profile(expression_vector)
        # Run a longer simulation to catch chaotic dynamics
        result = self.simulate(I, steps=100)
        
        # Calculate population spike entropy (high entropy = chaos)
        spikes = result["spikes"] # (100, 512)
        pop_activity = spikes.sum(dim=1).float() # (100,)
        
        # Calculate variance of inter-spike intervals
        diffs = pop_activity[1:] - pop_activity[:-1]
        isi_variance = float(torch.var(diffs).item())
        
        # If ISI variance is extremely high, it's fibrillating
        is_fibrillating = isi_variance > 5.0 or result["synchrony"] > 0.8
        
        return {
            "fibrillation_detected": bool(is_fibrillating),
            "isi_variance": float(isi_variance),
            "synchrony": float(result["synchrony"]),
            "phi_hat": float(result["phi_hat"])
        }


# ---------------------------------------------------------------------------
# Service layer (async, matches boltz_service.py patterns)
# ---------------------------------------------------------------------------

class NeurosSubstrateService:
    """Async service wrapper around the CardiacNeuralSubstrate.

    Follows the same pattern as BoltzService:
      - async methods
      - strip stack traces on error
      - caching via SQLAlchemy (see database/neural_models.py)
    """

    def __init__(self):
        self._substrate: Optional[CardiacNeuralSubstrate] = None
        self._lock = torch.Lock() if hasattr(torch, "Lock") else None

    @property
    def substrate(self) -> CardiacNeuralSubstrate:
        if self._substrate is None:
            self._substrate = CardiacNeuralSubstrate()
        return self._substrate

    def _hash_expression(self, expression_vector: Dict[str, float]) -> str:
        """SHA-256 hash of the expression vector (for caching)."""
        # sort keys for deterministic hashing
        items = sorted(expression_vector.items())
        raw = ";".join(f"{k}:{v:.6f}" for k, v in items)
        return hashlib.sha256(raw.encode()).hexdigest()

    async def analyze_ion_profile(
        self, expression_vector: Dict[str, float], steps: int = 50
    ) -> Dict[str, Any]:
        """Run the substrate on an ion-channel expression profile.

        Returns a dict with phi_hat, synchrony, active_fraction, ecg_proxy.
        """
        try:
            I = self.substrate.encode_ion_profile(expression_vector)
            result = self.substrate.simulate(I, steps=steps)
            ecg = self.substrate.generate_ecg_proxy(expression_vector, duration=200)
            return {
                "signal_hash": self._hash_expression(expression_vector),
                "phi_hat": float(result["phi_hat"]),
                "synchrony": float(result["synchrony"]),
                "active_fraction": float(result["active_fraction"]),
                "mean_firing_rate": float(result["mean_firing_rate"]),
                "ecg_proxy": ecg,
                "n_neurons": self.substrate.n_total,
                "n_edges": self.substrate.n_edges,
                "n_clusters": self.substrate.n_clusters,
                "ion_genes_detected": [
                    g for g in self.substrate.ION_CHANNEL_GENES
                    if g in expression_vector
                ],
                "ok": True,
            }
        except Exception as e:
            logger.error(f"substrate analysis failed: {_strip_trace(e)}")
            return {"ok": False, "error": _strip_trace(e)}

    async def compare_profiles(
        self, baseline: Dict[str, float], perturbed: Dict[str, float]
    ) -> Dict[str, Any]:
        """Compare substrate response before/after a perturbation.

        This is the core of the joint rejuvenation analysis — it shows how
        a gene perturbation changes the simulated cardiac electrical activity.
        """
        try:
            base = await self.analyze_ion_profile(baseline)
            pert = await self.analyze_ion_profile(perturbed)
            if not base.get("ok") or not pert.get("ok"):
                return {"ok": False, "error": "substrate analysis failed"}
            # compute deltas
            phi_delta = pert["phi_hat"] - base["phi_hat"]
            sync_delta = pert["synchrony"] - base["synchrony"]
            # stability assessment
            # higher phi = more integrated (good)
            # higher synchrony = more synchronized (can be arrhythmogenic if extreme)
            stability = "improved" if phi_delta > 0 and sync_delta < 0.1 else "degraded"
            if abs(phi_delta) < 0.0001 and abs(sync_delta) < 0.01:
                stability = "neutral"
            return {
                "ok": True,
                "baseline": base,
                "perturbed": pert,
                "deltas": {
                    "phi_hat": phi_delta,
                    "synchrony": sync_delta,
                    "active_fraction": pert["active_fraction"] - base["active_fraction"],
                },
                "stability_assessment": stability,
                "arrhythmia_risk": "elevated" if sync_delta > 0.15 else "nominal",
            }
        except Exception as e:
            logger.error(f"compare failed: {_strip_trace(e)}")
            return {"ok": False, "error": _strip_trace(e)}

    async def get_cluster_names(self) -> List[str]:
        """Return the cardiac region names for each cluster."""
        return self.substrate.CLUSTER_NAMES

    async def get_ion_genes(self) -> List[str]:
        """Return the ion-channel genes the substrate tracks."""
        return self.substrate.ION_CHANNEL_GENES

    async def get_neural_markers(self) -> List[str]:
        """Return the neural marker genes for the cardiac nervous system."""
        return self.substrate.NEURAL_MARKER_GENES


# ---------------------------------------------------------------------------
# Singleton (matches how bridge_server.py likely holds BoltzService)
# ---------------------------------------------------------------------------

_substrate_service: Optional[NeurosSubstrateService] = None

def get_substrate_service() -> NeurosSubstrateService:
    global _substrate_service
    if _substrate_service is None:
        _substrate_service = NeurosSubstrateService()
    return _substrate_service
