"""Domain validation for product discovery queries."""
from typing import List, Optional


class DomainValidator:
    """Validates if questions are within supported product domains."""

    SUPPORTED_DOMAINS = [
        "printers",
        "laptops", 
        "smartphones",
        "tablets"
    ]

    PRODUCT_KEYWORDS = {
        "printer": ["printer", "printing", "print", "inkjet", "laser", "multifunction"],
        "laptop": ["laptop", "notebook", "computer", "pc", "macbook", "gaming laptop"],
        "smartphone": ["phone", "smartphone", "mobile", "iphone", "android", "cell phone"],
        "tablet": ["tablet", "ipad", "android tablet", "surface", "e-reader"]
    }

    OUT_OF_SCOPE_PATTERNS = [
        # Personal/living things
        ["mom", "mother", "dad", "father", "family", "person", "people"],
        # Services
        ["service", "repair", "support", "help desk", "consultation"],
        # Non-product items
        ["food", "restaurant", "hotel", "car", "house", "clothing", "shoes"],
        # Abstract concepts
        ["advice", "information", "news", "weather", "directions"]
    ]

    def is_product_related(self, question: str) -> bool:
        """Check if question is related to supported product categories."""
        question_lower = question.lower()
        
        # Check for specific product keywords
        for category, keywords in self.PRODUCT_KEYWORDS.items():
            if any(keyword in question_lower for keyword in keywords):
                return True
                
        # Check for generic shopping terms that could be product-related
        shopping_terms = [
            "looking for", "want to buy", "need", "purchase", "shop",
            "recommendations", "compare", "price", "cost", "budget"
        ]
        
        if any(term in question_lower for term in shopping_terms):
            # Only consider it product-related if it's not clearly out of scope
            return not self._is_clearly_out_of_scope(question_lower)
            
        return False

    def _is_clearly_out_of_scope(self, question_lower: str) -> bool:
        """Check if question is clearly outside supported domains."""
        for pattern_group in self.OUT_OF_SCOPE_PATTERNS:
            if any(pattern in question_lower for pattern in pattern_group):
                return True
        return False

    def detect_product_category(self, question: str) -> Optional[str]:
        """Detect which product category the question is about."""
        question_lower = question.lower()
        
        # Check each category for keyword matches
        for category, keywords in self.PRODUCT_KEYWORDS.items():
            if any(keyword in question_lower for keyword in keywords):
                return category
                
        # If we detected it's product-related but can't determine category,
        # we might need to ask for clarification
        if self.is_product_related(question):
            return "unknown_product"
            
        return None

    def generate_rejection_message(self) -> str:
        """Generate friendly rejection message with supported domains."""
        domains_str = ", ".join(self.SUPPORTED_DOMAINS[:-1]) + f", and {self.SUPPORTED_DOMAINS[-1]}"
        return f"Sorry, I can't help with that. I only have information about {domains_str}."

    def generate_category_clarification_message(self) -> str:
        """Generate message asking for product category clarification."""
        domains_str = ", ".join(self.SUPPORTED_DOMAINS[:-1]) + f", or {self.SUPPORTED_DOMAINS[-1]}"
        return f"I can help you find products! Are you looking for {domains_str}?"

    def get_supported_domains(self) -> List[str]:
        """Get list of supported product domains."""
        return self.SUPPORTED_DOMAINS.copy()
