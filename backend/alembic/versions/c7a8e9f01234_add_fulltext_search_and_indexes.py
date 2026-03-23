"""add fulltext search and indexes (SPEC-08)

Revision ID: c7a8e9f01234
Revises: b06ee5d19fb8
Create Date: 2026-03-23 08:56:00.000000

Adds:
  - content_tsv tsvector column on document_chunks (generated from content)
  - GIN index on content_tsv for fast full-text search
  - Standard indexes for common query patterns (user scoping, etc.)
  - IVFFlat index on embeddings (commented out — enable when 1000+ chunks)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7a8e9f01234"
down_revision: Union[str, None] = "5655b9fad93d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Full-Text Search (for hybrid search) ─────────────────────────────

    # 1. Add tsvector column — auto-generated from content
    op.execute("""
        ALTER TABLE document_chunks
        ADD COLUMN IF NOT EXISTS content_tsv tsvector
        GENERATED ALWAYS AS (to_tsvector('english', content)) STORED
    """)

    # 2. GIN index on content_tsv for fast full-text search
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_content_tsv
        ON document_chunks
        USING gin(content_tsv)
    """)

    # ── Standard indexes for query performance ───────────────────────────

    # Speed up user-scoped chunk retrieval
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_user
        ON document_chunks(user_id)
    """)

    # Speed up per-document queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_document
        ON document_chunks(document_id)
    """)

    # Speed up user's document list
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_user
        ON documents(user_id)
    """)

    # Speed up message loading by chat
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_chat
        ON messages(chat_id)
    """)

    # Speed up chat listing by user
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_chats_user
        ON chats(user_id)
    """)

    # ── pgvector IVFFlat index (optional — uncomment when 1000+ chunks) ─
    # op.execute("""
    #     CREATE INDEX IF NOT EXISTS idx_chunks_embedding_ivfflat
    #     ON document_chunks
    #     USING ivfflat (embedding vector_cosine_ops)
    #     WITH (lists = 100)
    # """)


def downgrade() -> None:
    # Drop indexes in reverse order
    op.execute("DROP INDEX IF EXISTS idx_chats_user")
    op.execute("DROP INDEX IF EXISTS idx_messages_chat")
    op.execute("DROP INDEX IF EXISTS idx_documents_user")
    op.execute("DROP INDEX IF EXISTS idx_chunks_document")
    op.execute("DROP INDEX IF EXISTS idx_chunks_user")
    op.execute("DROP INDEX IF EXISTS idx_chunks_content_tsv")

    # Drop the tsvector column
    op.execute("ALTER TABLE document_chunks DROP COLUMN IF EXISTS content_tsv")
