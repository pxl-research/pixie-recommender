# Step 2: PostgreSQL Database Models Implementeren

## Objective
Implementeer Python database models voor alle producttypen en ondersteunende tabellen met SQLAlchemy ORM.

## Prerequisites
- Previous step completed: Database schema design
- Required tools/dependencies: SQLAlchemy, psycopg2-binary

## Actions
1. **Dependencies toevoegen aan pyproject.toml**
   - Voeg SQLAlchemy en PostgreSQL driver toe
   - Update requirements voor database connectivity
   - Zorg voor development en production compatibiliteit

2. **Database models directory structure aanmaken**
   - Maak `pixie/core/database/` directory
   - Maak `pixie/core/database/models/` subdirectory
   - Maak `__init__.py` bestanden voor Python modules

3. **Base model en configuration implementeren**
   - Creëer `base.py` met SQLAlchemy declarative base
   - Implementeer `database.py` voor connection management
   - Setup database session factory en configuration

4. **Product models implementeren**
   - Implementeer `printer.py` model volgens schema
   - Implementeer `laptop.py` model volgens schema
   - Implementeer `computer.py` model volgens schema
   - Implementeer `smartphone.py` model volgens schema

5. **Supporting models implementeren**
   - Implementeer `category.py` voor categorieën metadata
   - Implementeer `attribute.py` voor attributen configuratie
   - Zorg voor relationships tussen models

6. **Model validation en testing**
   - Voeg Pydantic integration toe voor data validation
   - Test model creation en relationships
   - Valideer dat alle JSON fields mapped zijn

## Success Criteria
- Alle database models zijn geïmplementeerd
- Models volgen SQLAlchemy best practices
- Data validation werkt correct
- All current JSON fields zijn mapped naar database fields
- Model relationships zijn correct gedefinieerd

## Next Step
Continue to: `03-database-connection.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
