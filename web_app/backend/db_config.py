"""
Database configuration for MySQL connection.
Store credentials securely using environment variables or config file.
"""
import os
from pathlib import Path

# Try to load from .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[DB] Loaded environment variables from {env_path}")
except ImportError:
    pass

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '148.113.31.152'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'database': os.getenv('DB_NAME', 'appdb'),  # Using 'appdb' as user has full access
    'user': os.getenv('DB_USER', 'bms-hil'),
    'password': os.getenv('DB_PASSWORD', 'Pearl@123'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': False,
    'connect_timeout': 10,
    'pool_size': 5,
    'pool_reset_session': True,
}

# Alternative host (for failover)
DB_SECONDARY_HOST = os.getenv('DB_SECONDARY_HOST', '148.113.31.149')
