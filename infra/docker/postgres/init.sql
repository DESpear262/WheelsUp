-- WheelsUp PostgreSQL initialization script
-- This script runs when the PostgreSQL container starts for the first time

-- Create the database user for the application
CREATE USER wheelsup_user WITH PASSWORD 'wheelsup_password';

-- Create the development database
CREATE DATABASE wheelsup_dev OWNER wheelsup_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE wheelsup_dev TO wheelsup_user;

-- Connect to the database to set up extensions and permissions
\c wheelsup_dev;

-- Enable PostGIS extension for geospatial features
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO wheelsup_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO wheelsup_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO wheelsup_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO wheelsup_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO wheelsup_user;
