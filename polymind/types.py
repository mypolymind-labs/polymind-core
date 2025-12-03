"""
Type definitions for PolyMind Core.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class MarketData(BaseModel):
    """Market data model."""
    symbol: str
    token_mint: Optional[str] = None
    price: Optional[float] = None
    volume_24h: float = 0.0
    liquidity_depth: Optional[float] = None
    sentiment_score: float = 0.5
    recent_transactions: int = 0
    block_height: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    data_source: str = "PolyFlow"


class PredictionResult(BaseModel):
    """Prediction result model."""
    direction: str  # UP, DOWN, NEUTRAL
    confidence_score: float = Field(ge=0.0, le=1.0)
    target_price_24h: Optional[float] = None
    risk_level: str  # LOW, MEDIUM, HIGH
    reasoning: Optional[str] = None
    key_factors: List[str] = Field(default_factory=list)
    model_version: str = "v2.0.0-ai"
    prediction_method: str = "AI"


class RiskAssessment(BaseModel):
    """Risk assessment model."""
    risk_level: str
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_factors: List[str] = Field(default_factory=list)
    opportunity_signals: List[str] = Field(default_factory=list)
    recommendation: Optional[str] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class TransactionData(BaseModel):
    """Transaction data model."""
    signature: str
    slot: Optional[int] = None
    block_time: Optional[int] = None
    confirmation_status: Optional[str] = None
    err: Optional[Any] = None
    transaction_type: Optional[str] = None
    amount: Optional[float] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None


class YieldOpportunity(BaseModel):
    """Yield opportunity model."""
    protocol: str
    pool: str
    current_apy: float
    predicted_apy: float
    risk_adjusted_return: float
    recommendation: str
    confidence: float = Field(ge=0.0, le=1.0)
    migration_risk: str = "LOW"


class PortfolioRebalance(BaseModel):
    """Portfolio rebalancing suggestion."""
    current_allocation: Dict[str, float]
    suggested_allocation: Dict[str, float]
    rebalancing_actions: List[Dict[str, Any]]
    expected_improvement: float
    risk_reduction: float
    reasoning: str


class SentimentAnalysis(BaseModel):
    """Sentiment analysis result."""
    token_symbol: str
    sentiment_score: float = Field(ge=-1.0, le=1.0)  # -1 bearish, +1 bullish
    sentiment_label: str  # BEARISH, NEUTRAL, BULLISH
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[str] = Field(default_factory=list)
    key_mentions: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class BatchPredictionRequest(BaseModel):
    """Batch prediction request model."""
    tokens: List[str] = Field(min_length=1, max_length=50)
    include_risk: bool = True
    include_sentiment: bool = False


class BatchPredictionResponse(BaseModel):
    """Batch prediction response model."""
    predictions: Dict[str, PredictionResult]
    summary: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

