"""
Tests for v0.2.0 API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app
from zkmind.types import Proof, ProofType, ProofStatus, VerificationResult
from multichain import ChainType

@pytest.fixture
def client():
    """Test client for API."""
    return TestClient(app)

@pytest.mark.asyncio
@patch('main.proof_generator')
async def test_zkml_generate_endpoint(mock_proof_generator, client):
    """Test zkML proof generation endpoint."""
    
    # Mock proof response
    mock_proof = Proof(
        proof_id="proof_123",
        model_id="test_model",
        proof_type=ProofType.INFERENCE,
        proof_data="0x123",
        public_inputs={"token": "SOL"},
        status=ProofStatus.COMPLETED
    )
    
    mock_proof_generator.generate_proof = AsyncMock(return_value=mock_proof)
    
    payload = {
        "model_id": "test_model",
        "input_data": {"token": "SOL"},
        "output_data": {"prediction": "UP"},
        "proof_type": "inference"
    }
    
    response = client.post("/zkml/proof/generate", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["proof_id"] == "proof_123"
    assert data["status"] == "completed"

@pytest.mark.asyncio
@patch('main.proof_generator')
@patch('main.proof_verifier')
async def test_zkml_verify_endpoint(mock_verifier, mock_generator, client):
    """Test zkML proof verification endpoint."""
    
    # Mock get_proof
    mock_proof = Proof(
        proof_id="proof_123",
        model_id="test_model",
        proof_type=ProofType.INFERENCE,
        proof_data="0x123",
        public_inputs={}
    )
    mock_generator.get_proof.return_value = mock_proof
    
    # Mock verification
    mock_result = VerificationResult(
        proof_id="proof_123",
        is_valid=True,
        error=None
    )
    mock_verifier.verify_proof = AsyncMock(return_value=mock_result)
    
    response = client.post("/zkml/proof/verify?proof_id=proof_123")
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["proof_id"] == "proof_123"

@pytest.mark.asyncio
@patch('main.multichain_manager')
async def test_multichain_balance_endpoint(mock_multichain, client):
    """Test multi-chain balance endpoint."""
    
    mock_multichain.get_balance = AsyncMock(return_value=1.5)
    
    response = client.get("/multichain/ethereum/balance/0x123")
    
    assert response.status_code == 200
    data = response.json()
    assert data["chain"] == "ethereum"
    assert data["balance"] == 1.5

@pytest.mark.asyncio
@patch('main.multichain_manager')
async def test_multichain_list_chains(mock_multichain, client):
    """Test listing supported chains."""
    
    mock_multichain.get_supported_chains.return_value = [
        ChainType.ETHEREUM,
        ChainType.POLYGON
    ]
    mock_multichain.get_all_chain_info = AsyncMock(return_value={
        "ethereum": {"chain": "ethereum"},
        "polygon": {"chain": "polygon"}
    })
    
    response = client.get("/multichain/chains")
    
    assert response.status_code == 200
    data = response.json()
    assert "ethereum" in data["supported_chains"]
    assert "polygon" in data["supported_chains"]

def test_models_list_endpoint(client):
    """Test listing models."""
    response = client.get("/models")
    
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) >= 2
    assert data["models"][0]["id"] == "predicore-v1"
