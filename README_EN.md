# Chamby Faucet Bot

A Telegram bot for distributing **Chamby (CHAMBY)** tokens on the TON network.

## Architecture

The project consists of two parts:

1. **Telegram Bot** (Python) — accepts user requests, checks limits and balances, sends signing commands to the signing service.
2. **Signing Service** (Node.js) — a separate service deployed on a VPS that stores the private key and signs token transfer transactions.

## Installation

### 1. Telegram Bot

```bash
# Clone the repository
git clone https://github.com/sbercoin-one/chamby-faucet-bot.git
cd chamby-faucet-bot

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and fill in the configuration
cp .env.example .env
# Edit .env — fill in all required values

# Start the bot
python bot.py
```

### 2. Signing Service

```bash
cd signing-service

# Copy and fill in the configuration
cp .env.example .env
# Edit .env

# Run with Docker
docker-compose up -d

# Or without Docker
npm install
node signing_service.js
```

## Configuration

All secrets are stored in the `.env` file (not committed to git). See `.env.example` for a template.

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather |
| `SENDER_WALLET_ADDRESS` | TON sender wallet address |
| `SENDER_WALLET_SEED` | Wallet seed phrase (24 words) |
| `SIGNING_SERVICE_URL` | Signing service URL (e.g. `http://your-vps-ip:5000`) |
| `SIGNING_SERVICE_API_KEY` | API key for signing service authorization |
| `TON_API_KEY` | toncenter.com API key |

## Bot Commands

- `/start` — welcome message and rules
- `/get_chamby <TON_address>` — receive tokens
- `/stats` — bot statistics

## Signing Service

A standalone Node.js service that stores the wallet private key and signs Jetton token transfer transactions. It is deployed on a separate VPS for security — the seed phrase never leaves the server.

**Stack:** Express.js, tonweb, tonweb-mnemonic

**API Endpoints:**

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `POST` | `/api/v1/send_tokens` | Send Jetton tokens (requires `X-API-Key`) |
| `GET` | `/api/v1/balance` | Sender wallet TON balance (requires `X-API-Key`) |

**Signing service configuration** (file `signing-service/.env`):

| Variable | Description |
|---|---|
| `API_SECRET_KEY` | Secret key for authorizing requests from the bot |
| `SENDER_WALLET_SEED` | Wallet seed phrase (24 words) |
| `CHAMBY_JETTON_CONTRACT` | Chamby Jetton contract address |
| `TONCENTER_API_KEY` | toncenter.com API key |
| `MAX_AMOUNT_PER_TX` | Maximum tokens per transaction (default: 100000) |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per minute (default: 10) |

**Run with Docker:**

```bash
cd signing-service
cp .env.example .env
# Fill in .env
docker-compose up -d
```

## Distribution Rules

- Up to 3 requests per day per user
- 10,000 CHAMBY per request
- Address must be valid (EQ/UQ format)
- Address must not hold any CHAMBY tokens (balance = 0)
