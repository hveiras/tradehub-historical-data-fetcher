import psycopg2
import logging
from psycopg2.extras import execute_values
from config import DB_CONFIG

logger = logging.getLogger(__name__)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    logger.debug("Connected to TimescaleDB successfully.")
except Exception as e:
    logger.error(f"Failed to connect to TimescaleDB: {e}")
    raise

def insert_futures_data_1m(data):
    """
    Insert a list of candlestick data into the TimescaleDB table.
    """
    insert_query = """
    INSERT INTO futures_data_1m (exchange, symbol, timestamp, open, high, low, close, volume)
    VALUES %s
    ON CONFLICT (exchange, symbol, timestamp) DO NOTHING
    RETURNING exchange;
    """
    try:
        logger.debug(f"Inserting {len(data)} records into TimescaleDB for symbol {data[0][1]}.")
        execute_values(cursor, insert_query, data, page_size=1000)
        inserted_rows = cursor.fetchall()
        rows_inserted = len(inserted_rows)
        conn.commit()
        if rows_inserted:
            logger.debug(f"Inserted {rows_inserted} records into TimescaleDB.")
        else:
            logger.debug("No new records were inserted.")
    except Exception as e:
        logger.error(f"Error inserting data into TimescaleDB: {e}")
        conn.rollback()
