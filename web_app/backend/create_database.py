"""
Create the target database if it doesn't exist.
This script will create the database and grant permissions.
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from db_config import DB_CONFIG
    import mysql.connector
    from mysql.connector import Error
    
    print("=" * 60)
    print("Database Creation Script")
    print("=" * 60)
    print(f"Target Database: {DB_CONFIG['database']}")
    print(f"User: {DB_CONFIG['user']}")
    print("-" * 60)
    
    # Connect without database
    print("\n[1] Connecting to MySQL server...")
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset'],
            connect_timeout=10,
        )
        
        if conn.is_connected():
            print("[OK] Connected successfully!")
            cursor = conn.cursor()
            
            # Check if database exists
            print(f"\n[2] Checking if database '{DB_CONFIG['database']}' exists...")
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            
            if DB_CONFIG['database'] in databases:
                print(f"[INFO] Database '{DB_CONFIG['database']}' already exists")
            else:
                print(f"[INFO] Database '{DB_CONFIG['database']}' does not exist")
                print(f"\n[3] Creating database '{DB_CONFIG['database']}'...")
                try:
                    # Create database with utf8mb4 charset
                    cursor.execute(f"CREATE DATABASE `{DB_CONFIG['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    print(f"[OK] Database '{DB_CONFIG['database']}' created successfully!")
                except Error as e:
                    if e.errno == 1044:  # Access denied
                        print(f"[ERROR] Permission denied: Cannot create database")
                        print("  You may need to:")
                        print("  1. Request database creation from your DBA")
                        print("  2. Use an existing database (like 'appdb')")
                        print(f"  3. Update db_config.py to use a different database")
                    else:
                        print(f"[ERROR] Failed to create database: {e}")
                    sys.exit(1)
            
            # Test connection to the database
            print(f"\n[4] Testing connection to '{DB_CONFIG['database']}'...")
            try:
                cursor.execute(f"USE `{DB_CONFIG['database']}`")
                print(f"[OK] Successfully connected to '{DB_CONFIG['database']}'")
                print("\n[OK] Database is ready to use!")
            except Error as e:
                print(f"[ERROR] Cannot access database: {e}")
                print("  You may need to request permissions from your DBA")
                sys.exit(1)
            
            cursor.close()
            conn.close()
            print("\n" + "=" * 60)
            print("Setup complete!")
            print("=" * 60)
            
        else:
            print("[ERROR] Connection failed")
            sys.exit(1)
            
    except Error as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(1)

except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
