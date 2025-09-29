#!/usr/bin/env python3
"""DEPRECATED: This migration script is no longer functional.

Use the seed.py system in pixie/core/database/seed.py instead.
The old model classes (Printer, Laptop, etc.) have been replaced
with a flexible Product/ProductType/AttributeDefinition system.
"""

import sys


def main():
    print("ERROR: This migration script is deprecated and broken.")
    print("Use the new seeding system: pixie/core/database/seed.py")
    print("The database is automatically seeded on startup.")
    sys.exit(1)


if __name__ == "__main__":
    main()
