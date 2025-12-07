"""
Base blockchain adapter interface.
Defines the contract that all chain adapters must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel
from datetime import datetime


class ChainType(str, Enum):
    """Supported blockchain types."""
    SOLANA = "solana"
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    BASE = "base"
    AVALANCHE = "avalanche"


class Transaction(BaseModel):
    """Universal transaction model."""
    chain: ChainType
    hash: str
    from_address: str
    to_address: Optional[str] = None
    value: float
    gas_price: Optional[float] = None
    gas_used: Optional[int] = None
    block_number: int
    timestamp: datetime
    status: str
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TokenInfo(BaseModel):
    """Universal token information model."""
    chain: ChainType
    address: str
    symbol: str
    name: str
    decimals: int
    total_supply: Optional[float] = None
    price_usd: Optional[float] = None
    market_cap: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class BlockInfo(BaseModel):
    """Universal block information model."""
    chain: ChainType
    block_number: int
    timestamp: datetime
    transaction_count: int
    hash: str
    parent_hash: str
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BlockchainAdapter(ABC):
    """
    Abstract base class for blockchain adapters.
    All chain-specific adapters must implement this interface.
    """

    def __init__(self, rpc_url: str, ws_url: Optional[str] = None):
        """
        Initialize blockchain adapter.
        
        Args:
            rpc_url: RPC endpoint URL
            ws_url: WebSocket endpoint URL (optional)
        """
        self.rpc_url = rpc_url
        self.ws_url = ws_url
        self.chain_type = self._get_chain_type()

    @abstractmethod
    def _get_chain_type(self) -> ChainType:
        """Get the chain type for this adapter."""
        pass

    @abstractmethod
    async def get_transaction(self, tx_hash: str) -> Transaction:
        """
        Get transaction by hash.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction object
        """
        pass

    @abstractmethod
    async def get_transactions(
        self, 
        address: str, 
        limit: int = 10,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None
    ) -> List[Transaction]:
        """
        Get transactions for an address.
        
        Args:
            address: Wallet/contract address
            limit: Maximum number of transactions
            start_block: Starting block number
            end_block: Ending block number
            
        Returns:
            List of transactions
        """
        pass

    @abstractmethod
    async def get_token_info(self, token_address: str) -> TokenInfo:
        """
        Get token information.
        
        Args:
            token_address: Token contract address
            
        Returns:
            Token information
        """
        pass

    @abstractmethod
    async def get_balance(self, address: str, token_address: Optional[str] = None) -> float:
        """
        Get balance for an address.
        
        Args:
            address: Wallet address
            token_address: Token contract address (None for native token)
            
        Returns:
            Balance amount
        """
        pass

    @abstractmethod
    async def get_block(self, block_number: int) -> BlockInfo:
        """
        Get block information.
        
        Args:
            block_number: Block number
            
        Returns:
            Block information
        """
        pass

    @abstractmethod
    async def get_latest_block_number(self) -> int:
        """
        Get the latest block number.
        
        Returns:
            Latest block number
        """
        pass

    @abstractmethod
    async def estimate_gas(self, transaction: Dict[str, Any]) -> int:
        """
        Estimate gas for a transaction.
        
        Args:
            transaction: Transaction parameters
            
        Returns:
            Estimated gas amount
        """
        pass

    @abstractmethod
    async def subscribe_to_transactions(
        self, 
        address: str, 
        callback: callable
    ) -> None:
        """
        Subscribe to real-time transactions for an address.
        
        Args:
            address: Address to monitor
            callback: Callback function for new transactions
        """
        pass

    async def get_chain_info(self) -> Dict[str, Any]:
        """
        Get general chain information.
        
        Returns:
            Chain information dictionary
        """
        latest_block = await self.get_latest_block_number()
        return {
            "chain": self.chain_type.value,
            "rpc_url": self.rpc_url,
            "latest_block": latest_block,
        }
