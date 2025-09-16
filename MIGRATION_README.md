# Data Migration Guide

This guide explains how to migrate data from JSON files to PostgreSQL database for Pixie-Core.

## Prerequisites

1. **PostgreSQL Database**: Ensure PostgreSQL is running and accessible
2. **Database Schema**: Run the database migrations to create tables:

   ```bash
   # Apply database schema (from previous steps)
   psql -d pixie_db -f pixie/core/database/schema/01_categories.sql
   psql -d pixie_db -f pixie/core/database/schema/02_attributes.sql
   psql -d pixie_db -f pixie/core/database/schema/03_printers.sql
   psql -d pixie_db -f pixie/core/database/schema/04_laptops.sql
   psql -d pixie_db -f pixie/core/database/schema/05_computers.sql
   psql -d pixie_db -f pixie/core/database/schema/06_smartphones.sql
   psql -d pixie_db -f pixie/core/database/schema/07_indexes.sql
   ```

3. **Environment Variables**: Set database connection:

   ```bash
   export DATABASE_URL="postgresql://pixie_user:pixie_password@localhost:5432/pixie_db"
   ```

## Running the Migration

### Option 1: Using the Migration Script

```bash
cd /Users/drphil/Documents/Werk/pixie-core

# Run the migration script
uv run python scripts/migrate_data.py
```

### Option 2: Manual Migration

If you prefer to run individual migration steps:

```bash
# Set data directory (optional, defaults to pixie/core/data)
export PIXIE_DATA_DIR="/path/to/your/data"

# Run migration
uv run python scripts/migrate_data.py
```

## What Gets Migrated

The migration script will:

1. **Categories & Attributes**: Create category definitions and attribute metadata
2. **Printers**: Migrate all printer data with specifications
3. **Laptops**: Migrate laptop data with hardware specifications
4. **Computers**: Migrate computer data with system specifications
5. **Smartphones**: Migrate smartphone data with device specifications

## Expected Output

```text
INFO: Starting data migration from JSON to PostgreSQL...
INFO: Migrating categories and attributes...
INFO: Created 4 categories and 45 attributes
INFO: Migrating printers...
INFO: Migrated 25 printers
INFO: Migrating laptops...
INFO: Migrated 30 laptops
INFO: Migrating computers...
INFO: Migrated 20 computers
INFO: Migrating smartphones...
INFO: Migrated 35 smartphones
INFO: Data migration completed successfully!
INFO: Migration Statistics:
INFO:   categories: 4
INFO:   attributes: 45
INFO:   printers: 25
INFO:   laptops: 30
INFO:   computers: 20
INFO:   smartphones: 35
INFO: Total products migrated: 110
```

## Verification

After migration, you can verify the data:

```bash
# Connect to database and check counts
psql -d pixie_db -c "SELECT 'printers' as table, COUNT(*) as count FROM printers UNION ALL SELECT 'laptops', COUNT(*) FROM laptops UNION ALL SELECT 'computers', COUNT(*) FROM computers UNION ALL SELECT 'smartphones', COUNT(*) FROM smartphones;"

# Should show:
#   table      | count
# -------------+-------
#  printers    |    25
#  laptops     |    30
#  computers   |    20
#  smartphones |    35
```

## Switching to Database Backend

After successful migration, enable database mode:

```bash
export PIXIE_USE_DATABASE=true
```

The unified search engine will automatically switch to using the database backend.

## Troubleshooting

### Database Connection Issues

- Ensure PostgreSQL is running
- Check DATABASE_URL environment variable
- Verify user permissions

### Migration Errors

- Check JSON file formats
- Ensure database schema is applied
- Review error logs for specific issues

### Performance Issues

- Migration may take time for large datasets
- Consider batch processing for very large datasets
- Monitor database performance during migration
