"""
Chat controller — business logic for chat operations (SPEC-05).
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.models.db_scheams.Chat import Chat
from src.models.db_scheams.Message import Message
from src.models.db_scheams.document import Document
from src.services.retrieval_service import search_similar_chunks
from src.services.context_builder import build_prompt, get_source_summary
from src.services.llm_service import generate_answer, generate_chat_title
from src.models.db_scheams.user import User
from src.helpers.logging_config import get_logger

logger = get_logger("chat.controller")


# ═════════════════════════════════════════════════════════════════════════════
#  Private helpers
# ═════════════════════════════════════════════════════════════════════════════


async def _get_user_chat(
    chat_id: str,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Chat:
    """Fetch a chat by ID and verify ownership.

    Raises:
        HTTPException 404: Chat not found.
        HTTPException 403: Chat belongs to another user.
    """
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    if chat.user_id != user_id:
        logger.warning(
            "Access denied: user=%s tried to access chat=%s owned by user=%s",
            user_id,
            chat_id,
            chat.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return chat


async def _count_ready_documents(user_id: uuid.UUID, db: AsyncSession) -> int:
    """Count how many 'ready' documents the user has."""
    result = await db.execute(
        select(func.count(Document.id)).where(
            Document.user_id == user_id,
            Document.status == "ready",
        )
    )
    return result.scalar() or 0


async def _get_chat_history(
    chat_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 10,
) -> list[dict]:
    """Get recent conversation history for context building."""
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()

    # Reverse to get chronological order (oldest first)
    messages = list(reversed(messages))

    return [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]


# ═════════════════════════════════════════════════════════════════════════════
#  Public API — called by routes
# ═════════════════════════════════════════════════════════════════════════════


async def create_chat(
    title: str | None,
    current_user: User,
    db: AsyncSession,
) -> dict:
    """Create a new chat session."""
    chat = Chat(
        user_id=current_user.id,
        title=title,
    )
    db.add(chat)
    await db.commit()
    await db.refresh(chat)

    logger.info("Chat created: id=%s user=%s", chat.id, current_user.id)

    return {
        "id": str(chat.id),
        "title": chat.title,
        "created_at": chat.created_at,
    }


async def list_chats(
    current_user: User,
    db: AsyncSession,
) -> dict:
    """List all chats for the current user with message counts."""
    # Use outer join to compute message_count and last_message_at
    stmt = (
        select(
            Chat,
            func.count(Message.id).label("message_count"),
            func.max(Message.created_at).label("last_message_at"),
        )
        .outerjoin(Message, Chat.id == Message.chat_id)
        .where(Chat.user_id == current_user.id)
        .group_by(Chat.id)
        .order_by(Chat.created_at.desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    chats = []
    for row in rows:
        chat = row[0]
        message_count = row[1]
        last_message_at = row[2]

        chats.append({
            "id": str(chat.id),
            "title": chat.title,
            "created_at": chat.created_at,
            "message_count": message_count,
            "last_message_at": last_message_at,
        })

    logger.info("Listed %d chats for user=%s", len(chats), current_user.id)

    return {"chats": chats, "total": len(chats)}


async def get_chat(
    chat_id: str,
    current_user: User,
    db: AsyncSession,
) -> dict:
    """Get a chat with all its messages."""
    chat = await _get_user_chat(chat_id, current_user.id, db)

    # Retrieve messages in ascending order
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat.id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()

    return {
        "id": str(chat.id),
        "title": chat.title,
        "created_at": chat.created_at,
        "messages": [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "source_chunks": msg.source_chunks,
                "created_at": msg.created_at,
            }
            for msg in messages
        ],
    }


async def delete_chat(
    chat_id: str,
    current_user: User,
    db: AsyncSession,
) -> dict:
    """Delete a chat and all its messages (cascade)."""
    chat = await _get_user_chat(chat_id, current_user.id, db)

    await db.delete(chat)
    await db.commit()

    logger.info("Chat deleted: id=%s", chat_id)

    return {"message": "Chat deleted successfully"}


async def rename_chat(
    chat_id: str,
    title: str,
    current_user: User,
    db: AsyncSession,
) -> dict:
    """Rename a chat."""
    chat = await _get_user_chat(chat_id, current_user.id, db)

    chat.title = title
    await db.commit()
    await db.refresh(chat)

    logger.info("Chat renamed: id=%s title=%s", chat_id, title)

    return {
        "message": "Chat updated successfully",
        "id": str(chat.id),
        "title": chat.title,
    }


async def query_chat(
    chat_id: str,
    question: str,
    document_ids: list[str] | None,
    current_user: User,
    db: AsyncSession,
) -> dict:
    """Process a research question through the full RAG pipeline."""
    # 1. Verify chat belongs to user
    chat = await _get_user_chat(chat_id, current_user.id, db)

    # 2. Check user has ready documents
    ready_count = await _count_ready_documents(current_user.id, db)
    if ready_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have no processed documents. Please upload PDFs first.",
        )

    # 3. Get conversation history
    history = await _get_chat_history(chat.id, db, limit=10)

    # 4. Retrieve relevant chunks (SPEC-04)
    try:
        chunks = await search_similar_chunks(
            query=question,
            user_id=str(current_user.id),
            db=db,
            top_k=5,
            document_ids=document_ids,
        )
    except Exception as e:
        logger.error("Retrieval failed for chat=%s: %s", chat_id, str(e))
        # Save the user message even if retrieval fails
        user_msg = Message(
            chat_id=chat.id,
            role="user",
            content=question,
        )
        db.add(user_msg)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve relevant documents. Please try again.",
        )

    # 5. Save user message FIRST (ensures persistence even if LLM fails)
    user_msg = Message(
        chat_id=chat.id,
        role="user",
        content=question,
    )
    db.add(user_msg)
    await db.flush()  # Assign ID without committing

    # 6. Build prompt (SPEC-04)
    messages = build_prompt(question, chunks, history)
    sources = get_source_summary(chunks)

    # 7. Generate answer
    try:
        answer = await generate_answer(messages)
    except Exception as e:
        # Commit the user message even if LLM fails (rule #7)
        await db.commit()
        logger.error("LLM failed for chat=%s: %s", chat_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate answer. Please try again.",
        )

    # 8. Save assistant message with sources
    assistant_msg = Message(
        chat_id=chat.id,
        role="assistant",
        content=answer,
        source_chunks=sources,
    )
    db.add(assistant_msg)

    # 9. Auto-generate chat title if first message
    if chat.title is None:
        try:
            chat.title = await generate_chat_title(question)
        except Exception as e:
            logger.warning("Title generation failed for chat=%s: %s", chat_id, str(e))
            # Non-fatal — leave title as None

    await db.commit()
    await db.refresh(assistant_msg)

    logger.info(
        "Query completed: chat=%s sources=%d",
        chat_id,
        len(sources),
    )

    # 10. Return response
    return {
        "message_id": str(assistant_msg.id),
        "answer": answer,
        "sources": sources,
    }


async def get_messages(
    chat_id: str,
    current_user: User,
    db: AsyncSession,
    limit: int = 50,
    before: str | None = None,
) -> dict:
    """Get paginated message history for a chat."""
    chat = await _get_user_chat(chat_id, current_user.id, db)

    # Base query
    query = select(Message).where(Message.chat_id == chat.id)

    # If 'before' cursor is provided, get messages before that one
    if before:
        # Look up the reference message to get its created_at
        ref_result = await db.execute(
            select(Message).where(Message.id == before, Message.chat_id == chat.id)
        )
        ref_msg = ref_result.scalar_one_or_none()
        if not ref_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reference message not found",
            )
        query = query.where(Message.created_at < ref_msg.created_at)

    # Get total count (without limit)
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply ordering and limit
    query = query.order_by(Message.created_at.asc()).limit(limit)

    result = await db.execute(query)
    messages = result.scalars().all()

    has_more = len(messages) < total

    return {
        "messages": [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "source_chunks": msg.source_chunks,
                "created_at": msg.created_at,
            }
            for msg in messages
        ],
        "total": total,
        "has_more": has_more,
    }
