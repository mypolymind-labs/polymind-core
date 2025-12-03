"""
Tests for PortfolioService.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from services.portfolio_service import PortfolioService
from tests.conftest import mock_openai_client


@pytest.mark.asyncio
async def test_suggest_rebalancing(portfolio_service):
    """Test portfolio rebalancing suggestions."""
    current_allocation = {
        "SOL": 80.0,
        "USDC": 15.0,
        "USDT": 5.0
    }
    
    result = await portfolio_service.suggest_rebalancing(
        current_allocation,
        risk_profile="MODERATE"
    )
    
    assert result.current_allocation == current_allocation
    assert result.suggested_allocation is not None
    assert len(result.rebalancing_actions) > 0
    assert result.expected_improvement >= 0
    assert result.reasoning is not None


@pytest.mark.asyncio
async def test_suggest_rebalancing_with_target(portfolio_service):
    """Test rebalancing with target allocation."""
    current_allocation = {
        "SOL": 70.0,
        "USDC": 30.0
    }
    target_allocation = {
        "SOL": 50.0,
        "USDC": 50.0
    }
    
    result = await portfolio_service.suggest_rebalancing(
        current_allocation,
        risk_profile="CONSERVATIVE",
        target_allocation=target_allocation
    )
    
    assert result.suggested_allocation == target_allocation
    assert len(result.rebalancing_actions) > 0


@pytest.mark.asyncio
async def test_calculate_rebalancing_actions(portfolio_service):
    """Test rebalancing actions calculation."""
    current = {"SOL": 80.0, "USDC": 20.0}
    target = {"SOL": 50.0, "USDC": 50.0}
    
    actions = portfolio_service._calculate_rebalancing_actions(current, target)
    
    assert len(actions) == 2
    assert any(a["token"] == "SOL" for a in actions)
    assert any(a["token"] == "USDC" for a in actions)


@pytest.mark.asyncio
async def test_generate_target_allocation(portfolio_service):
    """Test target allocation generation."""
    current = {"SOL": 60.0, "USDC": 40.0}
    
    target = portfolio_service._generate_target_allocation(current, "MODERATE")
    
    assert sum(target.values()) == pytest.approx(100.0, abs=0.01)
    assert "SOL" in target
    assert "USDC" in target

