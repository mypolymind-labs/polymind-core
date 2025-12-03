"""
PrediCore - Predictive Intelligence Layer
Uses AI models (OpenAI) to analyze market data and generate predictions.
"""
from typing import Dict, List, Optional
from openai import AsyncOpenAI
import json

from config import settings
from utils.logger import logger


class PredictiveModel:
    """
    AI-powered predictive model for market analysis.
    Integrates with OpenAI for intelligent market forecasting.
    """
    
    def __init__(self):
        self.model_version = "v2.0.0-ai"
        self.openai_client: Optional[AsyncOpenAI] = None
        
        if settings.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("OpenAI client initialized")
        else:
            logger.warning("OpenAI API key not found. AI features will be limited.")
    
    async def _analyze_with_ai(self, market_data: Dict) -> Dict:
        """
        Use OpenAI to analyze market data and generate intelligent predictions.
        
        Args:
            market_data: Market data dictionary
        
        Returns:
            AI-generated analysis and prediction
        """
        if not self.openai_client:
            logger.warning("OpenAI client not available, using fallback prediction")
            return None
        
        try:
            # Prepare prompt for AI analysis
            prompt = f"""
You are a DeFi market analyst for PolyMind Protocol. Analyze the following Solana market data and provide a prediction:

Market Data:
- Symbol: {market_data.get('symbol', 'Unknown')}
- Token Mint: {market_data.get('token_mint', 'N/A')}
- Volume 24h: {market_data.get('volume_24h', 0)}
- Recent Transactions: {market_data.get('recent_transactions', 0)}
- Block Height: {market_data.get('block_height', 'N/A')}
- Timestamp: {market_data.get('timestamp', 'N/A')}

Provide your analysis in JSON format with the following structure:
{{
    "direction": "UP" | "DOWN" | "NEUTRAL",
    "confidence_score": 0.0-1.0,
    "target_price_24h": number (or null if price unavailable),
    "risk_level": "LOW" | "MEDIUM" | "HIGH",
    "reasoning": "Brief explanation of your prediction",
    "key_factors": ["factor1", "factor2", "factor3"]
}}

Be analytical and consider:
1. Transaction volume and activity patterns
2. Market momentum indicators
3. Risk factors in the current market state
4. Historical patterns in DeFi markets
"""
            
            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert DeFi market analyst specializing in Solana blockchain markets. Provide accurate, data-driven predictions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=settings.openai_temperature,
                response_format={"type": "json_object"}
            )
            
            # Parse AI response
            content = response.choices[0].message.content
            ai_analysis = json.loads(content)
            
            logger.info(f"AI analysis completed for {market_data.get('symbol')}")
            return ai_analysis
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return None
    
    def _fallback_prediction(self, market_data: Dict) -> Dict:
        """
        Fallback prediction when AI is unavailable.
        Uses simple heuristics based on transaction volume.
        
        Args:
            market_data: Market data dictionary
        
        Returns:
            Basic prediction dictionary
        """
        volume = market_data.get("volume_24h", 0)
        recent_txs = market_data.get("recent_transactions", 0)
        
        # Simple heuristic: high volume/activity = bullish
        if volume > 1000000 or recent_txs > 50:
            direction = "UP"
            confidence = 0.65
        elif volume < 100000 or recent_txs < 10:
            direction = "DOWN"
            confidence = 0.60
        else:
            direction = "NEUTRAL"
            confidence = 0.50
        
        risk_level = "LOW" if confidence > 0.7 else "MEDIUM"
        
        return {
            "direction": direction,
            "confidence_score": round(confidence, 2),
            "target_price_24h": None,  # Price unavailable without DEX integration
            "risk_level": risk_level,
            "reasoning": f"Based on transaction volume ({volume}) and activity ({recent_txs} recent txs)",
            "key_factors": ["transaction_volume", "activity_level"]
        }
    
    async def predict(self, market_data: Dict) -> Dict:
        """
        Generate a forward-looking prediction based on market data.
        Uses AI when available, falls back to heuristics otherwise.
        
        Args:
            market_data: Market data dictionary from DataIngestor
        
        Returns:
            Prediction dictionary with direction, confidence, target price, and risk level
        """
        try:
            # Try AI analysis first
            ai_prediction = await self._analyze_with_ai(market_data)
            
            if ai_prediction:
                # Enhance with metadata
                ai_prediction["model_version"] = self.model_version
                ai_prediction["prediction_method"] = "AI"
                return ai_prediction
            
            # Fallback to heuristic prediction
            logger.info("Using fallback prediction method")
            prediction = self._fallback_prediction(market_data)
            prediction["model_version"] = self.model_version
            prediction["prediction_method"] = "Heuristic"
            return prediction
            
        except Exception as e:
            logger.error(f"Error generating prediction: {e}")
            # Return safe fallback
            return {
                "direction": "NEUTRAL",
                "confidence_score": 0.5,
                "target_price_24h": None,
                "risk_level": "MEDIUM",
                "reasoning": "Error in prediction model",
                "key_factors": [],
                "model_version": self.model_version,
                "prediction_method": "Error"
            }
    
    async def analyze_transaction(self, transaction_data: Dict) -> Dict:
        """
        Analyze a specific transaction for risk and opportunity signals.
        
        Args:
            transaction_data: Transaction data dictionary
        
        Returns:
            Analysis with risk assessment and insights
        """
        if not self.openai_client:
            return {
                "risk_level": "UNKNOWN",
                "insights": "AI analysis unavailable"
            }
        
        try:
            prompt = f"""
Analyze this Solana transaction for potential risks or opportunities:

Transaction Data:
{json.dumps(transaction_data, indent=2)}

Provide analysis in JSON:
{{
    "risk_level": "LOW" | "MEDIUM" | "HIGH",
    "risk_factors": ["factor1", "factor2"],
    "opportunity_signals": ["signal1", "signal2"],
    "recommendation": "Brief recommendation"
}}
"""
            
            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a DeFi security and market analysis expert. Identify risks and opportunities in blockchain transactions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more focused analysis
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error analyzing transaction: {e}")
            return {
                "risk_level": "UNKNOWN",
                "insights": f"Analysis error: {str(e)}"
            }
    
    async def predict_batch(
        self,
        market_data_list: List[Dict]
    ) -> Dict[str, Dict]:
        """
        Generate predictions for multiple tokens in batch.
        
        Args:
            market_data_list: List of market data dictionaries
        
        Returns:
            Dictionary mapping token symbols to predictions
        """
        predictions = {}
        
        # Process predictions concurrently
        import asyncio
        tasks = [
            self.predict(data) for data in market_data_list
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, (data, result) in enumerate(zip(market_data_list, results)):
            symbol = data.get("symbol", f"token_{i}")
            if isinstance(result, Exception):
                logger.error(f"Error predicting for {symbol}: {result}")
                predictions[symbol] = {
                    "direction": "NEUTRAL",
                    "confidence_score": 0.0,
                    "target_price_24h": None,
                    "risk_level": "UNKNOWN",
                    "error": str(result)
                }
            else:
                predictions[symbol] = result
        
        return predictions
