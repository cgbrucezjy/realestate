"""
Token counting utilities for the KAG system.

This module provides functions for counting tokens in text, which is important
for managing KV cache usage and token limits.
"""

import re
from typing import Dict, List, Union, Any, Optional

import tiktoken

from kag.utils.logger import get_logger
from kag.config import get_settings

# Initialize logger
logger = get_logger(__name__)

# Get settings
settings = get_settings()

# Cache encoder instances
_ENCODERS = {}

def get_encoder(model_name: str = None) -> tiktoken.Encoding:
    """
    Get a tokenizer for a model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Tokenizer for the model
    """
    # Default to cl100k_base for newer models
    if not model_name:
        model_name = "cl100k_base"
    
    # Check if encoder is cached
    if model_name in _ENCODERS:
        return _ENCODERS[model_name]
    
    try:
        # Try to get encoding for a specific model
        enc = tiktoken.encoding_for_model(model_name)
    except KeyError:
        # Fall back to cl100k_base
        enc = tiktoken.get_encoding("cl100k_base")
    
    # Cache encoder
    _ENCODERS[model_name] = enc
    return enc

def count_tokens(text: Union[str, List[Dict[str, str]], Dict[str, Any]], model_name: str = None) -> int:
    """
    Count tokens in text.
    
    Args:
        text: Text to count tokens for. Can be a string, list of messages, or a dictionary
        model_name: Name of the model to use for counting
        
    Returns:
        Number of tokens
    """
    # Get encoder
    encoder = get_encoder(model_name)
    
    # Handle different input types
    if isinstance(text, str):
        # Count tokens for string
        return len(encoder.encode(text))
    elif isinstance(text, list):
        # Assume list of messages
        token_count = 0
        
        # Handle chat messages format
        for message in text:
            if not isinstance(message, dict):
                continue
            
            # Count role
            role = message.get("role", "")
            token_count += len(encoder.encode(role))
            
            # Count content
            content = message.get("content", "")
            if isinstance(content, str):
                token_count += len(encoder.encode(content))
            
            # Count name if present
            name = message.get("name", "")
            if name:
                token_count += len(encoder.encode(name))
        
        # Add message format overhead
        token_count += 3  # Every message has a 3 token overhead
        
        return token_count
    elif isinstance(text, dict):
        # Handle dictionary - serialize to string and count
        import json
        serialized = json.dumps(text)
        return len(encoder.encode(serialized))
    else:
        # Unknown type
        logger.warning(f"Unknown type for token counting: {type(text)}")
        return 0

def truncate_text_to_token_limit(text: str, token_limit: int, model_name: str = None) -> str:
    """
    Truncate text to a token limit.
    
    Args:
        text: Text to truncate
        token_limit: Maximum number of tokens
        model_name: Name of the model to use for counting
        
    Returns:
        Truncated text
    """
    # Get encoder
    encoder = get_encoder(model_name)
    
    # Encode text
    tokens = encoder.encode(text)
    
    # Check if truncation needed
    if len(tokens) <= token_limit:
        return text
    
    # Truncate tokens
    truncated_tokens = tokens[:token_limit]
    
    # Decode truncated tokens
    truncated_text = encoder.decode(truncated_tokens)
    
    return truncated_text

def estimate_token_limit_by_bytes(text: str, bytes_per_token: float = 4.0) -> int:
    """
    Estimate token limit by bytes.
    
    This is a rough estimation useful when tiktoken is not available.
    
    Args:
        text: Text to estimate tokens for
        bytes_per_token: Average bytes per token
        
    Returns:
        Estimated number of tokens
    """
    # Get byte length of text
    byte_length = len(text.encode("utf-8"))
    
    # Estimate token count
    return int(byte_length / bytes_per_token) 