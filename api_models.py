"""
API Models and Validation for Historical Data Fetcher API

This module contains request/response models and validation logic for the Flask API.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class FetchRequest:
    """Model for historical data fetch request."""
    
    def __init__(self, data: dict):
        self.symbols = data.get('symbols')
        self.all_symbols = data.get('all_symbols', False)
        self.intervals = data.get('intervals', ['1m'])
        self.start_date = data.get('start_date', '2019-12-31')
        self.end_date = data.get('end_date')
        self.data_type = data.get('data_type', 'um')
        self.dry_run = data.get('dry_run', False)
    
    def validate(self) -> Tuple[bool, str]:
        """
        Validate the fetch request.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Validate symbol selection (mutually exclusive)
        if self.all_symbols and self.symbols:
            return False, "Cannot specify both 'symbols' and 'all_symbols'. Choose one."
        
        if not self.all_symbols and not self.symbols:
            return False, "Must specify either 'symbols' or set 'all_symbols' to true."
        
        if self.symbols and not isinstance(self.symbols, list):
            return False, "'symbols' must be a list of strings."
        
        if self.symbols and len(self.symbols) == 0:
            return False, "'symbols' list cannot be empty."
        
        # Validate intervals
        if not isinstance(self.intervals, list):
            return False, "'intervals' must be a list of strings."
        
        supported_intervals = ['1m', '5m', '1h', '1d']
        invalid_intervals = [i for i in self.intervals if i not in supported_intervals]
        if invalid_intervals:
            return False, f"Invalid intervals: {invalid_intervals}. Supported: {supported_intervals}"
        
        # Validate dates
        if not self._validate_date(self.start_date):
            return False, f"Invalid start_date format: {self.start_date}. Use YYYY-MM-DD format."
        
        if self.end_date and not self._validate_date(self.end_date):
            return False, f"Invalid end_date format: {self.end_date}. Use YYYY-MM-DD format."
        
        # Validate data type
        if self.data_type not in ['um', 'cm']:
            return False, f"Invalid data_type: {self.data_type}. Must be 'um' or 'cm'."
        
        # Validate boolean fields
        if not isinstance(self.all_symbols, bool):
            return False, "'all_symbols' must be a boolean."
        
        if not isinstance(self.dry_run, bool):
            return False, "'dry_run' must be a boolean."
        
        return True, ""
    
    def _validate_date(self, date_string: str) -> bool:
        """Validate date string format."""
        try:
            datetime.strptime(date_string, '%Y-%m-%d')
            return True
        except (ValueError, TypeError):
            return False
    
    def to_dict(self) -> dict:
        """Convert request to dictionary."""
        return {
            'symbols': self.symbols,
            'all_symbols': self.all_symbols,
            'intervals': self.intervals,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'data_type': self.data_type,
            'dry_run': self.dry_run
        }


class ApiResponse:
    """Base API response model."""
    
    def __init__(self, success: bool, message: str, data: Optional[dict] = None):
        self.success = success
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> dict:
        """Convert response to dictionary."""
        return {
            'success': self.success,
            'message': self.message,
            'data': self.data,
            'timestamp': self.timestamp
        }


class FetchResponse(ApiResponse):
    """Response model for fetch requests."""
    
    def __init__(self, success: bool, message: str, request_summary: Optional[dict] = None, 
                 estimated_data: Optional[dict] = None):
        super().__init__(success, message)
        if request_summary:
            self.data['request_summary'] = request_summary
        if estimated_data:
            self.data['estimated_data'] = estimated_data


class SymbolsResponse(ApiResponse):
    """Response model for symbols endpoint."""
    
    def __init__(self, success: bool, message: str, symbols: Optional[List[str]] = None):
        super().__init__(success, message)
        if symbols:
            self.data['symbols'] = symbols
            self.data['count'] = len(symbols)


class IntervalsResponse(ApiResponse):
    """Response model for intervals endpoint."""
    
    def __init__(self, success: bool, message: str, intervals: Optional[List[str]] = None):
        super().__init__(success, message)
        if intervals:
            self.data['intervals'] = intervals
            self.data['count'] = len(intervals)


def create_error_response(message: str, status_code: int = 400) -> Tuple[dict, int]:
    """Create a standardized error response."""
    response = ApiResponse(success=False, message=message)
    return response.to_dict(), status_code


def create_success_response(message: str, data: Optional[dict] = None) -> Tuple[dict, int]:
    """Create a standardized success response."""
    response = ApiResponse(success=True, message=message, data=data)
    return response.to_dict(), 200
