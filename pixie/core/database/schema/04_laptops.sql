-- Laptops table
-- Stores laptop product data with all relevant attributes

CREATE TABLE IF NOT EXISTS laptops (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    price_cents INTEGER GENERATED ALWAYS AS (ROUND(price * 100)) STORED,
    currency VARCHAR(3) DEFAULT 'EUR',
    screen_size_inches DECIMAL(4,1),
    processor VARCHAR(100),
    ram_gb INTEGER,
    storage_gb INTEGER,
    storage_type VARCHAR(50),
    battery_life_hours DECIMAL(4,1),
    operating_system VARCHAR(100),
    weight_kg DECIMAL(5,2),
    has_touchscreen BOOLEAN DEFAULT false,
    has_webcam BOOLEAN DEFAULT true,
    graphics_card VARCHAR(100),
    ports TEXT, -- JSON string or comma-separated
    warranty_years INTEGER,
    color VARCHAR(50),
    availability_status VARCHAR(50) DEFAULT 'in_stock',
    stock_level INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create trigger to update updated_at timestamp
CREATE TRIGGER update_laptops_updated_at
    BEFORE UPDATE ON laptops
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for common search patterns
CREATE INDEX IF NOT EXISTS idx_laptops_brand ON laptops(brand);
CREATE INDEX IF NOT EXISTS idx_laptops_price ON laptops(price);
CREATE INDEX IF NOT EXISTS idx_laptops_screen_size ON laptops(screen_size_inches);
CREATE INDEX IF NOT EXISTS idx_laptops_processor ON laptops(processor);
CREATE INDEX IF NOT EXISTS idx_laptops_ram_gb ON laptops(ram_gb);
CREATE INDEX IF NOT EXISTS idx_laptops_storage_gb ON laptops(storage_gb);
CREATE INDEX IF NOT EXISTS idx_laptops_availability_status ON laptops(availability_status);
