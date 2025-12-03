"""
Tests for PredictiveModel (PrediCore).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import json

from predicore.model import PredictiveModel
from tests.conftest import mock_openai_client, sample_market_data


@pytest.mark.asyncio
async def test_predict_with_ai(predictive_model, mock_openai_client, sample_market_data):
    """Test prediction with AI."""
    # Mock AI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "direction": "UP",
        "confidence_score": 0.85,
        "target_price_24h": 105.0,
        "risk_level": "LOW",
        "reasoning": "Strong bullish signals",
        "key_factors": ["high_volume", "positive_sentiment"]
    })
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    result = await predictive_model.predict(sample_market_data)
    
    assert result["direction"] in ["UP", "DOWN", "NEUTRAL"]
    assert 0.0 <= result["confidence_score"] <= 1.0
    assert result["prediction_method"] == "AI"


@pytest.mark.asyncio
async def test_predict_fallback(predictive_model, sample_market_data):
    """Test prediction fallback when AI is unavailable."""
    predictive_model.openai_client = None
    
    result = await predictive_model.predict(sample_market_data)
    
    assert result["direction"] in ["UP", "DOWN", "NEUTRAL"]
    assert 0.0 <= result["confidence_score"] <= 1.0
    assert result["prediction_method"] == "Heuristic"


@pytest.mark.asyncio
async def test_predict_batch(predictive_model, mock_openai_client):
    """Test batch predictions."""
    market_data_list = [
        {"symbol": "SOL", "volume_24h": 1000000, "recent_transactions": 50},
        {"symbol": "USDC", "volume_24h": 500000, "recent_transactions": 30}
    ]
    
    # Mock AI responses
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "direction": "UP",
        "confidence_score": 0.7,
        "target_price_24h": None,
        "risk_level": "MEDIUM",
        "reasoning": "Test",
        "key_factors": []
    })
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    results = await predictive_model.predict_batch(market_data_list)
    
    assert len(results) == 2
    assert "SOL" in results
    assert "USDC" in results


@pytest.mark.asyncio
async def test_analyze_transaction(predictive_model, mock_openai_client):
    """Test transaction analysis."""
    transaction_data = {
        "signature": "test_123",
        "slot": 200000000,
        "transaction_type": "SWAP",
        "amount": 1000.0
    }
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "risk_level": "LOW",
        "risk_factors": [],
        "opportunity_signals": ["arbitrage_opportunity"],
        "recommendation": "Safe transaction"
    })
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    result = await predictive_model.analyze_transaction(transaction_data)
    
    assert "risk_level" in result
    assert "risk_factors" in result or "insights" in result

