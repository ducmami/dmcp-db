def get_demo_dsn() -> str:
    return ":memory:"


def get_demo_init_script() -> str:
    return """
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    department TEXT,
    salary INTEGER
);

CREATE TABLE departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    manager_id INTEGER,
    FOREIGN KEY (manager_id) REFERENCES employees(id)
);

INSERT INTO departments (id, name, manager_id) VALUES
    (1, 'Engineering', NULL),
    (2, 'Sales', NULL),
    (3, 'Marketing', NULL);

INSERT INTO employees (id, first_name, last_name, email, department, salary) VALUES
    (1, 'John', 'Doe', 'john.doe@example.com', 'Engineering', 120000),
    (2, 'Jane', 'Smith', 'jane.smith@example.com', 'Engineering', 115000),
    (3, 'Bob', 'Johnson', 'bob.johnson@example.com', 'Sales', 95000),
    (4, 'Alice', 'Williams', 'alice.williams@example.com', 'Marketing', 85000),
    (5, 'Charlie', 'Brown', 'charlie.brown@example.com', 'Engineering', 105000);

UPDATE departments SET manager_id = 1 WHERE id = 1;
UPDATE departments SET manager_id = 3 WHERE id = 2;
UPDATE departments SET manager_id = 4 WHERE id = 3;
"""

