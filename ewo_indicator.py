import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ta.trend import SMAIndicator, EMAIndicator
import requests
import os

# -----------------------------
# Step 1: Data Preparation
# -----------------------------

def fetch_binance_futures_klines(symbol='BTCUSDT', interval='1h', limit=1500):
    """
    Fetch klines data from Binance Futures API.

    Parameters:
    - symbol: Trading pair symbol (default 'BTCUSDT').
    - interval: Kline interval (default '1h').
    - limit: Number of klines to retrieve (max 1500).

    Returns:
    - df: DataFrame with 'close' prices and datetime index.
    """
    url = 'https://fapi.binance.com/fapi/v1/klines'
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()

        # Define column names based on Binance API documentation
        columns = [
            'Open time', 'Open', 'High', 'Low', 'Close', 'Volume',
            'Close time', 'Quote asset volume', 'Number of trades',
            'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'
        ]

        # Create DataFrame
        df = pd.DataFrame(data, columns=columns)

        # Convert timestamp to datetime
        df['Open time'] = pd.to_datetime(df['Open time'], unit='ms')
        df.set_index('Open time', inplace=True)

        # Convert 'Close' to numeric
        df['close'] = pd.to_numeric(df['Close'])

        # Select only the 'close' price for simplicity
        df = df[['close']]

        return df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Binance API: {e}")
        return None

# Fetch the data
df = fetch_binance_futures_klines(symbol='BTCUSDT', interval='1h', limit=1500)

if df is not None and not df.empty:
    # Ensure the DataFrame is sorted by datetime
    df.sort_index(inplace=True)
else:
    raise ValueError("Failed to fetch data from Binance API.")

# -----------------------------
# Step 2: Define Indicator Parameters and Calculate EWO
# -----------------------------

def calculate_elliott_wave_oscillator(df, timeframe='1H', use_percent=True,
                                     sma1length=5, sma2length=35,
                                     smoothLength1D=1, tolerance1D=0.5,
                                     smoothLength1H=1, tolerance1H=0.5,
                                     smoothLength5M=1, tolerance5M=0.5,
                                     smoothLengthDefault=1, toleranceDefault=0.5,
                                     filter_peaks=True,
                                     show_breakbands=True,
                                     breakbands_color=(255/255, 255/255, 255/255, 0.216),
                                     export_csv=False,
                                     csv_filename='ewo_output.csv',
                                     export_directory='output'):
    """
    Calculate the Elliott Wave Oscillator with Derivative Peak Detection and Breakout Bands.

    Parameters:
    - df: pandas DataFrame with a DatetimeIndex and a 'close' column.
    - timeframe: String representing the timeframe (e.g., 'D', 'H', '1H', '5T').
    - use_percent: Boolean to determine if EWO is percentage-based.
    - sma1length: Length for short SMA.
    - sma2length: Length for long SMA.
    - smoothLength1D, tolerance1D: Smoothing length and tolerance for Daily.
    - smoothLength1H, tolerance1H: Smoothing length and tolerance for Hourly.
    - smoothLength5M, tolerance5M: Smoothing length and tolerance for 5-Minute.
    - smoothLengthDefault, toleranceDefault: Smoothing length and tolerance for other timeframes.
    - filter_peaks: Boolean to filter peaks by breakout bands.
    - show_breakbands: Boolean to show breakout bands.
    - breakbands_color: Color for the breakout bands (RGBA tuple).
    - export_csv: Boolean to determine if CSV export is needed.
    - csv_filename: Name of the output CSV file.
    - export_directory: Directory where the CSV will be saved.

    Returns:
    - df: DataFrame with additional columns for EWO, smoothed EWO, breakout bands, and peak/trough markers.
    """

    # -----------------------------
    # Step 3: Determine Timeframe and Set Parameters
    # -----------------------------

    # Mapping Pine Script's timeframe detection to pandas frequency
    # Pine Script uses 'D' for daily, '60' for hourly, '5T' for 5-minute, etc.
    # In pandas, frequencies are like 'D', 'H', '5T', etc.

    freq = pd.infer_freq(df.index)
    if freq is None:
        # If frequency can't be inferred, use the provided timeframe
        freq = timeframe

    if freq.startswith('D'):
        smoothLength = smoothLength1D
        tolerance = tolerance1D
    elif freq.startswith('H') or freq == '60' or freq.startswith('1H'):
        smoothLength = smoothLength1H
        tolerance = tolerance1H
    elif freq.startswith('T') or freq.startswith('min'):
        # Assuming 'T' stands for minute-based frequencies
        # Extract the number of minutes
        try:
            minutes = int(freq.rstrip('T'))
            if minutes == 5:
                smoothLength = smoothLength5M
                tolerance = tolerance5M
            else:
                smoothLength = smoothLengthDefault
                tolerance = toleranceDefault
        except ValueError:
            smoothLength = smoothLengthDefault
            tolerance = toleranceDefault
    else:
        smoothLength = smoothLengthDefault
        tolerance = toleranceDefault

    # -----------------------------
    # Step 4: Calculate Simple Moving Averages (SMA)
    # -----------------------------

    sma1 = SMAIndicator(close=df['close'], window=sma1length, fillna=True).sma_indicator()
    sma2 = SMAIndicator(close=df['close'], window=sma2length, fillna=True).sma_indicator()

    df['sma1'] = sma1
    df['sma2'] = sma2

    # -----------------------------
    # Step 5: Calculate Elliott Wave Oscillator (EWO)
    # -----------------------------

    if use_percent:
        df['smadif'] = (df['sma1'] - df['sma2']) / df['close'] * 100
    else:
        df['smadif'] = df['sma1'] - df['sma2']

    # -----------------------------
    # Step 6: Smooth the EWO with EMA
    # -----------------------------

    smadif_smooth = EMAIndicator(close=df['smadif'], window=smoothLength, fillna=True).ema_indicator()
    df['smadif_smooth'] = smadif_smooth

    # -----------------------------
    # Step 7: Calculate Derivative
    # -----------------------------

    df['derivative'] = df['smadif_smooth'].diff()

    # -----------------------------
    # Step 8: Identify Peaks and Troughs
    # -----------------------------

    df['derivative_prev'] = df['derivative'].shift(1)

    df['is_positive_peak'] = (
        (df['derivative_prev'] > 0) &
        (df['derivative'] < 0) &
        (df['derivative'].abs() < tolerance)
    )

    df['is_negative_trough'] = (
        (df['derivative_prev'] < 0) &
        (df['derivative'] > 0) &
        (df['derivative'].abs() < tolerance)
    )

    # -----------------------------
    # Step 9: Calculate Breakout Bands
    # -----------------------------

    if show_breakbands:
        upperband = []
        lowerband = []
        k = 1
        k2 = 0.0555

        # Initialize previous bands
        prev_upper = np.nan
        prev_lower = np.nan

        for idx, row in df.iterrows():
            smadif_val = row['smadif_smooth']

            if np.isnan(smadif_val):
                upperband.append(np.nan)
                lowerband.append(np.nan)
                continue

            if smadif_val > 0:
                if np.isnan(prev_upper):
                    current_upper = smadif_val
                else:
                    current_upper = prev_upper + k2 * (k * smadif_val - prev_upper)
                current_lower = prev_lower  # No change
            else:
                if np.isnan(prev_lower):
                    current_lower = smadif_val
                else:
                    current_lower = prev_lower + k2 * (k * smadif_val - prev_lower)
                current_upper = prev_upper  # No change

            upperband.append(current_upper)
            lowerband.append(current_lower)

            prev_upper = current_upper
            prev_lower = current_lower

        df['upperband'] = upperband
        df['lowerband'] = lowerband
    else:
        df['upperband'] = np.nan
        df['lowerband'] = np.nan

    # -----------------------------
    # Step 10: Filter Peaks Based on Breakout Bands
    # -----------------------------

    if filter_peaks and show_breakbands:
        df['plotPositivePeak'] = df['is_positive_peak'] & (df['smadif_smooth'] > df['upperband'])
        df['plotNegativeTrough'] = df['is_negative_trough'] & (df['smadif_smooth'] < df['lowerband'])
    else:
        df['plotPositivePeak'] = df['is_positive_peak']
        df['plotNegativeTrough'] = df['is_negative_trough']

    # -----------------------------
    # Step 11: Visualization
    # -----------------------------

    plt.figure(figsize=(14, 10))

    # Subplot 1: Price Chart (Optional)
    ax1 = plt.subplot(3, 1, 1)
    ax1.plot(df.index, df['close'], label='Close Price', color='black')
    ax1.set_title('Price Chart')
    ax1.set_ylabel('Price (USD)')
    ax1.legend()
    ax1.grid(True)

    # Subplot 2: Elliott Wave Oscillator
    ax2 = plt.subplot(3, 1, 2, sharex=ax1)
    ax2.bar(df.index, df['smadif'], color=np.where(df['smadif'] <= 0, 'red', 'green'), alpha=0.6, label='Original EWO')
    ax2.plot(df.index, df['smadif_smooth'], color='blue', linewidth=2, label='Smoothed EWO')
    if show_breakbands:
        ax2.plot(df.index, df['upperband'], color=np.array(breakbands_color), linewidth=2, label='Upper Band')
        ax2.plot(df.index, df['lowerband'], color=np.array(breakbands_color), linewidth=2, label='Lower Band')
    ax2.set_title('Elliott Wave Oscillator (EWO)')
    ax2.set_ylabel('EWO')
    ax2.legend()
    ax2.grid(True)

    # Subplot 3: Peaks and Troughs
    ax3 = plt.subplot(3, 1, 3, sharex=ax1)
    ax3.plot(df.index, df['smadif_smooth'], color='blue', linewidth=2, label='Smoothed EWO')
    if show_breakbands:
        ax3.plot(df.index, df['upperband'], color=np.array(breakbands_color), linewidth=2, label='Upper Band')
        ax3.plot(df.index, df['lowerband'], color=np.array(breakbands_color), linewidth=2, label='Lower Band')

    # Plot Positive Peaks
    peaks = df[df['plotPositivePeak']]
    ax3.scatter(peaks.index, peaks['smadif_smooth'], marker='^', color='purple', s=100, label='Positive Peak')

    # Plot Negative Troughs
    troughs = df[df['plotNegativeTrough']]
    ax3.scatter(troughs.index, troughs['smadif_smooth'], marker='v', color='red', s=100, label='Negative Trough')

    ax3.set_title('Peaks and Troughs')
    ax3.set_ylabel('EWO Smoothed')
    ax3.legend()
    ax3.grid(True)

    plt.tight_layout()
    plt.show()

    # -----------------------------
    # Step 12: Export EWO Data to CSV
    # -----------------------------

    if export_csv:
        # Create the export directory if it doesn't exist
        if not os.path.exists(export_directory):
            os.makedirs(export_directory)

        # Prepare the DataFrame for export
        export_df = pd.DataFrame({
            'Timestamp': df.index,
            'EWO_Value': df['smadif'],
            'Is_Max': df['is_positive_peak'],
            'Is_Min': df['is_negative_trough']
        })

        # Optionally, format the timestamp
        export_df['Timestamp'] = export_df['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

        # Define the full path for the CSV file
        csv_path = os.path.join(export_directory, csv_filename)

        try:
            export_df.to_csv(csv_path, index=False)
            print(f"EWO data successfully exported to {csv_path}")
        except Exception as e:
            print(f"Failed to export EWO data to CSV: {e}")

    return df

# Execute the indicator calculation with '1H' timeframe and export CSV
df_with_indicator = calculate_elliott_wave_oscillator(
    df,
    timeframe='1H',
    use_percent=True,
    export_csv=True,                 # Enable CSV export
    csv_filename='ewo_output.csv',   # Name of the CSV file
    export_directory='output'        # Directory to save the CSV
)

# The returned DataFrame `df_with_indicator` contains additional columns:
# - 'sma1', 'sma2', 'smadif', 'smadif_smooth'
# - 'derivative', 'derivative_prev'
# - 'is_positive_peak', 'is_negative_trough'
# - 'upperband', 'lowerband' (if breakout bands are shown)
# - 'plotPositivePeak', 'plotNegativeTrough'
