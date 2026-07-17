# Zombie Subscription Detector

An end-to-end data analytics and data science project designed to detect recurring billing subscriptions from raw transaction logs and identify "zombie" (forgotten or price-creeping) subscriptions.

## Project Structure
- `Zombie_Subscription_Detector_PID.md`: Project Initiation Document (PID) detailing scope and methodology.
- `generate_data.py`: Synthetic transaction-level data generator that creates the relational SQLite database.
- `read_docx.py`: Utility script to parse document contents.
- `.gitignore`: Specifying excluded local database files.

## How to Get Started
1. Run the data generator to create the database:
   ```bash
   python generate_data.py
   ```
2. This creates `zombie_detector.db` with user, merchant, subscription, and transaction tables.
