# KAG System - Knowledge Augmented Generation

A system that implements Knowledge Augmented Generation (KAG) using Qwen2-30B and vLLM, with support for per-user contexts and document integration via KV cache optimization.

## What is KAG?

Knowledge Augmented Generation (KAG) is an advancement over traditional RAG (Retrieval Augmented Generation) that loads documents directly into a language model's KV (key-value) cache rather than prepending them to the prompt. This provides several advantages:

- **Faster inference** - Documents are pre-processed into the KV cache
- **Better context utilization** - More efficient use of the context window
- **Persistent knowledge** - Document knowledge can be maintained across conversation turns

## Architecture

This system integrates:
- **vLLM backend**: Efficient model serving with KV cache optimization
- **User-specific contexts**: Each user has their own conversation and document context
- **Frontend integration**: Compatible with open-source chat UIs (OpenWebUI/Mistral ChatUI)

## Setup Instructions

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/kag-system.git
cd kag-system

# Create and activate conda environment
# Copy commands from conda.txt
conda create -n kag python=3.10 -y
conda activate kag
# ... rest of conda commands
```

### 2. Model Setup

Ensure you have Qwen2-30B model downloaded:

```bash
# If using HuggingFace models
huggingface-cli download Qwen/Qwen2-30B --local-dir ./qwq

# If using existing model
# Make sure model is accessible at ./qwq path
```

### 3. Starting the KAG Server

```bash
# Start the vLLM server with KAG extensions
python -m kag.server.main
```

### 4. Frontend Integration

#### Option 1: OpenWebUI (Recommended)

1. Install OpenWebUI following their [official documentation](https://github.com/open-webui/open-webui)
2. Configure an OpenAI-compatible API endpoint pointing to your KAG server:
   - API URL: `http://your_server_ip:11434/v1`
   - API Key: Set as needed by your configuration

#### Option 2: Mistral ChatUI

1. Install Mistral ChatUI following their [documentation](https://github.com/mistralai/mistral-ui)
2. Configure to connect to your KAG server API endpoint:
   - API URL: `http://your_server_ip:11434/v1`

## Usage

1. Upload documents through the frontend UI
2. Start chatting with context from your documents
3. The system will maintain your conversation context and document knowledge

## Performance Considerations

- Running with 2x H100 GPUs is recommended for optimal performance
- Adjust the `gpu-memory-utilization` parameter based on your available memory
- For multi-user setups, consider scaling horizontally with multiple instances

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT 