#!/bin/bash
# Linux/Mac startup script for BMS Simulator Backend
# This script starts the Flask backend server locally

echo "========================================"
echo "BMS Simulator - Local Backend Server"
echo "========================================"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Check if virtual environment exists
if [ -f "../../venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "../../venv/bin/activate"
fi

# Check if dependencies are installed
$PYTHON_CMD -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "WARNING: Flask not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if frontend is built
if [ ! -f "../frontend/build/index.html" ]; then
    echo "WARNING: Frontend not built. Building now..."
    cd ../frontend
    npm install
    npm run build
    cd ../backend
fi

echo ""
echo "Starting Flask backend server..."
echo "Backend will be available at: http://localhost:5000"
echo "Frontend will be available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Flask application
$PYTHON_CMD app.py
