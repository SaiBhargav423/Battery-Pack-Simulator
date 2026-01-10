# BMS Simulator Web Application

Master control panel for Battery Management System simulation with modular, hierarchical UI design.

## Architecture

```
web_app/
├── backend/
│   ├── app.py              # Flask API server with WebSocket support
│   └── requirements.txt    # Backend dependencies
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Dashboard.jsx          # Main layout with side navigation
    │   │   ├── Configuration.jsx      # Battery pack & simulation config
    │   │   ├── SimulationControl.jsx  # Start/stop/pause controls
    │   │   ├── Monitoring.jsx         # Real-time charts & cell status
    │   │   └── Analysis.jsx           # Test reports & data export
    │   ├── App.jsx                    # Main app with routing
    │   └── main.jsx                   # Entry point
    ├── package.json
    └── vite.config.js
```

## Features

### Modular Layout
- **Dashboard**: Side navigation with 4 main modules
- **Configuration**: Collapsible accordions for organized settings
- **Simulation Control**: Large, prominent action buttons
- **Monitoring**: Real-time charts with responsive grid layout
- **Analysis**: Report generation and data export

### Visual Hierarchy
- Critical actions (Start/Stop) use large, colored buttons
- Status indicators use color-coded chips (green=good, red=error)
- Real-time data prominently displayed in cards
- Collapsible sections prevent information overload

## Installation

### Backend

```bash
cd web_app/backend
pip install -r requirements.txt
```

### Frontend

```bash
cd web_app/frontend
npm install
```

## Running

### Start Backend Server

**Windows:**
```bash
cd web_app
start_backend.bat
```

**Linux/Mac:**
```bash
cd web_app
chmod +x start_backend.sh
./start_backend.sh
```

**Or manually:**
```bash
cd web_app/backend
python app.py
```

Backend runs on `http://localhost:5000`

### Start Frontend Development Server

```bash
cd web_app/frontend
npm run dev
```

Frontend runs on `http://localhost:3000`

## Usage

1. **Configuration**: Set up battery pack parameters, communication settings, and fault scenarios
2. **Simulation Control**: Start simulation with saved configuration
3. **Monitoring**: Watch real-time data streams with live charts
4. **Analysis**: Generate reports and export data (coming soon)

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/simulation/status` - Get simulation status
- `POST /api/simulation/start` - Start simulation
- `POST /api/simulation/stop` - Stop simulation
- `POST /api/simulation/pause` - Pause simulation
- `POST /api/simulation/resume` - Resume simulation
- `GET /api/config/default` - Get default configuration
- `GET /api/fault-scenarios` - List available fault scenarios

## WebSocket Events

- `simulation_data` - Real-time simulation data
- `simulation_status` - Status updates
- `simulation_stopped` - Simulation completion notification
