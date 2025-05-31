#!/usr/bin/env python3
"""
Historical Data Fetcher for Binance Futures - Utility Functions

This module contains utility functions for validating symbols, intervals, and dates
that are used by the API service. The service is now API-only and does not support
command-line arguments.

For API usage, see api.py
"""

import logging
import sys
from datetime import datetime
from binance_client import get_exchange_info, get_futures_symbols
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

if __name__ == '__main__':
    print("=" * 60)
    print("HISTORICAL DATA FETCHER - API ONLY SERVICE")
    print("=" * 60)
    print("This service is now API-only and does not support command-line arguments.")
    print("")
    print("To start the REST API server:")
    print("  python api.py")
    print("")
    print("The API will be available at: http://localhost:5000")
    print("")
    print("Available endpoints:")
    print("  POST /api/fetch        - Start a historical data fetch")
    print("  GET  /api/symbols      - Get available trading symbols")
    print("  GET  /api/intervals    - Get supported timeframes")
    print("  GET  /api/health       - Health check")
    print("  GET  /api/fetch/active - Get active fetch operations")
    print("")
    print("For detailed API documentation, see README.md")
    print("=" * 60)
    sys.exit(1)
