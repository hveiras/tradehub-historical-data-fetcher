# Historical Data Fetcher for Binance Futures

A command-line tool for fetching historical candlestick data from Binance futures markets and storing them in TimescaleDB tables organized by timeframe.

## Features

- ✅ Fetches historical data for multiple timeframes (1m, 5m 1h, 1d)
- ✅ Supports all Binance perpetual futures symbols
- ✅ Stores data in separate TimescaleDB tables by timeframe
- ✅ Intelligent caching to avoid re-downloading existing data
- ✅ Rate limiting to respect Binance API limits
- ✅ Flexible date range selection
- ✅ Command-line interface with comprehensive options
- ✅ Robust error handling and logging

## Database Schema

The tool creates separate tables for each timeframe:

- `futures_data_historical_1m` - 1-minute candlesticks
- `futures_data_historical_5m` - 5-minute candlesticks
- `futures_data_historical_1h` - 1-hour candlesticks
- `futures_data_historical_1d` - 1-day candlesticks

Each table contains: `exchange`, `symbol`, `timestamp`, `open`, `high`, `low`, `close`, `volume`

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables (create a `.env` file):
```env
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
DB_HOST=localhost
DB_NAME=my_timescale_db
DB_USER=postgres
DB_PASSWORD=mysecretpassword
```

3. Initialize the database with the provided schema:
```bash
psql -h localhost -U postgres -d my_timescale_db -f init.sql
```

## Usage

### Basic Examples

Fetch 1-minute data for specific symbols:
```bash
python app.py --symbols BTCUSDT ETHUSDT --intervals 1m
```

Fetch multiple timeframes for Bitcoin:
```bash
python app.py --symbols BTCUSDT --intervals 1m 5m 1h 1d
```

Fetch data for all perpetual futures symbols (WARNING: This will take a very long time!):
```bash
python app.py --all-symbols --intervals 1m 5m
```

### Date Range Examples

Fetch data from a specific start date:
```bash
python app.py --symbols BTCUSDT --intervals 1d --start-date 2020-01-01
```

Fetch data for a specific date range:
```bash
python app.py --symbols BTCUSDT ETHUSDT --intervals 1h --start-date 2023-01-01 --end-date 2023-12-31
```

### Advanced Options

Use dry-run mode to see what would be fetched:
```bash
python app.py --symbols BTCUSDT --intervals 1m 5m --dry-run
```

Specify custom cache directory:
```bash
python app.py --symbols BTCUSDT --intervals 1m --cache-dir /path/to/cache
```

Fetch COIN-M futures data instead of USD-M:
```bash
python app.py --symbols BTCUSD_PERP --intervals 1m --data-type cm
```

### Command-Line Options

```
usage: app.py [-h] (--symbols SYMBOLS [SYMBOLS ...] | --all-symbols)
              [--intervals INTERVALS [INTERVALS ...]] [--start-date START_DATE]
              [--end-date END_DATE] [--data-type {um,cm}] [--cache-dir CACHE_DIR]
              [--dry-run]

options:
  --symbols SYMBOLS [SYMBOLS ...]
                        List of trading symbols (e.g., BTCUSDT ETHUSDT)
  --all-symbols         Fetch data for all available perpetual futures symbols
  --intervals INTERVALS [INTERVALS ...]
                        List of timeframes to fetch (1m, 5m, 1h, 1d). Default: 1m
  --start-date START_DATE
                        Start date in YYYY-MM-DD format. Default: 2019-12-31
  --end-date END_DATE   End date in YYYY-MM-DD format. If not specified, fetches until today
  --data-type {um,cm}   Data type: um for USD-M Futures, cm for COIN-M Futures. Default: um
  --cache-dir CACHE_DIR
                        Directory to cache downloaded files. Default: data
  --dry-run             Show what would be fetched without actually downloading
```

## Performance Considerations

- **1-minute data**: Very large datasets, expect long download times
- **Daily data**: Much smaller, faster to download
- **All symbols**: 300+ symbols, use with caution for multiple timeframes
- **Caching**: Downloaded ZIP files are cached to avoid re-downloading
- **Rate limiting**: Built-in rate limiting respects Binance API limits

## Logging

The tool provides detailed logging including:
- Progress bars for each symbol and date
- Database insertion statistics
- Error handling and retry logic
- Rate limiting information

Set the log level via environment variable:
```env
LOG_LEVEL=DEBUG  # or INFO, WARNING, ERROR
```

## REST API

The historical data fetcher also provides a REST API for programmatic access. This allows you to start data fetches via HTTP requests instead of command line.

### Starting the API Server

```bash
python api.py
```

The API server will start on `http://localhost:5000` by default.

### API Endpoints

#### POST /api/fetch
Start a historical data fetch operation.

**Request Body:**
```json
{
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "intervals": ["1m", "5m"],
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "data_type": "um",
  "cache_dir": "data",
  "dry_run": false
}
```

**Alternative - Fetch all symbols:**
```json
{
  "all_symbols": true,
  "intervals": ["1d"],
  "start_date": "2023-01-01"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Historical data fetch started successfully with ID: fetch_1_1703123456",
  "data": {
    "request_summary": {
      "fetch_id": "fetch_1_1703123456",
      "symbols": ["BTCUSDT", "ETHUSDT"],
      "symbol_count": 2,
      "intervals": ["1m", "5m"],
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "data_type": "um",
      "cache_dir": "data",
      "dry_run": false
    }
  },
  "timestamp": "2023-12-21T10:30:56.123456"
}
```

#### GET /api/symbols
Get list of available trading symbols.

**Response:**
```json
{
  "success": true,
  "message": "Retrieved 300+ perpetual futures symbols",
  "data": {
    "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT", ...],
    "count": 300
  }
}
```

#### GET /api/intervals
Get list of supported timeframes.

**Response:**
```json
{
  "success": true,
  "message": "Retrieved 4 supported intervals",
  "data": {
    "intervals": ["1m", "5m", "1h", "1d"],
    "count": 4
  }
}
```

#### GET /api/fetch/{fetch_id}/status
Get status of a specific fetch operation.

**Response:**
```json
{
  "success": true,
  "message": "Fetch fetch_1_1703123456 status",
  "data": {
    "status": "running",
    "started_at": "2023-12-21T10:30:56.123456",
    "request": { ... }
  }
}
```

#### GET /api/fetch/active
Get list of all active fetch operations.

#### GET /api/health
Health check endpoint.

### API Parameters

All parameters from the command-line interface are supported:

- **symbols** (array): List of trading symbols (e.g., ["BTCUSDT", "ETHUSDT"])
- **all_symbols** (boolean): Fetch data for all available perpetual futures symbols
- **intervals** (array): List of timeframes (["1m", "5m", "1h", "1d"])
- **start_date** (string): Start date in YYYY-MM-DD format
- **end_date** (string): End date in YYYY-MM-DD format (optional)
- **data_type** (string): "um" for USD-M Futures, "cm" for COIN-M Futures
- **cache_dir** (string): Directory to cache downloaded files
- **dry_run** (boolean): Preview mode - shows what would be fetched without downloading

### Example API Usage

**Using curl:**
```bash
# Start a fetch for Bitcoin 1-minute data
curl -X POST http://localhost:5000/api/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["BTCUSDT"],
    "intervals": ["1m"],
    "start_date": "2023-12-01",
    "end_date": "2023-12-31"
  }'

# Check available symbols
curl http://localhost:5000/api/symbols

# Health check
curl http://localhost:5000/api/health
```

**Using Python requests:**
```python
import requests

# Start a fetch
response = requests.post('http://localhost:5000/api/fetch', json={
    'symbols': ['BTCUSDT', 'ETHUSDT'],
    'intervals': ['1h', '1d'],
    'start_date': '2023-01-01'
})

fetch_data = response.json()
fetch_id = fetch_data['data']['request_summary']['fetch_id']

# Check status
status_response = requests.get(f'http://localhost:5000/api/fetch/{fetch_id}/status')
print(status_response.json())
```

## Docker Deployment

### Using Docker Compose (Recommended)

The easiest way to run both the API and database is using Docker Compose:

```bash
# Set your Binance API credentials
export BINANCE_API_KEY=your_actual_api_key
export BINANCE_API_SECRET=your_actual_api_secret

# Start the API and database
docker-compose up -d

# Check logs
docker-compose logs -f historical-data-api

# Stop services
docker-compose down
```

This will start:
- TimescaleDB on port 5432
- Historical Data Fetcher API on port 5000

### Using Docker Compose for CLI

To run the command-line version with Docker:

```bash
# Run a one-time fetch
docker-compose run --rm historical-data-cli python app.py --symbols BTCUSDT --intervals 1h --dry-run

# Or start the CLI service
docker-compose --profile cli up historical-data-cli
```

### Manual Docker Build

```bash
# Build the image
docker build -t historical-data-fetcher .

# Run the API
docker run -d \
  --name historical-data-api \
  -p 5000:5000 \
  -e DB_HOST=your_db_host \
  -e DB_NAME=my_timescale_db \
  -e DB_USER=postgres \
  -e DB_PASSWORD=mysecretpassword \
  -e BINANCE_API_KEY=your_api_key \
  -e BINANCE_API_SECRET=your_api_secret \
  historical-data-fetcher python api.py

# Run CLI commands
docker run --rm \
  -e DB_HOST=your_db_host \
  -e BINANCE_API_KEY=your_api_key \
  -e BINANCE_API_SECRET=your_api_secret \
  historical-data-fetcher python app.py --symbols BTCUSDT --intervals 1m --dry-run
```

## Testing the API

Use the provided example script to test the API:

```bash
# Make sure the API is running first
python api.py

# In another terminal, run the example
python api_example.py
```

## Error Handling

The tool includes robust error handling for:
- Network connectivity issues
- Database connection problems
- Invalid symbols or date ranges
- Rate limit exceeded scenarios
- Corrupted or missing data files
