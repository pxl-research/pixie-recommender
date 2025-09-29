-- Smartphones table
-- Stores smartphone product data with all relevant attributes

CREATE TABLE IF NOT EXISTS smartphones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    price_cents INTEGER GENERATED ALWAYS AS (ROUND(price * 100)) STORED,
    currency VARCHAR(3) DEFAULT 'EUR',
    screen_size_inches DECIMAL(4,1),
    resolution VARCHAR(50),
    processor VARCHAR(100),
    ram_gb INTEGER,
    storage_gb INTEGER,
    battery_capacity_mah INTEGER,
    operating_system VARCHAR(100),
    camera_mp DECIMAL(4,1),
    has_5g BOOLEAN DEFAULT false,
    has_nfc BOOLEAN DEFAULT false,
    has_wireless_charging BOOLEAN DEFAULT false,
    water_resistance VARCHAR(50),
    weight_g DECIMAL(6,1),
    dimensions_mm VARCHAR(50),
    color VARCHAR(50),
    availability_status VARCHAR(50) DEFAULT 'in_stock',
    stock_level INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create trigger to update updated_at timestamp
CREATE TRIGGER update_smartphones_updated_at
    BEFORE UPDATE ON smartphones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for common search patterns
CREATE INDEX IF NOT EXISTS idx_smartphones_brand ON smartphones(brand);
CREATE INDEX IF NOT EXISTS idx_smartphones_price ON smartphones(price);
CREATE INDEX IF NOT EXISTS idx_smartphones_screen_size ON smartphones(screen_size_inches);
CREATE INDEX IF NOT EXISTS idx_smartphones_processor ON smartphones(processor);
CREATE INDEX IF NOT EXISTS idx_smartphones_ram_gb ON smartphones(ram_gb);
CREATE INDEX IF NOT EXISTS idx_smartphones_storage_gb ON smartphones(storage_gb);
CREATE INDEX IF NOT EXISTS idx_smartphones_camera_mp ON smartphones(camera_mp);
CREATE INDEX IF NOT EXISTS idx_smartphones_availability_status ON smartphones(availability_status);
