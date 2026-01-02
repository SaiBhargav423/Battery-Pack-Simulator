# Battery Pack Simulator

A **Software-in-the-Loop (SIL) Battery Management System (BMS) Simulator** for 16-cell series (16S) LiFePO₄ battery packs. This simulator provides realistic battery behavior modeling, AFE (Analog Front End) measurement simulation, and UART communication protocols for testing BMS hardware and software.

**Repository:** [XBattery-Energy/Battery-Pack-Simulator](https://github.com/XBattery-Energy/Battery-Pack-Simulator)

---

## 🚀 Features

### Battery Modeling
- **16S LiFePO₄ Pack Model** with cell-to-cell variations
- **Detailed ECM (Equivalent Circuit Model)** with 2RC network
- **Hysteresis modeling** (separate charge/discharge OCV curves)
- **Temperature effects** on OCV, capacity, and resistance
- **Aging models** (cycle aging + calendar aging)
- **Thermal coupling** between adjacent cells
- **Fault injection** capabilities

### AFE Simulation
- **MC33774 AFE measurement simulation**
- **ADC quantization** (16-bit voltage/current, 12-bit temperature)
- **Gaussian noise injection** (configurable)
- **Per-channel calibration errors** (gain/offset)
- **Fault injection** (open wire, stuck ADC, NTC faults, etc.)
- **Time-based fault scheduling**

### Communication Protocols
- **XBB Protocol** - Custom protocol with CRC8 checksum
- **MCU Protocol** - MCU-compatible format
- **Legacy Protocol** - Backward compatibility
- **UART transmission** with configurable baud rates
- **Thread-safe frame queue** with rate limiting

### Current Profiles
- **Constant current**
- **Pulse (square wave)**
- **YAML-based profiles** with time segments
- **Dynamic profiles** (user-defined functions)

---

## 📋 Requirements

- Python 3.8 or higher
- See `requirements.txt` for dependencies

---

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/XBattery-Energy/Battery-Pack-Simulator.git
cd Battery-Pack-Simulator
```

### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🎯 Quick Start

### Two Main Scripts

The project has two main entry points:

1. **`main.py`** - Full SIL simulator with AFE wrapper and UART communication (for BMS testing)
2. **`run_cell_simulation.py`** - Standalone pack simulation for analysis (saves CSV/plots, no AFE/UART)

### Fault Injection Scripts

For fault injection testing, there are two complementary scripts:

1. **`main.py`** - BMS hardware integration with fault injection (sends data to real BMS via UART)
2. **`run_fault_local_no_bms.py`** - Local fault simulation (no BMS connection, saves data for analysis)

Both scripts use the **same fault injection framework** and support all fault types identically. The only difference is that `main.py` adds UART transmission and AFE wrapper for hardware testing.

### Print-Only Mode (No UART)

Run simulation and print frame data to console:

```bash
python pc_simulator/main.py --current 50.0 --duration 10.0
```

### With UART Transmission

Connect to physical BMS hardware via serial port:

```bash
# Windows
python pc_simulator/main.py --port COM3 --current 50.0 --rate 1.0 --protocol xbb

# Linux/Mac
python pc_simulator/main.py --port /dev/ttyUSB0 --current 50.0 --rate 1.0 --protocol xbb
```

### Continuous Mode

Run infinite simulation (press Ctrl+C to stop):

```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 0
```

### Standalone Pack Simulation (Analysis Mode)

For analysis and testing without AFE/UART:

```bash
python pc_simulator/plant/run_cell_simulation.py --mode discharge --current 1.0 --duration 60
```

This script:
- Runs pack simulation only (no AFE wrapper, no UART)
- Saves CSV data to `pc_simulator/plant/output/`
- Optionally generates plots
- Useful for model validation and analysis

**When to use which script:**
- **`main.py`**: Use for BMS testing, HIL testing, or when you need AFE simulation and UART communication
- **`run_cell_simulation.py`**: Use for analysis, model validation, or when you just need pack simulation data
- **`run_fault_local_no_bms.py`**: Use for fault injection testing and analysis (saves detailed CSV data)
- **`main.py --fault-scenario`**: Use for fault injection with real BMS hardware testing

---

## 📖 Usage

### Command-Line Arguments

```bash
python pc_simulator/main.py [OPTIONS]
```

**Options:**

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--port` | str | None | Serial port (e.g., COM3, /dev/ttyUSB0). If not specified, print-only mode |
| `--baudrate` | int | 921600 | Baud rate for UART communication |
| `--rate` | float | 1.0 | Frame rate in Hz |
| `--duration` | float | 10.0 | Simulation duration in seconds (0 = infinite) |
| `--current` | float | 50.0 | Pack current in Amperes (positive = charge, negative = discharge) |
| `--soc` | float | 50.0 | Initial SOC in percent |
| `--protocol` | str | xbb | Protocol type: `xbb`, `mcu`, or `legacy` |
| `--verbose` | flag | False | Enable verbose logging |
| `--no-print` | flag | False | Disable frame printing |
| `--fault-scenario` | str | None | Path to YAML fault scenario file |
| `--wait-for-fault` | flag | False | Wait for fault to trigger (extends duration if needed) |
| `--extend-after-fault` | float | None | Extend simulation duration by this many seconds after fault triggers |
| `--max-duration` | float | None | Maximum duration when waiting for fault |

### Examples

#### Example 1: Charge Simulation
```bash
python pc_simulator/main.py --current 50.0 --duration 60.0 --soc 20.0
```
- Charge at 50A for 60 seconds
- Start from 20% SOC

#### Example 2: Discharge Simulation
```bash
python pc_simulator/main.py --current -100.0 --duration 120.0 --soc 80.0
```
- Discharge at 100A for 120 seconds
- Start from 80% SOC

#### Example 3: XBB Protocol with UART
```bash
python pc_simulator/main.py --port COM3 --protocol xbb --rate 10.0 --current 50.0
```
- Transmit via COM3 at 10 Hz
- Use XBB protocol
- Charge at 50A

#### Example 4: MCU Protocol
```bash
python pc_simulator/main.py --port COM3 --protocol mcu --rate 1.0 --current 25.0
```
- Use MCU-compatible protocol
- Transmit at 1 Hz

#### Example 5: Standalone Pack Simulation (Analysis Mode)
```bash
python pc_simulator/plant/run_cell_simulation.py --mode discharge --current 1.0 --duration 60
```
- Run pack simulation without AFE/UART
- Saves CSV data to `pc_simulator/plant/output/`
- Useful for analysis and testing

#### Example 6: Fault Injection with main.py (BMS Hardware)
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/Deterministic/internal_short_hard.yaml
```
- Test fault injection with real BMS hardware
- Sends fault-injected data via UART
- All 19 deterministic fault types supported

#### Example 7: Fault Injection Local Testing (No BMS)
```bash
python pc_simulator/run_fault_local_no_bms.py --scenario scenarios/Deterministic/internal_short_hard.yaml --mode discharge --current 50.0 --duration 3600
```
- Test fault injection locally (no hardware needed)
- Saves detailed CSV data for analysis
- Same fault framework as main.py

**Additional options for `run_cell_simulation.py`:**
```bash
# Charge simulation
python pc_simulator/plant/run_cell_simulation.py --mode charge --current 2.0 --duration 120

# Discharge until target SOC
python pc_simulator/plant/run_cell_simulation.py --mode discharge --current 1.0 --target-soc 50

# With plot generation
python pc_simulator/plant/run_cell_simulation.py --mode discharge --current 1.0 --duration 60 --plot

# Custom initial SOC
python pc_simulator/plant/run_cell_simulation.py --mode discharge --current 1.0 --duration 60 --initial-soc 80
```

---

## 📁 Project Structure

```
Battery-Pack-Simulator/
├── pc_simulator/
│   ├── main.py                      # Main integration script (BMS hardware)
│   ├── run_fault_local_no_bms.py    # Local fault injection testing
│   ├── test_all_deterministic_faults.py  # Automated fault test suite
│   ├── validate_fault_data.py       # Fault data validation script
│   ├── afe/
│   │   └── wrapper.py               # AFE measurement simulation
│   ├── communication/
│   │   ├── protocol_xbb.py         # XBB protocol encoder
│   │   ├── protocol_mcu.py         # MCU protocol encoder
│   │   ├── protocol.py              # Legacy protocol
│   │   ├── uart_tx_xbb.py          # XBB UART transmitter
│   │   ├── uart_tx_mcu.py          # MCU UART transmitter
│   │   └── uart_tx.py               # Base UART transmitter
│   ├── fault_injection/
│   │   ├── fault_framework.py      # Main fault injection framework
│   │   ├── fault_scenarios.py       # Scenario loading
│   │   ├── fault_types.py           # Fault type definitions
│   │   ├── fault_models.py          # Fault model implementations
│   │   └── ...                      # Additional fault modules
│   └── plant/
│       ├── cell_model.py            # LiFePO₄ cell ECM model
│       ├── pack_model.py            # 16S pack model
│       ├── current_profile.py       # Current profile generator
│       └── run_cell_simulation.py   # Standalone pack simulation
├── scenarios/
│   ├── Deterministic/               # Deterministic fault scenarios (19 types)
│   ├── Probabilistic/               # Probabilistic fault scenarios
│   ├── charge_discharge_cycle.yaml
│   ├── charge_profile.yaml
│   ├── discharge_profile.yaml
│   ├── mixed_profile.yaml
│   └── pulse_profile.yaml
├── tests_legacy/
│   ├── test_cell_model.py
│   ├── test_pack_model.py
│   ├── test_afe_wrapper.py
│   ├── test_current_profile.py
│   └── test_uart_tx.py
├── requirements.txt
└── README.md
```

---

## 📡 Protocol Details

### XBB Protocol

**Frame Format:**
```
[0xA5] [0x33] [SubIndex: 0x0000] [DataLen: 80] [Data: 80 bytes] [0xB5] [CRC8]
```

**Data Structure (20 int32 values, big-endian, 80 bytes):**
- `pack_current_A`: 4 bytes (int32, milli_A)
- `pack_voltage_V`: 4 bytes (int32, milli_V)
- `temp_cell_C`: 4 bytes (int32, milli_degC)
- `temp_pcb_C`: 4 bytes (int32, milli_degC)
- `cell_1_V` through `cell_16_V`: 64 bytes (16 × int32, milli_V)

**Total Frame Size:** 88 bytes

**CRC8:** Calculated over all bytes from 0xA5 through 0xB5 (excluding CRC8 byte)

### MCU Protocol

MCU-compatible protocol with support for:
- Multiple strings/modules
- Configurable cell/temperature sensor counts
- Legacy format compatibility

---

## ⚙️ Configuration

### Battery Pack Parameters

Default configuration in `pack_model.py`:
- **Cell Capacity:** 100 Ah per cell
- **Initial SOC:** 50%
- **Ambient Temperature:** 25°C
- **Cell Variations:**
  - Capacity mismatch: σ = 0.4%
  - SOC variation: σ = 0.25%
  - Resistance variation: ±2.5%

### AFE Parameters

Default configuration in `afe/wrapper.py`:
- **Voltage Noise:** σ = 2.0 mV
- **Temperature Noise:** σ = 0.5°C
- **Current Noise:** σ = 50 mA
- **Calibration Errors:**
  - Voltage: ±0.1% gain, ±5mV offset
  - Temperature: ±1°C offset
  - Current: ±0.2% gain, ±10mA offset

### Current Profiles

YAML-based profiles in `scenarios/` directory:

```yaml
name: "Charge_Discharge_Cycle"
description: "Complete charge-discharge cycle"
duration_sec: 7200
segments:
  - time_range: [0, 3600]
    current_a: 50
    description: "Charge at 0.5C"
  - time_range: [3600, 7200]
    current_a: -100
    description: "Discharge at 1C"
```

---

## 🛠️ Development

### Code Structure

- **Plant Model:** Battery physics simulation (`pc_simulator/plant/`)
- **AFE Wrapper:** Measurement simulation (`pc_simulator/afe/`)
- **Communication:** UART protocols (`pc_simulator/communication/`)
- **Main Integration:** Orchestrates components (`pc_simulator/main.py`)

### Key Classes

- `LiFePO4Cell`: Cell ECM model with 2RC network
- `BatteryPack16S`: 16-cell series pack model
- `AFEWrapper`: AFE measurement simulation
- `XBBFrameEncoder`: XBB protocol encoder
- `CurrentProfile`: Current profile generator

---

## 📊 Model Details

### Cell Model (LiFePO₄)

**ECM Structure:**
```
OCV(SOC, T, direction) - R0(SOC, T) - [R1 || C1] - [R2 || C2] - Terminal
```

**Parameters:**
- R0: 0.5 mΩ (at 50% SOC, 25°C)
- R1: 1 mΩ, C1: 2000 F (fast transient, τ=2s)
- R2: 0.5 mΩ, C2: 10000 F (slow transient, τ=5s)

**OCV-SOC Characteristics:**
- Flat plateau: ~3.26-3.30V (20-80% SOC)
- Steep ends: 2.86V (0%) to 3.47V (100%)
- Hysteresis: 5-15mV difference between charge/discharge

**Aging Models:**
- **Cycle Aging:** Capacity fade and resistance increase with cycles
- **Calendar Aging:** Arrhenius-based time-dependent capacity fade

---

## 🐛 Troubleshooting

### Serial Port Issues

**Windows:**
- Check COM port in Device Manager
- Ensure port is not in use by another application
- Try different baud rates (115200, 921600)

**Linux/Mac:**
- Check permissions: `sudo chmod 666 /dev/ttyUSB0`
- List available ports: `ls /dev/tty*`
- Check if port exists: `dmesg | grep tty`

### Import Errors

If you encounter import errors:
```bash
# Ensure you're in the project root directory
cd Battery-Pack-Simulator

# Verify Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📝 License

This project is part of XBattery Energy's BMS development tools.

---

## 👥 Contributing

For issues, feature requests, or contributions, please contact the XBattery Energy development team.

**Repository:** [XBattery-Energy/Battery-Pack-Simulator](https://github.com/XBattery-Energy/Battery-Pack-Simulator)

---

## 🔧 Fault Injection

### Overview

The simulator supports comprehensive fault injection for testing BMS fault detection and handling. All fault types are supported in both `main.py` (BMS hardware) and `run_fault_local_no_bms.py` (local testing).

### Supported Fault Types

#### Deterministic Faults (19 Types)

**Location**: `scenarios/Deterministic/`

**Electrical Faults:**
1. **Internal Short Circuit - Hard** (`internal_short_hard.yaml`)
   - Low resistance short (0.1Ω)
   - File: `scenarios/Deterministic/internal_short_hard.yaml`
2. **Internal Short Circuit - Soft** (`internal_short_soft.yaml`)
   - High resistance short (500Ω)
   - File: `scenarios/Deterministic/internal_short_soft.yaml`
3. **External Short Circuit** (`external_short.yaml`)
   - Pack-level short across terminals
   - File: `scenarios/Deterministic/external_short.yaml`
4. **Overcharge** (`overcharge.yaml`)
   - Force charging beyond safe voltage
   - File: `scenarios/Deterministic/overcharge.yaml`
5. **Overdischarge** (`overdischarge.yaml`)
   - Force discharging below safe voltage
   - File: `scenarios/Deterministic/overdischarge.yaml`
6. **Abnormal Self-Discharge** (`self_discharge.yaml`)
   - Constant leakage current
   - File: `scenarios/Deterministic/self_discharge.yaml`
7. **Open Circuit** (`open_circuit.yaml`)
   - High resistance disconnection
   - File: `scenarios/Deterministic/open_circuit.yaml`

**Thermal Faults:**
8. **Overheating** (`overheating.yaml`)
   - Elevated temperature condition
   - File: `scenarios/Deterministic/overheating.yaml`
9. **Thermal Runaway** (`thermal_runaway.yaml`)
   - Exponential temperature escalation
   - File: `scenarios/Deterministic/thermal_runaway.yaml`
10. **Abnormal Temperature** (`abnormal_temperature.yaml`)
    - Temperature offset
    - File: `scenarios/Deterministic/abnormal_temperature.yaml`

**Degradation Faults:**
11. **Capacity Fade** (`capacity_fade.yaml`)
    - Reduced cell capacity
    - File: `scenarios/Deterministic/capacity_fade.yaml`
12. **Resistance Increase** (`resistance_increase.yaml`)
    - Increased internal resistance
    - File: `scenarios/Deterministic/resistance_increase.yaml`
13. **Lithium Plating** (`lithium_plating.yaml`)
    - Capacity loss from plating
    - File: `scenarios/Deterministic/lithium_plating.yaml`
14. **Cell Imbalance** (`cell_imbalance.yaml`)
    - Multiple cells with variations
    - File: `scenarios/Deterministic/cell_imbalance.yaml`
15. **Electrolyte Leakage** (`electrolyte_leakage.yaml`)
    - Electrolyte loss effects
    - File: `scenarios/Deterministic/electrolyte_leakage.yaml`

**Sensor/System Faults:**
16. **Sensor Offset** (`sensor_offset.yaml`)
    - Constant measurement offset
    - File: `scenarios/Deterministic/sensor_offset.yaml`
17. **Sensor Drift** (`sensor_drift.yaml`)
    - Time-dependent measurement drift
    - File: `scenarios/Deterministic/sensor_drift.yaml`
18. **Insulation Fault** (`insulation_fault.yaml`)
    - Reduced pack-to-ground resistance
    - File: `scenarios/Deterministic/insulation_fault.yaml`

**Propagation Faults:**
19. **Thermal Propagation** (`thermal_propagation.yaml`)
    - Correlated thermal effects between cells
    - File: `scenarios/Deterministic/thermal_propagation.yaml`
20. **Cascading Failure** (`cascading_failure.yaml`)
    - Sequential fault propagation
    - File: `scenarios/Deterministic/cascading_failure.yaml`

#### Probabilistic Faults (10 Types)

**Location**: `scenarios/Probabilistic/`

1. **Internal Short - Monte Carlo** (`internal_short_mc.yaml`)
   - Uniform resistance distribution, Weibull timing
   - File: `scenarios/Probabilistic/internal_short_mc.yaml`
2. **Internal Short - Soft Probabilistic** (`internal_short_soft_probabilistic.yaml`)
   - Uniform resistance, Exponential timing
   - File: `scenarios/Probabilistic/internal_short_soft_probabilistic.yaml`
3. **Thermal Runaway - Probabilistic** (`thermal_runaway_probabilistic.yaml`)
   - Uniform escalation factor, Weibull timing
   - File: `scenarios/Probabilistic/thermal_runaway_probabilistic.yaml`
4. **Capacity Fade - Aging** (`capacity_fade_aging.yaml`)
   - Weibull distribution for fade factor
   - File: `scenarios/Probabilistic/capacity_fade_aging.yaml`
5. **Resistance Increase - Normal** (`resistance_increase_normal.yaml`)
   - Normal distribution, Poisson timing
   - File: `scenarios/Probabilistic/resistance_increase_normal.yaml`
6. **External Short - Probabilistic** (`external_short_probabilistic.yaml`)
   - Uniform resistance, variable duration
   - File: `scenarios/Probabilistic/external_short_probabilistic.yaml`
7. **Self-Discharge - Probabilistic** (`self_discharge_probabilistic.yaml`)
   - Normal distribution for leakage current
   - File: `scenarios/Probabilistic/self_discharge_probabilistic.yaml`
8. **Cell Imbalance - Probabilistic** (`cell_imbalance_probabilistic.yaml`)
   - Multiple distributions (uniform + normal)
   - File: `scenarios/Probabilistic/cell_imbalance_probabilistic.yaml`
9. **Multiple Faults - Correlated** (`multiple_faults_correlated.yaml`)
   - Gaussian copula correlation
   - File: `scenarios/Probabilistic/multiple_faults_correlated.yaml`
10. **Combined Degradation** (`combined_degradation.yaml`)
    - Multiple degradation faults with correlation
    - File: `scenarios/Probabilistic/combined_degradation.yaml`

### Configuring and Modifying Faults

#### Fault Scenario File Structure

Fault scenarios are YAML files located in:
- **Deterministic**: `scenarios/Deterministic/`
- **Probabilistic**: `scenarios/Probabilistic/`

**Basic Structure (Deterministic):**
```yaml
name: "Fault Name"
description: "Fault description"
mode: deterministic
seed: 42
faults:
  - type: internal_short_circuit_hard
    target: cell_5  # or "pack" for pack-level faults
    parameters:
      resistance_ohm: 0.1
    timing:
      trigger_soc: 80.0      # SOC-based trigger
      # OR trigger_time_sec: 60.0  # Time-based trigger
      # OR trigger_time_sec: 0.0   # Immediate trigger
      duration_sec: 600      # Optional: fault duration (None = permanent)
```

**Probabilistic Structure:**
```yaml
name: "Fault Name - Probabilistic"
mode: probabilistic
seed: 42
monte_carlo:
  n_runs: 1000
  sampling_strategy: lhs  # lhs, sobol, or random
faults:
  - type: internal_short_circuit_hard
    target: cell_5
    parameters:
      resistance_ohm:
        distribution: uniform  # uniform, normal, or weibull
        min: 0.01
        max: 0.1
    timing:
      trigger_model: weibull  # weibull, poisson, or exponential
      shape: 1.5
      scale: 7200.0
```

#### Where to Modify Faults

1. **Create New Fault Scenario**: Create a new YAML file in `scenarios/Deterministic/` or `scenarios/Probabilistic/`
2. **Modify Existing Fault**: Edit the YAML file directly
3. **Change Fault Parameters**: Modify the `parameters` section in the YAML file
4. **Change Fault Timing**: Modify the `timing` section in the YAML file
5. **Add Multiple Faults**: Add multiple entries to the `faults` list

#### Fault Type Reference

**File**: `pc_simulator/fault_injection/fault_types.py`

Available fault types:
- `internal_short_circuit_hard`
- `internal_short_circuit_soft`
- `external_short_circuit`
- `overcharge`
- `overdischarge`
- `abnormal_self_discharge`
- `open_circuit`
- `overheating`
- `thermal_runaway`
- `abnormal_temperature`
- `capacity_fade`
- `resistance_increase`
- `lithium_plating`
- `cell_imbalance`
- `electrolyte_leakage`
- `sensor_offset`
- `sensor_drift`
- `insulation_fault`
- `thermal_propagation`
- `cascading_failure`

#### Fault Implementation Details

**Fault Models**: `pc_simulator/fault_injection/fault_models.py`
- Contains implementation functions for each fault type
- Modify these functions to change fault behavior

**Fault Framework**: `pc_simulator/fault_injection/fault_framework.py`
- Core fault injection logic
- Fault state management
- Timing and triggering

**Fault Scenarios**: `pc_simulator/fault_injection/fault_scenarios.py`
- YAML loading and parsing
- Fault injector creation from scenarios

### Usage Examples

#### Running Fault Cases with main.py

**main.py** is the primary script for BMS hardware testing with fault injection. It sends fault-injected data to real BMS hardware via UART.

**Basic Syntax:**
```bash
python pc_simulator/main.py \
  --fault-scenario <path_to_yaml> \
  [--port COM3] \
  [--current 50.0] \
  [--duration 3600] \
  [--soc 50.0] \
  [--protocol xbb] \
  [--rate 1.0]
```

**Deterministic Fault Examples:**

1. **Internal Short Circuit (with UART to BMS):**
```bash
python pc_simulator/main.py \
  --port COM3 \
  --current 50.0 \
  --duration 3600 \
  --fault-scenario scenarios/Deterministic/internal_short_hard.yaml \
  --protocol xbb \
  --rate 1.0
```

2. **Thermal Runaway (Print-Only Mode, No Hardware):**
```bash
python pc_simulator/main.py \
  --current 50.0 \
  --duration 600 \
  --fault-scenario scenarios/Deterministic/thermal_runaway.yaml \
  --no-print
```

3. **Overcharge Fault (with UART):**
```bash
python pc_simulator/main.py \
  --port COM3 \
  --current 50.0 \
  --duration 3600 \
  --soc 50.0 \
  --fault-scenario scenarios/Deterministic/overcharge.yaml \
  --protocol xbb \
  --rate 1.0
```

4. **External Short Circuit:**
```bash
python pc_simulator/main.py \
  --port COM3 \
  --current 50.0 \
  --duration 3600 \
  --fault-scenario scenarios/Deterministic/external_short.yaml \
  --protocol mcu \
  --rate 10.0
```

5. **Wait for Fault and Extend Observation:**
```bash
python pc_simulator/main.py \
  --port COM3 \
  --current 50.0 \
  --duration 3600 \
  --fault-scenario scenarios/Deterministic/internal_short_hard.yaml \
  --wait-for-fault \
  --extend-after-fault 600 \
  --max-duration 7200 \
  --protocol xbb \
  --rate 1.0
```

**Probabilistic Fault Examples:**

6. **Probabilistic Internal Short (Single Run):**
```bash
python pc_simulator/main.py \
  --port COM3 \
  --current 50.0 \
  --duration 3600 \
  --fault-scenario scenarios/Probabilistic/internal_short_mc.yaml \
  --wait-for-fault \
  --extend-after-fault 600 \
  --max-duration 7200 \
  --protocol xbb \
  --rate 1.0
```

7. **Monte Carlo Ensemble (Multiple Runs):**
```bash
python pc_simulator/main.py \
  --port COM3 \
  --current 50.0 \
  --duration 3600 \
  --fault-scenario scenarios/Probabilistic/internal_short_mc.yaml \
  --monte-carlo \
  --n-runs 100 \
  --sampling-strategy lhs \
  --protocol xbb \
  --rate 1.0
```

**Command-Line Arguments for Fault Injection:**

| Argument | Description | Example |
|----------|-------------|---------|
| `--fault-scenario` | Path to YAML fault scenario file | `scenarios/Deterministic/internal_short_hard.yaml` |
| `--wait-for-fault` | Wait for fault to trigger (extends duration) | Flag |
| `--extend-after-fault` | Extend simulation by N seconds after fault | `--extend-after-fault 600` |
| `--max-duration` | Maximum duration when waiting for fault | `--max-duration 7200` |
| `--monte-carlo` | Enable Monte Carlo ensemble runs | Flag |
| `--n-runs` | Number of MC runs | `--n-runs 1000` |
| `--sampling-strategy` | MC sampling: `lhs`, `sobol`, or `random` | `--sampling-strategy lhs` |
| `--statistical-analysis` | Enable statistical analysis for MC | Flag |
| `--bayesian` | Enable Bayesian inference | Flag |

**Standard Arguments (also used with faults):**

| Argument | Description | Default |
|----------|-------------|---------|
| `--port` | Serial port (COM3, /dev/ttyUSB0) | None (print-only) |
| `--current` | Pack current in Amperes | 50.0 |
| `--duration` | Simulation duration in seconds | 10.0 |
| `--soc` | Initial SOC in percent | 50.0 |
| `--protocol` | Protocol: `xbb`, `mcu`, or `legacy` | `xbb` |
| `--rate` | Frame rate in Hz | 1.0 |
| `--no-print` | Disable frame printing | False |

**Notes:**
- If `--port` is not specified, `main.py` runs in print-only mode (no hardware needed)
- All deterministic and probabilistic fault types work with `main.py`
- Fault data is sent to BMS hardware via UART in real-time
- Use `--wait-for-fault` for probabilistic faults to ensure fault triggers

#### Running Fault Cases with run_fault_local_no_bms.py

**run_fault_local_no_bms.py** is for local testing and analysis (saves CSV data, no UART):
```bash
# Run single fault simulation
python pc_simulator/run_fault_local_no_bms.py \
  --scenario scenarios/Deterministic/internal_short_hard.yaml \
  --mode discharge \
  --current 50.0 \
  --duration 3600 \
  --output-dir output_test

# Test all deterministic faults
python pc_simulator/test_all_deterministic_faults.py
```

#### Probabilistic Faults (Monte Carlo)

**Single Run with Probabilistic Timing:**
```bash
python pc_simulator/run_fault_local_no_bms.py \
  --scenario scenarios/Probabilistic/internal_short_mc.yaml \
  --mode discharge \
  --current 50.0 \
  --duration 3600 \
  --wait-for-fault \
  --extend-after-fault 600 \
  --max-duration 7200
```

**Monte Carlo Ensemble (Statistical Analysis):**
```bash
# Run 1000 simulations with statistical analysis
python pc_simulator/run_fault_local_no_bms.py \
  --scenario scenarios/Probabilistic/internal_short_mc.yaml \
  --monte-carlo \
  --n-runs 1000 \
  --sampling-strategy lhs \
  --statistical-analysis \
  --mode discharge \
  --current 50.0 \
  --duration 3600 \
  --output-dir output_mc_analysis
```

**Outputs from Monte Carlo:**
- `ensemble_results.csv` - Results from all runs
- `statistics_summary.csv` - Mean, std, percentiles, confidence intervals
- `soc_distribution.png` - Distribution plots
- `voltage_distribution.png` - Distribution plots

### Fault Injection Compatibility

✅ **main.py and run_fault_local_no_bms.py are fully compatible**

Both scripts use the **identical fault injection framework**:
- Same fault loading: `load_scenario()` and `create_fault_injector_from_scenario()`
- Same fault application: `fault_injector.update()`, `apply_to_pack()`, `apply_to_cell()`
- Same cell model: `BatteryPack16S`
- All 19 deterministic fault types work identically in both scripts

**Differences:**
- `main.py`: Adds UART transmission and AFE wrapper for hardware testing
- `run_fault_local_no_bms.py`: Saves detailed CSV data for analysis

### Fault Timing Options

Faults can be triggered in three ways:
1. **Time-based**: Trigger at specific simulation time
2. **SOC-based**: Trigger when pack SOC reaches threshold
3. **Immediate**: Active from simulation start

Additional options:
- `--wait-for-fault`: Wait for fault to trigger (extends duration if needed)
- `--extend-after-fault`: Extend simulation after fault triggers
- `--max-duration`: Maximum duration when waiting for fault

### Pack and Cell Model Configuration

#### Pack Model Configuration

**File**: `pc_simulator/plant/pack_model.py`  
**Class**: `BatteryPack16S`

**Configurable Parameters** (in `__init__` method):

```python
BatteryPack16S(
    cell_capacity_ah=100.0,              # Nominal capacity per cell (Ah)
    initial_soc_pct=50.0,                 # Initial pack SOC (%)
    ambient_temp_c=25.0,                  # Ambient temperature (°C)
    capacity_variation_sigma=0.4,         # Capacity mismatch std dev (%)
    soc_variation_sigma=0.25,              # Initial SOC variation std dev (%)
    resistance_variation=0.025,           # Resistance variation range (±fraction)
    thermal_coupling_coeff=0.1,           # Thermal coupling coefficient (0-1)
    soc_calculation_mode='minimum',       # 'average' or 'minimum' for pack SOC
    seed=42                                # Random seed for reproducibility
)
```

**Where to Modify**:
- **Pack Parameters**: Edit `BatteryPack16S.__init__()` in `pc_simulator/plant/pack_model.py` (lines 37-48)
- **Cell Variations**: Modify variation generation logic (lines 72-91)
- **Thermal Coupling**: Edit `_apply_thermal_coupling()` method (lines 167+)
- **Pack SOC Calculation**: Modify `get_pack_soc()` method

**Default Values** (tuned to match real data):
- Capacity variation: σ = 0.4% (real packs show <1%)
- SOC variation: σ = 0.25% (real balanced packs have <0.5%)
- Resistance variation: ±2.5% (real data shows low variation)

#### Cell Model Configuration

**File**: `pc_simulator/plant/cell_model.py`  
**Class**: `LiFePO4Cell`

**Configurable Parameters** (class attributes):

```python
# ECM Parameters (lines 253-261)
R1 = 1e-3          # Fast transient resistance (1 mΩ)
C1 = 2000.0        # Fast transient capacitance (2000 F, τ1 = 2s)
R2 = 0.5e-3        # Slow transient resistance (0.5 mΩ)
C2 = 10000.0       # Slow transient capacitance (10000 F, τ2 = 5s)

# Temperature Coefficients (lines 263-265)
OCV_TEMP_COEFF = -0.5e-3      # OCV temperature coefficient (-0.5 mV/°C)
CAPACITY_TEMP_COEFF = 0.005   # Capacity temperature coefficient (+0.5% per °C)

# Aging Parameters (lines 267-276)
FADE_RATE = 0.0001             # Capacity fade rate per cycle
RESISTANCE_INCREASE_RATE = 0.001  # Resistance increase rate per cycle
CALENDAR_AGING_ACTIVATION_ENERGY = 30000.0  # J/mol
CALENDAR_AGING_BASE_RATE = 1.0e-9  # per hour at 25°C, 50% SOC

# Thermal Parameters (lines 279-287)
THERMAL_MASS = 3500.0          # Thermal mass (J/°C)
THERMAL_RESISTANCE = 0.5       # Thermal resistance to ambient (K/W)
CELL_SURFACE_AREA = 0.15       # m²
CONVECTION_COEFFICIENT = 10.0   # W/(m²·K)
EMISSIVITY = 0.9               # Surface emissivity
```

**Initialization Parameters** (in `__init__` method, lines 289-297):

```python
LiFePO4Cell(
    capacity_ah=100.0,          # Nominal capacity (Ah)
    initial_soc=0.5,            # Initial SOC (0.0 to 1.0)
    temperature_c=25.0,         # Initial temperature (°C)
    cycles=0,                   # Number of charge/discharge cycles
    ambient_temp_c=25.0,        # Ambient temperature (°C)
    resistance_multiplier=1.0   # Base resistance multiplier
)
```

**Where to Modify**:
- **ECM Parameters**: Edit class attributes (lines 253-261) for R1, C1, R2, C2
- **OCV Tables**: Modify `_OCV_SOC_TABLE_CHARGE` and `_OCV_SOC_TABLE_DISCHARGE` (lines 35-251)
- **Internal Resistance**: Modify `get_internal_resistance()` method (lines 455-511)
- **Thermal Model**: Edit thermal parameters (lines 279-287) and `_update_thermal_model()` (lines 513+)
- **Aging Models**: Modify aging parameters (lines 267-276) and `_update_aging()` method
- **Voltage Divider (Internal Short)**: Edit voltage divider calculation in `update()` method (lines 740-816)

**OCV-SOC Relationship**:
- Charge curve: `_OCV_SOC_TABLE_CHARGE` (lines 35-125)
- Discharge curve: `_OCV_SOC_TABLE_DISCHARGE` (lines 127-251)
- Modify these arrays to change OCV characteristics

**Internal Resistance (R0)**:
- Base R0: 0.5 mΩ at 50% SOC (line 491)
- SOC dependence: Multiplier varies from 1.4x (0% SOC) to 0.75x (100% SOC) (lines 484-489)
- Temperature dependence: -0.5% per °C (line 494)
- Modify `get_internal_resistance()` method (lines 455-511) to change R0 behavior

### Documentation

- **Fault Timing Guide (Deterministic)**: `scenarios/Deterministic/FAULT_TIMING_GUIDE.md`
- **Fault Timing Guide (Probabilistic)**: `scenarios/Probabilistic/FAULT_TIMING_GUIDE.md`
- **Probabilistic Faults README**: `scenarios/Probabilistic/README.md`
- **All Fault Commands**: `scenarios/ALL_FAULT_COMMANDS.md`
- **Test Results**: `pc_simulator/output_deterministic_tests/DETERMINISTIC_FAULT_TEST_DOCUMENTATION.md`

---

## 📚 Additional Resources

- **Codebase Analysis:** See `CODEBASE_ANALYSIS.md` for detailed technical analysis
- **Test Files:** See `tests_legacy/` directory for usage examples
- **Scenarios:** See `scenarios/` directory for YAML profile examples
- **Fault Injection:** See `scenarios/Deterministic/` for fault scenario files

---

## 🔗 Related Projects

- XBattery Energy BMS Firmware
- XBattery Energy Hardware-in-the-Loop (HIL) Test System

---

**Last Updated:** 2025-12-31

---

## ✅ Recent Improvements

### Internal Short Circuit Voltage Divider Fix
- Fixed voltage divider calculation for internal short circuits in ECM model
- Improved effective resistance calculation (R0 + structural impedance)
- Now shows realistic 10-30% voltage drops for hard shorts (0.1Ω)
- Enhanced ECM modeling following best practices

### Thermal Propagation Fault Fix
- Fixed missing numpy import in fault scenario loading
- All 19 deterministic fault tests now passing (100% success rate)

### Comprehensive Fault Testing
- Added automated test suite (`test_all_deterministic_faults.py`)
- Added validation script (`validate_fault_data.py`)
- All 19 deterministic fault types tested and documented
- Full compatibility verified between `main.py` and `run_fault_local_no_bms.py`

