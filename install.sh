#!/bin/bash

# --- TradeLM AI Microservice Setup Script ---
# Sets up the Python virtual environment and installs dependencies.

echo "Starting TradeLM AI Microservice setup..."

# 1. Create a Python Virtual Environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment 'venv'..."
    python3 -m venv venv
fi

# 2. Activate the Virtual Environment
echo "Activating virtual environment..."
source venv/bin/activate

# 3. Upgrade pip and install dependencies
echo "Upgrading pip and installing core dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Check installation status
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ AI Microservice setup complete. To run, use: ./run.sh"
else
    echo ""
    echo "❌ ERROR: Dependency installation failed. Please check ai-microservice/requirements.txt."
    exit 1
fi

deactivate