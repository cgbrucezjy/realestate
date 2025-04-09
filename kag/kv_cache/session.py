"""
Session management for the KAG system.

This module handles managing user sessions, including tracking conversation
history and associating sessions with KV caches.
"""

import time
import uuid
from typing import Dict, List, Optional, Any, Tuple

from kag.utils.logger import get_logger
from kag.config import get_settings

# Initialize logger
logger = get_logger(__name__)

# Get settings
settings = get_settings()

class Session:
    """
    Represents a user conversation session.
    
    A session contains:
    - User ID
    - Creation and last access timestamps
    - Conversation history
    - Associated document IDs
    """
    
    def __init__(self, session_id: str, user_id: str):
        """
        Initialize a new session.
        
        Args:
            session_id: The session ID
            user_id: The user ID
        """
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = time.time()
        self.last_accessed_at = time.time()
        self.conversation_history = []
        self.document_ids = []
    
    def add_message(self, message: Dict[str, Any]) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            message: The message to add
        """
        self.conversation_history.append(message)
        self.last_accessed_at = time.time()
    
    def add_documents(self, document_ids: List[str]) -> None:
        """
        Associate documents with this session.
        
        Args:
            document_ids: List of document IDs to associate
        """
        self.document_ids.extend([doc_id for doc_id in document_ids if doc_id not in self.document_ids])
        self.last_accessed_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert session to dictionary.
        
        Returns:
            Dictionary representation of the session
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "last_accessed_at": self.last_accessed_at,
            "conversation_length": len(self.conversation_history),
            "document_count": len(self.document_ids),
            "document_ids": self.document_ids
        }


class SessionManager:
    """
    Manages user sessions for the KAG system.
    
    This class handles creating, retrieving, and managing user sessions.
    It also handles cleaning up expired sessions.
    """
    
    def __init__(self):
        """Initialize the session manager."""
        self.sessions = {}  # Maps session_id to Session
        self.user_sessions = {}  # Maps user_id to list of session_ids
        self.session_timeout = settings.session_timeout
    
    def get_or_create_session(self, session_id: str, user_id: str) -> Session:
        """
        Get or create a session.
        
        Args:
            session_id: The session ID
            user_id: The user ID
            
        Returns:
            The session
        """
        # Check if session exists
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.last_accessed_at = time.time()
            return session
        
        # Create new session
        session = Session(session_id, user_id)
        self.sessions[session_id] = session
        
        # Associate session with user
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)
        
        logger.info(f"Created new session {session_id} for user {user_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.
        
        Args:
            session_id: The session ID
            
        Returns:
            The session, or None if not found
        """
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        session.last_accessed_at = time.time()
        return session
    
    def update_session(
        self, 
        session_id: str, 
        messages: List[Dict[str, Any]], 
        response: Dict[str, Any]
    ) -> None:
        """
        Update a session with new messages and response.
        
        Args:
            session_id: The session ID
            messages: The new messages
            response: The response
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found for update")
            return
        
        # Add messages to conversation history
        for message in messages:
            session.add_message(message)
        
        # Add response to conversation history
        session.add_message(response)
        
        logger.debug(f"Updated session {session_id} with {len(messages)} messages and response")
    
    def associate_documents(self, session_id: str, document_ids: List[str]) -> None:
        """
        Associate documents with a session.
        
        Args:
            session_id: The session ID
            document_ids: List of document IDs to associate
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found for document association")
            return
        
        session.add_documents(document_ids)
        logger.debug(f"Associated documents {document_ids} with session {session_id}")
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            List of sessions for the user
        """
        if user_id not in self.user_sessions:
            return []
        
        user_session_ids = self.user_sessions[user_id]
        user_sessions = [
            self.sessions[session_id].to_dict() 
            for session_id in user_session_ids 
            if session_id in self.sessions
        ]
        
        return user_sessions
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if the session was deleted, False otherwise
        """
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        user_id = session.user_id
        
        # Remove session from user sessions
        if user_id in self.user_sessions:
            if session_id in self.user_sessions[user_id]:
                self.user_sessions[user_id].remove(session_id)
        
        # Remove session
        del self.sessions[session_id]
        
        logger.info(f"Deleted session {session_id}")
        return True
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of expired sessions cleaned up
        """
        now = time.time()
        expired_sessions = [
            session_id 
            for session_id, session in self.sessions.items() 
            if now - session.last_accessed_at > self.session_timeout
        ]
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about sessions.
        
        Returns:
            Dictionary containing statistics about sessions
        """
        return {
            "total_sessions": len(self.sessions),
            "total_users": len(self.user_sessions),
            "sessions_per_user": {
                user_id: len(session_ids) 
                for user_id, session_ids in self.user_sessions.items()
            }
        } 