"""
Portfolio Rebalancing Service
Provides portfolio optimization and rebalancing recommendations.
"""
from typing import Dict, List, Optional
from datetime import datetime
import json

from polymind.types import PortfolioRebalance
from config import settings
from utils.logger import logger


class PortfolioService:
    """
    Portfolio rebalancing and optimization service.
    Provides actionable suggestions for portfolio management.
    """
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
    
    async def suggest_rebalancing(
        self,
        current_allocation: Dict[str, float],
        risk_profile: str = "MODERATE",
        target_allocation: Optional[Dict[str, float]] = None
    ) -> PortfolioRebalance:
        """
        Suggest portfolio rebalancing actions.
        
        Args:
            current_allocation: Current portfolio allocation (token -> percentage)
            risk_profile: Risk profile (CONSERVATIVE, MODERATE, AGGRESSIVE)
            target_allocation: Optional target allocation
        
        Returns:
            Rebalancing suggestions
        """
        # Normalize current allocation
        total = sum(current_allocation.values())
        if total > 0:
            current_allocation = {
                k: (v / total) * 100
                for k, v in current_allocation.items()
            }
        
        # Generate target allocation if not provided
        if not target_allocation:
            target_allocation = self._generate_target_allocation(
                current_allocation,
                risk_profile
            )
        
        # Calculate rebalancing actions
        rebalancing_actions = self._calculate_rebalancing_actions(
            current_allocation,
            target_allocation
        )
        
        # Calculate expected improvements
        expected_improvement = self._estimate_improvement(
            current_allocation,
            target_allocation
        )
        
        risk_reduction = self._calculate_risk_reduction(
            current_allocation,
            target_allocation,
            risk_profile
        )
        
        # Generate reasoning using AI if available
        reasoning = await self._generate_reasoning(
            current_allocation,
            target_allocation,
            risk_profile
        )
        
        return PortfolioRebalance(
            current_allocation=current_allocation,
            suggested_allocation=target_allocation,
            rebalancing_actions=rebalancing_actions,
            expected_improvement=expected_improvement,
            risk_reduction=risk_reduction,
            reasoning=reasoning
        )
    
    def _generate_target_allocation(
        self,
        current: Dict[str, float],
        risk_profile: str
    ) -> Dict[str, float]:
        """Generate optimal target allocation based on risk profile."""
        # Risk profile templates
        templates = {
            "CONSERVATIVE": {
                "SOL": 30,
                "USDC": 40,
                "USDT": 20,
                "Other": 10
            },
            "MODERATE": {
                "SOL": 50,
                "USDC": 25,
                "USDT": 15,
                "Other": 10
            },
            "AGGRESSIVE": {
                "SOL": 70,
                "USDC": 15,
                "USDT": 10,
                "Other": 5
            }
        }
        
        template = templates.get(risk_profile, templates["MODERATE"])
        
        # Adapt template to current holdings
        target = {}
        for token in current.keys():
            if token in template:
                target[token] = template[token]
            else:
                target[token] = template.get("Other", 5)
        
        # Normalize to 100%
        total = sum(target.values())
        if total > 0:
            target = {k: (v / total) * 100 for k, v in target.items()}
        
        return target
    
    def _calculate_rebalancing_actions(
        self,
        current: Dict[str, float],
        target: Dict[str, float]
    ) -> List[Dict]:
        """Calculate specific rebalancing actions needed."""
        actions = []
        
        all_tokens = set(current.keys()) | set(target.keys())
        
        for token in all_tokens:
            current_pct = current.get(token, 0.0)
            target_pct = target.get(token, 0.0)
            difference = target_pct - current_pct
            
            if abs(difference) > 1.0:  # Only rebalance if difference > 1%
                actions.append({
                    "token": token,
                    "action": "INCREASE" if difference > 0 else "DECREASE",
                    "current_percentage": round(current_pct, 2),
                    "target_percentage": round(target_pct, 2),
                    "difference": round(difference, 2)
                })
        
        return actions
    
    def _estimate_improvement(
        self,
        current: Dict[str, float],
        target: Dict[str, float]
    ) -> float:
        """Estimate expected improvement from rebalancing."""
        # Simple calculation based on diversification
        current_diversity = len([v for v in current.values() if v > 5])
        target_diversity = len([v for v in target.values() if v > 5])
        
        # More diversification = better risk-adjusted returns
        improvement = (target_diversity - current_diversity) * 0.5
        return round(max(0, improvement), 2)
    
    def _calculate_risk_reduction(
        self,
        current: Dict[str, float],
        target: Dict[str, float],
        risk_profile: str
    ) -> float:
        """Calculate expected risk reduction."""
        # Calculate concentration risk
        current_concentration = max(current.values()) if current else 0
        target_concentration = max(target.values()) if target else 0
        
        # Lower concentration = lower risk
        risk_reduction = (current_concentration - target_concentration) / 100
        
        # Adjust based on risk profile
        if risk_profile == "CONSERVATIVE":
            risk_reduction *= 1.2
        elif risk_profile == "AGGRESSIVE":
            risk_reduction *= 0.8
        
        return round(max(0, min(1, risk_reduction)), 2)
    
    async def _generate_reasoning(
        self,
        current: Dict[str, float],
        target: Dict[str, float],
        risk_profile: str
    ) -> str:
        """Generate reasoning for rebalancing suggestion."""
        if self.ai_client:
            try:
                prompt = f"""
Analyze this portfolio rebalancing:

Current allocation: {current}
Target allocation: {target}
Risk profile: {risk_profile}

Provide a brief reasoning (2-3 sentences) for why this rebalancing is recommended.
"""
                
                response = await self.ai_client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a portfolio management advisor. Provide clear, concise reasoning for rebalancing suggestions."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=150
                )
                
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"AI reasoning generation error: {e}")
        
        # Fallback reasoning
        actions = self._calculate_rebalancing_actions(current, target)
        return f"Rebalancing recommended to optimize {risk_profile.lower()} risk profile. {len(actions)} adjustments needed."

