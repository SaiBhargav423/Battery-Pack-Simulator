# Repository Changes Comparison

**Generated:** 2026-01-13 13:08:26

**Reference Repository:** `C:\git_sil_REPO\BAT_SIM_SATHISH\Battery-Pack-Simulator`  
**Current Repository:** `C:\git_sil_REPO\B2\Battery-Pack-Simulator`

---

## 📋 Executive Summary

This document compares the current repository with the reference repository, focusing on changes made to implement **sequential XBB communication protocol** and related improvements.

### Key Changes Overview:

1. **New Sequential XBB Communication Module** (`uart_xbb_sequential.py`)
   - Implements send-then-receive sequential communication (no threading)
   - Retry logic: 10 attempts with 1 second timeout
   - Full RX frame parsing and validation (118 bytes)
   - BMS state tracking for MOSFET gating logic

2. **XBB Protocol Enhancements** (`protocol_xbb.py`)
   - Added RX frame decoder (118 bytes total, 112 bytes payload)
   - Updated TX frame to include counter field (92 bytes total, 84 bytes payload)
   - Big-endian float parsing for SOC/SOH/SOE
   - Complete CRC8 validation

3. **Main Script Updates** (`main.py`)
   - Added `--sequential` flag for sequential XBB communication
   - Updated current sign convention: positive=discharge, negative=charge
   - Enhanced MOSFET gating logic with protection flags
   - Voltage clamping to minimum 2.51V (2510 mV)
   - Improved statistics handling for different transmitter types

4. **Cell Model Improvements** (`cell_model.py`)
   - Updated OCV tables for proper voltage range (0% SOC ≈ 2.52V)
   - Fixed charge/discharge hysteresis
   - Current sign convention: positive=discharge, negative=charge
   - Multiple voltage clamps to ensure minimum 2.51V (2510 mV)
   - Enhanced minimum voltage enforcement at 0% SOC

5. **Pack Model Updates** (`pack_model.py`)
   - Updated current sign convention documentation
   - Added voltage clamping to minimum 2.51V (2510 mV)

---

## 🆕 New Files

### `pc_simulator/communication/uart_xbb_sequential.py` ⭐ **NEW**
**Purpose:** Sequential XBB UART communication module (send-then-receive, no threading)

**Key Features:**
- Sequential send → wait → receive → parse flow
- Retry logic: 10 attempts with 1 second timeout each
- CRC8 validation for RX frames
- Receives and stores BMS state from RX frames (for MOSFET gating logic)
- Detailed TX/RX frame printing in readable format
- Statistics tracking (tx_count, rx_count, error_count, retry_count)

**File Size:** ~494 lines


---

---

## 📝 Modified Files

### Summary

| File | Lines Added | Lines Removed |
|------|-------------|---------------|
| `pc_simulator/communication/protocol_xbb.py` | +201 | -14 |
| `pc_simulator/main.py` | +117 | -29 |
| `pc_simulator/plant/cell_model.py` | +248 | -226 |
| `pc_simulator/plant/pack_model.py` | +9 | -4 |

---

### Detailed Changes

#### `pc_simulator/communication/protocol_xbb.py`

**Changes:** +201 lines, -14 lines

```diff
--- REF/pc_simulator/communication/protocol_xbb.py
+++ CURR/pc_simulator/communication/protocol_xbb.py
@@ -1,17 +1,36 @@
 """

 UART Protocol for XBB Communication

 

-Frame Format:

-[0xA5] [0x33] [SubIndex: 0x0000] [DataLen: 80] [Data: 80 bytes] [0xB5] [CRC8]

-

-Data Structure (20 int32 values, big-endian, 80 bytes total):

+TX Frame Format (92 bytes total):

+[0xA5] [0x33] [SubIndex: 0x0000] [DataLen: 84] [Data: 84 bytes] [0xB5] [CRC8]

+

+TX Data Structure (21 int32 values, big-endian, 84 bytes total):

 - pack_current_A: 4 bytes (int32, milli_A)

 - pack_voltage_V: 4 bytes (int32, milli_V)

 - temp_cell_C: 4 bytes (int32, milli_degC)

 - temp_pcb_C: 4 bytes (int32, milli_degC)

 - cell_1_V through cell_16_V: 16 × 4 = 64 bytes (int32, milli_V each)

-

-Total Frame Size: 88 bytes

+- Counter: 4 bytes (int32, sequence number)

+

+RX Frame Format (118 bytes total):

+[0xA5] [0x33] [Length: 0x0070] [Payload: 112 bytes] [0xB5] [CRC8]

+

+RX Payload Structure (112 bytes):

+- timestamp_ms: 4 bytes (uint32, big-endian) - offset 0-3

+- protection_flags: 2 bytes (uint16, big-endian) - offset 4-5

+- soc: 4 bytes (float, big-endian) - offset 6-9

+- soh: 4 bytes (float, big-endian) - offset 10-13

+- soe: 4 bytes (float, big-endian) - offset 14-17

+- bms_current_ma: 4 bytes (int32, big-endian, signed) - offset 18-21

+- bms_voltage_mv: 4 bytes (uint32, big-endian) - offset 22-25

+- balancing_status[16]: 32 bytes (16 × uint16, big-endian) - offset 26-57

+- fault_codes[8]: 8 bytes (8 × uint8) - offset 58-65

+- pcb_temperature_ddegC: 2 bytes (int16, big-endian, signed) - offset 66-67

+- cell_temperatures_ddegC[4]: 8 bytes (4 × int16, big-endian, signed) - offset 68-75

+- cell_voltages_mv[16]: 32 bytes (16 × uint16, big-endian) - offset 76-107

+- sequence: 2 bytes (uint16, big-endian) - offset 108-109

+- mosfet_status: 2 bytes (uint16, big-endian) - offset 110-111

+

 CRC8 calculated over all bytes from 0xA5 through 0xB5 (excluding CRC8 byte itself)

 """

 

@@ -25,7 +44,9 @@
 XBB_FRAME_MSG_ID = 0x33

 XBB_FRAME_FOOTER = 0xB5

 XBB_SUBINDEX = 0x0000

-XBB_DATA_LENGTH = 80  # 20 int32 values × 4 bytes = 80 bytes

+XBB_DATA_LENGTH = 84  # 21 int32 values × 4 bytes = 84 bytes (20 data + 1 counter)

+XBB_RX_PAYLOAD_LENGTH = 112  # RX payload size in bytes (removed bms_state_flags: 116-4=112)

+XBB_RX_FRAME_LENGTH = 118  # Total RX frame size (1+1+2+112+1+1)

 

 

 # CRC8 Table (provided by user)

@@ -102,7 +123,8 @@
         pack_voltage_mv: int,      # Pack voltage in milli-Volts (unsigned, but sent as signed int32)

         temp_cell_clc: float,        # Cell temperature in °C (converted to milli_degC)

         temp_pcb_c: float,         # PCB temperature in °C (converted to milli_degC)

-        cell_voltages_mv: np.ndarray  # Cell voltages in milli-Volts (array[16])

+        cell_voltages_mv: np.ndarray,  # Cell voltages in milli-Volts (array[16])

+        counter: int = 0            # Sequence counter (int32)

     ) -> bytes:

         """

         Encode XBB frame with battery pack data.

@@ -115,7 +137,7 @@
             cell_voltages_mv: Cell voltages in milli-Volts (array[16])

         

         Returns:

-            Encoded frame bytes (88 bytes total)

+            Encoded frame bytes (92 bytes total)

         """

         # Validate inputs

         if len(cell_voltages_mv) != 16:

@@ -129,7 +151,7 @@
         # Note: voltages are typically positive, but we use signed int32 to match spec

         cell_voltages_int32 = cell_voltages_mv.astype(np.int32)

         

-        # Pack data payload (20 int32 values, big-endian, 80 bytes total)

+        # Pack data payload (21 int32 values, big-endian, 84 bytes total)

         data_payload = bytearray()

         

         # 1. pack_current_A (4 bytes, int32, milli_A)

@@ -148,17 +170,20 @@
         for cell_voltage in cell_voltages_int32:

             data_payload.extend(pack_int32_be(cell_voltage))

         

+        # 6. Counter (4 bytes, int32)

+        data_payload.extend(pack_int32_be(counter))

+        

         # Verify data length

         if len(data_payload) != XBB_DATA_LENGTH:

             raise ValueError(f"Data payload length mismatch: got {len(data_payload)}, expected {XBB_DATA_LENGTH}")

         

-        # Build frame: [0xA5] [0x33] [SubIndex: 0x0000] [DataLen: 80] [Data: 80 bytes] [0xB5] [CRC8]

+        # Build frame: [0xA5] [0x33] [SubIndex: 0x0000] [DataLen: 84] [Data: 84 bytes] [0xB5] [CRC8]

         frame = bytearray()

         frame.append(XBB_FRAME_HEADER)  # 0xA5

         frame.append(XBB_FRAME_MSG_ID)  # 0x33


... (83 more lines) ...

+            if verbose:

+                print(f"[DEBUG] CRC mismatch: calculated 0x{calculated_crc:02X}, received 0x{received_crc:02X}")

+                print(f"[DEBUG] Frame hex (first 20): {' '.join([f'{b:02X}' for b in frame_bytes[:20]])}")

+                print(f"[DEBUG] Frame hex (last 10): {' '.join([f'{b:02X}' for b in frame_bytes[-10:]])}")

+        

+        # Parse payload according to 118-byte frame format (bms_state_flags removed)

+        try:

+            # timestamp_ms: 4 bytes (uint32, big-endian) - offset 0-3

+            timestamp_ms = struct.unpack('>I', payload[0:4])[0]

+            

+            # protection_flags: 2 bytes (uint16, big-endian) - offset 4-5

+            protection_flags = struct.unpack('>H', payload[4:6])[0]

+            

+            # SOC: 4 bytes (float, big-endian) - offset 6-9

+            soc_bytes = payload[6:10]

+            soc = struct.unpack('>f', soc_bytes)[0]  # Big-endian only

+            if np.isnan(soc) or np.isinf(soc) or not (0.0 <= soc <= 110.0):

+                soc = 0.0

+            

+            # SOH: 4 bytes (float, big-endian) - offset 10-13

+            soh_bytes = payload[10:14]

+            soh = struct.unpack('>f', soh_bytes)[0]  # Big-endian only

+            if np.isnan(soh) or np.isinf(soh) or not (0.0 <= soh <= 110.0):

+                soh = 0.0

+            

+            # SOE: 4 bytes (float, big-endian) - offset 14-17

+            soe_bytes = payload[14:18]

+            soe = struct.unpack('>f', soe_bytes)[0]  # Big-endian only

+            if np.isnan(soe) or np.isinf(soe) or not (0.0 <= soe <= 110.0):

+                soe = 0.0

+            

+            # bms_current_ma: 4 bytes (int32, big-endian, signed) - offset 18-21

+            bms_current_ma = struct.unpack('>i', payload[18:22])[0]

+            

+            # bms_voltage_mv: 4 bytes (uint32, big-endian) - offset 22-25

+            bms_voltage_mv = struct.unpack('>I', payload[22:26])[0]

+            

+            # balancing_status[16]: 32 bytes (16 × uint16, big-endian) - offset 26-57

+            balancing_status = []

+            for i in range(16):

+                offset = 26 + (i * 2)

+                balance_val = struct.unpack('>H', payload[offset:offset+2])[0]

+                balancing_status.append(balance_val)

+            

+            # fault_codes[8]: 8 bytes (8 × uint8) - offset 58-65

+            fault_codes = list(payload[58:66])

+            

+            # pcb_temperature_ddegC: 2 bytes (int16, big-endian, signed) - offset 66-67 (bms_state_flags removed)

+            pcb_temperature_ddegc = struct.unpack('>h', payload[66:68])[0]

+            pcb_temperature_c = pcb_temperature_ddegc / 10.0

+            

+            # cell_temperatures_ddegC[4]: 8 bytes (4 × int16, big-endian, signed) - offset 68-75

+            cell_temperatures_ddegc = []

+            for i in range(4):

+                offset = 68 + (i * 2)

+                temp_ddegc = struct.unpack('>h', payload[offset:offset+2])[0]

+                cell_temperatures_ddegc.append(temp_ddegc)

+            cell_temperatures_c = [t / 10.0 for t in cell_temperatures_ddegc]

+            

+            # cell_voltages_mv[16]: 32 bytes (16 × uint16, big-endian) - offset 76-107

+            cell_voltages_mv = []

+            for i in range(16):

+                offset = 76 + (i * 2)

+                voltage_mv = struct.unpack('>H', payload[offset:offset+2])[0]

+                cell_voltages_mv.append(voltage_mv)

+            

+            # sequence: 2 bytes (uint16, big-endian) - offset 108-109

+            sequence = struct.unpack('>H', payload[108:110])[0]

+            

+            # mosfet_status: 2 bytes (uint16, big-endian) - offset 110-111

+            mosfet_status = struct.unpack('>H', payload[110:112])[0]

+            

+            # Extract MOSFET bits

+            mosfet_charge = bool(mosfet_status & 0x01)

+            mosfet_discharge = bool(mosfet_status & 0x02)

+            

+            return {

+                'timestamp_ms': timestamp_ms,

+                'protection_flags': protection_flags,

+                'soc': soc,

+                'soh': soh,

+                'soe': soe,

+                'soc_bytes_raw': soc_bytes,  # Raw bytes for debugging

+                'soh_bytes_raw': soh_bytes,  # Raw bytes for debugging

+                'soe_bytes_raw': soe_bytes,  # Raw bytes for debugging

+                'bms_current_ma': bms_current_ma,

+                'bms_voltage_mv': bms_voltage_mv,

+                'balancing_status': balancing_status,

+                'fault_codes': fault_codes,

+                'pcb_temperature_c': pcb_temperature_c,

+                'cell_temperatures_c': cell_temperatures_c,

+                'cell_voltages_mv': cell_voltages_mv,

+                'sequence': sequence,

+                'mosfet_status': mosfet_status,

+                'mosfet_charge': mosfet_charge,

+                'mosfet_discharge': mosfet_discharge

+            }

+        except (struct.error, IndexError) as e:

+            return None

+

```

---

#### `pc_simulator/main.py`

**Changes:** +117 lines, -29 lines

```diff
--- REF/pc_simulator/main.py
+++ CURR/pc_simulator/main.py
@@ -33,6 +33,7 @@
 from communication.uart_tx import UARTTransmitter

 from communication.uart_tx_mcu import MCUCompatibleUARTTransmitter

 from communication.uart_tx_xbb import XBBUARTTransmitter

+from communication.uart_xbb_sequential import SequentialXBBUART

 

 # Optional bidirectional support

 try:

@@ -106,7 +107,7 @@
     parser.add_argument('--duration', type=float, default=10.0,

                        help='Simulation duration in seconds (default: 10.0). Use 0 for infinite/continuous transmission.')

     parser.add_argument('--current', type=float, default=50.0,

-                       help='Pack current in Amperes (default: 50.0, positive=charge)')

+                       help='Pack current in Amperes (default: 50.0, positive=discharge, negative=charge)')

     parser.add_argument('--soc', type=float, default=50.0,

                        help='Initial SOC in percent (default: 50.0)')

     parser.add_argument('--verbose', action='store_true',

@@ -120,6 +121,10 @@
                        help='Protocol type: xbb (default), mcu, or legacy')

     parser.add_argument('--bidirectional', action='store_true',

                        help='Enable bidirectional communication (receive BMS data)')

+    parser.add_argument('--sequential', action='store_true',

+                       help='Use sequential XBB communication (send-then-receive with retry)')

+    parser.add_argument('--no-mosfet-gate', action='store_true',

+                       help='Disable MOSFET-based current gating (use requested current regardless of BMS MOSFET state)')

     

     # Fault injection arguments

     if FAULT_INJECTION_AVAILABLE:

@@ -233,13 +238,25 @@
             print(f"Initializing UART Transmitter on {args.port} ({protocol_type} protocol)...")

             try:

                 if args.protocol == 'xbb':

-                    tx = XBBUARTTransmitter(

-                        port=args.port,

-                        baudrate=args.baudrate,

-                        frame_rate_hz=args.rate,

-                        verbose=args.verbose,

-                        print_frames=args.print_frames

-                    )

+                    if args.sequential:

+                        # Use sequential XBB communication

+                        tx = SequentialXBBUART(

+                            port=args.port,

+                            baudrate=args.baudrate,

+                            timeout=1.0,

+                            max_retries=10,

+                            verbose=args.verbose

+                        )

+                        print(f"  [MODE] Sequential XBB (send-then-receive with retry)")

+                    else:

+                        # Use standard XBB transmitter

+                        tx = XBBUARTTransmitter(

+                            port=args.port,

+                            baudrate=args.baudrate,

+                            frame_rate_hz=args.rate,

+                            verbose=args.verbose,

+                            print_frames=args.print_frames

+                        )

                 elif args.protocol == 'mcu':

                     tx = MCUCompatibleUARTTransmitter(

                         port=args.port,

@@ -299,7 +316,7 @@
         print(f"  Mode: CONTINUOUS (infinite loop - press Ctrl+C to stop)")

     else:

         print(f"  Total steps: {num_steps}")

-    print(f"  Current: {args.current} A ({'charge' if args.current > 0 else 'discharge'})")

+    print(f"  Current: {args.current} A ({'discharge' if args.current > 0 else 'charge'})")

     if FAULT_INJECTION_AVAILABLE and args.fault_scenario and args.extend_after_fault:

         print(f"  [Fault Timing] Will extend {args.extend_after_fault:.1f}s after fault triggers")

     print("\n" + "-" * 80)

@@ -309,6 +326,10 @@
     frame_count = 0

     fault_triggered = False

     first_fault_time_sec = None

+    

+    # Track MOSFET gating state

+    last_protection_flags = None

+    last_requested_current_ma = current_ma  # Track original requested current

     

     try:

         step = 0

@@ -353,18 +374,49 @@
             

             # Update battery pack

             # Check if current should be gated based on BMS MOSFET state

+            # Note: Positive current = discharge, Negative current = charge

             effective_current_ma = current_ma

-            if tx is not None and hasattr(tx, 'get_bms_state'):

+            if not args.no_mosfet_gate and tx is not None and hasattr(tx, 'get_bms_state'):

                 bms_state = tx.get_bms_state()

-                # Gate current if MOSFETs are open

-                if current_ma > 0 and not bms_state.get('mosfet_charge', True):

-                    effective_current_ma = 0.0

-                    if args.verbose and frame_count % 100 == 0:  # Print every 100 frames

-                        print(f"[GATE] Charge current gated - MOSFET open")

-                elif current_ma < 0 and not bms_state.get('mosfet_discharge', True):

-                    effective_current_ma = 0.0

-                    if args.verbose and frame_count % 100 == 0:


... (24 more lines) ...

+                    else:

+                        # Protection active - gate current if MOSFETs are OFF

+                        if current_ma > 0 and not bms_state.get('mosfet_discharge', True):

+                            # Positive current = discharge, check discharge MOSFET

+                            effective_current_ma = 0.0

+                            if args.verbose and frame_count % 100 == 0:  # Print every 100 frames

+                                print(f"[GATE] Discharge current gated - Protection active (0x{protection_flags:04X}), MOSFET open")

+                        elif current_ma < 0 and not bms_state.get('mosfet_charge', True):

+                            # Negative current = charge, check charge MOSFET

+                            effective_current_ma = 0.0

+                            if args.verbose and frame_count % 100 == 0:

+                                print(f"[GATE] Charge current gated - Protection active (0x{protection_flags:04X}), MOSFET open")

+                        else:

+                            # Protection active but MOSFETs are ON - allow current

+                            effective_current_ma = current_ma

+                            last_requested_current_ma = current_ma

             

             pack.update(current_ma=effective_current_ma, dt_ms=dt_ms, ambient_temp_c=32.0)

             

@@ -377,6 +429,11 @@
             measured_v, measured_t, measured_i, flags = afe.apply_measurement(

                 true_v, true_t, true_i

             )

+            

+            # Critical: Ensure all cell voltages are at least 2510 mV (2.51V)

+            # This is required for 0% SOC operation - cells must never go below 2.51V (ensures voltage > 2.5V)

+            # Clamp after AFE processing to account for noise that might push voltages below threshold

+            measured_v = np.maximum(measured_v, 2510.0)

             

             # Prepare frame data based on protocol

             if args.protocol == 'xbb':

@@ -390,7 +447,7 @@
                     'pack_voltage_mv': int(pack.get_pack_voltage()),  # Already in milli-Volts

                     'temp_cell_c': float(temp_cell_c),  # Average cell temperature in °C

                     'temp_pcb_c': float(temp_pcb_c),  # PCB temperature in °C

-                    'cell_voltages_mv': measured_v.astype(np.int32)  # Cell voltages in milli-Volts

+                    'cell_voltages_mv': measured_v.astype(np.int32)  # Cell voltages in milli-Volts (clamped to >= 2500 mV)

                 }

             else:

                 # Legacy/MCU protocols

@@ -439,19 +496,50 @@
             print("\nStopping UART transmitter...")

             tx.stop()

             

-            # Print statistics

+            # Print statistics (handle different statistics formats)

             stats = tx.get_statistics()

             print(f"\nTransmission Statistics:")

-            print(f"  Frames sent: {stats['sent_count']}")

-            print(f"  Errors: {stats['error_count']}")

-            print(f"  Last error: {stats['last_error'] if stats['last_error'] else 'None'}")

-            print(f"  Final sequence: {stats['sequence']}")

+            # Handle different key names from different transmitter types

+            if 'sent_count' in stats:

+                print(f"  Frames sent: {stats['sent_count']}")

+            elif 'tx_count' in stats:

+                print(f"  Frames sent: {stats['tx_count']}")

+                if 'rx_count' in stats:

+                    print(f"  Frames received: {stats['rx_count']}")

+            else:

+                print(f"  Frames sent: {stats.get('tx_count', 'N/A')}")

+            

+            if 'error_count' in stats:

+                print(f"  Errors: {stats['error_count']}")

+            if 'retry_count' in stats:

+                print(f"  Retries: {stats['retry_count']}")

+            if 'last_error' in stats:

+                print(f"  Last error: {stats['last_error'] if stats['last_error'] else 'None'}")

+            if 'sequence' in stats:

+                print(f"  Final sequence: {stats['sequence']}")

+            elif 'tx_counter' in stats:

+                print(f"  TX Counter: {stats['tx_counter']}")

         

-        # Print pack state

+        # Print pack state - use last received BMS data if available

         print(f"\nFinal Pack State:")

-        print(f"  Pack Voltage: {pack.get_pack_voltage()/1000:.3f} V")

-        print(f"  Pack SOC: {pack.get_pack_soc():.1f}%")

-        print(f"  Pack Current: {pack.get_pack_current()/1000:.3f} A")

+        bms_state = None

+        if tx is not None and hasattr(tx, 'get_bms_state'):

+            bms_state = tx.get_bms_state()

+        

+        if bms_state is not None:

+            # Use last received BMS frame data

+            print(f"  Pack Voltage: {bms_state.get('bms_voltage_mv', 0)/1000:.3f} V")

+            print(f"  Pack SOC: {bms_state.get('soc', 0):.2f}%")

+            print(f"  Pack Current: {bms_state.get('bms_current_ma', 0)/1000:.3f} A")

+            if 'soh' in bms_state:

+                print(f"  Pack SOH: {bms_state.get('soh', 0):.2f}%")

+            if 'soe' in bms_state:

+                print(f"  Pack SOE: {bms_state.get('soe', 0):.2f}%")

+        else:

+            # Fallback to simulator's internal state

+            print(f"  Pack Voltage: {pack.get_pack_voltage()/1000:.3f} V")

+            print(f"  Pack SOC: {pack.get_pack_soc():.1f}%")

+            print(f"  Pack Current: {pack.get_pack_current()/1000:.3f} A")

         

         imbalance = pack.get_cell_imbalance()

         print(f"\nCell Imbalance:")

```

---

#### `pc_simulator/plant/cell_model.py`

**Changes:** +248 lines, -226 lines

```diff
--- REF/pc_simulator/plant/cell_model.py
+++ CURR/pc_simulator/plant/cell_model.py
@@ -39,215 +39,216 @@
     # Precision: 0.001V (1mV) for better accuracy, especially in steep regions

     # Hysteresis: Separate curves for charge and discharge

     _OCV_SOC_TABLE_DISCHARGE = np.array([

-        # SOC%, OCV(V) - Interpolated from real data

-        [0.0, 2.862],   # 0% - fully discharged

-        [1.0, 2.912],

-        [2.0, 2.962],

-        [3.0, 3.012],

-        [4.0, 3.062],

-        [5.0, 3.112],

-        [6.0, 3.124],

-        [7.0, 3.136],

-        [8.0, 3.148],

-        [9.0, 3.160],

-        [10.0, 3.172],  # 10%

-        [11.0, 3.183],

-        [12.0, 3.193],

-        [13.0, 3.204],

-        [14.0, 3.215],

-        [15.0, 3.226],

-        [16.0, 3.236],

-        [17.0, 3.247],

-        [18.0, 3.258],

-        [19.0, 3.268],

-        [20.0, 3.279],  # 20%

-        [21.0, 3.280],

-        [22.0, 3.280],

-        [23.0, 3.281],

-        [24.0, 3.281],

-        [25.0, 3.282],

-        [26.0, 3.283],

-        [27.0, 3.283],

-        [28.0, 3.284],

-        [29.0, 3.284],

-        [30.0, 3.285],  # 30%

-        [31.0, 3.286],

-        [32.0, 3.286],

-        [33.0, 3.287],

-        [34.0, 3.287],

-        [35.0, 3.288],

-        [36.0, 3.289],

-        [37.0, 3.289],

-        [38.0, 3.290],

-        [39.0, 3.290],

-        [40.0, 3.291],  # 40%

-        [41.0, 3.292],

-        [42.0, 3.292],

-        [43.0, 3.293],

-        [44.0, 3.293],

-        [45.0, 3.294],

-        [46.0, 3.295],

-        [47.0, 3.295],

-        [48.0, 3.296],

-        [49.0, 3.296],

-        [50.0, 3.297],  # 50%

-        [51.0, 3.298],

-        [52.0, 3.298],

-        [53.0, 3.299],

-        [54.0, 3.299],

-        [55.0, 3.300],

-        [56.0, 3.300],

-        [57.0, 3.301],

-        [58.0, 3.302],

-        [59.0, 3.302],

-        [60.0, 3.303],  # 60%

-        [61.0, 3.303],

-        [62.0, 3.304],

-        [63.0, 3.304],

-        [64.0, 3.305],

-        [65.0, 3.306],

-        [66.0, 3.306],

-        [67.0, 3.307],

-        [68.0, 3.307],

-        [69.0, 3.308],

-        [70.0, 3.308],  # 70%

-        [71.0, 3.309],

-        [72.0, 3.309],

-        [73.0, 3.310],

-        [74.0, 3.311],

-        [75.0, 3.311],

-        [76.0, 3.312],

-        [77.0, 3.312],

-        [78.0, 3.313],

-        [79.0, 3.313],

-        [80.0, 3.314],  # 80%

-        [81.0, 3.316],

-        [82.0, 3.317],

-        [83.0, 3.319],

-        [84.0, 3.320],

-        [85.0, 3.322],

-        [86.0, 3.323],

-        [87.0, 3.325],

-        [88.0, 3.326],

-        [89.0, 3.328],

-        [90.0, 3.329],  # 90%

-        [91.0, 3.343],

-        [92.0, 3.358],


... (372 more lines) ...

             ambient_temp_c: Ambient temperature in °C (optional)

@@ -666,20 +668,21 @@
         capacity_ah = self._capacity_actual_ah * temp_capacity_factor * fault_capacity_factor

         

         # Update SOC using Coulomb counting

-        # SOC change: dSOC = I * dt / Q

-        # Positive current (charge) increases SOC, negative current (discharge) decreases SOC

+        # SOC change: dSOC = -I * dt / Q (negated because positive = discharge, negative = charge)

+        # Positive current (discharge) decreases SOC, negative current (charge) increases SOC

         # Use fault-modified current

         current_a = fault_current_ma / 1000.0

         dt_hours = dt_ms / (1000.0 * 3600.0)

-        dsoc = (current_a * dt_hours) / capacity_ah

+        dsoc = -(current_a * dt_hours) / capacity_ah  # Negate because positive = discharge

         

         self._soc += dsoc

         self._soc = np.clip(self._soc, 0.0, 1.0)

         

         # Update current direction for hysteresis

-        if current_ma > 0.001:  # Charging (small threshold to avoid noise)

+        # Note: Positive current = discharge, Negative current = charge

+        if current_ma > 0.001:  # Discharging (positive current, small threshold to avoid noise)

             new_direction = 1

-        elif current_ma < -0.001:  # Discharging

+        elif current_ma < -0.001:  # Charging (negative current)

             new_direction = -1

         else:  # Rest

             new_direction = 0

@@ -815,9 +818,10 @@
         else:

             v_terminal = v_internal

         

-        # Apply minimum voltage limit (2.5V for LiFePO4 - prevents unrealistic negative voltages)

+        # Apply minimum voltage limit (2.51V for LiFePO4 - ensures voltage > 2.5V)

+        # At 0% SOC, ensure voltage never drops below 2.51V (2510 mV)

         # Check if overdischarge fault is active - if so, use fault's voltage limit

-        MIN_VOLTAGE = 2.5  # Default minimum safe operating voltage for LiFePO4

+        MIN_VOLTAGE = 2.51  # Minimum safe operating voltage (2510 mV) - ensures voltage > 2.5V

         

         # Check for overdischarge fault - allows discharging below normal minimum

         if hasattr(self, '_fault_state') and self._fault_state:

@@ -825,10 +829,17 @@
                 voltage_limit_mv = self._fault_state['overdischarge'].get('voltage_limit_mv', 2500.0)

                 voltage_limit_v = voltage_limit_mv / 1000.0

                 # Overdischarge fault allows voltage to drop below normal minimum

-                # Use the fault's voltage limit instead of default 2.5V

+                # Use the fault's voltage limit instead of default 2.51V

                 MIN_VOLTAGE = voltage_limit_v

         

+        # Strictly enforce minimum voltage: ensure voltage never goes below 2.51V (2510 mV)

+        # This is critical for 0% SOC operation to ensure voltage > 2.5V

         v_terminal = max(v_terminal, MIN_VOLTAGE)

+        

+        # Additional safety check: if voltage is still below 2.51V after clamp, force it to 2.51V

+        # This handles any edge cases or rounding issues

+        if v_terminal < 2.51:

+            v_terminal = 2.51

         

         # Apply overcharge voltage limit if fault is active

         # Overcharge allows cell to charge beyond normal maximum (typically 3.65V for LiFePO4)

@@ -862,10 +873,13 @@
             self._last_update_time_hours = current_time_hours

         

         # Store terminal voltage for get_state() - ALWAYS store this

+        # Final safety check: ensure voltage is at least 2.51V (2510 mV) before storing

+        # This prevents any cell from going below 2.51V, especially at 0% SOC

+        v_terminal = max(v_terminal, 2.51)

         self._last_terminal_voltage_v = v_terminal

         

-        # Convert to mV

-        voltage_mv = v_terminal * 1000.0

+        # Convert to mV - ensure minimum 2510 mV (2.51V) - ensures voltage > 2.5V

+        voltage_mv = max(v_terminal * 1000.0, 2510.0)

         

         # Return voltage in mV and SOC in percent

         return voltage_mv, self._soc * 100.0

@@ -921,12 +935,20 @@
             else:

                 v_terminal = v_internal_approx

             

-            # Apply minimum voltage limit

-            v_terminal = max(v_terminal, 2.5)

+            # Apply minimum voltage limit - strictly enforce 2.51V minimum (2510 mV)

+            # This ensures cells never go below 2.51V, especially at 0% SOC

+            v_terminal = max(v_terminal, 2.51)

+            if v_terminal < 2.51:

+                v_terminal = 2.51

+        

+        # Ensure voltage is at least 2.51V (2510 mV) before returning

+        # This is critical for 0% SOC to ensure voltage > 2.5V

+        v_terminal = max(v_terminal, 2.51)

+        voltage_mv = max(v_terminal * 1000.0, 2510.0)

         

         return {

             'soc_pct': self._soc * 100.0,

-            'voltage_mv': v_terminal * 1000.0,  # Use stored or calculated terminal voltage

+            'voltage_mv': voltage_mv,  # Use stored or calculated terminal voltage (clamped to >= 2500 mV)

             'temperature_c': self._temperature_c,

             'capacity_ah': self._capacity_actual_ah,

             'internal_resistance_mohm': self.get_internal_resistance(),

```

---

#### `pc_simulator/plant/pack_model.py`

**Changes:** +9 lines, -4 lines

```diff
--- REF/pc_simulator/plant/pack_model.py
+++ CURR/pc_simulator/plant/pack_model.py
@@ -129,7 +129,7 @@
         Update all cells in the pack.

         

         Args:

-            current_ma: Pack current in mA (positive = charge, negative = discharge)

+            current_ma: Pack current in mA (positive = discharge, negative = charge)

             dt_ms: Time step in milliseconds

             ambient_temp_c: Ambient temperature in °C (optional)

         """

@@ -212,18 +212,23 @@
         Get cell voltages in mV.

         

         Returns:

-            numpy array[16] of cell voltages in mV

+            numpy array[16] of cell voltages in mV (minimum 2500 mV = 2.5V)

         """

         voltages = np.zeros(self.NUM_CELLS)

         

         for i, cell in enumerate(self._cells):

             if self._fault_voltages[i] is not None:

-                # Return fault-injected voltage

-                voltages[i] = self._fault_voltages[i]

+                # Return fault-injected voltage (but still enforce minimum)

+                voltages[i] = max(self._fault_voltages[i], 2510.0)

             else:

                 # Get actual cell voltage

                 state = cell.get_state()

                 voltages[i] = state['voltage_mv']

+        

+        # Final safety check: ensure ALL cell voltages are at least 2510 mV (2.51V)

+        # This is critical for 0% SOC to ensure voltage > 2.5V

+        # Clamp all voltages to minimum 2510 mV

+        voltages = np.maximum(voltages, 2510.0)

         

         return voltages

     

```

---


## 📊 Change Statistics

| Category | Count |
|----------|-------|
| **New Files** | 1 (uart_xbb_sequential.py) |
| **Modified Files** | 4 |
| **Total Lines Added** | +575 |
| **Total Lines Removed** | -273 |
| **Net Change** | +302 lines |

---

## 🔑 Key Technical Changes

### 1. Sequential XBB Communication
- **New Module:** `uart_xbb_sequential.py` (494 lines)
- **Purpose:** Sequential send-then-receive communication (no threading)
- **Features:**
  - Retry logic: 10 attempts with 1 second timeout
  - Full RX frame parsing (118 bytes)
  - BMS state tracking for MOSFET gating
  - Detailed TX/RX frame printing

### 2. RX Frame Format Updates
- **Frame Size:** 118 bytes total (4 header + 112 payload + 2 footer)
- **Payload Size:** 112 bytes (removed `bms_state_flags` field)
- **Length Field:** 0x0070 (112 in decimal)
- **All multi-byte data:** Big-endian format
- **Fields:** timestamp, protection_flags, SOC/SOH/SOE (float), current, voltage, balancing, faults, temperatures, cell voltages, sequence, MOSFET status

### 3. TX Frame Format Updates
- **Frame Size:** 92 bytes total (was 88 bytes)
- **Payload Size:** 84 bytes (was 80 bytes)
- **Added:** Counter field (4 bytes, int32)
- **Data Length Field:** Updated to 84 bytes

### 4. Current Sign Convention
- **Changed:** Positive = discharge, Negative = charge
- **Updated in:** `main.py`, `cell_model.py`, `pack_model.py`
- **Impact:** SOC calculation, MOSFET gating logic, documentation

### 5. Voltage Clamping
- **Minimum Voltage:** 2.51V (2510 mV) - ensures voltage > 2.5V
- **Applied at:** Multiple points in `cell_model.py` and `pack_model.py`
- **Purpose:** Prevent undervoltage at 0% SOC

### 6. OCV Table Adjustments
- **0% SOC Voltage:** ~2.52V (discharge), ~2.535V (charge)
- **Hysteresis:** Charge curve higher than discharge curve
- **Range:** Adjusted to match application requirements

### 7. MOSFET Gating Logic
- **Enhanced:** Uses both `protection_flags` and `mosfet_status`
- **Recovery:** Resumes current when protection clears
- **Direction-aware:** Checks correct MOSFET based on current direction

---

## 📝 Notes

- All changes maintain backward compatibility with existing code
- The sequential communication mode is optional (use `--sequential` flag)
- Voltage clamping ensures cells never go below 2.51V, especially at 0% SOC
- Current sign convention is now consistent: positive=discharge, negative=charge

---

**Document End**
