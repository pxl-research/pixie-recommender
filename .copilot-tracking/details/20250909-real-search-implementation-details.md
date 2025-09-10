<!-- markdownlint-disable-file -->
# Task Details: Real Search Implementation (PostgreSQL Migration Path)

## Research Reference

**Source Research**: #file:../research/20250909-real-search-implementation-research.md

## Phase 1: PostgreSQL-Ready Foundation

### Task 1.1: Design PostgreSQL schema and JSON structure

Create PostgreSQL-compatible data schema implemented initially as JSON structure for rapid development.

- **Files**:
  - pixie/core/data/schema.sql - PostgreSQL table definitions and indexes
  - pixie/core/data/schema.json - JSON schema validation rules
  - pixie/core/data/printers.json - PostgreSQL-structured data in JSON format
- **Success**:
  - JSON structure directly maps to PostgreSQL tables
  - Schema supports efficient filtering and indexing strategies
  - Price stored in cents for database precision
  - Boolean flags for features (wifi, duplex, color, multifunction)
  - Timestamps ready for PostgreSQL datetime handling
- **Research References**:
  - #file:../research/20250909-real-search-implementation-research.md (Lines 64-115) - PostgreSQL-ready data structure and schema mapping
  - #file:../../pixie/core/mock_search.py (Lines 15-50) - Current return format requirements
- **Dependencies**:
  - Analysis of current MockSearchEngine output format

### Task 1.2: Create abstract PrinterRepository interface

Implement abstract repository interface that supports both JSON and future PostgreSQL backends.

- **Files**:
  - pixie/core/repositories/printer_repository.py - Abstract PrinterRepository base class
  - pixie/core/repositories/__init__.py - Repository module initialization
- **Success**:
  - Abstract base class defines all required query methods
  - Interface supports filtering by budget, brand, technology, features
  - Methods designed for both JSON filtering and SQL translation
  - Type hints ensure consistent data contracts
  - Async-ready method signatures for future PostgreSQL integration
- **Research References**:
  - #file:../research/20250909-real-search-implementation-research.md (Lines 179-208) - Repository pattern architecture
  - #file:../research/20250909-real-search-implementation-research.md (Lines 425-463) - PostgreSQL migration strategy
- **Dependencies**:
  - Task 1.1 completion (schema defined)

### Task 1.3: Implement JsonPrinterRepository

Create JSON-file backend implementation of PrinterRepository interface.

- **Files**:
  - pixie/core/repositories/json_printer_repository.py - JSON file implementation
- **Success**:
  - Implements all PrinterRepository abstract methods
  - Loads and validates JSON data at initialization
  - Efficient in-memory filtering using list comprehensions
  - Handles price range queries with cent-based calculations
  - Graceful error handling for missing or corrupted files
- **Research References**:
  - #file:../research/20250909-real-search-implementation-research.md (Lines 304-330) - JSON data file location and loading
  - #file:../research/20250909-real-search-implementation-research.md (Lines 238-275) - Attribute filtering logic
- **Dependencies**:
  - Task 1.2 completion (abstract interface defined)

### Task 1.4: Create comprehensive printer dataset

Design realistic printer database with PostgreSQL production data structure.

- **Files**:
  - pixie/core/data/printers.json - Production-ready printer dataset
  - scripts/generate_test_data.py - Script for creating controlled test datasets
- **Success**:
  - 30-50 printer entries with realistic specifications
  - Price range €49-€599 covering all budget test scenarios
  - Brand distribution: 40% Brother, 25% HP, 15% Canon, 10% Epson, 10% Kyocera
  - Technology mix: 60% laser, 30% inkjet, 10% thermal inkjet
  - Feature distribution: 70% WiFi, 40% duplex, 30% color, 20% multifunction
  - Dutch product names and descriptions
- **Research References**:
  - #file:../research/20250909-real-search-implementation-research.md (Lines 388-405) - Sample dataset design
  - #file:../../tests/test_conversation_loop.py (Lines 80-120) - Expected test result patterns
- **Dependencies**:
  - Task 1.3 completion (JsonPrinterRepository ready to load data)

## Phase 2: Repository-Based Search Engine

### Task 2.1: Implement RealSearchEngine with repository pattern

Create search engine that uses repository abstraction for database-agnostic operations.

- **Files**:
  - pixie/core/search_engine.py - RealSearchEngine implementation
- **Success**:
  - Constructor accepts PrinterRepository interface
  - Maintains MockSearchEngine API compatibility
  - Translates search attributes to repository method calls
  - Returns same data structure as MockSearchEngine
  - Supports both JSON and future PostgreSQL backends transparently
- **Research References**:
  - #file:../research/20250909-real-search-implementation-research.md (Lines 209-237) - Search engine with repository pattern
  - #file:../../pixie/core/mock_search.py (Lines 8-55) - Current interface requirements
- **Dependencies**:
  - Phase 1 completion (repository infrastructure ready)

### Task 2.2: Create query abstraction layer

Build query translation layer that converts search attributes to repository calls.

- **Files**:
  - pixie/core/query/query_builder.py - Query abstraction and translation
  - pixie/core/query/__init__.py - Query module initialization
- **Success**:
  - Parses budget expressions ("minder dan 150€") into price ranges
  - Handles brand and technology filtering with normalization
  - Supports feature-based queries (WiFi, duplex, color)
  - Translates to repository method calls (JSON now, SQL later)
  - Maintains special case behaviors (budget constraints → empty results)
- **Research References**:
  - #file:../research/20250909-real-search-implementation-research.md (Lines 238-275) - Attribute filtering logic
  - #file:../../pixie/core/mock_search.py (Lines 31-50) - Current filtering behavior patterns
- **Dependencies**:
  - Task 2.1 completion (search engine architecture ready)

### Task 2.3: Add filtering and validation logic

Implement comprehensive data validation and error handling for production readiness.

- **Files**:
  - pixie/core/validation/printer_validator.py - Data validation logic
  - pixie/core/search_engine.py - Add validation to search engine
- **Success**:
  - Validates loaded printer data against schema requirements
  - Handles malformed search attributes gracefully
  - Comprehensive logging for debugging and monitoring
  - Performance optimization for large datasets
  - Fallback behaviors for edge cases
- **Research References**:
  - #file:../research/20250909-real-search-implementation-research.md (Lines 304-330) - Error handling strategy
  - #file:../../pixie/core/logging.py (Lines 1-50) - Existing logging patterns
- **Dependencies**:
  - Task 2.2 completion (query layer implemented)

## Phase 3: Integration and Migration Preparation

### Task 3.1: Create repository factory for backend selection

Implement factory pattern for runtime selection between JSON and PostgreSQL backends.

- **Files**:
  - pixie/core/repositories/repository_factory.py - Repository factory implementation
  - pixie/core/config/database_config.py - Database configuration management
- **Success**:
  - Environment variable controls backend selection (JSON/PostgreSQL)
  - Clean interface for switching repository implementations
  - Configuration validation and error handling
  - Default to JSON in development, PostgreSQL in production
  - Support for A/B testing during migration
- **Research References**:
  - #file:../research/20250909-real-search-implementation-research.md (Lines 456-463) - Development flexibility requirements
  - #file:../research/20250909-real-search-implementation-research.md (Lines 450-455) - Zero-downtime migration strategy
- **Dependencies**:
  - Task 2.3 completion (search engine fully implemented)

### Task 3.2: Update ConversationLoopManager integration

Modify conversation loop to use repository-based search engine.

- **Files**:
  - pixie/core/conversation_loop.py - Update to use repository factory
  - pixie/core/mock_llm_set.py - Update LLM set creation
- **Success**:
  - ConversationLoopManager uses repository factory for search engine
  - Existing tests continue to pass with JSON backend
  - Production configuration defaults to appropriate backend
  - Clean separation of concerns maintained
  - No breaking changes to existing API
- **Research References**:
  - #file:../research/20250909-real-search-implementation-research.md (Lines 33-40) - Current integration points
  - #file:../../pixie/core/conversation_loop.py (Lines 15-30) - Current search_fn parameter usage
- **Dependencies**:
  - Task 3.1 completion (repository factory available)

### Task 3.3: Prepare PostgreSQL migration foundation

Set up foundation for future PostgreSQL implementation without breaking current functionality.

- **Files**:
  - pixie/core/repositories/postgres_printer_repository.py - PostgreSQL repository stub
  - requirements/postgres.txt - PostgreSQL dependency specifications
  - migrations/001_create_printers_table.sql - Database migration script
- **Success**:
  - PostgresPrinterRepository interface implementation (stub methods)
  - Migration scripts ready for PostgreSQL deployment
  - Dependency specifications for asyncpg/psycopg2
  - Connection pooling and configuration preparation
  - Documentation for PostgreSQL migration process
- **Research References**:
  - #file:../research/20250909-real-search-implementation-research.md (Lines 432-437) - PostgreSQL preparation phase
  - #file:../research/20250909-real-search-implementation-research.md (Lines 92-115) - PostgreSQL schema definition
- **Dependencies**:
  - Task 3.2 completion (integration points updated)

### Task 3.4: Create comprehensive test suite

Develop test suite that validates both JSON and future PostgreSQL implementations.

- **Files**:
  - tests/test_repositories.py - Repository interface testing
  - tests/test_real_search_engine.py - Search engine testing
  - tests/data/test_printers.json - Controlled test dataset
  - tests/integration/test_migration_compatibility.py - Migration testing
- **Success**:
  - Abstract repository tests that work with both JSON and PostgreSQL
  - Test data produces predictable, verifiable results
  - Performance benchmarks within acceptable limits
  - Migration compatibility validation
  - Mock and real engine behavioral comparison
- **Research References**:
  - #file:../research/20250909-real-search-implementation-research.md (Lines 366-387) - Testing strategy
  - #file:../../tests/test_conversation_loop.py (Lines 80-164) - Existing search engine test patterns
- **Dependencies**:
  - Task 3.3 completion (PostgreSQL foundation ready)

## Phase 4: Validation and Documentation

### Task 4.1: Run compatibility tests with existing functionality

Execute comprehensive testing to ensure repository pattern works seamlessly.

- **Files**:
  - Run existing test suite with JsonPrinterRepository
  - Document compatibility results and performance metrics
- **Success**:
  - All tests in test_conversation_loop.py pass with repository-based engine
  - All tests in test_api_routes.py continue to work
  - No regression in existing functionality
  - Performance meets sub-100ms requirements
  - Memory usage reasonable for JSON dataset size
- **Research References**:
  - #file:../research/20250909-real-search-implementation-research.md (Lines 466-480) - Minimal risk factors
  - #file:../../tests/test_api_routes.py (Lines 1-105) - Existing API integration tests
- **Dependencies**:
  - Task 3.4 completion (comprehensive test suite ready)

### Task 4.2: Performance testing and optimization

Validate search performance and prepare for PostgreSQL scale requirements.

- **Files**:
  - Performance test scripts in tests/performance/
  - Optimization of JsonPrinterRepository if needed
- **Success**:
  - JSON backend performance baseline established
  - Search response time under 100ms for typical queries
  - Memory usage analysis for production dataset sizes
  - Performance comparison between mock and repository implementations
  - PostgreSQL performance projections and optimization planning
- **Research References**:
  - #file:../research/20250909-real-search-implementation-research.md (Lines 331-350) - Performance considerations
- **Dependencies**:
  - Task 4.1 completion (functionality validated)

### Task 4.3: Update documentation and PostgreSQL migration guide

Create comprehensive documentation for repository pattern and migration strategy.

- **Files**:
  - docs/repository-pattern.md - Repository architecture documentation
  - docs/postgresql-migration.md - Migration guide and timeline
  - README.md - Update with new search capabilities
  - pixie/core/repositories/README.md - Repository usage examples
- **Success**:
  - Clear documentation of repository pattern benefits
  - Step-by-step PostgreSQL migration guide
  - Usage examples for different filtering scenarios
  - API documentation updated for new architecture
  - Developer onboarding guide for repository pattern
- **Research References**:
  - #file:../research/20250909-real-search-implementation-research.md (Lines 425-463) - PostgreSQL migration strategy
  - #file:../../README.md (Lines 1-100) - Current documentation patterns
- **Dependencies**:
  - Task 4.2 completion (performance validated)

## Dependencies

- Python built-in json and abc modules
- Existing pixie-core test framework
- Current ConversationLoopManager architecture
- Future: PostgreSQL database and python drivers

## Success Criteria

- Repository pattern enables seamless JSON → PostgreSQL migration
- PostgreSQL-compatible schema validated with JSON implementation
- Zero-downtime migration path established and documented
- All existing functionality preserved with new architecture
- Performance meets production requirements for both JSON and PostgreSQL
- Clear migration timeline and process documented
