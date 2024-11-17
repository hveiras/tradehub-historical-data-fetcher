from binance.client import Client as BinanceAPI
import time
import psycopg2
from datetime import datetime, timedelta

# Binance API credentials
API_KEY = 'your_api_key'
API_SECRET = 'your_api_secret'

# Initialize Binance client
binance_client = BinanceAPI(API_KEY, API_SECRET)

# Database connection (replace these with your credentials)
DB_HOST = 'timescaledb'
DB_NAME = 'my_timescale_db'
DB_USER = 'postgres'
DB_PASSWORD = 'mysecretpassword'

# Connect to TimescaleDB
conn = psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cursor = conn.cursor()

# Function to insert data into TimescaleDB
def insert_candlestick_data(data):
    insert_query = """
    INSERT INTO candlestick_data (exchange, symbol, timestamp, open, high, low, close, volume)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (exchange, symbol, timestamp) DO NOTHING;
    """
    cursor.executemany(insert_query, data)
    conn.commit()

# Fetch all futures symbols
def get_futures_symbols():
    futures_info = binance_client.futures_exchange_info()
    return [s['symbol'] for s in futures_info['symbols']]

# Fetch 1-minute candles
def fetch_1m_candles(symbol, start_time, end_time):
    candles = binance_client.futures_klines(
        symbol=symbol,
        interval=BinanceAPI.KLINE_INTERVAL_1MINUTE,
        startTime=int(start_time.timestamp() * 1000),
        endTime=int(end_time.timestamp() * 1000)
    )
    # Parse and structure data for insertion
    return [
        (
            'binance',                 # Exchange name
            symbol,                    # Symbol
            datetime.fromtimestamp(c[0] / 1000),
            float(c[1]),               # Open
            float(c[2]),               # High
            float(c[3]),               # Low
            float(c[4]),               # Close
            float(c[5])                # Volume
        )
        for c in candles
    ]

# Main function to iterate over symbols and collect data
def collect_candlesticks():
    symbols = get_futures_symbols()
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=1)  # Fetch the last 1 minute only

    for symbol in symbols:
        try:
            print(f"Collecting data for {symbol}")
            # Fetch data
            data = fetch_1m_candles(symbol, start_time, end_time)
            if data:
                insert_candlestick_data(data)
                print(f"Inserted data for {symbol}")
            time.sleep(0.2)  # Avoid hitting API rate limits
        except Exception as e:
            print(f"Error collecting data for {symbol}: {e}")

# Run the service
if __name__ == "__main__":
    while True:
        collect_candlesticks()
        print("Waiting for the next minute...")
        time.sleep(60)  # Run the service every minute
