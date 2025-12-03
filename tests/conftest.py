"""
Pytest configuration and fixtures.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Optional

from polyflow.ingestor import DataIngestor
from predicore.model import PredictiveModel
from services.risk_engine import RiskEngine
from services.yield_optimizer import YieldOptimizer
from services.sentiment_analyzer import SentimentAnalyzer
from services.portfolio_service import PortfolioService


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    client = AsyncMock()
    client.chat.completions.create = AsyncMock()
    return client


@pytest.fixture
def mock_solana_client():
    """Mock Solana RPC client."""
    client = AsyncMock()
    client.get_account_info = AsyncMock()
    client.get_signatures_for_address = AsyncMock()
    client.get_block_height = AsyncMock()
    client.get_transaction = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        "symbol": "SOL",
        "token_mint": "So11111111111111111111111111111111111111112",
        "price": 100.0,
        "volume_24h": 1000000,
        "liquidity_depth": 500000,
        "sentiment_score": 0.7,
        "recent_transactions": 50,
        "block_height": 200000000,
        "timestamp": "2024-01-01T00:00:00",
        "data_source": "PolyFlow"
    }


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing."""
    return {
        "signature": "test_signature_123",
        "slot": 200000000,
        "block_time": 1704067200,
        "confirmation_status": "confirmed",
        "err": None,
        "transaction_type": "SWAP",
        "amount": 1000.0,
        "from_address": "test_from_address",
        "to_address": "test_to_address"
    }


@pytest.fixture
def data_ingestor(mock_solana_client):
    """DataIngestor instance with mocked Solana client."""
    ingestor = DataIngestor()
    ingestor.solana_client = mock_solana_client
    return ingestor


@pytest.fixture
def predictive_model(mock_openai_client):
    """PredictiveModel instance with mocked OpenAI client."""
    model = PredictiveModel()
    model.openai_client = mock_openai_client
    return model


@pytest.fixture
def risk_engine(mock_openai_client):
    """RiskEngine instance with mocked OpenAI client."""
    return RiskEngine(ai_client=mock_openai_client)


@pytest.fixture
def yield_optimizer(mock_openai_client):
    """YieldOptimizer instance with mocked OpenAI client."""
    return YieldOptimizer(ai_client=mock_openai_client)


@pytest.fixture
def sentiment_analyzer(mock_openai_client):
    """SentimentAnalyzer instance with mocked OpenAI client."""
    return SentimentAnalyzer(ai_client=mock_openai_client)


@pytest.fixture
def portfolio_service(mock_openai_client):
    """PortfolioService instance with mocked OpenAI client."""
    return PortfolioService(ai_client=mock_openai_client)

