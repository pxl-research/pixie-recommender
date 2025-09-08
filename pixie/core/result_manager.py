"""Result management strategies for product discovery."""
from typing import List, Optional
from pixie.core.contracts import Product


class ResultManager:
    """Manages product search results and handles edge cases."""

    def __init__(self, threshold: int = 10):
        self.threshold = threshold

    def is_empty_result(self, products: List[Product]) -> bool:
        """Check if result set is empty."""
        return len(products) == 0

    def is_too_many_results(self, products: List[Product]) -> bool:
        """Check if result set exceeds threshold."""
        return len(products) > self.threshold

    def generate_empty_result_message(self, applied_filters: dict) -> str:
        """Generate helpful message for empty results."""
        filter_parts = []
        
        if "brand" in applied_filters and applied_filters["brand"] != "any":
            filter_parts.append(f"{applied_filters['brand']}")
        
        if "technology" in applied_filters and applied_filters["technology"] != "any":
            filter_parts.append(f"{applied_filters['technology'].lower()}")
            
        if "category" in applied_filters:
            filter_parts.append(f"{applied_filters['category']}")
            
        if "budget" in applied_filters:
            budget = applied_filters["budget"]
            if isinstance(budget, dict):
                if budget["max"] < 150:
                    filter_parts.append("under €150")
                elif budget["min"] >= 300:
                    filter_parts.append("over €300")
                else:
                    filter_parts.append("within budget")

        criteria = " ".join(filter_parts) if filter_parts else "your criteria"
        
        return (
            f"Unfortunately, no products match {criteria}. "
            "Please try again with a broader budget or contact support for assistance."
        )

    def generate_too_many_results_message(self, count: int) -> str:
        """Generate message for large result sets."""
        return (
            f"I found {count} products. Would you like to see the top 5 sorted by price, "
            "or a random sample of 5?"
        )

    def generate_alternatives_suggestion(self, applied_filters: dict) -> List[str]:
        """Generate alternative search suggestions for empty results."""
        suggestions = []
        
        # Suggest removing most restrictive filters
        if "budget" in applied_filters:
            budget = applied_filters["budget"]
            if isinstance(budget, dict) and budget["max"] < 200:
                suggestions.append("Try increasing your budget to €200 or more")
                
        if "brand" in applied_filters and applied_filters["brand"] != "any":
            suggestions.append("Consider other brands for more options")
            
        if "technology" in applied_filters and applied_filters["technology"] != "any":
            suggestions.append("Try different technology types")

        if not suggestions:
            suggestions.append("Try broader search criteria")
            
        return suggestions

    def handle_refinement_options(self, products: List[Product]) -> dict:
        """Generate refinement options for large result sets."""
        return {
            "sort_options": [
                {"label": "Top 5 by price (lowest first)", "value": "price_asc_5"},
                {"label": "Top 5 by price (highest first)", "value": "price_desc_5"},
                {"label": "Random sample of 5", "value": "random_5"},
                {"label": "Show all results", "value": "all"},
            ],
            "total_count": len(products)
        }
