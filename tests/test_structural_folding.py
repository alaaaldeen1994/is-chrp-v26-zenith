import sys
import os
from unittest.mock import MagicMock, patch
import httpx

# Align path to import from workspace root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.structural_folder import StructuralFolderService
from config.settings import settings

def test_esmfold_live_success():
    service = StructuralFolderService()
    # Build a mock PDB matching 15 residues (MAEVPRRLLLLLLLL)
    atoms = []
    for i in range(1, 16):
        atoms.append(f"ATOM  {i:5}  CA  ALA A{i:4}       1.000   2.000   3.000  1.00 85.00           C")
    mock_pdb = "HEADER    PROTEIN BINDING                         02-JUL-26\n" + "\n".join(atoms) + "\nTER\nEND"
    
    # Mock httpx client post to return a successful 200 response with PDB contents
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = mock_pdb
    
    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        result = service.fold_sequence("MAEVPRRLLLLLLLL")
        
        assert result["status"] == "success"
        assert result["source"] == "ESMFold-Live"
        assert result["fallback_used"] is False
        assert result["provider_status"] == "ok"
        assert "ATOM" in result["pdb_data"]
        assert result["metrics"]["length"] == 15
        assert result["metrics"]["predicted_lddt"] == 0.85
        
        # Verify post arguments
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == settings.ESMFOLD_API_URL
        assert kwargs["content"] == "MAEVPRRLLLLLLLL"

def test_esmfold_provider_failure():
    service = StructuralFolderService()
    
    # Mock httpx client post to throw a connection error
    with patch("httpx.Client.post", side_effect=httpx.ConnectError("Connection timed out")) as mock_post:
        result = service.fold_sequence("MAEVPRRLLLLLLLL")
        
        assert result["status"] == "success"
        assert result["source"] == "Zenith-Synthetic-Fallback"
        assert result["fallback_used"] is True
        assert result["provider_status"] == "external_provider_failed"
        assert "Connection Failed" in result["provider_error"]
        assert "warning" in result
        assert "ATOM" in result["pdb_data"]
        assert result["metrics"]["predicted_lddt"] == 50.0

def test_esmfold_invalid_input():
    service = StructuralFolderService()
    
    # Empty sequence
    result_empty = service.fold_sequence("")
    assert result_empty["status"] == "error"
    assert result_empty["error_type"] == "validation_empty"
    
    # X is allowed in the service (unknown residue); only Z is truly invalid
    result_invalid = service.fold_sequence("MAEVPRRLLLLLLLLZ")
    assert result_invalid["status"] == "error"
    assert result_invalid["error_type"] == "validation_invalid_chars"
    assert "Z" in result_invalid["message"]

def test_esmfold_too_long():
    service = StructuralFolderService()
    
    # Generate sequence longer than settings.ESMFOLD_MAX_SEQUENCE_LENGTH
    long_seq = "A" * (settings.ESMFOLD_MAX_SEQUENCE_LENGTH + 1)
    result = service.fold_sequence(long_seq)
    
    assert result["status"] == "error"
    assert result["error_type"] == "validation_too_long"

if __name__ == "__main__":
    print("Running ESMFold Structural Folding Service tests...")
    test_esmfold_live_success()
    test_esmfold_provider_failure()
    test_esmfold_invalid_input()
    test_esmfold_too_long()
    print("All tests passed!")
