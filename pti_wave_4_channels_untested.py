import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def calculate_pti_with_channels(prices, wave1_idx, wave2_idx, wave3_idx, wave4_idx):
    """
    Approximates the Profit Taking Index (PTI) including Wave Four Channels.

    Parameters:
    - prices: A list or pandas Series of price data.
    - wave1_idx: Index of the Wave 1 point.
    - wave2_idx: Index of the Wave 2 point.
    - wave3_idx: Index of the Wave 3 point.
    - wave4_idx: Index of the Wave 4 point.

    Returns:
    - pti: A PTI score between 0 and 100.
    """

    # Extract prices at the wave points
    wave1_price = prices[wave1_idx]
    wave2_price = prices[wave2_idx]
    wave3_price = prices[wave3_idx]
    wave4_price = prices[wave4_idx]

    # Determine if the trend is upward or downward
    uptrend = wave3_price > wave2_price

    if uptrend:
        # Uptrend
        wave3_length = wave3_price - wave2_price
        retracement = wave3_price - wave4_price
    else:
        # Downtrend
        wave3_length = wave2_price - wave3_price
        retracement = wave4_price - wave3_price

    # Calculate the retracement percentage
    retracement_pct = (retracement / wave3_length) * 100

    # Map the retracement percentage to a PTI score
    if retracement_pct <= 38.2:
        pti = 80 + ((38.2 - retracement_pct) / 38.2) * 20  # PTI between 80 and 100
    elif retracement_pct <= 61.8:
        pti = 40 + ((61.8 - retracement_pct) / (61.8 - 38.2)) * 40  # PTI between 40 and 80
    elif retracement_pct <= 100:
        pti = ((100 - retracement_pct) / (100 - 61.8)) * 40  # PTI between 0 and 40
    else:
        pti = 0

    # Ensure PTI is within the 0-100 range
    pti = max(0, min(pti, 100))

    # Calculate Wave Four Channels
    # Base Channel: Line connecting Wave 2 and Wave 4
    base_slope = (wave4_price - wave2_price) / (wave4_idx - wave2_idx)
    base_intercept = wave2_price - base_slope * wave2_idx

    # Acceleration Channel: Line connecting Wave 1 and Wave 3
    accel_slope = (wave3_price - wave1_price) / (wave3_idx - wave1_idx)
    accel_intercept = wave1_price - accel_slope * wave1_idx

    # Expected Wave 4 Price based on Acceleration Channel
    expected_wave4_price = accel_slope * wave4_idx + accel_intercept

    # Adjust PTI based on Wave Four Channels
    channel_adjustment = 0
    if uptrend:
        if wave4_price < expected_wave4_price:
            # Wave 4 has broken below the acceleration channel (possible weakness)
            channel_adjustment = -20  # Reduce PTI by 20 points
    else:
        if wave4_price > expected_wave4_price:
            # Wave 4 has broken above the acceleration channel (possible weakness)
            channel_adjustment = -20  # Reduce PTI by 20 points

    # Apply channel adjustment
    pti += channel_adjustment
    pti = max(0, min(pti, 100))

    return pti

# Example usage:
prices = pd.Series([100, 105, 95, 110, 120, 125, 118, 115, 130])
wave1_idx = 0  # Index of Wave 1
wave2_idx = 2  # Index of Wave 2
wave3_idx = 5  # Index of Wave 3
wave4_idx = 7  # Index of Wave 4

pti_score = calculate_pti_with_channels(prices, wave1_idx, wave2_idx, wave3_idx, wave4_idx)
print(f"The approximated PTI score with Wave Four Channels is: {pti_score:.2f}")
