"""
Ethereum blockchain adapter.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from web3 import Web3
from web3.exceptions import TransactionNotFound

from .base import BlockchainAdapter, ChainType, Transaction, TokenInfo, BlockInfo
from utils.logger import get_logger

logger = get_logger(__name__)


class EthereumAdapter(BlockchainAdapter):
    """Adapter for Ethereum and EVM-compatible chains."""

    def __init__(self, rpc_url: str, ws_url: Optional[str] = None):
        """Initialize Ethereum adapter."""
        super().__init__(rpc_url, ws_url)
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not self.w3.is_connected():
            logger.warning(f"Failed to connect to Ethereum RPC: {rpc_url}")
        else:
            logger.info(f"Connected to Ethereum RPC: {rpc_url}")

    def _get_chain_type(self) -> ChainType:
        """Get chain type."""
        return ChainType.ETHEREUM

    async def get_transaction(self, tx_hash: str) -> Transaction:
        """Get transaction by hash."""
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            block = self.w3.eth.get_block(tx['blockNumber'])

            return Transaction(
                chain=self.chain_type,
                hash=tx_hash,
                from_address=tx['from'],
                to_address=tx.get('to'),
                value=float(self.w3.from_wei(tx['value'], 'ether')),
                gas_price=float(self.w3.from_wei(tx.get('gasPrice', 0), 'gwei')),
                gas_used=receipt['gasUsed'],
                block_number=tx['blockNumber'],
                timestamp=datetime.fromtimestamp(block['timestamp']),
                status='success' if receipt['status'] == 1 else 'failed',
                data={
                    'input': tx.get('input'),
                    'nonce': tx.get('nonce'),
                    'transaction_index': tx.get('transactionIndex'),
                }
            )

        except TransactionNotFound:
            raise ValueError(f"Transaction not found: {tx_hash}")
        except Exception as e:
            logger.error(f"Error fetching transaction {tx_hash}: {str(e)}")
            raise

    async def get_transactions(
        self,
        address: str,
        limit: int = 10,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None
    ) -> List[Transaction]:
        """
        Get transactions for an address.
        
        Note: This is a simplified implementation. In production, you would use
        services like Etherscan API or The Graph for efficient transaction indexing.
        """
        transactions = []
        
        try:
            # Get latest block if not specified
            if end_block is None:
                end_block = await self.get_latest_block_number()
            
            if start_block is None:
                start_block = max(0, end_block - 1000)  # Look back 1000 blocks

            # This is inefficient for production - use indexing service instead
            logger.warning("Using inefficient block scanning for transactions. Use indexing service in production.")
            
            # Scan recent blocks (limited for performance)
            scan_limit = min(100, end_block - start_block)
            for block_num in range(end_block, end_block - scan_limit, -1):
                if len(transactions) >= limit:
                    break
                    
                block = self.w3.eth.get_block(block_num, full_transactions=True)
                
                for tx in block['transactions']:
                    if tx['from'].lower() == address.lower() or \
                       (tx.get('to') and tx['to'].lower() == address.lower()):
                        
                        receipt = self.w3.eth.get_transaction_receipt(tx['hash'])
                        
                        transactions.append(Transaction(
                            chain=self.chain_type,
                            hash=tx['hash'].hex(),
                            from_address=tx['from'],
                            to_address=tx.get('to'),
                            value=float(self.w3.from_wei(tx['value'], 'ether')),
                            gas_price=float(self.w3.from_wei(tx.get('gasPrice', 0), 'gwei')),
                            gas_used=receipt['gasUsed'],
                            block_number=block_num,
                            timestamp=datetime.fromtimestamp(block['timestamp']),
                            status='success' if receipt['status'] == 1 else 'failed',
                        ))
                        
                        if len(transactions) >= limit:
                            break

            return transactions

        except Exception as e:
            logger.error(f"Error fetching transactions for {address}: {str(e)}")
            return []

    async def get_token_info(self, token_address: str) -> TokenInfo:
        """Get ERC20 token information."""
        try:
            # ERC20 ABI (minimal)
            erc20_abi = [
                {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
            ]

            contract = self.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc20_abi)

            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()
            decimals = contract.functions.decimals().call()
            total_supply = contract.functions.totalSupply().call()

            return TokenInfo(
                chain=self.chain_type,
                address=token_address,
                symbol=symbol,
                name=name,
                decimals=decimals,
                total_supply=float(total_supply / (10 ** decimals)),
            )

        except Exception as e:
            logger.error(f"Error fetching token info for {token_address}: {str(e)}")
            raise

    async def get_balance(self, address: str, token_address: Optional[str] = None) -> float:
        """Get balance for an address."""
        try:
            if token_address is None:
                # Get native ETH balance
                balance_wei = self.w3.eth.get_balance(Web3.to_checksum_address(address))
                return float(self.w3.from_wei(balance_wei, 'ether'))
            else:
                # Get ERC20 token balance
                erc20_abi = [
                    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], 
                     "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
                    {"constant": True, "inputs": [], "name": "decimals", 
                     "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
                ]
                
                contract = self.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc20_abi)
                balance = contract.functions.balanceOf(Web3.to_checksum_address(address)).call()
                decimals = contract.functions.decimals().call()
                
                return float(balance / (10 ** decimals))

        except Exception as e:
            logger.error(f"Error fetching balance for {address}: {str(e)}")
            return 0.0

    async def get_block(self, block_number: int) -> BlockInfo:
        """Get block information."""
        try:
            block = self.w3.eth.get_block(block_number)

            return BlockInfo(
                chain=self.chain_type,
                block_number=block_number,
                timestamp=datetime.fromtimestamp(block['timestamp']),
                transaction_count=len(block['transactions']),
                hash=block['hash'].hex(),
                parent_hash=block['parentHash'].hex(),
                metadata={
                    'gas_used': block.get('gasUsed'),
                    'gas_limit': block.get('gasLimit'),
                    'miner': block.get('miner'),
                }
            )

        except Exception as e:
            logger.error(f"Error fetching block {block_number}: {str(e)}")
            raise

    async def get_latest_block_number(self) -> int:
        """Get latest block number."""
        try:
            return self.w3.eth.block_number
        except Exception as e:
            logger.error(f"Error fetching latest block number: {str(e)}")
            raise

    async def estimate_gas(self, transaction: Dict[str, Any]) -> int:
        """Estimate gas for a transaction."""
        try:
            # Convert addresses to checksum format
            if 'from' in transaction:
                transaction['from'] = Web3.to_checksum_address(transaction['from'])
            if 'to' in transaction:
                transaction['to'] = Web3.to_checksum_address(transaction['to'])

            gas_estimate = self.w3.eth.estimate_gas(transaction)
            return gas_estimate

        except Exception as e:
            logger.error(f"Error estimating gas: {str(e)}")
            raise

    async def subscribe_to_transactions(self, address: str, callback: callable) -> None:
        """
        Subscribe to real-time transactions.
        
        Note: Requires WebSocket connection. This is a placeholder implementation.
        """
        if not self.ws_url:
            logger.warning("WebSocket URL not provided, cannot subscribe to transactions")
            return

        logger.info(f"Subscribing to transactions for {address} (WebSocket implementation needed)")
        # WebSocket subscription implementation would go here
        # This would use web3.py's WebSocket provider and event filters
