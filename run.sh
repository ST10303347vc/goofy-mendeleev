#!/bin/bash

# Change to the script's directory
cd "$(dirname "$0")"

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "python3 could not be found. Please install Python 3."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the Flask server
echo "Starting the application..."
echo "Access the app at: http://localhost:8000"
export FLASK_APP=backend.main
export FLASK_ENV=development
python3 -m flask run --host=0.0.0.0 --port=8000
