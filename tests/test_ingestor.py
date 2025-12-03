"""
Tests for DataIngestor (PolyFlow).
"""
import pytest
from unittest.mock import AsyncMock, patch
from solders.pubkey import Pubkey
from solders.signature import Signature

from polyflow.ingestor import DataIngestor
from tests.conftest import mock_solana_client, sample_market_data


@pytest.mark.asyncio
async def test_fetch_token_data(data_ingestor, mock_solana_client):
    """Test fetching token data from Solana."""
    # Mock account info response
    mock_solana_client.get_account_info.return_value = AsyncMock(value=MagicMock())
    mock_solana_client.get_signatures_for_address.return_value = AsyncMock(
        value=[MagicMock(signature=Signature.default())] * 10
    )
    
    result = await data_ingestor.fetch_token_data("So11111111111111111111111111111111111111112")
    
    assert result["token_mint"] == "So11111111111111111111111111111111111111112"
    assert "recent_transactions" in result
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_fetch_data(data_ingestor, mock_solana_client):
    """Test fetching market data for a token symbol."""
    mock_solana_client.get_account_info.return_value = AsyncMock(value=MagicMock())
    mock_solana_client.get_signatures_for_address.return_value = AsyncMock(
        value=[MagicMock(signature=Signature.default())] * 10
    )
    mock_solana_client.get_block_height.return_value = 200000000
    
    result = await data_ingestor.fetch_data("SOL")
    
    assert result["symbol"] == "SOL"
    assert "volume_24h" in result
    assert "data_source" in result


@pytest.mark.asyncio
async def test_get_recent_transactions(data_ingestor, mock_solana_client):
    """Test getting recent transactions for an account."""
    # Mock signatures response
    mock_sig = MagicMock()
    mock_sig.signature = Signature.default()
    mock_sig.slot = 200000000
    mock_sig.block_time = 1704067200
    mock_sig.confirmation_status = "confirmed"
    
    mock_solana_client.get_signatures_for_address.return_value = AsyncMock(
        value=[mock_sig] * 5
    )
    
    # Mock transaction response
    mock_tx = MagicMock()
    mock_tx.value.transaction.meta.err = None
    mock_solana_client.get_transaction.return_value = mock_tx
    
    transactions = await data_ingestor.get_recent_transactions("test_account", limit=5)
    
    assert len(transactions) <= 5
    if transactions:
        assert "signature" in transactions[0]
        assert "slot" in transactions[0]


@pytest.mark.asyncio
async def test_fetch_data_error_handling(data_ingestor, mock_solana_client):
    """Test error handling in fetch_data."""
    mock_solana_client.get_account_info.side_effect = Exception("RPC Error")
    
    result = await data_ingestor.fetch_data("INVALID")
    
    assert result["symbol"] == "INVALID"
    assert "error" in result or result.get("volume_24h") == 0


@pytest.mark.asyncio
async def test_close_connection(data_ingestor, mock_solana_client):
    """Test closing connections."""
    await data_ingestor.close()
    
    assert data_ingestor.solana_client is None
    assert not data_ingestor.is_monitoring

