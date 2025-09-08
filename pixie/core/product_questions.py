"""Product refinement question generation patterns."""
from typing import Dict, List, Optional


class ProductQuestionGenerator:
    """Generates intelligent refinement questions for product discovery."""

    BUDGET_RANGES = [
        {"label": "Less than €150", "min": 0, "max": 150},
        {"label": "Between €150–€300", "min": 150, "max": 300},
        {"label": "More than €300", "min": 300, "max": float("inf")},
        {"label": "No preference", "min": 0, "max": float("inf")},
    ]

    SUPPORTED_BRANDS = [
        "Brother",
        "BenQ", 
        "HP",
        "Kyocera",
        "Canon",
        "Epson",
    ]

    TECHNOLOGY_OPTIONS = {
        "printer": ["Inkjet", "Laser", "Thermal inkjet"],
        "laptop": ["Gaming", "Business", "Ultrabook"],
        "smartphone": ["Android", "iOS"],
        "tablet": ["Android", "iOS", "Windows"],
    }

    def __init__(self):
        self._question_order = ["budget", "brand", "technology"]

    def get_next_question(
        self, 
        category: str, 
        applied_filters: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Generate the next refinement question based on applied filters."""
        if applied_filters is None:
            applied_filters = {}

        # Find the first question type that hasn't been answered
        for question_type in self._question_order:
            if question_type not in applied_filters:
                return self._generate_question(question_type, category)

        return None  # All questions have been answered

    def _generate_question(self, question_type: str, category: str) -> str:
        """Generate a specific refinement question."""
        if question_type == "budget":
            return self._generate_budget_question()
        elif question_type == "brand":
            return self._generate_brand_question()
        elif question_type == "technology":
            return self._generate_technology_question(category)
        else:
            return "Can you provide more specific requirements?"

    def _generate_budget_question(self) -> str:
        """Generate budget refinement question."""
        options = ", ".join([r["label"] for r in self.BUDGET_RANGES])
        return f"What is your budget? {options}?"

    def _generate_brand_question(self) -> str:
        """Generate brand refinement question.""" 
        brands = ", ".join(self.SUPPORTED_BRANDS[:-1]) + f", {self.SUPPORTED_BRANDS[-1]}"
        return f"Which brand do you prefer? {brands}, or no preference?"

    def _generate_technology_question(self, category: str) -> str:
        """Generate technology-specific question based on product category."""
        technologies = self.TECHNOLOGY_OPTIONS.get(category, ["Standard", "Premium"])
        tech_options = ", ".join(technologies[:-1]) + f", {technologies[-1]}"
        
        if category == "printer":
            return f"Which printing technology? {tech_options}, or no preference?"
        elif category == "laptop":
            return f"What type of laptop? {tech_options}, or no preference?"
        elif category in ["smartphone", "tablet"]:
            return f"Which operating system? {tech_options}, or no preference?"
        else:
            return f"Which type? {tech_options}, or no preference?"

    def parse_budget_response(self, response: str) -> Optional[Dict[str, float]]:
        """Parse budget response into min/max values."""
        response_lower = response.lower()
        
        for budget_range in self.BUDGET_RANGES:
            label_lower = budget_range["label"].lower()
            if "less than" in label_lower and ("less than" in response_lower or "onder" in response_lower):
                if "150" in response_lower:
                    return {"min": 0, "max": 150}
            elif "between" in label_lower and ("between" in response_lower or "tussen" in response_lower):
                if "150" in response_lower and "300" in response_lower:
                    return {"min": 150, "max": 300}
            elif "more than" in label_lower and ("more than" in response_lower or "meer dan" in response_lower):
                if "300" in response_lower:
                    return {"min": 300, "max": float("inf")}
            elif "no preference" in label_lower and ("no preference" in response_lower or "geen" in response_lower):
                return {"min": 0, "max": float("inf")}

        return None

    def parse_brand_response(self, response: str) -> Optional[str]:
        """Parse brand response."""
        response_lower = response.lower()
        
        for brand in self.SUPPORTED_BRANDS:
            if brand.lower() in response_lower:
                return brand
                
        if "no preference" in response_lower or "geen" in response_lower:
            return "any"
            
        return None

    def parse_technology_response(self, response: str, category: str) -> Optional[str]:
        """Parse technology response based on category."""
        response_lower = response.lower()
        technologies = self.TECHNOLOGY_OPTIONS.get(category, [])
        
        for tech in technologies:
            if tech.lower() in response_lower:
                return tech
                
        if "no preference" in response_lower or "geen" in response_lower:
            return "any"
            
        return None
