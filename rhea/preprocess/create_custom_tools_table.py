"""
Database migration script to create the customtools table.

This script creates the necessary table and indexes for storing custom tools
(non-Galaxy tools like Academy agents) with vector embeddings.
"""

import os
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text

from rhea.utils.models import Base, CustomToolModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_custom_tools_table(db_url: str):
    """
    Create the customtools table in the database.
    
    Args:
        db_url: Database connection URL
    """
    engine: AsyncEngine = create_async_engine(db_url, echo=True, future=True)
    
    async with engine.begin() as conn:
        # Ensure pgvector extension is enabled
        logger.info("Ensuring pgvector extension is enabled...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        # Create the customtools table
        logger.info("Creating customtools table...")
        await conn.run_sync(Base.metadata.create_all, tables=[CustomToolModel.__table__])
        
        logger.info("Successfully created customtools table")
    
    await engine.dispose()


async def main():
    """Main entry point."""
    DATABASE_URL = os.environ.get(
        "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/rhea"
    )
    
    logger.info(f"Connecting to database: {DATABASE_URL}")
    await create_custom_tools_table(DATABASE_URL)
    logger.info("Migration complete!")


if __name__ == "__main__":
    asyncio.run(main())

