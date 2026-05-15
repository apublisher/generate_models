-- Test case for unique constraint fix
-- This validates that single-column unique generates unique=True
-- but composite unique does NOT

DROP TABLE IF EXISTS test_single_unique;
DROP TABLE IF EXISTS test_composite_unique;
DROP TABLE IF EXISTS test_mixed_unique;

-- Case 1: Single-column unique constraint
CREATE TABLE test_single_unique (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE,
    username VARCHAR(100) UNIQUE
);

-- Case 2: Composite unique constraint
CREATE TABLE test_composite_unique (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    UNIQUE KEY uk_tenant_external (tenant_id, external_id)
);

-- Case 3: Mixed - both single and composite unique constraints
CREATE TABLE test_mixed_unique (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE,
    tenant_id INT NOT NULL,
    slug VARCHAR(255) NOT NULL,
    UNIQUE KEY uk_tenant_slug (tenant_id, slug)
);
