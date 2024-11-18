from flask import Flask, jsonify
from threading import Event
import time
import logging
import psycopg2
from datetime import datetime, timedelta
from binance.client import Client as BinanceAPI
from apscheduler.schedulers.background import BackgroundScheduler

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Binance API credentials
API_KEY = 'your_api_key'
API_SECRET = 'your_api_secret'

# Initialize Binance client
binance_client = BinanceAPI(API_KEY, API_SECRET)

# Database connection (replace these with your credentials)
DB_HOST = 'localhost'
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

# Flask app initialization
app = Flask(__name__)

# Event to control the scheduler
stop_event = Event()

# APScheduler for background scheduling
scheduler = BackgroundScheduler()

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
    symbols = [s['symbol'] for s in futures_info['symbols']]
    logging.debug(f"Retrieved {len(symbols)} futures symbols.")
    return symbols

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

# Background data collection function
def collect_candlesticks():
    logging.debug("Starting candlestick collection...")
    symbols = get_futures_symbols()
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=1)  # Fetch the last 1 minute only

    for symbol in symbols:
        if stop_event.is_set():
            logging.debug("Stopping candlestick collection due to stop event.")
            break
        try:
            logging.debug(f"Collecting data for {symbol}")
            # Fetch data
            data = fetch_1m_candles(symbol, start_time, end_time)
            if data:
                insert_candlestick_data(data)
                logging.debug(f"Inserted data for {symbol}")
            time.sleep(0.1)  # Avoid hitting API rate limits, reduce sleep for more speed
        except Exception as e:
            logging.error(f"Error collecting data for {symbol}: {e}")

# Flask routes to start and stop the collection
@app.route('/start', methods=['POST'])
def start_collection():
    if scheduler.get_job('candlestick_job'):
        return jsonify({'status': 'Collector is already running.'}), 400

    stop_event.clear()
    scheduler.add_job(collect_candlesticks, 'interval', minutes=1, id='candlestick_job')
    scheduler.start()
    logging.debug("Collector job started.")
    return jsonify({'status': 'Collector started.'}), 200

@app.route('/stop', methods=['POST'])
def stop_collection():
    if not scheduler.get_job('candlestick_job'):
        return jsonify({'status': 'Collector is not running.'}), 400

    stop_event.set()
    scheduler.remove_job('candlestick_job')
    logging.debug("Collector job stopped.")
    return jsonify({'status': 'Collector stopped.'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
