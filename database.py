import psycopg2
import logging
import traceback
import socket
from psycopg2.extras import execute_values
from config import DB_CONFIG

logger = logging.getLogger(__name__)

# Global connection and cursor variables
conn = None
cursor = None

def connect_to_database(max_retries=3, retry_delay=5):
    """
    Establish a connection to TimescaleDB with retry logic and enhanced error reporting.
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Seconds to wait between retries
    
    Returns:
        tuple: (connection, cursor) if successful, raises exception otherwise
    """
    global conn, cursor
    
    import time
    
    for attempt in range(1, max_retries + 1):
        try:
            # Log connection attempt with DB host information
            logger.info(f"Connecting to TimescaleDB at {DB_CONFIG['host']}:{DB_CONFIG.get('port', 5432)}, "
                       f"database: {DB_CONFIG['dbname']} (Attempt {attempt}/{max_retries})")
            
            # Try to resolve hostname to check network connectivity
            try:
                ip_address = socket.gethostbyname(DB_CONFIG['host'])
                logger.debug(f"Resolved {DB_CONFIG['host']} to {ip_address}")
            except socket.gaierror as e:
                logger.error(f"DNS resolution failed for {DB_CONFIG['host']}: {e}")
            
            # Attempt connection with timeout
            conn = psycopg2.connect(**DB_CONFIG, connect_timeout=10)
            cursor = conn.cursor()
            
            # Test the connection with a simple query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            logger.info(f"Connected to TimescaleDB successfully. Server version: {version}")
            
            return conn, cursor
            
        except psycopg2.OperationalError as e:
            error_msg = str(e).strip()
            logger.error(f"Database connection error (Attempt {attempt}/{max_retries}): {error_msg}")
            
            # Provide more specific error guidance based on error message
            if "could not connect to server" in error_msg:
                logger.error("Connection refused. Possible causes:")
                logger.error(" - Database server is not running")
                logger.error(" - Firewall is blocking the connection")
                logger.error(" - Incorrect host or port")
            elif "password authentication failed" in error_msg:
                logger.error("Authentication failed. Check your username and password.")
            elif "database" in error_msg and "does not exist" in error_msg:
                logger.error(f"Database '{DB_CONFIG['dbname']}' does not exist. Create it or check the name.")
            
            # Print connection details for debugging (masking password)
            debug_config = DB_CONFIG.copy()
            if 'password' in debug_config:
                debug_config['password'] = '********'
            logger.debug(f"Connection parameters: {debug_config}")
            
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.critical("Maximum connection attempts reached. Could not connect to database.")
                raise
                
        except Exception as e:
            logger.error(f"Unexpected error connecting to database: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

# Try to establish the initial connection
try:
    conn, cursor = connect_to_database()
except Exception as e:
    logger.critical(f"Failed to establish initial database connection: {e}")
    # Don't raise here to allow the application to start even with DB issues
    # The application can try to reconnect later

def insert_futures_data(data, timeframe):
    """
    Insert a list of candlestick data into the appropriate TimescaleDB table based on timeframe.
    Includes connection recovery logic.

    :param data: List of tuples containing candlestick data
    :param timeframe: Timeframe string (1m, 5m, 1h, 1d)
    """
    global conn, cursor

    # Check if connection is still alive, reconnect if needed
    try:
        if conn is None or cursor is None or conn.closed:
            logger.warning("Database connection lost. Attempting to reconnect...")
            conn, cursor = connect_to_database()
    except Exception as e:
        logger.error(f"Failed to reconnect to database: {e}")
        raise

    # Map timeframes to table names
    table_mapping = {
        '1m': 'futures_data_historical_1m',
        '5m': 'futures_data_historical_5m',
        '1h': 'futures_data_historical_1h',
        '1d': 'futures_data_historical_1d'
    }

    if timeframe not in table_mapping:
        raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {list(table_mapping.keys())}")

    table_name = table_mapping[timeframe]
    insert_query = f"""
    INSERT INTO {table_name} (exchange, symbol, timestamp, open, high, low, close, volume)
    VALUES %s
    ON CONFLICT (exchange, symbol, timestamp) DO NOTHING
    RETURNING exchange;
    """

    try:
        if not data:
            logger.warning("Attempted to insert empty data set")
            return

        logger.debug(f"Inserting {len(data)} records into {table_name} for symbol {data[0][1]}.")
        execute_values(cursor, insert_query, data, page_size=1000)
        inserted_rows = cursor.fetchall()
        rows_inserted = len(inserted_rows)
        conn.commit()
        if rows_inserted:
            logger.debug(f"Inserted {rows_inserted} records into {table_name}.")
        else:
            logger.debug("No new records were inserted.")
    except psycopg2.Error as e:
        logger.error(f"Database error inserting data: {e.pgerror if hasattr(e, 'pgerror') else str(e)}")
        logger.error(f"Error code: {e.pgcode if hasattr(e, 'pgcode') else 'N/A'}")
        conn.rollback()

        # Try to reconnect if it's a connection issue
        if isinstance(e, psycopg2.OperationalError) or "connection" in str(e).lower():
            logger.warning("Connection may be lost. Attempting to reconnect...")
            try:
                conn, cursor = connect_to_database()
                logger.info("Reconnected to database successfully.")
            except Exception as reconnect_error:
                logger.error(f"Failed to reconnect: {reconnect_error}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error inserting data into {table_name}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Include sample of problematic data for debugging
        if data:
            sample = data[0] if len(data) == 1 else f"{data[0]} ... (and {len(data)-1} more)"
            logger.debug(f"Sample data that caused the error: {sample}")

        conn.rollback()
        raise

# Backward compatibility function
def insert_futures_data_1m(data):
    """
    Backward compatibility wrapper for 1m data insertion.
    """
    return insert_futures_data(data, '1m')
