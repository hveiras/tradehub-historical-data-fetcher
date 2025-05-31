#!/usr/bin/env python3
"""
Flask API for Historical Data Fetcher

This module provides a REST API interface for the historical data fetcher,
allowing users to start data fetches via HTTP requests instead of command line.

Usage:
    python api.py

API Endpoints:
    POST /api/fetch - Start a historical data fetch
    GET /api/symbols - Get available trading symbols
    GET /api/intervals - Get supported timeframes
    GET /api/health - Health check
"""

import logging
import sys
import threading
from datetime import datetime

from flask import Flask, request, Response
from flask_cors import CORS

# Import existing modules
from config import LOG_LEVEL, LOG_FORMAT
from binance_client import fetch_and_insert_all_historical_data, get_futures_symbols
from app import validate_symbols, validate_intervals, initialize_rate_limiter
from api_models import (
    FetchRequest, FetchResponse, SymbolsResponse, IntervalsResponse,
    create_error_response, create_success_response
)

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables for tracking active fetches
active_fetches = {}
fetch_counter = 0


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Test database connection by trying to get exchange info
        from database import connect_to_database
        conn, cursor = connect_to_database()
        if conn and cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            db_status = "connected"
        else:
            db_status = "disconnected"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        db_status = "error"
    
    health_data = {
        'status': 'healthy',
        'database': db_status,
        'active_fetches': len(active_fetches),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return create_success_response("Service is healthy", health_data)


@app.route('/api/symbols', methods=['GET'])
def get_symbols():
    """Get list of available trading symbols."""
    try:
        symbols = get_futures_symbols()
        if not symbols:
            return create_error_response("Failed to fetch symbols from Binance", 503)
        
        response = SymbolsResponse(
            success=True,
            message=f"Retrieved {len(symbols)} perpetual futures symbols",
            symbols=symbols
        )
        return response.to_dict(), 200
        
    except Exception as e:
        logger.error(f"Error fetching symbols: {e}")
        return create_error_response(f"Failed to fetch symbols: {str(e)}", 500)
    
@app.route('/api/symbols/perp-tradingview', methods=['GET'])
def get_symbols_perp():
    """Get list of available trading symbols in TradingView perpetual futures format."""
    try:
        symbols = get_futures_symbols()
        if not symbols:
            return create_error_response("Failed to fetch symbols from Binance", 503)

        # Convert to TradingView perpetual futures format
        perp_symbols = [f"BINANCE:{symbol}.P" for symbol in symbols]
        output_txt = ",".join(perp_symbols)

        return Response(output_txt, mimetype='text/plain'), 200

    except Exception as e:
        logger.error(f"Error fetching perp symbols: {e}")
        return create_error_response(f"Failed to fetch perp symbols: {str(e)}", 500)


@app.route('/api/intervals', methods=['GET'])
def get_intervals():
    """Get list of supported timeframes."""
    supported_intervals = ['1m', '5m', '1h', '1d']
    
    response = IntervalsResponse(
        success=True,
        message=f"Retrieved {len(supported_intervals)} supported intervals",
        intervals=supported_intervals
    )
    return response.to_dict(), 200


@app.route('/api/fetch', methods=['POST'])
def start_fetch():
    """Start a historical data fetch."""
    global fetch_counter
    
    try:
        # Parse request data
        if not request.is_json:
            return create_error_response("Request must be JSON", 400)
        
        data = request.get_json()
        if not data:
            return create_error_response("Request body cannot be empty", 400)
        
        # Create and validate request model
        fetch_request = FetchRequest(data)
        is_valid, error_message = fetch_request.validate()
        
        if not is_valid:
            return create_error_response(error_message, 400)
        
        # Validate symbols if provided
        if fetch_request.symbols:
            valid_symbols = validate_symbols(fetch_request.symbols)
            if not valid_symbols:
                return create_error_response("No valid symbols provided", 400)
            fetch_request.symbols = valid_symbols
        
        # Validate intervals
        valid_intervals = validate_intervals(fetch_request.intervals)
        if not valid_intervals:
            return create_error_response("No valid intervals provided", 400)
        fetch_request.intervals = valid_intervals
        
        # Generate fetch ID
        fetch_counter += 1
        fetch_id = f"fetch_{fetch_counter}_{int(datetime.utcnow().timestamp())}"
        
        # Prepare request summary
        request_summary = {
            'fetch_id': fetch_id,
            'symbols': fetch_request.symbols if fetch_request.symbols else "ALL_PERPETUAL_FUTURES",
            'symbol_count': len(fetch_request.symbols) if fetch_request.symbols else "ALL",
            'intervals': valid_intervals,
            'start_date': fetch_request.start_date,
            'end_date': fetch_request.end_date or 'today',
            'data_type': fetch_request.data_type,
            'dry_run': fetch_request.dry_run
        }
        
        # Handle dry run mode
        if fetch_request.dry_run:
            response = FetchResponse(
                success=True,
                message="Dry run completed - no data will be fetched",
                request_summary=request_summary
            )
            return response.to_dict(), 200
        
        # Start the fetch in a background thread
        def run_fetch():
            try:
                logger.info(f"Starting fetch {fetch_id}")
                active_fetches[fetch_id] = {
                    'status': 'running',
                    'started_at': datetime.utcnow().isoformat(),
                    'request': request_summary
                }
                
                # Initialize rate limiter
                rate_limiter = initialize_rate_limiter()
                
                # Start the historical data fetch
                fetch_and_insert_all_historical_data(
                    rate_limiter=rate_limiter,
                    symbols=fetch_request.symbols,
                    intervals=valid_intervals,
                    start_date=fetch_request.start_date,
                    end_date=fetch_request.end_date,
                    data_type=fetch_request.data_type
                )
                
                # Update status on completion
                active_fetches[fetch_id]['status'] = 'completed'
                active_fetches[fetch_id]['completed_at'] = datetime.utcnow().isoformat()
                logger.info(f"Fetch {fetch_id} completed successfully")
                
            except Exception as e:
                logger.error(f"Fetch {fetch_id} failed: {e}")
                active_fetches[fetch_id]['status'] = 'failed'
                active_fetches[fetch_id]['error'] = str(e)
                active_fetches[fetch_id]['failed_at'] = datetime.utcnow().isoformat()
        
        # Start the background thread
        fetch_thread = threading.Thread(target=run_fetch, daemon=True)
        fetch_thread.start()
        
        # Return immediate response
        response = FetchResponse(
            success=True,
            message=f"Historical data fetch started successfully with ID: {fetch_id}",
            request_summary=request_summary
        )
        return response.to_dict(), 202  # 202 Accepted for async operation
        
    except Exception as e:
        logger.error(f"Error starting fetch: {e}")
        return create_error_response(f"Failed to start fetch: {str(e)}", 500)


@app.route('/api/fetch/<fetch_id>/status', methods=['GET'])
def get_fetch_status(fetch_id):
    """Get status of a specific fetch operation."""
    if fetch_id not in active_fetches:
        return create_error_response(f"Fetch ID {fetch_id} not found", 404)
    
    fetch_info = active_fetches[fetch_id]
    return create_success_response(f"Fetch {fetch_id} status", fetch_info)


@app.route('/api/fetch/active', methods=['GET'])
def get_active_fetches():
    """Get list of all active fetch operations."""
    return create_success_response(f"Found {len(active_fetches)} fetch operations", {
        'fetches': active_fetches,
        'count': len(active_fetches)
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return create_error_response("Endpoint not found", 404)


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return create_error_response("Internal server error", 500)


if __name__ == '__main__':
    logger.info("Starting Historical Data Fetcher API...")
    logger.info("Available endpoints:")
    logger.info("  POST /api/fetch - Start a historical data fetch")
    logger.info("  GET /api/symbols - Get available trading symbols")
    logger.info("  GET /api/symbols/perp-tradingview - Convert symbols to perpetual futures format")
    logger.info("  GET /api/intervals - Get supported timeframes")
    logger.info("  GET /api/health - Health check")
    logger.info("  GET /api/fetch/<id>/status - Get fetch status")
    logger.info("  GET /api/fetch/active - Get active fetches")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=False)
