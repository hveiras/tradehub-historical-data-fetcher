import requests

def get_futures_symbols():
    try:
        # Binance Futures API endpoint for exchange information
        url = 'https://fapi.binance.com/fapi/v1/exchangeInfo'
        
        # Making the GET request
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        
        # Extracting symbol information
        symbols = response.json()['symbols']
        
        # Filtering the symbols for USDT-margined futures that are actively tradable
        usdt_symbols = [
            symbol['symbol'] for symbol in symbols 
            if symbol['quoteAsset'] == 'USDT' and symbol['status'] == 'TRADING'
        ]
        
        print('Available USDT Futures Symbols:', usdt_symbols)
    except requests.exceptions.RequestException as e:
        print('Error fetching symbols:', e)

# Run the function to get symbols
get_futures_symbols()