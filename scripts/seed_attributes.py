"""Database seeding script for attributes and categories."""

from pixie.core.database.connection import get_db_session
from pixie.core.database.models.attribute import Attribute
from pixie.core.database.models.category import Category


def seed_database():
    """Seed the database with initial attribute configuration."""
    with get_db_session() as session:
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
            # Check if category already exists
            existing_category = (
                session.query(Category)
                .filter(Category.name == cat_data["name"])
                .first()
            )

            if existing_category:
                categories[cat_data["name"]] = existing_category
                print(f"Category '{cat_data['name']}' already exists, skipping...")
            else:
                category = Category(
                    name=cat_data["name"],
                    display_name=cat_data["display_name"],
                    description=cat_data["description"],
                )
                session.add(category)
                categories[cat_data["name"]] = category
                print(f"Created category '{cat_data['name']}'")

        session.commit()  # Commit to get IDs

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
                {
                    "name": "processor",
                    "question": "Welke processor geef je de voorkeur aan?",
                    "type": "choice",
                    "description": "Preferred processor type",
                    "options": '["Intel Core i3", "Intel Core i5", '
                    '"Intel Core i7", "AMD Ryzen 3", '
                    '"AMD Ryzen 5", "AMD Ryzen 7"]',
                },
            ],
            "computers": [
                {
                    "name": "budget",
                    "question": "Wat is je budget voor de computer?",
                    "type": "range",
                    "description": "Maximum budget for the computer",
                },
                {
                    "name": "processor",
                    "question": "Welke processor geef je de voorkeur aan?",
                    "type": "choice",
                    "description": "Preferred processor type",
                    "options": '["Intel Core i3", "Intel Core i5", '
                    '"Intel Core i7", "AMD Ryzen 3", '
                    '"AMD Ryzen 5", "AMD Ryzen 7"]',
                },
                {
                    "name": "ram",
                    "question": "Hoeveel RAM heb je minimaal nodig?",
                    "type": "choice",
                    "description": "Minimum RAM requirement",
                    "options": '["4GB", "8GB", "16GB", "32GB"]',
                },
            ],
            "smartphones": [
                {
                    "name": "budget",
                    "question": "Wat is je budget voor de smartphone?",
                    "type": "range",
                    "description": "Maximum budget for the smartphone",
                },
                {
                    "name": "brand",
                    "question": "Welk merk geef je de voorkeur aan?",
                    "type": "choice",
                    "description": "Preferred smartphone brand",
                    "options": '["Samsung", "Apple", "Google", "OnePlus", "Xiaomi"]',
                },
                {
                    "name": "screen_size",
                    "question": "Welke schermgrootte geef je de voorkeur aan?",
                    "type": "choice",
                    "description": "Preferred screen size",
                    "options": '["5.5 inch", "6.1 inch", "6.5 inch", "6.7 inch"]',
                },
            ],
        }

        for category_name, attrs in attributes_data.items():
            category = categories[category_name]
            for attr_data in attrs:
                # Check if attribute already exists
                existing_attribute = (
                    session.query(Attribute)
                    .filter(
                        Attribute.category_id == category.id,
                        Attribute.name == attr_data["name"],
                    )
                    .first()
                )

                if existing_attribute:
                    print(
                        f"Attribute '{attr_data['name']}' for category "
                        f"'{category_name}' already exists, skipping..."
                    )
                else:
                    attribute = Attribute(
                        category_id=category.id,
                        name=attr_data["name"],
                        question=attr_data["question"],
                        type=attr_data["type"],
                        description=attr_data.get("description"),
                        options=attr_data.get("options"),
                    )
                    session.add(attribute)
                    print(
                        f"Created attribute '{attr_data['name']}' for category '{category_name}'"
                    )

        session.commit()
        print("✅ Database seeded with categories and attributes!")


if __name__ == "__main__":
    seed_database()
