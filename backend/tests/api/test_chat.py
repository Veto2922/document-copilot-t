"""
Unit tests for the Chat API router.
"""

import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status

from app.database.models import ChatThread, ChatMessage, User
from tests.conftest import TEST_USER_ID, TEST_USER_EMAIL


def test_list_threads_empty(client: TestClient, mock_db: AsyncMock):
    """Test GET /chat/threads returning an empty list."""
    # Mock user exists check
    mock_user_result = MagicMock()
    mock_user_result.scalar_one_or_none.return_value = User(id=TEST_USER_ID, email=TEST_USER_EMAIL)
    
    # Mock thread select query
    mock_thread_result = MagicMock()
    mock_thread_result.scalars.return_value.all.return_value = []
    
    # Configure mock execute responses in order:
    # 1. select User
    # 2. select ChatThread
    mock_db.execute.side_effect = [mock_user_result, mock_thread_result]
    
    response = client.get("/chat/threads")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_create_thread(client: TestClient, mock_db: AsyncMock):
    """Test POST /chat/threads creates a thread successfully."""
    # Mock user select query
    mock_user_result = MagicMock()
    mock_user_result.scalar_one_or_none.return_value = User(id=TEST_USER_ID, email=TEST_USER_EMAIL)
    mock_db.execute.return_value = mock_user_result
    
    # Mock refresh side-effect to assign database-generated fields
    async def mock_refresh(obj):
        obj.id = uuid.uuid4()
        from datetime import datetime, timezone
        obj.created_at = datetime.now(timezone.utc)
        obj.updated_at = datetime.now(timezone.utc)
    mock_db.refresh.side_effect = mock_refresh
    
    thread_title = "Filing Analysis"
    response = client.post("/chat/threads", json={"title": thread_title})
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == thread_title
    assert "id" in data
    assert data["user_id"] == str(TEST_USER_ID)
    
    # Verify the thread was added to the session
    assert mock_db.add.called
    assert mock_db.commit.called


def test_get_messages_unauthorized_403(client: TestClient, mock_db: AsyncMock):
    """Test GET /chat/threads/{id}/messages raises 403 for another user's thread."""
    other_user_id = uuid.uuid4()
    thread_id = uuid.uuid4()
    
    # Mock thread that belongs to another user
    other_thread = ChatThread(id=thread_id, user_id=other_user_id, title="Secret Thread")
    
    mock_thread_result = MagicMock()
    mock_thread_result.scalar_one_or_none.return_value = other_thread
    mock_db.execute.return_value = mock_thread_result
    
    response = client.get(f"/chat/threads/{thread_id}/messages")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Forbidden" in response.json()["detail"]


def test_get_messages_not_found_404(client: TestClient, mock_db: AsyncMock):
    """Test GET /chat/threads/{id}/messages raises 404 if thread doesn't exist."""
    thread_id = uuid.uuid4()
    
    # Mock thread not found
    mock_thread_result = MagicMock()
    mock_thread_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_thread_result
    
    response = client.get(f"/chat/threads/{thread_id}/messages")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_chat_stream_auth_403(client: TestClient, mock_db: AsyncMock):
    """Test POST /chat/stream raises 403 if thread is owned by another user."""
    other_user_id = uuid.uuid4()
    thread_id = uuid.uuid4()
    
    # Mock thread belonging to someone else
    other_thread = ChatThread(id=thread_id, user_id=other_user_id, title="Forbidden Thread")
    mock_thread_result = MagicMock()
    mock_thread_result.scalar_one_or_none.return_value = other_thread
    mock_db.execute.return_value = mock_thread_result
    
    response = client.post(
        "/chat/stream",
        json={"thread_id": str(thread_id), "messages": [{"role": "user", "content": "hi"}]}
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_chat_stream_success(client: TestClient, mock_db: AsyncMock):
    """Test POST /chat/stream streams chunks and stores user message."""
    thread_id = uuid.uuid4()
    thread = ChatThread(id=thread_id, user_id=TEST_USER_ID, title="Active Thread")
    
    # Mock thread query and recent message query
    mock_thread_result = MagicMock()
    mock_thread_result.scalar_one_or_none.return_value = thread
    
    mock_recent_result = MagicMock()
    mock_recent_result.scalar_one_or_none.return_value = None
    
    mock_db.execute.side_effect = [mock_thread_result, mock_recent_result]
    
    response = client.post(
        "/chat/stream",
        json={"thread_id": str(thread_id), "messages": [{"role": "user", "content": "Hello world!"}]}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"].startswith("text/plain")
    
    # Read streamed text content
    content = response.text
    assert "stubbed assistant response" in content
    
    # Verify user message was added
    assert mock_db.add.called
    assert mock_db.commit.called
