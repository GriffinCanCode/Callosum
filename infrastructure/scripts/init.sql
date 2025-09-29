-- Initialize Callosum database
CREATE DATABASE IF NOT EXISTS callosum;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas for each service
CREATE SCHEMA IF NOT EXISTS ai_engine;
CREATE SCHEMA IF NOT EXISTS graph_engine;  
CREATE SCHEMA IF NOT EXISTS event_processor;

-- Set search path
ALTER DATABASE callosum SET search_path TO public, ai_engine, graph_engine, event_processor;

-- Create basic tables (will be expanded by migrations)
CREATE TABLE IF NOT EXISTS personalities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    dsl_content TEXT NOT NULL,
    compiled_rules JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    personality_id UUID REFERENCES personalities(id),
    node_type VARCHAR(100) NOT NULL,
    content JSONB NOT NULL,
    embeddings VECTOR(768),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    personality_id UUID REFERENCES personalities(id),
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
