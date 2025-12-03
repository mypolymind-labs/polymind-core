"""
Tests for RiskEngine service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import json

from services.risk_engine import RiskEngine
from polymind.types import TransactionData
from polymind.constants import RiskLevel
from tests.conftest import mock_openai_client


@pytest.mark.asyncio
async def test_assess_transaction_risk_low(risk_engine):
    """Test risk assessment for low-risk transaction."""
    tx = TransactionData(
        signature="test_123",
        amount=100.0,
        transaction_type="TRANSFER",
        err=None
    )
    
    assessment = await risk_engine.assess_transaction_risk(tx)
    
    assert assessment.risk_level in [RiskLevel.LOW.value, RiskLevel.MEDIUM.value]
    assert 0.0 <= assessment.risk_score <= 1.0
    assert assessment.recommendation is not None


@pytest.mark.asyncio
async def test_assess_transaction_risk_high(risk_engine):
    """Test risk assessment for high-risk transaction."""
    tx = TransactionData(
        signature="test_456",
        amount=2000000.0,  # Large amount
        transaction_type="FLASH_LOAN",
        err=None
    )
    
    assessment = await risk_engine.assess_transaction_risk(tx)
    
    assert assessment.risk_level in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]
    assert assessment.risk_score > 0.3
    assert len(assessment.risk_factors) > 0


@pytest.mark.asyncio
async def test_assess_transaction_risk_with_error(risk_engine):
    """Test risk assessment for transaction with error."""
    tx = TransactionData(
        signature="test_789",
        amount=1000.0,
        transaction_type="SWAP",
        err="InsufficientFunds"
    )
    
    assessment = await risk_engine.assess_transaction_risk(tx)
    
    assert assessment.risk_level in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]
    assert "error" in str(assessment.risk_factors).lower() or len(assessment.risk_factors) > 0


@pytest.mark.asyncio
async def test_assess_transaction_risk_with_ai(risk_engine, mock_openai_client):
    """Test risk assessment with AI enhancement."""
    tx = TransactionData(
        signature="test_ai",
        amount=5000.0,
        transaction_type="SWAP"
    )
    
    # Mock AI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "risk_factors": ["suspicious_pattern", "unusual_amount"],
        "opportunity_signals": [],
        "risk_score": 0.6
    })
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    assessment = await risk_engine.assess_transaction_risk(tx)
    
    assert assessment.risk_score >= 0.6
    assert len(assessment.risk_factors) > 0


@pytest.mark.asyncio
async def test_scan_account_risks(risk_engine):
    """Test scanning account for risks."""
    transactions = [
        TransactionData(
            signature=f"tx_{i}",
            amount=1000.0 * (i + 1),
            transaction_type="SWAP"
        )
        for i in range(5)
    ]
    
    result = await risk_engine.scan_account_risks("test_account", transactions)
    
    assert result["account"] == "test_account"
    assert result["transaction_count"] == 5
    assert "overall_risk_level" in result
    assert "average_risk_score" in result
    assert len(result["assessments"]) == 5

