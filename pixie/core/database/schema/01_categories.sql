-- Categories table for product type metadata
-- This table stores the different product categories supported by the system

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert the supported product categories
INSERT INTO categories (name, display_name, description) VALUES
    ('printers', 'Printers', 'Various types of printers including inkjet and laser'),
    ('laptops', 'Laptops', 'Portable computers and notebooks'),
    ('computers', 'Computers', 'Desktop computers and workstations'),
    ('smartphones', 'Smartphones', 'Mobile phones and smartphones')
ON CONFLICT (name) DO NOTHING;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_categories_updated_at
    BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
