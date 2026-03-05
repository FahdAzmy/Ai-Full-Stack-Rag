"""Drop and recreate test DB tables to get the new chunk_index column."""

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def reset():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5433/auth_test"
    )
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS document_chunks CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS documents CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        print("Tables dropped successfully. They will be recreated on next test run.")
    await engine.dispose()


asyncio.run(reset())
