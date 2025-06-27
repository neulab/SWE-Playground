#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the project root (parent of scripts directory)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

# Debug info
echo "Script directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT"
echo "Looking for .env at: $ENV_FILE"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    echo "Please create a .env file in the project root directory"
    return 1 2>/dev/null || exit 1
fi

echo "Loading environment variables from $ENV_FILE"

# Enable automatic export of variables
set -a
# Source the .env file
. "$ENV_FILE"
# Disable automatic export
set +a

echo "Environment variables loaded successfully"