"""
Base Chain blockchain adapter.
"""

from .ethereum import EthereumAdapter
from .base import ChainType


class BaseChainAdapter(EthereumAdapter):
    """
    Adapter for Base network (Coinbase L2).
    Inherits from EthereumAdapter since Base is EVM-compatible.
    """

    def _get_chain_type(self) -> ChainType:
        """Get chain type."""
        return ChainType.BASE
