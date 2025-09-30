-- Initialize database with proper settings

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create monitoring database if it doesn't exist
-- Note: This is run automatically by docker-compose

-- Set timezone
SET timezone = 'UTC';

-- Create indexes for better performance (will be created by Alembic migrations)
-- This file serves as a placeholder for any additional database initialization