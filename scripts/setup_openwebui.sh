#!/bin/bash
# Setup script for OpenWebUI integration with KAG system

set -e

echo "==== Setting up OpenWebUI for KAG System ===="

# Check for Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Get KAG server details
read -p "Enter KAG server host (default: localhost): " KAG_HOST
KAG_HOST=${KAG_HOST:-localhost}

read -p "Enter KAG server port (default: 11434): " KAG_PORT
KAG_PORT=${KAG_PORT:-11434}

# Create a directory for OpenWebUI
OPENWEBUI_DIR="openwebui"
mkdir -p $OPENWEBUI_DIR
cd $OPENWEBUI_DIR

# Create docker-compose.yml
cat > docker-compose.yml << EOF
version: '3'

services:
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: openwebui
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - 'WEBUI_AUTH_PROVIDERS=${AUTH_PROVIDERS:-credentials}'
      - 'WEBUI_OLLAMA_API_BASE_URL=http://host.docker.internal:${KAG_PORT}'
      - 'WEBUI_OLLAMA_API_KEY=dummy-key'
      - 'WEBUI_DB_PROVIDER=sqlite'
      - 'WEBUI_DB_PATH=/data/sqlite.db'
      - 'WEBUI_MODEL=qwq'
      - 'WEBUI_KAG_ENABLED=true'
    volumes:
      - ./data:/data
    extra_hosts:
      - "host.docker.internal:host-gateway"
EOF

echo "Created docker-compose.yml with configuration for KAG server at $KAG_HOST:$KAG_PORT"

# Create .env file for additional configuration
cat > .env << EOF
# OpenWebUI configuration for KAG system

# Authentication
WEBUI_AUTH_PROVIDERS=credentials
# Additional providers: google,github,discord,openid

# KAG server connection
WEBUI_OLLAMA_API_BASE_URL=http://${KAG_HOST}:${KAG_PORT}
WEBUI_OLLAMA_API_KEY=dummy-key

# Database
WEBUI_DB_PROVIDER=sqlite
WEBUI_DB_PATH=/data/sqlite.db

# Default model
WEBUI_MODEL=qwq

# KAG-specific options
WEBUI_KAG_ENABLED=true
EOF

echo "Created .env file with additional configuration"

# Create data directory
mkdir -p data
echo "Created data directory for persistent storage"

# Start OpenWebUI
echo "Starting OpenWebUI..."
docker-compose up -d

echo "==== OpenWebUI Setup Complete ===="
echo "OpenWebUI is now running at http://localhost:3000"
echo ""
echo "To configure KAG integration in OpenWebUI:"
echo "1. Create an account on OpenWebUI"
echo "2. Go to Settings > Model Providers"
echo "3. Add a new provider with:"
echo "   - Name: KAG"
echo "   - API Base URL: http://${KAG_HOST}:${KAG_PORT}/v1"
echo "   - API Key: dummy-key"
echo "4. Go to Settings > Models"
echo "5. Add a model with:"
echo "   - Provider: KAG"
echo "   - Model ID: qwq"
echo ""
echo "For more customization options, edit .env and restart with 'docker-compose restart'" 