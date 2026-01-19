#!/bin/bash
set -e

# Define marker file path
MARKER_FILE="/app/.db_initialized"

# Check if DB needs initialization
if [ ! -f "$MARKER_FILE" ]; then
    echo "First run detected. Initializing database..."
    echo "Waiting for MariaDB to start..."
    sleep 30
    python -m app.utils.initDB
    
    # Create marker file
    touch "$MARKER_FILE"
    echo "Database initialized."
else
    echo "Database already initialized. Skipping init."
fi

# Execute the command passed to docker run
exec "$@"
