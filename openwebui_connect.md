# Connecting Existing OpenWebUI to KAG System

This guide provides instructions for connecting your existing OpenWebUI installation (running on port 3002) to the KAG system.

## Prerequisites

- OpenWebUI already installed and running on port 3002
- KAG system set up and running on port 11434 (or your configured port)

## Configuration Steps

### 1. Add KAG as a Model Provider in OpenWebUI

1. Open your OpenWebUI installation at http://localhost:3002
2. Login to your account
3. Navigate to **Settings > Model Providers**
4. Click **Add Provider**
5. Enter the following details:
   - **Name**: KAG
   - **API Base URL**: `http://localhost:11434/v1`
   - **API Key**: `dummy-key` (or your configured key if you've set one)
   - **Provider Type**: OpenAI API
6. Click **Save**

### 2. Add Qwen2-30B as a Model

1. Navigate to **Settings > Models**
2. Click **Add Model**
3. Enter the following details:
   - **Provider**: KAG (select from dropdown)
   - **Model ID**: `qwq` (or the model ID you configured in KAG)
   - **Model Name**: `Qwen2-30B KAG` (or any name you prefer)
   - **Context Length**: 4096 (adjust based on your configuration)
4. Click **Save**

### 3. Enable KAG Features (Document Processing)

1. Navigate to **Settings > Features** (if available)
2. Enable any document processing or RAG features in the UI
3. When creating a new chat, select the Qwen2-30B KAG model
4. Use the document upload feature to add documents to your chat
5. The system will automatically load documents into the KV cache

## Verifying the Connection

To verify that OpenWebUI is correctly connected to your KAG system:

1. Create a new chat
2. Select the Qwen2-30B KAG model
3. Send a test message
4. Check the KAG system logs to see if it's receiving and processing the request

## Troubleshooting

If you encounter connection issues:

1. Verify that the KAG system is running with `curl http://localhost:11434/health`
2. Check that your OpenWebUI can connect to the KAG API endpoint
3. Ensure that CORS is properly configured in the KAG server
4. Check the network settings if KAG and OpenWebUI are running on different machines

## Advanced Configuration

For advanced configuration, you may want to modify these settings:

1. In OpenWebUI, you can configure model-specific parameters like temperature and max tokens
2. In KAG, you can adjust the KV cache settings in the `.env` file to optimize for your usage

Remember that KAG provides enhanced document context handling through KV cache optimization, which should result in faster responses and better context utilization compared to traditional RAG approaches. 