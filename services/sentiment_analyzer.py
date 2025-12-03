"""
Sentiment Analysis Service
Analyzes social sentiment for tokens and markets.
"""
from typing import Dict, List, Optional
from datetime import datetime
import json

from polymind.types import SentimentAnalysis
from config import settings
from utils.logger import logger


class SentimentAnalyzer:
    """
    Sentiment analysis engine for DeFi tokens.
    Analyzes social media, news, and on-chain sentiment signals.
    """
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self.sentiment_sources = ["twitter", "reddit", "on_chain", "news"]
    
    async def analyze_sentiment(
        self,
        token_symbol: str,
        sources: Optional[List[str]] = None
    ) -> SentimentAnalysis:
        """
        Analyze sentiment for a token.
        
        Args:
            token_symbol: Token to analyze
            sources: Optional list of sources to use
        
        Returns:
            Sentiment analysis result
        """
        sources_to_use = sources or self.sentiment_sources
        
        # Collect sentiment signals from different sources
        sentiment_scores = []
        key_mentions = []
        
        for source in sources_to_use:
            try:
                source_sentiment = await self._analyze_source(
                    source,
                    token_symbol
                )
                if source_sentiment:
                    sentiment_scores.append(source_sentiment["score"])
                    key_mentions.extend(source_sentiment.get("mentions", []))
            except Exception as e:
                logger.error(f"Error analyzing {source} sentiment: {e}")
        
        # Calculate aggregate sentiment
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        else:
            avg_sentiment = 0.0  # Neutral if no data
        
        # Determine sentiment label
        if avg_sentiment > 0.3:
            sentiment_label = "BULLISH"
        elif avg_sentiment < -0.3:
            sentiment_label = "BEARISH"
        else:
            sentiment_label = "NEUTRAL"
        
        # Use AI for enhanced analysis if available
        if self.ai_client:
            try:
                ai_enhancement = await self._ai_sentiment_analysis(
                    token_symbol,
                    avg_sentiment,
                    key_mentions
                )
                if ai_enhancement:
                    avg_sentiment = ai_enhancement.get("score", avg_sentiment)
                    key_mentions.extend(ai_enhancement.get("mentions", []))
            except Exception as e:
                logger.error(f"AI sentiment enhancement error: {e}")
        
        return SentimentAnalysis(
            token_symbol=token_symbol,
            sentiment_score=round(avg_sentiment, 3),
            sentiment_label=sentiment_label,
            confidence=0.7 if sentiment_scores else 0.5,
            sources=sources_to_use,
            key_mentions=key_mentions[:10],  # Top 10 mentions
            timestamp=datetime.utcnow().isoformat()
        )
    
    async def _analyze_source(
        self,
        source: str,
        token_symbol: str
    ) -> Optional[Dict]:
        """Analyze sentiment from a specific source."""
        # In production, this would fetch real data from APIs
        # For now, simulate sentiment analysis
        
        if source == "twitter":
            # Simulate Twitter sentiment
            return {
                "score": self._simulate_sentiment(token_symbol, "twitter"),
                "mentions": [f"Twitter mention about {token_symbol}"]
            }
        elif source == "reddit":
            return {
                "score": self._simulate_sentiment(token_symbol, "reddit"),
                "mentions": [f"Reddit discussion about {token_symbol}"]
            }
        elif source == "on_chain":
            # On-chain sentiment based on transaction patterns
            return {
                "score": self._simulate_sentiment(token_symbol, "on_chain"),
                "mentions": [f"On-chain activity for {token_symbol}"]
            }
        elif source == "news":
            return {
                "score": self._simulate_sentiment(token_symbol, "news"),
                "mentions": [f"News article about {token_symbol}"]
            }
        
        return None
    
    def _simulate_sentiment(self, token: str, source: str) -> float:
        """Simulate sentiment score (would use real APIs in production)."""
        # Simple hash-based simulation
        hash_val = hash(f"{token}{source}") % 100
        # Convert to -1 to 1 range
        return (hash_val - 50) / 50
    
    async def _ai_sentiment_analysis(
        self,
        token_symbol: str,
        base_sentiment: float,
        mentions: List[str]
    ) -> Optional[Dict]:
        """Use AI to enhance sentiment analysis."""
        if not self.ai_client:
            return None
        
        try:
            prompt = f"""
Analyze sentiment for {token_symbol} token.

Base sentiment score: {base_sentiment:.2f} (-1 = bearish, +1 = bullish)
Key mentions: {', '.join(mentions[:5])}

Provide enhanced sentiment analysis in JSON:
{{
    "score": -1.0 to 1.0,
    "mentions": ["key insight 1", "key insight 2"],
    "reasoning": "brief explanation"
}}
"""
            
            response = await self.ai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a crypto market sentiment analyst. Analyze token sentiment from multiple sources."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"AI sentiment analysis error: {e}")
            return None
    
    async def compare_sentiment(
        self,
        tokens: List[str]
    ) -> Dict:
        """
        Compare sentiment across multiple tokens.
        
        Args:
            tokens: List of token symbols to compare
        
        Returns:
            Comparison results
        """
        analyses = []
        
        for token in tokens:
            analysis = await self.analyze_sentiment(token)
            analyses.append(analysis)
        
        # Sort by sentiment score
        analyses.sort(key=lambda x: x.sentiment_score, reverse=True)
        
        return {
            "comparison": {
                "most_bullish": analyses[0].token_symbol if analyses else None,
                "most_bearish": analyses[-1].token_symbol if analyses else None,
                "average_sentiment": sum(a.sentiment_score for a in analyses) / len(analyses) if analyses else 0.0
            },
            "analyses": [a.dict() for a in analyses],
            "timestamp": datetime.utcnow().isoformat()
        }

