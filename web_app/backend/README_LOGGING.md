# Runtime Error Logging and Monitoring

## Overview

The system includes comprehensive runtime error logging and monitoring capabilities to track all errors that occur during server operation.

## Log File Location

All runtime errors are logged to:
```
web_app/backend/logs/runtime_errors.log
```

## Features

### 1. Automatic Error Logging
- All exceptions are automatically caught and logged with full tracebacks
- Context information shows where each error occurred
- Timestamps for all error entries
- Non-blocking: errors in non-critical paths don't stop the simulation

### 2. Log Monitoring

#### Option 1: Watch Script (Recommended)
Run the watch script in a separate terminal to monitor errors in real-time:

```bash
cd web_app/backend
python watch_logs.py
```

This will:
- Display new errors as they occur
- Show error count and file statistics
- Update in real-time (checks every 0.5 seconds)

#### Option 2: API Endpoints
Query log information via REST API:

- **Get Recent Errors**: `GET /api/logs/errors?limit=50`
  - Returns recent error entries from the log file
  - Default limit: 50 entries

- **Get Log Statistics**: `GET /api/logs/stats`
  - Returns log file statistics:
    - Error count
    - File size
    - Last modified time
    - New errors since last check

- **Get New Errors**: `GET /api/logs/new`
  - Returns only new errors since last API call
  - Useful for polling for new errors

#### Option 3: Direct File Access
Monitor the log file directly:

```bash
# Windows PowerShell
Get-Content web_app\backend\logs\runtime_errors.log -Wait -Tail 20

# Linux/Mac
tail -f web_app/backend/logs/runtime_errors.log
```

## Log Format

Each error entry includes:
```
YYYY-MM-DD HH:MM:SS - bms_simulator - ERROR - Exception occurred in [CONTEXT]: ExceptionType: Error message

Full Traceback:
Traceback (most recent call last):
  File "...", line X, in function
    ...
ExceptionType: Error message
```

## Error Contexts

Errors are tagged with context information:
- `API: /api/simulation/start` - API endpoint errors
- `Simulation Loop: Pack Update` - Simulation loop errors
- `SimulationManager: start_simulation` - Manager initialization errors
- `WebSocket: connect` - WebSocket handler errors
- `Flask Error Handler` - Flask framework errors

## Usage Examples

### Monitor Logs in Real-Time
```bash
# Terminal 1: Start backend server
cd web_app/backend
python app.py

# Terminal 2: Watch logs
cd web_app/backend
python watch_logs.py
```

### Query Logs via API
```bash
# Get recent errors
curl http://localhost:5000/api/logs/errors?limit=10

# Get log statistics
curl http://localhost:5000/api/logs/stats

# Get new errors
curl http://localhost:5000/api/logs/new
```

### Check Log File Directly
```bash
# View last 50 lines
tail -n 50 web_app/backend/logs/runtime_errors.log

# Search for specific errors
grep "Simulation Loop" web_app/backend/logs/runtime_errors.log
```

## Integration

The logger is automatically initialized when the backend starts. You'll see:
```
[LOGGER] Runtime error logger initialized
[LOGGER] Log file: <path>
[LOGGER] Logging all runtime errors with full tracebacks
```

All errors are automatically logged - no additional configuration needed.

## Log File Management

- The log file is automatically created when the first error occurs
- The `logs/` directory is created on startup
- Log file grows over time - consider periodic cleanup for long-running servers
- Log file is excluded from git (see `.gitignore`)

## Troubleshooting

If errors aren't being logged:
1. Check that `logs/` directory exists and is writable
2. Verify logger initialization message appears on server start
3. Check file permissions on log file
4. Ensure logger module is imported correctly
