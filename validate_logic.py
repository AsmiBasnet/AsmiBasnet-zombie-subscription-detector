import sqlite3

DB_NAME = "zombie_detector.db"

def calculate_metrics(tp, fp, fn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    return precision, recall, f1

def run_validation():
    if not sqlite3:
        print("sqlite3 library not found.")
        return
        
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # This lets us access columns by name like row['column_name']
    cursor = conn.cursor()
    
    query = """
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
            ROUND(current_amount - start_amount, 2) AS price_creep
        FROM recurring_payments
        GROUP BY user_id, merchant_id
    )
    SELECT 
        f.user_id,
        f.merchant_id,
        f.tenure_days,
        f.price_creep,
        s.is_zombie_ground_truth,
        s.end_date
    FROM agg_features f
    JOIN dim_subscriptions s 
      ON f.user_id = s.user_id 
     AND f.merchant_id = s.merchant_id;
    """
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except Exception as e:
        print(f"Error executing query: {e}")
        conn.close()
        return

    # Filter out subscriptions that were cancelled in the past
    # Active subscriptions have end_date IS NULL
    active_rows = [row for row in rows if row['end_date'] is None or row['end_date'] == '']
    
    print(f"Evaluating model on {len(active_rows)} active subscriptions...")
    
    strategies = {
        "Strategy A: Price Creep Only (creep > 0)": lambda r: r['price_creep'] > 0,
        "Strategy B1: Long Tenure (tenure > 360 days)": lambda r: r['tenure_days'] > 360,
        "Strategy B2: Long Tenure (tenure > 180 days)": lambda r: r['tenure_days'] > 180,
        "Strategy C1: Combined (creep > 0 OR tenure > 360 days)": lambda r: (r['price_creep'] > 0) or (r['tenure_days'] > 360),
        "Strategy C2: Combined (creep > 0 OR tenure > 180 days)": lambda r: (r['price_creep'] > 0) or (r['tenure_days'] > 180)
    }
    
    for name, rule in strategies.items():
        tp = fp = fn = tn = 0
        for row in active_rows:
            actual = row['is_zombie_ground_truth']
            predicted = 1 if rule(row) else 0
            
            if predicted == 1 and actual == 1:
                tp += 1
            elif predicted == 1 and actual == 0:
                fp += 1
            elif predicted == 0 and actual == 1:
                fn += 1
            else:
                tn += 1
                
        precision, recall, f1 = calculate_metrics(tp, fp, fn)
        print(f"\n=== {name} ===")
        print(f"  True Positives (TP): {tp} | False Positives (FP): {fp}")
        print(f"  False Negatives (FN): {fn} | True Negatives (TN): {tn}")
        print(f"  Precision: {precision:.2%}")
        print(f"  Recall:    {recall:.2%}")
        print(f"  F1-Score:  {f1:.2%}")
        
    conn.close()

if __name__ == "__main__":
    run_validation()
