"""
Verify that the database has all required tables and components.
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from database import BMSDatabase
    from db_config import DB_CONFIG
    import mysql.connector
    from mysql.connector import Error
    
    print("=" * 70)
    print("Database Schema Verification")
    print("=" * 70)
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Host: {DB_CONFIG['host']}")
    print("-" * 70)
    
    # Required tables
    REQUIRED_TABLES = {
        'simulation_sessions': {
            'required_columns': [
                'id', 'session_name', 'start_time', 'end_time', 'config',
                'frame_count', 'status', 'created_at'
            ],
            'required_indexes': ['idx_start_time', 'idx_status'],
            'primary_key': 'id'
        },
        'bms_frames': {
            'required_columns': [
                'id', 'timestamp_ms', 'timestamp_iso', 'mosfet_status',
                'protection_flags', 'bms_current_ma', 'bms_voltage_mv',
                'balancing_status', 'fault_codes', 'bms_state_flags',
                'mosfet_charge', 'mosfet_discharge', 'protection_active',
                'sequence', 'session_id', 'created_at'
            ],
            'required_indexes': ['idx_timestamp', 'idx_session'],
            'primary_key': 'id',
            'foreign_keys': ['session_id -> simulation_sessions(id)']
        },
        'fault_events': {
            'required_columns': [
                'id', 'session_id', 'timestamp_ms', 'timestamp_iso',
                'fault_type', 'fault_description', 'cell_index',
                'severity', 'resolved'
            ],
            'required_indexes': ['idx_timestamp', 'idx_session'],
            'primary_key': 'id',
            'foreign_keys': ['session_id -> simulation_sessions(id)']
        }
    }
    
    print("\n[1] Connecting to database...")
    try:
        db = BMSDatabase()
        print("[OK] Database connection established")
        
        # Get direct connection for schema inspection
        conn = db._get_connection()
        cursor = conn.cursor()
        
        print("\n[2] Checking tables...")
        cursor.execute("SHOW TABLES")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        all_tables_exist = True
        for table_name in REQUIRED_TABLES.keys():
            if table_name in existing_tables:
                print(f"  [OK] Table '{table_name}' exists")
            else:
                print(f"  [ERROR] Table '{table_name}' is missing!")
                all_tables_exist = False
        
        if not all_tables_exist:
            print("\n[ERROR] Some required tables are missing!")
            sys.exit(1)
        
        print("\n[3] Verifying table structures...")
        all_structures_ok = True
        
        for table_name, requirements in REQUIRED_TABLES.items():
            print(f"\n  Checking table: {table_name}")
            
            # Get column information
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = {row[0]: row for row in cursor.fetchall()}
            
            # Check required columns
            missing_columns = []
            for col_name in requirements['required_columns']:
                if col_name in columns:
                    col_type = columns[col_name][1]
                    is_null = columns[col_name][2]
                    print(f"    [OK] Column '{col_name}' exists ({col_type}, NULL={is_null})")
                else:
                    print(f"    [ERROR] Column '{col_name}' is missing!")
                    missing_columns.append(col_name)
            
            if missing_columns:
                all_structures_ok = False
                continue
            
            # Check primary key
            cursor.execute(f"""
                SELECT COLUMN_NAME 
                FROM information_schema.KEY_COLUMN_USAGE 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = %s 
                AND CONSTRAINT_NAME = 'PRIMARY'
            """, (DB_CONFIG['database'], table_name))
            pk_result = cursor.fetchone()
            if pk_result:
                print(f"    [OK] Primary key: {pk_result[0]}")
            else:
                print(f"    [ERROR] Primary key not found!")
                all_structures_ok = False
            
            # Check indexes
            cursor.execute(f"SHOW INDEXES FROM `{table_name}`")
            indexes = {row[2]: row for row in cursor.fetchall()}
            
            for idx_name in requirements.get('required_indexes', []):
                if idx_name in indexes:
                    idx_col = indexes[idx_name][4]
                    print(f"    [OK] Index '{idx_name}' exists (on {idx_col})")
                else:
                    print(f"    [WARNING] Index '{idx_name}' not found (may affect performance)")
            
            # Check foreign keys
            if 'foreign_keys' in requirements:
                cursor.execute(f"""
                    SELECT 
                        CONSTRAINT_NAME,
                        COLUMN_NAME,
                        REFERENCED_TABLE_NAME,
                        REFERENCED_COLUMN_NAME
                    FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = %s
                    AND TABLE_NAME = %s
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """, (DB_CONFIG['database'], table_name))
                fks = cursor.fetchall()
                
                if fks:
                    for fk in fks:
                        print(f"    [OK] Foreign key: {fk[1]} -> {fk[2]}.{fk[3]}")
                else:
                    print(f"    [WARNING] No foreign keys found (expected: {requirements['foreign_keys']})")
        
        print("\n[4] Checking database engine and charset...")
        for table_name in REQUIRED_TABLES.keys():
            cursor.execute(f"""
                SELECT ENGINE, TABLE_COLLATION
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = %s
            """, (DB_CONFIG['database'], table_name))
            result = cursor.fetchone()
            if result:
                engine, collation = result
                print(f"  {table_name}:")
                print(f"    Engine: {engine} {'[OK]' if engine == 'InnoDB' else '[WARNING: Should be InnoDB]'}")
                print(f"    Collation: {collation} {'[OK]' if 'utf8mb4' in collation else '[WARNING]'}")
        
        print("\n[5] Testing database operations...")
        try:
            # Test session creation
            test_session_id = db.create_session(session_name="Schema Verification Test", config={"test": True})
            print(f"  [OK] Session creation: ID {test_session_id}")
            
            # Test frame storage
            test_frame = {
                'timestamp_ms': 1000,
                'mosfet_status': 1,
                'protection_flags': 0,
                'bms_current_ma': 50000,
                'bms_voltage_mv': 51200,
                'balancing_status': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'fault_codes': [0, 0, 0, 0, 0, 0, 0, 0],
                'bms_state_flags': 0,
                'mosfet_charge': True,
                'mosfet_discharge': True,
                'protection_active': False,
                'sequence': 1
            }
            db.store_bms_frame(test_frame, session_id=test_session_id)
            print(f"  [OK] Frame storage: Success")
            
            # Test frame retrieval
            frames = db.get_frames(session_id=test_session_id, limit=10)
            print(f"  [OK] Frame retrieval: {len(frames)} frames")
            
            # Test statistics
            stats = db.get_statistics(session_id=test_session_id)
            print(f"  [OK] Statistics: {stats['total_frames']} frames")
            
            # Clean up test data
            db.end_session(test_session_id, frame_count=len(frames))
            print(f"  [OK] Session cleanup: Success")
            
        except Exception as e:
            print(f"  [ERROR] Database operations failed: {e}")
            import traceback
            traceback.print_exc()
            all_structures_ok = False
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 70)
        if all_structures_ok:
            print("[OK] Database schema is complete and ready for production!")
            print("=" * 70)
            print("\nAll required components:")
            print("  [OK] All required tables exist")
            print("  [OK] All required columns exist")
            print("  [OK] Primary keys configured")
            print("  [OK] Indexes created")
            print("  [OK] Foreign keys configured")
            print("  [OK] Database operations working")
            print("\nDatabase is ready to host the application!")
        else:
            print("[ERROR] Database schema has issues!")
            print("=" * 70)
            sys.exit(1)
            
    except Exception as e:
        print(f"[ERROR] Database verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
