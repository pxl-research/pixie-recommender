# Step 1: Database Schema Ontwerp en Setup

## Objective
Ontwerp PostgreSQL database schema met afzonderlijke tabellen per producttype en ondersteunende tabellen voor attributen configuratie.

## Prerequisites
- Research rapport gelezen en begrepen
- JSON schema.json bestudeerd
- Current JSON data structure geanalyseerd

## Actions
1. **PostgreSQL schema SQL bestanden aanmaken**
   - Maak `pixie/core/database/schema/` directory
   - Creëer `01_categories.sql` voor categorieën metadata
   - Creëer `02_attributes.sql` voor attributen configuratie
   - Creëer `03_printers.sql` voor printers tabel
   - Creëer `04_laptops.sql` voor laptops tabel
   - Creëer `05_computers.sql` voor computers tabel
   - Creëer `06_smartphones.sql` voor smartphones tabel
   - Creëer `07_indexes.sql` voor prestatie indexes

2. **Database schema design volgens requirements**
   - Eenvoudige, begrijpbare tabel structuur
   - Afzonderlijke tabel per producttype voor prestaties
   - Flexibele attributen configuratie tabel
   - Categorieën metadata tabel voor dynamische detectie
   - Goede indexering voor snelle queries

3. **Schema validatie en documentatie**
   - Vergelijk schema met huidige JSON structure
   - Documenteer design keuzes
   - Valideer dat alle huidige data fields ondersteund worden
   - Zorg voor future-proof extensibility

## Success Criteria
- Alle SQL schema bestanden zijn aangemaakt
- Schema ondersteunt alle huidige producttypen en attributen
- Database design is eenvoudig en begrijpbaar
- Schema is geoptimaliseerd voor prestaties
- Documentatie is compleet en duidelijk

## Next Step
Continue to: `02-database-models.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
