CREATE TABLE IF NOT EXISTS futures_data_1m (
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (exchange, symbol, timestamp)
);

SELECT create_hypertable('futures_data_1m', 'timestamp', if_not_exists => TRUE);
