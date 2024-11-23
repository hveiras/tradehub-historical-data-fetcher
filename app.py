import logging
from flask import Flask, jsonify
from threading import Event
from binance_client import get_futures_symbols, fetch_historical_candlesticks
from database import insert_futures_data_1m
from websocket_handler import start_websocket_stream

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from flask import Flask, jsonify
from threading import Event
from websocket_handler import start_websocket_stream

app = Flask(__name__)

# Event to control WebSocket
stop_event = Event()
websocket_app = None

# Fetch and insert historical data at startup
def fetch_and_insert_historical_data():
    symbols = get_futures_symbols()
    for symbol in symbols:
        logging.info(f"Fetching historical data for {symbol}...")
        historical_data = fetch_historical_candlesticks(symbol, start_str="1 year ago UTC")  # Adjust start date as needed
        if historical_data:
            insert_futures_data_1m(historical_data)

@app.route('/start', methods=['POST'])
def start_collection():
    global websocket_app
    if websocket_app:
        return jsonify({'status': 'Collector is already running.'}), 400

    logging.info("Fetching and inserting historical data...")
    fetch_and_insert_historical_data()

    websocket_app = start_websocket_stream()
    logging.info("WebSocket collector started.")
    return jsonify({'status': 'Collector started.'}), 200

@app.route('/stop', methods=['POST'])
def stop_collection():
    global websocket_app
    if not websocket_app:
        return jsonify({'status': 'Collector is not running.'}), 400

    websocket_app.close()
    websocket_app = None
    logging.info("WebSocket collector stopped.")
    return jsonify({'status': 'Collector stopped.'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
