import os
import duckdb
from dotenv import load_dotenv

# -------------------------------------------------------------
# Week 2 Validation Script
# This script connects to MotherDuck and runs a set of checks
# to make sure the data loaded by Airbyte looks correct.
# The goal is to validate the raw tables before moving on to
# any transformations or analytics work.
# -------------------------------------------------------------

# Load the MotherDuck token from the .env file
load_dotenv()
token = os.getenv("MOTHERDUCK_TOKEN")

if not token:
    raise ValueError("MotherDuck token is missing. Make sure the .env file is set up correctly.")

# Connect to MotherDuck using the token
conn = duckdb.connect(f"md:?motherduck_token={token}")
print("Connected to MotherDuck.")

# Switch to the project database
conn.execute("USE retail_data;")

# -------------------------------------------------------------
# Record Count Check
# -------------------------------------------------------------
print("\n--- Record Count Check ---")
print(conn.execute("""
SELECT 'sales_transactions' AS table_name, COUNT(*) AS row_count FROM raw.sales_transactions
UNION ALL
SELECT 'customers', COUNT(*) FROM raw.customers
UNION ALL
SELECT 'products', COUNT(*) FROM raw.products;
""").fetchdf())

# -------------------------------------------------------------
# Null Value Check
# -------------------------------------------------------------
print("\n--- Null Value Check ---")
print(conn.execute("""
SELECT 
    SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) AS null_order_ids,
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customer_ids,
    SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) AS null_product_ids
FROM raw.sales_transactions;
""").fetchdf())

# -------------------------------------------------------------
# Duplicate Check
# -------------------------------------------------------------
print("\n--- Duplicate Check ---")

print("\nDuplicate order_id values:")
print(conn.execute("""
SELECT order_id, COUNT(*) 
FROM raw.sales_transactions
GROUP BY order_id
HAVING COUNT(*) > 1;
""").fetchdf())

print("\nDuplicate customer_id values:")
print(conn.execute("""
SELECT customer_id, COUNT(*) 
FROM raw.customers
GROUP BY customer_id
HAVING COUNT(*) > 1;
""").fetchdf())

# -------------------------------------------------------------
# Foreign Key Check (UPDATED TO USE validated.products)
# -------------------------------------------------------------
print("\n--- Foreign Key Check ---")

print("\nMissing customer_id references:")
print(conn.execute("""
SELECT COUNT(*) AS broken_customer_ids
FROM raw.sales_transactions
WHERE customer_id NOT IN (SELECT customer_id FROM raw.customers);
""").fetchdf())

print("\nMissing product_id references (validated):")
print(conn.execute("""
SELECT COUNT(*) AS broken_product_ids
FROM raw.sales_transactions
WHERE product_id NOT IN (SELECT product_id FROM validated.products);
""").fetchdf())

# -------------------------------------------------------------
# Data Type Review
# -------------------------------------------------------------
print("\n--- Data Type Review ---")
print(conn.execute("""
SELECT 
    column_name, 
    data_type 
FROM information_schema.columns
WHERE table_schema = 'raw'
  AND table_name = 'sales_transactions';
""").fetchdf())

# -------------------------------------------------------------
# Column Mapping Review
# -------------------------------------------------------------
print("\n--- Column Mapping Review ---")

expected_columns = [
    'order_id', 'customer_id', 'product_id', 'product_name',
    'category', 'region', 'segment', 'quantity', 'sales', 'profit'
]

actual_columns = conn.execute("""
SELECT column_name 
FROM information_schema.columns
WHERE table_schema = 'raw'
  AND table_name = 'sales_transactions';
""").fetchdf()['column_name'].tolist()

missing = [col for col in expected_columns if col not in actual_columns]
extra = [col for col in actual_columns if col not in expected_columns]

print("Missing columns:", missing)
print("Unexpected columns:", extra)

# -------------------------------------------------------------
# Value Range Profiling
# -------------------------------------------------------------
# In this section, we check the minimum and maximum values for
# quantity, sales, and profit. This helps us confirm that the
# numeric fields fall within expected business ranges and that
# there are no extreme outliers or incorrect values.
print("\n--- Value Range Profiling ---")

print("\nQuantity Range:")
print(conn.execute("""
SELECT MIN(quantity) AS min_qty, MAX(quantity) AS max_qty
FROM raw.sales_transactions;
""").fetchdf())

print("\nSales Range:")
print(conn.execute("""
SELECT MIN(sales) AS min_sales, MAX(sales) AS max_sales
FROM raw.sales_transactions;
""").fetchdf())

print("\nProfit Range:")
print(conn.execute("""
SELECT MIN(profit) AS min_profit, MAX(profit) AS max_profit
FROM raw.sales_transactions;
""").fetchdf())


# -------------------------------------------------------------
# Create Analytical Views (sales_summary & top_products)
# -------------------------------------------------------------
# After validating the raw and validated layers, we now create
# two analytical SQL views. These views will be used for reporting
# and analysis in later stages of the pipeline.
#
# 1. sales_summary  → aggregates daily sales metrics
# 2. top_products   → identifies the highest‑performing products
#
# These views are created inside the 'analytics' schema so they
# can be easily queried from BI tools or dashboards.
print("\n--- Creating Analytical Views ---")

# Ensure the analytics schema exists before creating views
conn.execute("CREATE SCHEMA IF NOT EXISTS analytics;")

# Create the daily sales summary view
# Note: Using CAST because raw fields are currently stored as text (VARCHAR)
conn.execute("""
CREATE OR REPLACE VIEW analytics.sales_summary AS
SELECT
    CAST(order_date AS DATE) AS order_date,
    SUM(CAST(quantity AS INT)) AS total_quantity,
    SUM(CAST(sales AS DECIMAL(18,2))) AS total_sales,
    SUM(CAST(profit AS DECIMAL(18,2))) AS total_profit
FROM raw.sales_transactions
GROUP BY order_date
ORDER BY order_date;
""")
print("View created: analytics.sales_summary")

# Create the top products view
conn.execute("""
CREATE OR REPLACE VIEW analytics.top_products AS
SELECT
    st.product_id,
    p.product_name,
    SUM(CAST(st.sales AS DECIMAL(18,2))) AS total_sales,
    SUM(CAST(st.quantity AS INT)) AS total_quantity,
    SUM(CAST(st.profit AS DECIMAL(18,2))) AS total_profit
FROM raw.sales_transactions st
JOIN validated.products p
    ON st.product_id = p.product_id
GROUP BY st.product_id, p.product_name
ORDER BY total_sales DESC
LIMIT 10;
""")
print("View created: analytics.top_products")


# -------------------------------------------------------------
# Close the connection
# -------------------------------------------------------------
# Once all validation checks and view creation steps are complete,
# we safely close the connection to MotherDuck.
conn.close()
print("\nValidation complete. Connection closed.")