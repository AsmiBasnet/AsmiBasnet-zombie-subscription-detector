import sqlite3
import csv
import os

DB_NAME = "zombie_detector.db"
TABLES = ["dim_users", "dim_merchants", "dim_subscriptions", "fact_transactions"]

DETECTION_QUERY = """
WITH raw_payments AS (
    SELECT 
        user_id,
        merchant_id,
        amount,
        transaction_date,
        CAST(JULIANDAY(transaction_date) - JULIANDAY(
            LAG(transaction_date, 1) OVER (
                PARTITION BY user_id, merchant_id  
                ORDER BY transaction_date     
            )
        ) AS INTEGER) AS days_since_last_payment,
        CAST(JULIANDAY(
            LEAD(transaction_date, 1) OVER (
                PARTITION BY user_id, merchant_id  
                ORDER BY transaction_date     
            )
        ) - JULIANDAY(transaction_date) AS INTEGER) AS days_until_next_payment
    FROM fact_transactions
    WHERE status = 'settled'
),
recurring_payments AS (
    SELECT 
        user_id,
        merchant_id,
        amount,
        transaction_date,
        FIRST_VALUE(amount) OVER (
            PARTITION BY user_id, merchant_id
            ORDER BY transaction_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS start_amount,
        LAST_VALUE(amount) OVER (
            PARTITION BY user_id, merchant_id
            ORDER BY transaction_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS current_amount
    FROM raw_payments
    WHERE 
        ((days_since_last_payment BETWEEN 27 AND 33) OR (days_until_next_payment BETWEEN 27 AND 33))
        AND ROUND(amount - CAST(amount AS INTEGER), 2) IN (0.99, 0.49)
),
agg_features AS (
    SELECT 
        user_id,
        merchant_id,
        MIN(transaction_date) AS subscription_start,
        MAX(transaction_date) AS subscription_latest,
        CAST(JULIANDAY(MAX(transaction_date)) - JULIANDAY(MIN(transaction_date)) AS INTEGER) AS tenure_days,
        start_amount,
        current_amount,
        ROUND(current_amount - start_amount, 2) AS price_creep,
        COUNT(*) AS total_payments
    FROM recurring_payments
    GROUP BY user_id, merchant_id
)
SELECT 
    f.user_id,
    f.merchant_id,
    f.subscription_start,
    f.subscription_latest,
    f.tenure_days,
    f.start_amount,
    f.current_amount,
    f.price_creep,
    f.total_payments,
    CASE WHEN f.price_creep > 0 THEN 1 ELSE 0 END AS is_zombie_price_creep,
    CASE WHEN f.tenure_days > 360 THEN 1 ELSE 0 END AS is_zombie_long_tenure,
    CASE WHEN f.price_creep > 0 OR f.tenure_days > 360 THEN 1 ELSE 0 END AS is_zombie_candidate
FROM agg_features f;
"""

def export_to_csv():
    if not os.path.exists(DB_NAME):
        print(f"Error: {DB_NAME} not found. Please run generate_data.py first.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Export static tables
    for table_name in TABLES:
        cursor.execute(f"SELECT * FROM {table_name};")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        csv_filename = f"{table_name}.csv"
        with open(csv_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)
            
        print(f"Successfully exported {table_name} to {csv_filename} ({len(rows)} rows)")
        
    # 2. Export detected subscriptions and metrics
    cursor.execute(DETECTION_QUERY)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    csv_filename = "detected_subscriptions.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
        
    print(f"Successfully exported detected subscriptions to {csv_filename} ({len(rows)} rows)")
        
    conn.close()

if __name__ == "__main__":
    export_to_csv()
