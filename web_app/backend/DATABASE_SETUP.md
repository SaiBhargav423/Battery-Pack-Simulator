# MySQL Database Setup

This application now uses MySQL instead of SQLite for storing BMS data.

## Setup Instructions

### 1. Install Dependencies

```bash
cd web_app/backend
pip install -r requirements.txt
```

This will install:
- `mysql-connector-python` - MySQL database connector
- `python-dotenv` - Environment variable management

### 2. Configure Database Connection

Create a `.env` file in the `web_app/backend/` directory with the following content:

```bash
# MySQL Database Configuration

# Primary database host
DB_HOST=148.113.31.152

# Database port
DB_PORT=3306

# Database name
DB_NAME=mysql-84661-25809837-b1a0

# Database username (REQUIRED - set this)
DB_USER=your_username_here

# Database password (REQUIRED - set this)
DB_PASSWORD=your_password_here

# Secondary database host (for failover)
DB_SECONDARY_HOST=148.113.31.149
```

**Important:** Replace `your_username_here` and `your_password_here` with your actual MySQL credentials.

### 3. Database Schema

The database schema will be automatically created when you first run the application. The following tables will be created:

- `bms_frames` - Stores BMS response frames
- `simulation_sessions` - Stores simulation session metadata
- `fault_events` - Stores fault event records

### 4. Connection Features

- **Connection Pooling**: Uses MySQL connection pooling for better performance
- **Failover Support**: Automatically tries secondary host if primary fails
- **Thread-Safe**: All database operations are thread-safe
- **Error Handling**: Graceful error handling with automatic retry on secondary host

### 5. Testing the Connection

After setting up the `.env` file, start the backend server:

```bash
cd web_app/backend
python app.py
```

You should see:
```
[DB] Loaded environment variables from ...
[DB] Connection pool initialized: 5 connections
[DB] Database schema initialized successfully
```

### 6. Troubleshooting

**Connection Errors:**
- Verify your database credentials in `.env`
- Check that the database server is accessible from your network
- Ensure the database name exists on the MySQL server
- Check firewall rules allow connections on port 3306

**Import Errors:**
- Make sure `mysql-connector-python` is installed: `pip install mysql-connector-python`
- Make sure `python-dotenv` is installed: `pip install python-dotenv`

**Schema Errors:**
- The schema will be created automatically on first run
- If tables already exist, the application will use them
- Foreign key constraints require InnoDB engine (default)

### 7. Security Notes

- **Never commit `.env` file to version control** - it contains sensitive credentials
- The `.env` file is already added to `.gitignore`
- Use strong passwords for database access
- Consider using database user with minimal required permissions
