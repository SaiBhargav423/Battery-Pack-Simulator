"""
MySQL Database Module for BMS Data Storage and Analysis

Stores BMS response frames received via bidirectional UART communication.
Provides querying and analysis capabilities.
"""

import mysql.connector
from mysql.connector import pooling, Error
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
import threading
from db_config import DB_CONFIG, DB_SECONDARY_HOST


class BMSDatabase:
    """MySQL database for storing BMS data."""
    
    _connection_pool = None
    _pool_lock = threading.Lock()
    
    def __init__(self, use_pooling: bool = True):
        """
        Initialize BMS database.
        
        Args:
            use_pooling: Use connection pooling for better performance
        """
        self.use_pooling = use_pooling
        self.lock = threading.Lock()
        self._init_connection_pool()
        try:
            self._init_database()
        except Exception as e:
            print(f"[ERROR] Failed to initialize database: {e}")
            raise
    
    def _init_connection_pool(self):
        """Initialize MySQL connection pool."""
        if not self.use_pooling:
            return
            
        with self._pool_lock:
            if self._connection_pool is None:
                try:
                    pool_config = {
                        'pool_name': 'bms_pool',
                        'pool_size': DB_CONFIG.get('pool_size', 5),
                        'pool_reset_session': DB_CONFIG.get('pool_reset_session', True),
                        'host': DB_CONFIG['host'],
                        'port': DB_CONFIG['port'],
                        'database': DB_CONFIG['database'],
                        'user': DB_CONFIG['user'],
                        'password': DB_CONFIG['password'],
                        'charset': DB_CONFIG['charset'],
                        'autocommit': DB_CONFIG.get('autocommit', False),
                        'connect_timeout': DB_CONFIG.get('connect_timeout', 10),
                    }
                    self._connection_pool = pooling.MySQLConnectionPool(**pool_config)
                    print(f"[DB] Connection pool initialized: {pool_config['pool_size']} connections")
                except Error as e:
                    print(f"[DB] Failed to create connection pool: {e}")
                    self._connection_pool = None
    
    def _get_connection(self):
        """Get database connection from pool or create new one."""
        if self.use_pooling and self._connection_pool:
            try:
                return self._connection_pool.get_connection()
            except Error as e:
                print(f"[DB] Pool connection failed, trying direct: {e}")
        
        # Fallback to direct connection
        try:
            return mysql.connector.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                database=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset'],
                autocommit=DB_CONFIG.get('autocommit', False),
                connect_timeout=DB_CONFIG.get('connect_timeout', 10),
            )
        except Error as e:
            # Try secondary host
            print(f"[DB] Primary host failed, trying secondary: {e}")
            try:
                return mysql.connector.connect(
                    host=DB_SECONDARY_HOST,
                    port=DB_CONFIG['port'],
                    database=DB_CONFIG['database'],
                    user=DB_CONFIG['user'],
                    password=DB_CONFIG['password'],
                    charset=DB_CONFIG['charset'],
                    autocommit=DB_CONFIG.get('autocommit', False),
                    connect_timeout=DB_CONFIG.get('connect_timeout', 10),
                )
            except Error as e2:
                print(f"[DB] Secondary host also failed: {e2}")
                raise
    
    def _init_database(self):
        """Initialize database schema."""
        with self.lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Create simulation_sessions table FIRST (no foreign keys)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS simulation_sessions (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        session_name VARCHAR(255),
                        start_time VARCHAR(50) NOT NULL,
                        end_time VARCHAR(50),
                        config TEXT,
                        frame_count INT DEFAULT 0,
                        status VARCHAR(20) DEFAULT 'running',
                        created_at VARCHAR(50) NOT NULL,
                        INDEX idx_start_time (start_time),
                        INDEX idx_status (status)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Create bms_frames table (references simulation_sessions)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bms_frames (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        timestamp_ms BIGINT NOT NULL,
                        timestamp_iso VARCHAR(50) NOT NULL,
                        mosfet_status INT NOT NULL,
                        protection_flags INT NOT NULL,
                        bms_current_ma INT NOT NULL,
                        bms_voltage_mv INT NOT NULL,
                        balancing_status TEXT NOT NULL,
                        fault_codes TEXT NOT NULL,
                        bms_state_flags INT NOT NULL,
                        mosfet_charge TINYINT NOT NULL,
                        mosfet_discharge TINYINT NOT NULL,
                        protection_active TINYINT NOT NULL,
                        sequence INT,
                        session_id INT,
                        created_at VARCHAR(50) NOT NULL,
                        INDEX idx_timestamp (timestamp_ms),
                        INDEX idx_session (session_id),
                        FOREIGN KEY (session_id) REFERENCES simulation_sessions(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Create fault_events table (references simulation_sessions)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS fault_events (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        session_id INT,
                        timestamp_ms BIGINT NOT NULL,
                        timestamp_iso VARCHAR(50) NOT NULL,
                        fault_type VARCHAR(100) NOT NULL,
                        fault_description TEXT,
                        cell_index INT,
                        severity VARCHAR(20),
                        resolved TINYINT DEFAULT 0,
                        INDEX idx_timestamp (timestamp_ms),
                        INDEX idx_session (session_id),
                        FOREIGN KEY (session_id) REFERENCES simulation_sessions(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Check if session_id column exists in bms_frames (migration)
                cursor.execute('''
                    SELECT COUNT(*) 
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = %s 
                    AND TABLE_NAME = 'bms_frames' 
                    AND COLUMN_NAME = 'session_id'
                ''', (DB_CONFIG['database'],))
                
                if cursor.fetchone()[0] == 0:
                    print("[DB] Adding session_id column to bms_frames table...")
                    cursor.execute('''
                        ALTER TABLE bms_frames 
                        ADD COLUMN session_id INT,
                        ADD INDEX idx_bms_frames_session (session_id)
                    ''')
                
                conn.commit()
                print("[DB] Database schema initialized successfully")
                
            except Error as e:
                if conn:
                    conn.rollback()
                print(f"[DB] Error initializing database: {e}")
                raise
            finally:
                if conn and conn.is_connected():
                    cursor.close()
                    conn.close()
    
    def create_session(self, session_name: Optional[str] = None, config: Optional[Dict] = None) -> int:
        """Create a new simulation session."""
        with self.lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                now = datetime.utcnow().isoformat()
                config_json = json.dumps(config) if config else None
                
                cursor.execute('''
                    INSERT INTO simulation_sessions 
                    (session_name, start_time, config, created_at)
                    VALUES (%s, %s, %s, %s)
                ''', (session_name, now, config_json, now))
                
                session_id = cursor.lastrowid
                conn.commit()
                return session_id
            except Error as e:
                if conn:
                    conn.rollback()
                print(f"[DB] Error creating session: {e}")
                raise
            finally:
                if conn and conn.is_connected():
                    cursor.close()
                    conn.close()
    
    def end_session(self, session_id: int, frame_count: int = 0):
        """End a simulation session."""
        with self.lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                now = datetime.utcnow().isoformat()
                cursor.execute('''
                    UPDATE simulation_sessions 
                    SET end_time = %s, frame_count = %s, status = 'completed'
                    WHERE id = %s
                ''', (now, frame_count, session_id))
                
                conn.commit()
            except Error as e:
                if conn:
                    conn.rollback()
                print(f"[DB] Error ending session: {e}")
                raise
            finally:
                if conn and conn.is_connected():
                    cursor.close()
                    conn.close()
    
    def store_bms_frame(self, bms_data: Dict[str, Any], session_id: Optional[int] = None):
        """Store BMS frame data."""
        with self.lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                timestamp_ms = bms_data.get('timestamp_ms', 0)
                timestamp_iso = datetime.utcnow().isoformat()
                
                # Convert numpy arrays to JSON strings
                balancing_status = json.dumps(
                    bms_data.get('balancing_status', []).tolist() 
                    if isinstance(bms_data.get('balancing_status'), np.ndarray)
                    else bms_data.get('balancing_status', [])
                )
                
                fault_codes = json.dumps(
                    bms_data.get('fault_codes', []).tolist()
                    if isinstance(bms_data.get('fault_codes'), np.ndarray)
                    else bms_data.get('fault_codes', [])
                )
                
                cursor.execute('''
                    INSERT INTO bms_frames (
                        timestamp_ms, timestamp_iso, mosfet_status, protection_flags,
                        bms_current_ma, bms_voltage_mv, balancing_status, fault_codes,
                        bms_state_flags, mosfet_charge, mosfet_discharge, protection_active,
                        sequence, session_id, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    timestamp_ms,
                    timestamp_iso,
                    bms_data.get('mosfet_status', 0),
                    bms_data.get('protection_flags', 0),
                    bms_data.get('bms_current_ma', 0),
                    bms_data.get('bms_voltage_mv', 0),
                    balancing_status,
                    fault_codes,
                    bms_data.get('bms_state_flags', 0),
                    1 if bms_data.get('mosfet_charge', False) else 0,
                    1 if bms_data.get('mosfet_discharge', False) else 0,
                    1 if bms_data.get('protection_active', False) else 0,
                    bms_data.get('sequence'),
                    session_id,
                    timestamp_iso
                ))
                
                conn.commit()
            except Error as e:
                if conn:
                    conn.rollback()
                print(f"[DB] Error storing BMS frame: {e}")
                # Don't raise - continue simulation even if storage fails
            finally:
                if conn and conn.is_connected():
                    cursor.close()
                    conn.close()
    
    def get_frames(
        self,
        session_id: Optional[int] = None,
        start_time_ms: Optional[int] = None,
        end_time_ms: Optional[int] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Query BMS frames."""
        with self.lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor(dictionary=True)  # Returns dict instead of tuple
                
                query = 'SELECT * FROM bms_frames WHERE 1=1'
                params = []
                
                if session_id:
                    query += ' AND session_id = %s'
                    params.append(session_id)
                
                if start_time_ms:
                    query += ' AND timestamp_ms >= %s'
                    params.append(start_time_ms)
                
                if end_time_ms:
                    query += ' AND timestamp_ms <= %s'
                    params.append(end_time_ms)
                
                query += ' ORDER BY timestamp_ms DESC LIMIT %s'
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                frames = []
                for row in rows:
                    frame = dict(row)
                    # Parse JSON fields
                    if frame.get('balancing_status'):
                        frame['balancing_status'] = json.loads(frame['balancing_status'])
                    if frame.get('fault_codes'):
                        frame['fault_codes'] = json.loads(frame['fault_codes'])
                    frames.append(frame)
                
                return frames
            except Error as e:
                print(f"[DB] Error getting frames: {e}")
                return []
            finally:
                if conn and conn.is_connected():
                    cursor.close()
                    conn.close()
    
    def get_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of simulation sessions."""
        with self.lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor(dictionary=True)
                
                cursor.execute('''
                    SELECT * FROM simulation_sessions 
                    ORDER BY start_time DESC 
                    LIMIT %s
                ''', (limit,))
                
                rows = cursor.fetchall()
                sessions = []
                for row in rows:
                    session = dict(row)
                    if session.get('config'):
                        session['config'] = json.loads(session['config'])
                    sessions.append(session)
                
                return sessions
            except Error as e:
                print(f"[DB] Error getting sessions: {e}")
                return []
            finally:
                if conn and conn.is_connected():
                    cursor.close()
                    conn.close()
    
    def get_statistics(self, session_id: Optional[int] = None) -> Dict[str, Any]:
        """Get statistics for BMS data."""
        with self.lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                if session_id:
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total_frames,
                            MIN(timestamp_ms) as min_timestamp,
                            MAX(timestamp_ms) as max_timestamp,
                            AVG(bms_current_ma) as avg_current,
                            AVG(bms_voltage_mv) as avg_voltage,
                            SUM(CASE WHEN protection_active = 1 THEN 1 ELSE 0 END) as protection_events,
                            SUM(CASE WHEN mosfet_charge = 0 THEN 1 ELSE 0 END) as charge_mosfet_opens,
                            SUM(CASE WHEN mosfet_discharge = 0 THEN 1 ELSE 0 END) as discharge_mosfet_opens
                        FROM bms_frames
                        WHERE session_id = %s
                    ''', (session_id,))
                else:
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total_frames,
                            MIN(timestamp_ms) as min_timestamp,
                            MAX(timestamp_ms) as max_timestamp,
                            AVG(bms_current_ma) as avg_current,
                            AVG(bms_voltage_mv) as avg_voltage,
                            SUM(CASE WHEN protection_active = 1 THEN 1 ELSE 0 END) as protection_events,
                            SUM(CASE WHEN mosfet_charge = 0 THEN 1 ELSE 0 END) as charge_mosfet_opens,
                            SUM(CASE WHEN mosfet_discharge = 0 THEN 1 ELSE 0 END) as discharge_mosfet_opens
                        FROM bms_frames
                    ''')
                
                row = cursor.fetchone()
                
                if row:
                    return {
                        'total_frames': row[0] or 0,
                        'min_timestamp_ms': row[1],
                        'max_timestamp_ms': row[2],
                        'avg_current_ma': float(row[3]) if row[3] else 0.0,
                        'avg_voltage_mv': float(row[4]) if row[4] else 0.0,
                        'protection_events': row[5] or 0,
                        'charge_mosfet_opens': row[6] or 0,
                        'discharge_mosfet_opens': row[7] or 0
                    }
                else:
                    return {
                        'total_frames': 0,
                        'min_timestamp_ms': None,
                        'max_timestamp_ms': None,
                        'avg_current_ma': 0.0,
                        'avg_voltage_mv': 0.0,
                        'protection_events': 0,
                        'charge_mosfet_opens': 0,
                        'discharge_mosfet_opens': 0
                    }
            except Error as e:
                print(f"[DB] Error getting statistics: {e}")
                return {
                    'total_frames': 0,
                    'min_timestamp_ms': None,
                    'max_timestamp_ms': None,
                    'avg_current_ma': 0.0,
                    'avg_voltage_mv': 0.0,
                    'protection_events': 0,
                    'charge_mosfet_opens': 0,
                    'discharge_mosfet_opens': 0
                }
            finally:
                if conn and conn.is_connected():
                    cursor.close()
                    conn.close()
    
    def export_to_csv(self, session_id: Optional[int] = None, output_path: str = "bms_export.csv") -> str:
        """Export BMS data to CSV."""
        import csv
        
        frames = self.get_frames(session_id=session_id, limit=100000)
        
        if not frames:
            raise ValueError("No data to export")
        
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = [
                'timestamp_ms', 'timestamp_iso', 'mosfet_status', 'protection_flags',
                'bms_current_ma', 'bms_voltage_mv', 'mosfet_charge', 'mosfet_discharge',
                'protection_active', 'sequence'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for frame in frames:
                writer.writerow({
                    'timestamp_ms': frame['timestamp_ms'],
                    'timestamp_iso': frame['timestamp_iso'],
                    'mosfet_status': frame['mosfet_status'],
                    'protection_flags': frame['protection_flags'],
                    'bms_current_ma': frame['bms_current_ma'],
                    'bms_voltage_mv': frame['bms_voltage_mv'],
                    'mosfet_charge': frame['mosfet_charge'],
                    'mosfet_discharge': frame['mosfet_discharge'],
                    'protection_active': frame['protection_active'],
                    'sequence': frame.get('sequence', '')
                })
        
        return output_path
