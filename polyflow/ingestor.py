"""
PolyFlow - Data Ingestion Layer
Monitors live Solana transactions and aggregates market data.
"""
import asyncio
import json
from typing import Dict, List, Optional, Callable
from datetime import datetime
from solders.pubkey import Pubkey
from solders.signature import Signature
from solana.rpc.async_api import AsyncClient
from solana.rpc.websocket_api import connect
from solana.rpc.commitment import Confirmed

from config import settings
from utils.logger import logger


class DataIngestor:
    """
    High-throughput data ingestion layer for PolyMind.
    Monitors live Solana transactions and aggregates market data.
    """
    
    def __init__(self):
        self.solana_client: Optional[AsyncClient] = None
        self.subscription_id: Optional[int] = None
        self.transaction_callbacks: List[Callable] = []
        self.is_monitoring = False
        
    async def _get_client(self) -> AsyncClient:
        """Get or create Solana RPC client."""
        if self.solana_client is None:
            self.solana_client = AsyncClient(settings.solana_rpc_url)
            logger.info(f"Connected to Solana RPC: {settings.solana_rpc_url}")
        return self.solana_client
    
    async def fetch_token_data(self, token_mint: str) -> Dict:
        """
        Fetch current token data from Solana blockchain.
        
        Args:
            token_mint: Token mint address (e.g., "So11111111111111111111111111111111111111112" for SOL)
        
        Returns:
            Dictionary containing token price, volume, and market data
        """
        try:
            client = await self._get_client()
            
            # Get token account info
            pubkey = Pubkey.from_string(token_mint)
            account_info = await client.get_account_info(pubkey, commitment=Confirmed)
            
            # Get recent transaction signatures for volume calculation
            signatures = await client.get_signatures_for_address(
                pubkey,
                limit=100,
                commitment=Confirmed
            )
            
            # Calculate 24h volume (simplified - would need DEX pool analysis for accurate data)
            recent_txs = len(signatures.value)
            
            return {
                "token_mint": token_mint,
                "timestamp": datetime.utcnow().isoformat(),
                "recent_transactions": recent_txs,
                "account_exists": account_info.value is not None,
                "data_source": "Solana RPC"
            }
        except Exception as e:
            logger.error(f"Error fetching token data for {token_mint}: {e}")
            raise
    
    async def fetch_data(self, symbol: str) -> Dict:
        """
        Fetch aggregated market data for a token symbol.
        Maps common symbols to Solana token mints.
        
        Args:
            symbol: Token symbol (e.g., "SOL", "USDC", or mint address)
        
        Returns:
            Dictionary containing market data
        """
        # Map common symbols to Solana token mints
        token_mints = {
            "SOL": "So11111111111111111111111111111111111111112",
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        }
        
        token_mint = token_mints.get(symbol.upper(), symbol)
        
        try:
            token_data = await self.fetch_token_data(token_mint)
            
            # Get recent block data for volume estimation
            client = await self._get_client()
            recent_block = await client.get_block_height(commitment=Confirmed)
            
            return {
                "symbol": symbol,
                "token_mint": token_mint,
                "price": None,  # Would need DEX price oracle integration
                "volume_24h": token_data.get("recent_transactions", 0) * 1000,  # Estimate
                "liquidity_depth": None,  # Would need AMM pool analysis
                "sentiment_score": 0.5,  # Placeholder - would integrate sentiment API
                "block_height": recent_block,
                "timestamp": token_data.get("timestamp"),
                "data_source": "Solana Mainnet"
            }
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            # Return fallback data
            return {
                "symbol": symbol,
                "price": None,
                "volume_24h": 0,
                "liquidity_depth": None,
                "sentiment_score": 0.5,
                "error": str(e)
            }
    
    async def monitor_transactions(
        self,
        account_address: Optional[str] = None,
        callback: Optional[Callable] = None
    ):
        """
        Monitor live Solana transactions via WebSocket.
        
        Args:
            account_address: Specific account to monitor (None = monitor all)
            callback: Function to call when transaction is received
        """
        if callback:
            self.transaction_callbacks.append(callback)
        
        if self.is_monitoring:
            logger.warning("Transaction monitoring already active")
            return
        
        self.is_monitoring = True
        logger.info("Starting live transaction monitoring...")
        
        try:
            async with connect(settings.solana_ws_url) as websocket:
                # Subscribe to account notifications or program logs
                if account_address:
                    await websocket.account_subscribe(
                        Pubkey.from_string(account_address),
                        commitment=Confirmed
                    )
                else:
                    # Subscribe to program logs (monitor all transactions)
                    await websocket.logs_subscribe(
                        commitment=Confirmed
                    )
                
                logger.info("WebSocket subscription active")
                
                async for notification in websocket:
                    if callback:
                        try:
                            await callback(notification)
                        except Exception as e:
                            logger.error(f"Error in transaction callback: {e}")
                    
                    # Also notify all registered callbacks
                    for cb in self.transaction_callbacks:
                        try:
                            await cb(notification)
                        except Exception as e:
                            logger.error(f"Error in registered callback: {e}")
                            
        except Exception as e:
            logger.error(f"WebSocket monitoring error: {e}")
            self.is_monitoring = False
            raise
    
    async def get_recent_transactions(
        self,
        account_address: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent transactions for an account.
        
        Args:
            account_address: Account address to query
            limit: Maximum number of transactions to return
        
        Returns:
            List of transaction dictionaries
        """
        try:
            client = await self._get_client()
            pubkey = Pubkey.from_string(account_address)
            
            signatures = await client.get_signatures_for_address(
                pubkey,
                limit=limit,
                commitment=Confirmed
            )
            
            transactions = []
            for sig_info in signatures.value:
                tx = await client.get_transaction(
                    Signature.from_string(str(sig_info.signature)),
                    commitment=Confirmed,
                    max_supported_transaction_version=0
                )
                
                if tx.value:
                    transactions.append({
                        "signature": str(sig_info.signature),
                        "slot": sig_info.slot,
                        "block_time": sig_info.block_time,
                        "confirmation_status": sig_info.confirmation_status,
                        "err": tx.value.transaction.meta.err if tx.value.transaction.meta else None
                    })
            
            return transactions
        except Exception as e:
            logger.error(f"Error fetching recent transactions: {e}")
            return []
    
    async def close(self):
        """Close connections and cleanup."""
        if self.solana_client:
            await self.solana_client.close()
            self.solana_client = None
        
        self.is_monitoring = False
        logger.info("DataIngestor connections closed")
