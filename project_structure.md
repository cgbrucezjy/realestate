# Project Structure

```
kag-system/
├── README.md                 # Project overview and instructions
├── PLAN.md                   # Implementation plan
├── conda.txt                 # Environment setup commands
├── .env.example              # Example environment variables
├── requirements.txt          # Python dependencies (auto-generated from conda)
├── kag/                      # Main package
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration management
│   ├── document_processor/   # Document processing module
│   │   ├── __init__.py
│   │   ├── chunker.py        # Document chunking
│   │   ├── loader.py         # Document loading (PDF, DOCX, etc.)
│   │   ├── processor.py      # Main document processing
│   │   └── schema.py         # Document schemas
│   ├── kv_cache/             # KV cache management module
│   │   ├── __init__.py
│   │   ├── manager.py        # KV cache manager
│   │   ├── session.py        # Session management
│   │   └── prefill.py        # KV cache prefilling with documents
│   ├── user/                 # User management module
│   │   ├── __init__.py
│   │   ├── auth.py           # Authentication
│   │   ├── models.py         # User models
│   │   └── session.py        # User session management
│   ├── query/                # Query processing module
│   │   ├── __init__.py
│   │   ├── handler.py        # Query handling
│   │   ├── response.py       # Response generation
│   │   └── conversation.py   # Conversation tracking
│   ├── server/               # API server module
│   │   ├── __init__.py
│   │   ├── main.py           # Server entry point
│   │   ├── api.py            # API routes
│   │   ├── openai_compat.py  # OpenAI API compatibility
│   │   ├── middlewares.py    # Server middlewares
│   │   └── utils.py          # Server utilities
│   └── utils/                # Utility module
│       ├── __init__.py
│       ├── token_counter.py  # Token counting
│       ├── logger.py         # Logging utilities
│       └── vllm_helpers.py   # vLLM integration helpers
├── scripts/                  # Utility scripts
│   ├── convert_conda_to_requirements.py  # Generate requirements.txt
│   ├── setup_openwebui.sh    # Script to setup OpenWebUI
│   └── benchmark.py          # Performance benchmarking
├── tests/                    # Tests
│   ├── __init__.py
│   ├── conftest.py           # Test configuration
│   ├── test_document_processor.py
│   ├── test_kv_cache.py
│   ├── test_query.py
│   └── test_server.py
└── docs/                     # Documentation
    ├── api.md                # API documentation
    ├── frontend_setup.md     # Frontend setup guide
    ├── TROUBLESHOOTING.md    # Troubleshooting guide
    └── CONTRIBUTING.md       # Contributing guidelines
``` 