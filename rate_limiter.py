import time
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class BinanceRateLimiter:
    def __init__(self, rate_limits):
        """
        Initialize the rate limiter with Binance's rate limit information.
        """
        self.rate_limits = rate_limits
        self.locks = {}
        self.counters = {}
        self.reset_times = {}
        self.lock = Lock()
        
        for limit in self.rate_limits:
            key = limit['rateLimitType']
            self.locks[key] = Lock()
            self.counters[key] = 0
            interval = limit['intervalNum'] * self.get_interval_seconds(limit['interval'])
            self.reset_times[key] = time.time() + interval

    def get_interval_seconds(self, interval):
        """
        Convert Binance interval string to seconds.
        """
        if interval == "SECOND":
            return 1
        elif interval == "MINUTE":
            return 60
        elif interval == "DAY":
            return 86400
        else:
            logger.warning(f"Unknown interval type: {interval}. Defaulting to 60 seconds.")
            return 60

    def acquire(self, rate_limit_type):
        """
        Acquire permission to make a request under the specified rate limit type.
        """
        with self.locks[rate_limit_type]:
            current_time = time.time()
            if current_time >= self.reset_times[rate_limit_type]:
                # Reset the counter and reset time
                self.counters[rate_limit_type] = 0
                interval = self.rate_limits_by_type(rate_limit_type)['intervalNum'] * \
                           self.get_interval_seconds(self.rate_limits_by_type(rate_limit_type)['interval'])
                self.reset_times[rate_limit_type] = current_time + interval
                logger.debug(f"Resetting rate limit for {rate_limit_type}. New reset time: {self.reset_times[rate_limit_type]}")

            if self.counters[rate_limit_type] < self.rate_limits_by_type(rate_limit_type)['limit']:
                self.counters[rate_limit_type] += 1
                logger.debug(f"Acquired {rate_limit_type} request. Count: {self.counters[rate_limit_type]}")
                return
            else:
                # Need to wait until the reset time
                sleep_time = self.reset_times[rate_limit_type] - current_time
                logger.warning(f"Rate limit reached for {rate_limit_type}. Sleeping for {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
                # Reset after sleeping
                self.counters[rate_limit_type] = 1
                self.reset_times[rate_limit_type] = time.time() + \
                    self.rate_limits_by_type(rate_limit_type)['intervalNum'] * \
                    self.get_interval_seconds(self.rate_limits_by_type(rate_limit_type)['interval'])
                logger.debug(f"Resumed after sleep. New count for {rate_limit_type}: {self.counters[rate_limit_type]}")

    def rate_limits_by_type(self, rate_limit_type):
        """
        Retrieve rate limit details by type.
        """
        for limit in self.rate_limits:
            if limit['rateLimitType'] == rate_limit_type:
                return limit
        logger.error(f"Rate limit type {rate_limit_type} not found.")
        raise ValueError(f"Rate limit type {rate_limit_type} not found.")
