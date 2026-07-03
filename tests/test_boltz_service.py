"""
test_boltz_service.py - Unit tests for Boltz API service
=========================================================
Uses pytest + unittest.mock to test without real API calls.
Run with: poetry run pytest tests/test_boltz_service.py -v
"""

import json
import pytest
from unittest.mock import patch, MagicMock


# ── Validation tests ──────────────────────────────────────────────────────────

def test_validate_valid_protein_dna():
    from services.boltz_service import validate_complex_manifest
    manifest = {
        "entities": [
            {"type": "protein", "value": "MKTIIALSYIFCLVFA", "chain_ids": ["A"]},
            {"type": "dna",     "value": "ATGCAAATGAAT",     "chain_ids": ["B"]},
        ]
    }
    result = validate_complex_manifest(manifest)
    assert result["valid"] is True
    assert result["summary"]["proteins"] == 1
    assert result["summary"]["dna"] == 1
    assert result["errors"] == []


def test_validate_empty_entities():
    from services.boltz_service import validate_complex_manifest
    result = validate_complex_manifest({"entities": []})
    assert result["valid"] is False
    assert any("required" in e.lower() for e in result["errors"])


def test_validate_no_protein():
    from services.boltz_service import validate_complex_manifest
    manifest = {
        "entities": [
            {"type": "dna", "value": "ATGCAAAT", "chain_ids": ["A"]},
        ]
    }
    result = validate_complex_manifest(manifest)
    assert result["valid"] is False
    assert any("protein" in e.lower() for e in result["errors"])


def test_validate_invalid_protein_chars():
    from services.boltz_service import validate_complex_manifest
    manifest = {
        "entities": [
            {"type": "protein", "value": "MKTB2##ZZ", "chain_ids": ["A"]},  # invalid
        ]
    }
    result = validate_complex_manifest(manifest)
    assert result["valid"] is False
    assert any("invalid amino acid" in e.lower() for e in result["errors"])


def test_validate_invalid_dna_chars():
    from services.boltz_service import validate_complex_manifest
    manifest = {
        "entities": [
            {"type": "protein", "value": "MKTII", "chain_ids": ["A"]},
            {"type": "dna",     "value": "ATGBZQ",  "chain_ids": ["B"]},  # invalid
        ]
    }
    result = validate_complex_manifest(manifest)
    assert result["valid"] is False
    assert any("dna" in e.lower() for e in result["errors"])


def test_validate_duplicate_chain_ids():
    from services.boltz_service import validate_complex_manifest
    manifest = {
        "entities": [
            {"type": "protein", "value": "MKTII",    "chain_ids": ["A"]},
            {"type": "dna",     "value": "ATGCAAAT", "chain_ids": ["A"]},  # duplicate
        ]
    }
    result = validate_complex_manifest(manifest)
    assert result["valid"] is False
    assert any("chain_id" in e.lower() or "already used" in e.lower() for e in result["errors"])


def test_validate_injection_attempt():
    from services.boltz_service import validate_complex_manifest
    manifest = {
        "entities": [
            {"type": "protein", "value": "<script>alert(1)</script>", "chain_ids": ["A"]},
        ]
    }
    result = validate_complex_manifest(manifest)
    assert result["valid"] is False


def test_validate_valid_protein_rna_ligand():
    from services.boltz_service import validate_complex_manifest
    manifest = {
        "entities": [
            {"type": "protein",    "value": "MKTIIALSYIF", "chain_ids": ["A"]},
            {"type": "rna",        "value": "AUGCAAAU",    "chain_ids": ["B"]},
            {"type": "ligand_ccd", "value": "ATP",          "chain_ids": ["C"]},
        ]
    }
    result = validate_complex_manifest(manifest)
    assert result["valid"] is True
    assert result["summary"]["proteins"] == 1
    assert result["summary"]["rna"] == 1
    assert result["summary"]["ligands"] == 1


# ── Disabled / missing key tests ──────────────────────────────────────────────

def test_submit_raises_when_api_disabled():
    from services.boltz_service import submit_boltz_job, BoltzDisabledError
    with patch("services.boltz_service.settings") as mock_settings:
        mock_settings.BOLTZ_API_ENABLED = False
        mock_settings.BOLTZ_API_KEY = "sk_bc_ws_test_abc"
        mock_settings.BOLTZ_API_BASE_URL = "https://api.boltz.bio"
        mock_settings.BOLTZ_API_TIMEOUT_SECONDS = 30.0
        with pytest.raises(BoltzDisabledError):
            submit_boltz_job({"entities": [{"type": "protein", "value": "MKTII", "chain_ids": ["A"]}]})


def test_submit_raises_when_no_key():
    from services.boltz_service import submit_boltz_job, BoltzDisabledError
    with patch("services.boltz_service.settings") as mock_settings:
        mock_settings.BOLTZ_API_ENABLED = True
        mock_settings.BOLTZ_API_KEY = ""
        mock_settings.BOLTZ_API_BASE_URL = "https://api.boltz.bio"
        mock_settings.BOLTZ_API_TIMEOUT_SECONDS = 30.0
        with pytest.raises(BoltzDisabledError):
            submit_boltz_job({"entities": [{"type": "protein", "value": "MKTII", "chain_ids": ["A"]}]})


# ── API key security: key never returned in response ──────────────────────────

def test_api_key_not_in_boltz_headers_response():
    """The API key must never be included in any object returned to callers."""
    from services.boltz_service import _boltz_headers, _check_enabled
    with patch("services.boltz_service.settings") as mock_settings:
        mock_settings.BOLTZ_API_ENABLED = True
        mock_settings.BOLTZ_API_KEY = "sk_bc_ws_test_supersecretkey"
        headers = _boltz_headers()
        # Headers used for HTTP call internally - not returned to clients
        # Verify the key IS in the header (needed for API call)
        assert "x-api-key" in headers
        # Verify no accidental leak through sanitize_error
        from services.boltz_service import _sanitize_error
        err = _sanitize_error("Error with x-api-key: sk_bc_ws_test_supersecretkey in message")
        assert "sk_bc_ws_test_supersecretkey" not in err
        assert "****" in err


# ── Synthetic fallback must never be generated ────────────────────────────────

def test_no_synthetic_fallback_on_api_failure():
    """
    On Boltz API failure, the service must raise BoltzJobError.
    It must NEVER return synthetic CIF data.
    """
    from services.boltz_service import get_boltz_job_status, BoltzJobError
    with patch("services.boltz_service.settings") as mock_settings:
        mock_settings.BOLTZ_API_ENABLED = True
        mock_settings.BOLTZ_API_KEY = "sk_bc_ws_test_abc"
        mock_settings.BOLTZ_API_BASE_URL = "https://api.boltz.bio"

        with patch("httpx.Client") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.json.return_value = {"message": "Internal Server Error"}
            mock_response.text = "Internal Server Error"

            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(BoltzJobError):
                get_boltz_job_status("pred_test123")
