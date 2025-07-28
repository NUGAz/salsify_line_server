#!/bin/bash
set -e

# Load environment variables from the .env file.
if [ -f .env ]; then
  export $(cat .env | sed 's/#.*//g' | xargs)
fi

if [ -z "$1" ]; then
    echo "Error: Please provide the path to the file to be served."
    echo "Usage: $0 <filepath>"
    exit 1
fi

export SOURCE_FILE=$1
export CACHE_FILE=${SOURCE_FILE}.index

touch "$CACHE_FILE"

# --- New Step: Pre-build the index ---
echo "--- Checking/Building Index Cache ---"
python3 build_cache.py "$SOURCE_FILE" "$CACHE_FILE"
echo "--- Cache Check Complete ---"

# (Docker daemon check remains the same)
if ! sudo systemctl is-active --quiet docker; then
    echo "Docker service is not running, attempting to start..."
    sudo systemctl start docker
fi

echo "Starting server for file: $SOURCE_FILE..."
sudo -E docker compose up --build