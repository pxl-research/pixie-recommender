-- Additional performance indexes
-- This file contains advanced indexes for optimal query performance

-- Full-text search indexes for product names and descriptions
CREATE INDEX IF NOT EXISTS idx_printers_name_fts ON printers USING gin(to_tsvector('dutch', name));
CREATE INDEX IF NOT EXISTS idx_printers_description_fts ON printers USING gin(to_tsvector('dutch', description));

CREATE INDEX IF NOT EXISTS idx_laptops_name_fts ON laptops USING gin(to_tsvector('dutch', name));
CREATE INDEX IF NOT EXISTS idx_laptops_description_fts ON laptops USING gin(to_tsvector('dutch', description));

CREATE INDEX IF NOT EXISTS idx_computers_name_fts ON computers USING gin(to_tsvector('dutch', name));
CREATE INDEX IF NOT EXISTS idx_computers_description_fts ON computers USING gin(to_tsvector('dutch', description));

CREATE INDEX IF NOT EXISTS idx_smartphones_name_fts ON smartphones USING gin(to_tsvector('dutch', name));
CREATE INDEX IF NOT EXISTS idx_smartphones_description_fts ON smartphones USING gin(to_tsvector('dutch', description));

-- Composite indexes for common filter combinations
CREATE INDEX IF NOT EXISTS idx_printers_brand_technology ON printers(brand, technology);
CREATE INDEX IF NOT EXISTS idx_printers_price_brand ON printers(price_cents, brand);
CREATE INDEX IF NOT EXISTS idx_printers_availability_stock ON printers(availability_status, stock_level);

CREATE INDEX IF NOT EXISTS idx_laptops_brand_price ON laptops(brand, price);
CREATE INDEX IF NOT EXISTS idx_laptops_screen_ram ON laptops(screen_size_inches, ram_gb);
CREATE INDEX IF NOT EXISTS idx_laptops_availability_stock ON laptops(availability_status, stock_level);

CREATE INDEX IF NOT EXISTS idx_computers_brand_price ON computers(brand, price);
CREATE INDEX IF NOT EXISTS idx_computers_processor_ram ON computers(processor, ram_gb);
CREATE INDEX IF NOT EXISTS idx_computers_availability_stock ON computers(availability_status, stock_level);

CREATE INDEX IF NOT EXISTS idx_smartphones_brand_price ON smartphones(brand, price);
CREATE INDEX IF NOT EXISTS idx_smartphones_screen_ram ON smartphones(screen_size_inches, ram_gb);
CREATE INDEX IF NOT EXISTS idx_smartphones_availability_stock ON smartphones(availability_status, stock_level);

-- GIN index for attributes options (JSONB)
CREATE INDEX IF NOT EXISTS idx_attributes_options ON attributes USING gin(options);

-- Index for attributes by category
CREATE INDEX IF NOT EXISTS idx_attributes_category_type ON attributes(category_id, type);

-- Partial indexes for active products
CREATE INDEX IF NOT EXISTS idx_printers_active ON printers(brand, technology) WHERE availability_status = 'in_stock' AND stock_level > 0;
CREATE INDEX IF NOT EXISTS idx_laptops_active ON laptops(brand, price) WHERE availability_status = 'in_stock' AND stock_level > 0;
CREATE INDEX IF NOT EXISTS idx_computers_active ON computers(brand, price) WHERE availability_status = 'in_stock' AND stock_level > 0;
CREATE INDEX IF NOT EXISTS idx_smartphones_active ON smartphones(brand, price) WHERE availability_status = 'in_stock' AND stock_level > 0;
