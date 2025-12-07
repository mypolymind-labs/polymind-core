"""
Multi-Chain Manager
Manages multiple blockchain adapters and provides unified interface.
"""

from typing import Dict, List, Optional, Any
from .base import BlockchainAdapter, ChainType, Transaction, TokenInfo
from .ethereum import EthereumAdapter
from .polygon import PolygonAdapter
from .arbitrum import ArbitrumAdapter
from .base_chain import BaseChainAdapter
from utils.logger import get_logger

logger = get_logger(__name__)


class MultiChainManager:
    """
    Manages multiple blockchain adapters.
    Provides unified interface for cross-chain operations.
    """

    def __init__(self):
        """Initialize multi-chain manager."""
        self.adapters: Dict[ChainType, BlockchainAdapter] = {}
        logger.info("MultiChainManager initialized")

    def add_chain(
        self,
        chain_type: ChainType,
        rpc_url: str,
        ws_url: Optional[str] = None
    ) -> None:
        """
        Add a blockchain adapter.

        Args:
            chain_type: Type of blockchain
            rpc_url: RPC endpoint URL
            ws_url: WebSocket endpoint URL (optional)
        """
        try:
            if chain_type == ChainType.ETHEREUM:
                adapter = EthereumAdapter(rpc_url, ws_url)
            elif chain_type == ChainType.POLYGON:
                adapter = PolygonAdapter(rpc_url, ws_url)
            elif chain_type == ChainType.ARBITRUM:
                adapter = ArbitrumAdapter(rpc_url, ws_url)
            elif chain_type == ChainType.BASE:
                adapter = BaseChainAdapter(rpc_url, ws_url)
            else:
                raise ValueError(f"Unsupported chain type: {chain_type}")

            self.adapters[chain_type] = adapter
            logger.info(f"Added {chain_type.value} chain adapter")

        except Exception as e:
            logger.error(f"Failed to add {chain_type.value} adapter: {str(e)}")
            raise

    def get_adapter(self, chain_type: ChainType) -> Optional[BlockchainAdapter]:
        """
        Get adapter for a specific chain.

        Args:
            chain_type: Type of blockchain

        Returns:
            Blockchain adapter or None if not found
        """
        return self.adapters.get(chain_type)

    async def get_transaction(self, chain_type: ChainType, tx_hash: str) -> Transaction:
        """
        Get transaction from specific chain.

        Args:
            chain_type: Blockchain type
            tx_hash: Transaction hash

        Returns:
            Transaction object
        """
        adapter = self.get_adapter(chain_type)
        if not adapter:
            raise ValueError(f"No adapter found for chain: {chain_type}")

        return await adapter.get_transaction(tx_hash)

    async def get_transactions(
        self,
        chain_type: ChainType,
        address: str,
        limit: int = 10
    ) -> List[Transaction]:
        """
        Get transactions for an address on specific chain.

        Args:
            chain_type: Blockchain type
            address: Wallet address
            limit: Maximum number of transactions

        Returns:
            List of transactions
        """
        adapter = self.get_adapter(chain_type)
        if not adapter:
            raise ValueError(f"No adapter found for chain: {chain_type}")

        return await adapter.get_transactions(address, limit)

    async def get_all_transactions(
        self,
        address: str,
        limit_per_chain: int = 10
    ) -> Dict[ChainType, List[Transaction]]:
        """
        Get transactions for an address across all chains.

        Args:
            address: Wallet address
            limit_per_chain: Maximum transactions per chain

        Returns:
            Dictionary mapping chain type to transactions
        """
        results = {}

        for chain_type, adapter in self.adapters.items():
            try:
                transactions = await adapter.get_transactions(address, limit_per_chain)
                results[chain_type] = transactions
            except Exception as e:
                logger.error(f"Error fetching transactions from {chain_type.value}: {str(e)}")
                results[chain_type] = []

        return results

    async def get_balance(
        self,
        chain_type: ChainType,
        address: str,
        token_address: Optional[str] = None
    ) -> float:
        """
        Get balance for an address on specific chain.

        Args:
            chain_type: Blockchain type
            address: Wallet address
            token_address: Token contract address (None for native token)

        Returns:
            Balance amount
        """
        adapter = self.get_adapter(chain_type)
        if not adapter:
            raise ValueError(f"No adapter found for chain: {chain_type}")

        return await adapter.get_balance(address, token_address)

    async def get_all_balances(
        self,
        address: str,
        token_addresses: Optional[Dict[ChainType, str]] = None
    ) -> Dict[ChainType, float]:
        """
        Get balances across all chains.

        Args:
            address: Wallet address
            token_addresses: Optional mapping of chain to token address

        Returns:
            Dictionary mapping chain type to balance
        """
        results = {}

        for chain_type, adapter in self.adapters.items():
            try:
                token_addr = token_addresses.get(chain_type) if token_addresses else None
                balance = await adapter.get_balance(address, token_addr)
                results[chain_type] = balance
            except Exception as e:
                logger.error(f"Error fetching balance from {chain_type.value}: {str(e)}")
                results[chain_type] = 0.0

        return results

    async def get_token_info(
        self,
        chain_type: ChainType,
        token_address: str
    ) -> TokenInfo:
        """
        Get token information from specific chain.

        Args:
            chain_type: Blockchain type
            token_address: Token contract address

        Returns:
            Token information
        """
        adapter = self.get_adapter(chain_type)
        if not adapter:
            raise ValueError(f"No adapter found for chain: {chain_type}")

        return await adapter.get_token_info(token_address)

    async def get_chain_info(self, chain_type: ChainType) -> Dict[str, Any]:
        """
        Get information about a specific chain.

        Args:
            chain_type: Blockchain type

        Returns:
            Chain information
        """
        adapter = self.get_adapter(chain_type)
        if not adapter:
            raise ValueError(f"No adapter found for chain: {chain_type}")

        return await adapter.get_chain_info()

    async def get_all_chain_info(self) -> Dict[ChainType, Dict[str, Any]]:
        """
        Get information about all configured chains.

        Returns:
            Dictionary mapping chain type to chain info
        """
        results = {}

        for chain_type, adapter in self.adapters.items():
            try:
                info = await adapter.get_chain_info()
                results[chain_type] = info
            except Exception as e:
                logger.error(f"Error fetching info from {chain_type.value}: {str(e)}")
                results[chain_type] = {"error": str(e)}

        return results

    def get_supported_chains(self) -> List[ChainType]:
        """
        Get list of currently supported chains.

        Returns:
            List of chain types
        """
        return list(self.adapters.keys())

    def is_chain_supported(self, chain_type: ChainType) -> bool:
        """
        Check if a chain is supported.

        Args:
            chain_type: Blockchain type

        Returns:
            True if chain is supported
        """
        return chain_type in self.adapters
