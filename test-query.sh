#!/bin/bash

# Test curl command for KAG proxy
echo "Sending test query to KAG proxy (localhost:11435)..."
curl -X POST http://localhost:11435/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:latest",
    "messages": [
      {
        "role": "user",
        "content": "Tell me about the best neighborhoods in Los Angeles for buying real estate. What makes them attractive for investment?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }'

echo -e "\n\nIf you get an error, you can try directly with Ollama using:"
echo "curl -X POST http://localhost:11434/api/chat -d '{\"model\": \"llama3.2:latest\", \"messages\": [{\"role\": \"user\", \"content\": \"Tell me about the best neighborhoods in Los Angeles for buying real estate\"}]}'" 