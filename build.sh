#!/bin/bash
set -e

# Load environment variables from the .env file if it exists.
if [ -f .env ]; then
  # Read the .env file, removes comments/empty lines, and exports the variables.
  export $(cat .env | sed 's/#.*//g' | xargs)
fi

# Define and export build-time variables directly.
export SOURCE_FILE=${SOURCE_FILE:-test_file.txt}
export CACHE_FILE=${CACHE_FILE:-test_file.txt.index}

# Check if the Docker daemon is running else start it
sudo systemctl is-active --quiet docker || sudo systemctl start docker >&2

echo "Building Docker image"

# Run the docker compose command with sudo to handle permissions
sudo -E docker compose build

echo "Docker image built successfully."
