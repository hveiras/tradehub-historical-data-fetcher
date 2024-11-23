import psycopg2
import logging
from config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

def insert_futures_data_1m(data):
    query = """
    INSERT INTO futures_data_1m (exchange, symbol, timestamp, open, high, low, close, volume)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (exchange, symbol, timestamp) DO NOTHING;
    """
    try:
        cursor.executemany(query, data)
        rows_inserted = cursor.rowcount
        conn.commit()
        logging.debug(f"Inserted {rows_inserted} records into TimescaleDB.")
    except Exception as e:
        logging.error(f"Error inserting data: {e}")
        conn.rollback()
