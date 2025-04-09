#!/bin/bash
# Script to start KAG system with integration to existing OpenWebUI on port 3002

set -e

echo "==== Starting KAG System with OpenWebUI Integration ===="

# Check for conda environment
if ! command -v conda &> /dev/null; then
    echo "Conda is not installed. Please install conda first."
    exit 1
fi

# Activate conda environment
if [ -z "$CONDA_DEFAULT_ENV" ] || [ "$CONDA_DEFAULT_ENV" != "kag" ]; then
    echo "Activating kag conda environment..."
    source "$(conda info --base)/etc/profile.d/conda.sh"
    if conda env list | grep -q "kag"; then
        conda activate kag
    else
        echo "KAG conda environment not found. Creating from conda.txt..."
        conda create -n kag python=3.10 -y
        conda activate kag
        
        # Install dependencies from conda.txt
        while read -r line; do
            # Skip comments and empty lines
            [[ "$line" =~ ^#.*$ ]] && continue
            [[ -z "$line" ]] && continue
            
            # Execute conda commands
            if [[ "$line" == conda* ]]; then
                eval "$line"
            fi
        done < conda.txt
        
        # Install pip dependencies
        while read -r line; do
            # Skip comments, empty lines and conda commands
            [[ "$line" =~ ^#.*$ ]] && continue
            [[ -z "$line" ]] && continue
            [[ "$line" == conda* ]] && continue
            
            # Execute pip commands
            if [[ "$line" == pip* ]]; then
                eval "$line"
            fi
        done < conda.txt
    fi
fi

# Check for OpenWebUI
echo "Checking OpenWebUI availability at http://localhost:3002..."
if ! curl -s --head --request GET http://localhost:3002 | grep "200 OK" > /dev/null; then
    echo "Warning: OpenWebUI does not appear to be running at http://localhost:3002"
    echo "Please make sure your OpenWebUI instance is running."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for CUDA
if ! command -v nvcc &> /dev/null; then
    echo "Warning: CUDA not found. GPU acceleration may not be available."
fi

# Check for model
if [ ! -d "./qwq" ]; then
    echo "Warning: Model directory './qwq' not found. Please ensure your model is available."
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
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
TENSOR_PARALLEL_SIZE=2
GPU_MEMORY_UTILIZATION=0.7
HOST="0.0.0.0"
PORT=11434
DISABLE_CUSTOM_ALL_REDUCE=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --tensor-parallel-size)
        TENSOR_PARALLEL_SIZE="$2"
        shift
        shift
        ;;
        --gpu-memory-utilization)
        GPU_MEMORY_UTILIZATION="$2"
        shift
        shift
        ;;
        --host)
        HOST="$2"
        shift
        shift
        ;;
        --port)
        PORT="$2"
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

# Set OpenWebUI-specific environment variables
export KAG_CORS_ORIGINS="http://localhost:3002"
export KAG_CORS_ALLOW_CREDENTIALS="true"
export OPENWEBUI_URL="http://localhost:3002"

# Start the KAG server
echo "Starting KAG server with the following configuration:"
echo "  - Tensor Parallel Size: $TENSOR_PARALLEL_SIZE"
echo "  - GPU Memory Utilization: $GPU_MEMORY_UTILIZATION"
echo "  - Host: $HOST"
echo "  - Port: $PORT"
echo "  - Model Path: ./qwq"
echo "  - OpenWebUI URL: http://localhost:3002"

# Set environment variables for server
export KAG_TENSOR_PARALLEL_SIZE=$TENSOR_PARALLEL_SIZE
export KAG_GPU_MEMORY_UTILIZATION=$GPU_MEMORY_UTILIZATION
export KAG_HOST=$HOST
export KAG_PORT=$PORT
export KAG_MODEL_PATH="./qwq"
export KAG_DISABLE_CUSTOM_ALL_REDUCE=$DISABLE_CUSTOM_ALL_REDUCE

# Set config file path
export KAG_CONFIG_FILE="openwebui_config.json"

# Run the server
echo "Running with config from openwebui_config.json..."
python -m kag.server.main

echo "==== KAG Server Started ====" 