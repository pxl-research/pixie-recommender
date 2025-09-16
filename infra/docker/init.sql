-- Initialize PostgreSQL database for Pixie Core
-- This script sets up the necessary extensions and initial data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create database user if not exists
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'pixie_user') THEN
      CREATE USER pixie_user WITH PASSWORD 'pixie_password';
   END IF;
END
$$;

-- Create database if not exists
SELECT 'CREATE DATABASE pixie_dev OWNER pixie_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'pixie_dev')\gexec

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE pixie_dev TO pixie_user;
