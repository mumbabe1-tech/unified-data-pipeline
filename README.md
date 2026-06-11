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
