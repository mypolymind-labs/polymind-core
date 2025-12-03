"""
Tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from main import app


@pytest.fixture
def client():
    """Test client for API."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["system"] == "PolyMind Core"


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "ingestor" in data
    assert "model" in data


@pytest.mark.asyncio
@patch('main.ingestor')
@patch('main.model')
async def test_predict_endpoint(mock_model, mock_ingestor, client):
    """Test prediction endpoint."""
    # Mock ingestor response
    mock_ingestor.fetch_data = AsyncMock(return_value={
        "symbol": "SOL",
        "volume_24h": 1000000,
        "recent_transactions": 50,
        "block_height": 200000000,
        "timestamp": "2024-01-01T00:00:00"
    })
    
    # Mock model response
    mock_model.predict = AsyncMock(return_value={
        "direction": "UP",
        "confidence_score": 0.8,
        "target_price_24h": 105.0,
        "risk_level": "LOW"
    })
    
    response = client.get("/predict/SOL")
    
    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "SOL"
    assert "prediction" in data


@pytest.mark.asyncio
@patch('main.ingestor')
async def test_transactions_endpoint(mock_ingestor, client):
    """Test transactions endpoint."""
    mock_ingestor.get_recent_transactions = AsyncMock(return_value=[
        {
            "signature": "test_123",
            "slot": 200000000,
            "block_time": 1704067200
        }
    ])
    
    response = client.get("/transactions/test_account?limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert data["account"] == "test_account"
    assert "transactions" in data


@pytest.mark.asyncio
@patch('main.risk_engine')
async def test_risk_scan_endpoint(mock_risk_engine, client):
    """Test risk scan endpoint."""
    mock_risk_engine.scan_account_risks = AsyncMock(return_value={
        "account": "test_account",
        "overall_risk_level": "LOW",
        "average_risk_score": 0.3,
        "transaction_count": 5,
        "high_risk_transactions": 0,
        "assessments": []
    })
    
    response = client.post("/risk/scan?account_address=test_account&limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert data["account"] == "test_account"
    assert "overall_risk_level" in data


@pytest.mark.asyncio
@patch('main.yield_optimizer')
async def test_yield_optimize_endpoint(mock_yield_optimizer, client):
    """Test yield optimization endpoint."""
    from services.yield_optimizer import YieldOpportunity
    
    mock_opportunity = YieldOpportunity(
        protocol="Jupiter",
        pool="SOL/USDC",
        current_apy=10.0,
        predicted_apy=12.0,
        risk_adjusted_return=11.0,
        recommendation="Good opportunity",
        confidence=0.8,
        migration_risk="LOW"
    )
    
    mock_yield_optimizer.optimize_yield = AsyncMock(
        return_value=[mock_opportunity]
    )
    
    response = client.get("/yield/optimize?token_symbol=SOL")
    
    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "SOL"
    assert "opportunities" in data


@pytest.mark.asyncio
@patch('main.portfolio_service')
async def test_portfolio_rebalance_endpoint(mock_portfolio_service, client):
    """Test portfolio rebalancing endpoint."""
    from polymind.types import PortfolioRebalance
    
    mock_rebalance = PortfolioRebalance(
        current_allocation={"SOL": 80.0, "USDC": 20.0},
        suggested_allocation={"SOL": 50.0, "USDC": 50.0},
        rebalancing_actions=[],
        expected_improvement=0.5,
        risk_reduction=0.3,
        reasoning="Test reasoning"
    )
    
    mock_portfolio_service.suggest_rebalancing = AsyncMock(
        return_value=mock_rebalance
    )
    
    response = client.post(
        "/portfolio/rebalance?risk_profile=MODERATE",
        json={"SOL": 80.0, "USDC": 20.0}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "current_allocation" in data
    assert "suggested_allocation" in data


@pytest.mark.asyncio
@patch('main.sentiment_analyzer')
async def test_sentiment_endpoint(mock_sentiment_analyzer, client):
    """Test sentiment analysis endpoint."""
    from polymind.types import SentimentAnalysis
    
    mock_sentiment = SentimentAnalysis(
        token_symbol="SOL",
        sentiment_score=0.7,
        sentiment_label="BULLISH",
        confidence=0.8,
        sources=["twitter"],
        key_mentions=["Positive news"],
        timestamp="2024-01-01T00:00:00"
    )
    
    mock_sentiment_analyzer.analyze_sentiment = AsyncMock(
        return_value=mock_sentiment
    )
    
    response = client.get("/sentiment/SOL")
    
    assert response.status_code == 200
    data = response.json()
    assert data["token_symbol"] == "SOL"
    assert data["sentiment_label"] == "BULLISH"

