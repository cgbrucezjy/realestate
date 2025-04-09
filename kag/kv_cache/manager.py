"""
KV Cache Manager for KAG system.

This module handles the management of KV cache for the KAG system, including loading 
documents into the KV cache and maintaining cache state across requests.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple

import torch
from vllm.sampling_params import SamplingParams
from vllm.engine.async_llm_engine import AsyncLLMEngine

from kag.document_processor.processor import DocumentProcessor
from kag.utils.logger import get_logger
from kag.utils.token_counter import count_tokens
from kag.config import get_settings

# Initialize logger
logger = get_logger(__name__)

# Get settings
settings = get_settings()

class KVCacheManager:
    """
    Manages KV cache operations for the KAG system.
    
    This class handles loading documents into the KV cache and maintaining 
    cache state across requests for different user sessions.
    """
    
    def __init__(self):
        """Initialize the KV cache manager."""
        self.document_processor = DocumentProcessor()
        self.session_kv_caches = {}  # Maps session_id to KV cache
        self.session_document_map = {}  # Maps session_id to document_ids
        self.document_token_counts = {}  # Maps document_id to token count
        self.lock = asyncio.Lock()
        
        # Will be initialized when connecting to the LLM engine
        self.llm_engine = None
    
    async def connect_to_llm_engine(self, engine: AsyncLLMEngine) -> None:
        """Connect to the LLM engine."""
        self.llm_engine = engine
        logger.info("Connected to LLM engine")
    
    async def ensure_documents_loaded(
        self, 
        session_id: str, 
        document_ids: List[str],
        user_id: str
    ) -> None:
        """
        Ensure that the specified documents are loaded into the KV cache.
        
        Args:
            session_id: The ID of the session
            document_ids: List of document IDs to load
            user_id: The ID of the user making the request
        """
        async with self.lock:
            # Check if we already have these documents loaded
            if session_id in self.session_document_map:
                current_docs = self.session_document_map[session_id]
                if set(current_docs) == set(document_ids):
                    logger.info(f"Documents already loaded for session {session_id}")
                    return
            
            # Get document chunks
            document_chunks = []
            for doc_id in document_ids:
                chunks = await self.document_processor.get_document_chunks(doc_id, user_id)
                if not chunks:
                    logger.warning(f"Document {doc_id} not found or no chunks available")
                    continue
                document_chunks.extend(chunks)
            
            # If no chunks found, return early
            if not document_chunks:
                logger.warning("No document chunks found to load")
                return
            
            # Create KV cache for documents
            await self._create_kv_cache_for_documents(session_id, document_chunks)
            
            # Update session document map
            self.session_document_map[session_id] = document_ids
            
            logger.info(f"Documents loaded for session {session_id}: {document_ids}")
    
    async def _create_kv_cache_for_documents(
        self, 
        session_id: str, 
        document_chunks: List[str]
    ) -> None:
        """
        Create KV cache for document chunks.
        
        This is where the core KAG magic happens - we process documents through the model
        but only save the KV cache, not generating any output tokens.
        
        Args:
            session_id: The ID of the session
            document_chunks: List of document chunk texts
        """
        if not self.llm_engine:
            raise ValueError("LLM engine not connected")
        
        # Combine chunks with separator
        # The format here depends on your model's preferences
        separator = "\n\n"
        document_text = separator.join(document_chunks)
        
        # Count tokens for analytics
        token_count = count_tokens(document_text)
        logger.info(f"Loading {token_count} tokens into KV cache for session {session_id}")
        
        # Process document through model to generate KV cache
        # Note: We're using a special mode where we only want to create the KV cache
        # without actually generating tokens
        sampling_params = SamplingParams(
            temperature=0.0,  # Deterministic
            max_tokens=1,  # We only need to generate 1 token to create the KV cache
            kv_cache_mode="prefill_only"  # Special mode to only create KV cache
        )
        
        # Format the document as a system message for processing
        prompt = f"<system>\nThe following are important documents to reference: {document_text}\n</system>"
        
        try:
            # Process through the model to create KV cache
            # In a real implementation, this would call the actual vLLM engine
            # with appropriate methods to extract and preserve the KV cache
            start_time = time.time()
            
            # This is a simplified representation of how vLLM would process this
            # The actual implementation depends on how vLLM exposes KV cache functionality
            results = await self.llm_engine.prefill_kv_cache(
                prompt=prompt,
                sampling_params=sampling_params
            )
            
            # Get the KV cache from results
            kv_cache = results.get("kv_cache")
            
            # Store the KV cache for this session
            self.session_kv_caches[session_id] = kv_cache
            
            processing_time = time.time() - start_time
            logger.info(f"KV cache created in {processing_time:.2f}s for session {session_id}")
        
        except Exception as e:
            logger.error(f"Error creating KV cache: {str(e)}")
            raise
    
    async def get_session_kv_cache(self, session_id: str) -> Optional[Any]:
        """
        Get the KV cache for a session.
        
        Args:
            session_id: The ID of the session
            
        Returns:
            The KV cache for the session, or None if not found
        """
        return self.session_kv_caches.get(session_id)
    
    async def clear_session_kv_cache(self, session_id: str) -> None:
        """
        Clear the KV cache for a session.
        
        Args:
            session_id: The ID of the session
        """
        async with self.lock:
            if session_id in self.session_kv_caches:
                del self.session_kv_caches[session_id]
            if session_id in self.session_document_map:
                del self.session_document_map[session_id]
            logger.info(f"Cleared KV cache for session {session_id}")
    
    async def get_kv_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the KV cache.
        
        Returns:
            Dictionary containing statistics about the KV cache
        """
        return {
            "active_sessions": len(self.session_kv_caches),
            "total_documents_loaded": sum(len(docs) for docs in self.session_document_map.values()),
            "session_document_counts": {
                session_id: len(docs) for session_id, docs in self.session_document_map.items()
            }
        } 