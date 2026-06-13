# unified-data-pipeline
Centralizes and automates regional sales, customer, and product data into a cloud-native platform. This repository replaces fragmented manual workflows with scalable, automated pipelines to eliminate data silos, enforce data quality, and deliver reliable, near-real-time business intelligence for strategic decision-making.

A full validation of the raw data ingested into MotherDuck through Airbyte was achieved. 
Here it was ensured that the raw layer was complete, consistent, and ready for transformation into the validated (Silver) layer.

What the Script Does
The script connects to MotherDuck using a secure token and performs the following checks:

Record Count Validation  
Confirms that all raw tables (sales_transactions, customers, products) were fully ingested.

Null Checks  
Ensures that key identifier fields (order_id, customer_id, product_id) contain no null values.

Duplicate Checks  
Verifies that order_id and customer_id values are unique.

Foreign Key Integrity

Validates customer_id against raw.customers

Validates product_id against validated.products (updated after Week 2 corrections)

Schema Profiling  
Lists all columns in the raw sales table and highlights unexpected or extra fields (e.g., shipping details, location fields, Airbyte metadata).

Value Range Profiling  
Checks the minimum and maximum values for quantity, sales, and profit.

Why the Script Was Updated
During validation, it was discovered that the raw.products table was not a true product dimension.
To fix this, a correct product dimension was rebuilt using distinct product attributes from raw.sales_transactions and stored as:


validated.products
The Python script was updated to validate product_id against this corrected table.
After the update, the script correctly reports:


0 broken_product_ids
How This Script Fits Into the Pipeline
This script ensures that:

The raw layer is clean

The validated layer is aligned

Downstream transformations can be built on reliable data


# Full pipeline setup

# Automated Data Ingestion and Analytics Pipeline

## Pipeline Architecture (Medallion Pattern)

Medallion Data Boundaries: Explicit breakdowns of Bronze (Raw), Silver (Validated), and Gold (Analytics) structural schemas within MotherDuck.

[ Google Drive Source Files ]
│
▼ (Airbyte Sync: Full Refresh and Overwrite)
┌────────────────────────────────────────────────────────┐
│ BRONZE LAYER (raw schema)                              │
│ ───                                                    │
│  • Extracted rows stored entirely as VARCHAR strings    │
│  • Includes raw audit tracks (_airbyte_raw_id)         │
└────────────────────────┬───────────────────────────────┘
│
▼ (Data Validation and Layout Clean-up)
┌────────────────────────────────────────────────────────┐
│ SILVER LAYER (validated schema)                        │
│ ───                                                    │
│  • Cleaned product table with aligned identifiers      │
│  • Referential constraint checking                     │
└────────────────────────┬───────────────────────────────┘
│
▼ (Python Automation: Explicit Type Casting)
┌────────────────────────────────────────────────────────┐
│ GOLD LAYER (analytics schema)                          │
│ ───                                                    │
│  • analytics.sales_summary  ──► [Converted to DATE and DECIMAL]
│  • analytics.top_products    ──► [Top 10 Performance View]
└────────────────────────────────────────────────────────┘


Bronze Layer (raw schema): This is our landing pad. Airbyte pulls data straight from our files (Google Drive) and drops it here exactly as it looks at the source. To prevent ingestion crashes, everything arrives as text characters (VARCHAR).

Silver Layer (validated schema): This is the cleaning station. Here, duplicate records are removed and bad formatting is fixed. This is where our keys are accurately aligned.

Gold Layer (analytics schema): This is the presentation room. We use SQL views here to cast text columns into proper mathematical types (INTEGER, DATE, DECIMAL) and run aggregates so BI tools can build charts instantly.

Ingestion Metadata Mapping: Documentation on Airbyte tracking metadata components (_airbyte_raw_id, _airbyte_extracted_at, _airbyte_meta) preserved within your database for complete row lineage.

## Tools and Technologies Used
* **Storage Source:** Google Drive (CSV file stores containing sales transactions, user listings, and inventory catalogs).
* **Data Integration (ELT):** Airbyte Cloud (handles cloud extraction, schema tracking, and target loading syncs).
* **Data Warehouse:** MotherDuck / DuckDB (handles cloud computation storage and rapid SQL processing).
* **Pipeline Code and Automation:** Python 3 (executes schema validation queries, checks database integrity, and builds virtual views).

## Core Production Data Dictionary

### Table: raw.sales_transactions
* `order_id` (VARCHAR): Unique order reference string (Primary Key).
* `customer_id` (VARCHAR): Linked customer account identification key.
* `product_id` (VARCHAR): Linked inventory catalogue item identification key.
* `sales` (VARCHAR): Raw text representation of order revenue.
* `quantity` (VARCHAR): Raw text representation of unit items shipped.

### Generated Analytical View: analytics.top_products
* `product_id` (VARCHAR): Validated inventory item reference.
* `product_name` (VARCHAR): Clear display string pulled from the catalog layer.
* `total_sales` (DECIMAL): Computed revenue tracking matching clean accounting decimal limits.
* `total_quantity` (INTEGER): Clean whole-number sum of shipped merchandise.

## Sample Production Queries

### 1. View Schema Verification
Ran this statement inside MotherDuck to verify that our Python automation script successfully created the metrics with their proper data types:
```sql

DESCRIBE analytics.top_products;

## Issues Encountered That Were Fixed

### 1. Top Products View Returned 0 Rows
* **What happened:** When I first wrote the query joining raw.sales_transactions with raw.products, the view ran fine but displayed completely empty rows.
* **The Cause:** A detailed root-cause narrative showed an alphanumeric product ID layout discrepancy across the layers. The raw transaction tables mapped records using dash-separated strings, whereas the raw product catalog file relied on an incompatible formatting layout, which chronicles why the view originally yielded 0 rows.
* **The Fix:** In the Silver layer, I changed the query to join with validated.products instead of the raw version. The IDs matched instantly, and the data populated perfectly.

### 2. Python Code Crashed with a MotherDuck Syntax Error
* **What happened:** My terminal threw a confusing Parser Error: syntax error at or near "#" exception.
* **The Cause:** I had typed a descriptive Python comment character (# <--- CHANGED THIS LINE) inside my triple-quoted SQL string. Python didn't read it as a comment; it sent the raw # symbol straight to MotherDuck, which didn't know how to read it.
* **The Fix:** I deleted the inline comment text out of the raw SQL string, and the database script compiled perfectly.

## Sample Production Queries

### 1. View Schema Verification
Run this statement inside MotherDuck to verify that our Python automation script successfully created the metrics with their proper data types:
```sql
DESCRIBE analytics.top_products;

Cloud Data Integration vs. Traditional ETL
The Old Way (Traditional ETL - Extract, Transform, Load): In older environments, specialized data servers transformed data before it reached the warehouse. If a single data row had a broken data type format (like a word inside a salary number column), the entire ingestion tool would crash mid-run, blocking updates until an engineer manually adjusted it.

The Modern Cloud Way (ELT - Extract, Load, Transform): With modern cloud tools like Airbyte and MotherDuck, we switch the order to ELT. We extract and load the data as raw text strings into the warehouse first (Bronze Layer). This guarantees our daily syncs never crash due to mismatched data types. Once the data safely lands inside the warehouse, we use flexible SQL script commands inside Python to convert those data types and model the tables cleanly (Gold Layer).

By adopting ELT, our data pipeline stays highly reliable, and we perform all the complex data heavy-lifting directly inside our cloud database instead of wasting processing power elsewhere
