#!/bin/bash

# Test vLLM directly
echo "Testing vLLM directly on port 11434..."
curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "messages": [
      {
        "role": "user",
        "content": "Tell me about the best neighborhoods in Los Angeles for buying real estate."
      }
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }' 