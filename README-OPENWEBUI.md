# KAG System - OpenWebUI Integration

This guide explains how to connect your KAG system to your existing OpenWebUI installation running on port 3002.

## Quick Start

1. Make sure your OpenWebUI is running on port 3002
2. Make sure you have set up the KAG system environment (see main README.md)
3. Run the specialized startup script:

```bash
chmod +x start_with_openwebui.sh
./start_with_openwebui.sh
```

This script will:
- Set up CORS to allow connections from OpenWebUI at port 3002
- Start the KAG server on port 11434
- Load necessary configuration for the integration

## Manual Configuration

If you prefer to configure things manually, follow these steps:

1. Copy the `.env.example` file to `.env` and update these settings:
   ```
   KAG_CORS_ORIGINS=http://localhost:3002
   KAG_CORS_ALLOW_CREDENTIALS=true
   OPENWEBUI_URL=http://localhost:3002
   ```

2. Start the KAG server using:
   ```bash
   ./start.sh
   ```

3. Follow the instructions in `openwebui_connect.md` to configure the connection in OpenWebUI.

## Troubleshooting Connectivity

If you encounter connectivity issues:

1. Make sure both services can reach each other
   - If using Docker for OpenWebUI, make sure host networking is set up correctly
   - Test with `curl http://localhost:11434/health` to confirm KAG is accessible

2. Check CORS configuration
   - If you see CORS errors in browser console, check that the KAG server CORS settings match your OpenWebUI URL

3. Verify OpenWebUI API configuration
   - Make sure your OpenWebUI provider configuration uses the correct URL: `http://localhost:11434/v1`

## Features

When properly integrated, your OpenWebUI will have these enhanced features:

1. KV cache optimization for documents
2. Per-user session management
3. Improved context handling via KAG's optimized document loading
4. Better performance compared to standard RAG approaches

## Need Help?

If you encounter issues with the integration, check the KAG logs and OpenWebUI logs for errors.
Then refer to the troubleshooting section in the main documentation. 