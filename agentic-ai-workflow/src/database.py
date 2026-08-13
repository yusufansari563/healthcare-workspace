import sys
import logging
import asyncio
from typing import Optional, Any
from src.config import settings

logger = logging.getLogger(__name__)

# Fix for Windows asyncio event loop policy with psycopg3
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

# Checkpointer instances
_postgres_saver = None
_memory_saver = None

def get_memory_checkpointer():
    global _memory_saver
    if _memory_saver is None:
        from langgraph.checkpoint.memory import MemorySaver
        _memory_saver = MemorySaver()
        logger.info("Initialized MemorySaver fallback checkpointer.")
    return _memory_saver

async def get_checkpointer():
    """
    Attempts to initialize Postgres checkpointer using langgraph-checkpoint-postgres.
    If database connection fails or times out, seamlessly falls back to MemorySaver.
    """
    global _postgres_saver
    if _postgres_saver is not None:
        return _postgres_saver

    db_url = settings.get_database_url()
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg_pool import AsyncConnectionPool

        logger.info(f"Connecting to Postgres at {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}...")
        pool = AsyncConnectionPool(
            conninfo=db_url,
            max_size=10,
            kwargs={"autocommit": True, "connect_timeout": 2},
            open=False
        )
        
        # Connect with 2 second timeout for fast fallback
        await asyncio.wait_for(pool.open(wait=True), timeout=2.5)
        
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        _postgres_saver = checkpointer
        logger.info("Successfully setup LangGraph AsyncPostgresSaver checkpointer.")
        return _postgres_saver
    except Exception as e:
        logger.warning(f"Postgres database not available ({e}). Using MemorySaver in-memory fallback.")
        try:
            if 'pool' in locals() and pool:
                await pool.close()
        except Exception:
            pass
        return get_memory_checkpointer()


