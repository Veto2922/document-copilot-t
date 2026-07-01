"""
Chat API router.

Handles CRUD operations for chat threads and messages, and provides a mock
streaming endpoint to verify end-to-end integration before wiring up the LLM.
"""

import asyncio
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import structlog

from app.auth.dependencies import get_current_user, CurrentUser
from app.database.session import get_db_session, async_session_maker
from app.database.models import ChatThread, ChatMessage, User

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class ThreadCreate(BaseModel):
    """Payload to create a new chat thread."""
    title: Optional[str] = Field(default=None, max_length=255)


from datetime import datetime

class ThreadResponse(BaseModel):
    """API response schema for a chat thread."""
    id: uuid.UUID
    user_id: uuid.UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageParam(BaseModel):
    """A single message representation inside the message list."""
    role: str = Field(..., description="The role of the sender: 'user' or 'assistant'")
    content: str = Field(..., description="The message content")


class StreamRequest(BaseModel):
    """Payload to request a streaming chat response."""
    messages: list[MessageParam] = Field(..., min_length=1)
    thread_id: uuid.UUID


class MessageResponse(BaseModel):
    """API response schema for a chat message."""
    id: uuid.UUID
    thread_id: uuid.UUID
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def ensure_user_exists(db: AsyncSession, user_id: uuid.UUID, email: str) -> User:
    """
    Ensure the user exists in the local SQL database.
    Performs an upsert if the user row is missing.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    
    if not db_user:
        db_user = User(id=user_id, email=email)
        db.add(db_user)
        try:
            await db.commit()
            await db.refresh(db_user)
        except IntegrityError:
            await db.rollback()
            # Select again in case of concurrent creation
            result = await db.execute(select(User).where(User.id == user_id))
            db_user = result.scalar_one_or_none()
            if not db_user:
                raise
    return db_user


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/threads", response_model=list[ThreadResponse])
async def list_threads(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ChatThread]:
    """List all chat threads belonging to the authenticated user."""
    await ensure_user_exists(db, user.id, user.email)
    
    result = await db.execute(
        select(ChatThread)
        .where(ChatThread.user_id == user.id)
        .order_by(ChatThread.updated_at.desc())
    )
    threads = result.scalars().all()
    # Explicitly validate using Pydantic model_validate to handle datetime parsing
    return [ThreadResponse.model_validate(t) for t in threads]


@router.post("/threads", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    payload: ThreadCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ThreadResponse:
    """Create a new chat thread for the authenticated user."""
    await ensure_user_exists(db, user.id, user.email)
    
    title = payload.title.strip() if payload.title else "New Chat"
    thread = ChatThread(user_id=user.id, title=title)
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    return ThreadResponse.model_validate(thread)


@router.get("/threads/{thread_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    thread_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[MessageResponse]:
    """Fetch all messages for a specific chat thread."""
    result = await db.execute(select(ChatThread).where(ChatThread.id == thread_id))
    thread = result.scalar_one_or_none()
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    if thread.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have access to this thread"
        )
    
    msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = msg_result.scalars().all()
    return [MessageResponse.model_validate(m) for m in messages]


@router.post("/stream")
async def chat_stream(
    payload: StreamRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Handle streaming chat requests.

    Accepts the current list of messages, validates thread ownership, persists
    the new user message, streams a stubbed assistant reply, and persists the
    reply when complete.
    """
    # 1. Fetch thread and verify access
    result = await db.execute(select(ChatThread).where(ChatThread.id == payload.thread_id))
    thread = result.scalar_one_or_none()
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    if thread.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have access to this thread"
        )
    
    # 2. Extract and insert the new user message
    last_msg = payload.messages[-1]
    if last_msg.role != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Last message must be from user"
        )
    
    # Check if the user message already exists to prevent duplicate insertion (e.g. on client retries)
    recent_msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.thread_id == payload.thread_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(1)
    )
    recent_msg = recent_msg_result.scalar_one_or_none()
    
    if not recent_msg or recent_msg.role != "user" or recent_msg.content != last_msg.content:
        user_message = ChatMessage(
            thread_id=payload.thread_id,
            role="user",
            content=last_msg.content
        )
        db.add(user_message)
        thread.updated_at = func.now()
        await db.commit()
    
    # Release the database session connection during slow streaming
    await db.close()

    # 3. Stream generator for mock assistant reply
    async def response_generator():
        reply_content = (
            "This is a stubbed assistant response. In a future phase, I will be integrated with "
            "Gemini and retrieval systems to perform semantic queries on SEC filings. For now, "
            "this mock stream verifies that the end-to-end connection is operating correctly."
        )
        
        words = reply_content.split(" ")
        accumulated_reply = ""
        
        for i, word in enumerate(words):
            chunk = word if i == 0 else " " + word
            accumulated_reply += chunk
            yield chunk
            # Yield control back to the event loop
            await asyncio.sleep(0.04)
            
        # 4. Save the assistant message to the database once the stream completes
        async with async_session_maker() as session:
            try:
                t_result = await session.execute(
                    select(ChatThread).where(ChatThread.id == payload.thread_id)
                )
                t_obj = t_result.scalar_one_or_none()
                if t_obj:
                    assistant_msg = ChatMessage(
                        thread_id=payload.thread_id,
                        role="assistant",
                        content=accumulated_reply
                    )
                    session.add(assistant_msg)
                    t_obj.updated_at = func.now()
                    await session.commit()
                    logger.info("Persisted assistant message to database", thread_id=str(payload.thread_id))
            except Exception as exc:
                logger.error("Failed to save assistant message", thread_id=str(payload.thread_id), error=str(exc))
                await session.rollback()

    return StreamingResponse(
        response_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
