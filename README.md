# Nifty Option Trading Bot (Triple Alignment Strategy)

This is a Python-based algorithmic trading bot designed for Nifty options using the Fyers API v3.

## Best Platforms to Run
For Indian markets (Nifty/BankNifty), latency and reliability are key. The best options are:

1.  **AWS (Mumbai Region - `ap-south-1`)**: Recommended for lowest latency to Fyers/NSE servers. A `t3.micro` or `t3.small` instance is sufficient.
2.  **DigitalOcean (Bangalore Data Center)**: Extremely reliable and cost-effective ($4-$6/month). Use their "Droplets".
3.  **Google Cloud (Mumbai or Delhi Region)**: Another high-performance option with low latency.

## Setup Instructions

### 1. Environment Variables
To keep your credentials secure, the bot uses environment variables. Create a `.env` file or set them on your server:

```bash
export FYERS_CLIENT_ID="your_client_id"
export FYERS_SECRET_KEY="your_secret_key"
export FYERS_ACCESS_TOKEN="your_token"
export EXECUTION_MODE="PAPER" # Change to LIVE only after testing
```

### 2. Running with Docker (Recommended)
Docker ensures the bot runs the same way on any platform.

```bash
# Build the image
docker build -t nifty-bot .

# Run the container
docker run -d \
  --name my-trading-bot \
  -e FYERS_CLIENT_ID="your_id" \
  -e FYERS_SECRET_KEY="your_key" \
  -e FYERS_ACCESS_TOKEN="your_token" \
  -e EXECUTION_MODE="PAPER" \
  nifty-bot
```

### 3. Running Locally
```bash
pip install fyers-apiv3 pandas numpy
python main.py
```

## Strategy Details: "Triple Alignment Breakout"
The bot is configured to run a single, high-probability strategy:
*   **Trend**: Price must be above VWAP and sloping 20 EMA.
*   **Momentum**: RSI > 65 for Bulls, RSI < 35 for Bears.
*   **Volume**: 1.2x breakout above Volume SMA.
*   **Safety**: Automatic halt if **Max Daily Loss (100 pts)** is reached.

## Deployment Roadmap
1.  **DRY_RUN**: Test logic without any API calls (simulated prices).
2.  **PAPER**: Connect to live market data but log trades instead of placing them. (Run for 1-2 weeks).
3.  **LIVE**: Place real orders with 1 lot to start.
