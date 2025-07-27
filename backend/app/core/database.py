"""
Database Configuration
SQLAlchemy setup and database session management for the Procurement System.
Supports both sync (for migrations) and async (for FastAPI) operations with Supabase.
"""

from typing import AsyncGenerator, Generator
import logging
from sqlalchemy import create_engine, event, MetaData, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import asyncio

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# =====================================================
# DATABASE METADATA AND BASE
# =====================================================

# Create metadata with naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s", 
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

# Create declarative base
Base = declarative_base(metadata=metadata)

# =====================================================
# SYNC DATABASE ENGINE (for migrations and admin tasks)
# =====================================================

def create_sync_engine():
    """Create synchronous database engine for Alembic migrations."""
    return create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,  # Verify connections before use
        echo=settings.DEBUG,  # Log SQL queries in debug mode
        future=True
    )

# Create sync engine
sync_engine = create_sync_engine()

# Create sync session factory
SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
    future=True
)

# =====================================================
# ASYNC DATABASE ENGINE (for FastAPI app)
# =====================================================

def create_async_engine_url():
    """Convert sync database URL to async URL for asyncpg."""
    if settings.DATABASE_URL.startswith("postgresql://"):
        return settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    elif settings.DATABASE_URL.startswith("postgresql+asyncpg://"):
        return settings.DATABASE_URL
    else:
        raise ValueError("DATABASE_URL must be a PostgreSQL connection string")

def create_async_db_engine():
    """Create asynchronous database engine for FastAPI."""
    async_url = create_async_engine_url()
    
    return create_async_engine(
        async_url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
        echo=settings.DEBUG,
        future=True
    )

# Create async engine
engine = create_async_db_engine()

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

# =====================================================
# DATABASE SESSION DEPENDENCIES
# =====================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async database session dependency for FastAPI.
    
    Usage:
        @app.get("/users/")
        async def get_users(db: AsyncSession = Depends(get_db)):
            # Use db session here
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            logger.debug("Database session started")
            yield session
            await session.commit()
            logger.debug("Database session committed")
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
            logger.debug("Database session closed")


def get_sync_db() -> Generator[Session, None, None]:
    """
    Synchronous database session for admin tasks and migrations.
    
    Usage:
        def some_admin_function():
            with next(get_sync_db()) as db:
                # Use db session here
                result = db.execute(select(User))
                return result.scalars().all()
    """
    db = SyncSessionLocal()
    try:
        logger.debug("Sync database session started")
        yield db
        db.commit()
        logger.debug("Sync database session committed")
    except Exception as e:
        logger.error(f"Sync database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("Sync database session closed")

# =====================================================
# DATABASE CONNECTION UTILITIES
# =====================================================

async def check_database_connection() -> bool:
    """
    Check if async database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.info("✅ Async database connection successful")
                return True
            else:
                logger.error("❌ Async database connection test failed")
                return False
    except Exception as e:
        logger.error(f"❌ Async database connection failed: {e}")
        return False


def check_sync_database_connection() -> bool:
    """
    Check if sync database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        with sync_engine.begin() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.info("✅ Sync database connection successful")
                return True
            else:
                logger.error("❌ Sync database connection test failed")
                return False
    except Exception as e:
        logger.error(f"❌ Sync database connection failed: {e}")
        return False


async def get_database_version() -> str:
    """
    Get PostgreSQL database version.
    
    Returns:
        str: Database version string
    """
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            return version
    except Exception as e:
        logger.error(f"Failed to get database version: {e}")
        return "Unknown"

# =====================================================
# TABLE MANAGEMENT UTILITIES
# =====================================================

async def create_tables():
    """
    Create all tables in the database.
    ⚠️ This should only be used in development or testing.
    In production, use Alembic migrations.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise


async def drop_tables():
    """
    Drop all tables in the database.
    ⚠️ DANGEROUS: This will delete all data!
    Only use in development/testing environments.
    """
    if not settings.DEBUG:
        raise RuntimeError("Cannot drop tables in production mode")
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("⚠️ All database tables dropped")
    except Exception as e:
        logger.error(f"❌ Failed to drop database tables: {e}")
        raise


def create_sync_tables():
    """
    Create all tables using sync engine (for migrations).
    """
    try:
        Base.metadata.create_all(bind=sync_engine)
        logger.info("✅ Database tables created successfully (sync)")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables (sync): {e}")
        raise

# =====================================================
# TRANSACTION UTILITIES
# =====================================================

class DatabaseTransaction:
    """
    Async context manager for database transactions.
    
    Usage:
        async with DatabaseTransaction() as db:
            # Database operations here
            user = User(name="John Doe")
            db.add(user)
            # Auto-commit on success, rollback on exception
    """
    
    def __init__(self):
        self.session: AsyncSession = None
    
    async def __aenter__(self) -> AsyncSession:
        self.session = AsyncSessionLocal()
        logger.debug("Transaction started")
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                await self.session.commit()
                logger.debug("Transaction committed")
            else:
                await self.session.rollback()
                logger.warning(f"Transaction rolled back due to: {exc_val}")
        except Exception as e:
            logger.error(f"Error during transaction cleanup: {e}")
        finally:
            await self.session.close()
            logger.debug("Transaction session closed")


class SyncDatabaseTransaction:
    """
    Sync context manager for database transactions.
    
    Usage:
        with SyncDatabaseTransaction() as db:
            # Database operations here
            user = User(name="John Doe")
            db.add(user)
            # Auto-commit on success, rollback on exception
    """
    
    def __init__(self):
        self.session: Session = None
    
    def __enter__(self) -> Session:
        self.session = SyncSessionLocal()
        logger.debug("Sync transaction started")
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                self.session.commit()
                logger.debug("Sync transaction committed")
            else:
                self.session.rollback()
                logger.warning(f"Sync transaction rolled back due to: {exc_val}")
        except Exception as e:
            logger.error(f"Error during sync transaction cleanup: {e}")
        finally:
            self.session.close()
            logger.debug("Sync transaction session closed")

# =====================================================
# DATABASE HEALTH CHECK
# =====================================================

async def database_health_check() -> dict:
    """
    Comprehensive database health check for monitoring.
    
    Returns:
        dict: Health check results with detailed metrics
    """
    health_status = {
        "status": "unknown",
        "connection": False,
        "pool_size": 0,
        "checked_out": 0,
        "overflow": 0,
        "invalid": 0,
        "postgres_version": None,
        "response_time_ms": None
    }
    
    import time
    start_time = time.time()
    
    try:
        # Test basic connection and get database version
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            health_status["postgres_version"] = version[:100]  # Truncate long version string
            health_status["connection"] = True
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000
        health_status["response_time_ms"] = round(response_time, 2)
        
        # Check connection pool status
        pool = engine.pool
        health_status.update({
            "pool_size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid()
        })
        
        # Determine overall status
        if response_time < 100:  # Less than 100ms is excellent
            health_status["status"] = "healthy"
        elif response_time < 500:  # Less than 500ms is acceptable
            health_status["status"] = "degraded" 
        else:
            health_status["status"] = "slow"
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        health_status["response_time_ms"] = (time.time() - start_time) * 1000
    
    return health_status

# =====================================================
# MULTI-TENANT UTILITIES
# =====================================================

def get_unit_filter_clause(unit_ids: list) -> str:
    """
    Generate SQL WHERE clause for multi-tenant filtering.
    
    Args:
        unit_ids: List of unit IDs the user has access to
    
    Returns:
        str: SQL WHERE clause for filtering by units
    """
    if not unit_ids:
        return "1=0"  # No access - always false condition
    
    # Convert UUIDs to strings for SQL
    unit_ids_str = "', '".join(str(uid) for uid in unit_ids)
    return f"unit_id IN ('{unit_ids_str}')"


async def test_multi_tenant_access(user_id: str, unit_id: str) -> bool:
    """
    Test if a user has access to a specific unit.
    
    Args:
        user_id: User UUID as string
        unit_id: Unit UUID as string
    
    Returns:
        bool: True if user has access, False otherwise
    """
    try:
        async with DatabaseTransaction() as db:
            result = await db.execute(
                text("""
                    SELECT 1 FROM user_unit_assignments 
                    WHERE user_id = :user_id AND unit_id = :unit_id
                """),
                {"user_id": user_id, "unit_id": unit_id}
            )
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Error testing multi-tenant access: {e}")
        return False

# =====================================================
# INITIALIZATION AND CLEANUP
# =====================================================

async def init_database():
    """
    Initialize database connection and perform startup checks.
    """
    logger.info("🔄 Initializing database connection...")
    
    try:
        # Check async connection
        if await check_database_connection():
            version = await get_database_version()
            logger.info(f"✅ Database initialized successfully")
            logger.info(f"📊 PostgreSQL version: {version[:50]}...")
        else:
            raise Exception("Async database connection failed")
        
        # Check sync connection
        if check_sync_database_connection():
            logger.info("✅ Sync database connection verified")
        else:
            logger.warning("⚠️ Sync database connection failed")
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def close_database():
    """
    Clean up database connections gracefully.
    """
    logger.info("🔄 Closing database connections...")
    
    try:
        # Close async engine
        await engine.dispose()
        logger.info("✅ Async database connections closed")
        
        # Close sync engine
        sync_engine.dispose()
        logger.info("✅ Sync database connections closed")
        
    except Exception as e:
        logger.error(f"❌ Error closing database connections: {e}")


# =====================================================
# DATABASE EVENTS (for connection monitoring)
# =====================================================

@event.listens_for(sync_engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Handle new database connections."""
    logger.debug("New database connection established")


@event.listens_for(sync_engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Handle connection checkout from pool."""
    logger.debug("Database connection checked out from pool")


@event.listens_for(sync_engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Handle connection checkin to pool."""
    logger.debug("Database connection returned to pool")


# =====================================================
# TESTING UTILITIES
# =====================================================

async def test_database_operations():
    """
    Test basic database operations for development/testing.
    """
    if not settings.DEBUG:
        logger.warning("Database operations test skipped (not in debug mode)")
        return
    
    logger.info("🧪 Testing database operations...")
    
    try:
        # Test basic query
        async with DatabaseTransaction() as db:
            result = await db.execute(text("SELECT COUNT(*) FROM units"))
            count = result.scalar()
            logger.info(f"✅ Found {count} units in database")
        
        # Test user access query
        async with DatabaseTransaction() as db:
            result = await db.execute(text("""
                SELECT u.unit_name, COUNT(uua.user_id) as user_count
                FROM units u
                LEFT JOIN user_unit_assignments uua ON u.id = uua.unit_id
                GROUP BY u.id, u.unit_name
                ORDER BY u.unit_name
            """))
            units = result.fetchall()
            
            logger.info("📊 Unit access summary:")
            for unit_name, user_count in units:
                logger.info(f"   {unit_name}: {user_count} users")
        
        logger.info("✅ Database operations test completed")
        
    except Exception as e:
        logger.error(f"❌ Database operations test failed: {e}")
        raise


# Export commonly used items
__all__ = [
    "Base",
    "engine", 
    "sync_engine",
    "get_db",
    "get_sync_db",
    "AsyncSessionLocal",
    "SyncSessionLocal",
    "DatabaseTransaction",
    "SyncDatabaseTransaction",
    "check_database_connection",
    "check_sync_database_connection",
    "database_health_check",
    "init_database",
    "close_database",
    "create_tables",
    "drop_tables",
    "test_database_operations",
    "get_unit_filter_clause",
    "test_multi_tenant_access"
]