# Local Development Setup Guide

This guide explains how to run the BMS Simulator locally with online MySQL database.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LOCAL MACHINE                         │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │         React Frontend (Built Static)            │   │
│  │         Served by Flask                          │   │
│  └──────────────────────────────────────────────────┘   │
│                        ↕ HTTP/WebSocket                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Flask Backend (Python)                    │   │
│  │         - REST API                               │   │
│  │         - WebSocket (SocketIO)                   │   │
│  │         - Simulation Engine                     │   │
│  └──────────────────────────────────────────────────┘   │
│                        ↕                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │         UART/USB Hardware Interface              │   │
│  │         - BidirectionalUART                      │   │
│  │         - Direct Serial Port Access              │   │
│  └──────────────────────────────────────────────────┘   │
│                        ↕                                │
│              [BMS Hardware via USB/UART]               │
└─────────────────────────────────────────────────────────┘
                        ↕ MySQL Connection
┌─────────────────────────────────────────────────────────┐
│              ONLINE CLOUD (MySQL)                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │         MySQL Database (148.113.31.152)         │   │
│  │         - simulation_sessions                    │   │
│  │         - bms_frames                              │   │
│  │         - fault_events                            │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.8 or higher
- Node.js 18+ and npm (for frontend build)
- Serial port access (for UART communication with BMS hardware)
- Internet connection (for MySQL database)

## Installation Steps

### 1. Clone and Navigate to Project

```bash
cd "Battery Pack Simulator"
```

### 2. Create Python Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
pip install -r web_app/backend/requirements.txt
```

### 4. Build Frontend

```bash
cd web_app/frontend
npm install
npm run build
cd ../..
```

The built frontend will be in `web_app/frontend/build/` and will be served by Flask.

### 5. Configure Database (Optional)

The application is pre-configured to use the online MySQL database. If you need to override settings, create a `.env` file:

**Windows:**
```bash
cd web_app\backend
copy .env.example .env
```

**Linux/Mac:**
```bash
cd web_app/backend
cp .env.example .env
```

Edit `.env` with your database credentials if needed:
```env
DB_HOST=148.113.31.152
DB_PORT=3306
DB_NAME=appdb
DB_USER=bms-hil
DB_PASSWORD=Pearl@123
DB_SECONDARY_HOST=148.113.31.149
```

## Running the Application

### Option 1: Using Startup Scripts

**Windows:**
```bash
web_app\backend\start_backend.bat
```

**Linux/Mac:**
```bash
chmod +x web_app/backend/start_backend.sh
./web_app/backend/start_backend.sh
```

### Option 2: Manual Start

```bash
cd web_app/backend
python app.py
```

The application will start on:
- **Backend API:** http://localhost:5000
- **Frontend:** http://localhost:5000 (served by Flask)
- **WebSocket:** ws://localhost:5000/socket.io

## Accessing the Application

1. Open your web browser
2. Navigate to: http://localhost:5000
3. The React frontend will be served automatically

## UART Hardware Connection

To connect to BMS hardware via UART:

1. **Find your serial port:**
   - Windows: Check Device Manager for COM ports (e.g., COM3, COM4)
   - Linux: Check `/dev/ttyUSB*` or `/dev/ttyACM*`
   - Mac: Check `/dev/cu.*` or `/dev/tty.*`

2. **Configure in Web UI:**
   - Go to Simulation Configuration
   - Enter your serial port (e.g., `COM3` or `/dev/ttyUSB0`)
   - Set baud rate (default: 921600)
   - Enable bidirectional communication if needed

3. **Or use API:**
   ```bash
   POST http://localhost:5000/api/simulation/start
   {
     "uart_port": "COM3",
     "baudrate": 921600,
     "bidirectional": true,
     "frame_rate_hz": 50.0
   }
   ```

## Database Configuration

The application uses an online MySQL database by default. Configuration is in `web_app/backend/db_config.py`:

- **Primary Host:** 148.113.31.152:3306
- **Database:** appdb
- **User:** bms-hil
- **Secondary Host:** 148.113.31.149 (failover)

All simulation data (sessions, frames, fault events) is stored in the cloud database.

## Troubleshooting

### Port Already in Use

If port 5000 is already in use:

```bash
# Windows: Find process using port 5000
netstat -ano | findstr :5000

# Linux/Mac: Find process using port 5000
lsof -i :5000
```

Kill the process or change the port in `app.py`:
```python
socketio.run(app, host='0.0.0.0', port=5001, ...)
```

### Serial Port Access Issues

**Windows:**
- Check Device Manager for COM port
- Ensure port is not in use by another application
- Try running as Administrator if permission issues

**Linux:**
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER
# Log out and back in, or:
newgrp dialout
```

**Mac:**
- Check System Preferences > Security & Privacy
- Grant terminal access to serial ports

### Database Connection Issues

1. **Check internet connection**
2. **Verify database credentials** in `.env` or `db_config.py`
3. **Test connection:**
   ```bash
   cd web_app/backend
   python test_db_connection.py
   ```

### Frontend Not Loading

1. **Ensure frontend is built:**
   ```bash
   cd web_app/frontend
   npm run build
   ```

2. **Check build directory exists:**
   - Should have `web_app/frontend/build/index.html`

3. **Check Flask static folder configuration** in `app.py`:
   ```python
   app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
   ```

### Import Errors

If you see import errors:

```bash
# Ensure you're in the project root
cd "Battery Pack Simulator"

# Verify Python path includes project
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
pip install -r web_app/backend/requirements.txt --force-reinstall
```

## Development Workflow

### Making Frontend Changes

1. Edit files in `web_app/frontend/src/`
2. Rebuild:
   ```bash
   cd web_app/frontend
   npm run build
   ```
3. Restart Flask backend to serve new build

### Making Backend Changes

1. Edit files in `web_app/backend/`
2. Restart Flask backend (auto-reloads in debug mode)

### Testing UART Communication

1. Start the application
2. Configure simulation with UART port
3. Check logs in `web_app/backend/logs/runtime_errors.log`
4. Monitor serial port activity

## File Structure

```
Battery Pack Simulator/
├── web_app/
│   ├── backend/
│   │   ├── app.py              # Flask server (serves frontend + API)
│   │   ├── db_config.py        # MySQL config (online)
│   │   ├── database.py         # MySQL connection
│   │   ├── .env                # Optional: DB credentials
│   │   ├── start_backend.bat   # Windows startup script
│   │   └── start_backend.sh    # Linux/Mac startup script
│   └── frontend/
│       ├── src/                # React source code
│       └── build/              # Built React app (served by Flask)
├── pc_simulator/               # Simulation modules
└── scenarios/                  # Fault scenarios
```

## Production Deployment (Optional)

For production, consider:

1. **Use a production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Use nginx as reverse proxy** (optional)

3. **Set up process management:**
   - Windows: Task Scheduler or NSSM
   - Linux: systemd service
   - Mac: launchd

4. **Environment variables:**
   - Use `.env` file for sensitive credentials
   - Never commit `.env` to version control

## Support

For issues or questions:
- Check logs: `web_app/backend/logs/runtime_errors.log`
- API health: http://localhost:5000/api/health
- Database connection: Run `test_db_connection.py`
