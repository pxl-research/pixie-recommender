-- Attributes table for conversational attribute configurations
-- This table stores the attribute definitions for each product category

CREATE TABLE IF NOT EXISTS attributes (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('range', 'choice')),
    question TEXT NOT NULL,
    description TEXT,
    options JSONB, -- For choice type attributes, stores the available options
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category_id, name)
);

-- Create trigger to update updated_at timestamp
CREATE TRIGGER update_attributes_updated_at
    BEFORE UPDATE ON attributes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert attribute configurations for printers
INSERT INTO attributes (category_id, name, type, question, description, options) VALUES
    ((SELECT id FROM categories WHERE name = 'printers'), 'budget', 'range', 'Wat is je budget voor een printer?', 'Price range the user is willing to spend', NULL),
    ((SELECT id FROM categories WHERE name = 'printers'), 'brand', 'choice', 'Heb je een voorkeur voor een bepaald merk?', 'Preferred printer brand', NULL),
    ((SELECT id FROM categories WHERE name = 'printers'), 'technology', 'choice', 'Welke printtechnologie heeft je voorkeur?', 'Inkjet vs laser printing technology', '["inkjet", "laser"]'::jsonb);

-- Insert attribute configurations for laptops
INSERT INTO attributes (category_id, name, type, question, description, options) VALUES
    ((SELECT id FROM categories WHERE name = 'laptops'), 'budget', 'range', 'Wat is je budget voor een laptop?', 'Price range the user is willing to spend', NULL),
    ((SELECT id FROM categories WHERE name = 'laptops'), 'brand', 'choice', 'Heb je een voorkeur voor een bepaald merk?', 'Preferred laptop brand', NULL),
    ((SELECT id FROM categories WHERE name = 'laptops'), 'screen_size', 'choice', 'Welke schermgrootte heeft je voorkeur?', 'Preferred screen size', '["13 inch", "14 inch", "15 inch", "16 inch", "17 inch"]'::jsonb);

-- Insert attribute configurations for computers
INSERT INTO attributes (category_id, name, type, question, description, options) VALUES
    ((SELECT id FROM categories WHERE name = 'computers'), 'budget', 'range', 'Wat is je budget voor een computer?', 'Price range the user is willing to spend', NULL),
    ((SELECT id FROM categories WHERE name = 'computers'), 'brand', 'choice', 'Heb je een voorkeur voor een bepaald merk?', 'Preferred computer brand', NULL),
    ((SELECT id FROM categories WHERE name = 'computers'), 'processor', 'choice', 'Welke processor heeft je voorkeur?', 'Preferred processor type', '["Intel Core i3", "Intel Core i5", "Intel Core i7", "Intel Core i9", "AMD Ryzen 3", "AMD Ryzen 5", "AMD Ryzen 7", "AMD Ryzen 9"]'::jsonb);

-- Insert attribute configurations for smartphones
INSERT INTO attributes (category_id, name, type, question, description, options) VALUES
    ((SELECT id FROM categories WHERE name = 'smartphones'), 'budget', 'range', 'Wat is je budget voor een smartphone?', 'Price range the user is willing to spend', NULL),
    ((SELECT id FROM categories WHERE name = 'smartphones'), 'brand', 'choice', 'Heb je een voorkeur voor een bepaald merk?', 'Preferred smartphone brand', NULL),
    ((SELECT id FROM categories WHERE name = 'smartphones'), 'screen_size', 'choice', 'Welke schermgrootte heeft je voorkeur?', 'Preferred screen size', '["5 inch", "6 inch", "6.5 inch", "7 inch"]'::jsonb);
