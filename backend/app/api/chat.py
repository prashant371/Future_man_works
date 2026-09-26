"""
Chat API Routes

POST /api/chat                          — Send a message and get agent response
GET  /api/conversations                 — List user's conversations
POST /api/conversations                 — Create a new conversation
GET  /api/conversations/{id}            — Get conversation with messages
DELETE /api/conversations/{id}          — Delete a conversation
"""

from uuid import UUID
from typing import Optional

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.database import get_db
from app.database.models import User, Conversation, Message, PlatformConnection
from app.auth.security import get_current_user
from app.agent.agent import get_agent

router = APIRouter(prefix="/api", tags=["Chat"])


# ── Request / Response Schemas ────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    status: str  # completed, awaiting_confirmation, error
    task_id: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    last_message: Optional[str] = None


class ConversationDetailResponse(BaseModel):
    id: str
    title: str
    created_at: str
    messages: list[MessageResponse]


# ── Routes ────────────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to the AI agent and get a response."""
    agent = get_agent()

    # Get or create conversation
    conversation = None
    if request.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == UUID(request.conversation_id),
                Conversation.user_id == current_user.id,
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
    else:
        # Create a new conversation
        conversation = Conversation(
            user_id=current_user.id,
            title=request.message[:80] + ("..." if len(request.message) > 80 else ""),
        )
        db.add(conversation)
        await db.flush()

    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)
    await db.flush()

    # Load conversation history
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in messages[:-1]  # exclude the message we just added (it's the current input)
    ]

    # Get connected platforms for context
    result = await db.execute(
        select(PlatformConnection.platform).where(
            PlatformConnection.user_id == current_user.id
        )
    )
    connected_platforms = [row[0] for row in result.all()]

    # Process with AI agent
    agent_response = await agent.process_message(
        db=db,
        user_id=current_user.id,
        conversation_id=conversation.id,
        user_message=request.message,
        conversation_history=conversation_history,
        connected_platforms=connected_platforms,
    )

    # Save assistant message
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=agent_response["message"],
    )
    db.add(assistant_msg)

    return ChatResponse(
        message=agent_response["message"],
        conversation_id=str(conversation.id),
        status=agent_response.get("status", "completed"),
        task_id=agent_response.get("task_id"),
    )


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations for the current user."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(desc(Conversation.updated_at))
    )
    conversations = result.scalars().all()

    response = []
    for conv in conversations:
        # Get last message
        msg_result = await db.execute(
            select(Message.content)
            .where(Message.conversation_id == conv.id)
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        last_msg = msg_result.scalar_one_or_none()

        response.append(ConversationResponse(
            id=str(conv.id),
            title=conv.title,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
            last_message=last_msg,
        ))

    return response


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new empty conversation."""
    conversation = Conversation(
        user_id=current_user.id,
        title="New Conversation",
    )
    db.add(conversation)
    await db.flush()

    return ConversationResponse(
        id=str(conversation.id),
        title=conversation.title,
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with all its messages."""
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.id == UUID(conversation_id),
            Conversation.user_id == current_user.id,
        )
        .options(selectinload(Conversation.messages))
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return ConversationDetailResponse(
        id=str(conversation.id),
        title=conversation.title,
        created_at=conversation.created_at.isoformat(),
        messages=[
            MessageResponse(
                id=str(msg.id),
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at.isoformat(),
            )
            for msg in conversation.messages
        ],
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == UUID(conversation_id),
            Conversation.user_id == current_user.id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    await db.delete(conversation)
