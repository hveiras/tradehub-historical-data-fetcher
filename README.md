# Historical Data Fetcher for Binance Futures

A command-line tool for fetching historical candlestick data from Binance futures markets and storing them in TimescaleDB tables organized by timeframe.

## Features

- ✅ Fetches historical data for multiple timeframes (1m, 5m, 15m, 1h, 4h, 1d)
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
- `futures_data_historical_15m` - 15-minute candlesticks
- `futures_data_historical_1h` - 1-hour candlesticks
- `futures_data_historical_4h` - 4-hour candlesticks
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
                        List of timeframes to fetch (1m, 5m, 15m, 1h, 4h, 1d). Default: 1m
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

## Error Handling

The tool includes robust error handling for:
- Network connectivity issues
- Database connection problems
- Invalid symbols or date ranges
- Rate limit exceeded scenarios
- Corrupted or missing data files

## Changes from Previous Version

This version has been completely refactored to:
- ❌ Remove all WebSocket functionality
- ✅ Add support for multiple timeframes (1m, 5m, 15m, 1h, 4h, 1d)
- ✅ Replace Flask web interface with command-line interface
- ✅ Add comprehensive argument validation
- ✅ Improve database schema to match timeframe-specific tables
- ✅ Add date range selection capabilities
- ✅ Enhance error handling and logging