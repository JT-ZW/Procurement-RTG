"""
Database Configuration and Session Management - psycopg2 Compatibility
"""
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import asyncio
from functools import wraps

from app.core.config import settings

# Create metadata with naming convention
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s", 
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)

# Create synchronous engine using psycopg2
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300
)

# Create synchronous session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Async compatibility wrapper
class AsyncSessionWrapper:
    """Wrapper to make sync session look like async session"""
    def __init__(self, session: Session):
        self._session = session
    
    async def execute(self, query, params=None):
        """Execute query asynchronously (but actually sync)"""
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._session.execute(query, params or {})
        )
    
    async def commit(self):
        """Commit transaction"""
        await asyncio.get_event_loop().run_in_executor(
            None, self._session.commit
        )
    
    async def rollback(self):
        """Rollback transaction"""
        await asyncio.get_event_loop().run_in_executor(
            None, self._session.rollback
        )
    
    async def close(self):
        """Close session"""
        await asyncio.get_event_loop().run_in_executor(
            None, self._session.close
        )

# Database session dependency
async def get_db() -> AsyncGenerator[AsyncSessionWrapper, None]:
    """
    Async-compatible database session dependency for FastAPI.
    """
    db = SessionLocal()
    session_wrapper = AsyncSessionWrapper(db)
    try:
        yield session_wrapper
        await session_wrapper.commit()
    except Exception:
        await session_wrapper.rollback()
        raise
    finally:
        await session_wrapper.close()

# Synchronous database session dependency  
def get_sync_db() -> Generator[Session, None, None]:
    """
    Synchronous database session dependency for FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
