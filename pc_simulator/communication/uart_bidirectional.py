"""
Bidirectional UART Communication for HIL Testing

Provides bidirectional communication with BMS hardware:
- TX: Send AFE measurement frames (PC → BMS)
- RX: Receive BMS application frames (BMS → PC)
- Thread-safe operation
- Backward compatible with UARTTransmitter interface
"""

import serial
import serial.tools.list_ports
import threading
import queue
import time
import logging
import struct
from typing import Optional, Dict, Callable
import numpy as np
from communication.protocol import (
    AFEMeasFrame,
    BMSAppFrame,
    validate_afe_meas_data,
    crc16_ccitt,
    SOF,
    EOF
)


class BidirectionalUART:
    """
    Bidirectional UART communication for HIL testing.
    
    Features:
    - Separate TX/RX threads for concurrent operation
    - Thread-safe queues
    - Callback-based BMS data handling
    - Automatic reconnection
    - Statistics tracking
    - Backward compatible with UARTTransmitter interface
    """
    
    def __init__(
        self,
        port: str,
        baudrate: int = 921600,
        tx_rate_hz: float = 50.0,
        rx_timeout: float = 0.1,
        verbose: bool = False
    ):
        """
        Initialize bidirectional UART.
        
        Args:
            port: Serial port (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
            baudrate: Baud rate (default: 921600)
            tx_rate_hz: TX frame rate in Hz (default: 50.0)
            rx_timeout: RX timeout in seconds (default: 0.1)
            verbose: Enable verbose logging (default: False)
        """
        self._port = port
        self._baudrate = baudrate
        self._tx_rate_hz = tx_rate_hz
        self._tx_frame_interval_sec = 1.0 / tx_rate_hz if tx_rate_hz > 0 else 0.0
        self._rx_timeout = rx_timeout
        self._verbose = verbose
        
        # Serial port (shared between TX/RX)
        self._serial: Optional[serial.Serial] = None
        self._serial_lock = threading.Lock()
        
        # TX thread and queue
        self._tx_thread: Optional[threading.Thread] = None
        self._tx_queue = queue.Queue(maxsize=100)
        self._tx_stop_event = threading.Event()
        self._tx_sequence = 0
        self._last_tx_time = 0.0
        
        # RX thread and queue
        self._rx_thread: Optional[threading.Thread] = None
        self._rx_queue = queue.Queue(maxsize=1000)
        self._rx_stop_event = threading.Event()
        self._rx_buffer = bytearray()
        
        # BMS data callback
        self._bms_data_callback: Optional[Callable[[dict], None]] = None
        self._callback_lock = threading.Lock()
        
        # Statistics
        self._tx_count = 0
        self._rx_count = 0
        self._tx_errors = 0
        self._rx_errors = 0
        self._crc_errors = 0
        self._frame_errors = 0
        self._stats_lock = threading.Lock()
        
        # BMS state (thread-safe)
        self._bms_state = {
            'mosfet_charge': True,
            'mosfet_discharge': True,
            'protection_active': False,
            'protection_flags': 0,
            'bms_current_ma': 0,
            'bms_voltage_mv': 0,
            'last_update_ms': 0,
            'last_update_time': 0.0
        }
        self._bms_state_lock = threading.Lock()
        
        # Logging
        self._logger = logging.getLogger(__name__)
        if verbose:
            self._logger.setLevel(logging.DEBUG)
        else:
            self._logger.setLevel(logging.INFO)
    
    def set_bms_data_callback(self, callback: Callable[[dict], None]):
        """
        Set callback for received BMS data.
        
        Args:
            callback: Function that takes BMS data dict as argument
        """
        with self._callback_lock:
            self._bms_data_callback = callback
    
    def get_bms_state(self) -> dict:
        """
        Get current BMS state (thread-safe).
        
        Returns:
            Dictionary with BMS state:
            - mosfet_charge: bool
            - mosfet_discharge: bool
            - protection_active: bool
            - protection_flags: int
            - bms_current_ma: int
            - bms_voltage_mv: int
            - last_update_ms: int
        """
        with self._bms_state_lock:
            return self._bms_state.copy()
    
    def _open_serial_port(self) -> bool:
        """Open serial port with error handling."""
        try:
            with self._serial_lock:
                if self._serial is not None and self._serial.is_open:
                    return True
                
                self._serial = serial.Serial(
                    port=self._port,
                    baudrate=self._baudrate,
                    timeout=self._rx_timeout,
                    write_timeout=1.0
                )
                
                if self._verbose:
                    self._logger.debug(f"Opened serial port: {self._port} at {self._baudrate} baud")
                
                return True
        except serial.SerialException as e:
            self._logger.error(f"Serial port error: {e}")
            with self._stats_lock:
                self._tx_errors += 1
            return False
        except Exception as e:
            self._logger.error(f"Unexpected error opening serial port: {e}")
            with self._stats_lock:
                self._tx_errors += 1
            return False
    
    def _close_serial_port(self):
        """Close serial port."""
        with self._serial_lock:
            if self._serial is not None and self._serial.is_open:
                try:
                    self._serial.close()
                    if self._verbose:
                        self._logger.debug(f"Closed serial port: {self._port}")
                except Exception as e:
                    self._logger.warning(f"Error closing serial port: {e}")
    
    def _tx_worker(self):
        """TX thread worker - sends AFE frames."""
        if self._verbose:
            self._logger.debug("TX thread started")
        
        while not self._tx_stop_event.is_set():
            try:
                # Get frame from queue (with timeout to check stop event)
                try:
                    frame_data = self._tx_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Rate limiting
                current_time = time.time()
                time_since_last = current_time - self._last_tx_time
                
                if time_since_last < self._tx_frame_interval_sec:
                    sleep_time = self._tx_frame_interval_sec - time_since_last
                    time.sleep(sleep_time)
                
                # Send frame
                with self._serial_lock:
                    if self._serial is None or not self._serial.is_open:
                        if not self._open_serial_port():
                            self._tx_queue.task_done()
                            continue
                    
                    try:
                        bytes_written = self._serial.write(frame_data['frame'])
                        self._serial.flush()
                        
                        if bytes_written != len(frame_data['frame']):
                            raise serial.SerialTimeoutException(
                                f"Only wrote {bytes_written} of {len(frame_data['frame'])} bytes"
                            )
                        
                        with self._stats_lock:
                            self._tx_count += 1
                        self._last_tx_time = time.time()
                        
                        if self._verbose:
                            self._logger.debug(f"Sent frame: {len(frame_data['frame'])} bytes, sequence: {self._tx_sequence}")
                    
                    except serial.SerialTimeoutException as e:
                        self._logger.warning(f"TX timeout: {e}")
                        with self._stats_lock:
                            self._tx_errors += 1
                        self._close_serial_port()
                    
                    except serial.SerialException as e:
                        self._logger.warning(f"TX serial error: {e}")
                        with self._stats_lock:
                            self._tx_errors += 1
                        self._close_serial_port()
                
                self._tx_queue.task_done()
            
            except Exception as e:
                self._logger.error(f"TX thread error: {e}")
                with self._stats_lock:
                    self._tx_errors += 1
        
        # Close serial port when thread stops
        self._close_serial_port()
        
        if self._verbose:
            self._logger.debug("TX thread stopped")
    
    def _rx_worker(self):
        """RX thread worker - continuously reads BMS frames."""
        if self._verbose:
            self._logger.debug("RX thread started")
        
        while not self._rx_stop_event.is_set():
            try:
                with self._serial_lock:
                    if not self._serial or not self._serial.is_open:
                        time.sleep(0.1)
                        continue
                    
                    # Read available data
                    if self._serial.in_waiting > 0:
                        data = self._serial.read(self._serial.in_waiting)
                        self._rx_buffer.extend(data)
                    
                    # Try to parse frames
                    while True:
                        frame = self._extract_frame()
                        if not frame:
                            break
                        
                        bms_data = BMSAppFrame.decode(frame)
                        if bms_data:
                            with self._stats_lock:
                                self._rx_count += 1
                            
                            self._update_bms_state(bms_data)
                            
                            # Call callback if set
                            with self._callback_lock:
                                if self._bms_data_callback:
                                    try:
                                        self._bms_data_callback(bms_data)
                                    except Exception as e:
                                        self._logger.error(f"Callback error: {e}")
                            
                            # Queue for processing
                            try:
                                self._rx_queue.put_nowait(bms_data)
                            except queue.Full:
                                # Drop oldest data
                                try:
                                    self._rx_queue.get_nowait()
                                    self._rx_queue.put_nowait(bms_data)
                                except queue.Empty:
                                    pass
                        else:
                            with self._stats_lock:
                                self._crc_errors += 1
                
                time.sleep(self._rx_timeout)
            
            except Exception as e:
                self._logger.error(f"RX thread error: {e}")
                with self._stats_lock:
                    self._rx_errors += 1
                time.sleep(0.1)
        
        if self._verbose:
            self._logger.debug("RX thread stopped")
    
    def _extract_frame(self) -> Optional[bytes]:
        """
        Extract complete frame from RX buffer.
        
        Returns:
            Frame bytes or None if no complete frame available
        """
        # Find SOF
        sof_idx = -1
        for i, byte in enumerate(self._rx_buffer):
            if byte == SOF:
                sof_idx = i
                break
        
        if sof_idx == -1:
            # No SOF found, clear buffer
            self._rx_buffer.clear()
            return None
        
        # Remove data before SOF
        if sof_idx > 0:
            self._rx_buffer[:] = self._rx_buffer[sof_idx:]
        
        if len(self._rx_buffer) < 7:  # Minimum frame size
            return None
        
        # Get length from header (assuming same format as AFEMeasFrame)
        try:
            msg_id, length, seq = struct.unpack('<BBH', self._rx_buffer[1:5])
        except (struct.error, IndexError):
            # Invalid header, remove SOF and try again
            self._rx_buffer.pop(0)
            return None
        
        expected_size = 1 + 4 + length + 2 + 1  # SOF + header + payload + CRC + EOF
        
        if len(self._rx_buffer) < expected_size:
            return None
        
        # Check EOF
        if self._rx_buffer[expected_size - 1] != EOF:
            # Invalid frame, remove SOF and try again
            self._rx_buffer.pop(0)
            with self._stats_lock:
                self._frame_errors += 1
            return None
        
        # Extract frame
        frame = bytes(self._rx_buffer[:expected_size])
        self._rx_buffer[:] = self._rx_buffer[expected_size:]
        return frame
    
    def _update_bms_state(self, bms_data: dict):
        """Update BMS state from received data."""
        with self._bms_state_lock:
            self._bms_state['mosfet_charge'] = bms_data.get('mosfet_charge', True)
            self._bms_state['mosfet_discharge'] = bms_data.get('mosfet_discharge', True)
            self._bms_state['protection_active'] = bms_data.get('protection_active', False)
            self._bms_state['protection_flags'] = bms_data.get('protection_flags', 0)
            self._bms_state['bms_current_ma'] = bms_data.get('bms_current_ma', 0)
            self._bms_state['bms_voltage_mv'] = bms_data.get('bms_voltage_mv', 0)
            self._bms_state['last_update_ms'] = bms_data.get('timestamp_ms', 0)
            self._bms_state['last_update_time'] = time.time()
    
    def send_frame(self, afe_meas_data: dict) -> bool:
        """
        Send AFE measurement frame (backward compatible interface).
        
        Args:
            afe_meas_data: Dictionary with measurement data:
                - timestamp_ms: int
                - vcell_mv: numpy array[16] (uint16, mV)
                - tcell_cc: numpy array[16] (int16, centi-°C)
                - pack_current_ma: int (mA)
                - pack_voltage_mv: int (mV)
                - status_flags: int (uint32)
        
        Returns:
            True if frame queued successfully, False otherwise
        """
        # Validate data
        is_valid, error_msg = validate_afe_meas_data(afe_meas_data)
        if not is_valid:
            self._logger.error(f"Frame validation failed: {error_msg}")
            with self._stats_lock:
                self._tx_errors += 1
            return False
        
        # Encode frame
        try:
            frame = AFEMeasFrame.encode(
                timestamp_ms=afe_meas_data['timestamp_ms'],
                vcell_mv=afe_meas_data['vcell_mv'],
                tcell_cc=afe_meas_data['tcell_cc'],
                pack_current_ma=int(afe_meas_data['pack_current_ma']),
                pack_voltage_mv=int(afe_meas_data['pack_voltage_mv']),
                status_flags=afe_meas_data['status_flags'],
                sequence=self._tx_sequence
            )
            
            # Increment sequence (wrap at 65535)
            self._tx_sequence = (self._tx_sequence + 1) & 0xFFFF
        
        except Exception as e:
            self._logger.error(f"Frame encoding error: {e}")
            with self._stats_lock:
                self._tx_errors += 1
            return False
        
        # Queue frame for transmission
        try:
            self._tx_queue.put_nowait({
                'frame': frame,
                'timestamp': time.time()
            })
            return True
        
        except queue.Full:
            self._logger.warning("TX queue full, dropping frame")
            with self._stats_lock:
                self._tx_errors += 1
            return False
    
    def receive_frame(self, timeout: float = 1.0) -> Optional[dict]:
        """
        Receive BMS frame (blocking with timeout).
        
        Args:
            timeout: Timeout in seconds (default: 1.0)
        
        Returns:
            BMS data dictionary or None if timeout
        """
        try:
            return self._rx_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def start(self) -> bool:
        """
        Start TX and RX threads (backward compatible interface).
        
        Returns:
            True if started successfully, False otherwise
        """
        # Open serial port
        if not self._open_serial_port():
            return False
        
        # Start threads
        self._tx_stop_event.clear()
        self._rx_stop_event.clear()
        
        self._tx_thread = threading.Thread(target=self._tx_worker, daemon=True)
        self._rx_thread = threading.Thread(target=self._rx_worker, daemon=True)
        
        self._tx_thread.start()
        self._rx_thread.start()
        
        if self._verbose:
            self._logger.info(
                f"Bidirectional UART started: {self._port} at {self._baudrate} baud, "
                f"TX: {self._tx_rate_hz} Hz"
            )
        
        return True
    
    def stop(self):
        """Stop threads and close port (backward compatible interface)."""
        self._tx_stop_event.set()
        self._rx_stop_event.set()
        
        if self._tx_thread:
            self._tx_thread.join(timeout=2.0)
        if self._rx_thread:
            self._rx_thread.join(timeout=2.0)
        
        self._close_serial_port()
        
        if self._verbose:
            self._logger.info("Bidirectional UART stopped")
    
    def get_statistics(self) -> dict:
        """
        Get communication statistics (backward compatible interface).
        
        Returns:
            Dictionary with statistics:
            - tx_count: Number of frames sent
            - rx_count: Number of frames received
            - tx_errors: Number of TX errors
            - rx_errors: Number of RX errors
            - crc_errors: Number of CRC errors
            - frame_errors: Number of frame format errors
            - tx_queue_size: Current TX queue size
            - rx_queue_size: Current RX queue size
        """
        with self._stats_lock:
            return {
                'tx_count': self._tx_count,
                'rx_count': self._rx_count,
                'tx_errors': self._tx_errors,
                'rx_errors': self._rx_errors,
                'crc_errors': self._crc_errors,
                'frame_errors': self._frame_errors,
                'tx_queue_size': self._tx_queue.qsize(),
                'rx_queue_size': self._rx_queue.qsize()
            }
    
    def reset_statistics(self):
        """Reset statistics counters."""
        with self._stats_lock:
            self._tx_count = 0
            self._rx_count = 0
            self._tx_errors = 0
            self._rx_errors = 0
            self._crc_errors = 0
            self._frame_errors = 0
