"""
Verify that the application is using MySQL instead of SQLite.
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("Verifying MySQL Switch from SQLite")
print("=" * 70)

# Check database.py
print("\n[1] Checking database.py...")
try:
    with open('database.py', 'r') as f:
        content = f.read()
        
    if 'mysql.connector' in content:
        print("  [OK] Uses mysql.connector")
    else:
        print("  [ERROR] mysql.connector not found!")
        
    if 'sqlite3' in content:
        print("  [ERROR] Still contains sqlite3 references!")
    else:
        print("  [OK] No sqlite3 references")
        
    if 'BMSDatabase' in content and 'MySQL' in content:
        print("  [OK] BMSDatabase class is MySQL-based")
        
except Exception as e:
    print(f"  [ERROR] Could not read database.py: {e}")

# Check app.py
print("\n[2] Checking app.py...")
try:
    with open('app.py', 'r') as f:
        content = f.read()
        
    if 'from database import BMSDatabase' in content:
        print("  [OK] Imports BMSDatabase from database module")
    else:
        print("  [ERROR] Does not import BMSDatabase!")
        
    if 'bms_db = BMSDatabase()' in content:
        print("  [OK] Initializes BMSDatabase instance")
    else:
        print("  [ERROR] Does not initialize BMSDatabase!")
        
    if 'sqlite3' in content.lower():
        print("  [WARNING] Contains sqlite3 references (may be in comments)")
    else:
        print("  [OK] No sqlite3 references")
        
except Exception as e:
    print(f"  [ERROR] Could not read app.py: {e}")

# Test actual import
print("\n[3] Testing actual database import...")
try:
    from database import BMSDatabase
    import database
    
    # Check what the module actually imports
    if hasattr(database, 'mysql'):
        print("  [OK] mysql.connector is imported")
    else:
        print("  [WARNING] Could not verify mysql.connector import")
    
    if hasattr(database, 'sqlite3'):
        print("  [ERROR] sqlite3 is still imported!")
    else:
        print("  [OK] sqlite3 is not imported")
    
    # Check class docstring
    if 'MySQL' in BMSDatabase.__doc__:
        print("  [OK] BMSDatabase class is documented as MySQL")
    else:
        print("  [WARNING] BMSDatabase docstring doesn't mention MySQL")
    
    # Try to initialize (this will connect to MySQL)
    print("\n[4] Testing database initialization...")
    try:
        db = BMSDatabase()
        print("  [OK] Database initialized successfully")
        print(f"  [OK] Using MySQL database: {db._get_connection().database}")
        print("  [OK] Application is using MySQL!")
    except Exception as e:
        print(f"  [ERROR] Database initialization failed: {e}")
        print("  This may indicate MySQL connection issues")
        
except ImportError as e:
    print(f"  [ERROR] Could not import database module: {e}")
except Exception as e:
    print(f"  [ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Verification Complete")
print("=" * 70)
