# Zombie Subscription Detector

An end-to-end data analytics and data science project designed to detect recurring billing subscriptions from raw transaction logs and identify "zombie" (forgotten or price-creeping) subscriptions.

## Project Structure
- `Zombie_Subscription_Detector_PID.md`: Project Initiation Document (PID) detailing scope and methodology.
- `generate_data.py`: Synthetic transaction-level data generator that creates the relational SQLite database.
- `export_csv.py`: Helper script to dump SQLite database tables to CSV format for visual analysis.
- `detect_zombies.sql`: SQL query using `LAG` and `FIRST_VALUE`/`LAST_VALUE` window functions to identify and aggregate subscriptions.
- `query_db.py`: Quick runner to test SQL queries against the local database directly in the terminal.
- `validate_logic.py`: Data Science validation script that evaluates our SQL-based rules against ground-truth labels and calculates metrics.

## How to Get Started
1. Run the data generator to create the database:
   ```bash
   python generate_data.py
   ```
2. Run the validation harness to see how our rules perform:
   ```bash
   python validate_logic.py
   ```

## Phase 2: Detection & Validation Metrics
Here is how our optimized rules (using dual-direction gap checks and psychological pricing filters) performed on 855 active subscriptions against the ground truth:

| Strategy | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: |
| **A: Price Creep Only** (`creep > 0`) | **100.00%** | 46.04% | **63.05%** |
| **B: Long Tenure Only** (`tenure > 360 days`) | 24.77% | 80.69% | 37.91% |
| **C: Combined** (`creep > 0` OR `tenure > 360 days`) | 26.67% | **89.11%** | 41.05% |
