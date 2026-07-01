import os
import time
from typing import List, Dict, Any, Optional
import httpx
from zenith.exceptions import (
    ZenithException,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    APIError
)

class ZenithClient:
    """
    Official Python Client SDK for the Nilus Lab Zenith Computational Biology Platform.
    """
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://niluslab.com/api/v1"):
        self.api_key = api_key or os.getenv("ZENITH_API_KEY")
        if not self.api_key:
            raise AuthenticationError("API Key is required. Set it during initialization or in the ZENITH_API_KEY environment variable.")
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=httpx.Timeout(30.0, connect=10.0)
        )

    def _request(self, method: str, path: str, **kwargs) -> Any:
        try:
            res = self.client.request(method, path, **kwargs)
            if res.status_code == 401:
                raise AuthenticationError(res.json().get("message", "Invalid or missing API key"))
            elif res.status_code == 429:
                raise RateLimitError(res.json().get("message", "API rate limit exceeded"))
            elif res.status_code == 422:
                raise ValidationError(res.json().get("detail", "Request failed validation"))
            elif not (200 <= res.status_code < 300):
                raise APIError(res.status_code, res.text)
            
            # Successful response
            return res.json()
        except httpx.HTTPError as e:
            raise ZenithException(f"Network request failed: {e}")

    def safety_audit(self, factors: List[str], cpg_methylation: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Evaluates candidate reprogramming factors for safety and calculates methylation age.
        """
        payload = {"factors": factors}
        if cpg_methylation:
            payload["cpg_methylation"] = cpg_methylation
        response = self._request("POST", "/safety/audit", json=payload)
        return response.get("data", response)

    def fold_sequence(self, sequence: str) -> Dict[str, Any]:
        """
        Folds amino acid sequence using ESMFold, returning PDB data.
        """
        response = self._request("POST", "/structure/fold", json={"sequence": sequence})
        return response.get("data", response)

    def optimize_lnp(
        self,
        molar_ratios: Dict[str, float],
        np_ratio: float,
        active_ligand_conjugation: bool = False,
        ligand_density: float = 0.0,
        peg_mw: float = 2000.0
    ) -> Dict[str, Any]:
        """
        Simulates and optimizes Lipid Nanoparticle tropism and efficacy.
        """
        payload = {
            "molar_ratios": molar_ratios,
            "np_ratio": np_ratio,
            "active_ligand_conjugation": active_ligand_conjugation,
            "ligand_density": ligand_density,
            "peg_mw": peg_mw
        }
        response = self._request("POST", "/lnp/optimize", json=payload)
        return response.get("data", response)

    def predict_perturbation(
        self,
        perturbation_factors: Dict[str, float],
        baseline_cell_type: str = "ventricular_myocyte",
        census_filter: Optional[str] = None,
        poll: bool = True,
        poll_interval: float = 2.0
    ) -> Dict[str, Any]:
        """
        Runs transcriptomic perturbation forecasts.
        If census_filter is provided and poll is True, blocks and waits until job completion.
        """
        payload = {
            "baseline_cell_type": baseline_cell_type,
            "perturbation_factors": perturbation_factors
        }
        if census_filter:
            payload["census_filter"] = census_filter
        
        response = self._request("POST", "/predict/perturbation", json=payload)
        
        # If it returns a queued job and polling is enabled
        if census_filter and "job_id" in response and poll:
            job_id = response["job_id"]
            print(f"[Zenith] Async job queued: {job_id}. Polling...")
            return self.poll_job(job_id, interval=poll_interval)
            
        return response

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Checks status of an asynchronous background job.
        """
        response = self._request("GET", f"/jobs/{job_id}")
        return response.get("data", response)

    def poll_job(self, job_id: str, interval: float = 2.0, timeout: float = 60.0) -> Dict[str, Any]:
        """
        Polls job status until complete or failed.
        """
        start = time.time()
        while time.time() - start < timeout:
            status_data = self.get_job_status(job_id)
            status = status_data.get("status")
            if status == "completed":
                return status_data
            elif status == "failed":
                raise ZenithException(f"Job {job_id} failed: {status_data.get('error', 'Unknown error')}")
            time.sleep(interval)
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds.")

    def download_result(self, job_id: str, output_path: str):
        """
        Downloads completed AnnData binary h5ad file and writes it to disk.
        """
        status_data = self.get_job_status(job_id)
        if status_data.get("status") != "completed":
            raise ZenithException(f"Cannot download: job status is '{status_data.get('status')}'")
            
        download_url = status_data.get("result", {}).get("download_url")
        if not download_url:
            # Fallback to direct URL if result is shaped differently
            download_url = f"/jobs/{job_id}/download"
            
        # Handle relative pathing
        if download_url.startswith("/"):
            url = f"{self.base_url}{download_url}"
        else:
            url = download_url
            
        try:
            with self.client.stream("GET", url) as stream:
                stream.raise_for_status()
                with open(output_path, "wb") as f:
                    for chunk in stream.iter_bytes(chunk_size=8192):
                        f.write(chunk)
            print(f"[Zenith] Successfully downloaded AnnData matrix to {output_path}")
        except Exception as e:
            raise ZenithException(f"Failed to download file payload: {e}")

    def subscribe_webhook(self, url: str) -> Dict[str, Any]:
        """
        Subscribes a webhook URL to event updates.
        """
        response = self._request("POST", "/webhooks/subscribe", json={"url": url})
        return response.get("data", response)
