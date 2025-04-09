"""
Proxy server for KAG that connects to an existing Ollama instance.

This module creates a proxy server that connects to Ollama
and adds the knowledge loading and document processing capabilities.
"""

import asyncio
import os
import time
import glob
import json
import requests
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.background import BackgroundTask
import httpx

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("kag-proxy-ollama")

# Create FastAPI app
app = FastAPI(
    title="KAG Proxy API for Ollama",
    description="Knowledge Augmented Generation Proxy API for Ollama",
    version="1.0.0"
)

# Get CORS settings
cors_origins = os.environ.get("KAG_CORS_ORIGINS", "*").split(",")
cors_allow_credentials = os.environ.get("KAG_CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get external LLM URL
external_llm_url = os.environ.get("KAG_EXTERNAL_LLM_URL", "http://localhost:11434")

# Create HTTP client for forwarding requests
http_client = httpx.AsyncClient(base_url=external_llm_url)

# Keep track of loaded documents
loaded_documents = []

async def load_knowledge_folder():
    """
    Load all Markdown files from kag/knowledge folder.
    This ensures all knowledge is available for the KAG system on startup.
    """
    global loaded_documents
    
    logger.info("Loading knowledge files from kag/knowledge folder...")
    
    # Get path to knowledge folder
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    knowledge_path = os.path.join(base_path, "kag", "knowledge")
    
    if not os.path.exists(knowledge_path):
        logger.warning(f"Knowledge folder not found: {knowledge_path}")
        return
    
    # Get all markdown files
    md_files = glob.glob(os.path.join(knowledge_path, "*.md"))
    
    if not md_files:
        logger.warning("No markdown files found in knowledge folder")
        return
    
    logger.info(f"Found {len(md_files)} markdown files in knowledge folder")
    
    # Process each file
    for md_file in md_files:
        try:
            # Get filename without extension
            filename = os.path.basename(md_file)
            document_name = os.path.splitext(filename)[0]
            
            # Read file content
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Add to loaded documents
            loaded_documents.append({
                "name": document_name,
                "content": content,
                "path": md_file
            })
            
            logger.info(f"Loaded knowledge file: {filename}")
            
        except Exception as e:
            logger.error(f"Error loading knowledge file {md_file}: {str(e)}")
    
    logger.info(f"Loaded {len(loaded_documents)} knowledge documents")
    logger.info("Documents are ready to be used in queries")

# Documents endpoint
@app.get("/documents")
async def list_documents():
    """List loaded documents."""
    return {
        "count": len(loaded_documents),
        "documents": [{"name": doc["name"], "path": doc["path"]} for doc in loaded_documents]
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint that also checks the external LLM server."""
    # Check if the external LLM server is reachable
    try:
        # Try Ollama's endpoint
        response = requests.get(f"{external_llm_url}/api/health", timeout=5)
        
        if response.status_code == 200:
            return {
                "status": "ok",
                "version": "1.0.0",
                "external_llm": "connected",
                "external_llm_url": external_llm_url,
                "loaded_documents": len(loaded_documents)
            }
        else:
            return {
                "status": "warning",
                "message": f"External LLM server returned status {response.status_code}",
                "external_llm_url": external_llm_url,
                "loaded_documents": len(loaded_documents)
            }
    except Exception as e:
        return {
            "status": "warning",
            "message": f"Error connecting to external LLM server: {str(e)}",
            "external_llm_url": external_llm_url,
            "loaded_documents": len(loaded_documents)
        }

# Convert OpenAI format to Ollama format
async def convert_openai_to_ollama(data):
    """Convert OpenAI-style request to Ollama format."""
    
    # Start with base structure for Ollama
    ollama_data = {
        "model": data.get("model", "llama3"),
        "messages": data.get("messages", [])
    }
    
    # Add optional parameters if present
    if "temperature" in data:
        ollama_data["temperature"] = data["temperature"]
    
    if "max_tokens" in data:
        ollama_data["max_length"] = data["max_tokens"]
    
    # Add system prompt with context if needed
    if loaded_documents:
        # Get any existing system message
        system_content = ""
        has_system = False
        
        for msg in ollama_data["messages"]:
            if msg.get("role") == "system":
                system_content = msg["content"]
                has_system = True
                break
        
        # Add document context
        doc_context = "The following documents contain important information:\n\n"
        
        # Add content from documents (limit to reasonable size)
        for i, doc in enumerate(loaded_documents):
            doc_context += f"Document: {doc['name']}\n"
            # Limit content length to avoid token issues
            content_preview = doc['content'][:1000] + ("..." if len(doc['content']) > 1000 else "")
            doc_context += f"{content_preview}\n\n"
        
        # Add or update system message
        if has_system:
            # Update existing system message
            for msg in ollama_data["messages"]:
                if msg.get("role") == "system":
                    msg["content"] = system_content + "\n\n" + doc_context
                    break
        else:
            # Add new system message at the beginning
            ollama_data["messages"].insert(0, {
                "role": "system",
                "content": doc_context
            })
    
    logger.info("Converted OpenAI format to Ollama format with document context")
    return ollama_data

# Proxy function
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def proxy(request: Request, path: str):
    """
    Proxy all requests to the external Ollama server while adding document context.
    """
    try:
        # Get request body as string first to avoid issues
        body_str = (await request.body()).decode('utf-8')
        
        # Get all headers
        headers = dict(request.headers)
        
        # Determine the target URL and request format
        if path == "v1/chat/completions":
            # OpenAI-style API request, convert to Ollama format
            try:
                # Parse the request body
                data = json.loads(body_str)
                
                # Convert OpenAI format to Ollama format
                ollama_data = await convert_openai_to_ollama(data)
                
                # Update the request body
                body_str = json.dumps(ollama_data)
                
                # Change target URL to Ollama's endpoint
                url = "/api/chat"
                
            except Exception as e:
                logger.error(f"Error converting request format: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Error converting request format: {str(e)}")
        else:
            # Pass through as-is
            url = f"/{path}"
        
        # Convert body_str to bytes
        body = body_str.encode('utf-8')
        
        # Update content length header
        if 'content-length' in headers:
            headers['content-length'] = str(len(body))
        
        logger.info(f"Forwarding request to {url}")
        
        # Forward the request to the external LLM server
        response = await http_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body
        )
        
        # Return the response
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            background=BackgroundTask(response.aclose)
        )
    
    except Exception as e:
        logger.error(f"Error proxying request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error connecting to LLM server: {str(e)}")

# Startup event to load knowledge
@app.on_event("startup")
async def startup_event():
    """Startup event handler that loads knowledge files."""
    logger.info(f"Starting KAG proxy server connected to Ollama at {external_llm_url}")
    
    # Load knowledge files
    await load_knowledge_folder()

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down KAG proxy server...")
    await http_client.aclose()

# Main entry point
if __name__ == "__main__":
    # Get settings
    host = os.environ.get("KAG_HOST", "0.0.0.0")
    port = int(os.environ.get("KAG_PORT", 11435))
    
    logger.info(f"Starting KAG proxy on {host}:{port}, connecting to Ollama at {external_llm_url}")
    
    # Start server
    uvicorn.run("kag.server.proxy_ollama:app", host=host, port=port, reload=False) 