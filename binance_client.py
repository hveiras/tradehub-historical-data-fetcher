from binance.client import Client
from config import API_KEY, API_SECRET
import logging
from datetime import datetime

client = Client(api_key=API_KEY, api_secret=API_SECRET)

def get_futures_symbols():
    try:
        futures_info = client.futures_exchange_info()
        symbols = [s['symbol'] for s in futures_info['symbols']]
        logging.debug(f"Retrieved {len(symbols)} futures symbols.")
        return symbols
    except Exception as e:
        logging.error(f"Error fetching futures symbols: {e}")
        return []

def fetch_historical_candlesticks(symbol, start_str="1 year ago UTC"):
    """
    Fetch historical 1m candlesticks from Binance Futures API.
    :param symbol: str - The futures symbol, e.g., 'BTCUSDT'
    :param start_str: str - The start date for the candlesticks (default: "1 year ago UTC")
    :return: list - List of candlesticks, each represented as a tuple
    """
    try:
        klines = client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, start_str=start_str)

        historical_data = []
        for kline in klines:
            historical_data.append((
                'binance',
                symbol,
                datetime.fromtimestamp(int(kline[0]) / 1000),  # Timestamp as datetime object
                float(kline[1]),  # Open
                float(kline[2]),  # High
                float(kline[3]),  # Low
                float(kline[4]),  # Close
                float(kline[5])   # Volume
            ))
        logging.debug(f"Fetched {len(historical_data)} historical candlesticks for {symbol}.")
        return historical_data
    except Exception as e:
        logging.error(f"Error fetching historical candlesticks for {symbol}: {e}")
        return []