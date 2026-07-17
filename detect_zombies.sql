-- Phase 2: Recurring Transaction Gap Analysis
-- Let's calculate the date difference between consecutive transactions
-- for the same user at the same merchant.

SELECT 
    user_id,
    merchant_id,
    amount,
    transaction_date,
    -- Step 1: Use LAG() to get the date of the previous transaction.
    -- Hint: You need to PARTITION BY the unique identifiers that define a specific subscription relationship,
    -- and ORDER BY the column that ensures they are in chronological order.
    LAG(transaction_date, 1) OVER (
        PARTITION BY ______  -- Fill in the columns to group by (separate by comma)
        ORDER BY ______      -- Fill in the column to sort by
    ) AS previous_transaction_date
FROM fact_transactions
WHERE status = 'settled'
LIMIT 10;
