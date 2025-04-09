"""
Document processor for the KAG system.

This module handles processing documents for the KAG system, including
loading, chunking, and preparing documents for loading into KV cache.
"""

import base64
import json
import os
import tempfile
import uuid
from typing import Dict, List, Optional, Any, BinaryIO, Tuple

import aiosqlite
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
    BSHTMLLoader
)

from kag.utils.logger import get_logger
from kag.config import get_settings

# Initialize logger
logger = get_logger(__name__)

# Get settings
settings = get_settings()

class DocumentProcessor:
    """
    Processes documents for the KAG system.
    
    This class handles:
    - Loading documents from various formats (PDF, DOCX, TXT, etc.)
    - Chunking documents into manageable pieces
    - Storing document chunks in the database
    - Retrieving document chunks for KV cache loading
    """
    
    def __init__(self):
        """Initialize the document processor."""
        self.db_path = settings.database_url.replace("sqlite:///", "")
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len
        )
        
        # Ensure database exists
        self._create_tables_if_not_exist()
    
    async def _create_tables_if_not_exist(self) -> None:
        """Create database tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            # Create documents table
            await db.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                user_id TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
            """)
            
            # Create document chunks table
            await db.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
            )
            """)
            
            await db.commit()
            logger.debug("Database tables created if they didn't exist")
    
    async def process_document(
        self,
        document: str,
        document_type: str,
        document_name: str,
        document_id: Optional[str] = None,
        user_id: str = "anonymous"
    ) -> List[str]:
        """
        Process a document and store its chunks in the database.
        
        Args:
            document: Base64 encoded document or raw text
            document_type: Type of document (pdf, txt, docx, etc.)
            document_name: Name of the document
            document_id: Optional ID for the document
            user_id: ID of the user uploading the document
            
        Returns:
            List of document chunk contents
        """
        # Generate document ID if not provided
        if not document_id:
            document_id = str(uuid.uuid4())
        
        # Load document content based on type
        chunks = await self._load_and_chunk_document(document, document_type)
        
        # Store document and chunks in database
        await self._store_document(document_id, document_name, document_type, user_id, chunks)
        
        return [chunk for chunk in chunks]
    
    async def _load_and_chunk_document(
        self,
        document: str,
        document_type: str
    ) -> List[str]:
        """
        Load and chunk a document.
        
        Args:
            document: Base64 encoded document or raw text
            document_type: Type of document (pdf, txt, docx, etc.)
            
        Returns:
            List of document chunks
        """
        document_content = None
        
        try:
            # Handle different document types
            if document_type.lower() == "txt" or document_type.lower() == "text":
                # Raw text
                document_content = document
                chunks = self.text_splitter.split_text(document_content)
            else:
                # Binary document (PDF, DOCX, etc.)
                # Try to decode base64
                try:
                    decoded_content = base64.b64decode(document)
                except:
                    # If not base64, assume it's already decoded
                    decoded_content = document.encode('utf-8')
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{document_type.lower()}") as temp_file:
                    temp_file.write(decoded_content)
                    temp_path = temp_file.name
                
                # Process based on file type
                try:
                    if document_type.lower() == "pdf":
                        loader = PyPDFLoader(temp_path)
                    elif document_type.lower() == "docx":
                        loader = Docx2txtLoader(temp_path)
                    elif document_type.lower() == "md" or document_type.lower() == "markdown":
                        loader = UnstructuredMarkdownLoader(temp_path)
                    elif document_type.lower() == "html":
                        loader = BSHTMLLoader(temp_path)
                    else:
                        # Default to text loader
                        loader = TextLoader(temp_path)
                    
                    # Load document
                    documents = loader.load()
                    
                    # Combine and split text
                    combined_text = "\n\n".join([doc.page_content for doc in documents])
                    chunks = self.text_splitter.split_text(combined_text)
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
            
            logger.info(f"Document loaded and split into {len(chunks)} chunks")
            return chunks
        
        except Exception as e:
            logger.error(f"Error loading document: {str(e)}")
            raise
    
    async def _store_document(
        self,
        document_id: str,
        document_name: str,
        document_type: str,
        user_id: str,
        chunks: List[str]
    ) -> None:
        """
        Store a document and its chunks in the database.
        
        Args:
            document_id: ID of the document
            document_name: Name of the document
            document_type: Type of document
            user_id: ID of the user uploading the document
            chunks: List of document chunks
        """
        import time
        
        async with aiosqlite.connect(self.db_path) as db:
            # Store document
            await db.execute(
                "INSERT OR REPLACE INTO documents (id, name, type, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
                (document_id, document_name, document_type, user_id, int(time.time()))
            )
            
            # Delete existing chunks if any
            await db.execute(
                "DELETE FROM document_chunks WHERE document_id = ?",
                (document_id,)
            )
            
            # Store chunks
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                await db.execute(
                    "INSERT INTO document_chunks (id, document_id, chunk_index, content) VALUES (?, ?, ?, ?)",
                    (chunk_id, document_id, i, chunk)
                )
            
            await db.commit()
            logger.info(f"Document {document_id} with {len(chunks)} chunks stored in database")
    
    async def get_document_chunks(
        self,
        document_id: str,
        user_id: Optional[str] = None
    ) -> List[str]:
        """
        Get chunks for a document.
        
        Args:
            document_id: ID of the document
            user_id: Optional user ID for permission check
            
        Returns:
            List of document chunks
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Check if user has access to document
            if user_id:
                cursor = await db.execute(
                    "SELECT id FROM documents WHERE id = ? AND user_id = ?",
                    (document_id, user_id)
                )
                result = await cursor.fetchone()
                if not result:
                    logger.warning(f"User {user_id} does not have access to document {document_id}")
                    return []
            
            # Get chunks
            cursor = await db.execute(
                "SELECT content FROM document_chunks WHERE document_id = ? ORDER BY chunk_index",
                (document_id,)
            )
            chunks = await cursor.fetchall()
            
            return [chunk[0] for chunk in chunks]
    
    async def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of documents
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Get documents
            cursor = await db.execute(
                """
                SELECT d.id, d.name, d.type, d.created_at, COUNT(c.id) as chunk_count
                FROM documents d
                LEFT JOIN document_chunks c ON d.id = c.document_id
                WHERE d.user_id = ?
                GROUP BY d.id
                ORDER BY d.created_at DESC
                """,
                (user_id,)
            )
            rows = await cursor.fetchall()
            
            # Convert to list of dictionaries
            documents = []
            for row in rows:
                documents.append({
                    "id": row[0],
                    "name": row[1],
                    "type": row[2],
                    "created_at": row[3],
                    "chunk_count": row[4]
                })
            
            return documents
    
    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """
        Delete a document.
        
        Args:
            document_id: ID of the document
            user_id: ID of the user
            
        Returns:
            True if document was deleted, False otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Check if user has access to document
            cursor = await db.execute(
                "SELECT id FROM documents WHERE id = ? AND user_id = ?",
                (document_id, user_id)
            )
            result = await cursor.fetchone()
            if not result:
                logger.warning(f"User {user_id} does not have access to document {document_id}")
                return False
            
            # Delete document (will cascade to chunks)
            await db.execute(
                "DELETE FROM documents WHERE id = ?",
                (document_id,)
            )
            
            await db.commit()
            logger.info(f"Document {document_id} deleted")
            return True 