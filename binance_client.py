import requests
from zipfile import ZipFile
import pandas as pd
from tqdm import tqdm
from datetime import datetime, timedelta, timezone
import logging
import time
from io import BytesIO

from config import API_KEY, API_SECRET  # Assuming these are still needed for some API interactions
from database import insert_futures_data, check_data_exists
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

def generate_date_range(start_date_str='2019-12-31', end_date_str=None):
    """
    Generate a list of dates from a start date to an end date (inclusive).
    Each date is a string in the format YYYY-MM-DD.

    :param start_date_str: Start date as a string in 'YYYY-MM-DD' format.
    :param end_date_str: End date as a string in 'YYYY-MM-DD' format. If None, uses today.
    :return: List of date strings.
    """
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except ValueError as e:
        logger.error(f"Invalid start_date format: {e}")
        return []

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError as e:
            logger.error(f"Invalid end_date format: {e}")
            return []
    else:
        end_date = datetime.utcnow().date()

    if start_date > end_date:
        logger.error(f"Start date {start_date_str} is after end date {end_date}")
        return []

    delta = end_date - start_date
    dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta.days + 1)]
    logger.debug(f"Generated date range from {start_date_str} to {end_date}. Total days: {len(dates)}")
    return dates

def download_and_extract_zip_streaming(symbol, interval, date, data_type='um'):
    """
    Download and extract the ZIP file for a given symbol, interval, and date using in-memory streaming.
    Checks database first to avoid re-downloading existing data.

    :param symbol: Trading symbol, e.g., 'ADABUSD'
    :param interval: Kline interval, e.g., '1m'
    :param date: Date string in 'YYYY-MM-DD' format
    :param data_type: 'um' for USD-M Futures, 'cm' for COIN-M Futures
    :return: DataFrame containing the klines data or None if download/extraction fails
    """
    # Check if data already exists in database
    try:
        if check_data_exists(symbol, date, interval):
            logger.debug(f"Data already exists in database for {symbol} on {date} ({interval}). Skipping download.")
            return None
    except Exception as e:
        logger.warning(f"Could not check if data exists for {symbol} on {date} ({interval}): {e}. Proceeding with download.")

    # Construct download URL
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

    # Process ZIP file in memory
    try:
        # Create a BytesIO object from the response content
        zip_buffer = BytesIO(response.content)

        # Extract and read CSV directly from memory
        with ZipFile(zip_buffer, 'r') as thezip:
            with thezip.open(thezip.namelist()[0]) as thefile:
                df = pd.read_csv(thefile, header=None)
                logger.debug(f"Downloaded and extracted CSV for {symbol} on {date} ({interval}) - {len(df)} rows")
                return df
    except Exception as e:
        logger.error(f"Error extracting or parsing ZIP file for {symbol} on {date}: {e}")
        return None

def process_and_insert_data(symbol, df, timeframe='1m'):
    """
    Process the DataFrame and insert data into the database.

    :param symbol: Trading symbol, e.g., 'ADABUSD'
    :param df: DataFrame containing the klines data
    :param timeframe: Timeframe string (1m, 5m, 1h, 1d)
    """
    if df.empty:
        logger.debug(f"No data in DataFrame for {symbol}.")
        return

    # Define column names based on Binance's Klines data structure
    column_names = [
    'open_time', 'open', 'high', 'low', 'close', 'volume',
    'close_time', 'quote_volume', 'count',
    'taker_buy_volume', 'taker_buy_quote_volume', 'ignore'
    ]
    df.columns = column_names

    batch_data = []
    last_open_time = None

    for _, row in df.iterrows():
        open_time = None
        try:
            open_time_ms = pd.to_numeric(row['open_time'], errors='coerce')
            open_time = datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc)
            last_open_time = open_time  # Keep track of the last successfully processed timestamp
            data_point = (
                'binance',
                symbol,
                open_time,
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                float(row['volume']),
            )
            batch_data.append(data_point)
        except Exception as e:
            logger.error(f"Error processing row for {symbol}: {e}")
            continue

    if not batch_data:
        logger.debug(f"No valid data points to insert for {symbol}.")
        return

    # Insert and log, but guard against missing last_open_time
    try:
        insert_futures_data(batch_data, timeframe)
        if last_open_time:
            logger.info(
                f"Inserted {len(batch_data)} candlesticks for {symbol} "
                f"({timeframe}) on {last_open_time.date()}."
            )
        else:
            logger.info(f"Inserted {len(batch_data)} candlesticks for {symbol} ({timeframe}).")
    except Exception as e:
        when = last_open_time.date() if last_open_time else "unknown date"
        logger.error(
            f"Error inserting data for {symbol} ({timeframe}) on {when}: {e}"
        )

def fetch_historical_candlesticks(symbol, rate_limiter, dates, interval='1m', data_type='um'):
    """
    Fetch historical candlesticks for a symbol by downloading and processing ZIP files from Binance's public data.
    Uses in-memory streaming to avoid local storage issues in Kubernetes.

    :param symbol: Trading symbol, e.g., 'ADABUSD'
    :param rate_limiter: Rate limiter instance (if needed)
    :param dates: List of date strings in 'YYYY-MM-DD' format
    :param interval: Kline interval, e.g., '1m'
    :param data_type: 'um' for USD-M Futures, 'cm' for COIN-M Futures
    """
    for date in tqdm(dates, desc=f"Fetching {symbol} ({interval})", unit="day"):
        try:
            if rate_limiter:
                rate_limiter.acquire("REQUEST_WEIGHT")

            df = download_and_extract_zip_streaming(symbol, interval, date, data_type=data_type)
            if df is not None:
                process_and_insert_data(symbol, df, timeframe=interval)
            else:
                logger.debug(f"No data for {symbol} on {date}. Skipping.")
        except Exception as e:
            logger.error(f"Unexpected failure for {symbol} on {date} ({interval}): {e}")
        finally:
            time.sleep(0.1)

def fetch_and_insert_all_historical_data(rate_limiter, symbols=None, intervals=None, start_date='2019-12-31', end_date=None, data_type='um'):
    """
    Fetch and insert historical candlestick data for specified symbols and intervals.
    Uses in-memory streaming to avoid local storage issues in Kubernetes.

    :param rate_limiter: Rate limiter instance (if needed)
    :param symbols: List of symbols to fetch. If None, fetches all perpetual futures symbols
    :param intervals: List of intervals to fetch (e.g., ['1m', '5m', '1h']). If None, fetches only '1m'
    :param start_date: Start date as string in 'YYYY-MM-DD' format
    :param end_date: End date as string in 'YYYY-MM-DD' format. If None, fetches until today
    :param data_type: 'um' for USD-M Futures, 'cm' for COIN-M Futures
    """
    if symbols is None:
        symbols = get_futures_symbols()

    if intervals is None:
        intervals = ['1m']

    dates = generate_date_range(start_date, end_date)
    end_date_display = end_date or 'today'
    logger.info(f"Starting historical data fetch for {len(symbols)} symbols, {len(intervals)} intervals from {start_date} to {end_date_display}.")

    for idx, symbol in enumerate(symbols, 1):
        logger.info(f"Fetching historical data for {symbol} ({idx}/{len(symbols)})...")
        for interval in intervals:
            try:
                logger.info(f"  Fetching {interval} data for {symbol}...")
                fetch_historical_candlesticks(symbol, rate_limiter, dates, interval=interval, data_type=data_type)
            except Exception as e:
                logger.error(f"Failed to fetch {interval} historical data for {symbol}: {e}")
        # Optional: Sleep between symbols to distribute rate limit usage
        time.sleep(0.1)

    logger.info("Completed historical data fetch for all symbols and intervals.")
