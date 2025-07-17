"""
Plant Care Application - Base Database Models

This module contains the base SQLAlchemy model class and common functionality.
Individual modules will define their own models that inherit from this base.
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, func

# Create the base class for all database models
Base = declarative_base()


class TimestampMixin:
    """
    Mixin to add created_at and updated_at timestamps to models.
    """
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class BaseModel(Base, TimestampMixin):
    """
    Base model class with common functionality.
    """
    __abstract__ = True
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
    
    def __repr__(self):
        """String representation of the model."""
        return f"<{self.__class__.__name__}({self.id if hasattr(self, 'id') else 'no_id'})>"


# Export the base classes
__all__ = ["Base", "BaseModel", "TimestampMixin"]