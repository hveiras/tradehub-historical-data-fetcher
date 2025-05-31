#!/usr/bin/env python3
"""
Historical Data Fetcher for Binance Futures

This script fetches historical candlestick data from Binance for futures trading pairs
and stores them in TimescaleDB tables organized by timeframe.

Usage:
    python app.py --symbols BTCUSDT ETHUSDT --intervals 1m 5m 1h --start-date 2023-01-01
    python app.py --all-symbols --intervals 1m 5m 1h 1d
    python app.py --symbols BTCUSDT --intervals 1d --start-date 2020-01-01 --end-date 2023-12-31
"""

import argparse
import logging
import sys
from datetime import datetime
from binance_client import fetch_and_insert_all_historical_data, get_exchange_info, get_futures_symbols
from rate_limiter import BinanceRateLimiter
from config import LOG_LEVEL, LOG_FORMAT

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def initialize_rate_limiter():
    """
    Initialize the Binance rate limiter based on exchange info.
    """
    try:
        exchange_info = get_exchange_info()
        rate_limits = exchange_info['rateLimits']
        rate_limiter = BinanceRateLimiter(rate_limits)
        logger.debug("Initialized Binance rate limiter.")
        return rate_limiter
    except Exception as e:
        logger.error(f"Failed to initialize rate limiter: {e}")
        logger.warning("Continuing without rate limiter...")
        return None

def validate_symbols(symbols):
    """
    Validate that the provided symbols exist in Binance futures.

    :param symbols: List of symbol strings
    :return: List of valid symbols
    """
    try:
        all_symbols = get_futures_symbols()
        valid_symbols = []
        invalid_symbols = []

        for symbol in symbols:
            symbol_upper = symbol.upper()
            if symbol_upper in all_symbols:
                valid_symbols.append(symbol_upper)
            else:
                invalid_symbols.append(symbol)

        if invalid_symbols:
            logger.warning(f"Invalid symbols (will be skipped): {invalid_symbols}")

        if not valid_symbols:
            logger.error("No valid symbols provided!")
            return []

        logger.info(f"Valid symbols to process: {valid_symbols}")
        return valid_symbols

    except Exception as e:
        logger.error(f"Failed to validate symbols: {e}")
        return symbols  # Return original list if validation fails

def validate_intervals(intervals):
    """
    Validate that the provided intervals are supported.

    :param intervals: List of interval strings
    :return: List of valid intervals
    """
    supported_intervals = ['1m', '5m', '1h', '1d']
    valid_intervals = []
    invalid_intervals = []

    for interval in intervals:
        if interval in supported_intervals:
            valid_intervals.append(interval)
        else:
            invalid_intervals.append(interval)

    if invalid_intervals:
        logger.warning(f"Invalid intervals (will be skipped): {invalid_intervals}")
        logger.info(f"Supported intervals: {supported_intervals}")

    if not valid_intervals:
        logger.error("No valid intervals provided!")
        return []

    logger.info(f"Valid intervals to process: {valid_intervals}")
    return valid_intervals

def validate_date(date_string):
    """
    Validate date string format.

    :param date_string: Date string in YYYY-MM-DD format
    :return: True if valid, False otherwise
    """
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Fetch historical data from Binance futures and store in TimescaleDB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch 1m and 5m data for specific symbols
  python app.py --symbols BTCUSDT ETHUSDT --intervals 1m 5m

  # Fetch all timeframes for all symbols (WARNING: This will take a very long time!)
  python app.py --all-symbols --intervals 1m 5m 1h 1d

  # Fetch daily data for Bitcoin from 2020 onwards
  python app.py --symbols BTCUSDT --intervals 1d --start-date 2020-01-01

  # Fetch data for a specific date range
  python app.py --symbols BTCUSDT ETHUSDT --intervals 1h --start-date 2023-01-01 --end-date 2023-12-31
        """
    )

    # Symbol selection (mutually exclusive)
    symbol_group = parser.add_mutually_exclusive_group(required=True)
    symbol_group.add_argument(
        '--symbols',
        nargs='+',
        help='List of trading symbols (e.g., BTCUSDT ETHUSDT)'
    )
    symbol_group.add_argument(
        '--all-symbols',
        action='store_true',
        help='Fetch data for all available perpetual futures symbols'
    )

    # Timeframe selection
    parser.add_argument(
        '--intervals',
        nargs='+',
        default=['1m'],
        help='List of timeframes to fetch (1m, 5m, 1h, 1d). Default: 1m'
    )

    # Date range
    parser.add_argument(
        '--start-date',
        default='2019-12-31',
        help='Start date in YYYY-MM-DD format. Default: 2019-12-31'
    )
    parser.add_argument(
        '--end-date',
        help='End date in YYYY-MM-DD format. If not specified, fetches until today'
    )

    # Other options
    parser.add_argument(
        '--data-type',
        choices=['um', 'cm'],
        default='um',
        help='Data type: um for USD-M Futures, cm for COIN-M Futures. Default: um'
    )
    parser.add_argument(
        '--cache-dir',
        default='data',
        help='Directory to cache downloaded files. Default: data'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be fetched without actually downloading'
    )

    args = parser.parse_args()

    # Validate arguments
    if not validate_date(args.start_date):
        logger.error(f"Invalid start date format: {args.start_date}. Use YYYY-MM-DD format.")
        sys.exit(1)

    if args.end_date and not validate_date(args.end_date):
        logger.error(f"Invalid end date format: {args.end_date}. Use YYYY-MM-DD format.")
        sys.exit(1)

    # Validate intervals
    valid_intervals = validate_intervals(args.intervals)
    if not valid_intervals:
        sys.exit(1)

    # Determine symbols to fetch
    if args.all_symbols:
        logger.info("Fetching data for all available perpetual futures symbols...")
        symbols = None  # Will be determined by the fetch function
    else:
        symbols = validate_symbols(args.symbols)
        if not symbols:
            sys.exit(1)

    # Initialize rate limiter
    rate_limiter = initialize_rate_limiter()

    # Show summary
    logger.info("=" * 60)
    logger.info("HISTORICAL DATA FETCH CONFIGURATION")
    logger.info("=" * 60)
    if symbols:
        logger.info(f"Symbols: {symbols}")
    else:
        logger.info("Symbols: ALL PERPETUAL FUTURES SYMBOLS")
    logger.info(f"Intervals: {valid_intervals}")
    logger.info(f"Start date: {args.start_date}")
    logger.info(f"End date: {args.end_date or 'today'}")
    logger.info(f"Data type: {args.data_type}")
    logger.info(f"Cache directory: {args.cache_dir}")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("DRY RUN MODE - No data will be downloaded")
        return

    # Confirm before proceeding with large operations
    if args.all_symbols and len(valid_intervals) > 2:
        response = input("WARNING: This will fetch a LOT of data and may take days to complete. Continue? (y/N): ")
        if response.lower() != 'y':
            logger.info("Operation cancelled by user.")
            return

    try:
        # Start the historical data fetch
        logger.info("Starting historical data fetch...")
        fetch_and_insert_all_historical_data(
            rate_limiter=rate_limiter,
            symbols=symbols,
            intervals=valid_intervals,
            start_date=args.start_date,
            end_date=args.end_date,
            data_type=args.data_type,
            cache_dir=args.cache_dir
        )
        logger.info("Historical data fetch completed successfully!")

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to fetch historical data: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
