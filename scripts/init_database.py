#!/usr/bin/env python3
"""Simple database initialization script for CI/CD environments."""

import logging
import os

from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment variables."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://pixie_user:pixie_password@localhost:5432/pixie_dev",
    )


def init_database_simple():
    """Initialize database with simple SQL commands."""
    engine = create_engine(get_database_url())

    try:
        with engine.connect() as conn:
            # Create tables if they don't exist (using the model definitions would be better)
            logger.info("Checking database initialization...")

            # Check if tables exist
            result = conn.execute(
                text(
                    """
                SELECT COUNT(*) as table_count 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('product_types', 'products')
            """
                )
            )
            table_count = result.scalar()

            if table_count < 2:
                logger.info("Tables don't exist, they will be created by the ORM")
                return False

            # Check if printers product type exists
            result = conn.execute(
                text(
                    """
                SELECT COUNT(*) as printer_type_count 
                FROM product_types 
                WHERE name = 'printers'
            """
                )
            )
            printer_type_count = result.scalar()

            if printer_type_count == 0:
                logger.info("Adding printers product type...")
                conn.execute(
                    text(
                        """
                    INSERT INTO product_types (
                        name, display_name, description, is_active, created_at, updated_at
                    )
                    VALUES (
                        'printers', 'Printers', 
                        'Various types of printers including inkjet and laser', 
                        true, NOW(), NOW()
                    )
                """
                    )
                )
                conn.commit()

            # Check if printer products exist
            result = conn.execute(
                text(
                    """
                SELECT COUNT(*) as printer_count 
                FROM products p 
                JOIN product_types pt ON p.product_type_id = pt.id 
                WHERE pt.name = 'printers'
            """
                )
            )
            printer_count = result.scalar()

            if printer_count == 0:
                logger.info("Adding printer products...")
                conn.execute(
                    text(
                        """
                    INSERT INTO products (
                        external_id, product_type_id, name, description, brand, model, 
                        price_cents, currency, availability_status, stock_level, 
                        is_active, created_at, updated_at
                    )
                    SELECT 
                        'BROTHER-XC-2570-1', 
                        pt.id, 
                        'Brother XC 2570', 
                        'Reliable laser printer for home and office use', 
                        'Brother', 
                        'XC 2570', 
                        19900, 
                        'EUR', 
                        'in_stock', 
                        10, 
                        true, 
                        NOW(), 
                        NOW()
                    FROM product_types pt WHERE pt.name = 'printers'
                    
                    UNION ALL
                    
                    SELECT 
                        'BROTHER-XT-3560-1', 
                        pt.id, 
                        'Brother XT 3560', 
                        'Compact laser printer with wireless connectivity', 
                        'Brother', 
                        'XT 3560', 
                        15900, 
                        'EUR', 
                        'in_stock', 
                        5, 
                        true, 
                        NOW(), 
                        NOW()
                    FROM product_types pt WHERE pt.name = 'printers'
                    
                    UNION ALL
                    
                    SELECT 
                        'HP-LASERJET-PRO-1', 
                        pt.id, 
                        'HP LaserJet Pro M404n', 
                        'Professional laser printer with fast printing speeds', 
                        'HP', 
                        'LaserJet Pro M404n', 
                        17900, 
                        'EUR', 
                        'in_stock', 
                        8, 
                        true, 
                        NOW(), 
                        NOW()
                    FROM product_types pt WHERE pt.name = 'printers'
                    
                    UNION ALL
                    
                    SELECT 
                        'CANON-INKJET-1', 
                        pt.id, 
                        'Canon PIXMA TS3350', 
                        'All-in-one inkjet printer for home use', 
                        'Canon', 
                        'PIXMA TS3350', 
                        8900, 
                        'EUR', 
                        'in_stock', 
                        12, 
                        true, 
                        NOW(), 
                        NOW()
                    FROM product_types pt WHERE pt.name = 'printers'
                """
                    )
                )
                conn.commit()
                logger.info("Added printer products successfully")

            # Create attribute definitions for printers
            result = conn.execute(
                text(
                    """
                SELECT COUNT(*) as attr_count 
                FROM attribute_definitions ad 
                JOIN product_types pt ON ad.product_type_id = pt.id 
                WHERE pt.name = 'printers'
                """
                )
            )
            attr_count = result.scalar()

            if attr_count == 0:
                logger.info("Adding attribute definitions for printers...")
                conn.execute(
                    text(
                        """
                    INSERT INTO attribute_definitions (
                        id, product_type_id, name, display_name, data_type, 
                        is_required, validation_rules, options, display_order, 
                        canonical_name, is_searchable, is_filterable, created_at, updated_at
                    )
                    SELECT 
                        gen_random_uuid(),
                        pt.id,
                        'budget',
                        'Budget',
                        'number',
                        true,
                        NULL::json,
                        NULL::json,
                        1,
                        'budget',
                        true,
                        true,
                        NOW(),
                        NOW()
                    FROM product_types pt WHERE pt.name = 'printers'
                    
                    UNION ALL
                    
                    SELECT 
                        gen_random_uuid(),
                        pt.id,
                        'brand',
                        'Brand',
                        'choice',
                        false,
                        NULL::json,
                        NULL::json,
                        2,
                        'brand',
                        true,
                        true,
                        NOW(),
                        NOW()
                    FROM product_types pt WHERE pt.name = 'printers'
                    
                    UNION ALL
                    
                    SELECT 
                        gen_random_uuid(),
                        pt.id,
                        'technology',
                        'Technology',
                        'choice',
                        false,
                        NULL::json,
                        '["inkjet", "laser"]'::json,
                        3,
                        'technology',
                        true,
                        true,
                        NOW(),
                        NOW()
                    FROM product_types pt WHERE pt.name = 'printers'
                """
                    )
                )
                conn.commit()
                logger.info("Added attribute definitions successfully")

            # Create product attribute values
            result = conn.execute(
                text(
                    """
                SELECT COUNT(*) as attr_value_count 
                FROM product_attribute_values pav 
                JOIN products p ON pav.product_id = p.id 
                JOIN product_types pt ON p.product_type_id = pt.id 
                WHERE pt.name = 'printers'
                """
                )
            )
            attr_value_count = result.scalar()

            if attr_value_count == 0:
                logger.info("Adding product attribute values for printers...")
                conn.execute(
                    text(
                        """
                    -- Brother XC 2570 attributes
                    INSERT INTO product_attribute_values (
                        product_id, attribute_definition_id, string_value, created_at, updated_at
                    )
                    SELECT 
                        p.id,
                        ad.id,
                        'Brother',
                        NOW(),
                        NOW()
                    FROM products p
                    JOIN product_types pt ON p.product_type_id = pt.id
                    JOIN attribute_definitions ad ON ad.product_type_id = pt.id
                    WHERE pt.name = 'printers' 
                    AND p.name = 'Brother XC 2570' 
                    AND ad.name = 'brand'
                    
                    UNION ALL
                    
                    SELECT 
                        p.id,
                        ad.id,
                        'laser',
                        NOW(),
                        NOW()
                    FROM products p
                    JOIN product_types pt ON p.product_type_id = pt.id
                    JOIN attribute_definitions ad ON ad.product_type_id = pt.id
                    WHERE pt.name = 'printers' 
                    AND p.name = 'Brother XC 2570' 
                    AND ad.name = 'technology'
                    
                    UNION ALL
                    
                    -- Brother XT 3560 attributes
                    SELECT 
                        p.id,
                        ad.id,
                        'Brother',
                        NOW(),
                        NOW()
                    FROM products p
                    JOIN product_types pt ON p.product_type_id = pt.id
                    JOIN attribute_definitions ad ON ad.product_type_id = pt.id
                    WHERE pt.name = 'printers' 
                    AND p.name = 'Brother XT 3560' 
                    AND ad.name = 'brand'
                    
                    UNION ALL
                    
                    SELECT 
                        p.id,
                        ad.id,
                        'laser',
                        NOW(),
                        NOW()
                    FROM products p
                    JOIN product_types pt ON p.product_type_id = pt.id
                    JOIN attribute_definitions ad ON ad.product_type_id = pt.id
                    WHERE pt.name = 'printers' 
                    AND p.name = 'Brother XT 3560' 
                    AND ad.name = 'technology'
                    
                    UNION ALL
                    
                    -- HP LaserJet attributes
                    SELECT 
                        p.id,
                        ad.id,
                        'HP',
                        NOW(),
                        NOW()
                    FROM products p
                    JOIN product_types pt ON p.product_type_id = pt.id
                    JOIN attribute_definitions ad ON ad.product_type_id = pt.id
                    WHERE pt.name = 'printers' 
                    AND p.name = 'HP LaserJet Pro M404n' 
                    AND ad.name = 'brand'
                    
                    UNION ALL
                    
                    SELECT 
                        p.id,
                        ad.id,
                        'laser',
                        NOW(),
                        NOW()
                    FROM products p
                    JOIN product_types pt ON p.product_type_id = pt.id
                    JOIN attribute_definitions ad ON ad.product_type_id = pt.id
                    WHERE pt.name = 'printers' 
                    AND p.name = 'HP LaserJet Pro M404n' 
                    AND ad.name = 'technology'
                    
                    UNION ALL
                    
                    -- Canon PIXMA attributes
                    SELECT 
                        p.id,
                        ad.id,
                        'Canon',
                        NOW(),
                        NOW()
                    FROM products p
                    JOIN product_types pt ON p.product_type_id = pt.id
                    JOIN attribute_definitions ad ON ad.product_type_id = pt.id
                    WHERE pt.name = 'printers' 
                    AND p.name = 'Canon PIXMA TS3350' 
                    AND ad.name = 'brand'
                    
                    UNION ALL
                    
                    SELECT 
                        p.id,
                        ad.id,
                        'inkjet',
                        NOW(),
                        NOW()
                    FROM products p
                    JOIN product_types pt ON p.product_type_id = pt.id
                    JOIN attribute_definitions ad ON ad.product_type_id = pt.id
                    WHERE pt.name = 'printers' 
                    AND p.name = 'Canon PIXMA TS3350' 
                    AND ad.name = 'technology'
                """
                    )
                )
                conn.commit()
                logger.info("Added product attribute values successfully")

            logger.info("Database initialization completed")
            return True

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database_simple()
