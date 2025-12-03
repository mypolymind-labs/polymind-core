"""
Constants and enums for PolyMind Core.
"""
from enum import Enum
from typing import Dict


class PredictionDirection(str, Enum):
    """Prediction direction enum."""
    UP = "UP"
    DOWN = "DOWN"
    NEUTRAL = "NEUTRAL"


class RiskLevel(str, Enum):
    """Risk level enum."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TransactionType(str, Enum):
    """Transaction type enum."""
    SWAP = "SWAP"
    TRANSFER = "TRANSFER"
    STAKE = "STAKE"
    UNSTAKE = "UNSTAKE"
    LIQUIDATE = "LIQUIDATE"
    FLASH_LOAN = "FLASH_LOAN"
    UNKNOWN = "UNKNOWN"


# Solana token mints mapping
SOLANA_TOKEN_MINTS: Dict[str, str] = {
    "SOL": "So11111111111111111111111111111111111111112",
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
    "SRM": "SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt",
}

# Risk thresholds
RISK_THRESHOLDS = {
    "liquidation_risk": 0.8,
    "flash_loan_threshold": 1000000,  # USD
    "rug_pull_indicators": ["large_withdrawal", "liquidity_drop", "owner_change"],
    "volatility_spike": 0.3,  # 30% price change
}

# API endpoints
API_ENDPOINTS = {
    "predict": "/predict",
    "batch_predict": "/predict/batch",
    "transactions": "/transactions",
    "risk_scan": "/risk/scan",
    "yield_optimize": "/yield/optimize",
    "portfolio_rebalance": "/portfolio/rebalance",
    "sentiment": "/sentiment",
}

