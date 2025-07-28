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

CACHE_DIR=".cache"
# Create the cache directory if it doesn't exist
mkdir -p "$CACHE_DIR"
# Create a unique cache file name based on the source file's base name
BASENAME=$(basename "$SOURCE_FILE")

export CACHE_FILE="${CACHE_DIR}/${BASENAME}.index"
touch "$CACHE_FILE"

echo "--- Checking/Building Index Cache ---"
python3 build_cache.py "$SOURCE_FILE" "$CACHE_FILE"
echo "--- Cache Check Complete ---"

# (Docker daemon check remains the same)
if ! sudo systemctl is-active --quiet docker; then
    echo "Docker service is not running, attempting to start..."
    sudo systemctl start docker
fi

echo "Starting server fower file: $SOURCE_FILE..."
sudo -E docker compose up --build