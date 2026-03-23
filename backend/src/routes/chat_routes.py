"""
Chat routes for FastAPI (SPEC-05).
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.helpers.db import get_db
from src.helpers.security import get_current_user
from src.models.schemas.chat_schemas import (
    CreateChatRequest,
    QueryRequest,
    UpdateChatRequest,
)
from src.controllers.chat_controller import (
    create_chat,
    list_chats,
    get_chat,
    delete_chat,
    rename_chat,
    query_chat,
    stream_query_chat,
    get_messages,
)
from src.helpers.logging_config import get_logger

logger = get_logger("chat.routes")

router = APIRouter(prefix="/chats", tags=["Chats"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_endpoint(
    body: CreateChatRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new chat session.

    - **title** (optional): Chat title. Auto-generated from first question if omitted.

    Requires a valid JWT access token.
    """
    return await create_chat(body.title, current_user, db)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
)
async def list_chats_endpoint(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all chats for the current user, newest first.

    Returns chat list with message counts and last message timestamps.

    Requires a valid JWT access token.
    """
    return await list_chats(current_user, db)


@router.get(
    "/{chat_id}",
    status_code=status.HTTP_200_OK,
)
async def get_chat_endpoint(
    chat_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a chat with all its messages.

    - **chat_id**: UUID of the chat

    Requires a valid JWT access token.
    """
    return await get_chat(chat_id, current_user, db)


@router.delete(
    "/{chat_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_chat_endpoint(
    chat_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a chat and all its messages.

    Requires a valid JWT access token.
    """
    return await delete_chat(chat_id, current_user, db)


@router.patch(
    "/{chat_id}",
    status_code=status.HTTP_200_OK,
)
async def rename_chat_endpoint(
    chat_id: str,
    body: UpdateChatRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Rename a chat.

    Requires a valid JWT access token.
    """
    return await rename_chat(chat_id, body.title, current_user, db)


@router.post(
    "/{chat_id}/query",
    status_code=status.HTTP_200_OK,
)
async def query_chat_endpoint(
    chat_id: str,
    body: QueryRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a research question and get a RAG-powered answer.

    - **question**: The research question
    - **document_ids** (optional): Restrict search to specific documents

    Requires a valid JWT access token.
    """
    return await query_chat(
        chat_id,
        body.question,
        body.document_ids,
        current_user,
        db,
    )


@router.post(
    "/{chat_id}/query/stream",
    status_code=status.HTTP_200_OK,
)
async def stream_query_endpoint(
    chat_id: str,
    body: QueryRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a research question and get a STREAMED RAG-powered answer.
    """
    return await stream_query_chat(
        chat_id,
        body.question,
        body.document_ids,
        current_user,
        db,
    )


@router.get(
    "/{chat_id}/messages",
    status_code=status.HTTP_200_OK,
)
async def get_messages_endpoint(
    chat_id: str,
    limit: int = Query(50, ge=1, le=200),
    before: str | None = Query(None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated message history for a chat.

    - **limit** (optional, default 50): Max messages to return
    - **before** (optional): Message UUID — return earlier messages

    Requires a valid JWT access token.
    """
    return await get_messages(chat_id, current_user, db, limit, before)

