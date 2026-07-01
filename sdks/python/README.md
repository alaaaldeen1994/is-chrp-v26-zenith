# Zenith Python SDK

The official Python client library for interacting with the Nilus Lab Zenith Computational Biology Platform.

## Installation

```bash
pip install zenith-sdk
```

## Quickstart

```python
from zenith import ZenithClient

# Initialize the client with your institutional API Key
client = ZenithClient(api_key="your_api_key", base_url="https://niluslab.com/api/v1")

# 1. Fold a protein sequence
fold_result = client.fold_sequence("MGDVEKGKKIFIMKCSQCHTVEKGGKHKTGPNLHGLFG")
print(f"PDB Data: {fold_result['pdb_data'][:100]}...")

# 2. Run a safety audit on candidate reprogramming factors
audit = client.safety_audit(factors=["GATA4", "TBX5", "OCT4"])
print(f"Approved: {audit['approved_factors']}")
print(f"Blocked: {audit['blocked_factors']}")
```

## Features

- **Pioneer Factor Safety Audits**: Automated oncogenic factor filtering.
- **Lipid Nanoparticle (LNP) Optimization**: Machine learning-based organ tropism optimization.
- **Asynchronous Job Polling**: Sub-second tracking of heavy transcriptomic simulations.
- **AnnData Matrix Serialization**: Automatic binary download mapping.
