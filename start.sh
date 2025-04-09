#!/bin/bash
# KAG System Startup Script (Connect to existing vLLM)

set -e

echo "==== Starting KAG System (Using existing vLLM) ===="

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: No active virtual environment detected."
    echo "It's recommended to run this script inside a virtual environment with all dependencies installed."
    echo "Continuing anyway..."
    
    # Activate the virtual environment if it exists
    if [ -d "kag_venv" ]; then
        echo "Found kag_venv directory. Activating..."
        source kag_venv/bin/activate
    fi
else
    echo "Using virtual environment: $VIRTUAL_ENV"
fi

# Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
fi

# Create the required directories
mkdir -p kag/document_processor
mkdir -p kag/kv_cache
mkdir -p kag/query
mkdir -p kag/server
mkdir -p kag/user
mkdir -p kag/utils

# Create empty __init__.py files if they don't exist
touch kag/__init__.py
touch kag/document_processor/__init__.py
touch kag/kv_cache/__init__.py
touch kag/query/__init__.py
touch kag/server/__init__.py
touch kag/user/__init__.py
touch kag/utils/__init__.py

# Parse arguments
VLLM_HOST="localhost"  # Host where LLM server is running
VLLM_PORT=11434        # Port where LLM server is running
KAG_HOST="0.0.0.0"     # KAG will listen on all interfaces
KAG_PORT=11435         # KAG will use a different port (11435)
PROXY_MODE=true        # Run in proxy mode to use existing LLM server
LLM_TYPE="vllm"        # Default LLM type: vllm or ollama

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --vllm-host)
        VLLM_HOST="$2"
        shift
        shift
        ;;
        --vllm-port)
        VLLM_PORT="$2"
        shift
        shift
        ;;
        --kag-host)
        KAG_HOST="$2"
        shift
        shift
        ;;
        --kag-port)
        KAG_PORT="$2"
        shift
        shift
        ;;
        --llm-type)
        LLM_TYPE="$2"
        shift
        shift
        ;;
        *)
        echo "Unknown option: $1"
        shift
        ;;
    esac
done

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Start the KAG server
echo "Starting KAG server with the following configuration:"
echo "  - KAG Host: ${KAG_HOST}"
echo "  - KAG Port: ${KAG_PORT}"
echo "  - Using existing ${LLM_TYPE} server at: ${VLLM_HOST}:${VLLM_PORT}"
echo "  - Proxy Mode: Enabled"
echo "  - LLM Type: ${LLM_TYPE}"

# Set environment variables for server (in proxy mode)
export KAG_HOST=$KAG_HOST
export KAG_PORT=$KAG_PORT
export KAG_PROXY_MODE=$PROXY_MODE
export KAG_EXTERNAL_LLM_URL="http://${VLLM_HOST}:${VLLM_PORT}"
export KAG_LLM_TYPE=$LLM_TYPE

# Make test scripts executable
if [ -f "test-query.sh" ]; then
    chmod +x test-query.sh
fi

if [ -f "check-documents.sh" ]; then
    chmod +x check-documents.sh
fi

# Run the server in proxy mode
echo "Starting KAG in proxy mode to connect to existing vLLM instance..."
python -m kag.server.proxy

echo "==== KAG Server Started ====" 