#!/usr/bin/env python3
"""
Test script to verify app.py shows the correct API-only message
"""

import sys
import subprocess
from unittest.mock import patch, Mock

# Mock all the external dependencies
sys.modules['pandas'] = Mock()
sys.modules['tqdm'] = Mock()
sys.modules['binance'] = Mock()
sys.modules['binance.client'] = Mock()
sys.modules['binance.exceptions'] = Mock()
sys.modules['psycopg2'] = Mock()
sys.modules['psycopg2.extras'] = Mock()

# Mock the config module
config_mock = Mock()
config_mock.LOG_LEVEL = 'INFO'
config_mock.LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
config_mock.API_KEY = 'test_key'
config_mock.API_SECRET = 'test_secret'
config_mock.DB_CONFIG = {'host': 'localhost'}
sys.modules['config'] = config_mock

# Mock the database module
database_mock = Mock()
sys.modules['database'] = database_mock

# Mock the rate_limiter module
rate_limiter_mock = Mock()
sys.modules['rate_limiter'] = rate_limiter_mock

# Mock the binance_client module
binance_client_mock = Mock()
binance_client_mock.get_exchange_info = Mock()
binance_client_mock.get_futures_symbols = Mock()
sys.modules['binance_client'] = binance_client_mock

def test_app_message():
    """Test that app.py shows the correct API-only message."""
    print("Testing app.py API-only message...")
    
    try:
        # Import app.py after mocking dependencies
        import app
        
        # Capture the output when running the main block
        with patch('sys.exit') as mock_exit:
            with patch('builtins.print') as mock_print:
                # Simulate running the script
                exec(compile(open('app.py').read(), 'app.py', 'exec'))
        
        # Check that print was called with the expected messages
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        
        expected_messages = [
            "=" * 60,
            "HISTORICAL DATA FETCHER - API ONLY SERVICE",
            "This service is now API-only and does not support command-line arguments.",
            "To start the REST API server:",
            "  python api.py",
            "The API will be available at: http://localhost:5000",
            "Available endpoints:",
            "  POST /api/fetch        - Start a historical data fetch",
            "For detailed API documentation, see README.md"
        ]
        
        # Check that key messages are present
        all_output = ' '.join(print_calls)
        
        for expected in expected_messages:
            if expected in all_output:
                print(f"✅ Found expected message: {expected[:50]}...")
            else:
                print(f"❌ Missing expected message: {expected[:50]}...")
                return False
        
        # Check that sys.exit(1) was called
        mock_exit.assert_called_with(1)
        print("✅ sys.exit(1) was called correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing app.py: {e}")
        return False

def main():
    """Run the test."""
    print("🧪 Testing app.py API-only message")
    print("=" * 50)
    
    success = test_app_message()
    
    if success:
        print("\n🎉 Test passed! app.py correctly shows API-only message.")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
