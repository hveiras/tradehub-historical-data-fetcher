#!/usr/bin/env python3
"""
Simple test script for the Historical Data Fetcher API

This script tests the API endpoints without requiring external dependencies.
"""

import json
import sys
from unittest.mock import Mock, patch

# Mock the external dependencies for testing
sys.modules['flask'] = Mock()
sys.modules['flask_cors'] = Mock()
sys.modules['psycopg2'] = Mock()
sys.modules['pandas'] = Mock()
sys.modules['tqdm'] = Mock()
sys.modules['binance'] = Mock()
sys.modules['binance.client'] = Mock()
sys.modules['binance.exceptions'] = Mock()

# Import our modules after mocking
from api_models import FetchRequest, ApiResponse, create_error_response, create_success_response

def test_fetch_request_validation():
    """Test FetchRequest validation logic."""
    print("Testing FetchRequest validation...")
    
    # Test valid request with symbols
    valid_data = {
        'symbols': ['BTCUSDT', 'ETHUSDT'],
        'intervals': ['1m', '5m'],
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
        'data_type': 'um',
        'cache_dir': 'data',
        'dry_run': False
    }
    
    request = FetchRequest(valid_data)
    is_valid, error = request.validate()
    assert is_valid, f"Valid request failed validation: {error}"
    print("✅ Valid symbols request passed")
    
    # Test valid request with all_symbols
    valid_all_symbols = {
        'all_symbols': True,
        'intervals': ['1d'],
        'start_date': '2023-01-01'
    }
    
    request = FetchRequest(valid_all_symbols)
    is_valid, error = request.validate()
    assert is_valid, f"Valid all_symbols request failed validation: {error}"
    print("✅ Valid all_symbols request passed")
    
    # Test invalid: both symbols and all_symbols
    invalid_both = {
        'symbols': ['BTCUSDT'],
        'all_symbols': True,
        'intervals': ['1m']
    }
    
    request = FetchRequest(invalid_both)
    is_valid, error = request.validate()
    assert not is_valid, "Should fail when both symbols and all_symbols are provided"
    print("✅ Invalid both symbols and all_symbols correctly rejected")
    
    # Test invalid: neither symbols nor all_symbols
    invalid_neither = {
        'intervals': ['1m'],
        'start_date': '2023-01-01'
    }
    
    request = FetchRequest(invalid_neither)
    is_valid, error = request.validate()
    assert not is_valid, "Should fail when neither symbols nor all_symbols are provided"
    print("✅ Invalid neither symbols nor all_symbols correctly rejected")
    
    # Test invalid intervals
    invalid_intervals = {
        'symbols': ['BTCUSDT'],
        'intervals': ['1m', '15m', '4h'],  # 15m and 4h are not supported
        'start_date': '2023-01-01'
    }
    
    request = FetchRequest(invalid_intervals)
    is_valid, error = request.validate()
    assert not is_valid, "Should fail with invalid intervals"
    assert '15m' in error and '4h' in error, "Error should mention invalid intervals"
    print("✅ Invalid intervals correctly rejected")
    
    # Test invalid date format
    invalid_date = {
        'symbols': ['BTCUSDT'],
        'intervals': ['1m'],
        'start_date': '2023/01/01'  # Wrong format
    }
    
    request = FetchRequest(invalid_date)
    is_valid, error = request.validate()
    assert not is_valid, "Should fail with invalid date format"
    print("✅ Invalid date format correctly rejected")
    
    # Test invalid data type
    invalid_data_type = {
        'symbols': ['BTCUSDT'],
        'intervals': ['1m'],
        'start_date': '2023-01-01',
        'data_type': 'invalid'
    }
    
    request = FetchRequest(invalid_data_type)
    is_valid, error = request.validate()
    assert not is_valid, "Should fail with invalid data type"
    print("✅ Invalid data type correctly rejected")

def test_api_responses():
    """Test API response models."""
    print("\nTesting API response models...")
    
    # Test success response
    success_response = create_success_response("Test message", {"key": "value"})
    response_dict, status_code = success_response
    
    assert status_code == 200, "Success response should have status 200"
    assert response_dict['success'] is True, "Success response should have success=True"
    assert response_dict['message'] == "Test message", "Message should match"
    assert response_dict['data']['key'] == "value", "Data should be included"
    print("✅ Success response format correct")
    
    # Test error response
    error_response = create_error_response("Error message", 400)
    response_dict, status_code = error_response
    
    assert status_code == 400, "Error response should have status 400"
    assert response_dict['success'] is False, "Error response should have success=False"
    assert response_dict['message'] == "Error message", "Error message should match"
    print("✅ Error response format correct")
    
    # Test ApiResponse
    api_response = ApiResponse(True, "Test", {"test": "data"})
    response_dict = api_response.to_dict()
    
    assert 'timestamp' in response_dict, "Response should include timestamp"
    assert response_dict['success'] is True, "Success should be preserved"
    assert response_dict['data']['test'] == "data", "Data should be preserved"
    print("✅ ApiResponse model correct")

def test_request_to_dict():
    """Test FetchRequest to_dict conversion."""
    print("\nTesting FetchRequest to_dict...")
    
    data = {
        'symbols': ['BTCUSDT'],
        'intervals': ['1m', '5m'],
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
        'data_type': 'um',
        'cache_dir': 'data',
        'dry_run': True
    }
    
    request = FetchRequest(data)
    result_dict = request.to_dict()
    
    # Check all fields are preserved
    for key, value in data.items():
        assert result_dict[key] == value, f"Field {key} not preserved in to_dict"
    
    # Check default values
    assert result_dict['all_symbols'] is False, "all_symbols should default to False"
    print("✅ FetchRequest to_dict conversion correct")

def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("\nTesting edge cases...")
    
    # Test empty symbols list
    empty_symbols = {
        'symbols': [],
        'intervals': ['1m'],
        'start_date': '2023-01-01'
    }
    
    request = FetchRequest(empty_symbols)
    is_valid, error = request.validate()
    assert not is_valid, "Empty symbols list should be invalid"
    print("✅ Empty symbols list correctly rejected")
    
    # Test non-list symbols
    non_list_symbols = {
        'symbols': 'BTCUSDT',  # Should be a list
        'intervals': ['1m'],
        'start_date': '2023-01-01'
    }
    
    request = FetchRequest(non_list_symbols)
    is_valid, error = request.validate()
    assert not is_valid, "Non-list symbols should be invalid"
    print("✅ Non-list symbols correctly rejected")
    
    # Test non-list intervals
    non_list_intervals = {
        'symbols': ['BTCUSDT'],
        'intervals': '1m',  # Should be a list
        'start_date': '2023-01-01'
    }
    
    request = FetchRequest(non_list_intervals)
    is_valid, error = request.validate()
    assert not is_valid, "Non-list intervals should be invalid"
    print("✅ Non-list intervals correctly rejected")
    
    # Test non-boolean flags
    non_bool_dry_run = {
        'symbols': ['BTCUSDT'],
        'intervals': ['1m'],
        'start_date': '2023-01-01',
        'dry_run': 'true'  # Should be boolean
    }
    
    request = FetchRequest(non_bool_dry_run)
    is_valid, error = request.validate()
    assert not is_valid, "Non-boolean dry_run should be invalid"
    print("✅ Non-boolean dry_run correctly rejected")

def main():
    """Run all tests."""
    print("🧪 Running API Model Tests")
    print("=" * 50)
    
    try:
        test_fetch_request_validation()
        test_api_responses()
        test_request_to_dict()
        test_edge_cases()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed!")
        print("\nThe API models are working correctly.")
        print("You can now start the API with: python api.py")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
