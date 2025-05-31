#!/usr/bin/env python3
"""
Example usage of the Historical Data Fetcher API

This script demonstrates how to use the REST API to start data fetches
and monitor their progress.
"""

import requests
import time
import json
from datetime import datetime, timedelta

# API base URL
API_BASE = "http://localhost:5001/api"

def check_api_health():
    """Check if the API is running and healthy."""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API is healthy")
            print(f"   Database: {data['data']['database']}")
            print(f"   Active fetches: {data['data']['active_fetches']}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

def get_available_symbols():
    """Get list of available trading symbols."""
    try:
        response = requests.get(f"{API_BASE}/symbols")
        if response.status_code == 200:
            data = response.json()
            symbols = data['data']['symbols']
            print(f"✅ Found {len(symbols)} available symbols")
            print(f"   First 10: {symbols[:10]}")
            return symbols
        else:
            print(f"❌ Failed to get symbols: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting symbols: {e}")
        return []

def get_supported_intervals():
    """Get list of supported timeframes."""
    try:
        response = requests.get(f"{API_BASE}/intervals")
        if response.status_code == 200:
            data = response.json()
            intervals = data['data']['intervals']
            print(f"✅ Supported intervals: {intervals}")
            return intervals
        else:
            print(f"❌ Failed to get intervals: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting intervals: {e}")
        return []

def start_sample_fetch(dry_run=True):
    """Start a sample data fetch."""
    # Calculate date range (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    fetch_request = {
        "symbols": ["BTCUSDT", "ETHUSDT"],
        "intervals": ["1h", "1d"],
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "data_type": "um",
        "dry_run": dry_run
    }
    
    print(f"\n🚀 Starting {'dry run' if dry_run else 'actual'} fetch...")
    print(f"   Request: {json.dumps(fetch_request, indent=2)}")
    
    try:
        response = requests.post(f"{API_BASE}/fetch", json=fetch_request)
        if response.status_code in [200, 202]:
            data = response.json()
            print("✅ Fetch started successfully")
            print(f"   Message: {data['message']}")
            
            if 'request_summary' in data['data']:
                summary = data['data']['request_summary']
                fetch_id = summary.get('fetch_id')
                print(f"   Fetch ID: {fetch_id}")
                return fetch_id
            return None
        else:
            print(f"❌ Failed to start fetch: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error starting fetch: {e}")
        return None

def monitor_fetch(fetch_id, max_wait_seconds=60):
    """Monitor a fetch operation until completion or timeout."""
    if not fetch_id:
        print("❌ No fetch ID provided")
        return
    
    print(f"\n📊 Monitoring fetch {fetch_id}...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        try:
            response = requests.get(f"{API_BASE}/fetch/{fetch_id}/status")
            if response.status_code == 200:
                data = response.json()
                status_info = data['data']
                status = status_info.get('status', 'unknown')
                
                print(f"   Status: {status}")
                
                if status == 'completed':
                    print("✅ Fetch completed successfully!")
                    if 'completed_at' in status_info:
                        print(f"   Completed at: {status_info['completed_at']}")
                    break
                elif status == 'failed':
                    print("❌ Fetch failed!")
                    if 'error' in status_info:
                        print(f"   Error: {status_info['error']}")
                    break
                elif status == 'running':
                    print("   ⏳ Still running...")
                
            else:
                print(f"❌ Failed to get status: {response.status_code}")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error checking status: {e}")
            break
        
        time.sleep(5)  # Wait 5 seconds before checking again
    
    if time.time() - start_time >= max_wait_seconds:
        print(f"⏰ Monitoring timeout after {max_wait_seconds} seconds")

def get_active_fetches():
    """Get list of all active fetch operations."""
    try:
        response = requests.get(f"{API_BASE}/fetch/active")
        if response.status_code == 200:
            data = response.json()
            fetches = data['data']['fetches']
            count = data['data']['count']
            
            print(f"\n📋 Active fetches: {count}")
            for fetch_id, fetch_info in fetches.items():
                status = fetch_info.get('status', 'unknown')
                started_at = fetch_info.get('started_at', 'unknown')
                print(f"   {fetch_id}: {status} (started: {started_at})")
            
            return fetches
        else:
            print(f"❌ Failed to get active fetches: {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting active fetches: {e}")
        return {}

def main():
    """Main example function."""
    print("🔧 Historical Data Fetcher API Example")
    print("=" * 50)
    print("Note: This service is API-only. CLI commands are no longer supported.")
    print("")

    # Check API health
    if not check_api_health():
        print("\n❌ API is not available. Make sure to start it with: python api.py")
        print("The service no longer supports command-line arguments.")
        return
    
    # Get available symbols and intervals
    print("\n📊 Getting API information...")
    symbols = get_available_symbols()
    intervals = get_supported_intervals()
    
    if not symbols or not intervals:
        print("❌ Failed to get basic API information")
        return
    
    # Show active fetches
    get_active_fetches()
    
    # Start a dry run fetch
    print("\n🧪 Testing with dry run...")
    fetch_id = start_sample_fetch(dry_run=True)
    
    if fetch_id:
        monitor_fetch(fetch_id, max_wait_seconds=30)
    
    # Ask user if they want to start a real fetch
    print("\n" + "=" * 50)
    response = input("Do you want to start a real data fetch? (y/N): ")
    
    if response.lower() == 'y':
        print("\n🚀 Starting real fetch...")
        fetch_id = start_sample_fetch(dry_run=False)
        
        if fetch_id:
            print(f"\n✅ Real fetch started with ID: {fetch_id}")
            print("You can monitor it by running:")
            print(f"curl http://localhost:5001/api/fetch/{fetch_id}/status")
    else:
        print("\n👍 Dry run completed. No real data was fetched.")
    
    print("\n🎉 Example completed!")

if __name__ == "__main__":
    main()
