"""
Yield Optimization Service
Predicts yield opportunities and optimizes yield strategies.
"""
from typing import Dict, List, Optional
from datetime import datetime
import json

from polymind.types import YieldOpportunity
from polymind.constants import RiskLevel
from config import settings
from utils.logger import logger


class YieldOptimizer:
    """
    Predictive yield optimization engine.
    Forecasts APY changes and recommends optimal yield strategies.
    """
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self.protocols = self._load_protocols()
    
    def _load_protocols(self) -> Dict:
        """Load known yield protocols and their characteristics."""
        return {
            "jupiter": {
                "name": "Jupiter",
                "type": "DEX",
                "typical_apy_range": (5, 50)
            },
            "raydium": {
                "name": "Raydium",
                "type": "AMM",
                "typical_apy_range": (10, 100)
            },
            "marinade": {
                "name": "Marinade Finance",
                "type": "Staking",
                "typical_apy_range": (6, 8)
            },
            "solend": {
                "name": "Solend",
                "type": "Lending",
                "typical_apy_range": (3, 15)
            }
        }
    
    async def optimize_yield(
        self,
        token_symbol: str,
        current_positions: Optional[List[Dict]] = None
    ) -> List[YieldOpportunity]:
        """
        Find optimal yield opportunities for a token.
        
        Args:
            token_symbol: Token to optimize yield for
            current_positions: Current yield positions (optional)
        
        Returns:
            List of yield opportunities sorted by risk-adjusted return
        """
        opportunities = []
        
        # Generate opportunities for each protocol
        for protocol_id, protocol_info in self.protocols.items():
            try:
                opportunity = await self._analyze_protocol(
                    protocol_id,
                    protocol_info,
                    token_symbol
                )
                if opportunity:
                    opportunities.append(opportunity)
            except Exception as e:
                logger.error(f"Error analyzing protocol {protocol_id}: {e}")
        
        # Sort by risk-adjusted return
        opportunities.sort(key=lambda x: x.risk_adjusted_return, reverse=True)
        
        return opportunities
    
    async def _analyze_protocol(
        self,
        protocol_id: str,
        protocol_info: Dict,
        token_symbol: str
    ) -> Optional[YieldOpportunity]:
        """Analyze a protocol for yield opportunities."""
        # Simulate current APY (would fetch from protocol in production)
        current_apy = self._estimate_current_apy(protocol_info, token_symbol)
        
        # Predict future APY using AI if available
        predicted_apy = await self._predict_apy(
            protocol_id,
            token_symbol,
            current_apy
        )
        
        # Calculate risk-adjusted return
        risk_adjusted_return = self._calculate_risk_adjusted_return(
            current_apy,
            predicted_apy,
            protocol_info
        )
        
        # Determine migration risk
        migration_risk = self._assess_migration_risk(
            current_apy,
            predicted_apy
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            current_apy,
            predicted_apy,
            migration_risk
        )
        
        return YieldOpportunity(
            protocol=protocol_info["name"],
            pool=f"{token_symbol}/{protocol_id}",
            current_apy=current_apy,
            predicted_apy=predicted_apy,
            risk_adjusted_return=risk_adjusted_return,
            recommendation=recommendation,
            confidence=0.7,
            migration_risk=migration_risk
        )
    
    def _estimate_current_apy(self, protocol_info: Dict, token: str) -> float:
        """Estimate current APY (simplified - would fetch real data in production)."""
        apy_range = protocol_info["typical_apy_range"]
        # Simulate based on protocol type and token
        base_apy = (apy_range[0] + apy_range[1]) / 2
        return round(base_apy + (hash(token) % 20), 2)
    
    async def _predict_apy(
        self,
        protocol_id: str,
        token_symbol: str,
        current_apy: float
    ) -> float:
        """Predict future APY using AI."""
        if not self.ai_client:
            # Fallback: simple trend prediction
            return current_apy * 0.95  # Assume slight decline
        
        try:
            prompt = f"""
Predict the APY for {token_symbol} on {protocol_id} protocol.

Current APY: {current_apy}%

Consider:
- Market conditions
- Liquidity trends
- Protocol incentives
- Historical patterns

Respond in JSON:
{{
    "predicted_apy": number,
    "reasoning": "brief explanation"
}}
"""
            
            response = await self.ai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a DeFi yield analyst. Predict APY changes based on market conditions."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return round(float(result.get("predicted_apy", current_apy)), 2)
        except Exception as e:
            logger.error(f"APY prediction error: {e}")
            return current_apy * 0.95
    
    def _calculate_risk_adjusted_return(
        self,
        current_apy: float,
        predicted_apy: float,
        protocol_info: Dict
    ) -> float:
        """Calculate risk-adjusted return score."""
        # Simple calculation: predicted APY adjusted for protocol risk
        protocol_risk_factor = 0.9 if protocol_info["type"] == "Staking" else 0.85
        return round(predicted_apy * protocol_risk_factor, 2)
    
    def _assess_migration_risk(
        self,
        current_apy: float,
        predicted_apy: float
    ) -> str:
        """Assess risk of migrating to this opportunity."""
        apy_change = predicted_apy - current_apy
        
        if apy_change > 5:
            return "LOW"  # Significant improvement
        elif apy_change > 0:
            return "MEDIUM"  # Small improvement
        else:
            return "HIGH"  # Declining APY
    
    def _generate_recommendation(
        self,
        current_apy: float,
        predicted_apy: float,
        migration_risk: str
    ) -> str:
        """Generate yield optimization recommendation."""
        apy_change = predicted_apy - current_apy
        
        if migration_risk == "LOW" and apy_change > 5:
            return f"STRONG BUY: Expected {apy_change:.2f}% APY improvement"
        elif apy_change > 0:
            return f"CONSIDER: Potential {apy_change:.2f}% APY gain"
        else:
            return f"AVOID: APY expected to decline by {abs(apy_change):.2f}%"
    
    async def compare_yield_strategies(
        self,
        token_symbol: str,
        strategies: List[Dict]
    ) -> Dict:
        """
        Compare multiple yield strategies.
        
        Args:
            token_symbol: Token symbol
            strategies: List of strategy configurations
        
        Returns:
            Comparison results with recommendations
        """
        comparisons = []
        
        for strategy in strategies:
            opportunities = await self.optimize_yield(
                token_symbol,
                strategy.get("positions", [])
            )
            
            if opportunities:
                best_opportunity = opportunities[0]
                comparisons.append({
                    "strategy": strategy.get("name", "Unknown"),
                    "best_apy": best_opportunity.predicted_apy,
                    "risk_adjusted_return": best_opportunity.risk_adjusted_return,
                    "recommendation": best_opportunity.recommendation
                })
        
        # Find best overall strategy
        if comparisons:
            best_strategy = max(comparisons, key=lambda x: x["risk_adjusted_return"])
            return {
                "token": token_symbol,
                "comparisons": comparisons,
                "best_strategy": best_strategy,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "token": token_symbol,
            "comparisons": [],
            "best_strategy": None,
            "timestamp": datetime.utcnow().isoformat()
        }

