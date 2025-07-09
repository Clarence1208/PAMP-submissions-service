-- SQL Sample File - Comprehensive Database Operations
-- This file demonstrates various SQL features including:
-- - DDL (Data Definition Language) - CREATE, ALTER, DROP
-- - DML (Data Manipulation Language) - INSERT, UPDATE, DELETE, SELECT
-- - DCL (Data Control Language) - GRANT, REVOKE
-- - Advanced features like stored procedures, functions, triggers, views
-- - Window functions, CTEs, and complex queries
-- - Multiple SQL dialect examples (PostgreSQL, MySQL, SQL Server)

-- =====================================================
-- DATABASE AND SCHEMA CREATION
-- =====================================================

-- PostgreSQL syntax
DROP DATABASE IF EXISTS sample_company_db;
CREATE DATABASE sample_company_db
    WITH ENCODING 'UTF8'
    LC_COLLATE='en_US.utf8'
    LC_CTYPE='en_US.utf8'
    TEMPLATE=template0;

\c sample_company_db;

-- Create schemas for organization
CREATE SCHEMA IF NOT EXISTS hr;
CREATE SCHEMA IF NOT EXISTS sales;
CREATE SCHEMA IF NOT EXISTS analytics;

-- =====================================================
-- TABLE CREATION WITH CONSTRAINTS
-- =====================================================

-- Departments table
CREATE TABLE hr.departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    manager_id INTEGER,
    location_id INTEGER,
    budget DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Employees table with complex constraints
CREATE TABLE hr.employees (
    employee_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone_number VARCHAR(20),
    hire_date DATE NOT NULL DEFAULT CURRENT_DATE,
    job_title VARCHAR(100) NOT NULL,
    salary DECIMAL(10,2) CHECK (salary > 0),
    commission_pct DECIMAL(3,2) CHECK (commission_pct BETWEEN 0 AND 1),
    manager_id INTEGER,
    department_id INTEGER NOT NULL,
    birth_date DATE CHECK (birth_date < CURRENT_DATE),
    gender CHAR(1) CHECK (gender IN ('M', 'F', 'O')),
    address JSONB,
    skills TEXT[],
    performance_rating INTEGER CHECK (performance_rating BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_emp_dept FOREIGN KEY (department_id) 
        REFERENCES hr.departments(department_id) ON DELETE RESTRICT,
    CONSTRAINT fk_emp_manager FOREIGN KEY (manager_id) 
        REFERENCES hr.employees(employee_id) ON DELETE SET NULL,
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Add foreign key to departments after employees table is created
ALTER TABLE hr.departments
ADD CONSTRAINT fk_dept_manager 
FOREIGN KEY (manager_id) REFERENCES hr.employees(employee_id);

-- Customers table
CREATE TABLE sales.customers (
    customer_id SERIAL PRIMARY KEY,
    company_name VARCHAR(200) NOT NULL,
    contact_first_name VARCHAR(50),
    contact_last_name VARCHAR(50),
    contact_email VARCHAR(100),
    contact_phone VARCHAR(20),
    billing_address JSONB,
    shipping_address JSONB,
    customer_type VARCHAR(20) DEFAULT 'Regular' 
        CHECK (customer_type IN ('Regular', 'Premium', 'VIP')),
    credit_limit DECIMAL(12,2) DEFAULT 0,
    tax_exempt BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_order_date DATE,
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(15,2) DEFAULT 0
);

-- Products table
CREATE TABLE sales.products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    category_id INTEGER,
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    cost DECIMAL(10,2) CHECK (cost >= 0),
    stock_quantity INTEGER DEFAULT 0 CHECK (stock_quantity >= 0),
    reorder_level INTEGER DEFAULT 10,
    discontinued BOOLEAN DEFAULT FALSE,
    supplier_id INTEGER,
    specifications JSONB,
    dimensions VARCHAR(100),
    weight DECIMAL(8,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE sales.orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    employee_id INTEGER,
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    required_date DATE,
    shipped_date DATE,
    ship_via INTEGER,
    freight DECIMAL(8,2) DEFAULT 0,
    ship_name VARCHAR(100),
    ship_address JSONB,
    order_status VARCHAR(20) DEFAULT 'Pending' 
        CHECK (order_status IN ('Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled')),
    payment_method VARCHAR(50),
    payment_status VARCHAR(20) DEFAULT 'Pending'
        CHECK (payment_status IN ('Pending', 'Paid', 'Refunded', 'Failed')),
    subtotal DECIMAL(12,2) DEFAULT 0,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    shipping_amount DECIMAL(8,2) DEFAULT 0,
    total_amount DECIMAL(12,2) GENERATED ALWAYS AS (subtotal + tax_amount + shipping_amount) STORED,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_order_customer FOREIGN KEY (customer_id) 
        REFERENCES sales.customers(customer_id),
    CONSTRAINT fk_order_employee FOREIGN KEY (employee_id) 
        REFERENCES hr.employees(employee_id),
    CONSTRAINT valid_dates CHECK (required_date >= order_date AND 
                                 (shipped_date IS NULL OR shipped_date >= order_date))
);

-- Order details table
CREATE TABLE sales.order_details (
    order_detail_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    discount DECIMAL(3,2) DEFAULT 0 CHECK (discount BETWEEN 0 AND 1),
    line_total DECIMAL(12,2) GENERATED ALWAYS AS (unit_price * quantity * (1 - discount)) STORED,
    
    CONSTRAINT fk_orderdetail_order FOREIGN KEY (order_id) 
        REFERENCES sales.orders(order_id) ON DELETE CASCADE,
    CONSTRAINT fk_orderdetail_product FOREIGN KEY (product_id) 
        REFERENCES sales.products(product_id),
    CONSTRAINT uk_order_product UNIQUE (order_id, product_id)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Primary indexes are created automatically, create additional ones
CREATE INDEX idx_employees_department ON hr.employees(department_id);
CREATE INDEX idx_employees_manager ON hr.employees(manager_id);
CREATE INDEX idx_employees_name ON hr.employees(last_name, first_name);
CREATE INDEX idx_employees_email ON hr.employees(email);
CREATE INDEX idx_employees_hire_date ON hr.employees(hire_date);

CREATE INDEX idx_customers_company ON sales.customers(company_name);
CREATE INDEX idx_customers_type ON sales.customers(customer_type);
CREATE INDEX idx_customers_email ON sales.customers(contact_email);

CREATE INDEX idx_products_sku ON sales.products(sku);
CREATE INDEX idx_products_name ON sales.products(product_name);
CREATE INDEX idx_products_category ON sales.products(category_id);
CREATE INDEX idx_products_price ON sales.products(unit_price);

CREATE INDEX idx_orders_customer ON sales.orders(customer_id);
CREATE INDEX idx_orders_employee ON sales.orders(employee_id);
CREATE INDEX idx_orders_date ON sales.orders(order_date);
CREATE INDEX idx_orders_status ON sales.orders(order_status);

-- Partial index for active employees only
CREATE INDEX idx_employees_active ON hr.employees(employee_id) WHERE salary > 0;

-- Composite index for order details
CREATE INDEX idx_orderdetails_order_product ON sales.order_details(order_id, product_id);

-- JSON indexes (PostgreSQL specific)
CREATE INDEX idx_employee_address_city ON hr.employees USING GIN ((address->>'city'));
CREATE INDEX idx_customer_billing_state ON sales.customers USING GIN ((billing_address->>'state'));

-- =====================================================
-- SAMPLE DATA INSERTION
-- =====================================================

-- Insert departments
INSERT INTO hr.departments (department_name, budget, location_id) VALUES
    ('Human Resources', 500000.00, 1),
    ('Information Technology', 1200000.00, 1),
    ('Sales', 800000.00, 2),
    ('Marketing', 600000.00, 2),
    ('Finance', 750000.00, 1),
    ('Operations', 950000.00, 3),
    ('Research & Development', 1500000.00, 1),
    ('Customer Service', 400000.00, 2);

-- Insert employees
INSERT INTO hr.employees (
    first_name, last_name, email, phone_number, hire_date, job_title, 
    salary, department_id, birth_date, gender, address, skills, performance_rating
) VALUES
    ('John', 'Smith', 'john.smith@company.com', '555-1001', '2020-01-15', 'Software Engineer', 
     75000.00, 2, '1990-05-20', 'M', 
     '{"street": "123 Main St", "city": "New York", "state": "NY", "zip": "10001"}',
     ARRAY['Python', 'JavaScript', 'SQL'], 4),
    
    ('Sarah', 'Johnson', 'sarah.johnson@company.com', '555-1002', '2019-03-10', 'HR Manager', 
     85000.00, 1, '1985-08-12', 'F',
     '{"street": "456 Oak Ave", "city": "New York", "state": "NY", "zip": "10002"}',
     ARRAY['Leadership', 'Recruiting', 'Employee Relations'], 5),
    
    ('Michael', 'Brown', 'michael.brown@company.com', '555-1003', '2021-06-01', 'Sales Representative', 
     55000.00, 3, '1992-11-30', 'M',
     '{"street": "789 Pine Rd", "city": "Chicago", "state": "IL", "zip": "60601"}',
     ARRAY['Sales', 'Customer Service', 'Negotiation'], 3),
    
    ('Emily', 'Davis', 'emily.davis@company.com', '555-1004', '2018-09-20', 'Marketing Specialist', 
     62000.00, 4, '1988-03-25', 'F',
     '{"street": "321 Elm St", "city": "Los Angeles", "state": "CA", "zip": "90210"}',
     ARRAY['Digital Marketing', 'Content Creation', 'Analytics'], 4),
    
    ('David', 'Wilson', 'david.wilson@company.com', '555-1005', '2017-12-05', 'Financial Analyst', 
     68000.00, 5, '1987-07-18', 'M',
     '{"street": "654 Maple Dr", "city": "Boston", "state": "MA", "zip": "02101"}',
     ARRAY['Financial Analysis', 'Excel', 'PowerBI'], 4);

-- Update managers
UPDATE hr.departments SET manager_id = 2 WHERE department_name = 'Human Resources';
UPDATE hr.departments SET manager_id = 1 WHERE department_name = 'Information Technology';

-- Insert customers
INSERT INTO sales.customers (
    company_name, contact_first_name, contact_last_name, contact_email, 
    customer_type, credit_limit, billing_address
) VALUES
    ('Tech Solutions Inc', 'Robert', 'Anderson', 'robert@techsolutions.com', 
     'Premium', 50000.00, 
     '{"street": "100 Business Blvd", "city": "Seattle", "state": "WA", "zip": "98101"}'),
    
    ('Global Marketing Corp', 'Lisa', 'Thompson', 'lisa@globalmarketing.com', 
     'VIP', 100000.00,
     '{"street": "200 Commerce St", "city": "San Francisco", "state": "CA", "zip": "94102"}'),
    
    ('Small Business LLC', 'James', 'Garcia', 'james@smallbiz.com', 
     'Regular', 10000.00,
     '{"street": "50 Local Ave", "city": "Austin", "state": "TX", "zip": "73301"}');

-- Insert products
INSERT INTO sales.products (
    product_name, sku, unit_price, cost, stock_quantity, 
    specifications, dimensions, weight
) VALUES
    ('Professional Software License', 'SW-PRO-001', 299.99, 50.00, 1000,
     '{"type": "software", "platform": "multi", "license_type": "perpetual"}', 
     'Digital Download', 0.000),
    
    ('Enterprise Consulting Package', 'CON-ENT-001', 1500.00, 500.00, 50,
     '{"hours": 40, "level": "senior", "includes": ["analysis", "implementation"]}',
     'Service Package', 0.000),
    
    ('Training Manual Set', 'TRN-MAN-001', 79.99, 25.00, 200,
     '{"pages": 500, "format": "hardcover", "language": "english"}',
     '8.5x11x2 inches', 2.500);

-- =====================================================
-- VIEWS FOR DATA ACCESS
-- =====================================================

-- Employee details view with department information
CREATE OR REPLACE VIEW hr.employee_details AS
SELECT 
    e.employee_id,
    e.first_name || ' ' || e.last_name AS full_name,
    e.email,
    e.job_title,
    e.salary,
    e.hire_date,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, e.hire_date)) AS years_employed,
    d.department_name,
    m.first_name || ' ' || m.last_name AS manager_name,
    e.performance_rating,
    e.address->>'city' AS city,
    e.address->>'state' AS state
FROM hr.employees e
JOIN hr.departments d ON e.department_id = d.department_id
LEFT JOIN hr.employees m ON e.manager_id = m.employee_id
WHERE e.salary > 0; -- Only active employees

-- Sales summary view
CREATE OR REPLACE VIEW sales.order_summary AS
SELECT 
    o.order_id,
    c.company_name,
    c.contact_first_name || ' ' || c.contact_last_name AS contact_name,
    e.first_name || ' ' || e.last_name AS sales_rep,
    o.order_date,
    o.order_status,
    o.total_amount,
    COUNT(od.order_detail_id) AS item_count,
    SUM(od.quantity) AS total_quantity
FROM sales.orders o
JOIN sales.customers c ON o.customer_id = c.customer_id
LEFT JOIN hr.employees e ON o.employee_id = e.employee_id
LEFT JOIN sales.order_details od ON o.order_id = od.order_id
GROUP BY o.order_id, c.company_name, c.contact_first_name, c.contact_last_name,
         e.first_name, e.last_name, o.order_date, o.order_status, o.total_amount;

-- Product performance view
CREATE OR REPLACE VIEW analytics.product_performance AS
SELECT 
    p.product_id,
    p.product_name,
    p.sku,
    p.unit_price,
    p.stock_quantity,
    COALESCE(SUM(od.quantity), 0) AS total_sold,
    COALESCE(SUM(od.line_total), 0) AS total_revenue,
    COALESCE(AVG(od.unit_price), p.unit_price) AS avg_selling_price,
    CASE 
        WHEN p.stock_quantity <= p.reorder_level THEN 'Low Stock'
        WHEN p.stock_quantity = 0 THEN 'Out of Stock'
        ELSE 'In Stock'
    END AS stock_status
FROM sales.products p
LEFT JOIN sales.order_details od ON p.product_id = od.product_id
GROUP BY p.product_id, p.product_name, p.sku, p.unit_price, 
         p.stock_quantity, p.reorder_level;

-- =====================================================
-- STORED PROCEDURES AND FUNCTIONS
-- =====================================================

-- Function to calculate employee bonus
CREATE OR REPLACE FUNCTION hr.calculate_bonus(
    emp_id INTEGER,
    bonus_percentage DECIMAL DEFAULT 0.10
) RETURNS DECIMAL AS $$
DECLARE
    emp_salary DECIMAL;
    emp_rating INTEGER;
    calculated_bonus DECIMAL;
BEGIN
    -- Get employee salary and performance rating
    SELECT salary, performance_rating 
    INTO emp_salary, emp_rating
    FROM hr.employees 
    WHERE employee_id = emp_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Employee with ID % not found', emp_id;
    END IF;
    
    -- Calculate bonus based on performance rating
    calculated_bonus := emp_salary * bonus_percentage * emp_rating;
    
    RETURN calculated_bonus;
END;
$$ LANGUAGE plpgsql;

-- Procedure to update customer total spent
CREATE OR REPLACE FUNCTION sales.update_customer_totals(cust_id INTEGER)
RETURNS VOID AS $$
DECLARE
    order_count INTEGER;
    total_amount DECIMAL;
    latest_order DATE;
BEGIN
    -- Calculate totals
    SELECT 
        COUNT(*),
        COALESCE(SUM(total_amount), 0),
        MAX(order_date)
    INTO order_count, total_amount, latest_order
    FROM sales.orders
    WHERE customer_id = cust_id;
    
    -- Update customer record
    UPDATE sales.customers
    SET 
        total_orders = order_count,
        total_spent = total_amount,
        last_order_date = latest_order
    WHERE customer_id = cust_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get top selling products
CREATE OR REPLACE FUNCTION analytics.get_top_products(
    limit_count INTEGER DEFAULT 10,
    start_date DATE DEFAULT NULL,
    end_date DATE DEFAULT NULL
) RETURNS TABLE (
    product_name VARCHAR,
    sku VARCHAR,
    total_quantity BIGINT,
    total_revenue DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.product_name,
        p.sku,
        SUM(od.quantity) AS total_quantity,
        SUM(od.line_total) AS total_revenue
    FROM sales.products p
    JOIN sales.order_details od ON p.product_id = od.product_id
    JOIN sales.orders o ON od.order_id = o.order_id
    WHERE (start_date IS NULL OR o.order_date >= start_date)
      AND (end_date IS NULL OR o.order_date <= end_date)
    GROUP BY p.product_id, p.product_name, p.sku
    ORDER BY total_revenue DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Trigger function to update timestamps
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply timestamp triggers
CREATE TRIGGER tr_employees_updated
    BEFORE UPDATE ON hr.employees
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER tr_products_updated
    BEFORE UPDATE ON sales.products
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Trigger to update customer totals when orders change
CREATE OR REPLACE FUNCTION update_customer_totals_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM sales.update_customer_totals(OLD.customer_id);
        RETURN OLD;
    ELSE
        PERFORM sales.update_customer_totals(NEW.customer_id);
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_orders_customer_totals
    AFTER INSERT OR UPDATE OR DELETE ON sales.orders
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_totals_trigger();

-- =====================================================
-- COMPLEX QUERIES AND ANALYTICS
-- =====================================================

-- Common Table Expression (CTE) example - Sales by quarter
WITH quarterly_sales AS (
    SELECT 
        EXTRACT(YEAR FROM order_date) AS year,
        EXTRACT(QUARTER FROM order_date) AS quarter,
        SUM(total_amount) AS total_sales,
        COUNT(*) AS order_count,
        AVG(total_amount) AS avg_order_value
    FROM sales.orders
    WHERE order_status != 'Cancelled'
    GROUP BY EXTRACT(YEAR FROM order_date), EXTRACT(QUARTER FROM order_date)
),
growth_calculation AS (
    SELECT 
        year,
        quarter,
        total_sales,
        order_count,
        avg_order_value,
        LAG(total_sales) OVER (ORDER BY year, quarter) AS prev_quarter_sales,
        ROUND(
            ((total_sales - LAG(total_sales) OVER (ORDER BY year, quarter)) / 
             NULLIF(LAG(total_sales) OVER (ORDER BY year, quarter), 0)) * 100, 2
        ) AS growth_percentage
    FROM quarterly_sales
)
SELECT * FROM growth_calculation
ORDER BY year, quarter;

-- Window functions example - Employee ranking by salary within department
SELECT 
    e.first_name || ' ' || e.last_name AS employee_name,
    d.department_name,
    e.salary,
    RANK() OVER (PARTITION BY d.department_id ORDER BY e.salary DESC) AS salary_rank,
    DENSE_RANK() OVER (PARTITION BY d.department_id ORDER BY e.salary DESC) AS salary_dense_rank,
    ROW_NUMBER() OVER (PARTITION BY d.department_id ORDER BY e.salary DESC, e.hire_date) AS row_num,
    ROUND(AVG(e.salary) OVER (PARTITION BY d.department_id), 2) AS dept_avg_salary,
    e.salary - AVG(e.salary) OVER (PARTITION BY d.department_id) AS salary_diff_from_avg
FROM hr.employees e
JOIN hr.departments d ON e.department_id = d.department_id
ORDER BY d.department_name, e.salary DESC;

-- Recursive CTE example - Employee hierarchy
WITH RECURSIVE employee_hierarchy AS (
    -- Base case: employees without managers (top level)
    SELECT 
        employee_id,
        first_name,
        last_name,
        manager_id,
        1 AS level,
        first_name || ' ' || last_name AS hierarchy_path
    FROM hr.employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- Recursive case: employees with managers
    SELECT 
        e.employee_id,
        e.first_name,
        e.last_name,
        e.manager_id,
        eh.level + 1,
        eh.hierarchy_path || ' -> ' || e.first_name || ' ' || e.last_name
    FROM hr.employees e
    INNER JOIN employee_hierarchy eh ON e.manager_id = eh.employee_id
)
SELECT 
    employee_id,
    REPEAT('  ', level - 1) || first_name || ' ' || last_name AS indented_name,
    level,
    hierarchy_path
FROM employee_hierarchy
ORDER BY level, last_name, first_name;

-- Advanced aggregation with GROUPING SETS
SELECT 
    d.department_name,
    e.job_title,
    COUNT(*) AS employee_count,
    AVG(e.salary) AS avg_salary,
    MIN(e.salary) AS min_salary,
    MAX(e.salary) AS max_salary,
    CASE 
        WHEN GROUPING(d.department_name) = 1 THEN 'All Departments'
        ELSE d.department_name
    END AS dept_grouping,
    CASE 
        WHEN GROUPING(e.job_title) = 1 THEN 'All Titles'
        ELSE e.job_title
    END AS title_grouping
FROM hr.employees e
JOIN hr.departments d ON e.department_id = d.department_id
GROUP BY GROUPING SETS (
    (d.department_name, e.job_title),
    (d.department_name),
    (e.job_title),
    ()
)
ORDER BY dept_grouping, title_grouping;

-- =====================================================
-- PERFORMANCE AND MAINTENANCE QUERIES
-- =====================================================

-- Analyze table statistics (PostgreSQL)
ANALYZE hr.employees;
ANALYZE sales.orders;
ANALYZE sales.order_details;

-- Index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Table size information
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size
FROM pg_tables
WHERE schemaname IN ('hr', 'sales')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- =====================================================
-- DATA CLEANUP AND MAINTENANCE
-- =====================================================

-- Clean up test data (commented out for safety)
-- DELETE FROM sales.order_details WHERE order_id IN (SELECT order_id FROM sales.orders WHERE order_date < '2020-01-01');
-- DELETE FROM sales.orders WHERE order_date < '2020-01-01';

-- Update statistics
UPDATE sales.customers 
SET total_orders = (
    SELECT COUNT(*) 
    FROM sales.orders 
    WHERE orders.customer_id = customers.customer_id
);

-- Archive old records (example)
-- CREATE TABLE sales.orders_archive (LIKE sales.orders INCLUDING ALL);
-- INSERT INTO sales.orders_archive SELECT * FROM sales.orders WHERE order_date < '2020-01-01';

-- =====================================================
-- SAMPLE REPORTING QUERIES
-- =====================================================

-- Monthly sales report
SELECT 
    TO_CHAR(order_date, 'YYYY-MM') AS month,
    COUNT(*) AS total_orders,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_order_value,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM sales.orders
WHERE order_status != 'Cancelled'
  AND order_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY TO_CHAR(order_date, 'YYYY-MM')
ORDER BY month;

-- Customer segmentation analysis
SELECT 
    customer_type,
    COUNT(*) AS customer_count,
    AVG(total_spent) AS avg_total_spent,
    SUM(total_spent) AS total_revenue,
    AVG(total_orders) AS avg_orders_per_customer
FROM sales.customers
GROUP BY customer_type
ORDER BY total_revenue DESC;

-- Employee performance dashboard
SELECT 
    d.department_name,
    COUNT(e.employee_id) AS employee_count,
    AVG(e.salary) AS avg_salary,
    AVG(e.performance_rating) AS avg_performance,
    COUNT(CASE WHEN e.performance_rating >= 4 THEN 1 END) AS high_performers
FROM hr.employees e
JOIN hr.departments d ON e.department_id = d.department_id
GROUP BY d.department_name
ORDER BY avg_performance DESC;

-- End of SQL sample file 