-- Printers table
-- Stores printer product data with all relevant attributes

CREATE TABLE IF NOT EXISTS printers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    technology VARCHAR(50) NOT NULL,
    price_cents INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    description TEXT,
    has_wifi BOOLEAN DEFAULT false,
    has_duplex BOOLEAN DEFAULT false,
    has_color BOOLEAN DEFAULT false,
    is_multifunction BOOLEAN DEFAULT false,
    print_speed_ppm INTEGER,
    resolution_dpi VARCHAR(50),
    max_paper_size VARCHAR(50),
    availability_status VARCHAR(50) DEFAULT 'in_stock',
    stock_level INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create trigger to update updated_at timestamp
CREATE TRIGGER update_printers_updated_at
    BEFORE UPDATE ON printers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for common search patterns
CREATE INDEX IF NOT EXISTS idx_printers_brand ON printers(brand);
CREATE INDEX IF NOT EXISTS idx_printers_technology ON printers(technology);
CREATE INDEX IF NOT EXISTS idx_printers_price_cents ON printers(price_cents);
CREATE INDEX IF NOT EXISTS idx_printers_has_wifi ON printers(has_wifi);
CREATE INDEX IF NOT EXISTS idx_printers_has_color ON printers(has_color);
CREATE INDEX IF NOT EXISTS idx_printers_availability_status ON printers(availability_status);
