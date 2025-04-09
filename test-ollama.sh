#!/bin/bash

# Test Ollama directly
echo "Testing Ollama directly on port 11434..."
curl -X POST http://localhost:11434/api/chat \
  -d '{
    "model": "llama3.2:latest",
    "messages": [
      {
        "role": "user",
        "content": "Tell me about the best neighborhoods in Los Angeles for buying real estate."
      }
    ]
  }' 