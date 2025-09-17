"""Database fixtures and test utilities for integration tests."""

import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pixie.core.database.models.attribute import Attribute
from pixie.core.database.models.base import Base
from pixie.core.database.models.category import Category
from pixie.core.database.models.laptop import Laptop
from pixie.core.database.models.printer import Printer


@pytest.fixture(scope="session")
def test_db_path():
    """Create a temporary database file for testing."""
    # Create temporary file
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_pixie.db"
    yield str(db_path)

    # Cleanup after tests
    if db_path.exists():
        db_path.unlink()
    Path(temp_dir).rmdir()


@pytest.fixture(scope="session")
def test_engine(test_db_path):
    """Create a test database engine."""
    # Set test database URL
    test_db_url = f"sqlite:///{test_db_path}"

    # Create engine
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=None,  # Disable connection pooling for SQLite
        echo=False,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    engine.dispose()


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a test database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def seeded_test_session(test_session):
    """Create a test session with seeded data."""
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
        {
            "name": "computers",
            "display_name": "Computers",
            "description": "Desktop computers",
        },
        {
            "name": "smartphones",
            "display_name": "Smartphones",
            "description": "Mobile phones",
        },
    ]

    categories = {}
    for cat_data in categories_data:
        category = Category(
            name=cat_data["name"],
            display_name=cat_data["display_name"],
            description=cat_data["description"],
        )
        test_session.add(category)
        categories[cat_data["name"]] = category

    test_session.commit()

    # Create attributes for each category
    attributes_data = {
        "printers": [
            {
                "name": "budget",
                "question": "Wat is je budget?",
                "type": "range",
                "description": "Maximum budget for the printer",
            },
            {
                "name": "brand",
                "question": "Heb je een voorkeur voor een merk?",
                "type": "choice",
                "description": "Preferred printer brand",
                "options": '["HP", "Brother", "Epson", "Canon", "Samsung"]',
            },
            {
                "name": "technology",
                "question": "Welke printer technologie geef je de voorkeur aan?",
                "type": "choice",
                "description": "Printing technology preference",
                "options": '["Laser", "Inkjet", "Dot Matrix"]',
            },
        ],
        "laptops": [
            {
                "name": "budget",
                "question": "Wat is je budget voor de laptop?",
                "type": "range",
                "description": "Maximum budget for the laptop",
            },
            {
                "name": "screen_size",
                "question": "Welke schermgrootte geef je de voorkeur aan?",
                "type": "choice",
                "description": "Preferred screen size",
                "options": '["13 inch", "14 inch", "15.6 inch", "16 inch", "17 inch"]',
            },
        ],
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
            test_session.add(attribute)

    # Create test products
    # Printers
    printers_data = [
        {
            "name": "HP LaserJet Pro",
            "brand": "HP",
            "technology": "Laser",
            "price": 199.99,
        },
        {
            "name": "Brother MFC-1910W",
            "brand": "Brother",
            "technology": "Laser",
            "price": 149.99,
        },
        {
            "name": "Epson EcoTank",
            "brand": "Epson",
            "technology": "Inkjet",
            "price": 299.99,
        },
    ]

    for printer_data in printers_data:
        printer = Printer(
            name=printer_data["name"],
            brand=printer_data["brand"],
            technology=printer_data["technology"],
            price=printer_data["price"],
            price_cents=int(printer_data["price"] * 100),
            currency="EUR",
        )
        test_session.add(printer)

    # Laptops
    laptops_data = [
        {
            "name": "Dell XPS 13",
            "brand": "Dell",
            "price": 1299.99,
            "screen_size_inches": 13.3,
        },
        {
            "name": "MacBook Air",
            "brand": "Apple",
            "price": 1199.99,
            "screen_size_inches": 13.3,
        },
    ]

    for laptop_data in laptops_data:
        laptop = Laptop(
            name=laptop_data["name"],
            brand=laptop_data["brand"],
            price=laptop_data["price"],
            price_cents=int(laptop_data["price"] * 100),
            currency="EUR",
            screen_size_inches=laptop_data["screen_size_inches"],
        )
        test_session.add(laptop)

    test_session.commit()

    yield test_session


@pytest.fixture(scope="function")
def test_db_url(test_db_path):
    """Provide test database URL."""
    return f"sqlite:///{test_db_path}"


@pytest.fixture(scope="function")
def db_session_override(test_db_url, monkeypatch):
    """Override the database URL for testing."""
    monkeypatch.setenv("DATABASE_URL", test_db_url)
