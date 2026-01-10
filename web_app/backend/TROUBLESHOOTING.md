# Troubleshooting: "Request failed with status code 500" on Start Simulation

## Quick Diagnosis Steps

### 1. Check the Log File
The error should be logged to: `web_app/backend/logs/runtime_errors.log`

Run this command to see recent errors:
```bash
cd web_app/backend
python check_error.py
```

Or check the log file directly:
```bash
# Windows PowerShell
Get-Content logs\runtime_errors.log -Tail 50

# Linux/Mac
tail -n 50 logs/runtime_errors.log
```

### 2. Check Backend Console
Look at the terminal/console where the backend server is running. You should see:
- `[API] Starting simulation with config keys: ...`
- `[API] Simulation start result: success=...`
- `[ERROR] Failed to start simulation: ...` (if error occurs)

### 3. Common Issues and Fixes

#### Issue: Missing Required Config Fields
**Error**: "Missing required fields: ..."

**Fix**: Ensure the frontend sends all required fields:
- `cell_capacity_ah`
- `initial_soc_pct`
- `temperature_c`
- `current_amp`

#### Issue: Simulation Modules Not Available
**Error**: "Simulation modules not available"

**Fix**: Install missing dependencies:
```bash
pip install pyserial pyyaml numpy
```

#### Issue: Fault Scenario Path Not Found
**Error**: "Fault scenario file not found"

**Fix**: 
- Check that the fault scenario path is correct
- Ensure the scenario file exists in `scenarios/deterministic/`
- If no fault scenario is needed, leave it empty (not a path)

#### Issue: Database Error
**Error**: Database-related errors

**Fix**: 
- Check that `bms_data.db` can be created in `web_app/backend/`
- Ensure write permissions in the backend directory

#### Issue: UART Port Error
**Error**: UART-related errors

**Fix**: 
- If UART is not needed, leave `uart_port` empty in config
- If UART is needed, ensure the port exists and is available

### 4. Enable Detailed Logging

The logger is already enabled. Check:
1. Log file exists: `web_app/backend/logs/runtime_errors.log`
2. Backend console shows error messages
3. API response includes error details

### 5. Test with Minimal Config

Try starting simulation with minimal required fields:
```json
{
  "cell_capacity_ah": 100.0,
  "initial_soc_pct": 50.0,
  "temperature_c": 32.0,
  "current_amp": 50.0,
  "duration_sec": 10.0,
  "frame_rate_hz": 50.0,
  "simulation_mode": "custom"
}
```

### 6. Check API Response

The error response should include details:
```json
{
  "success": false,
  "error": "Detailed error message here"
}
```

Check the browser's Network tab to see the full error response.

## Next Steps

1. **Check the log file** - This will show the exact error with full traceback
2. **Check backend console** - Look for error messages when clicking "Start Simulation"
3. **Share the error message** - The log file will contain the exact error that needs to be fixed
