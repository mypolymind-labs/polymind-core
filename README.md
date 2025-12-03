# PolyMind Core

This is the brain of the PolyMind Protocol. It houses the AI/ML engines and data pipelines that power the predictive intelligence network.

## Components

- **PolyFlow**: Data ingestion layer. Connects to Solana RPC, monitors live transactions via WebSocket, and aggregates market data.
- **PrediCore**: The predictive engine. Uses OpenAI for intelligent market analysis and forecasting.
- **zkMind**: (Experimental) Zero-knowledge proof generation for model inference verification.

## Features

- 🔴 **Live Solana Transaction Monitoring**: Real-time transaction tracking via WebSocket
- 🤖 **AI-Powered Predictions**: OpenAI integration for intelligent market analysis
- 📊 **Risk Detection Engine**: Multi-layer risk assessment (flash loans, rug pulls, liquidation risks)
- 💰 **Yield Optimization**: Predictive yield opportunities across multiple protocols
- 📈 **Sentiment Analysis**: Social sentiment analysis from multiple sources
- 🎯 **Portfolio Rebalancing**: AI-powered portfolio optimization suggestions
- 📦 **Batch Predictions**: Analyze multiple tokens simultaneously
- 🔌 **WebSocket API**: Real-time updates for connected clients
- 🧪 **Comprehensive Tests**: Full test coverage with pytest
- 🚀 **Production Ready**: Proper error handling, logging, and configuration management

## Setup

### Prerequisites

- Python 3.10+
- Poetry (recommended) or pip
- OpenAI API key (for AI predictions)
- Solana RPC endpoint (default: public mainnet)

### Installation

```bash
# Install dependencies using Poetry
poetry install

# Or using pip
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
# OpenAI API Key (required for AI predictions)
OPENAI_API_KEY=your_openai_api_key_here

# OpenAI Model Configuration
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7

# Solana RPC Configuration
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_WS_URL=wss://api.mainnet-beta.solana.com

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
```

### Running the Server

```bash
# Using Poetry
poetry run python main.py

# Or directly
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### REST API

#### Core Endpoints

- `GET /` - API information and status
- `GET /health` - Health check endpoint

#### Predictions

- `GET /predict/{token_symbol}` - Get prediction for a token (e.g., `/predict/SOL`)
- `POST /predict/batch` - Get predictions for multiple tokens

#### Transactions & Risk

- `GET /transactions/{account_address}` - Get recent transactions for an account
- `POST /analyze/transaction` - Analyze a transaction for risks
- `POST /risk/scan` - Scan an account for risk patterns
- `POST /risk/transaction` - Assess risk of a specific transaction

#### Yield Optimization

- `GET /yield/optimize` - Find optimal yield opportunities for a token

#### Portfolio Management

- `POST /portfolio/rebalance` - Get portfolio rebalancing suggestions

#### Sentiment Analysis

- `GET /sentiment/{token_symbol}` - Analyze sentiment for a token
- `POST /sentiment/compare` - Compare sentiment across multiple tokens

### WebSocket API

- `WS /ws` - Real-time transaction monitoring and updates

#### WebSocket Usage Example

```javascript
const ws = new WebSocket("ws://localhost:8000/ws");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Received:", data);
};

// Subscribe to transactions for an account
ws.send(
  JSON.stringify({
    type: "SUBSCRIBE_TRANSACTIONS",
    account: "YourSolanaAccountAddress",
  })
);
```

## Example Usage

### Get Prediction for SOL

```bash
curl http://localhost:8000/predict/SOL
```

### Get Recent Transactions

```bash
curl http://localhost:8000/transactions/YourAccountAddress?limit=10
```

### Analyze Transaction

```bash
curl -X POST http://localhost:8000/analyze/transaction \
  -H "Content-Type: application/json" \
  -d '{
    "signature": "transaction_signature_here",
    "slot": 123456,
    "block_time": 1234567890
  }'
```

## Architecture

```
┌─────────────────┐
│   FastAPI App   │
│    (main.py)    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│PolyFlow│ │PrediCore│
│Ingestor│ │  Model  │
└───┬───┘ └──┬────┘
    │        │
    │    ┌───▼────┐
    │    │ OpenAI │
    │    │  API   │
    │    └────────┘
    │
┌───▼──────────┐
│ Solana RPC   │
│  & WebSocket │
└──────────────┘
```

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_model.py

# Run with verbose output
pytest -v
```

Test coverage includes:

- Unit tests for all services
- API endpoint tests
- Mock-based testing for external APIs
- Async function testing

## Development

### Project Structure

```
polymind-core/
├── main.py                    # FastAPI application
├── config.py                  # Configuration management
├── polymind/
│   ├── constants.py          # Constants and enums
│   └── types.py              # Type definitions
├── polyflow/
│   └── ingestor.py           # Data ingestion layer
├── predicore/
│   └── model.py              # AI prediction model
├── services/
│   ├── risk_engine.py        # Risk detection service
│   ├── yield_optimizer.py    # Yield optimization service
│   ├── sentiment_analyzer.py # Sentiment analysis service
│   └── portfolio_service.py   # Portfolio rebalancing service
├── utils/
│   └── logger.py             # Logging utilities
├── tests/                    # Test suite
│   ├── test_ingestor.py
│   ├── test_model.py
│   ├── test_risk_engine.py
│   ├── test_yield_optimizer.py
│   ├── test_sentiment_analyzer.py
│   ├── test_portfolio_service.py
│   └── test_api.py
├── pyproject.toml            # Dependencies
├── requirements.txt           # Pip requirements
└── pytest.ini                 # Pytest configuration
```

### Code Quality

The project follows clean code principles:

- **Separation of Concerns**: Services are separated from API layer
- **Type Safety**: Pydantic models for data validation
- **Error Handling**: Comprehensive error handling throughout
- **Logging**: Structured logging for debugging
- **Testing**: High test coverage with pytest
- **Documentation**: Docstrings for all functions and classes

## Notes

- Without OpenAI API key, the system will use fallback heuristic predictions
- Solana RPC endpoints may have rate limits - consider using a dedicated RPC provider for production
- WebSocket connections are managed automatically with reconnection support
