# BMS Data Storage and Analysis Module

## Overview

This module implements SQLite-based storage for BMS data received via bidirectional UART communication. All BMS response frames are automatically stored during simulation runs and can be analyzed through the web interface.

## Features

### 1. Automatic Data Capture
- **Bidirectional UART Integration**: When bidirectional communication is enabled, all BMS response frames are automatically captured
- **Session Management**: Each simulation run creates a database session with metadata
- **Thread-Safe Storage**: Database operations are thread-safe for concurrent access

### 2. Database Schema

#### `bms_frames` Table
Stores individual BMS response frames:
- `timestamp_ms`: Frame timestamp in milliseconds
- `mosfet_status`: MOSFET status flags
- `protection_flags`: Protection event flags
- `bms_current_ma`: BMS measured current (mA)
- `bms_voltage_mv`: BMS measured voltage (mV)
- `balancing_status`: Per-cell balancing status (JSON)
- `fault_codes`: Fault codes array (JSON)
- `mosfet_charge`: Charge MOSFET state (boolean)
- `mosfet_discharge`: Discharge MOSFET state (boolean)
- `protection_active`: Protection active flag (boolean)
- `session_id`: Foreign key to simulation session

#### `simulation_sessions` Table
Stores simulation session metadata:
- `session_name`: User-defined session name
- `start_time`: Session start timestamp
- `end_time`: Session end timestamp
- `config`: Simulation configuration (JSON)
- `frame_count`: Total number of frames
- `status`: Session status (running/completed)

### 3. API Endpoints

#### List Sessions
```
GET /api/sessions?limit=50
```
Returns list of all simulation sessions.

#### Get Session Details
```
GET /api/sessions/<session_id>
```
Returns detailed information about a specific session.

#### Get Session Frames
```
GET /api/sessions/<session_id>/frames?start_time_ms=<ts>&end_time_ms=<ts>&limit=1000
```
Returns BMS frames for a session with optional time filtering.

#### Get Session Statistics
```
GET /api/sessions/<session_id>/statistics
```
Returns statistical analysis for a session:
- Total frames
- Average current and voltage
- Protection event count
- MOSFET open events

#### Export Session Data
```
GET /api/sessions/<session_id>/export
```
Exports session data to CSV file for external analysis.

### 4. Usage

#### Enable Bidirectional Communication
In the Configuration module:
1. Set `uart_port` to your serial port (e.g., "COM3")
2. Enable `bidirectional` checkbox
3. Start simulation

#### View Stored Data
1. Navigate to **Analysis** module
2. Select a session from the dropdown
3. View statistics, charts, and frame data
4. Export to CSV if needed

### 5. Database Location

The SQLite database file (`bms_data.db`) is created in the `web_app/backend/` directory.

### 6. Analysis Features

The Analysis module provides:
- **Session Statistics**: Overview cards with key metrics
- **Time-Series Charts**: 
  - BMS Current over time
  - BMS Voltage over time
  - Protection events timeline
- **Frame Table**: Detailed view of stored frames
- **CSV Export**: Download data for external analysis

### 7. Example Use Cases

1. **Protection Response Analysis**: Analyze how quickly the BMS responds to fault conditions
2. **MOSFET Behavior**: Track charge/discharge MOSFET open events
3. **Performance Benchmarking**: Compare BMS behavior across multiple test runs
4. **Fault Investigation**: Review stored data to understand protection triggers

## Technical Details

- **Database**: SQLite3 with indexed queries for performance
- **Thread Safety**: All database operations use locks
- **Data Format**: JSON for complex fields (balancing_status, fault_codes)
- **Storage Efficiency**: Only stores BMS response frames, not simulation data
