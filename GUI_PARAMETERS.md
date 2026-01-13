# GUI Parameters Summary

This document lists all parameters that the BMS Simulator GUI expects to receive/configure.

## Master Settings (Global Configuration)

These settings apply to all simulation sessions and are configured in the **Configuration** page:

### Battery Pack Model
- **`cell_capacity_ah`** (float, default: 100.0) - Cell capacity in Ampere-hours
- **`num_cells`** (int, default: 16) - Number of cells in the battery pack
- **`temperature_c`** (float, default: 32.0) - Ambient temperature in Celsius

### Communication Settings
- **`protocol`** (string, default: 'mcu') - Communication protocol:
  - `'mcu'` - MCU Protocol
  - `'xbb'` - XBB Protocol  
  - `'legacy'` - Legacy Protocol
- **`uart_port`** (string, optional) - Serial port (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
- **`baudrate`** (int, default: 921600) - UART baud rate
- **`frame_rate_hz`** (float, default: 50.0) - Frame transmission rate in Hz
- **`bidirectional`** (boolean, default: false) - Enable bidirectional communication (receive BMS data)

### AFE Noise Settings
- **`voltage_noise_mv`** (float, default: 2.0) - Voltage measurement noise in millivolts
- **`temp_noise_c`** (float, default: 0.5) - Temperature measurement noise in Celsius
- **`current_noise_ma`** (float, default: 50.0) - Current measurement noise in milliamperes

---

## Session Settings (Per-Simulation Configuration)

These settings are configured per simulation session in the **Simulation Control** page:

### Required Parameters
- **`cell_capacity_ah`** (float) - Must match master settings or be provided
- **`initial_soc_pct`** (float) - Initial State of Charge percentage (0-100)
- **`temperature_c`** (float) - Must match master settings or be provided
- **`current_amp`** (float) - Current in Amperes (positive = discharge, negative = charge)

### Optional Parameters
- **`session_name`** (string) - Name for this simulation session
- **`simulation_mode`** (string) - Simulation mode:
  - `'custom'` - Custom current profile
  - `'charge'` - Charge cycle
  - `'discharge'` - Discharge cycle
- **`duration_sec`** (float, default: 3600.0) - Simulation duration in seconds
- **`target_soc_pct`** (float, optional) - Target SOC for charge/discharge cycles
- **`use_target_soc`** (boolean, default: false) - Use target SOC instead of duration
- **`fault_scenario`** (string, optional) - Path to fault scenario YAML file (relative to project root)
- **`seed`** (int, default: 42) - Random seed for reproducibility

---

## Complete Configuration Object Example

When starting a simulation via `/api/simulation/start`, the complete configuration object should include:

```json
{
  "cell_capacity_ah": 100.0,
  "num_cells": 16,
  "initial_soc_pct": 50.0,
  "temperature_c": 32.0,
  "current_amp": 50.0,
  "duration_sec": 3600.0,
  "frame_rate_hz": 50.0,
  "protocol": "mcu",
  "bidirectional": false,
  "uart_port": "COM3",
  "baudrate": 921600,
  "voltage_noise_mv": 2.0,
  "temp_noise_c": 0.5,
  "current_noise_ma": 50.0,
  "fault_scenario": null,
  "session_name": "Test Session",
  "simulation_mode": "custom",
  "use_target_soc": false,
  "target_soc_pct": null,
  "seed": 42
}
```

---

## Parameters Used by `uart_bidirectional.py`

When bidirectional communication is enabled, the `BidirectionalUART` class receives these parameters:

### Initialization Parameters
- **`port`** (string) - Serial port
- **`baudrate`** (int, default: 921600) - Baud rate
- **`tx_rate_hz`** (float, default: 50.0) - Transmission rate
- **`rx_timeout`** (float, default: 1.0) - Receive timeout in seconds
- **`verbose`** (boolean, default: false) - Enable verbose logging

### Data Sent (AFE Measurement Frame)
The `send_frame()` or `send_and_receive()` method expects:
- **`timestamp_ms`** (int) - Timestamp in milliseconds
- **`vcell_mv`** (numpy array[16]) - Cell voltages in millivolts (uint16)
- **`tcell_cc`** (numpy array[16]) - Cell temperatures in centi-°C (int16)
- **`pack_current_ma`** (int) - Pack current in milliamperes
- **`pack_voltage_mv`** (int) - Pack voltage in millivolts
- **`status_flags`** (int) - Status flags (uint32)

### Data Received (BMS Application Frame) - FROM BMS MCU TO PC
**These parameters are sent FROM the BMS MCU board TO the PC** via the `BMS_APP_FRAME` message.

The `receive_frame()` method returns a dictionary with:
- **`timestamp_ms`** (int, uint32) - Timestamp in milliseconds
- **`mosfet_status`** (int, uint16) - MOSFET status flags:
  - Bit 0: `MOSFET_CHARGE_ENABLED` (0x0001)
  - Bit 1: `MOSFET_DISCHARGE_ENABLED` (0x0002)
  - Bit 2: `MOSFET_CHARGE_OPEN` (0x0004)
  - Bit 3: `MOSFET_DISCHARGE_OPEN` (0x0008)
- **`protection_flags`** (int, uint16) - Protection status flags:
  - Bit 0: `PROT_OVERVOLTAGE` (0x0001)
  - Bit 1: `PROT_UNDERVOLTAGE` (0x0002)
  - Bit 2: `PROT_OVERCURRENT_CHARGE` (0x0004)
  - Bit 3: `PROT_OVERCURRENT_DISCHARGE` (0x0008)
  - Bit 4: `PROT_OVERTEMPERATURE` (0x0010)
  - Bit 5: `PROT_UNDERTEMPERATURE` (0x0020)
  - Bit 6: `PROT_SHORT_CIRCUIT` (0x0040)
  - Bit 7: `PROT_CELL_IMBALANCE` (0x0080)
- **`bms_current_ma`** (int, int32) - BMS measured current in milliamperes
- **`bms_voltage_mv`** (int, uint32) - BMS measured voltage in millivolts
- **`balancing_status`** (numpy array[16], uint16) - Per-cell balancing status (16 cells)
- **`fault_codes`** (numpy array[8], uint8) - Fault codes array (8 bytes)
- **`bms_state_flags`** (int, uint32) - BMS state flags
- **`sequence`** (int, uint16) - Frame sequence number

**Convenience fields** (automatically computed):
- **`mosfet_charge`** (bool) - True if charge MOSFET is enabled
- **`mosfet_discharge`** (bool) - True if discharge MOSFET is enabled
- **`protection_active`** (bool) - True if any protection flag is set

**Frame Format (BMS_APP_FRAME):**
```
[SOF: 0xA5] [MSG_ID: 0x02] [LENGTH: 2 bytes] [SEQUENCE: 2 bytes] 
[PAYLOAD: 56 bytes] 
[CRC16: 2 bytes] [EOF: 0xAA]
```

**Payload Structure (56 bytes, little-endian):**
- `timestamp_ms`: 4 bytes (uint32)
- `mosfet_status`: 2 bytes (uint16)
- `protection_flags`: 2 bytes (uint16)
- `bms_current_ma`: 4 bytes (int32)
- `bms_voltage_mv`: 4 bytes (uint32)
- `balancing_status[16]`: 32 bytes (16 × uint16)
- `fault_codes[8]`: 8 bytes (8 × uint8)
- `bms_state_flags`: 4 bytes (uint32)

---

## API Endpoints

### Configuration
- `GET /api/config/default` - Get default configuration
- `GET /api/config/master` - Get master settings
- `POST /api/config/master` - Save master settings

### Simulation Control
- `POST /api/simulation/start` - Start simulation (requires full config object)
- `POST /api/simulation/stop` - Stop simulation
- `POST /api/simulation/pause` - Pause simulation
- `POST /api/simulation/resume` - Resume simulation
- `GET /api/simulation/status` - Get simulation status

### Fault Scenarios
- `GET /api/fault-scenarios` - List available fault scenarios
- `GET /api/fault-scenarios/<name>` - Get specific fault scenario

---

## Notes

1. **Required Fields Validation**: The API validates these required fields:
   - `cell_capacity_ah`
   - `initial_soc_pct`
   - `temperature_c`
   - `current_amp`

2. **Numeric Conversion**: The backend automatically converts string values to numbers for numeric fields.

3. **Master vs Session Settings**: Master settings are global defaults, while session settings are per-simulation. When starting a simulation, both are merged (session settings override master settings).

4. **Bidirectional Communication**: When `bidirectional: true`, the system uses `BidirectionalUART` which can both send AFE frames and receive BMS frames.
