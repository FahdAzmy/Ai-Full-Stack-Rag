"""
Initialize the test database with all tables + pgvector extension.

Usage:
    python scripts/init_test_db.py

This script:
1. Enables the pgvector extension
2. Creates all tables via SQLAlchemy Base.metadata.create_all
3. Stamps Alembic to 'head' so migrations are in sync
"""

import asyncio
import subprocess
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Import Base and ALL models so they register with metadata
from src.helpers.db import Base
from src.models.db_scheams.user import User  # noqa: F401
from src.models.db_scheams.document import Document  # noqa: F401
from src.models.db_scheams.DocumentChunk import DocumentChunk  # noqa: F401
from src.models.db_scheams.Chat import Chat  # noqa: F401
from src.models.db_scheams.Message import Message  # noqa: F401

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/auth_test"


async def init_test_db():
    engine = create_async_engine(TEST_DB_URL, echo=True)

    async with engine.begin() as conn:
        # 1. Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        print("✅ pgvector extension enabled")

        # 2. Drop all existing tables (clean slate)
        await conn.run_sync(Base.metadata.drop_all)
        print("✅ Old tables dropped")

        # 3. Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✅ All tables created")

    await engine.dispose()

    # 4. Stamp alembic to head (so it knows the DB is up to date)
    print("\n📌 Stamping Alembic to head...")
    result = subprocess.run(
        ["alembic", "-c", "alembic-test.ini", "stamp", "head"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("✅ Alembic stamped to head")
    else:
        print(f"⚠️  Alembic stamp warning: {result.stderr}")

    print("\n🎉 Test database ready!")


if __name__ == "__main__":
    asyncio.run(init_test_db())
