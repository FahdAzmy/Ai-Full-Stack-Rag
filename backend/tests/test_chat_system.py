"""
Test cases for Chat System & LLM Integration (SPEC-05).
Written following strict TDD — tests BEFORE implementation.

All external services (LLM, retrieval, embedding) are mocked.
"""

import uuid
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.helpers.security import hash_password, generate_access_token
from src.models.db_scheams.user import User
from src.models.db_scheams.Chat import Chat
from src.models.db_scheams.Message import Message
from src.models.db_scheams.document import Document


# ═════════════════════════════════════════════════════════════════════════════
#  Test Helpers
# ═════════════════════════════════════════════════════════════════════════════


async def create_verified_user(
    db_session: AsyncSession,
    email: str = "chatuser@example.com",
) -> User:
    """Create a verified user in the DB and return the User object."""
    user = User(
        email=email,
        name="Chat Test User",
        hashed_password=hash_password("SecurePass123"),
        is_verified=True,
        verification_token="123456",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def auth_header(user: User) -> dict:
    """Generate Authorization header with a valid access token."""
    token = generate_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


async def create_chat_in_db(
    db_session: AsyncSession,
    user: User,
    title: str | None = None,
    created_at: datetime | None = None,
) -> Chat:
    """Insert a Chat record directly into the DB for test setup."""
    chat = Chat(
        id=uuid.uuid4(),
        user_id=user.id,
        title=title,
    )
    if created_at:
        chat.created_at = created_at
    db_session.add(chat)
    await db_session.commit()
    await db_session.refresh(chat)
    return chat


async def create_message_in_db(
    db_session: AsyncSession,
    chat: Chat,
    role: str = "user",
    content: str = "Test message",
    source_chunks: list | None = None,
    created_at: datetime | None = None,
) -> Message:
    """Insert a Message record directly into the DB for test setup."""
    msg = Message(
        id=uuid.uuid4(),
        chat_id=chat.id,
        role=role,
        content=content,
        source_chunks=source_chunks,
    )
    if created_at:
        msg.created_at = created_at
    db_session.add(msg)
    await db_session.commit()
    await db_session.refresh(msg)
    return msg


async def create_ready_document(
    db_session: AsyncSession,
    user: User,
    file_name: str = "paper.pdf",
) -> Document:
    """Create a document with status='ready' for query tests."""
    doc = Document(
        id=uuid.uuid4(),
        user_id=user.id,
        file_name=file_name,
        file_path=f"{user.id}/{uuid.uuid4()}.pdf",
        status="ready",
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


# Realistic mock data for RAG pipeline
MOCK_CHUNKS = [
    {
        "chunk_id": str(uuid.uuid4()),
        "content": "Convolutional neural networks require large annotated datasets, "
                   "which are often unavailable in medical imaging. Transfer learning "
                   "from natural image datasets partially addresses this limitation.",
        "page_number": 15,
        "chunk_index": 3,
        "document_id": str(uuid.uuid4()),
        "file_name": "deep_learning.pdf",
        "title": "Deep Learning in Medicine",
        "author": "Smith, John",
        "year": "2020",
        "journal": "Journal of Medical AI",
        "doi": "10.1234/jmai.2020.001",
        "similarity": 0.87,
    },
    {
        "chunk_id": str(uuid.uuid4()),
        "content": "The primary challenge remains the need for high-quality labeled "
                   "data. Semi-supervised and self-supervised approaches have emerged "
                   "as promising solutions.",
        "page_number": 8,
        "chunk_index": 2,
        "document_id": str(uuid.uuid4()),
        "file_name": "cnn_challenges.pdf",
        "title": "CNN Challenges in Healthcare",
        "author": "Doe, Jane",
        "year": "2021",
        "journal": "Healthcare AI Review",
        "doi": None,
        "similarity": 0.82,
    },
]

MOCK_LLM_ANSWER = (
    "Based on your uploaded research papers, the main limitations of CNN in "
    "medical imaging include:\n\n"
    "1. **Data Requirements** — CNNs require large annotated datasets [Source 1]. "
    "Transfer learning helps but does not fully resolve this.\n\n"
    "2. **Label Quality** — High-quality labeled data is scarce [Source 2].\n\n"
    "## References Used\n"
    "- [Source 1] Smith (2020), p.15\n"
    "- [Source 2] Doe (2021), p.8"
)

MOCK_TITLE = "CNN Limitations in Medical Imaging"


# ═════════════════════════════════════════════════════════════════════════════
#  Mock Fixtures
# ═════════════════════════════════════════════════════════════════════════════


RETRIEVAL_MOCK_PATH = "src.controllers.chat_controller.search_similar_chunks"
LLM_ANSWER_MOCK_PATH = "src.controllers.chat_controller.generate_answer"
LLM_TITLE_MOCK_PATH = "src.controllers.chat_controller.generate_chat_title"


@pytest.fixture
def mock_retrieval():
    """Mock the retrieval service to return realistic chunks."""
    with patch(RETRIEVAL_MOCK_PATH, new_callable=AsyncMock) as mock:
        mock.return_value = MOCK_CHUNKS
        yield mock


@pytest.fixture
def mock_retrieval_empty():
    """Mock retrieval service returning zero chunks."""
    with patch(RETRIEVAL_MOCK_PATH, new_callable=AsyncMock) as mock:
        mock.return_value = []
        yield mock


@pytest.fixture
def mock_retrieval_crash():
    """Mock retrieval service that crashes."""
    with patch(RETRIEVAL_MOCK_PATH, new_callable=AsyncMock) as mock:
        mock.side_effect = Exception("Retrieval service unavailable")
        yield mock


@pytest.fixture
def mock_llm():
    """Mock the LLM generate_answer to return a realistic answer."""
    with patch(LLM_ANSWER_MOCK_PATH, new_callable=AsyncMock) as mock:
        mock.return_value = MOCK_LLM_ANSWER
        yield mock


@pytest.fixture
def mock_llm_empty():
    """Mock LLM that returns empty response."""
    with patch(LLM_ANSWER_MOCK_PATH, new_callable=AsyncMock) as mock:
        mock.return_value = ""
        yield mock


@pytest.fixture
def mock_llm_failure():
    """Mock LLM that raises an API error."""
    with patch(LLM_ANSWER_MOCK_PATH, new_callable=AsyncMock) as mock:
        mock.side_effect = Exception("OpenAI API error: rate limit exceeded")
        yield mock


@pytest.fixture
def mock_llm_timeout():
    """Mock LLM that times out."""
    with patch(LLM_ANSWER_MOCK_PATH, new_callable=AsyncMock) as mock:
        mock.side_effect = TimeoutError("LLM request timed out")
        yield mock


@pytest.fixture
def mock_title_gen():
    """Mock auto title generation."""
    with patch(LLM_TITLE_MOCK_PATH, new_callable=AsyncMock) as mock:
        mock.return_value = MOCK_TITLE
        yield mock


@pytest.fixture
def mock_title_gen_failure():
    """Mock title generation that fails."""
    with patch(LLM_TITLE_MOCK_PATH, new_callable=AsyncMock) as mock:
        mock.side_effect = Exception("Title generation failed")
        yield mock


@pytest.fixture
def mock_full_pipeline(mock_retrieval, mock_llm, mock_title_gen):
    """Combine all mocks for a full successful pipeline test."""
    return {
        "retrieval": mock_retrieval,
        "llm": mock_llm,
        "title_gen": mock_title_gen,
    }


# ═════════════════════════════════════════════════════════════════════════════
# 1. TestCreateChat — POST /chats/
# ═════════════════════════════════════════════════════════════════════════════


class TestCreateChat:
    """Test cases for POST /chats/ — Create a new chat session."""

    @pytest.mark.asyncio
    async def test_create_chat_without_title(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Create a chat with no title → 201, title is null."""
        user = await create_verified_user(db_session)

        response = await client.post(
            "/chats/",
            json={},
            headers=auth_header(user),
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] is None
        assert "created_at" in data

        # Verify DB record
        result = await db_session.execute(
            select(Chat).where(Chat.id == data["id"])
        )
        chat = result.scalar_one_or_none()
        assert chat is not None
        assert chat.user_id == user.id
        assert chat.title is None

    @pytest.mark.asyncio
    async def test_create_chat_with_title(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Create a chat with provided title → 201, title retained."""
        user = await create_verified_user(db_session)

        response = await client.post(
            "/chats/",
            json={"title": "Literature Review Questions"},
            headers=auth_header(user),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Literature Review Questions"

    @pytest.mark.asyncio
    async def test_create_chat_without_auth(self, client: AsyncClient):
        """Create a chat without auth → 401/403."""
        response = await client.post("/chats/", json={})
        assert response.status_code in (401, 403)


# ═════════════════════════════════════════════════════════════════════════════
# 2. TestListChats — GET /chats/
# ═════════════════════════════════════════════════════════════════════════════


class TestListChats:
    """Test cases for GET /chats/ — List user's chats."""

    @pytest.mark.asyncio
    async def test_list_chats_with_results(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """List chats (has 3) → 200, returns 3 items sorted by created_at desc."""
        user = await create_verified_user(db_session)
        now = datetime.utcnow()

        chat1 = await create_chat_in_db(db_session, user, "First Chat",
                                         created_at=now - timedelta(hours=3))
        chat2 = await create_chat_in_db(db_session, user, "Second Chat",
                                         created_at=now - timedelta(hours=2))
        chat3 = await create_chat_in_db(db_session, user, "Third Chat",
                                         created_at=now - timedelta(hours=1))

        response = await client.get("/chats/", headers=auth_header(user))

        assert response.status_code == 200
        data = response.json()
        assert "chats" in data
        assert len(data["chats"]) == 3
        assert data["total"] == 3

        # Verify sorted by created_at descending (newest first)
        titles = [c["title"] for c in data["chats"]]
        assert titles == ["Third Chat", "Second Chat", "First Chat"]

    @pytest.mark.asyncio
    async def test_list_chats_empty(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """List chats (has 0) → 200, returns empty array."""
        user = await create_verified_user(db_session)

        response = await client.get("/chats/", headers=auth_header(user))

        assert response.status_code == 200
        data = response.json()
        assert data["chats"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_chats_includes_message_count(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Chat list items include message_count and last_message_at."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Active Chat")

        # Add messages
        msg_time = datetime.utcnow()
        await create_message_in_db(db_session, chat, "user", "Hello",
                                   created_at=msg_time - timedelta(minutes=5))
        await create_message_in_db(db_session, chat, "assistant", "Hi there!",
                                   created_at=msg_time)

        response = await client.get("/chats/", headers=auth_header(user))

        assert response.status_code == 200
        data = response.json()
        assert len(data["chats"]) == 1

        chat_item = data["chats"][0]
        assert chat_item["message_count"] == 2
        assert chat_item["last_message_at"] is not None

    @pytest.mark.asyncio
    async def test_list_chats_user_isolation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Each user only sees their own chats."""
        user_a = await create_verified_user(db_session, "chat_a@example.com")
        user_b = await create_verified_user(db_session, "chat_b@example.com")

        await create_chat_in_db(db_session, user_a, "A's Chat 1")
        await create_chat_in_db(db_session, user_a, "A's Chat 2")
        await create_chat_in_db(db_session, user_b, "B's Chat 1")

        response_a = await client.get("/chats/", headers=auth_header(user_a))
        response_b = await client.get("/chats/", headers=auth_header(user_b))

        assert response_a.json()["total"] == 2
        assert response_b.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_list_chats_without_auth(self, client: AsyncClient):
        """List chats without auth → 401/403."""
        response = await client.get("/chats/")
        assert response.status_code in (401, 403)


# ═════════════════════════════════════════════════════════════════════════════
# 3. TestGetChat — GET /chats/{chat_id}
# ═════════════════════════════════════════════════════════════════════════════


class TestGetChat:
    """Test cases for GET /chats/{chat_id} — Get a chat with messages."""

    @pytest.mark.asyncio
    async def test_get_chat_with_messages(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Get chat with messages → 200, messages in ascending order."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Test Chat")

        now = datetime.utcnow()
        await create_message_in_db(db_session, chat, "user",
                                   "What are CNNs?",
                                   created_at=now - timedelta(minutes=2))
        await create_message_in_db(db_session, chat, "assistant",
                                   "CNNs are convolutional neural networks...",
                                   created_at=now - timedelta(minutes=1))
        await create_message_in_db(db_session, chat, "user",
                                   "What about RNNs?",
                                   created_at=now)

        response = await client.get(
            f"/chats/{chat.id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(chat.id)
        assert data["title"] == "Test Chat"
        assert len(data["messages"]) == 3

        # Verify ascending order
        roles = [m["role"] for m in data["messages"]]
        assert roles == ["user", "assistant", "user"]

    @pytest.mark.asyncio
    async def test_get_chat_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Get non-existent chat → 404."""
        user = await create_verified_user(db_session)
        fake_id = uuid.uuid4()

        response = await client.get(
            f"/chats/{fake_id}",
            headers=auth_header(user),
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_other_users_chat(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Get another user's chat → 403, 'Access denied'."""
        owner = await create_verified_user(db_session, "chat_owner@example.com")
        intruder = await create_verified_user(db_session, "chat_intruder@example.com")
        chat = await create_chat_in_db(db_session, owner, "Private Chat")

        response = await client.get(
            f"/chats/{chat.id}",
            headers=auth_header(intruder),
        )

        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_chat_without_auth(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Get chat without auth → 401/403."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user)

        response = await client.get(f"/chats/{chat.id}")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_chat_messages_include_source_chunks(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Assistant messages include source_chunks, user messages have null."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Sources Chat")

        sources = [
            {"source_number": 1, "title": "Test Paper", "similarity": 0.9}
        ]
        await create_message_in_db(db_session, chat, "user", "Question?")
        await create_message_in_db(db_session, chat, "assistant", "Answer.",
                                   source_chunks=sources)

        response = await client.get(
            f"/chats/{chat.id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        msgs = response.json()["messages"]
        assert msgs[0]["source_chunks"] is None  # user message
        assert msgs[1]["source_chunks"] is not None  # assistant message
        assert msgs[1]["source_chunks"][0]["title"] == "Test Paper"


# ═════════════════════════════════════════════════════════════════════════════
# 4. TestDeleteChat — DELETE /chats/{chat_id}
# ═════════════════════════════════════════════════════════════════════════════


class TestDeleteChat:
    """Test cases for DELETE /chats/{chat_id}."""

    @pytest.mark.asyncio
    async def test_delete_chat_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Delete chat → 200, chat removed from DB."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "To Delete")
        chat_id = chat.id

        response = await client.delete(
            f"/chats/{chat_id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify DB record is gone
        result = await db_session.execute(
            select(Chat).where(Chat.id == chat_id)
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_delete_chat_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Delete non-existent chat → 404."""
        user = await create_verified_user(db_session)
        fake_id = uuid.uuid4()

        response = await client.delete(
            f"/chats/{fake_id}",
            headers=auth_header(user),
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_other_users_chat(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Delete another user's chat → 403."""
        owner = await create_verified_user(db_session, "del_owner@example.com")
        intruder = await create_verified_user(db_session, "del_intruder@example.com")
        chat = await create_chat_in_db(db_session, owner, "Private")

        response = await client.delete(
            f"/chats/{chat.id}",
            headers=auth_header(intruder),
        )

        assert response.status_code == 403

        # Verify chat was NOT deleted
        result = await db_session.execute(
            select(Chat).where(Chat.id == chat.id)
        )
        assert result.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_delete_chat_without_auth(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Delete chat without auth → 401/403."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user)

        response = await client.delete(f"/chats/{chat.id}")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_delete_chat_cascades_messages(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Deleting a chat also deletes all its messages."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "With Messages")
        chat_id = chat.id

        # Create several messages
        for i in range(5):
            await create_message_in_db(db_session, chat, "user", f"Msg {i}")

        response = await client.delete(
            f"/chats/{chat_id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200

        # Verify messages are also gone
        result = await db_session.execute(
            select(func.count(Message.id)).where(Message.chat_id == chat_id)
        )
        count = result.scalar()
        assert count == 0


# ═════════════════════════════════════════════════════════════════════════════
# 5. TestRenameChat — PATCH /chats/{chat_id}
# ═════════════════════════════════════════════════════════════════════════════


class TestRenameChat:
    """Test cases for PATCH /chats/{chat_id} — Rename a chat."""

    @pytest.mark.asyncio
    async def test_rename_chat_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Rename a chat → 200, title updated."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Old Title")

        response = await client.patch(
            f"/chats/{chat.id}",
            json={"title": "New Title"},
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["id"] == str(chat.id)
        assert "message" in data

        # Verify DB was updated
        await db_session.refresh(chat)
        assert chat.title == "New Title"

    @pytest.mark.asyncio
    async def test_rename_chat_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Rename non-existent chat → 404."""
        user = await create_verified_user(db_session)
        fake_id = uuid.uuid4()

        response = await client.patch(
            f"/chats/{fake_id}",
            json={"title": "New Title"},
            headers=auth_header(user),
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_rename_other_users_chat(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Rename another user's chat → 403."""
        owner = await create_verified_user(db_session, "rename_owner@example.com")
        intruder = await create_verified_user(db_session, "rename_intruder@example.com")
        chat = await create_chat_in_db(db_session, owner, "My Chat")

        response = await client.patch(
            f"/chats/{chat.id}",
            json={"title": "Hacked"},
            headers=auth_header(intruder),
        )

        assert response.status_code == 403

        # Verify title was NOT changed
        await db_session.refresh(chat)
        assert chat.title == "My Chat"

    @pytest.mark.asyncio
    async def test_rename_chat_without_auth(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Rename chat without auth → 401/403."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user)

        response = await client.patch(
            f"/chats/{chat.id}",
            json={"title": "No Auth"},
        )
        assert response.status_code in (401, 403)


# ═════════════════════════════════════════════════════════════════════════════
# 6. TestQueryEndpoint — POST /chats/{chat_id}/query (RAG pipeline)
# ═════════════════════════════════════════════════════════════════════════════


class TestQueryEndpoint:
    """Test the main RAG query pipeline: question → retrieval → LLM → response."""

    @pytest.mark.asyncio
    async def test_query_success_full_pipeline(
        self, client: AsyncClient, db_session: AsyncSession, mock_full_pipeline
    ):
        """Full pipeline: valid question → 200, answer + sources + message_id."""
        user = await create_verified_user(db_session)
        await create_ready_document(db_session, user)
        chat = await create_chat_in_db(db_session, user)

        response = await client.post(
            f"/chats/{chat.id}/query",
            json={"question": "What are the limitations of CNN in medical imaging?"},
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert "message_id" in data
        assert "answer" in data
        assert "sources" in data
        assert len(data["sources"]) > 0
        assert data["answer"] == MOCK_LLM_ANSWER

    @pytest.mark.asyncio
    async def test_query_saves_user_message(
        self, client: AsyncClient, db_session: AsyncSession, mock_full_pipeline
    ):
        """User message is persisted to DB after query."""
        user = await create_verified_user(db_session)
        await create_ready_document(db_session, user)
        chat = await create_chat_in_db(db_session, user)

        question = "How does transfer learning work?"
        await client.post(
            f"/chats/{chat.id}/query",
            json={"question": question},
            headers=auth_header(user),
        )

        # Verify user message was saved
        result = await db_session.execute(
            select(Message).where(
                Message.chat_id == chat.id,
                Message.role == "user",
            )
        )
        user_msg = result.scalar_one_or_none()
        assert user_msg is not None
        assert user_msg.content == question
        assert user_msg.source_chunks is None

    @pytest.mark.asyncio
    async def test_query_saves_assistant_message_with_sources(
        self, client: AsyncClient, db_session: AsyncSession, mock_full_pipeline
    ):
        """Assistant message is persisted with source_chunks JSON."""
        user = await create_verified_user(db_session)
        await create_ready_document(db_session, user)
        chat = await create_chat_in_db(db_session, user)

        await client.post(
            f"/chats/{chat.id}/query",
            json={"question": "Tell me about CNNs."},
            headers=auth_header(user),
        )

        # Verify assistant message was saved with sources
        result = await db_session.execute(
            select(Message).where(
                Message.chat_id == chat.id,
                Message.role == "assistant",
            )
        )
        assistant_msg = result.scalar_one_or_none()
        assert assistant_msg is not None
        assert assistant_msg.content == MOCK_LLM_ANSWER
        assert assistant_msg.source_chunks is not None
        assert len(assistant_msg.source_chunks) == 2

    @pytest.mark.asyncio
    async def test_query_auto_generates_title(
        self, client: AsyncClient, db_session: AsyncSession, mock_full_pipeline
    ):
        """First query on a chat with no title → auto-generates title."""
        user = await create_verified_user(db_session)
        await create_ready_document(db_session, user)
        chat = await create_chat_in_db(db_session, user, title=None)

        assert chat.title is None

        await client.post(
            f"/chats/{chat.id}/query",
            json={"question": "What are the limitations of CNN?"},
            headers=auth_header(user),
        )

        # Verify title was auto-generated
        await db_session.refresh(chat)
        assert chat.title == MOCK_TITLE

    @pytest.mark.asyncio
    async def test_query_preserves_existing_title(
        self, client: AsyncClient, db_session: AsyncSession, mock_full_pipeline
    ):
        """Query on a chat that already has a title → title unchanged."""
        user = await create_verified_user(db_session)
        await create_ready_document(db_session, user)
        chat = await create_chat_in_db(db_session, user, title="My Research")

        await client.post(
            f"/chats/{chat.id}/query",
            json={"question": "What about RNNs?"},
            headers=auth_header(user),
        )

        await db_session.refresh(chat)
        assert chat.title == "My Research"
        # generate_chat_title should NOT have been called
        mock_full_pipeline["title_gen"].assert_not_called()

    @pytest.mark.asyncio
    async def test_query_source_references_structure(
        self, client: AsyncClient, db_session: AsyncSession, mock_full_pipeline
    ):
        """Sources in the response contain all required metadata fields."""
        user = await create_verified_user(db_session)
        await create_ready_document(db_session, user)
        chat = await create_chat_in_db(db_session, user)

        response = await client.post(
            f"/chats/{chat.id}/query",
            json={"question": "Tell me about data requirements."},
            headers=auth_header(user),
        )

        data = response.json()
        source = data["sources"][0]
        assert "source_number" in source
        assert "title" in source
        assert "author" in source
        assert "year" in source
        assert "page_number" in source
        assert "file_name" in source
        assert "document_id" in source
        assert "chunk_id" in source
        assert "similarity" in source
        assert "excerpt" in source

    @pytest.mark.asyncio
    async def test_query_with_document_ids_filter(
        self, client: AsyncClient, db_session: AsyncSession, mock_full_pipeline
    ):
        """Query with document_ids → passed to retrieval service."""
        user = await create_verified_user(db_session)
        doc = await create_ready_document(db_session, user)
        chat = await create_chat_in_db(db_session, user)

        doc_id = str(doc.id)
        await client.post(
            f"/chats/{chat.id}/query",
            json={
                "question": "What about this paper?",
                "document_ids": [doc_id],
            },
            headers=auth_header(user),
        )

        # Verify document_ids was passed to retrieval
        call_kwargs = mock_full_pipeline["retrieval"].call_args
        assert call_kwargs.kwargs.get("document_ids") == [doc_id] or \
               (call_kwargs.args and doc_id in str(call_kwargs))

    @pytest.mark.asyncio
    async def test_query_uses_conversation_history(
        self, client: AsyncClient, db_session: AsyncSession, mock_full_pipeline
    ):
        """Previous messages are included in the prompt context."""
        user = await create_verified_user(db_session)
        await create_ready_document(db_session, user)
        chat = await create_chat_in_db(db_session, user, title="History Test")

        # Add existing conversation history
        await create_message_in_db(db_session, chat, "user",
                                   "What are CNNs?")
        await create_message_in_db(db_session, chat, "assistant",
                                   "CNNs are convolutional neural networks.")

        # Now query again
        response = await client.post(
            f"/chats/{chat.id}/query",
            json={"question": "Tell me more about their architecture."},
            headers=auth_header(user),
        )

        assert response.status_code == 200


# ═════════════════════════════════════════════════════════════════════════════
# 7. TestQueryEdgeCases — Error & edge scenarios
# ═════════════════════════════════════════════════════════════════════════════


class TestQueryEdgeCases:
    """Edge cases and error scenarios for the query endpoint."""

    @pytest.mark.asyncio
    async def test_query_empty_question(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Query with empty question → 422 validation error."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user)

        response = await client.post(
            f"/chats/{chat.id}/query",
            json={"question": ""},
            headers=auth_header(user),
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_query_whitespace_question(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Query with whitespace-only question → 422 validation error."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user)

        response = await client.post(
            f"/chats/{chat.id}/query",
            json={"question": "   \t\n  "},
            headers=auth_header(user),
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_query_no_ready_documents(
        self, client: AsyncClient, db_session: AsyncSession,
        mock_retrieval, mock_llm, mock_title_gen
    ):
        """Query with no ready documents → 400."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user)
        # No documents created — user has zero ready documents

        response = await client.post(
            f"/chats/{chat.id}/query",
            json={"question": "What is deep learning?"},
            headers=auth_header(user),
        )

        assert response.status_code == 400
        assert "no processed documents" in response.json()["detail"].lower() or \
               "upload" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_query_chat_not_found(
        self, client: AsyncClient, db_session: AsyncSession,
        mock_retrieval, mock_llm, mock_title_gen
    ):
        """Query on non-existent chat → 404."""
        user = await create_verified_user(db_session)
        fake_id = uuid.uuid4()

        response = await client.post(
            f"/chats/{fake_id}/query",
            json={"question": "Hello?"},
            headers=auth_header(user),
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_query_other_users_chat(
        self, client: AsyncClient, db_session: AsyncSession,
        mock_retrieval, mock_llm, mock_title_gen
    ):
        """Query on another user's chat → 403."""
        owner = await create_verified_user(db_session, "q_owner@example.com")
        intruder = await create_verified_user(db_session, "q_intruder@example.com")
        chat = await create_chat_in_db(db_session, owner)

        response = await client.post(
            f"/chats/{chat.id}/query",
            json={"question": "Sneaky question"},
            headers=auth_header(intruder),
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_query_invalid_document_ids(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Query with invalid UUID in document_ids → 422 validation error."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user)

        response = await client.post(
            f"/chats/{chat.id}/query",
            json={
                "question": "Valid question",
                "document_ids": ["not-a-valid-uuid", "also-invalid"],
            },
            headers=auth_header(user),
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_query_retrieval_returns_zero_chunks(
        self, client: AsyncClient, db_session: AsyncSession,
        mock_retrieval_empty, mock_llm, mock_title_gen
    ):
        """Retrieval returns no chunks → 200, answer generated, empty sources."""
        user = await create_verified_user(db_session)
        await create_ready_document(db_session, user)
        chat = await create_chat_in_db(db_session, user)

        response = await client.post(
            f"/chats/{chat.id}/query",
            json={"question": "Something very obscure?"},
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sources"] == []

    @pytest.mark.asyncio
    async def test_query_without_auth(self, client: AsyncClient):
        """Query without auth → 401/403."""
        fake_id = uuid.uuid4()
        response = await client.post(
            f"/chats/{fake_id}/query",
            json={"question": "Hello"},
        )
        assert response.status_code in (401, 403)


# ═════════════════════════════════════════════════════════════════════════════
# 8. TestQueryFailureSimulation — LLM/retrieval/DB failures
# ═════════════════════════════════════════════════════════════════════════════


class TestQueryFailureSimulation:
    """Simulate failures in external services."""

    @pytest.mark.asyncio
    async def test_query_llm_api_failure(
        self, client: AsyncClient, db_session: AsyncSession,
        mock_retrieval, mock_llm_failure, mock_title_gen
    ):
        """LLM API failure → 500, safe error message."""
        user = await create_verified_user(db_session)
        await create_ready_document(db_session, user)
        chat = await create_chat_in_db(db_session, user)

        response = await client.post(
            f"/chats/{chat.id}/query",
            json={"question": "What is machine learning?"},
            headers=auth_header(user),
        )

        assert response.status_code == 500
        assert "failed to generate" in response.json()["detail"].lower() or \
               "try again" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_query_llm_returns_empty(
        self, client: AsyncClient, db_session: AsyncSession,
        mock_retrieval, mock_llm_empty, mock_title_gen
    ):
        """LLM returns empty string → 200, empty answer handled gracefully."""
        user = await create_verified_user(db_session)
        await create_ready_document(db_session, user)
        chat = await create_chat_in_db(db_session, user)

        response = await client.post(
            f"/chats/{chat.id}/query",
            json={"question": "Tell me something."},
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == ""

    @pytest.mark.asyncio
    async def test_query_llm_timeout(
        self, client: AsyncClient, db_session: AsyncSession,
        mock_retrieval, mock_llm_timeout, mock_title_gen
    ):
        """LLM timeout → 500, safe error message."""
        user = await create_verified_user(db_session)
        await create_ready_document(db_session, user)
        chat = await create_chat_in_db(db_session, user)

        response = await client.post(
            f"/chats/{chat.id}/query",
            json={"question": "What is NLP?"},
            headers=auth_header(user),
        )

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_query_retrieval_crash(
        self, client: AsyncClient, db_session: AsyncSession,
        mock_retrieval_crash, mock_llm, mock_title_gen
    ):
        """Retrieval service crashes → 500, safe error message."""
        user = await create_verified_user(db_session)
        await create_ready_document(db_session, user)
        chat = await create_chat_in_db(db_session, user)

        response = await client.post(
            f"/chats/{chat.id}/query",
            json={"question": "Any question."},
            headers=auth_header(user),
        )

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_query_user_message_persisted_even_if_llm_fails(
        self, client: AsyncClient, db_session: AsyncSession,
        mock_retrieval, mock_llm_failure, mock_title_gen
    ):
        """Even when LLM fails, the user message should be saved (per spec rule #7)."""
        user = await create_verified_user(db_session)
        await create_ready_document(db_session, user)
        chat = await create_chat_in_db(db_session, user)

        question = "This should be saved even if LLM fails"
        await client.post(
            f"/chats/{chat.id}/query",
            json={"question": question},
            headers=auth_header(user),
        )

        # Verify user message was still saved
        result = await db_session.execute(
            select(Message).where(
                Message.chat_id == chat.id,
                Message.role == "user",
            )
        )
        user_msg = result.scalar_one_or_none()
        assert user_msg is not None
        assert user_msg.content == question

    @pytest.mark.asyncio
    async def test_query_title_generation_failure_non_fatal(
        self, client: AsyncClient, db_session: AsyncSession,
        mock_retrieval, mock_llm, mock_title_gen_failure
    ):
        """Title generation failure should not fail the query."""
        user = await create_verified_user(db_session)
        await create_ready_document(db_session, user)
        chat = await create_chat_in_db(db_session, user, title=None)

        response = await client.post(
            f"/chats/{chat.id}/query",
            json={"question": "What is AI?"},
            headers=auth_header(user),
        )

        # The query itself should still succeed
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data


# ═════════════════════════════════════════════════════════════════════════════
# 9. TestGetMessages — GET /chats/{chat_id}/messages
# ═════════════════════════════════════════════════════════════════════════════


class TestGetMessages:
    """Test cases for GET /chats/{chat_id}/messages — paginated history."""

    @pytest.mark.asyncio
    async def test_get_messages_default(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Get messages with default params → 200, all messages."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Msg Test")

        for i in range(5):
            await create_message_in_db(db_session, chat, "user", f"Message {i}")

        response = await client.get(
            f"/chats/{chat.id}/messages",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) == 5
        assert "total" in data
        assert "has_more" in data

    @pytest.mark.asyncio
    async def test_get_messages_with_limit(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Get messages with limit → respects limit param."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Limit Test")

        for i in range(10):
            await create_message_in_db(db_session, chat, "user", f"Msg {i}")

        response = await client.get(
            f"/chats/{chat.id}/messages?limit=3",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 3
        assert data["has_more"] is True

    @pytest.mark.asyncio
    async def test_get_messages_with_before(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Get messages with 'before' cursor → returns earlier messages."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Before Test")

        now = datetime.utcnow()
        msg1 = await create_message_in_db(db_session, chat, "user", "First",
                                           created_at=now - timedelta(minutes=3))
        msg2 = await create_message_in_db(db_session, chat, "user", "Second",
                                           created_at=now - timedelta(minutes=2))
        msg3 = await create_message_in_db(db_session, chat, "user", "Third",
                                           created_at=now - timedelta(minutes=1))

        response = await client.get(
            f"/chats/{chat.id}/messages?before={msg3.id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        # Should return messages before msg3 (i.e., msg1 and msg2)
        assert len(data["messages"]) == 2

    @pytest.mark.asyncio
    async def test_get_messages_has_more_false(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """has_more is false when all messages fit in limit."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Complete")

        for i in range(3):
            await create_message_in_db(db_session, chat, "user", f"Msg {i}")

        response = await client.get(
            f"/chats/{chat.id}/messages?limit=50",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_more"] is False

    @pytest.mark.asyncio
    async def test_get_messages_chat_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Get messages for non-existent chat → 404."""
        user = await create_verified_user(db_session)
        fake_id = uuid.uuid4()

        response = await client.get(
            f"/chats/{fake_id}/messages",
            headers=auth_header(user),
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_messages_other_users_chat(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Get messages from another user's chat → 403."""
        owner = await create_verified_user(db_session, "msg_owner@example.com")
        intruder = await create_verified_user(db_session, "msg_intruder@example.com")
        chat = await create_chat_in_db(db_session, owner)

        response = await client.get(
            f"/chats/{chat.id}/messages",
            headers=auth_header(intruder),
        )

        assert response.status_code == 403


# ═════════════════════════════════════════════════════════════════════════════
# 10. TestLLMServiceUnit — Unit tests for llm_service.py
# ═════════════════════════════════════════════════════════════════════════════


class TestLLMServiceUnit:
    """Unit tests for the LLM service functions."""

    @pytest.mark.asyncio
    async def test_generate_answer_success(self):
        """generate_answer returns LLM response text."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test answer"
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 150

        with patch(
            "src.services.llm_service.client.chat.completions.create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            from src.services.llm_service import generate_answer

            result = await generate_answer([
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hello"},
            ])

            assert result == "Test answer"

    @pytest.mark.asyncio
    async def test_generate_answer_api_error(self):
        """generate_answer raises exception on API error."""
        with patch(
            "src.services.llm_service.client.chat.completions.create",
            new_callable=AsyncMock,
            side_effect=Exception("API rate limit"),
        ):
            from src.services.llm_service import generate_answer

            with pytest.raises(Exception, match="API rate limit"):
                await generate_answer([{"role": "user", "content": "Hello"}])

    @pytest.mark.asyncio
    async def test_generate_chat_title_success(self):
        """generate_chat_title returns a short title."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '"CNN Medical Imaging Limits"'

        with patch(
            "src.services.llm_service.client.chat.completions.create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            from src.services.llm_service import generate_chat_title

            title = await generate_chat_title("What are CNN limitations?")
            assert title == "CNN Medical Imaging Limits"  # Quotes stripped

    @pytest.mark.asyncio
    async def test_generate_chat_title_strips_quotes(self):
        """generate_chat_title strips surrounding quotes from the title."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '  "Deep Learning Survey"  '

        with patch(
            "src.services.llm_service.client.chat.completions.create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            from src.services.llm_service import generate_chat_title

            title = await generate_chat_title("Tell me about deep learning")
            assert title == "Deep Learning Survey"


# ═════════════════════════════════════════════════════════════════════════════
# 11. TestChatSchemaValidation — Pydantic schema edge cases
# ═════════════════════════════════════════════════════════════════════════════


class TestChatSchemaValidation:
    """Unit tests for Pydantic schema validators."""

    def test_query_request_strips_whitespace(self):
        """QueryRequest strips whitespace from question."""
        from src.models.schemas.chat_schemas import QueryRequest
        req = QueryRequest(question="  Hello world  ")
        assert req.question == "Hello world"

    def test_query_request_rejects_empty_string(self):
        """QueryRequest rejects empty string."""
        from src.models.schemas.chat_schemas import QueryRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            QueryRequest(question="")

    def test_query_request_rejects_whitespace_only(self):
        """QueryRequest rejects whitespace-only string."""
        from src.models.schemas.chat_schemas import QueryRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            QueryRequest(question="   \t\n   ")

    def test_query_request_valid_document_ids(self):
        """QueryRequest accepts valid UUID document_ids."""
        from src.models.schemas.chat_schemas import QueryRequest
        valid_id = str(uuid.uuid4())
        req = QueryRequest(question="Hello", document_ids=[valid_id])
        assert req.document_ids == [valid_id]

    def test_query_request_invalid_document_ids(self):
        """QueryRequest rejects invalid UUID document_ids."""
        from src.models.schemas.chat_schemas import QueryRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            QueryRequest(question="Hello", document_ids=["not-a-uuid"])
