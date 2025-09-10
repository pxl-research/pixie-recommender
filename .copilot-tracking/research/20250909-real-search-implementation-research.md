# Real Search Implementation Research Report

**Date**: 9 September 2025  
**Branch**: v0.3_pixie_mock_real_flow  
**Task**: Replace mock_search with real search implementation - PostgreSQL migration path

## Executive Summary

This research analyzes the transition from mock search functionality to real search implementation with **PostgreSQL as the target production database**. The goal is to replace the deterministic `MockSearchEngine` with a realistic search system using an intermediate JSON-based approach that establishes the foundation for seamless PostgreSQL migration. This strategy enables rapid development while building the proper database abstraction layer for production scalability.

## Current MockSearchEngine Analysis

### Current Implementation Review

The existing `MockSearchEngine` in `pixie/core/mock_search.py` provides:

**Key Characteristics**:
- **Deterministic Results**: Predictable output based on input attributes
- **Size-based Logic**: Returns 152 items for no attributes, 1-5 for specific attributes  
- **Special Rules**: Empty results for "minder dan 50€" budget
- **Simple Data Structure**: `{"id": int, "name": str, "price": int}`
- **Hash-based Selection**: Uses attribute hash to determine result count

**Current Usage Patterns**:
```python
def search(self, sql: str, attributes: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Returns many items when attributes is None (152 items)
    # Returns empty for specific budget constraint
    # Returns 1-5 items based on attribute hash
```

**Integration Points**:
- Used in `ConversationLoopManager` as `search_fn` parameter
- Called with SQL string and attributes dictionary
- Expected to return list of product dictionaries

## Real Search Implementation Strategy

### Database Strategy: PostgreSQL Migration Path

**Target Architecture**: PostgreSQL production database with intermediate JSON phase

**Phase 1: JSON Foundation (Current Implementation)**:
- **PostgreSQL Schema Design**: Design JSON structure to mirror future PostgreSQL tables
- **Repository Pattern**: Implement abstract repository interface for database operations  
- **Query Abstraction**: Build query layer that translates to both JSON filtering and SQL
- **Migration Ready**: JSON structure directly maps to PostgreSQL schema

**Phase 2: PostgreSQL Migration (Future)**:
- **Database Schema**: Convert JSON structure to PostgreSQL tables
- **Repository Implementation**: Swap JSON repository for PostgreSQL repository
- **Query Translation**: Convert abstract queries to actual SQL
- **Zero Downtime**: Same API, different backend

**Rationale for JSON-first Approach**:
- **Rapid Development**: No PostgreSQL setup needed initially
- **Schema Validation**: Test database design with real data
- **Migration Foundation**: Establish proper abstraction layers
- **Team Productivity**: Developers can work without database dependencies

### PostgreSQL-Ready Data Structure

**JSON Schema (PostgreSQL Table Design)**:
```json
{
  "printers": [
    {
      "id": 1,
      "name": "Brother HL-L2350DW",
      "brand": "Brother", 
      "technology": "laser",
      "price_cents": 12999,
      "currency": "EUR",
      "description": "Compacte zwart-wit laserprinter met WiFi",
      "has_wifi": true,
      "has_duplex": true,
      "has_color": false,
      "is_multifunction": false,
      "print_speed_ppm": 30,
      "resolution_dpi": "2400x600",
      "max_paper_size": "A4",
      "availability_status": "in_stock",
      "stock_level": 25,
      "created_at": "2025-09-09T10:00:00Z",
      "updated_at": "2025-09-09T10:00:00Z"
    }
  ]
}
```

**Future PostgreSQL Schema Mapping**:
```sql
CREATE TABLE printers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    technology VARCHAR(50) NOT NULL,
    price_cents INTEGER NOT NULL,
    currency CHAR(3) DEFAULT 'EUR',
    description TEXT,
    has_wifi BOOLEAN DEFAULT false,
    has_duplex BOOLEAN DEFAULT false, 
    has_color BOOLEAN DEFAULT false,
    is_multifunction BOOLEAN DEFAULT false,
    print_speed_ppm INTEGER,
    resolution_dpi VARCHAR(20),
    max_paper_size VARCHAR(10),
    availability_status VARCHAR(20) DEFAULT 'in_stock',
    stock_level INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_printers_brand ON printers(brand);
CREATE INDEX idx_printers_technology ON printers(technology);  
CREATE INDEX idx_printers_price ON printers(price_cents);
CREATE INDEX idx_printers_features ON printers(has_wifi, has_duplex, has_color);
```
```

**Sample Dataset Requirements**:
- **Size**: 20-50 printer entries for realistic variety
- **Brands**: Brother, HP, Canon, Epson, Kyocera
- **Technologies**: laser, inkjet, thermal inkjet
- **Price Range**: €49 - €599 to test various budget scenarios
- **Features**: WiFi, duplex, color, compact, multifunction

### Search Implementation Architecture

**New SearchEngine Class Design**:
```python
class RealSearchEngine:
    def __init__(self, data_file_path: str):
        self.data = self._load_data(data_file_path)
    
    def search(self, sql: str, attributes: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Parse attributes to create filters
        # Apply filters to dataset
        # Return matching results
```

**Backward Compatibility Requirements**:
- Must return same data structure as MockSearchEngine
- Must handle same attribute patterns (budget, brand, technology)
- Must maintain deterministic behavior for testing
- Must support empty results for budget constraints

### SQL Integration Strategy

**Current SQL Usage**: The `MockSQLLLM` always returns `"SELECT * FROM printers;"`

**Enhanced SQL Processing Options**:
1. **Simple Attribute Mapping**: Ignore SQL, use attributes directly
2. **Basic SQL Parsing**: Extract WHERE clauses for filtering
3. **Full SQL Engine**: Use sqlite3 in-memory with JSON data

**Recommended Approach**: Simple attribute mapping for initial implementation, with option to enhance later.

## Implementation Specifications

### File Structure Recommendations

```
pixie/core/
├── data/
│   ├── printers.json          # Static printer database
│   └── schema.json           # JSON schema for validation
├── search_engine.py          # New real search implementation
├── mock_search.py           # Keep for testing/comparison
└── ...
```

### Repository Pattern Architecture

**Abstract Repository Interface (PostgreSQL-Ready)**:
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class PrinterRepository(ABC):
    @abstractmethod
    def find_all(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod 
    def find_by_filters(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def find_by_price_range(self, min_cents: int, max_cents: int) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def find_by_brand(self, brand: str) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def find_by_technology(self, technology: str) -> List[Dict[str, Any]]:
        pass

class JsonPrinterRepository(PrinterRepository):
    # JSON file implementation
    
class PostgresPrinterRepository(PrinterRepository):  
    # Future PostgreSQL implementation
```

**Search Engine with Repository Pattern**:
```python
class RealSearchEngine:
    def __init__(self, repository: PrinterRepository):
        self.repository = repository
        
    def search(self, sql: str, attributes: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Translate attributes to repository calls
        # This layer remains the same for JSON → PostgreSQL migration
```

### Attribute Filtering Logic

**Budget Filtering**:
```python
def _filter_by_budget(self, items: List[Dict], budget: str) -> List[Dict]:
    if "minder dan 50" in budget.lower():
        return [item for item in items if item["price"] < 50]
    elif "minder dan 150" in budget.lower():
        return [item for item in items if item["price"] < 150]
    # Add more budget ranges
```

**Brand Filtering**:
```python
def _filter_by_brand(self, items: List[Dict], brand: str) -> List[Dict]:
    return [item for item in items if item["brand"].lower() == brand.lower()]
```

**Technology Filtering**:
```python
def _filter_by_technology(self, items: List[Dict], technology: str) -> List[Dict]:
    return [item for item in items if item["technology"].lower() == technology.lower()]
```

### Test Compatibility Strategy

**Maintaining Test Behavior**:
- Create dataset that produces expected test results
- Ensure specific attribute combinations return predictable counts
- Preserve special cases like "minder dan 50€" → empty results

**Test Data Design**:
- Include printers under €50 and ensure proper filtering
- Include variety of brands and technologies for selection testing
- Ensure sufficient variety for "many results" scenarios

## Integration Plan

### Phase 1: Core Implementation

**Step 1: Create Printer Dataset**
- Design JSON schema for printer data
- Create comprehensive printer dataset (20-50 items)
- Include variety across brands, technologies, and price ranges

**Step 2: Implement RealSearchEngine**
- Create new search_engine.py with RealSearchEngine class
- Implement attribute-based filtering logic
- Maintain MockSearchEngine interface compatibility

**Step 3: Integration Points**
- Update ConversationLoopManager to optionally use RealSearchEngine
- Create factory function for search engine selection
- Ensure backward compatibility with existing tests

### Phase 2: Enhanced Search Features

**Step 1: Advanced Filtering**
- Support price range queries
- Add feature-based filtering (WiFi, duplex, color)
- Implement sorting options (price, rating, popularity)

**Step 2: Search Result Enhancement**
- Rich product descriptions
- Specification details in results
- Availability and stock information

### Phase 3: SQL Processing (Optional)

**Step 1: Basic SQL Parsing**
- Extract WHERE clauses from SQL
- Map SQL conditions to attribute filters
- Support ORDER BY for sorting

**Step 2: Full SQL Engine**
- Use sqlite3 in-memory database
- Load JSON data into SQLite tables
- Process actual SQL queries

## Technical Implementation Details

### JSON Data File Location

**Recommended Path**: `pixie/core/data/printers.json`

**Rationale**:
- Within core module for easy access
- Separate data directory for organization
- Version controlled with code
- Easy to modify for testing

### Error Handling Strategy

**File Loading Errors**:
```python
def _load_data(self, file_path: str) -> List[Dict]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('printers', [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # Log error and fall back to empty dataset or mock data
        logger.warning(f"Failed to load printer data: {e}")
        return []
```

**Search Errors**:
- Graceful handling of malformed attributes
- Default empty results for parsing failures
- Logging for debugging and monitoring

### Performance Considerations

**In-Memory Loading**:
- Load JSON once at initialization
- Cache filtered results if needed
- Consider lazy loading for larger datasets

**Filtering Efficiency**:
- Use list comprehensions for simple filters
- Consider pandas for complex filtering if dataset grows
- Profile performance with realistic data sizes

### Configuration Management

**Environment-based Configuration**:
```python
class RealSearchEngine:
    def __init__(self, data_file_path: str = None):
        if data_file_path is None:
            data_file_path = os.getenv(
                'PIXIE_PRINTER_DATA',
                'pixie/core/data/printers.json'
            )
```

**Factory Pattern for Engine Selection**:
```python
def create_search_engine(engine_type: str = "real") -> SearchEngineProtocol:
    if engine_type == "mock":
        return MockSearchEngine()
    elif engine_type == "real":
        return RealSearchEngine()
    else:
        raise ValueError(f"Unknown engine type: {engine_type}")
```

## Testing Strategy

### Test Data Management

**Separate Test Dataset**:
- Create `test_printers.json` with controlled data for testing
- Ensure specific attribute combinations produce expected results
- Maintain compatibility with existing test assertions

**Test Environment Configuration**:
```python
@pytest.fixture
def real_search_engine():
    test_data_path = "tests/data/test_printers.json"
    return RealSearchEngine(test_data_path)
```

### Compatibility Testing

**Existing Test Preservation**:
- Run all existing tests with RealSearchEngine
- Verify same behavior as MockSearchEngine for critical test cases
- Add new tests for enhanced functionality

**Migration Testing**:
- Side-by-side comparison of mock vs real results
- Performance benchmarking
- Edge case validation

## Sample Dataset Design

### Core Printer Categories

**Budget Printers (€49-€99)**:
- Basic inkjet and laser options
- Include some under €50 for budget constraint testing
- Mix of brands: Brother, Canon, HP

**Mid-range Printers (€100-€299)**:
- Feature-rich options with WiFi, duplex
- Color and monochrome options
- Popular brands: Brother, HP, Epson

**Premium Printers (€300-€599)**:
- High-performance laser and professional inkjet
- Advanced features and specifications
- Professional brands: Kyocera, high-end Brother/HP

### Attribute Distribution

**Brands**: 40% Brother, 25% HP, 15% Canon, 10% Epson, 10% Kyocera
**Technology**: 60% laser, 30% inkjet, 10% thermal inkjet
**Features**: 70% WiFi, 40% duplex, 30% color, 20% multifunction

This distribution ensures realistic variety while maintaining predictable test behavior.

## PostgreSQL Migration Strategy

### Migration Phases

**Phase 1: JSON Foundation (Current Sprint)**
- Implement repository pattern with JSON backend
- Design PostgreSQL-compatible schema in JSON format  
- Build query abstraction layer
- Establish testing patterns for database operations

**Phase 2: PostgreSQL Preparation (Next Sprint)**
- Add PostgreSQL dependencies (psycopg2, SQLAlchemy/asyncpg)
- Implement PostgresPrinterRepository
- Create database migration scripts
- Add connection pooling and configuration

**Phase 3: PostgreSQL Migration (Future Sprint)**
- Deploy PostgreSQL database infrastructure
- Run data migration from JSON to PostgreSQL
- Switch repository implementation via configuration
- Monitor performance and optimize queries

**Phase 4: PostgreSQL Optimization (Ongoing)**
- Add full-text search capabilities
- Implement advanced indexing strategies
- Add database monitoring and analytics
- Scale database for production load

### Repository Interface Benefits

**Zero-Downtime Migration**:
- Same `PrinterRepository` interface for JSON and PostgreSQL
- Configuration-driven backend selection
- A/B testing capabilities during migration
- Rollback safety if issues occur

**Development Flexibility**:
- Developers work with JSON locally, PostgreSQL in production
- Test suite runs against both backends for compatibility
- Feature development independent of database choice
- Easy integration testing with different data sources

## Migration Risk Assessment

### Minimal Risk Factors

- **Interface Abstraction**: Repository pattern enables seamless backend swapping
- **Schema Compatibility**: JSON structure directly maps to PostgreSQL tables
- **Query Translation**: Abstract query methods work with both backends
- **Proven Pattern**: Repository pattern is industry standard for database abstraction

### Considerations

- **Performance**: JSON file loading adds minimal overhead
- **Data Management**: Static data requires manual updates but provides full control
- **Complexity**: Attribute parsing adds some complexity but remains manageable

### Mitigation Strategies

- **Feature Flags**: Environment variable to switch between mock and real engines
- **Comprehensive Testing**: Validate both engines produce expected results
- **Gradual Rollout**: Start with development environment, then production

## Success Criteria

### Functional Requirements

1. **Backward Compatibility**: All existing tests pass with RealSearchEngine
2. **Realistic Results**: Search returns actual printer data with proper attributes
3. **Filter Accuracy**: Budget, brand, and technology filters work correctly
4. **Performance**: Search response time remains under 100ms
5. **Error Handling**: Graceful degradation when data file unavailable

### Quality Requirements

1. **Code Quality**: Clean, well-documented implementation
2. **Test Coverage**: >90% test coverage for new search functionality
3. **Data Quality**: Comprehensive, realistic printer dataset
4. **Documentation**: Clear integration and usage documentation

The real search implementation represents a significant step toward production-ready functionality while maintaining the simplicity and testability of the current mock system.
