"""Fake product catalog for mocking product discovery flows."""
from typing import List, Optional, Dict, Any
from pixie.core.contracts import Product


class FakeProductCatalog:
    """Mock product catalog with realistic sample data and filtering capabilities."""

    def __init__(self):
        self._products = self._create_sample_products()
        self.result_threshold = 10  # Configurable threshold for "too many results"

    def _create_sample_products(self) -> List[Product]:
        """Create comprehensive sample product data."""
        return [
            # Brother Printers
            Product(
                id="brother-xc-2570",
                name="Brother XC 2570",
                price=199.0,
                brand="Brother",
                category="printer",
                technology="Laser",
                description="Reliable laser printer for small offices"
            ),
            Product(
                id="brother-xt-3560", 
                name="Brother XT 3560",
                price=159.0,
                brand="Brother",
                category="printer",
                technology="Laser",
                description="Compact laser printer with fast printing"
            ),
            Product(
                id="brother-zx-1570",
                name="Brother ZX 1570", 
                price=69.0,
                brand="Brother",
                category="printer", 
                technology="Laser",
                description="Budget-friendly laser printer"
            ),
            Product(
                id="brother-inkjet-250",
                name="Brother Inkjet 250",
                price=89.0,
                brand="Brother",
                category="printer",
                technology="Inkjet", 
                description="Color inkjet printer for home use"
            ),
            
            # HP Printers
            Product(
                id="hp-inkjet-234",
                name="HP Inkjet 234",
                price=79.0,
                brand="HP",
                category="printer",
                technology="Inkjet",
                description="Affordable inkjet printer with wireless"
            ),
            Product(
                id="hp-inkjet-1234", 
                name="HP Inkjet 1234",
                price=109.0,
                brand="HP",
                category="printer",
                technology="Inkjet",
                description="All-in-one inkjet printer with scanning"
            ),
            Product(
                id="hp-laserjet-400",
                name="HP LaserJet 400",
                price=289.0,
                brand="HP",
                category="printer",
                technology="Laser",
                description="Professional laser printer for office use"
            ),
            Product(
                id="hp-envy-6000",
                name="HP Envy 6000",
                price=149.0,
                brand="HP", 
                category="printer",
                technology="Thermal inkjet",
                description="Premium thermal inkjet with photo printing"
            ),
            
            # Kyocera Printers
            Product(
                id="kyocera-t70",
                name="Kyocera T70",
                price=99.0,
                brand="Kyocera", 
                category="printer",
                technology="Laser",
                description="Eco-friendly laser printer"
            ),
            Product(
                id="kyocera-ecosys-p2040",
                name="Kyocera ECOSYS P2040",
                price=179.0,
                brand="Kyocera",
                category="printer",
                technology="Laser", 
                description="Energy-efficient monochrome laser printer"
            ),
            
            # Canon Printers
            Product(
                id="canon-pixma-ts3300",
                name="Canon PIXMA TS3300",
                price=59.0,
                brand="Canon",
                category="printer",
                technology="Inkjet",
                description="Compact wireless inkjet printer"
            ),
            Product(
                id="canon-imageclass-mf240",
                name="Canon imageCLASS MF240", 
                price=199.0,
                brand="Canon",
                category="printer",
                technology="Laser",
                description="Multifunction laser printer with fax"
            ),
            Product(
                id="canon-pixma-pro-100",
                name="Canon PIXMA PRO-100",
                price=349.0,
                brand="Canon",
                category="printer",
                technology="Inkjet",
                description="Professional photo inkjet printer"
            ),
            
            # Epson Printers  
            Product(
                id="epson-workforce-3600",
                name="Epson WorkForce 3600",
                price=129.0,
                brand="Epson",
                category="printer",
                technology="Inkjet", 
                description="Business inkjet printer with duplex"
            ),
            Product(
                id="epson-ecotank-2800",
                name="Epson EcoTank 2800",
                price=229.0,
                brand="Epson",
                category="printer",
                technology="Inkjet",
                description="Cartridge-free inkjet with refillable tanks"
            ),
            
            # Additional printers for threshold testing
            Product(
                id="brother-mfc-l2750",
                name="Brother MFC-L2750",
                price=249.0,
                brand="Brother",
                category="printer",
                technology="Laser",
                description="Multifunction laser printer with ADF"
            ),
            Product(
                id="hp-officejet-pro-9000",
                name="HP OfficeJet Pro 9000",
                price=319.0,
                brand="HP",
                category="printer", 
                technology="Inkjet",
                description="High-volume office inkjet printer"
            ),
            Product(
                id="canon-maxify-mb5400",
                name="Canon MAXIFY MB5400",
                price=279.0,
                brand="Canon",
                category="printer",
                technology="Inkjet",
                description="Small office inkjet with high capacity"
            ),
            Product(
                id="epson-workforce-pro-4700",
                name="Epson WorkForce Pro 4700",
                price=399.0,
                brand="Epson",
                category="printer",
                technology="Inkjet",
                description="Professional color inkjet for business"
            ),
            Product(
                id="kyocera-taskalfa-2553",
                name="Kyocera TASKalfa 2553",
                price=449.0,
                brand="Kyocera",
                category="printer",
                technology="Laser",
                description="Heavy-duty multifunctional laser system"
            ),
        ]

    def get_all_products(self) -> List[Product]:
        """Get all products in the catalog."""
        return self._products.copy()

    def search_products(self, filters: Optional[Dict[str, Any]] = None) -> List[Product]:
        """Search products with optional filters."""
        if filters is None:
            return self.get_all_products()

        results = self._products.copy()

        # Apply category filter
        if "category" in filters:
            category = filters["category"].lower()
            results = [p for p in results if p.category.lower() == category]

        # Apply budget filter
        if "budget" in filters:
            budget = filters["budget"]
            if isinstance(budget, dict) and "min" in budget and "max" in budget:
                min_price, max_price = budget["min"], budget["max"]
                results = [p for p in results if min_price <= p.price <= max_price]

        # Apply brand filter
        if "brand" in filters:
            brand = filters["brand"]
            if brand != "any":
                results = [p for p in results if p.brand.lower() == brand.lower()]

        # Apply technology filter
        if "technology" in filters:
            tech = filters["technology"]
            if tech != "any" and tech is not None:
                results = [p for p in results if p.technology and p.technology.lower() == tech.lower()]

        return results

    def filter_by_budget(self, products: List[Product], min_price: float = 0, max_price: float = float('inf')) -> List[Product]:
        """Filter products by price range."""
        return [p for p in products if min_price <= p.price <= max_price]

    def filter_by_brand(self, products: List[Product], brand: str) -> List[Product]:
        """Filter products by brand (case-insensitive)."""
        if brand.lower() == "any":
            return products
        return [p for p in products if p.brand.lower() == brand.lower()]

    def filter_by_technology(self, products: List[Product], technology: str) -> List[Product]:
        """Filter products by technology type."""
        if technology.lower() == "any":
            return products
        return [p for p in products if p.technology and p.technology.lower() == technology.lower()]

    def filter_by_category(self, products: List[Product], category: str) -> List[Product]:
        """Filter products by category."""
        return [p for p in products if p.category.lower() == category.lower()]

    def sort_products(self, products: List[Product], sort_by: str = "price") -> List[Product]:
        """Sort products by specified criteria."""
        if sort_by == "price":
            return sorted(products, key=lambda p: p.price)
        elif sort_by == "price_desc":
            return sorted(products, key=lambda p: p.price, reverse=True)
        elif sort_by == "name":
            return sorted(products, key=lambda p: p.name.lower())
        else:
            return products

    def sample_products(self, products: List[Product], count: int = 5) -> List[Product]:
        """Get a random sample of products."""
        import random
        if len(products) <= count:
            return products
        return random.sample(products, count)

    def get_top_products(self, products: List[Product], count: int = 5, sort_by: str = "price") -> List[Product]:
        """Get top N products sorted by specified criteria."""
        sorted_products = self.sort_products(products, sort_by)
        return sorted_products[:count]
