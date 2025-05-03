#!/bin/bash
set -e

# Make data directory if it doesn't exist
mkdir -p /app/data

# Set database path to the mounted volume
export DATABASE_URL=${DATABASE_URL:-sqlite:///./data/email_assistant.db}

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 