import pandas as pd

def calculate_pti(prices, wave2_idx, wave3_idx, wave4_idx):
    """
    Approximates the Profit Taking Index (PTI) based on Wave 3 and Wave 4 retracement.

    Parameters:
    - prices: A list or pandas Series of price data.
    - wave2_idx: Index of the Wave 2 point.
    - wave3_idx: Index of the Wave 3 point.
    - wave4_idx: Index of the Wave 4 point.

    Returns:
    - pti: A PTI score between 0 and 100.
    """

    # Extract prices at the wave points
    wave2_price = prices[wave2_idx]
    wave3_price = prices[wave3_idx]
    wave4_price = prices[wave4_idx]

    # Determine if the trend is upward or downward
    if wave3_price > wave2_price:
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
        # Strong likelihood of Wave 5 completion
        pti = 80 + ((38.2 - retracement_pct) / 38.2) * 20  # PTI between 80 and 100
    elif retracement_pct <= 61.8:
        # Moderate likelihood
        pti = 40 + ((61.8 - retracement_pct) / (61.8 - 38.2)) * 40  # PTI between 40 and 80
    elif retracement_pct <= 100:
        # Weak likelihood
        pti = ((100 - retracement_pct) / (100 - 61.8)) * 40  # PTI between 0 and 40
    else:
        # Retracement exceeds 100%, very low likelihood
        pti = 0

    # Ensure PTI is within the 0-100 range
    pti = max(0, min(pti, 100))

    return pti

# Example usage:
# Suppose we have a pandas Series of prices and the indices of Waves 2, 3, and 4
prices = pd.Series([100, 105, 110, 115, 120, 125, 120, 118, 122])
wave2_idx = 2  # Index of Wave 2
wave3_idx = 5  # Index of Wave 3
wave4_idx = 7  # Index of Wave 4

pti_score = calculate_pti(prices, wave2_idx, wave3_idx, wave4_idx)
print(f"The approximated PTI score is: {pti_score:.2f}")
