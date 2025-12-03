"""
Risk Engine Service
Detects and analyzes risks in DeFi transactions and positions.
"""
from typing import Dict, List, Optional
from datetime import datetime
import json

from polymind.types import RiskAssessment, TransactionData
from polymind.constants import RiskLevel, RISK_THRESHOLDS
from config import settings
from utils.logger import logger


class RiskEngine:
    """
    Multi-layer risk detection engine for DeFi.
    Detects liquidation risks, flash loans, rug pulls, and anomalies.
    """
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self.risk_patterns = self._load_risk_patterns()
    
    def _load_risk_patterns(self) -> Dict:
        """Load known risk patterns and signatures."""
        return {
            "flash_loan_indicators": [
                "large_amount",
                "same_block_repay",
                "multiple_protocols"
            ],
            "rug_pull_indicators": [
                "owner_change",
                "liquidity_withdrawal",
                "token_mint_authority_change"
            ],
            "liquidation_signals": [
                "high_ltv",
                "price_drop",
                "collateral_devaluation"
            ]
        }
    
    async def assess_transaction_risk(
        self,
        transaction: TransactionData
    ) -> RiskAssessment:
        """
        Assess risk level of a transaction.
        
        Args:
            transaction: Transaction data to analyze
        
        Returns:
            Risk assessment with level, factors, and recommendations
        """
        risk_factors = []
        opportunity_signals = []
        risk_score = 0.0
        
        # Check for flash loan patterns
        if transaction.amount and transaction.amount > RISK_THRESHOLDS["flash_loan_threshold"]:
            risk_factors.append("Large transaction amount detected (possible flash loan)")
            risk_score += 0.3
        
        # Check for errors
        if transaction.err:
            risk_factors.append(f"Transaction error: {transaction.err}")
            risk_score += 0.5
        
        # Check transaction type
        if transaction.transaction_type == "FLASH_LOAN":
            risk_factors.append("Flash loan transaction detected")
            risk_score += 0.4
        
        # Use AI for advanced analysis if available
        if self.ai_client:
            try:
                ai_analysis = await self._ai_risk_analysis(transaction)
                if ai_analysis:
                    risk_factors.extend(ai_analysis.get("risk_factors", []))
                    opportunity_signals.extend(ai_analysis.get("opportunity_signals", []))
                    risk_score = max(risk_score, ai_analysis.get("risk_score", 0.0))
            except Exception as e:
                logger.error(f"AI risk analysis error: {e}")
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 0.5:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Generate recommendation
        recommendation = self._generate_recommendation(risk_level, risk_factors)
        
        return RiskAssessment(
            risk_level=risk_level.value,
            risk_score=round(risk_score, 2),
            risk_factors=risk_factors,
            opportunity_signals=opportunity_signals,
            recommendation=recommendation,
            confidence=0.8 if risk_factors else 0.5
        )
    
    async def _ai_risk_analysis(self, transaction: TransactionData) -> Optional[Dict]:
        """Use AI to analyze transaction risks."""
        if not self.ai_client:
            return None
        
        try:
            prompt = f"""
Analyze this Solana transaction for DeFi risks:

Transaction:
- Signature: {transaction.signature}
- Type: {transaction.transaction_type}
- Amount: {transaction.amount}
- Error: {transaction.err}

Identify:
1. Risk factors (flash loans, rug pulls, exploits)
2. Opportunity signals (arbitrage, yield opportunities)
3. Risk score (0.0-1.0)

Respond in JSON:
{{
    "risk_factors": ["factor1", "factor2"],
    "opportunity_signals": ["signal1"],
    "risk_score": 0.0-1.0
}}
"""
            
            response = await self.ai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a DeFi security expert. Analyze transactions for risks and opportunities."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"AI risk analysis error: {e}")
            return None
    
    def _generate_recommendation(
        self,
        risk_level: RiskLevel,
        risk_factors: List[str]
    ) -> str:
        """Generate risk mitigation recommendation."""
        if risk_level == RiskLevel.CRITICAL:
            return "CRITICAL RISK: Do not proceed. Review transaction carefully."
        elif risk_level == RiskLevel.HIGH:
            return "HIGH RISK: Exercise extreme caution. Verify all details."
        elif risk_level == RiskLevel.MEDIUM:
            return "MEDIUM RISK: Proceed with caution. Monitor closely."
        else:
            return "LOW RISK: Transaction appears safe. Standard precautions apply."
    
    async def scan_account_risks(
        self,
        account_address: str,
        transactions: List[TransactionData]
    ) -> Dict:
        """
        Scan an account for risk patterns across multiple transactions.
        
        Args:
            account_address: Account to scan
            transactions: List of transactions to analyze
        
        Returns:
            Account risk assessment
        """
        risk_assessments = []
        total_risk_score = 0.0
        
        for tx in transactions:
            assessment = await self.assess_transaction_risk(tx)
            risk_assessments.append(assessment)
            total_risk_score += assessment.risk_score
        
        avg_risk_score = total_risk_score / len(transactions) if transactions else 0.0
        
        # Determine overall account risk
        if avg_risk_score >= 0.7:
            overall_risk = RiskLevel.CRITICAL
        elif avg_risk_score >= 0.5:
            overall_risk = RiskLevel.HIGH
        elif avg_risk_score >= 0.3:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW
        
        return {
            "account": account_address,
            "overall_risk_level": overall_risk.value,
            "average_risk_score": round(avg_risk_score, 2),
            "transaction_count": len(transactions),
            "high_risk_transactions": sum(
                1 for a in risk_assessments
                if a.risk_level in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]
            ),
            "assessments": [a.dict() for a in risk_assessments]
        }

