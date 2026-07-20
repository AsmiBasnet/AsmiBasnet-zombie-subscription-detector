-- Phase 2: Step 3 - Group and Aggregate Subscription Series
WITH raw_payments AS (
    SELECT 
        user_id,
        merchant_id,
        amount,
        transaction_date,
        -- Get the interval since last payment (LAG)
        CAST(JULIANDAY(transaction_date) - JULIANDAY(
            LAG(transaction_date, 1) OVER (
                PARTITION BY user_id, merchant_id  
                ORDER BY transaction_date     
            )
        ) AS INTEGER) AS days_since_last_payment,
        -- Get the interval until next payment (LEAD)
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
    -- Retain transactions that are part of a regular 30-day billing cycle.
    -- The first payment has days_since_last_payment IS NULL but days_until_next_payment between 27 and 33.
    -- The last payment has days_until_next_payment IS NULL but days_since_last_payment between 27 and 33.
    -- A middle payment has both.
    -- One-off payments will have neither of these.
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
)
SELECT 
    user_id,
    merchant_id,
    MIN(transaction_date) AS subscription_start,
    MAX(transaction_date) AS subscription_latest,
    -- Calculate active tenure in days
    CAST(JULIANDAY(MAX(transaction_date)) - JULIANDAY(MIN(transaction_date)) AS INTEGER) AS tenure_days,
    start_amount,
    current_amount,
    -- Price Creep is the growth in subscription price over time
    ROUND(current_amount - start_amount, 2) AS price_creep,
    COUNT(*) AS total_payments
FROM recurring_payments
GROUP BY user_id, merchant_id;
