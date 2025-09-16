#!/usr/bin/env python3
"""Simple test script to verify database functionality."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import our database modules
from pixie.core.database.models.base import Base
from pixie.core.database.models.attribute import Attribute
from pixie.core.database.models.category import Category
from pixie.core.database.repositories.attribute_repository import AttributeRepository
from pixie.core.database.repositories.category_repository import CategoryRepository


def test_database_functionality():
    """Test basic database operations."""
    print("Testing database functionality...")

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        # Create engine and session
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        with SessionLocal() as session:
            # Create test data
            print("Creating test categories...")

            # Create categories
            categories_data = [
                {
                    "name": "printers",
                    "display_name": "Printers",
                    "description": "Printer and multifunction devices",
                },
                {
                    "name": "laptops",
                    "display_name": "Laptops",
                    "description": "Laptop computers",
                },
            ]

            categories = {}
            for cat_data in categories_data:
                category = Category(
                    name=cat_data["name"],
                    display_name=cat_data["display_name"],
                    description=cat_data["description"],
                )
                session.add(category)
                categories[cat_data["name"]] = category

            session.commit()

            # Create attributes
            print("Creating test attributes...")
            attributes_data = {
                "printers": [
                    {
                        "name": "budget",
                        "question": "Wat is je budget?",
                        "type": "range",
                        "description": "Maximum budget",
                    },
                    {
                        "name": "brand",
                        "question": "Welk merk?",
                        "type": "choice",
                        "description": "Brand preference",
                        "options": '["HP", "Canon"]',
                    },
                ]
            }

            for category_name, attrs in attributes_data.items():
                category = categories[category_name]
                for attr_data in attrs:
                    attribute = Attribute(
                        category_id=category.id,
                        name=attr_data["name"],
                        question=attr_data["question"],
                        type=attr_data["type"],
                        description=attr_data.get("description"),
                        options=attr_data.get("options"),
                    )
                    session.add(attribute)

            session.commit()

            # Test repositories
            print("Testing repositories...")

            category_repo = CategoryRepository(session)
            attr_repo = AttributeRepository(session)

            # Test category retrieval
            all_categories = category_repo.get_all()
            print(f"Found {len(all_categories)} categories")

            printers_cat = category_repo.get_by_name("printers")
            if printers_cat is None:
                print("❌ Printers category not found!")
                return
            print(f"Printers category: {printers_cat.display_name}")

            # Test attribute retrieval
            printer_attrs = attr_repo.get_by_category(printers_cat.id)
            print(f"Found {len(printer_attrs)} printer attributes")

            for attr in printer_attrs:
                print(f"  - {attr.name}: {attr.question}")

            budget_attr = attr_repo.get_by_category_and_name(printers_cat.id, "budget")
            if budget_attr is None:
                print("❌ Budget attribute not found!")
                return
            print(f"Budget attribute type: {budget_attr.type}")

            print("✅ All database tests passed!")

    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    test_database_functionality()
