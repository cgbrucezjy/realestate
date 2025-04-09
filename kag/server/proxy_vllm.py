"""
Proxy server for KAG that connects to an existing vLLM instance.

This module creates a proxy server that connects to vLLM
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
logger = logging.getLogger("kag-proxy-vllm")

# Create FastAPI app
app = FastAPI(
    title="KAG Proxy API for vLLM",
    description="Knowledge Augmented Generation Proxy API for vLLM",
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
        # Try vLLM's endpoint
        response = requests.get(f"{external_llm_url}/health", timeout=5)
        
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

# Proxy function
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def proxy(request: Request, path: str):
    """
    Proxy all requests to the external vLLM server while adding document context.
    """
    # Get target URL
    url = f"/{path}"
    
    # Get all headers
    headers = dict(request.headers)
    
    # Check if this is a chat completion request (where we'll add document context)
    is_chat_completion = path.endswith("chat/completions")
    
    # Get request body as string first to avoid issues
    body_str = (await request.body()).decode('utf-8')
    
    try:
        if is_chat_completion and loaded_documents and body_str:
            try:
                # Parse the request body
                data = json.loads(body_str)
                
                # Only modify if it's using the messages format
                if "messages" in data:
                    # Create a system message with document context
                    doc_context = "The following documents contain important information:\n\n"
                    
                    # Add content from documents (limit to reasonable size)
                    for i, doc in enumerate(loaded_documents):
                        doc_context += f"Document: {doc['name']}\n"
                        # Limit content length to avoid token issues
                        content_preview = doc['content'][:1000] + ("..." if len(doc['content']) > 1000 else "")
                        doc_context += f"{content_preview}\n\n"
                    
                    # Check if there's already a system message
                    has_system = False
                    for msg in data["messages"]:
                        if msg.get("role") == "system":
                            # Append to existing system message
                            msg["content"] += "\n\n" + doc_context
                            has_system = True
                            break
                    
                    # If no system message, add one
                    if not has_system:
                        data["messages"].insert(0, {
                            "role": "system", 
                            "content": doc_context
                        })
                    
                    # Convert back to JSON
                    body_str = json.dumps(data)
                    
                    logger.info("Injected document context into chat completion request")
            except Exception as e:
                logger.error(f"Error modifying request with document context: {str(e)}")
        
        # Convert body_str to bytes
        body = body_str.encode('utf-8')
        
        # Update content length header
        if 'content-length' in headers:
            headers['content-length'] = str(len(body))
        
        logger.info(f"Forwarding request to vLLM: {url}")
        
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
    logger.info(f"Starting KAG proxy server connected to vLLM at {external_llm_url}")
    
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
    
    logger.info(f"Starting KAG proxy on {host}:{port}, connecting to vLLM at {external_llm_url}")
    
    # Start server
    uvicorn.run("kag.server.proxy_vllm:app", host=host, port=port, reload=False) 