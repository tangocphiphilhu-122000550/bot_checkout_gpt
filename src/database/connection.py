"""Database connection management"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from database.models import Base
from utils.logger import log


class Database:
    """Database connection manager"""
    
    def __init__(self, database_url: str = None):
        """
        Initialize database connection
        
        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        
        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment variables")
        
        # Create engine
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=5,
            max_overflow=10
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self):
        """Create all tables if they don't exist"""
        try:
            Base.metadata.create_all(bind=self.engine)
            log.success("✅ Database tables created/verified")
        except Exception as e:
            log.error(f"❌ Failed to create tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session with automatic cleanup
        
        Usage:
            with db.get_session() as session:
                # Use session here
                pass
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            log.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()


# Global database instance
_db_instance = None


def get_database() -> Database:
    """Get or create global database instance"""
    global _db_instance
    
    if _db_instance is None:
        _db_instance = Database()
        _db_instance.create_tables()
    
    return _db_instance


def init_database():
    """Initialize database (create tables)"""
    db = get_database()
    db.create_tables()
    log.success("✅ Database initialized")
