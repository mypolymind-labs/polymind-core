"""
Polygon blockchain adapter.
"""

from typing import Optional
from .ethereum import EthereumAdapter
from .base import ChainType


class PolygonAdapter(EthereumAdapter):
    """
    Adapter for Polygon (Matic) network.
    Inherits from EthereumAdapter since Polygon is EVM-compatible.
    """

    def _get_chain_type(self) -> ChainType:
        """Get chain type."""
        return ChainType.POLYGON
