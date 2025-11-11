-- Auto-initialization script for PostgreSQL
-- This script runs automatically when container starts for the first time

-- Create production database
CREATE DATABASE standart_prod_db
    WITH
    OWNER = standart_admin
    ENCODING = 'UTF8'
    LC_COLLATE = 'C'
    LC_CTYPE = 'C'
    TEMPLATE = template0;

-- Create development/staging database
CREATE DATABASE standart_dev_db
    WITH
    OWNER = standart_admin
    ENCODING = 'UTF8'
    LC_COLLATE = 'C'
    LC_CTYPE = 'C'
    TEMPLATE = template0;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE standart_prod_db TO standart_admin;
GRANT ALL PRIVILEGES ON DATABASE standart_dev_db TO standart_admin;

-- Connect to production DB and set up extensions (if needed)
\c standart_prod_db
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Connect to development DB and set up extensions (if needed)
\c standart_dev_db
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Log success
\echo 'Databases created successfully: standart_prod_db, standart_dev_db'
