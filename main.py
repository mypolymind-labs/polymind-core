"""
PolyMind Core API Server
Main FastAPI application with WebSocket support for real-time transaction monitoring.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import asyncio
import json
from contextlib import asynccontextmanager

from polyflow.ingestor import DataIngestor
from predicore.model import PredictiveModel
from services.risk_engine import RiskEngine
from services.yield_optimizer import YieldOptimizer
from services.sentiment_analyzer import SentimentAnalyzer
from services.portfolio_service import PortfolioService
from polymind.types import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    TransactionData,
    SentimentAnalysis
)
from config import settings
from utils.logger import logger

# v0.2.0 imports
from zkmind import ProofGenerator, ProofVerifier
from zkmind.types import ProofRequest, ProofType
from multichain import MultiChainManager, ChainType

# Global instances
ingestor: Optional[DataIngestor] = None
model: Optional[PredictiveModel] = None
risk_engine: Optional[RiskEngine] = None
yield_optimizer: Optional[YieldOptimizer] = None
sentiment_analyzer: Optional[SentimentAnalyzer] = None
portfolio_service: Optional[PortfolioService] = None

# v0.2.0 global instances
proof_generator: Optional[ProofGenerator] = None
proof_verifier: Optional[ProofVerifier] = None
multichain_manager: Optional[MultiChainManager] = None

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global ingestor, model, risk_engine, yield_optimizer, sentiment_analyzer, portfolio_service
    global proof_generator, proof_verifier, multichain_manager
    
    # Startup
    logger.info("Starting PolyMind Core API v0.2.0...")
    ingestor = DataIngestor()
    model = PredictiveModel()
    
    # Initialize services with AI client if available
    ai_client = model.openai_client if hasattr(model, 'openai_client') else None
    risk_engine = RiskEngine(ai_client=ai_client)
    yield_optimizer = YieldOptimizer(ai_client=ai_client)
    sentiment_analyzer = SentimentAnalyzer(ai_client=ai_client)
    portfolio_service = PortfolioService(ai_client=ai_client)
    
    # Initialize v0.2.0 services
    logger.info("Initializing zkML verification layer...")
    proof_generator = ProofGenerator()
    proof_verifier = ProofVerifier()
    
    logger.info("Initializing multi-chain support...")
    multichain_manager = MultiChainManager()
    
    # Add default chains (can be configured via environment variables)
    try:
        # Ethereum mainnet
        multichain_manager.add_chain(
            ChainType.ETHEREUM,
            "https://eth.llamarpc.com"
        )
        logger.info("Added Ethereum chain support")
    except Exception as e:
        logger.warning(f"Could not add Ethereum chain: {e}")
    
    try:
        # Polygon mainnet
        multichain_manager.add_chain(
            ChainType.POLYGON,
            "https://polygon-rpc.com"
        )
        logger.info("Added Polygon chain support")
    except Exception as e:
        logger.warning(f"Could not add Polygon chain: {e}")
    
    logger.info("PolyMind Core API v0.2.0 started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PolyMind Core API...")
    if ingestor:
        await ingestor.close()
    logger.info("Shutdown complete")


app = FastAPI(
    title="PolyMind Core API",
    version="2.0.0",
    description="AI-powered predictive intelligence protocol for DeFi",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "status": "active",
        "system": "PolyMind Core",
        "version": "2.0.0",
        "features": [
            "Live Solana transaction monitoring",
            "AI-powered market predictions",
            "Real-time WebSocket updates",
            "Risk analysis"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "ingestor": "active" if ingestor else "inactive",
        "model": "active" if model else "inactive"
    }


@app.get("/predict/{token_symbol}")
async def get_prediction(token_symbol: str):
    """
    Get a predictive analysis for a specific token.
    
    Args:
        token_symbol: Token symbol (e.g., "SOL", "USDC") or Solana mint address
    
    Returns:
        Prediction result with direction, confidence, and risk assessment
    """
    try:
        if not ingestor or not model:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # 1. Ingest real-time data from Solana
        logger.info(f"Fetching data for token: {token_symbol}")
        market_data = await ingestor.fetch_data(token_symbol)
        
        # 2. Run AI-powered prediction model
        logger.info(f"Generating prediction for {token_symbol}")
        prediction = await model.predict(market_data)
        
        # 3. Return comprehensive result
        result = {
            "token": token_symbol,
            "token_mint": market_data.get("token_mint"),
            "data_source": market_data.get("data_source", "PolyFlow"),
            "market_data": {
                "volume_24h": market_data.get("volume_24h"),
                "recent_transactions": market_data.get("recent_transactions"),
                "block_height": market_data.get("block_height"),
                "timestamp": market_data.get("timestamp")
            },
            "prediction": prediction
        }
        
        # Broadcast to WebSocket clients
        await manager.broadcast({
            "type": "PREDICTION",
            "data": result
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/transactions/{account_address}")
async def get_transactions(
    account_address: str,
    limit: int = Query(default=10, ge=1, le=100)
):
    """
    Get recent transactions for a Solana account.
    
    Args:
        account_address: Solana account address
        limit: Maximum number of transactions to return (1-100)
    
    Returns:
        List of recent transactions
    """
    try:
        if not ingestor:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        transactions = await ingestor.get_recent_transactions(account_address, limit)
        
        return {
            "account": account_address,
            "transaction_count": len(transactions),
            "transactions": transactions
        }
        
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/transaction")
async def analyze_transaction(transaction_data: dict):
    """
    Analyze a specific transaction for risks and opportunities.
    
    Args:
        transaction_data: Transaction data dictionary
    
    Returns:
        Risk analysis and insights
    """
    try:
        if not model:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        analysis = await model.analyze_transaction(transaction_data)
        
        return {
            "transaction": transaction_data.get("signature", "unknown"),
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time transaction monitoring and updates.
    
    Clients can subscribe to:
    - Live transaction feeds
    - Prediction updates
    - Risk alerts
    """
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "CONNECTED",
            "message": "Connected to PolyMind Core WebSocket",
            "features": [
                "Live transaction monitoring",
                "Real-time predictions",
                "Risk alerts"
            ]
        })
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for client messages (subscriptions, etc.)
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
                
                # Handle client requests
                if data.get("type") == "SUBSCRIBE_TRANSACTIONS":
                    account = data.get("account")
                    if account:
                        # Start monitoring transactions for this account
                        logger.info(f"Client subscribed to transactions for {account}")
                        await websocket.send_json({
                            "type": "SUBSCRIBED",
                            "account": account,
                            "message": f"Monitoring transactions for {account}"
                        })
                
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({
                    "type": "PING",
                    "timestamp": asyncio.get_event_loop().time()
                })
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def batch_predictions(request: BatchPredictionRequest):
    """
    Get predictions for multiple tokens in batch.
    
    Args:
        request: Batch prediction request with list of tokens
    
    Returns:
        Batch prediction results
    """
    try:
        if not ingestor or not model:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Fetch data for all tokens
        market_data_list = []
        for token in request.tokens:
            try:
                data = await ingestor.fetch_data(token)
                market_data_list.append(data)
            except Exception as e:
                logger.error(f"Error fetching data for {token}: {e}")
        
        # Generate batch predictions
        predictions = await model.predict_batch(market_data_list)
        
        # Calculate summary
        directions = [p.get("direction") for p in predictions.values()]
        avg_confidence = sum(
            p.get("confidence_score", 0) for p in predictions.values()
        ) / len(predictions) if predictions else 0
        
        summary = {
            "total_tokens": len(predictions),
            "bullish": sum(1 for d in directions if d == "UP"),
            "bearish": sum(1 for d in directions if d == "DOWN"),
            "neutral": sum(1 for d in directions if d == "NEUTRAL"),
            "average_confidence": round(avg_confidence, 2)
        }
        
        return BatchPredictionResponse(
            predictions=predictions,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Error in batch predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/risk/scan")
async def scan_risks(account_address: str, limit: int = Query(default=10, ge=1, le=100)):
    """
    Scan an account for risk patterns.
    
    Args:
        account_address: Account address to scan
        limit: Number of transactions to analyze
    
    Returns:
        Risk assessment for the account
    """
    try:
        if not ingestor or not risk_engine:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Get transactions
        transactions_raw = await ingestor.get_recent_transactions(account_address, limit)
        
        # Convert to TransactionData objects
        transactions = [
            TransactionData(**tx) for tx in transactions_raw
        ]
        
        # Scan for risks
        risk_assessment = await risk_engine.scan_account_risks(
            account_address,
            transactions
        )
        
        return risk_assessment
        
    except Exception as e:
        logger.error(f"Error scanning risks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/risk/transaction")
async def assess_transaction_risk(transaction_data: dict):
    """
    Assess risk of a specific transaction.
    
    Args:
        transaction_data: Transaction data
    
    Returns:
        Risk assessment
    """
    try:
        if not risk_engine:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        tx = TransactionData(**transaction_data)
        assessment = await risk_engine.assess_transaction_risk(tx)
        
        return assessment.dict()
        
    except Exception as e:
        logger.error(f"Error assessing transaction risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/yield/optimize")
async def optimize_yield(
    token_symbol: str,
    include_positions: bool = Query(default=False)
):
    """
    Find optimal yield opportunities for a token.
    
    Args:
        token_symbol: Token to optimize yield for
        include_positions: Include current positions in analysis
    
    Returns:
        List of yield opportunities
    """
    try:
        if not yield_optimizer:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        current_positions = None  # Would fetch from user's account if include_positions
        
        opportunities = await yield_optimizer.optimize_yield(
            token_symbol,
            current_positions
        )
        
        return {
            "token": token_symbol,
            "opportunities": [opp.dict() for opp in opportunities],
            "best_opportunity": opportunities[0].dict() if opportunities else None
        }
        
    except Exception as e:
        logger.error(f"Error optimizing yield: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/portfolio/rebalance")
async def rebalance_portfolio(
    current_allocation: dict,
    risk_profile: str = Query(default="MODERATE", regex="^(CONSERVATIVE|MODERATE|AGGRESSIVE)$"),
    target_allocation: Optional[dict] = None
):
    """
    Get portfolio rebalancing suggestions.
    
    Args:
        current_allocation: Current portfolio allocation
        risk_profile: Risk profile (CONSERVATIVE, MODERATE, AGGRESSIVE)
        target_allocation: Optional target allocation
    
    Returns:
        Rebalancing suggestions
    """
    try:
        if not portfolio_service:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        rebalance = await portfolio_service.suggest_rebalancing(
            current_allocation,
            risk_profile,
            target_allocation
        )
        
        return rebalance.dict()
        
    except Exception as e:
        logger.error(f"Error rebalancing portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sentiment/{token_symbol}", response_model=SentimentAnalysis)
async def get_sentiment(
    token_symbol: str,
    sources: Optional[str] = Query(default=None, description="Comma-separated sources")
):
    """
    Analyze sentiment for a token.
    
    Args:
        token_symbol: Token to analyze
        sources: Optional comma-separated list of sources
    
    Returns:
        Sentiment analysis result
    """
    try:
        if not sentiment_analyzer:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        source_list = sources.split(",") if sources else None
        
        analysis = await sentiment_analyzer.analyze_sentiment(
            token_symbol,
            source_list
        )
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sentiment/compare")
async def compare_sentiment(tokens: List[str]):
    """
    Compare sentiment across multiple tokens.
    
    Args:
        tokens: List of token symbols
    
    Returns:
        Comparison results
    """
    try:
        if not sentiment_analyzer:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        comparison = await sentiment_analyzer.compare_sentiment(tokens)
        
        return comparison
        
    except Exception as e:
        logger.error(f"Error comparing sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# v0.2.0 NEW ENDPOINTS
# ============================================================================

@app.post("/zkml/proof/generate")
async def generate_proof(request: ProofRequest):
    """
    Generate a zero-knowledge proof for model inference.
    
    Args:
        request: Proof generation request
    
    Returns:
        Generated proof
    """
    try:
        if not proof_generator:
            raise HTTPException(status_code=503, detail="zkML service not initialized")
        
        proof = await proof_generator.generate_proof(request)
        
        return proof.dict()
        
    except Exception as e:
        logger.error(f"Error generating proof: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/zkml/proof/verify")
async def verify_proof(proof_id: str):
    """
    Verify a zero-knowledge proof.
    
    Args:
        proof_id: ID of the proof to verify
    
    Returns:
        Verification result
    """
    try:
        if not proof_generator or not proof_verifier:
            raise HTTPException(status_code=503, detail="zkML service not initialized")
        
        # Get the proof
        proof = proof_generator.get_proof(proof_id)
        if not proof:
            raise HTTPException(status_code=404, detail="Proof not found")
        
        # Verify it
        result = await proof_verifier.verify_proof(proof)
        
        return result.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying proof: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/zkml/proof/{proof_id}")
async def get_proof(proof_id: str):
    """
    Get a proof by ID.
    
    Args:
        proof_id: Proof identifier
    
    Returns:
        Proof object
    """
    try:
        if not proof_generator:
            raise HTTPException(status_code=503, detail="zkML service not initialized")
        
        proof = proof_generator.get_proof(proof_id)
        if not proof:
            raise HTTPException(status_code=404, detail="Proof not found")
        
        return proof.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching proof: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/multichain/chains")
async def get_supported_chains():
    """
    Get list of supported blockchain networks.
    
    Returns:
        List of supported chains
    """
    try:
        if not multichain_manager:
            raise HTTPException(status_code=503, detail="Multi-chain service not initialized")
        
        chains = multichain_manager.get_supported_chains()
        chain_info = await multichain_manager.get_all_chain_info()
        
        return {
            "supported_chains": [chain.value for chain in chains],
            "chain_info": {chain.value: info for chain, info in chain_info.items()}
        }
        
    except Exception as e:
        logger.error(f"Error fetching chain info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/multichain/{chain}/transaction/{tx_hash}")
async def get_multichain_transaction(chain: str, tx_hash: str):
    """
    Get transaction from a specific blockchain.
    
    Args:
        chain: Blockchain name (ethereum, polygon, arbitrum, base)
        tx_hash: Transaction hash
    
    Returns:
        Transaction details
    """
    try:
        if not multichain_manager:
            raise HTTPException(status_code=503, detail="Multi-chain service not initialized")
        
        # Convert chain string to ChainType
        try:
            chain_type = ChainType(chain.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported chain: {chain}")
        
        transaction = await multichain_manager.get_transaction(chain_type, tx_hash)
        
        return transaction.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/multichain/{chain}/balance/{address}")
async def get_multichain_balance(
    chain: str,
    address: str,
    token_address: Optional[str] = Query(default=None)
):
    """
    Get balance for an address on a specific blockchain.
    
    Args:
        chain: Blockchain name
        address: Wallet address
        token_address: Optional token contract address
    
    Returns:
        Balance information
    """
    try:
        if not multichain_manager:
            raise HTTPException(status_code=503, detail="Multi-chain service not initialized")
        
        try:
            chain_type = ChainType(chain.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported chain: {chain}")
        
        balance = await multichain_manager.get_balance(chain_type, address, token_address)
        
        return {
            "chain": chain,
            "address": address,
            "token_address": token_address,
            "balance": balance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/multichain/balance/{address}")
async def get_all_chain_balances(address: str):
    """
    Get balances across all supported chains.
    
    Args:
        address: Wallet address
    
    Returns:
        Balances for all chains
    """
    try:
        if not multichain_manager:
            raise HTTPException(status_code=503, detail="Multi-chain service not initialized")
        
        balances = await multichain_manager.get_all_balances(address)
        
        return {
            "address": address,
            "balances": {chain.value: balance for chain, balance in balances.items()}
        }
        
    except Exception as e:
        logger.error(f"Error fetching balances: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def list_models():
    """
    List available prediction models.
    
    Returns:
        List of available models
    """
    return {
        "models": [
            {
                "id": "predicore-v1",
                "name": "PrediCore v1",
                "type": "ai_powered",
                "description": "OpenAI-powered predictive model for DeFi",
                "status": "active" if model else "inactive"
            },
            {
                "id": "risk-engine-v1",
                "name": "Risk Engine v1",
                "type": "risk_analysis",
                "description": "Multi-layer risk detection engine",
                "status": "active" if risk_engine else "inactive"
            }
        ]
    }


@app.post("/models/{model_id}/predict")
async def predict_with_model(model_id: str, token_symbol: str):
    """
    Get prediction using a specific model.
    
    Args:
        model_id: Model identifier
        token_symbol: Token to predict
    
    Returns:
        Prediction result
    """
    try:
        if model_id == "predicore-v1":
            if not model or not ingestor:
                raise HTTPException(status_code=503, detail="Model not initialized")
            
            market_data = await ingestor.fetch_data(token_symbol)
            prediction = await model.predict(market_data)
            
            # Generate zkML proof for this prediction
            if proof_generator:
                try:
                    proof_request = ProofRequest(
                        model_id=model_id,
                        input_data={"token": token_symbol, "market_data": market_data},
                        output_data=prediction,
                        proof_type=ProofType.INFERENCE
                    )
                    proof = await proof_generator.generate_proof(proof_request)
                    prediction["zkml_proof_id"] = proof.proof_id
                except Exception as e:
                    logger.warning(f"Could not generate proof: {e}")
            
            return {
                "model_id": model_id,
                "token": token_symbol,
                "prediction": prediction
            }
        else:
            raise HTTPException(status_code=404, detail="Model not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in model prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/summary")
async def get_analytics_summary():
    """
    Get analytics summary across all services.
    
    Returns:
        Analytics summary
    """
    try:
        summary = {
            "version": "0.2.0",
            "services": {
                "predicore": "active" if model else "inactive",
                "risk_engine": "active" if risk_engine else "inactive",
                "yield_optimizer": "active" if yield_optimizer else "inactive",
                "sentiment_analyzer": "active" if sentiment_analyzer else "inactive",
                "zkml": "active" if proof_generator else "inactive",
                "multichain": "active" if multichain_manager else "inactive",
            },
            "features": [
                "AI-Powered Predictions",
                "Multi-Chain Support",
                "zkML Verification",
                "Risk Detection",
                "Yield Optimization",
                "Sentiment Analysis",
                "Portfolio Management"
            ]
        }
        
        if multichain_manager:
            summary["supported_chains"] = [
                chain.value for chain in multichain_manager.get_supported_chains()
            ]
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.log_level == "DEBUG" else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )
