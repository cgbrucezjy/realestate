"""
OpenAI API compatibility layer for the KAG system.

This module provides OpenAI-compatible endpoints that leverage KV cache for
efficient document context management. It extends the standard vLLM OpenAI
compatibility with KAG-specific functionality.
"""

import json
import time
import uuid
from typing import Dict, List, Optional, Any, Union

from fastapi import APIRouter, Depends, HTTPException, Request, Body
from pydantic import BaseModel, Field

from kag.kv_cache.manager import KVCacheManager
from kag.kv_cache.session import SessionManager
from kag.document_processor.processor import DocumentProcessor
from kag.user.auth import get_current_user, User
from kag.utils.token_counter import count_tokens
from kag.utils.logger import get_logger
from kag.config import get_settings

# Initialize logger
logger = get_logger(__name__)

# Initialize router
router = APIRouter()

# Initialize managers
kv_cache_manager = KVCacheManager()
session_manager = SessionManager()
document_processor = DocumentProcessor()

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class CompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    max_tokens: Optional[int] = 256
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    user: Optional[str] = None
    stream: Optional[bool] = False
    # KAG specific parameters
    kag_enabled: Optional[bool] = True
    document_ids: Optional[List[str]] = None
    session_id: Optional[str] = None

class DocumentUploadRequest(BaseModel):
    document: str = Field(..., description="Base64 encoded document or raw text")
    document_type: str = Field(..., description="Type of document (pdf, txt, docx, etc.)")
    document_name: str = Field(..., description="Name of the document")
    document_id: Optional[str] = Field(None, description="Optional ID for the document")

# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.post("/chat/completions")
async def chat_completions(
    request: CompletionRequest,
    current_user: User = Depends(get_current_user),
    raw_request: Request = None,
):
    """
    OpenAI-compatible chat completions endpoint with KAG support.
    
    This endpoint handles both regular chat completions and KAG-enhanced completions
    where document context is loaded into the KV cache.
    """
    start_time = time.time()
    
    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())
    session = session_manager.get_or_create_session(session_id, current_user.id)
    
    # Process with KAG if enabled
    if request.kag_enabled:
        # Get documents for this session if document_ids provided
        if request.document_ids:
            # Load documents into KV cache if not already loaded
            await kv_cache_manager.ensure_documents_loaded(
                session_id=session_id,
                document_ids=request.document_ids,
                user_id=current_user.id
            )
        
        # Get the KV cache for this session
        kv_cache = await kv_cache_manager.get_session_kv_cache(session_id)
        
        # Add KV cache to request for vLLM
        # This is where the magic happens - we're using the pre-loaded document
        # context from the KV cache rather than adding it to the prompt
        raw_request.state.kv_cache = kv_cache
    
    # Count tokens for analytics
    token_count = count_tokens(request.messages)
    logger.info(f"Request token count: {token_count}")
    
    # Create response (integration with vLLM happens here)
    # In a full implementation, this would call the vLLM server with the KV cache
    response = {
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a sample response from the KAG system."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": token_count,
            "completion_tokens": 10,  # Example value
            "total_tokens": token_count + 10
        },
        "session_id": session_id,
        "kag_enabled": request.kag_enabled,
        "processing_time": time.time() - start_time
    }
    
    # Update session with new completion
    session_manager.update_session(session_id, request.messages, response["choices"][0]["message"])
    
    return response

@router.post("/documents/upload")
async def upload_document(
    request: DocumentUploadRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Upload a document to be used with KAG.
    """
    try:
        # Process document
        document_id = request.document_id or str(uuid.uuid4())
        chunks = await document_processor.process_document(
            document=request.document,
            document_type=request.document_type,
            document_name=request.document_name,
            document_id=document_id,
            user_id=current_user.id
        )
        
        # Return success
        return {
            "success": True,
            "document_id": document_id,
            "chunk_count": len(chunks),
            "message": "Document uploaded and processed successfully"
        }
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing document: {str(e)}")

@router.get("/documents")
async def list_documents(
    current_user: User = Depends(get_current_user)
):
    """
    List all documents available for the current user.
    """
    try:
        documents = await document_processor.get_user_documents(current_user.id)
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error listing documents: {str(e)}")

@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user)
):
    """
    List all sessions for the current user.
    """
    try:
        sessions = session_manager.get_user_sessions(current_user.id)
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error listing sessions: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a document.
    """
    try:
        success = await document_processor.delete_document(document_id, current_user.id)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error deleting document: {str(e)}") 