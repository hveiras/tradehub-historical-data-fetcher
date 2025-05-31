# Migration Guide: CLI to API-Only Service

This document explains the changes made to convert the Historical Data Fetcher from a CLI-based tool to an API-only service.

## What Changed

### ❌ Removed: Command-Line Interface
The service no longer accepts command-line arguments. Running `python app.py` with any arguments will show an informational message directing users to the API.

**Before (CLI):**
```bash
python app.py --symbols BTCUSDT ETHUSDT --intervals 1m 5m --start-date 2023-01-01
```

**After (API-only):**
```bash
# Start the API server
python api.py

# Use API endpoints
curl -X POST http://localhost:5000/api/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "intervals": ["1m", "5m"],
    "start_date": "2023-01-01"
  }'
```

### ✅ Added: REST API Interface
All functionality is now available through REST API endpoints:

- **POST /api/fetch** - Start historical data fetch
- **GET /api/symbols** - Get available symbols
- **GET /api/intervals** - Get supported timeframes
- **GET /api/health** - Health check
- **GET /api/fetch/{id}/status** - Get fetch status
- **GET /api/fetch/active** - Get active fetches

## File Changes

### Modified Files

1. **`app.py`**
   - Removed all CLI argument parsing
   - Removed main() function with argparse
   - Added informational message for API-only usage
   - Kept utility functions (validate_symbols, validate_intervals, etc.) for API use

2. **`README.md`**
   - Removed CLI usage examples
   - Added comprehensive API documentation
   - Updated Docker instructions
   - Marked CLI service as deprecated

3. **`Dockerfile`**
   - Changed default command from `app.py --help` to `api.py`
   - Updated comments to reflect API-only nature

4. **`docker-compose.yml`**
   - Updated CLI service with deprecation notice
   - CLI service now shows API-only message

### New Files

1. **`api.py`** - Main Flask application
2. **`api_models.py`** - Request/response models and validation
3. **`api_example.py`** - Example usage script
4. **`test_api.py`** - Test suite for API models
5. **`test_app_message.py`** - Test for app.py message

## Parameter Mapping

All CLI parameters are supported in the API with the same names:

| CLI Parameter | API Parameter | Type | Description |
|---------------|---------------|------|-------------|
| `--symbols` | `symbols` | array | List of trading symbols |
| `--all-symbols` | `all_symbols` | boolean | Fetch all symbols |
| `--intervals` | `intervals` | array | Timeframes (1m, 5m, 1h, 1d) |
| `--start-date` | `start_date` | string | Start date (YYYY-MM-DD) |
| `--end-date` | `end_date` | string | End date (YYYY-MM-DD) |
| `--data-type` | `data_type` | string | um/cm for USD-M/COIN-M |
| `--cache-dir` | `cache_dir` | string | Cache directory |
| `--dry-run` | `dry_run` | boolean | Preview mode |

## Migration Steps

### For Users

1. **Stop using CLI commands**
   ```bash
   # This no longer works:
   python app.py --symbols BTCUSDT --intervals 1m
   ```

2. **Start the API server**
   ```bash
   python api.py
   ```

3. **Use API endpoints**
   ```bash
   curl -X POST http://localhost:5000/api/fetch \
     -H "Content-Type: application/json" \
     -d '{"symbols": ["BTCUSDT"], "intervals": ["1m"]}'
   ```

### For Docker Users

1. **Update docker-compose usage**
   ```bash
   # Start API service (default)
   docker-compose up -d
   
   # CLI service is deprecated but still available for backward compatibility
   docker-compose --profile cli up historical-data-cli
   ```

2. **API will be available at http://localhost:5000**

### For Developers

1. **Import utility functions from app.py**
   ```python
   from app import validate_symbols, validate_intervals, initialize_rate_limiter
   ```

2. **Use API models for validation**
   ```python
   from api_models import FetchRequest
   
   request = FetchRequest(data)
   is_valid, error = request.validate()
   ```

## Benefits of API-Only Approach

1. **Better Integration** - Easy to integrate with web applications, automation tools
2. **Async Operations** - Fetch operations run in background with status tracking
3. **Standardized Responses** - Consistent JSON responses with error handling
4. **Scalability** - Can handle multiple concurrent requests
5. **Monitoring** - Health checks and operation status endpoints
6. **CORS Support** - Ready for web frontend integration

## Backward Compatibility

- The CLI service in Docker Compose is kept but shows a deprecation message
- All validation logic and core functionality remains the same
- Database schema and data format unchanged
- Environment variables and configuration unchanged

## Testing

Use the provided test scripts to verify the migration:

```bash
# Test API models
python test_api.py

# Test app.py message
python test_app_message.py

# Test API functionality
python api_example.py
```

## Support

For questions about the migration or API usage, refer to:
- `README.md` - Complete API documentation
- `api_example.py` - Working examples
- API endpoints at `/api/health` for service status
