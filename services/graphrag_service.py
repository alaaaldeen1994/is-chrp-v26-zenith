import sys
import os
import json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# Align path to ensure we can import grn_authority
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from grn_authority import GRNAuthority

# Gene to index mapping for the 12 network nodes
GENE_TO_IDX = {
    'GATA4': 0, 'MEF2C': 1, 'TBX5': 2, 'NKX2-5': 3, 'MYC': 4, 'SNAI1': 5,
    'TNNT2': 6, 'MYH6': 7, 'ACTC1': 8, 'NPPA': 9, 'FOS': 10, 'JUN': 11
}
IDX_TO_GENE = {v: k for k, v in GENE_TO_IDX.items()}


class GaussianKernelAutoencoder(nn.Module):
    """
    Gaussian-kernel Autoencoder to extract gene expression features X 
    from neighborhood matrix G and its transpose G^T (Merge 1 -> Gaussian Kernel -> Merge 2 -> Merge 3).
    """
    def __init__(self, num_nodes, latent_dim=16):
        super().__init__()
        self.num_nodes = num_nodes
        # Input: concatenation of G (row) and G^T (column) -> size 2 * num_nodes
        self.fc_in = nn.Linear(num_nodes * 2, 32)
        self.latent_dim = latent_dim
        self.fc_latent = nn.Linear(32, latent_dim)
        
        # Decoder to reconstruct
        self.fc_dec1 = nn.Linear(latent_dim, 32)
        self.fc_dec2 = nn.Linear(32, num_nodes * 2)

    def gaussian_kernel(self, x, gamma=0.5):
        # Compute pairwise distance matrix
        dist_sq = torch.sum(x**2, dim=1, keepdim=True) + torch.sum(x**2, dim=1) - 2 * torch.matmul(x, x.t())
        return torch.exp(-gamma * dist_sq)

    def forward(self, G):
        # G shape: [num_nodes, num_nodes]
        # Concatenate G and G^T row-wise for each node
        inputs = torch.cat([G, G.t()], dim=1) # [num_nodes, num_nodes * 2]
        x = F.relu(self.fc_in(inputs))
        
        # Apply Gaussian kernel to latent features to capture non-linear similarity
        latent = self.fc_latent(x) # [num_nodes, latent_dim]
        similarity = self.gaussian_kernel(latent) # [num_nodes, num_nodes]
        
        # Reconstruct
        dec = F.relu(self.fc_dec1(latent))
        reconstructed = self.fc_dec2(dec)
        
        return latent, similarity, reconstructed


class CausalGCN(nn.Module):
    """
    Graph Convolutional Network (GCN) with Causal Feature Reconstruction
    utilizing difference vectors (H2 - H1) representing causal information propagation (TE).
    """
    def __init__(self, feature_dim, hidden_dim=16):
        super().__init__()
        self.gcn1 = nn.Linear(feature_dim, hidden_dim)
        self.gcn2 = nn.Linear(hidden_dim, hidden_dim)
        self.causal_fc = nn.Linear(hidden_dim, hidden_dim)

    def forward(self, A, X):
        # A: Adjacency matrix [num_nodes, num_nodes]
        # X: Node features [num_nodes, feature_dim]
        
        # Normalized Laplacian: D^-1/2 * (A + I) * D^-1/2
        I = torch.eye(A.size(0), device=A.device)
        A_tilde = A + I
        deg = torch.sum(A_tilde, dim=1)
        deg_inv_sqrt = torch.pow(deg, -0.5)
        deg_inv_sqrt[torch.isinf(deg_inv_sqrt)] = 0.0
        D_tilde = torch.diag(deg_inv_sqrt)
        
        L = torch.matmul(torch.matmul(D_tilde, A_tilde), D_tilde)
        
        # GCN Layer 1
        h1 = F.relu(self.gcn1(torch.matmul(L, X)))
        # GCN Layer 2
        h2 = F.relu(self.gcn2(torch.matmul(L, h1)))
        
        # Causal Feature Reconstruction mapping (TE GCN1 -> GCN2 emulation)
        causal_reconstruction = F.relu(self.causal_fc(h2 - h1))
        
        # Node embedding Z
        Z = h2 + causal_reconstruction
        return Z


class CausalGRNInferenceModel(nn.Module):
    def __init__(self, num_nodes=12, feature_dim=12, latent_dim=16, hidden_dim=16):
        super().__init__()
        self.autoencoder = GaussianKernelAutoencoder(num_nodes, latent_dim)
        self.gcn = CausalGCN(latent_dim, hidden_dim)

    def forward(self, A, G):
        # 1. Extract expression features X from G via Autoencoder
        X, similarity, _ = self.autoencoder(G)
        
        # 2. Compute GCN embeddings Z
        Z = self.gcn(A, X)
        
        # 3. Link prediction: Preferential Attachment via inner product Z * Z^T
        A_hat = torch.sigmoid(torch.matmul(Z, Z.t()))
        return A_hat, Z


class GraphRAGService:
    def __init__(self):
        # Retrieve biologically verified regulatory links from the GRN Authority
        self.grn_links = GRNAuthority.REGULATORY_LINKS
        
        # Define safety scores for transcription factors
        self.safety_registry = {
            "GATA4": 0.95,
            "TBX5": 0.94,
            "NKX2-5": 0.93,
            "MEF2C": 0.92,
            "POU5F1": 0.70,
            "SOX2": 0.75,
            "KLF4": 0.65,
            "MYC": 0.15,
            "SNAI1": 0.35
        }

        # Instantiate the GCN Causal Inference model
        self.num_nodes = len(GENE_TO_IDX)
        self.model = CausalGRNInferenceModel(num_nodes=self.num_nodes)
        
        # Load weights (mock pre-trained initialization for reproducibility)
        torch.manual_seed(42)
        
        # Initialize default Adjacency matrix A from verified regulatory connections
        A = np.zeros((self.num_nodes, self.num_nodes), dtype=np.float32)
        for tf, targets in self.grn_links.items():
            if tf in GENE_TO_IDX:
                tf_idx = GENE_TO_IDX[tf]
                for target, weight in targets.items():
                    if target in GENE_TO_IDX:
                        target_idx = GENE_TO_IDX[target]
                        A[tf_idx, target_idx] = 1.0
        self.A = torch.tensor(A)

        # Initialize baseline Co-expression Neighborhood matrix G
        G = np.eye(self.num_nodes, dtype=np.float32)
        # Core TFs show positive baseline co-expression synergy
        tf_indices = [0, 1, 2, 3]
        for i in tf_indices:
            for j in tf_indices:
                if i != j:
                    G[i, j] = 0.65
        # Upstream TFs and targets baseline correlations
        G[0, 6] = G[6, 0] = 0.70 # GATA4 - TNNT2
        G[0, 7] = G[7, 0] = 0.60 # GATA4 - MYH6
        G[1, 7] = G[7, 1] = 0.80 # MEF2C - MYH6
        G[2, 8] = G[8, 2] = 0.75 # TBX5 - ACTC1
        G[3, 6] = G[6, 3] = 0.65 # NKX2-5 - TNNT2
        G[3, 9] = G[9, 3] = 0.70 # NKX2-5 - NPPA
        
        # Risk factor paths correlations
        G[4, 10] = G[10, 4] = 0.85 # MYC - FOS
        G[4, 11] = G[11, 4] = 0.80 # MYC - JUN
        G[5, 9] = G[9, 5] = 0.50  # SNAI1 - NPPA
        
        self.G_base = torch.tensor(G)

    def execute_semantic_reasoning(self, query: str, top_k_subgraphs: int = 5, confidence_threshold: float = 0.75) -> dict:
        """
        Executes causal network inference via the GCN model on the query.
        Alters G based on active factors and targets, evaluates safety, and returns dynamic regulatory weights.
        """
        normalized_query = query.upper()
        
        # 1. Detect active genes in query
        detected_tfs = []
        detected_targets = []
        
        all_tfs = list(self.grn_links.keys())
        all_targets = set()
        for targets in self.grn_links.values():
            all_targets.update(targets.keys())
            
        for tf in all_tfs:
            if tf in normalized_query:
                detected_tfs.append(tf)
                
        for target in all_targets:
            if target in normalized_query and target not in detected_tfs:
                detected_targets.append(target)

        # Fallback if query is broad
        if len(detected_tfs) == 0:
            detected_tfs = ["GATA4", "TBX5", "NKX2-5"]
            detected_targets = ["TNNT2", "MYH6"]

        # 2. Perturb neighborhood matrix G based on active genes in query
        # This simulates overexpression / active pathway dynamics in the Autoencoder input
        G_perturbed = self.G_base.clone()
        for gene in detected_tfs + detected_targets:
            if gene in GENE_TO_IDX:
                idx = GENE_TO_IDX[gene]
                # Amplify correlation signals for queried genes
                G_perturbed[idx, :] *= 1.3
                G_perturbed[:, idx] *= 1.3
                G_perturbed[idx, idx] = 1.0
        
        # Clip values to valid correlation range
        G_perturbed = torch.clamp(G_perturbed, -1.0, 1.0)

        # 3. Run GCN forward pass to obtain inferred network A_hat and embeddings
        with torch.no_grad():
            self.model.eval()
            A_hat, Z = self.model(self.A, G_perturbed)
            A_hat_np = A_hat.numpy()

        # 4. Compile interaction pathway description with dynamic predicted weights
        pathway_descriptions = []
        recommended_factors = []
        safety_status = "SAFE"
        myc_prob = 0.01
        safety_alerts = []

        for tf in detected_tfs:
            safety_score = self.safety_registry.get(tf, 0.90)
            recommended_factors.append(tf)
            
            targets_dict = self.grn_links.get(tf, {})
            active_targets = [t for t in detected_targets if t in targets_dict]
            if not active_targets:
                active_targets = list(targets_dict.keys())[:3]
                
            for target in active_targets:
                if tf in GENE_TO_IDX and target in GENE_TO_IDX:
                    tf_idx = GENE_TO_IDX[tf]
                    target_idx = GENE_TO_IDX[target]
                    # Map GCN prediction output (0-1) to regulatory weight scale
                    raw_pred = A_hat_np[tf_idx, target_idx]
                    weight = (raw_pred * 2.0) - 1.0 # rescale to [-1.0, 1.0]
                    # Retain original direction/activation sign
                    orig_sign = 1.0 if targets_dict.get(target, 1.0) >= 0 else -1.0
                    weight = abs(weight) * orig_sign
                else:
                    weight = targets_dict.get(target, 0.50)
                
                action = "activates" if weight >= 0 else "represses"
                pathway_descriptions.append(
                    f"{tf} {action} the promoter of {target} (regulatory weight: {weight:+.2f})."
                )

            # Evaluate safety profile
            if safety_score < 0.50:
                safety_status = "WARNING"
                if tf == "MYC":
                    myc_prob = 0.85
                    safety_alerts.append("Critical Warning: Active MYC pathway increases oncogenic transformation risk.")
                else:
                    myc_prob = max(myc_prob, 0.40)
                    safety_alerts.append(f"Warning: Factor {tf} exhibits high developmental drift risk.")

        interaction_pathway = " ".join(pathway_descriptions)
        if not interaction_pathway:
            interaction_pathway = "No direct active regulatory chains resolved for the query."

        return {
            "recommended_factors": recommended_factors,
            "interaction_pathway": interaction_pathway,
            "safety_risk_assessment": {
                "MYC_activation_probability": myc_prob,
                "status": safety_status,
                "alerts": safety_alerts
            }
        }
