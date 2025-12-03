"""
Tests for YieldOptimizer service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import json

from services.yield_optimizer import YieldOptimizer
from tests.conftest import mock_openai_client


@pytest.mark.asyncio
async def test_optimize_yield(yield_optimizer):
    """Test yield optimization."""
    opportunities = await yield_optimizer.optimize_yield("SOL")
    
    assert isinstance(opportunities, list)
    assert len(opportunities) > 0
    
    # Check opportunity structure
    opp = opportunities[0]
    assert opp.protocol is not None
    assert opp.current_apy >= 0
    assert opp.predicted_apy >= 0
    assert opp.risk_adjusted_return >= 0
    assert opp.recommendation is not None


@pytest.mark.asyncio
async def test_optimize_yield_with_ai(yield_optimizer, mock_openai_client):
    """Test yield optimization with AI."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "predicted_apy": 15.5,
        "reasoning": "Strong liquidity trends"
    })
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    opportunities = await yield_optimizer.optimize_yield("SOL")
    
    assert len(opportunities) > 0
    # AI should provide more accurate predictions
    assert opportunities[0].predicted_apy > 0


@pytest.mark.asyncio
async def test_compare_yield_strategies(yield_optimizer):
    """Test comparing yield strategies."""
    strategies = [
        {"name": "Strategy A", "positions": []},
        {"name": "Strategy B", "positions": []}
    ]
    
    result = await yield_optimizer.compare_yield_strategies("SOL", strategies)
    
    assert result["token"] == "SOL"
    assert len(result["comparisons"]) == 2
    assert "best_strategy" in result
    assert result["best_strategy"] is not None


@pytest.mark.asyncio
async def test_calculate_risk_adjusted_return(yield_optimizer):
    """Test risk-adjusted return calculation."""
    current_apy = 10.0
    predicted_apy = 12.0
    protocol_info = {"type": "Staking"}
    
    risk_adjusted = yield_optimizer._calculate_risk_adjusted_return(
        current_apy,
        predicted_apy,
        protocol_info
    )
    
    assert risk_adjusted > 0
    assert risk_adjusted <= predicted_apy  # Should be adjusted down

