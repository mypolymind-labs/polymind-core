"""
Arbitrum blockchain adapter.
"""

from .ethereum import EthereumAdapter
from .base import ChainType


class ArbitrumAdapter(EthereumAdapter):
    """
    Adapter for Arbitrum network.
    Inherits from EthereumAdapter since Arbitrum is EVM-compatible.
    """

    def _get_chain_type(self) -> ChainType:
        """Get chain type."""
        return ChainType.ARBITRUM
