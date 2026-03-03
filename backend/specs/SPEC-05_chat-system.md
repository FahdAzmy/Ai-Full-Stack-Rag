# SPEC-05: Chat System & LLM Integration

> **Status:** 🔲 Todo  
> **Dependencies:** SPEC-04 (Retrieval Layer)  
> **Priority:** P0 — Critical Path  
> **Estimated effort:** 4–5 days

---

## Overview

Complete chat system with CRUD operations and LLM-powered answer generation using RAG. When a user sends a question:

1. A new user message is saved
2. The retrieval layer (SPEC-04) finds relevant chunks  
3. A prompt is built with context + history
4. The LLM generates an answer
5. The assistant message is saved with source references
6. The answer + sources are returned to the user

```
User Question
    │
    ▼
┌─────────────────────────────┐
│       CHAT SYSTEM           │
│                             │
│  1. Save user message       │
│  2. Call Retrieval Layer     │──► SPEC-04
│  3. Build prompt            │
│  4. Call LLM                │──► OpenAI API
│  5. Save assistant message  │
│  6. Return response         │
│                             │
└─────────────────────────────┘
    │
    ▼
Answer + Sources + Citations
```

---

## Database Changes

### Modify `messages` table

**File:** `src/models/db_scheams/Message.py`

Add `source_chunks` JSON column to store referenced sources per message:

| Column | Type | Constraints | New? | Purpose |
|---|---|---|---|---|
| `id` | UUID | PK | ❌ | Primary key |
| `chat_id` | UUID | FK → chats.id | ❌ | Parent chat |
| `role` | String(20) | NOT NULL | ❌ | "user" or "assistant" |
| `content` | Text | NOT NULL | ❌ | Message text |
| `source_chunks` | JSON | nullable | ✅ | Sources used for this response |
| `embedding` | Vector(1536) | nullable | ❌ | Optional semantic memory |
| `created_at` | DateTime | default utcnow | ❌ | |

**Updated model:**

```python
from sqlalchemy import Column, Text, DateTime, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from src.helpers.db import Base
import uuid
from datetime import datetime


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False)

    role = Column(String(20), nullable=False)      # "user" | "assistant"
    content = Column(Text, nullable=False)

    # Sources used to generate this response (assistant messages only)
    source_chunks = Column(JSON, nullable=True)    # NEW

    # Optional semantic memory
    embedding = Column(Vector(1536), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")
```

### `source_chunks` JSON Structure

For assistant messages, `source_chunks` stores an array of source references:

```json
[
  {
    "source_number": 1,
    "chunk_id": "uuid-...",
    "document_id": "uuid-...",
    "title": "Deep Learning in Medicine",
    "author": "Smith, John",
    "year": "2020",
    "page_number": 15,
    "file_name": "deep_learning.pdf",
    "similarity": 0.87,
    "excerpt": "Convolutional neural networks have shown..."
  }
]
```

For user messages, `source_chunks` is `null`.

### Migration

```bash
alembic revision --autogenerate -m "add source_chunks to messages"
alembic upgrade head
```

---

## API Endpoints

All endpoints require `Authorization: Bearer <access_token>` header.

---

### `POST /chats/`

Create a new chat session.

**Request Body (optional):**
```json
{
  "title": "Literature Review Questions"
}
```

If no title is provided, it will be auto-generated from the first question.

**Success Response (201):**
```json
{
  "id": "chat-uuid-...",
  "title": null,
  "created_at": "2026-03-01T10:30:00Z"
}
```

---

### `GET /chats/`

List all chats for the current user, newest first.

**Success Response (200):**
```json
{
  "chats": [
    {
      "id": "chat-uuid-1",
      "title": "Deep Learning Questions",
      "created_at": "2026-03-01T10:30:00Z",
      "message_count": 12,
      "last_message_at": "2026-03-01T11:45:00Z"
    },
    {
      "id": "chat-uuid-2",
      "title": "NLP Survey Review",
      "created_at": "2026-02-28T14:00:00Z",
      "message_count": 6,
      "last_message_at": "2026-02-28T15:20:00Z"
    }
  ],
  "total": 2
}
```

---

### `GET /chats/{chat_id}`

Get a chat with all its messages.

**Success Response (200):**
```json
{
  "id": "chat-uuid-1",
  "title": "Deep Learning Questions",
  "created_at": "2026-03-01T10:30:00Z",
  "messages": [
    {
      "id": "msg-uuid-1",
      "role": "user",
      "content": "What are the limitations of CNN in medical imaging?",
      "source_chunks": null,
      "created_at": "2026-03-01T10:30:15Z"
    },
    {
      "id": "msg-uuid-2",
      "role": "assistant",
      "content": "Based on your uploaded papers, the main limitations of CNN...\n\n## References Used\n- [Source 1] ...",
      "source_chunks": [
        {
          "source_number": 1,
          "title": "Deep Learning in Medicine",
          "author": "Smith, John",
          "year": "2020",
          "page_number": 15,
          "similarity": 0.87,
          "excerpt": "Despite impressive results, CNNs face..."
        }
      ],
      "created_at": "2026-03-01T10:30:22Z"
    }
  ]
}
```

**Error Responses:**

| Status | Condition | Response |
|---|---|---|
| 404 | Chat not found | `{"detail": "Chat not found"}` |
| 403 | Not owner | `{"detail": "Access denied"}` |

---

### `DELETE /chats/{chat_id}`

Delete a chat and all its messages.

**Success Response (200):**
```json
{
  "message": "Chat deleted successfully"
}
```

---

### `PATCH /chats/{chat_id}`

Rename a chat.

**Request Body:**
```json
{
  "title": "Updated Chat Title"
}
```

**Success Response (200):**
```json
{
  "message": "Chat updated successfully",
  "id": "chat-uuid-...",
  "title": "Updated Chat Title"
}
```

---

### `POST /chats/{chat_id}/query` ⭐ Main Endpoint

Send a research question and get a RAG-powered answer.

**Request Body:**
```json
{
  "question": "What are the main limitations of using CNN for medical image analysis?",
  "document_ids": ["doc-uuid-1", "doc-uuid-2"]
}
```

- `question` — required, the research question
- `document_ids` — optional, restrict search to specific documents. If null/empty, searches all user's documents.

**Success Response (200):**
```json
{
  "message_id": "msg-uuid-...",
  "answer": "Based on your uploaded research papers, the main limitations of CNN in medical imaging include:\n\n1. **Data Requirements** — CNNs require large annotated datasets [Source 1]...\n\n## References Used\n- [Source 1] Smith (2020), p.15\n- [Source 2] Doe (2021), p.8",
  "sources": [
    {
      "source_number": 1,
      "title": "Deep Learning in Medicine",
      "author": "Smith, John",
      "year": "2020",
      "page_number": 15,
      "file_name": "deep_learning.pdf",
      "document_id": "doc-uuid-1",
      "chunk_id": "chunk-uuid-1",
      "similarity": 0.87,
      "excerpt": "Despite impressive results, CNNs face several limitations..."
    },
    {
      "source_number": 2,
      "title": "CNN Challenges in Healthcare",
      "author": "Doe, Jane",
      "year": "2021",
      "page_number": 8,
      "file_name": "cnn_challenges.pdf",
      "document_id": "doc-uuid-2",
      "chunk_id": "chunk-uuid-2",
      "similarity": 0.82,
      "excerpt": "The primary challenge remains the need for..."
    }
  ]
}
```

**Error Responses:**

| Status | Condition | Response |
|---|---|---|
| 400 | Empty question | `{"detail": "Question cannot be empty"}` |
| 400 | No ready documents | `{"detail": "You have no processed documents. Please upload PDFs first."}` |
| 404 | Chat not found | `{"detail": "Chat not found"}` |
| 403 | Not owner | `{"detail": "Access denied"}` |
| 500 | LLM API error | `{"detail": "Failed to generate answer. Please try again."}` |

**Side Effects:**
1. User message saved to `messages` table
2. Assistant message saved with `source_chunks` JSON
3. Chat title auto-generated from first question (if currently null)

---

### `GET /chats/{chat_id}/messages`

Get message history for a chat (paginated).

**Query Parameters:**
- `limit` (optional, default 50): Max messages to return
- `before` (optional): Message UUID — get messages before this one

**Success Response (200):**
```json
{
  "messages": [...],
  "total": 24,
  "has_more": false
}
```

---

## LLM Service

**New file:** `src/services/llm_service.py`

```python
"""
LLM Service — Generate answers using OpenAI GPT models.

Supports both complete (blocking) and streaming responses.
"""
from openai import OpenAI
from src.helpers.config import settings
from src.helpers.logging_config import get_logger

logger = get_logger("llm")

client = OpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_answer(messages: list[dict]) -> str:
    """
    Generate a complete answer from the LLM.

    Args:
        messages: OpenAI-compatible message list from context_builder.

    Returns:
        The assistant's response text.

    Raises:
        Exception: If the API call fails.
    """
    logger.info(f"Calling LLM ({settings.LLM_MODEL}) with {len(messages)} messages")

    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=0.3,        # Low for factual accuracy
            max_tokens=2000,
            top_p=0.9,
        )

        answer = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else "N/A"
        logger.info(f"LLM response generated ({tokens_used} tokens)")

        return answer

    except Exception as e:
        logger.error(f"LLM API error: {str(e)}")
        raise


async def generate_answer_stream(messages: list[dict]):
    """
    Generate a streaming answer (for Server-Sent Events).

    Yields:
        Chunks of text as they arrive from the LLM.
    """
    logger.info(f"Calling LLM ({settings.LLM_MODEL}) with streaming")

    try:
        stream = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
            top_p=0.9,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        logger.error(f"LLM streaming error: {str(e)}")
        raise


async def generate_chat_title(question: str) -> str:
    """
    Auto-generate a short chat title from the first question.

    Returns:
        A 3-6 word title summarizing the question.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Use cheaper model for title generation
        messages=[
            {
                "role": "system",
                "content": "Generate a short title (3-6 words) for a research chat based on the user's first question. Return ONLY the title, nothing else."
            },
            {"role": "user", "content": question}
        ],
        temperature=0.5,
        max_tokens=20,
    )
    return response.choices[0].message.content.strip().strip('"')
```

---

## Config Additions

**File:** `src/helpers/config.py` — add (if not already present from SPEC-03):

```python
# LLM
LLM_MODEL: str = "gpt-4o-mini"
LLM_MAX_TOKENS: int = 2000
LLM_TEMPERATURE: float = 0.3
```

**File:** `.env` — add:
```env
LLM_MODEL=gpt-4o-mini
```

---

## Pydantic Schemas

**New file:** `src/models/schemas/chat_schemas.py`

```python
from pydantic import BaseModel, field_validator
from datetime import datetime


class CreateChatRequest(BaseModel):
    title: str | None = None


class ChatListItem(BaseModel):
    id: str
    title: str | None
    created_at: datetime
    message_count: int
    last_message_at: datetime | None

    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    question: str
    document_ids: list[str] | None = None

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()


class QueryResponse(BaseModel):
    message_id: str
    answer: str
    sources: list[dict]


class UpdateChatRequest(BaseModel):
    title: str
```

---

## Chat Controller

**New file:** `src/controllers/chat_controller.py`

The main query flow (pseudocode):

```python
class ChatController:

    @staticmethod
    async def query(chat_id, question, document_ids, current_user, db):
        # 1. Verify chat belongs to user
        chat = await _get_user_chat(chat_id, current_user.id, db)
        if not chat:
            raise HTTPException(404, "Chat not found")

        # 2. Check user has ready documents
        ready_count = await _count_ready_documents(current_user.id, db)
        if ready_count == 0:
            raise HTTPException(400, "No processed documents. Upload PDFs first.")

        # 3. Get conversation history
        history = await _get_chat_history(chat_id, db, limit=10)

        # 4. Retrieve relevant chunks (SPEC-04)
        from src.services.retrieval_service import search_similar_chunks
        chunks = await search_similar_chunks(
            query=question,
            user_id=str(current_user.id),
            db=db,
            top_k=5,
            document_ids=document_ids,
        )

        # 5. Build prompt (SPEC-04)
        from src.services.context_builder import build_prompt, get_source_summary
        messages = build_prompt(question, chunks, history)
        sources = get_source_summary(chunks)

        # 6. Generate answer (this spec)
        from src.services.llm_service import generate_answer
        answer = await generate_answer(messages)

        # 7. Save user message
        user_msg = Message(
            chat_id=chat.id,
            role="user",
            content=question,
        )
        db.add(user_msg)

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
            from src.services.llm_service import generate_chat_title
            chat.title = await generate_chat_title(question)

        await db.commit()
        await db.refresh(assistant_msg)

        # 10. Return response
        return {
            "message_id": str(assistant_msg.id),
            "answer": answer,
            "sources": sources,
        }
```

---

## File Structure

### New Files to Create

| File | Purpose |
|---|---|
| `src/routes/chat_routes.py` | Chat & message API endpoints |
| `src/controllers/chat_controller.py` | Chat business logic |
| `src/services/llm_service.py` | LLM interaction (OpenAI) |
| `src/models/schemas/chat_schemas.py` | Pydantic schemas |

### Files to Modify

| File | Change |
|---|---|
| `src/models/db_scheams/Message.py` | Add `source_chunks` JSON column |
| `src/helpers/config.py` | Add LLM settings |
| `src/main.py` | Register chat routes |
| `.env` | Add `LLM_MODEL` |

---

## Business Rules

1. **User isolation:** Users can only see and interact with their own chats.
2. **Chat title auto-generation:** If no title is provided and this is the first message, generate a title from the question using a cheap LLM call.
3. **Empty documents guard:** If user has no ready documents, return 400 instead of a hallucinated answer.
4. **Source preservation:** Assistant messages store `source_chunks` JSON so sources can be retrieved later without re-querying pgvector.
5. **Message ordering:** Messages are always returned in `created_at` ascending order.
6. **Cascade delete:** Deleting a chat deletes all its messages (already configured in Chat model's relationship).

---

## Test Scenarios

| # | Scenario | Expected Result |
|---|---|---|
| 1 | Create a new chat | 201, chat returned with null title |
| 2 | Create chat with title | 201, chat with provided title |
| 3 | List chats (has 3) | 200, returns 3 items sorted by created_at desc |
| 4 | List chats (has 0) | 200, returns empty array |
| 5 | Get chat with messages | 200, returns chat + messages in order |
| 6 | Get another user's chat | 403, "Access denied" |
| 7 | Delete chat | 200, chat and messages deleted |
| 8 | Query with valid question | 200, answer + sources returned |
| 9 | Query with empty question | 400, "Question cannot be empty" |
| 10 | Query with no ready documents | 400, "No processed documents" |
| 11 | Query auto-generates title | Chat title updated after first query |
| 12 | Query uses conversation history | Previous messages influence the answer |
| 13 | Query returns source references | Sources include title, author, year, page |
| 14 | Rename a chat | 200, title updated |

---

## Acceptance Criteria

- [ ] User can create a new chat session
- [ ] User can list their chats with message counts
- [ ] User can get a chat with all its messages
- [ ] User can delete a chat (cascades to messages)
- [ ] User can rename a chat
- [ ] `POST /chats/{id}/query` processes a question through the full RAG pipeline
- [ ] Answer is generated by LLM based on retrieved chunks (not general knowledge)
- [ ] Answer includes `[Source N]` references in the text
- [ ] Sources are returned in the response with metadata
- [ ] User message is saved to DB
- [ ] Assistant message is saved with `source_chunks` JSON
- [ ] Chat title is auto-generated from the first question
- [ ] Users cannot access other users' chats
- [ ] Empty questions are rejected
- [ ] Queries with no ready documents return helpful error
- [ ] LLM API errors are handled gracefully
