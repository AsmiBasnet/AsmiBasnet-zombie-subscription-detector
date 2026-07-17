import sqlite3
import random
import os
from datetime import datetime, timedelta

# Configuration & Seed for reproducibility
random.seed(42)
DB_NAME = "zombie_detector.db"
START_SIMULATION = datetime(2023, 1, 1)
END_SIMULATION = datetime(2026, 7, 1)

# Synthetic data pools
FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth",
               "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

MERCHANT_TEMPLATES = [
    {"name": "NetStream Premium", "category": "Streaming", "base_price": 15.99},
    {"name": "SoniCloud Music", "category": "Streaming", "base_price": 9.99},
    {"name": "FlexFitness Gym", "category": "Fitness", "base_price": 44.99},
    {"name": "AdobeCreative Cloud", "category": "Software", "base_price": 54.99},
    {"name": "Daily Chronicle", "category": "News", "base_price": 4.99},
    {"name": "ChefBox Meal Delivery", "category": "Meal Kit", "base_price": 69.99},
    {"name": "CloudSpace Storage", "category": "Software", "base_price": 2.99},
    {"name": "CodeAcademy Learn", "category": "Software", "base_price": 29.99},
    {"name": "CleanWater Filters", "category": "Home", "base_price": 19.99},
    {"name": "GamePass Central", "category": "Streaming", "base_price": 14.99}
]

def generate_random_date(start, end):
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)

def create_database():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Removed existing database: {DB_NAME}")
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE dim_users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        signup_date DATE NOT NULL
    );
    """)
    
    # 2. Merchants Table
    cursor.execute("""
    CREATE TABLE dim_merchants (
        merchant_id INTEGER PRIMARY KEY AUTOINCREMENT,
        merchant_name TEXT NOT NULL,
        category TEXT NOT NULL
    );
    """)
    
    # 3. Subscriptions (Ground Truth) Table
    cursor.execute("""
    CREATE TABLE dim_subscriptions (
        subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        merchant_id INTEGER NOT NULL,
        billing_amount REAL NOT NULL,
        billing_frequency TEXT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE,
        is_zombie_ground_truth INTEGER NOT NULL,
        has_price_creep INTEGER NOT NULL,
        FOREIGN KEY(user_id) REFERENCES dim_users(user_id),
        FOREIGN KEY(merchant_id) REFERENCES dim_merchants(merchant_id)
    );
    """)
    
    # 4. Transactions Table
    cursor.execute("""
    CREATE TABLE fact_transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        merchant_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        transaction_date DATE NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES dim_users(user_id),
        FOREIGN KEY(merchant_id) REFERENCES dim_merchants(merchant_id)
    );
    """)
    
    conn.commit()
    return conn

def populate_static_data(conn):
    cursor = conn.cursor()
    
    # Generate 500 users
    users = []
    for i in range(1, 501):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}{random.randint(10, 99)}@example.com"
        signup_date = generate_random_date(START_SIMULATION, END_SIMULATION - timedelta(days=180))
        users.append((name, email, signup_date.strftime("%Y-%m-%d")))
        
    cursor.executemany("INSERT INTO dim_users (name, email, signup_date) VALUES (?, ?, ?);", users)
    
    # Insert merchants
    merchants = [(m["name"], m["category"]) for m in MERCHANT_TEMPLATES]
    cursor.executemany("INSERT INTO dim_merchants (merchant_name, category) VALUES (?, ?);", merchants)
    
    conn.commit()
    print(f"Populated 500 users and {len(MERCHANT_TEMPLATES)} merchants.")

def populate_subscriptions_and_transactions(conn):
    cursor = conn.cursor()
    
    # Retrieve user IDs and signup dates
    cursor.execute("SELECT user_id, signup_date FROM dim_users;")
    users_data = cursor.fetchall()
    
    # Retrieve merchant data
    cursor.execute("SELECT merchant_id, merchant_name, category FROM dim_merchants;")
    merchants_data = cursor.fetchall()
    
    subscriptions_to_insert = []
    transactions_to_insert = []
    
    for user_id, signup_date_str in users_data:
        signup_date = datetime.strptime(signup_date_str, "%Y-%m-%d")
        
        # Each user has 1 to 4 subscriptions
        num_subs = random.randint(1, 4)
        selected_merchants = random.sample(merchants_data, num_subs)
        
        for merchant_id, name, category in selected_merchants:
            # Subscription start date is at or after user signup date
            start_date = signup_date + timedelta(days=random.randint(0, 30))
            if start_date > END_SIMULATION:
                continue
                
            # Base price template
            base_price = next(m["base_price"] for m in MERCHANT_TEMPLATES if m["name"] == name)
            
            # Determine if this subscription is cancelled
            is_cancelled = random.random() < 0.35
            if is_cancelled:
                # Cancelled after some active months
                active_days = random.randint(60, 500)
                end_date = start_date + timedelta(days=active_days)
                if end_date > END_SIMULATION:
                    end_date = None
            else:
                end_date = None
                
            # Determine if this is a "zombie" subscription (ground truth)
            # Conditions: active (no end_date), long-running (> 6 months), and user "forgot" it
            # We flag ~20% of active subscriptions as zombies
            is_zombie = 0
            has_price_creep = 0
            
            if end_date is None:
                tenure_days = (END_SIMULATION - start_date).days
                if tenure_days > 180: # Long-running
                    if random.random() < 0.25: # Zombie rate
                        is_zombie = 1
                        # Half of the zombies have price creep, half are flat
                        if random.random() < 0.50:
                            has_price_creep = 1
            
            subscriptions_to_insert.append((
                user_id,
                merchant_id,
                base_price,
                "monthly",
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d") if end_date else None,
                is_zombie,
                has_price_creep
            ))
            
            # Generate the transaction history for this subscription
            current_date = start_date
            current_price = base_price
            price_change_counter = 0
            
            limit_date = end_date if end_date else END_SIMULATION
            
            while current_date <= limit_date:
                # Price Creep: if marked, increase price by $1 to $2 every 6 months
                if has_price_creep:
                    months_active = (current_date - start_date).days // 30
                    if months_active > 0 and months_active % 6 == 0 and price_change_counter < (months_active // 6):
                        current_price += random.choice([1.00, 1.50, 2.00])
                        price_change_counter += 1
                
                # Transaction status (mostly settled, occasionally failed)
                status = "settled"
                if random.random() < 0.02: # 2% failure rate
                    status = "failed"
                    
                # Add main monthly transaction
                transactions_to_insert.append((
                    user_id,
                    merchant_id,
                    round(current_price, 2),
                    current_date.strftime("%Y-%m-%d"),
                    status
                ))
                
                # Sometimes user performs a one-off charge (non-subscription noise) at same merchant
                if random.random() < 0.05: # 5% chance of extra purchase
                    extra_date = current_date + timedelta(days=random.randint(1, 20))
                    if extra_date <= limit_date:
                        transactions_to_insert.append((
                            user_id,
                            merchant_id,
                            round(random.uniform(5.00, 30.00), 2),
                            extra_date.strftime("%Y-%m-%d"),
                            "settled"
                        ))
                
                # Move to next monthly billing cycle (approx 30 days)
                current_date += timedelta(days=30)
                
    # Batch insertions
    cursor.executemany("""
        INSERT INTO dim_subscriptions (
            user_id, merchant_id, billing_amount, billing_frequency, start_date, end_date, is_zombie_ground_truth, has_price_creep
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, subscriptions_to_insert)
    
    cursor.executemany("""
        INSERT INTO fact_transactions (
            user_id, merchant_id, amount, transaction_date, status
        ) VALUES (?, ?, ?, ?, ?);
    """, transactions_to_insert)
    
    conn.commit()
    print(f"Generated {len(subscriptions_to_insert)} subscriptions.")
    print(f"Generated {len(transactions_to_insert)} transaction records.")

def verify_data(conn):
    cursor = conn.cursor()
    
    print("\n--- Verification Summary ---")
    cursor.execute("SELECT COUNT(*) FROM dim_users;")
    print(f"Total Users: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM dim_merchants;")
    print(f"Total Merchants: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM dim_subscriptions;")
    print(f"Total Subscriptions: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*), SUM(is_zombie_ground_truth), SUM(has_price_creep) FROM dim_subscriptions;")
    total, zombies, creep = cursor.fetchone()
    print(f"Active Subscriptions: {total}")
    print(f"Ground Truth Zombie Subscriptions: {zombies} ({(zombies/total)*100:.1f}%)")
    print(f"Price Creep Subscriptions: {creep} ({(creep/total)*100:.1f}%)")
    
    cursor.execute("SELECT COUNT(*) FROM fact_transactions;")
    print(f"Total Transactions: {cursor.fetchone()[0]}")
    
    print("\nSample Users:")
    cursor.execute("SELECT * FROM dim_users LIMIT 3;")
    for row in cursor.fetchall():
        print(row)
        
    print("\nSample Subscriptions (showing ground truth zombies first):")
    cursor.execute("SELECT * FROM dim_subscriptions ORDER BY is_zombie_ground_truth DESC LIMIT 5;")
    for row in cursor.fetchall():
        print(row)

def main():
    print("Starting synthetic data generation...")
    conn = create_database()
    populate_static_data(conn)
    populate_subscriptions_and_transactions(conn)
    verify_data(conn)
    conn.close()
    print("\nData generation complete! Database 'zombie_detector.db' is ready.")

if __name__ == "__main__":
    main()
