CREATE TABLE IF NOT EXISTS employees (
    employee_id VARCHAR(20) PRIMARY KEY,
    name TEXT NOT NULL,
    primary_skill TEXT NOT NULL,
    secondary_skill TEXT,
    years_experience INTEGER NOT NULL,
    certifications TEXT,
    availability_status TEXT,
    current_utilization NUMERIC(5,2),
    location TEXT,
    role TEXT,
    resume_text TEXT
);

CREATE TABLE IF NOT EXISTS projects (
    project_id VARCHAR(20) PRIMARY KEY,
    project_name TEXT NOT NULL,
    required_skills TEXT,
    preferred_certifications TEXT,
    min_experience INTEGER,
    required_headcount INTEGER,
    location TEXT,
    domain TEXT
);

CREATE TABLE IF NOT EXISTS historical_allocations (
    allocation_id VARCHAR(20) PRIMARY KEY,
    employee_id VARCHAR(20) REFERENCES employees(employee_id),
    project_id VARCHAR(20) REFERENCES projects(project_id),
    allocation_month VARCHAR(7),
    allocation_percentage INTEGER,
    performance_rating NUMERIC(2,1)
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(30) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
