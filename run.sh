#!/bin/bash

# --- TradeLM AI Microservice Execution Script ---

# 1. Activate the Python Virtual Environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment 'venv' not found. Please run ./install.sh first."
    exit 1
fi

# 2. Set environment variables (for pydantic-settings to load)
if [ -f .env ]; then
    echo "Loading environment variables from .env"
    export $(grep -v '^#' .env | xargs)
fi

# 3. Start the Uvicorn server on the dedicated port (8001)
# The application module is at app.main:app
echo "Starting FastAPI AI Microservice (http://0.0.0.0:8001)..."
uvicorn main:app --app-dir app --host 0.0.0.0 --port ${PORT:-8001} --reload

# Deactivate the environment when done
deactivate