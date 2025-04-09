"""
Generic proxy server for KAG that selects the appropriate implementation
based on the LLM type.
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("kag-proxy")

# Get the LLM type from environment variables
llm_type = os.environ.get("KAG_LLM_TYPE", "vllm").lower()

# Check if a valid type is provided
if llm_type not in ["vllm", "ollama"]:
    logger.error(f"Invalid LLM type: {llm_type}")
    logger.error("Valid options are: vllm, ollama")
    logger.error("Defaulting to vllm")
    llm_type = "vllm"

# Choose the appropriate proxy implementation
if llm_type == "vllm":
    logger.info("Using vLLM proxy implementation")
    from kag.server.proxy_vllm import app, startup_event, shutdown_event, load_knowledge_folder
else:  # ollama
    logger.info("Using Ollama proxy implementation")
    from kag.server.proxy_ollama import app, startup_event, shutdown_event, load_knowledge_folder

# Entry point
if __name__ == "__main__":
    import uvicorn
    
    # Get settings
    host = os.environ.get("KAG_HOST", "0.0.0.0")
    port = int(os.environ.get("KAG_PORT", 11435))
    
    logger.info(f"Starting KAG proxy on {host}:{port} using {llm_type.upper()} implementation")
    
    # Run the appropriate server
    module_name = f"kag.server.proxy_{llm_type}"
    uvicorn.run(f"{module_name}:app", host=host, port=port, reload=False) 