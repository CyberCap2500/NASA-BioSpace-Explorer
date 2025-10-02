#!/usr/bin/env python3
"""
Prepare data for Streamlit Cloud deployment
This script ensures all necessary data files are available for cloud deployment
"""

import os
import shutil
import sys
from pathlib import Path

def prepare_cloud_data():
    """Prepare data files for cloud deployment"""
    print("🚀 Preparing data for Streamlit Cloud deployment...")
    
    # Create data directory if it doesn't exist
    data_dir = Path("backend/data")
    data_dir.mkdir(exist_ok=True)
    
    # Check if we have the necessary data files
    required_files = [
        "backend/data/metadata.sqlite",
        "backend/vector_store/faiss_index",
        "backend/vector_store/faiss_index.ids"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required data files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n🔧 To fix this, run the data ingestion script:")
        print("   cd backend && python ingest_and_embed.py")
        return False
    
    print("✅ All required data files found!")
    
    # Create a minimal dataset for cloud demo if needed
    if os.path.getsize("backend/data/metadata.sqlite") < 1024:  # Less than 1KB
        print("⚠️  Database seems empty. Creating demo data...")
        create_demo_data()
    
    print("🎉 Data preparation complete!")
    print("\n📋 Next steps:")
    print("1. git add .")
    print("2. git commit -m 'Add cloud deployment files'")
    print("3. git push origin main")
    print("4. Deploy on Streamlit Cloud!")
    
    return True

def create_demo_data():
    """Create minimal demo data for testing"""
    import sqlite3
    import json
    
    # Create minimal metadata
    conn = sqlite3.connect("backend/data/metadata.sqlite")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY,
            title TEXT,
            abstract TEXT,
            authors TEXT,
            year INTEGER,
            url TEXT,
            pmc_id TEXT
        )
    """)
    
    # Insert demo articles
    demo_articles = [
        {
            "title": "Effects of Microgravity on Bone Density in Astronauts",
            "abstract": "This study examines the impact of microgravity on bone density during space missions...",
            "authors": "Smith, J., Johnson, A.",
            "year": 2023,
            "url": "https://example.com/article1",
            "pmc_id": "PMC123456"
        },
        {
            "title": "Plant Growth Experiments on the International Space Station",
            "abstract": "Research on plant biology in microgravity conditions aboard the ISS...",
            "authors": "Brown, K., Davis, L.",
            "year": 2022,
            "url": "https://example.com/article2",
            "pmc_id": "PMC789012"
        }
    ]
    
    for article in demo_articles:
        cursor.execute("""
            INSERT INTO articles (title, abstract, authors, year, url, pmc_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (article["title"], article["abstract"], article["authors"], 
              article["year"], article["url"], article["pmc_id"]))
    
    conn.commit()
    conn.close()
    
    print("✅ Demo data created!")

if __name__ == "__main__":
    success = prepare_cloud_data()
    sys.exit(0 if success else 1)
