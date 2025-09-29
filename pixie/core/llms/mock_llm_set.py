from __future__ import annotations

from typing import Any, Tuple


class MockRelevance:
    def is_relevant(self, text: str) -> bool:
        # Check for product-related keywords
        product_keywords = [
            "printer",
            "laptop",
            "computer",
            "phone",
            "tablet",
            "monitor",
            "keyboard",
            "mouse",
            "headphones",
            "speaker",
            "camera",
            "tv",
            "mixer",
            "koop",
            "prijs",
            "budget",
            "merk",
            "brand",
            "laser",
            "inkjet",
            # Dutch keywords
            "telefoon",
            "drukker",
            "afdrukken",
            "beeldscherm",
            "toetsenbord",
            "muis",
            "koptelefoon",
            "luidspreker",
            "fotocamera",
            "televisie",
            "mixers",
            "keukenmachine",
            "handmixer",
            "staafmixer",
            "planetmixer",
            "blender",
        ]
        text_lower = text.lower()

        # Exclude personal/family questions
        personal_keywords = ["mama", "papa", "moeder", "vader", "familie", "vriend"]
        if any(personal in text_lower for personal in personal_keywords):
            return False

        return any(keyword in text_lower for keyword in product_keywords)

    def detect_category(self, question: str) -> str | None:
        """Detect the product category using keyword-based approach.

        Returns one of: "printers", "laptops", "computers", "smartphones", or None
        """
        text_lower = question.lower()

        # Define keywords for each category
        category_keywords = {
            "printers": ["printer", "print", "laser", "inkjet", "drukker", "afdrukken"],
            "laptops": ["laptop", "notebook", "ultrabook", "macbook", "chromebook"],
            "computers": [
                "computer",
                "pc",
                "desktop",
                "tower",
                "all-in-one",
                "workstation",
            ],
            "smartphones": [
                "smartphone",
                "phone",
                "telefoon",
                "iphone",
                "android",
                "samsung",
                "huawei",
                "xiaomi",
            ],
            "mixers": [
                "mixer",
                "mixers",
                "keukenmachine",
                "handmixer",
                "staafmixer",
                "planetmixer",
                "blender",
                "kitchenaid",
                "bosch",
            ],
        }

        # Check for category-specific keywords
        for category, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return category

        # If no specific category found but product-related,
        # default to printers for backward compatibility
        if self.is_relevant(question):
            return "printers"

        return None


class MockSQL:
    def generate_sql(
        self,
        question: str,
        attributes: dict | None = None,
        table_name: str | None = None,
    ) -> str:
        table = table_name or "printers"
        return f"SELECT * FROM {table};"


class MockRefinement:
    def generate_refinement_question(self, context: dict) -> "str | None":
        if not context:
            return "Wat is je budget?"

        collected = set(context.get("collected_attributes", []))
        category = context.get("category", "printers")

        # Get the appropriate attribute sequence based on category
        if category == "printers":
            attr_sequence = [
                "budget",
                "brand",
                "technology",
                "color",
                "pages_per_minute",
            ]
        elif category == "mixer":
            attr_sequence = [
                "budget",
                "type",
                "brand",
                "power",
                "bowl_capacity",
                "attachments",
            ]
        else:
            # Default sequence for other categories
            attr_sequence = ["budget", "brand"]

        # Find next uncollected attribute
        for attr in attr_sequence:
            if attr not in collected:
                return self._get_mock_question_for_attribute(attr, category)

        return None  # All attributes collected

    def _get_mock_question_for_attribute(
        self, attr_name: str, category: str = "printers"
    ) -> str:
        """Get mock question for an attribute."""
        questions = {
            "budget": "Wat is je budget?",
            "brand": "Heb je een voorkeur voor een merk?",
            "technology": "Welke technologie heeft je voorkeur (inkjet/laser)?",
            "color": "Wil je een kleurenprinter of is zwart-wit voldoende?",
            "pages_per_minute": "Hoeveel pagina's per minuut moet de printer "
            "minimaal kunnen printen?",
            "screen_size": "Welke schermgrootte heb je in gedachten?",
            "processor": "Heb je voorkeur voor een bepaalde processor?",
            "ram": "Hoeveel RAM heb je minimaal nodig?",
            "storage": "Hoeveel opslagruimte heb je nodig?",
            "camera": "Hoe belangrijk is de camera kwaliteit?",
            "battery_life": "Hoe belangrijk is de batterijduur?",
            "usage_type": "Waar ga je het apparaat voor gebruiken?",
            "operating_system": "Welk besturingssysteem heeft je voorkeur?",
            # Mixer-specific questions
            "type": (
                "Welk type mixer heb je in gedachten? Handmixer, staafmixer, "
                "planetmixer, blender of keukenmachine?"
            ),
            "power": (
                "Hoeveel vermogen heeft je voorkeur "
                "(200-400W, 400-600W, 600-800W, 800-1000W, of 1000W+)?"
            ),
            "bowl_capacity": "Welke komgrootte heb je nodig (1-2L, 3-4L, 5-6L, of 7L+)?",
            "attachments": (
                "Welke hulpstukken zijn belangrijk voor je "
                "(deeghaak, garde, platte beater, blender attachment, "
                "vleesmolen, pasta roller)?"
            ),
        }

        # For brand questions, make them category-specific
        if attr_name == "brand":
            if category == "mixer":
                return (
                    "Heb je een voorkeur voor een merk, zoals KitchenAid, Bosch, "
                    "Philips, Braun, Kenwood, Smeg of Sage?"
                )
            elif category == "printers":
                return (
                    "Heb je een voorkeur voor een merk zoals HP, Brother, "
                    "Canon, Epson of Samsung?"
                )
            else:
                return "Heb je een voorkeur voor een merk?"

        return questions.get(attr_name, f"Wat zijn je voorkeuren voor {attr_name}?")


def create_mock_llm_set() -> Tuple[Any, Any, Any]:
    """Create mock LLM instances for testing."""
    return MockRelevance(), MockSQL(), MockRefinement()
