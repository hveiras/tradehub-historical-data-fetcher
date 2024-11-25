import os

# Binance API credentials
API_KEY = os.getenv('BINANCE_API_KEY', 'your_api_key')
API_SECRET = os.getenv('BINANCE_API_SECRET', 'your_api_secret')

# Database connection
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'dbname': os.getenv('DB_NAME', 'my_timescale_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'mysecretpassword'),
}

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'