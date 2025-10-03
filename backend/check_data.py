import sqlite3
import pandas as pd

# Check what's actually in the database
conn = sqlite3.connect('backend/data/metadata.sqlite')
df = pd.read_sql_query("SELECT * FROM documents LIMIT 20", conn)
conn.close()

print("Sample data from database:")
print(df[['title', 'year', 'url']].head(10))

print("\nUnique years:", sorted(df['year'].unique()))
print("Total records:", len(df))

# Check for NASA/space-related content
nasa_keywords = ['nasa', 'space', 'microgravity', 'astronaut', 'iss', 'spaceflight']
nasa_count = 0

for _, row in df.iterrows():
    title = str(row['title']).lower()
    if any(keyword in title for keyword in nasa_keywords):
        nasa_count += 1
        if nasa_count <= 5:
            print(f"NASA-related: {row['title']}")

print(f"\nNASA-related articles found: {nasa_count} out of {len(df)}")

