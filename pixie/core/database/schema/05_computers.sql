-- Computers table
-- Stores desktop computer product data with all relevant attributes

CREATE TABLE IF NOT EXISTS computers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    price_cents INTEGER GENERATED ALWAYS AS (ROUND(price * 100)) STORED,
    currency VARCHAR(3) DEFAULT 'EUR',
    processor VARCHAR(100),
    ram_gb INTEGER,
    storage_gb INTEGER,
    storage_type VARCHAR(50),
    motherboard VARCHAR(100),
    power_supply_watts INTEGER,
    case_type VARCHAR(50),
    operating_system VARCHAR(100),
    has_wifi BOOLEAN DEFAULT true,
    has_bluetooth BOOLEAN DEFAULT true,
    graphics_card VARCHAR(100),
    cooling_system VARCHAR(100),
    ports TEXT, -- JSON string or comma-separated
    warranty_years INTEGER,
    color VARCHAR(50),
    availability_status VARCHAR(50) DEFAULT 'in_stock',
    stock_level INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create trigger to update updated_at timestamp
CREATE TRIGGER update_computers_updated_at
    BEFORE UPDATE ON computers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for common search patterns
CREATE INDEX IF NOT EXISTS idx_computers_brand ON computers(brand);
CREATE INDEX IF NOT EXISTS idx_computers_price ON computers(price);
CREATE INDEX IF NOT EXISTS idx_computers_processor ON computers(processor);
CREATE INDEX IF NOT EXISTS idx_computers_ram_gb ON computers(ram_gb);
CREATE INDEX IF NOT EXISTS idx_computers_storage_gb ON computers(storage_gb);
CREATE INDEX IF NOT EXISTS idx_computers_graphics_card ON computers(graphics_card);
CREATE INDEX IF NOT EXISTS idx_computers_availability_status ON computers(availability_status);
