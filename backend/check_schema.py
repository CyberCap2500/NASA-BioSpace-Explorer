import sqlite3
import pandas as pd

# Check corpus_per_row.db
print("=" * 60)
print("Checking corpus_per_row.db")
print("=" * 60)
try:
    conn = sqlite3.connect('backend/database/outputs/corpus_per_row.db')
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nTables: {tables}")
    
    if tables:
        table_name = tables[0][0]
        print(f"\nTable: {table_name}")
        
        # Get columns
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print("\nColumns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Get sample data
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 3", conn)
        print(f"\nSample data (first 3 rows):")
        print(df.head())
        print(f"\nTotal rows: {len(pd.read_sql_query(f'SELECT COUNT(*) as count FROM {table_name}', conn))}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Checking corpus.db")
print("=" * 60)
try:
    conn = sqlite3.connect('backend/database/outputs/corpus.db')
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nTables: {tables}")
    
    if tables:
        table_name = tables[0][0]
        print(f"\nTable: {table_name}")
        
        # Get columns
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print("\nColumns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Get sample data
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 3", conn)
        print(f"\nSample data (first 3 rows):")
        print(df.head())
        print(f"\nTotal rows: {len(pd.read_sql_query(f'SELECT COUNT(*) as count FROM {table_name}', conn))}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
