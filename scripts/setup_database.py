#!/usr/bin/env python3
"""Database setup and testing script for flexible product system."""

import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pixie.core.database.connection import test_connection
from pixie.core.database.init import create_tables, reset_database
from pixie.core.database.seed import seed_database
from pixie.core.database.test_flexible_system import run_all_tests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Set up the database with tables and initial data."""
    logger.info("Setting up database...")
    
    try:
        # Test connection
        if not test_connection():
            logger.error("Database connection failed")
            return False
            
        # Create tables
        create_tables()
        
        # Seed with initial data
        seed_database()
        
        logger.info("Database setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False

def reset_and_setup():
    """Reset database and set up from scratch."""
    logger.info("Resetting and setting up database...")
    
    try:
        reset_database()
        seed_database()
        logger.info("Database reset and setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database reset and setup failed: {e}")
        return False

def run_tests():
    """Run the flexible system tests."""
    logger.info("Running flexible system tests...")
    
    try:
        run_all_tests()
        return True
        
    except Exception as e:
        logger.error(f"Tests failed: {e}")
        return False

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python setup_database.py <command>")
        print("Commands:")
        print("  setup     - Set up database with tables and initial data")
        print("  reset     - Reset database and set up from scratch") 
        print("  test      - Run flexible system tests")
        print("  all       - Setup, seed, and test")
        return
        
    command = sys.argv[1]
    
    if command == "setup":
        success = setup_database()
    elif command == "reset":
        success = reset_and_setup()
    elif command == "test":
        success = run_tests()
    elif command == "all":
        success = setup_database()
        if success:
            success = run_tests()
    else:
        print(f"Unknown command: {command}")
        return
        
    if success:
        print("✓ Operation completed successfully!")
        sys.exit(0)
    else:
        print("✗ Operation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
