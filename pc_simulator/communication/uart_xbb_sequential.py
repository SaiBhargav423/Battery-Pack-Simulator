"""
Sequential XBB UART Communication

Implements sequential send-then-receive communication for XBB protocol:
- Sends TX frame (92 bytes) to BMS
- Waits for RX response (118 bytes) from BMS with timeout
- Retries up to 10 times if no response
- Parses and validates RX frame
- Receives and stores BMS state (for internal use, e.g., MOSFET gating logic)
"""

import serial
import time
import logging
from typing import Optional, Dict
import numpy as np
from communication.protocol_xbb import XBBFrameEncoder, XBBFrameDecoder, XBB_RX_FRAME_LENGTH


class SequentialXBBUART:
    """
    Sequential XBB UART communication (no threads).
    
    Features:
    - Sequential send → wait → receive → parse flow
    - Retry logic: 10 attempts with 1 second timeout each
    - CRC8 validation for RX frames
    - Receives and stores BMS state from RX frames (for internal use, e.g., MOSFET gating logic)
    """
    
    def __init__(
        self,
        port: str,
        baudrate: int = 921600,
        timeout: float = 1.0,
        max_retries: int = 10,
        verbose: bool = False
    ):
        """
        Initialize sequential XBB UART communication.
        
        Args:
            port: Serial port (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
            baudrate: Baud rate (default: 921600)
            timeout: Receive timeout in seconds (default: 1.0)
            max_retries: Maximum retry attempts (default: 10)
            verbose: Enable verbose logging (default: False)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.max_retries = max_retries
        self.verbose = verbose
        
        # Setup logging
        self._logger = logging.getLogger(__name__)
        if verbose:
            self._logger.setLevel(logging.DEBUG)
        
        # Serial port
        self._serial: Optional[serial.Serial] = None
        
        # Sequence counter for TX frames
        self._tx_counter = 0
        
        # BMS state (received and stored from RX frames - for internal use only)
        self._bms_state: Optional[Dict] = None
        
        # Statistics
        self._tx_count = 0
        self._rx_count = 0
        self._error_count = 0
        self._retry_count = 0
    
    def start(self) -> bool:
        """
        Open serial port.
        
        Returns:
            True if port opened successfully
        """
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=1.0,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Clear buffers
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
            
            if self.verbose:
                self._logger.info(f"Serial port opened: {self.port} @ {self.baudrate} baud")
            
            return True
        except Exception as e:
            self._logger.error(f"Failed to open serial port: {e}")
            return False
    
    def stop(self):
        """Close serial port."""
        if self._serial and self._serial.is_open:
            self._serial.close()
            if self.verbose:
                self._logger.info("Serial port closed")
    
    def send_and_receive(
        self,
        pack_current_ma: int,
        pack_voltage_mv: int,
        temp_cell_c: float,
        temp_pcb_c: float,
        cell_voltages_mv: np.ndarray
    ) -> bool:
        """
        Send TX frame and wait for RX response with retry logic.
        
        Args:
            pack_current_ma: Pack current in milli-Amperes
            pack_voltage_mv: Pack voltage in milli-Volts
            temp_cell_c: Cell temperature in °C
            temp_pcb_c: PCB temperature in °C
            cell_voltages_mv: Cell voltages in milli-Volts (array[16])
        
        Returns:
            True if successful (sent and received valid response), False otherwise
        """
        if self._serial is None or not self._serial.is_open:
            self._logger.error("Serial port not open")
            return False
        
        # Encode TX frame with counter
        try:
            tx_frame = XBBFrameEncoder.encode_frame(
                pack_current_ma=pack_current_ma,
                pack_voltage_mv=pack_voltage_mv,
                temp_cell_c=temp_cell_c,
                temp_pcb_c=temp_pcb_c,
                cell_voltages_mv=cell_voltages_mv,
                counter=self._tx_counter
            )
            current_counter = self._tx_counter
            self._tx_counter = (self._tx_counter + 1) % (2**31)  # Wrap at 32-bit limit
        except Exception as e:
            self._logger.error(f"Failed to encode TX frame: {e}")
            return False
        
        # Print TX frame data (only once, before first send)
        self.print_tx_data(
            pack_current_ma=pack_current_ma,
            pack_voltage_mv=pack_voltage_mv,
            temp_cell_c=temp_cell_c,
            temp_pcb_c=temp_pcb_c,
            cell_voltages_mv=cell_voltages_mv,
            counter=current_counter,
            frame_bytes=tx_frame
        )
        
        # Retry loop: Send frame, wait for response, resend if no response
        for attempt in range(1, self.max_retries + 1):
            # Clear input buffer before sending (to remove any stale data)
            if attempt == 1:
                self._serial.reset_input_buffer()
            else:
                # On retry, clear buffer and show retry message
                self._serial.reset_input_buffer()
                print(f"[RETRY {attempt}/{self.max_retries}] Resending frame and waiting for response...")
            
            # Send TX frame
            if not self._send_frame(tx_frame):
                self._error_count += 1
                if attempt < self.max_retries:
                    if self.verbose:
                        self._logger.warning(f"TX send failed, retrying ({attempt}/{self.max_retries})...")
                    time.sleep(0.1)  # Small delay before retry
                    continue
                else:
                    self._logger.error(f"TX send failed after {self.max_retries} attempts")
                    return False
            
            # Wait for RX response (with full timeout)
            if self.verbose:
                print(f"[Attempt {attempt}/{self.max_retries}] Waiting for RX response (timeout: {self.timeout}s)...")
            
            rx_frame = self._receive_frame()
            
            if rx_frame is not None:
                # Parse and validate RX frame
                bms_data = XBBFrameDecoder.decode(rx_frame, verbose=self.verbose)
                
                if bms_data is not None:
                    # Store received BMS state (for internal use, e.g., MOSFET gating logic)
                    self._bms_state = bms_data
                    self._rx_count += 1
                    
                    # Print RX frame data
                    self.print_rx_data(bms_data)
                    
                    if self.verbose:
                        print(f"[SUCCESS] RX frame received and parsed on attempt {attempt}")
                    
                    return True
                else:
                    # Invalid frame (CRC or parsing error)
                    self._error_count += 1
                    print(f"[ERROR] RX frame validation failed (CRC or parsing error) - attempt {attempt}/{self.max_retries}")
                    if self.verbose:
                        # Print received frame for debugging
                        print(f"[DEBUG] Received frame length: {len(rx_frame)} bytes")
                        print(f"[DEBUG] First 20 bytes: {' '.join([f'{b:02X}' for b in rx_frame[:20]])}")
                        print(f"[DEBUG] Last 10 bytes: {' '.join([f'{b:02X}' for b in rx_frame[-10:]])}")
                    if attempt < self.max_retries:
                        time.sleep(0.1)  # Small delay before retry
            else:
                # No response received within timeout
                self._error_count += 1
                print(f"[TIMEOUT] No RX response received (attempt {attempt}/{self.max_retries})")
            
            # If not last attempt, wait a bit before retrying
            if attempt < self.max_retries:
                self._retry_count += 1
                time.sleep(0.2)  # Small delay between retries
        
        # All attempts failed - terminate process
        self._logger.error(f"Failed to receive valid response after {self.max_retries} attempts")
        self._logger.error("Terminating process due to communication failure")
        import sys
        sys.exit(1)
    
    def _send_frame(self, frame_bytes: bytes) -> bool:
        """
        Send frame via UART.
        
        Args:
            frame_bytes: Frame bytes to send
        
        Returns:
            True if sent successfully
        """
        try:
            self._serial.write(frame_bytes)
            self._serial.flush()
            self._tx_count += 1
            return True
        except Exception as e:
            self._logger.error(f"Failed to send frame: {e}")
            return False
    
    def _receive_frame(self) -> Optional[bytes]:
        """
        Receive RX frame with timeout.
        
        Returns:
            Received frame bytes (118 bytes) or None if timeout/error
        """
        try:
            # Wait for header (0xA5) with timeout
            start_time = time.time()
            header_found = False
            
            # First, wait for header byte (0xA5)
            while (time.time() - start_time) < self.timeout:
                if self._serial.in_waiting > 0:
                    byte = self._serial.read(1)
                    if len(byte) == 1 and byte[0] == 0xA5:
                        header_found = True
                        break
                time.sleep(0.01)  # Small delay to avoid busy loop
            
            if not header_found:
                # Timeout waiting for header
                return None
            
            # Header found, now read remaining bytes
            # Calculate remaining time
            elapsed = time.time() - start_time
            remaining_timeout = max(0.1, self.timeout - elapsed)  # At least 100ms for remaining bytes
            
            # Read remaining frame bytes (118 - 1 = 117 bytes)
            remaining = XBB_RX_FRAME_LENGTH - 1
            frame = bytearray([0xA5])
            
            # Read remaining bytes with timeout
            self._serial.timeout = remaining_timeout
            remaining_bytes = self._serial.read(remaining)
            self._serial.timeout = self.timeout  # Restore original timeout
            
            if len(remaining_bytes) == remaining:
                frame.extend(remaining_bytes)
                return bytes(frame)
            else:
                # Incomplete frame - didn't receive all bytes in time
                return None
                
        except Exception as e:
            self._logger.error(f"Error receiving frame: {e}")
            return None
    
    def get_bms_state(self) -> Optional[Dict]:
        """
        Get latest BMS state from last received RX frame.
        
        Note: This returns the BMS state received from the BMS (not sent by the application).
        The application only sends TX frames (pack data) and receives RX frames (BMS status).
        
        Returns:
            Dictionary with BMS state, or None if no data received yet
        """
        return self._bms_state
    
    def get_statistics(self) -> Dict:
        """
        Get communication statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'tx_count': self._tx_count,
            'rx_count': self._rx_count,
            'error_count': self._error_count,
            'retry_count': self._retry_count,
            'tx_counter': self._tx_counter
        }
    
    def print_tx_data(
        self,
        pack_current_ma: int,
        pack_voltage_mv: int,
        temp_cell_c: float,
        temp_pcb_c: float,
        cell_voltages_mv: np.ndarray,
        counter: int,
        frame_bytes: bytes
    ):
        """
        Print TX frame data in readable format.
        
        Args:
            pack_current_ma: Pack current in milli-Amperes
            pack_voltage_mv: Pack voltage in milli-Volts
            temp_cell_c: Cell temperature in °C
            temp_pcb_c: PCB temperature in °C
            cell_voltages_mv: Cell voltages in milli-Volts (array[16])
            counter: Sequence counter
            frame_bytes: Encoded frame bytes
        """
        print("\n" + "=" * 80)
        print(">>> TX FRAME SENT <<<")
        print("=" * 80)
        
        # Convert to readable units
        pack_current_a = pack_current_ma / 1000.0
        pack_voltage_v = pack_voltage_mv / 1000.0
        temp_cell_milli = int(round(temp_cell_c * 1000.0))
        temp_pcb_milli = int(round(temp_pcb_c * 1000.0))
        
        # Print in format similar to reference implementation
        print(f"(Counter: {counter}): pack_current_A={pack_current_a:.1f} ({pack_current_ma} milli), "
              f"pack_voltage_V={pack_voltage_v:.6f} ({pack_voltage_mv} milli), "
              f"temp_cell_C={temp_cell_c:.6f} ({temp_cell_milli} milli), "
              f"temp_pcb_C={temp_pcb_c:.6f} ({temp_pcb_milli} milli), ", end='')
        
        # Print all 16 cell voltages
        for i in range(16):
            cell_v = cell_voltages_mv[i] / 1000.0
            cell_v_milli = int(cell_voltages_mv[i])
            if i < 15:
                print(f"cell_{i+1}_V={cell_v:.6f} ({cell_v_milli} milli), ", end='')
            else:
                print(f"cell_{i+1}_V={cell_v:.6f} ({cell_v_milli} milli)")
        
        # Print hex frame
        hex_str = ' '.join([f'{b:02X}' for b in frame_bytes])
        print(f"Frame ({len(frame_bytes)} bytes): {hex_str}")
        print("=" * 80 + "\n")
    
    def print_rx_data(self, bms_data: dict):
        """
        Print RX frame data in readable format.
        
        Args:
            bms_data: Dictionary with BMS state data
        """
        print("\n" + "=" * 80)
        print("<<< RX FRAME RECEIVED <<<")
        print("=" * 80)
        
        # Convert to readable units
        bms_voltage_v = bms_data['bms_voltage_mv'] / 1000.0
        bms_current_a = bms_data['bms_current_ma'] / 1000.0
        
        print(f"\nTimestamp: {bms_data['timestamp_ms']} ms")
        print(f"Sequence: {bms_data['sequence']}")
        
        print(f"\nPack Measurements:")
        print(f"  BMS Voltage: {bms_data['bms_voltage_mv']} mV ({bms_voltage_v:.6f} V)")
        print(f"  BMS Current: {bms_data['bms_current_ma']} mA ({bms_current_a:.6f} A)")
        
        print(f"\nBattery Status:")
        print(f"  SOC: {bms_data['soc']:.2f} %")
        print(f"  SOH: {bms_data['soh']:.2f} %")
        print(f"  SOE: {bms_data['soe']:.2f} %")
        
        # Debug: Show raw bytes in hex if SOH is zero
        if abs(bms_data['soh']) < 0.01:
            soh_bytes_raw = bms_data.get('soh_bytes_raw')
            if soh_bytes_raw:
                import struct
                soh_hex = ' '.join([f'{b:02X}' for b in soh_bytes_raw])
                print(f"\n[DEBUG SOH] SOH is 0.00% - Raw bytes (hex): {soh_hex}")
                # Show big-endian float interpretation
                soh_be_float = struct.unpack('>f', soh_bytes_raw)[0]
                soh_be_uint = struct.unpack('>I', soh_bytes_raw)[0]
                print(f"           BE float: {soh_be_float:.6f}, BE uint32: {soh_be_uint}")
                if abs(bms_data['soc']) > 0.01:
                    print(f"           [WARNING] SOC is {bms_data['soc']:.2f}% - SOH should not be 0 for a working battery")
        
        print(f"\nTemperatures:")
        print(f"  PCB Temperature: {bms_data.get('pcb_temperature_c', 0.0):.2f} °C")
        if 'cell_temperatures_c' in bms_data:
            print(f"  Cell Temperatures (4 sensors):")
            for i in range(0, len(bms_data['cell_temperatures_c']), 4):
                temps = [f"T[{j}]: {bms_data['cell_temperatures_c'][j]:5.2f} °C" for j in range(i, min(i+4, len(bms_data['cell_temperatures_c'])))]
                print("    " + "  |  ".join(temps))
        
        print(f"\nCell Voltages (16 cells):")
        if 'cell_voltages_mv' in bms_data:
            for i in range(0, 16, 4):
                cells = [f"C[{j:2d}]: {bms_data['cell_voltages_mv'][j]:5d} mV ({bms_data['cell_voltages_mv'][j]/1000.0:.3f} V)" for j in range(i, min(i+4, 16))]
                print("    " + "  |  ".join(cells))
        
        print(f"\nBalancing Status (16 cells):")
        for i in range(0, 16, 4):
            cells = [f"Cell {j+1:2d}: {bms_data['balancing_status'][j]:5d}" for j in range(i, min(i+4, 16))]
            print("    " + "  |  ".join(cells))
        
        print(f"\nFault Codes:")
        fault_names = ['Overvoltage', 'Undervoltage', 'Overcurrent', 'Overtemp', 'Undertemp', 'Short Circuit', 'Thermal Runaway', 'Insulation Short']
        for i, fault_name in enumerate(fault_names):
            status = 'YES' if i < len(bms_data['fault_codes']) and bms_data['fault_codes'][i] != 0 else 'NO'
            print(f"  {fault_name:20s}: {status}")
        
        print(f"\nProtection Flags: 0x{bms_data['protection_flags']:04X}")
        
        print(f"\nMOSFET Status:")
        print(f"  Charge MOSFET: {'ON' if bms_data['mosfet_charge'] else 'OFF'}")
        print(f"  Discharge MOSFET: {'ON' if bms_data['mosfet_discharge'] else 'OFF'}")
        print(f"  Raw Status: 0x{bms_data['mosfet_status']:04X}")
        
        print("=" * 80 + "\n")
    
    def send_frame(self, frame_data: dict) -> bool:
        """
        Interface method compatible with main.py.
        
        Args:
            frame_data: Dictionary with keys:
                - pack_current_ma: pack current in milli-Amperes
                - pack_voltage_mv: pack voltage in milli-Volts
                - temp_cell_c: cell temperature in °C
                - temp_pcb_c: PCB temperature in °C
                - cell_voltages_mv: cell voltages in milli-Volts (array[16])
        
        Returns:
            True if successful
        """
        # Validate required fields
        required_fields = ['pack_current_ma', 'pack_voltage_mv', 'temp_cell_c', 'temp_pcb_c', 'cell_voltages_mv']
        for field in required_fields:
            if field not in frame_data:
                self._logger.error(f"Missing required field: {field}")
                return False
        
        # Validate cell voltages array
        cell_voltages = frame_data['cell_voltages_mv']
        if not isinstance(cell_voltages, np.ndarray) or len(cell_voltages) != 16:
            self._logger.error(f"cell_voltages_mv must be numpy array with 16 elements")
            return False
        
        # Call send_and_receive
        return self.send_and_receive(
            pack_current_ma=int(frame_data['pack_current_ma']),
            pack_voltage_mv=int(frame_data['pack_voltage_mv']),
            temp_cell_c=float(frame_data['temp_cell_c']),
            temp_pcb_c=float(frame_data['temp_pcb_c']),
            cell_voltages_mv=cell_voltages
        )
