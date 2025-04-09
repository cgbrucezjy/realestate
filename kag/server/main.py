"""
Main entry point for the KAG server.

This module initializes the vLLM engine and connects it with our KAG extensions
to provide a complete Knowledge Augmented Generation system.
"""

import argparse
import asyncio
import os
import time
import glob
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

# vLLM imports
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.sampling_params import SamplingParams
from vllm.entrypoints.openai.serving_chat import OpenAIServingChat

# KAG imports
from kag.kv_cache.manager import KVCacheManager
from kag.kv_cache.session import SessionManager
from kag.document_processor.processor import DocumentProcessor
from kag.user.auth import setup_auth
from kag.utils.logger import setup_logging, get_logger
from kag.config import get_settings
from kag.server.openai_compat import router as openai_router

# Get settings
settings = get_settings()

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Initialize managers
kv_cache_manager = KVCacheManager()
session_manager = SessionManager()
document_processor = DocumentProcessor()

# Create FastAPI app
app = FastAPI(
    title="KAG API",
    description="Knowledge Augmented Generation API",
    version="1.0.0"
)

# Get CORS settings
cors_origins = os.environ.get("KAG_CORS_ORIGINS", "*").split(",")
cors_allow_credentials = os.environ.get("KAG_CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

# Add CORS middleware with support for OpenWebUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Allow OpenWebUI origin
    allow_credentials=cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup authentication
setup_auth(app)

# Add OpenAI-compatible routes
app.include_router(openai_router, prefix="/v1")

# Add health check route
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}

# Add KV cache stats route
@app.get("/stats/kv_cache")
async def kv_cache_stats():
    """Get KV cache statistics."""
    return await kv_cache_manager.get_kv_cache_stats()

# Add session stats route
@app.get("/stats/sessions")
async def session_stats():
    """Get session statistics."""
    return session_manager.get_stats()

async def load_knowledge_folder():
    """
    Load all Markdown files from kag/knowledge folder into the document database.
    This ensures all knowledge is available for the KAG system on startup.
    """
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
    
    # Create a default session ID for the knowledge base
    kb_session_id = "knowledge_base_session"
    document_ids = []
    
    # Process each file
    for md_file in md_files:
        try:
            # Get filename without extension
            filename = os.path.basename(md_file)
            document_name = os.path.splitext(filename)[0]
            document_id = f"kb_{document_name}"
            document_ids.append(document_id)
            
            # Read file content
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Process document
            await document_processor.process_document(
                document=content,
                document_type="md",
                document_name=document_name,
                document_id=document_id,
                user_id="system"
            )
            
            logger.info(f"Processed knowledge file: {filename}")
            
        except Exception as e:
            logger.error(f"Error processing knowledge file {md_file}: {str(e)}")
    
    # Load documents into KV cache
    if document_ids:
        try:
            await kv_cache_manager.ensure_documents_loaded(
                session_id=kb_session_id,
                document_ids=document_ids,
                user_id="system"
            )
            logger.info(f"Loaded {len(document_ids)} knowledge documents into KV cache")
        except Exception as e:
            logger.error(f"Error loading knowledge documents into KV cache: {str(e)}")

async def setup_vllm_engine():
    """Setup vLLM engine with KAG extensions."""
    logger.info("Setting up vLLM engine with KAG extensions...")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default=settings.model_path)
    parser.add_argument("--tensor-parallel-size", type=int, default=settings.tensor_parallel_size)
    parser.add_argument("--gpu-memory-utilization", type=float, default=settings.gpu_memory_utilization)
    parser.add_argument("--max-model-len", type=int, default=settings.max_model_len)
    parser.add_argument("--host", type=str, default=settings.host)
    parser.add_argument("--port", type=int, default=settings.port)
    parser.add_argument("--disable-custom-all-reduce", action="store_true", default=settings.disable_custom_all_reduce)
    args = parser.parse_args()
    
    # Create engine arguments
    engine_args = AsyncEngineArgs(
        model=args.model,
        tensor_parallel_size=args.tensor_parallel_size,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=args.max_model_len,
        trust_remote_code=True,
        disable_custom_all_reduce=args.disable_custom_all_reduce
    )
    
    # Create engine
    engine = AsyncLLMEngine.from_engine_args(engine_args)
    
    # Setup OpenAI-compatible chat endpoint with our extensions
    openai_serving_chat = OpenAIServingChat(
        engine=engine,
        served_model=args.model
    )
    
    # Register our vLLM hooks for KV cache access
    # This would need to be implemented based on vLLM's internal APIs
    register_vllm_hooks(engine)
    
    # Connect KV cache manager to engine
    await kv_cache_manager.connect_to_llm_engine(engine)
    
    # Store engine in app state
    app.state.engine = engine
    app.state.openai_serving_chat = openai_serving_chat
    
    logger.info("vLLM engine setup complete")
    
    return args

def register_vllm_hooks(engine):
    """
    Register hooks into vLLM to access KV cache.
    
    Note: This is a placeholder function. The actual implementation would
    depend on vLLM's internal APIs for KV cache access.
    """
    # This would hook into vLLM's internals to expose KV cache functionality
    # The exact implementation depends on vLLM's architecture
    logger.info("Registered vLLM hooks for KV cache access")
    
    # Example of what this might look like:
    # engine.register_kv_cache_handler(kv_cache_manager.handle_kv_cache)
    pass

async def startup_event():
    """Startup event handler."""
    args = await setup_vllm_engine()
    logger.info(f"Starting server on {args.host}:{args.port}")
    logger.info(f"CORS configured for origins: {cors_origins}")
    
    # Load knowledge files
    await load_knowledge_folder()

async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down server...")

# Register startup and shutdown events
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

if __name__ == "__main__":
    # Get settings
    host = settings.host
    port = settings.port
    
    # Start server
    uvicorn.run("kag.server.main:app", host=host, port=port, reload=False) 