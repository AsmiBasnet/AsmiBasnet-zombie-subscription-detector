import sqlite3
import os
import sys

DB_NAME = "zombie_detector.db"

def run_query(sql_file_path):
    if not os.path.exists(sql_file_path):
        print(f"Error: SQL file '{sql_file_path}' not found.")
        return
        
    if not os.path.exists(DB_NAME):
        print(f"Error: Database '{DB_NAME}' not found. Please run generate_data.py first.")
        return

    with open(sql_file_path, 'r', encoding='utf-8') as f:
        query = f.read().strip()
        
    if not query:
        print(f"Error: SQL file '{sql_file_path}' is empty.")
        return
        
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Execute query
        cursor.execute(query)
        
        # Fetch columns and rows
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchmany(30)  # Limit output to 30 rows for readability
        total_rows = len(cursor.fetchall()) + len(rows) # Get total rows
        
        if not rows:
            print("Query returned 0 results.")
            return
            
        # Determine column widths
        widths = [len(col) for col in columns]
        for row in rows:
            for idx, val in enumerate(row):
                widths[idx] = max(widths[idx], len(str(val)) if val is not None else 4)
                
        # Format and print table
        header_fmt = " | ".join([f"{{:<{w}}}" for w in widths])
        separator = "-+-".join(["-" * w for w in widths])
        
        print("\n" + header_fmt.format(*columns))
        print(separator)
        for row in rows:
            row_str = [str(val) if val is not None else "NULL" for val in row]
            print(header_fmt.format(*row_str))
            
        if total_rows > 30:
            print(f"\n... and {total_rows - 30} more rows (output capped at 30 rows).")
            
        conn.close()
    except Exception as e:
        print(f"SQL Error: {e}")

if __name__ == "__main__":
    sql_file = "detect_zombies.sql"
    if len(sys.argv) > 1:
        sql_file = sys.argv[1]
    run_query(sql_file)
