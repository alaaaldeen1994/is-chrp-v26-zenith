import pytest
import respx
import httpx
from zenith import ZenithClient
from zenith.exceptions import (
    AuthenticationError,
    RateLimitError,
    ValidationError,
    APIError,
    ZenithException
)

@pytest.fixture
def base_url():
    return "https://api.zenith-test.com/v1"

@pytest.fixture
def client(base_url):
    return ZenithClient(api_key="test_api_key", base_url=base_url)

def test_client_initialization_error():
    import os
    if "ZENITH_API_KEY" in os.environ:
        del os.environ["ZENITH_API_KEY"]
    with pytest.raises(AuthenticationError):
        ZenithClient(api_key=None)

@respx.mock
def test_client_safety_audit(client, base_url):
    route = respx.post(f"{base_url}/safety/audit").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "success",
                "data": {
                    "approved_factors": ["GATA4", "TBX5"],
                    "blocked_factors": ["OCT4"],
                    "safety_summary": "Passed checks."
                },
                "meta": {"credits_used": 1}
            }
        )
    )
    result = client.safety_audit(factors=["GATA4", "TBX5", "OCT4"])
    assert route.called
    assert result["approved_factors"] == ["GATA4", "TBX5"]
    assert result["blocked_factors"] == ["OCT4"]

@respx.mock
def test_client_fold_sequence(client, base_url):
    route = respx.post(f"{base_url}/structure/fold").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "success",
                "data": {
                    "pdb_data": "ATOM      1  CA  ALA A   1",
                    "metrics": {"length": 30}
                },
                "meta": {"credits_used": 10}
            }
        )
    )
    result = client.fold_sequence("MGDVEKGKK")
    assert route.called
    assert "pdb_data" in result
    assert result["metrics"]["length"] == 30

@respx.mock
def test_client_optimize_lnp(client, base_url):
    route = respx.post(f"{base_url}/lnp/optimize").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "success",
                "data": {
                    "encapsulation_efficiency_percent": 94.2,
                    "particle_size_nm": 82.5,
                    "heart_selectivity_score": 0.88
                },
                "meta": {"credits_used": 1}
            }
        )
    )
    result = client.optimize_lnp(
        molar_ratios={"ionizable": 0.50, "helper": 0.10, "cholesterol": 0.385, "peg": 0.015},
        np_ratio=6.0
    )
    assert route.called
    assert result["encapsulation_efficiency_percent"] == 94.2

@respx.mock
def test_client_rate_limit(client, base_url):
    respx.post(f"{base_url}/safety/audit").mock(
        return_value=httpx.Response(429, json={"message": "API rate limit exceeded"})
    )
    with pytest.raises(RateLimitError):
        client.safety_audit(factors=["GATA4"])

@respx.mock
def test_client_validation_error(client, base_url):
    respx.post(f"{base_url}/safety/audit").mock(
        return_value=httpx.Response(422, json={"detail": "Validation error details"})
    )
    with pytest.raises(ValidationError):
        client.safety_audit(factors=[])

@respx.mock
def test_client_predict_perturbation_async(client, base_url):
    # Mock launch
    launch_route = respx.post(f"{base_url}/predict/perturbation").mock(
        return_value=httpx.Response(
            202,
            json={
                "job_id": "job_012345",
                "status": "pending",
                "status_url": f"{base_url}/jobs/job_012345"
            }
        )
    )
    
    # Mock job status checks (running -> completed)
    status_route = respx.get(f"{base_url}/jobs/job_012345").mock(
        side_effect=[
            httpx.Response(200, json={"status": "success", "data": {"status": "running"}}),
            httpx.Response(200, json={
                "status": "success",
                "data": {
                    "status": "completed",
                    "result": {
                        "cell_count": 50,
                        "download_url": "/jobs/job_012345/download"
                    }
                }
            })
        ]
    )

    result = client.predict_perturbation(
        perturbation_factors={"GATA4": 1.5},
        census_filter="tissue == 'heart'",
        poll_interval=0.1
    )
    assert launch_route.called
    assert status_route.call_count == 2
    assert result["status"] == "completed"
