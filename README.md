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
