-- 1m data
CREATE TABLE IF NOT EXISTS futures_data_historical_1m (
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

SELECT create_hypertable('futures_data_historical_1m', 'timestamp', if_not_exists => TRUE);

-- 5m data
CREATE TABLE IF NOT EXISTS futures_data_historical_5m (
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

SELECT create_hypertable('futures_data_historical_5m', 'timestamp', if_not_exists => TRUE);

-- 1h data
CREATE TABLE IF NOT EXISTS futures_data_historical_1h (
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

SELECT create_hypertable('futures_data_historical_1h', 'timestamp', if_not_exists => TRUE);

-- 1d data
CREATE TABLE IF NOT EXISTS futures_data_historical_1d (
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

SELECT create_hypertable('futures_data_historical_1d', 'timestamp', if_not_exists => TRUE);
