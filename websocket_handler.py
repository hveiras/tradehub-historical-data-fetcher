import json
import logging
from datetime import datetime
from threading import Thread
import websocket
from binance_client import get_futures_symbols
from database import insert_futures_data_1m

def on_message(ws, message):
    try:
        msg = json.loads(message)
        if 'data' in msg and msg['data']['e'] == 'kline':
            kline = msg['data']['k']
            symbol = msg['data']['s']
            if kline['x']:
                data_point = (
                    'binance',
                    symbol,
                    datetime.fromtimestamp(kline['t'] / 1000),
                    float(kline['o']),
                    float(kline['h']),
                    float(kline['l']),
                    float(kline['c']),
                    float(kline['v']),
                )
                insert_futures_data_1m([data_point])
    except Exception as e:
        logging.error(f"Error processing WebSocket message: {e}")

def on_error(ws, error):
    logging.error(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    logging.debug("WebSocket connection closed")

def on_open(ws):
    logging.debug("WebSocket connection opened")

def start_websocket_stream():
    symbols = get_futures_symbols()
    stream_names = [f"{symbol.lower()}@kline_1m" for symbol in symbols]
    stream_url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(stream_names)}"

    ws = websocket.WebSocketApp(
        stream_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    thread = Thread(target=ws.run_forever)
    thread.start()
    logging.debug("Combined WebSocket stream started.")
    return ws
