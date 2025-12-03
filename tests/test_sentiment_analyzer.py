"""
Tests for SentimentAnalyzer service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import json

from services.sentiment_analyzer import SentimentAnalyzer
from tests.conftest import mock_openai_client


@pytest.mark.asyncio
async def test_analyze_sentiment(sentiment_analyzer):
    """Test sentiment analysis."""
    result = await sentiment_analyzer.analyze_sentiment("SOL")
    
    assert result.token_symbol == "SOL"
    assert -1.0 <= result.sentiment_score <= 1.0
    assert result.sentiment_label in ["BULLISH", "BEARISH", "NEUTRAL"]
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.sources) > 0


@pytest.mark.asyncio
async def test_analyze_sentiment_with_sources(sentiment_analyzer):
    """Test sentiment analysis with specific sources."""
    result = await sentiment_analyzer.analyze_sentiment(
        "SOL",
        sources=["twitter", "reddit"]
    )
    
    assert result.token_symbol == "SOL"
    assert "twitter" in result.sources
    assert "reddit" in result.sources


@pytest.mark.asyncio
async def test_analyze_sentiment_with_ai(sentiment_analyzer, mock_openai_client):
    """Test sentiment analysis with AI enhancement."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "score": 0.8,
        "mentions": ["Strong community support", "Positive news"],
        "reasoning": "Very bullish sentiment"
    })
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    result = await sentiment_analyzer.analyze_sentiment("SOL")
    
    assert result.sentiment_score > 0
    assert len(result.key_mentions) > 0


@pytest.mark.asyncio
async def test_compare_sentiment(sentiment_analyzer):
    """Test comparing sentiment across tokens."""
    tokens = ["SOL", "USDC", "USDT"]
    
    result = await sentiment_analyzer.compare_sentiment(tokens)
    
    assert "comparison" in result
    assert "analyses" in result
    assert len(result["analyses"]) == 3
    assert result["comparison"]["most_bullish"] is not None
    assert result["comparison"]["most_bearish"] is not None

