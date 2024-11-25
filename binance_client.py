import os
import requests
from zipfile import ZipFile
from io import BytesIO
import pandas as pd
from tqdm import tqdm
from datetime import datetime, timedelta, timezone
import logging
import time

from config import API_KEY, API_SECRET  # Assuming these are still needed for some API interactions
from database import insert_futures_data_1m
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Initialize Binance Client
client = Client(api_key=API_KEY, api_secret=API_SECRET)

# Configure Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # You can set this based on your LOG_LEVEL in config
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Constants
INTERVAL_DURATION_MS = 60 * 1000  # 1 minute in milliseconds
BASE_URL = "https://data.binance.vision/data/futures"

def get_exchange_info():
    """
    Retrieve exchange information, including rate limits.
    """
    try:
        exchange_info = client.futures_exchange_info()
        logger.debug("Fetched exchange information from Binance.")
        return exchange_info
    except BinanceAPIException as e:
        logger.error(f"Error fetching exchange info: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching exchange info: {e}")
        raise

def get_futures_symbols():
    """
    Retrieve all perpetual futures symbols from Binance.
    """
    try:
        exchange_info = get_exchange_info()
        symbols = [s['symbol'] for s in exchange_info['symbols'] if s['contractType'] == 'PERPETUAL']
        logger.info(f"Retrieved {len(symbols)} perpetual futures symbols.")
        return symbols
    except Exception as e:
        logger.error(f"Error fetching futures symbols: {e}")
        return []

def generate_date_range(start_date_str='2019-12-31'):
    """
    Generate a list of dates from a start date to today (inclusive).
    Each date is a string in the format YYYY-MM-DD.
    
    :param start_date_str: Start date as a string in 'YYYY-MM-DD' format.
    :return: List of date strings.
    """
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except ValueError as e:
        logger.error(f"Invalid start_date format: {e}")
        return []
    
    end_date = datetime.utcnow().date()
    delta = end_date - start_date
    dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta.days + 1)]
    logger.debug(f"Generated date range from {start_date_str} to {end_date}. Total days: {len(dates)}")
    return dates

def download_and_extract_zip(symbol, interval, date, data_type='um', cache_dir='data'):
    """
    Download and extract the ZIP file for a given symbol, interval, and date.
    Implements caching to avoid re-downloading existing files.
    
    :param symbol: Trading symbol, e.g., 'ADABUSD'
    :param interval: Kline interval, e.g., '1m'
    :param date: Date string in 'YYYY-MM-DD' format
    :param data_type: 'um' for USD-M Futures, 'cm' for COIN-M Futures
    :param cache_dir: Directory to cache downloaded ZIP files
    :return: DataFrame containing the klines data or None if download/extraction fails
    """
    os.makedirs(cache_dir, exist_ok=True)
    zip_filename = f"{symbol}-{interval}-{date}.zip"
    zip_path = os.path.join(cache_dir, zip_filename)
    csv_filename = f"{symbol}-{interval}-{date}.csv"  # Assuming the CSV inside ZIP follows this naming

    if os.path.exists(zip_path):
        logger.debug(f"Using cached ZIP file for {symbol} on {date}.")
        try:
            with ZipFile(zip_path, 'r') as thezip:
                with thezip.open(thezip.namelist()[0]) as thefile:
                    df = pd.read_csv(thefile, header=None)
                    return df
        except Exception as e:
            logger.error(f"Error extracting cached ZIP file {zip_path}: {e}")
            return None

    # Proceed to download if not cached
    url = f"{BASE_URL}/{data_type}/daily/klines/{symbol}/{interval}/{symbol}-{interval}-{date}.zip"
    logger.debug(f"Downloading ZIP file from {url}")

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
    except requests.HTTPError as http_err:
        if response.status_code == 404:
            logger.warning(f"Data file not found for {symbol} on {date}. Skipping.")
        else:
            logger.error(f"HTTP error occurred while downloading {url}: {http_err}")
        return None
    except Exception as err:
        logger.error(f"Error occurred while downloading {url}: {err}")
        return None

    # Save ZIP file to cache
    try:
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        logger.debug(f"Saved ZIP file to {zip_path}")
    except Exception as e:
        logger.error(f"Error saving ZIP file {zip_path}: {e}")
        return None

    # Extract and read CSV
    try:
        with ZipFile(zip_path, 'r') as thezip:
            with thezip.open(thezip.namelist()[0]) as thefile:
                df = pd.read_csv(thefile, header=None)
                logger.debug(f"Extracted and read CSV from {zip_path}")
                return df
    except Exception as e:
        logger.error(f"Error extracting or parsing ZIP file {zip_path}: {e}")
        return None

def process_and_insert_data(symbol, df):
    """
    Process the DataFrame and insert data into the database.
    
    :param symbol: Trading symbol, e.g., 'ADABUSD'
    :param df: DataFrame containing the klines data
    """
    if df.empty:
        logger.debug(f"No data in DataFrame for {symbol}.")
        return

    # Define column names based on Binance's Klines data structure
    column_names = [
        'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume',
        'Close Time', 'Quote Asset Volume', 'Number of Trades',
        'Taker Buy Base Asset Volume', 'Taker Buy Quote Asset Volume', 'Ignore'
    ]
    df.columns = column_names

    batch_data = []
    for _, row in df.iterrows():
        try:
            open_time = datetime.fromtimestamp(row['Open Time'] / 1000, tz=timezone.utc)
            data_point = (
                'binance',
                symbol,
                open_time,
                float(row['Open']),
                float(row['High']),
                float(row['Low']),
                float(row['Close']),
                float(row['Volume']),
            )
            batch_data.append(data_point)
        except Exception as e:
            logger.error(f"Error processing row for {symbol} on {open_time}: {e}")
            continue

    if batch_data:
        try:
            insert_futures_data_1m(batch_data)
            logger.info(f"Inserted {len(batch_data)} candlesticks for {symbol} on {open_time.date()}.")
        except Exception as e:
            logger.error(f"Error inserting data into database for {symbol} on {open_time.date()}: {e}")
    else:
        logger.debug(f"No valid data points to insert for {symbol}.")

def fetch_historical_candlesticks(symbol, rate_limiter, dates, interval='1m', data_type='um', cache_dir='data'):
    """
    Fetch historical candlesticks for a symbol by downloading and processing ZIP files from Binance's public data.
    
    :param symbol: Trading symbol, e.g., 'ADABUSD'
    :param rate_limiter: Rate limiter instance (if needed)
    :param dates: List of date strings in 'YYYY-MM-DD' format
    :param interval: Kline interval, e.g., '1m'
    :param data_type: 'um' for USD-M Futures, 'cm' for COIN-M Futures
    :param cache_dir: Directory to cache downloaded ZIP files
    """
    for date in tqdm(dates, desc=f"Fetching {symbol}", unit="day"):
        if rate_limiter:
            rate_limiter.acquire()

        df = download_and_extract_zip(symbol, interval, date, data_type=data_type, cache_dir=cache_dir)
        if df is not None:
            process_and_insert_data(symbol, df)
        else:
            logger.debug(f"No data for {symbol} on {date}. Skipping.")

        # Optional: Respect rate limits by adding a small sleep
        time.sleep(0.1)

def fetch_and_insert_all_historical_data(rate_limiter, data_type='um', cache_dir='data'):
    """
    Fetch and insert historical candlestick data for all symbols.
    
    :param rate_limiter: Rate limiter instance (if needed)
    :param data_type: 'um' for USD-M Futures, 'cm' for COIN-M Futures
    :param cache_dir: Directory to cache downloaded ZIP files
    """
    symbols = get_futures_symbols()
    dates = generate_date_range()
    logger.info(f"Starting historical data fetch for {len(symbols)} symbols from 2019-12-31 to today.")

    for idx, symbol in enumerate(symbols, 1):
        logger.info(f"Fetching historical data for {symbol} ({idx}/{len(symbols)})...")
        try:
            fetch_historical_candlesticks(symbol, rate_limiter, dates, interval='1m', data_type=data_type, cache_dir=cache_dir)
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {e}")
        # Optional: Sleep between symbols to distribute rate limit usage
        time.sleep(0.1)

    logger.info("Completed historical data fetch for all symbols.")
