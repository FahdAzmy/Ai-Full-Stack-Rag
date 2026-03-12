"""
Citation routes for FastAPI (SPEC-06).

Endpoints:
  - GET /citations/messages/{message_id}       — Get citations for a message
  - GET /citations/export                      — Export citations as plain text
"""

import uuid
from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.helpers.db import get_db
from src.helpers.security import get_current_user
from src.controllers.citation_controller import (
    get_message_citations,
    export_citations,
)
from src.helpers.logging_config import get_logger

logger = get_logger("citation.routes")


class CitationFormat(str, Enum):
    apa = "apa"
    mla = "mla"
    bibtex = "bibtex"


router = APIRouter(prefix="/citations", tags=["Citations"])


@router.get(
    "/messages/{message_id}",
    status_code=status.HTTP_200_OK,
)
async def get_message_citations_endpoint(
    message_id: str,
    format: Optional[str] = Query(None, description="Citation format: apa, mla, bibtex, or all"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get citations for all sources used in a specific assistant message.

    - **message_id**: UUID of the message
    - **format** (optional): Citation format (apa, mla, bibtex). Defaults to all formats.

    Requires a valid JWT access token.
    """
    return await get_message_citations(message_id, current_user, db, format)


@router.get(
    "/export",
    status_code=status.HTTP_200_OK,
    response_class=PlainTextResponse,
)
async def export_citations_endpoint(
    message_id: uuid.UUID = Query(..., description="UUID of the message to export citations for"),
    format: CitationFormat = Query(..., description="Citation format: apa, mla, or bibtex"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export citations for a message as plain text.

    - **message_id**: UUID of the message
    - **format**: Citation format (apa, mla, bibtex)

    Requires a valid JWT access token.
    Returns plain text response with formatted citations.
    """
    text = await export_citations(str(message_id), format.value, current_user, db)
    return PlainTextResponse(content=text, media_type="text/plain")
