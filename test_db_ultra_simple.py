#!/usr/bin/env python3
"""Ultra simple test for database models only."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    display_name = Column(String)
    description = Column(Text, nullable=True)


class Attribute(Base):
    __tablename__ = "attributes"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    name = Column(String)
    question = Column(String)
    type = Column(String)
    description = Column(Text, nullable=True)
    options = Column(Text, nullable=True)

    category = relationship("Category")


def test_basic_db():
    """Test basic database operations."""
    print("Testing basic database functionality...")

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        # Create engine and session
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        with SessionLocal() as session:
            # Create test category
            print("Creating test category...")
            category = Category(
                name="printers", display_name="Printers", description="Printer devices"
            )
            session.add(category)
            session.commit()

            # Create test attribute
            print("Creating test attribute...")
            attribute = Attribute(
                category_id=category.id,
                name="budget",
                question="Wat is je budget?",
                type="range",
                description="Maximum budget",
            )
            session.add(attribute)
            session.commit()

            # Query data
            print("Querying data...")
            cats = session.query(Category).all()
            print(f"Found {len(cats)} categories")

            attrs = session.query(Attribute).all()
            print(f"Found {len(attrs)} attributes")

            for cat in cats:
                print(f"Category: {cat.name} - {cat.display_name}")

            for attr in attrs:
                print(f"Attribute: {attr.name} - {attr.question}")

            print("✅ Basic database test passed!")

    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    test_basic_db()
