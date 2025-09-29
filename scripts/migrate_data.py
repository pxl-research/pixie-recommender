#!/usr/bin/env python3
"""Data migration script to populate database from JSON files."""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pixie.core.database.connection import get_db_session
from pixie.core.database.models import (
    Attribute,
    Category,
    Computer,
    Laptop,
    Printer,
    Smartphone,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataMigration:
    """Handles migration of JSON data to PostgreSQL database."""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.stats = {
            "printers": 0,
            "laptops": 0,
            "computers": 0,
            "smartphones": 0,
            "categories": 0,
            "attributes": 0,
        }

    def load_json_file(self, filename: str) -> Dict[str, Any]:
        """Load a JSON file from the data directory."""
        file_path = self.data_dir / filename
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return {}

    def migrate_categories_and_attributes(self):
        """Migrate categories and attributes first."""
        logger.info("Migrating categories and attributes...")

        # Load attributes data
        attributes_data = self.load_json_file("attributes.json")

        with get_db_session() as session:
            try:
                # Create categories
                categories = ["printers", "laptops", "computers", "smartphones"]

                for category_name in categories:
                    category = Category(name=category_name)
                    session.add(category)
                    self.stats["categories"] += 1

                # Create attributes for each category
                for category_name, attrs in attributes_data.items():
                    if category_name in categories:
                        for attr_name, attr_info in attrs.items():
                            attribute = Attribute(
                                name=attr_name,
                                category=category_name,
                                data_type=attr_info.get("type", "string"),
                                required=attr_info.get("required", False),
                                description=attr_info.get("description", ""),
                            )
                            session.add(attribute)
                            self.stats["attributes"] += 1

                session.commit()
                logger.info(
                    f"Created {self.stats['categories']} categories and "
                    f"{self.stats['attributes']} attributes"
                )

            except Exception as e:
                session.rollback()
                logger.error(f"Error migrating categories and attributes: {e}")
                raise

    def migrate_printers(self):
        """Migrate printer data."""
        logger.info("Migrating printers...")

        data = self.load_json_file("printers.json")
        printers_data = data.get("printers", [])

        with get_db_session() as session:
            try:
                for item in printers_data:
                    printer = Printer(
                        name=item["name"],
                        brand=item["brand"],
                        technology=item["technology"],
                        price=item["price"],
                        price_cents=item.get("price_cents"),
                        currency=item.get("currency", "EUR"),
                        description=item.get("description", ""),
                        has_wifi=item.get("has_wifi", False),
                        has_duplex=item.get("has_duplex", False),
                        has_color=item.get("has_color", False),
                        is_multifunction=item.get("is_multifunction", False),
                        print_speed_ppm=item.get("print_speed_ppm"),
                        resolution_dpi=item.get("resolution_dpi"),
                        max_paper_size=item.get("max_paper_size"),
                        availability_status=item.get("availability_status", "unknown"),
                        stock_level=item.get("stock_level", 0),
                    )
                    session.add(printer)
                    self.stats["printers"] += 1

                session.commit()
                logger.info(f"Migrated {self.stats['printers']} printers")

            except Exception as e:
                session.rollback()
                logger.error(f"Error migrating printers: {e}")
                raise

    def migrate_laptops(self):
        """Migrate laptop data."""
        logger.info("Migrating laptops...")

        data = self.load_json_file("laptops.json")
        laptops_data = data.get("laptops", [])

        with get_db_session() as session:
            try:
                for item in laptops_data:
                    laptop = Laptop(
                        name=item["name"],
                        brand=item["brand"],
                        price=item["price"],
                        currency=item.get("currency", "EUR"),
                        screen_size_inches=item.get("screen_size_inches"),
                        processor=item.get("processor"),
                        ram_gb=item.get("ram_gb"),
                        storage_gb=item.get("storage_gb"),
                        storage_type=item.get("storage_type"),
                        battery_life_hours=item.get("battery_life_hours"),
                        operating_system=item.get("operating_system"),
                        graphics_card=item.get("graphics_card"),
                        weight_kg=item.get("weight_kg"),
                        has_touchscreen=item.get("has_touchscreen", False),
                        has_webcam=item.get("has_webcam", True),
                        warranty_years=item.get("warranty_years"),
                        availability_status=item.get("availability_status", "unknown"),
                        stock_level=item.get("stock_level", 0),
                    )
                    session.add(laptop)
                    self.stats["laptops"] += 1

                session.commit()
                logger.info(f"Migrated {self.stats['laptops']} laptops")

            except Exception as e:
                session.rollback()
                logger.error(f"Error migrating laptops: {e}")
                raise

    def migrate_computers(self):
        """Migrate computer data."""
        logger.info("Migrating computers...")

        data = self.load_json_file("computers.json")
        computers_data = data.get("computers", [])

        with get_db_session() as session:
            try:
                for item in computers_data:
                    computer = Computer(
                        name=item["name"],
                        brand=item["brand"],
                        price=item["price"],
                        currency=item.get("currency", "EUR"),
                        processor=item.get("processor"),
                        ram_gb=item.get("ram_gb"),
                        storage_gb=item.get("storage_gb"),
                        storage_type=item.get("storage_type"),
                        graphics_card=item.get("graphics_card"),
                        has_wifi=item.get("has_wifi", True),
                        has_bluetooth=item.get("has_bluetooth", True),
                        operating_system=item.get("operating_system"),
                        form_factor=item.get("form_factor"),
                        power_supply_watts=item.get("power_supply_watts"),
                        warranty_years=item.get("warranty_years"),
                        availability_status=item.get("availability_status", "unknown"),
                        stock_level=item.get("stock_level", 0),
                    )
                    session.add(computer)
                    self.stats["computers"] += 1

                session.commit()
                logger.info(f"Migrated {self.stats['computers']} computers")

            except Exception as e:
                session.rollback()
                logger.error(f"Error migrating computers: {e}")
                raise

    def migrate_smartphones(self):
        """Migrate smartphone data."""
        logger.info("Migrating smartphones...")

        data = self.load_json_file("smartphones.json")
        smartphones_data = data.get("smartphones", [])

        with get_db_session() as session:
            try:
                for item in smartphones_data:
                    smartphone = Smartphone(
                        name=item["name"],
                        brand=item["brand"],
                        price=item["price"],
                        currency=item.get("currency", "EUR"),
                        screen_size_inches=item.get("screen_size_inches"),
                        operating_system=item.get("operating_system"),
                        processor=item.get("processor"),
                        ram_gb=item.get("ram_gb"),
                        storage_gb=item.get("storage_gb"),
                        battery_capacity_mah=item.get("battery_capacity_mah"),
                        camera_mp=item.get("camera_mp"),
                        has_5g=item.get("has_5g", False),
                        has_nfc=item.get("has_nfc", False),
                        has_wireless_charging=item.get("has_wireless_charging", False),
                        color_options=item.get("color_options", []),
                        warranty_years=item.get("warranty_years"),
                        availability_status=item.get("availability_status", "unknown"),
                        stock_level=item.get("stock_level", 0),
                    )
                    session.add(smartphone)
                    self.stats["smartphones"] += 1

                session.commit()
                logger.info(f"Migrated {self.stats['smartphones']} smartphones")

            except Exception as e:
                session.rollback()
                logger.error(f"Error migrating smartphones: {e}")
                raise

    def run_migration(self):
        """Run the complete data migration."""
        logger.info("Starting data migration from JSON to PostgreSQL...")

        try:
            # Migrate in order: categories/attributes first, then products
            self.migrate_categories_and_attributes()
            self.migrate_printers()
            self.migrate_laptops()
            self.migrate_computers()
            self.migrate_smartphones()

            logger.info("Data migration completed successfully!")
            logger.info("Migration Statistics:")
            for category, count in self.stats.items():
                logger.info(f"  {category}: {count}")

            total_products = (
                self.stats["printers"]
                + self.stats["laptops"]
                + self.stats["computers"]
                + self.stats["smartphones"]
            )
            logger.info(f"Total products migrated: {total_products}")

        except Exception as e:
            logger.error(f"Data migration failed: {e}")
            raise


def main():
    """Main entry point for the migration script."""
    # Default data directory
    data_dir = os.getenv("PIXIE_DATA_DIR", "pixie/core/data")

    if not os.path.exists(data_dir):
        logger.error(f"Data directory not found: {data_dir}")
        sys.exit(1)

    migration = DataMigration(data_dir)
    migration.run_migration()


if __name__ == "__main__":
    main()
