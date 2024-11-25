from flask import Flask, jsonify
from threading import Event, Thread
import logging
from binance_client import fetch_and_insert_all_historical_data, get_exchange_info
from websocket_handler import start_websocket_stream
from rate_limiter import BinanceRateLimiter
from config import LOG_LEVEL, LOG_FORMAT
import sys

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global variables for thread management
stop_event = Event()
websocket_thread = None
historical_thread = None
websocket_app = None  # Assuming this is an object returned by start_websocket_stream()

def initialize_rate_limiter():
    """
    Initialize the Binance rate limiter based on exchange info.
    """
    exchange_info = get_exchange_info()
    rate_limits = exchange_info['rateLimits']
    rate_limiter = BinanceRateLimiter(rate_limits)
    logger.debug("Initialized Binance rate limiter.")
    return rate_limiter

# Initialize rate limiter
rate_limiter = initialize_rate_limiter()

def run_historical_fetch():
    """
    Background thread function to fetch historical data.
    """
    try:
        logger.info("Starting historical data fetch...")
        fetch_and_insert_all_historical_data(rate_limiter, data_type='um')
        logger.info("Historical data fetch completed.")
    except Exception as e:
        logger.error(f"Failed to fetch historical data: {e}")

def run_websocket():
    """
    Background thread function to start WebSocket stream.
    """
    global websocket_app
    try:
        websocket_app = start_websocket_stream(stop_event)
        logger.info("WebSocket collector started.")
        websocket_app.run_forever()
    except Exception as e:
        logger.error(f"Failed to run WebSocket collector: {e}")

@app.route('/fetch_historical', methods=['POST'])
def fetch_historical():
    """
    Endpoint to start fetching historical data.
    """
    global historical_thread

    if historical_thread and historical_thread.is_alive():
        logger.warning("Historical data fetch is already running.")
        return jsonify({'status': 'Historical data fetch is already running.'}), 400

    # Start the historical data fetch in a new thread
    historical_thread = Thread(target=run_historical_fetch, daemon=True)
    historical_thread.start()
    logger.info("Historical data fetch thread started.")
    return jsonify({'status': 'Historical data fetch started.'}), 200

@app.route('/start', methods=['POST'])
def start_websocket_endpoint():
    """
    Endpoint to start the WebSocket collector.
    """
    global websocket_thread, websocket_app

    if websocket_thread and websocket_thread.is_alive():
        logger.warning("WebSocket collector is already running.")
        return jsonify({'status': 'WebSocket collector is already running.'}), 400

    # Clear the stop event before starting
    stop_event.clear()

    # Start the WebSocket collector in a new thread
    websocket_thread = Thread(target=run_websocket, daemon=True)
    websocket_thread.start()
    logger.info("WebSocket collector thread started.")
    return jsonify({'status': 'WebSocket collector started.'}), 200

@app.route('/stop', methods=['POST'])
def stop_websocket():
    """
    Endpoint to stop the WebSocket collector.
    """
    global websocket_app

    if not websocket_thread or not websocket_thread.is_alive():
        logger.warning("WebSocket collector is not running.")
        return jsonify({'status': 'WebSocket collector is not running.'}), 400

    try:
        # Signal the WebSocket thread to stop
        stop_event.set()

        # If websocket_app has a close method, call it
        if websocket_app and hasattr(websocket_app, 'close'):
            websocket_app.close()

        # Wait for the thread to finish
        websocket_thread.join(timeout=10)
        if websocket_thread.is_alive():
            logger.warning("WebSocket collector thread did not terminate gracefully.")
            return jsonify({'status': 'Failed to stop WebSocket collector gracefully.'}), 500

        websocket_app = None
        websocket_thread = None
        logger.info("WebSocket collector stopped.")
        return jsonify({'status': 'WebSocket collector stopped.'}), 200
    except Exception as e:
        logger.error(f"Failed to stop WebSocket collector: {e}")
        return jsonify({'status': 'Failed to stop WebSocket collector.'}), 500

@app.route('/')
def index():
    """
    Health check endpoint.
    """
    status = {
        'message': 'Binance Collector is running.',
        'historical_fetch_running': historical_thread.is_alive() if historical_thread else False,
        'websocket_running': websocket_thread.is_alive() if websocket_thread else False
    }
    return jsonify(status), 200

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)
