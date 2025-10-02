#!/usr/bin/env python3
"""
Check if essential data files exist for deployment
"""

import os
from pathlib import Path

def check_data_files():
    """Check if all required data files exist"""
    print("🔍 Checking essential data files for deployment...")
    
    required_files = [
        "backend/data/metadata.sqlite",
        "backend/vector_store/faiss_index", 
        "backend/vector_store/faiss_index.ids",
        "backend/database/SB_publication_PMC.csv",
        "backend/database/outputs/metadata.csv"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            existing_files.append((file_path, size))
            print(f"✅ {file_path} ({size:,} bytes)")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path} - MISSING")
    
    print(f"\n📊 Summary:")
    print(f"   Found: {len(existing_files)} files")
    print(f"   Missing: {len(missing_files)} files")
    
    if missing_files:
        print(f"\n⚠️  Missing files need to be created before deployment:")
        for f in missing_files:
            print(f"   - {f}")
        
        print(f"\n🔧 To create missing files, run:")
        print(f"   cd backend")
        print(f"   python ingest_and_embed.py")
        print(f"   python scripts/import_database_outputs.py")
        
        return False
    else:
        print(f"\n🎉 All required data files found!")
        print(f"✅ Ready for GitHub deployment!")
        return True

def check_git_status():
    """Check if data files are properly tracked by git"""
    print(f"\n📋 Git status for data files:")
    
    import subprocess
    try:
        # Check git status
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        
        data_files_in_git = []
        for line in result.stdout.split('\n'):
            if any(keyword in line for keyword in ['metadata.sqlite', 'faiss_index', 'SB_publication_PMC.csv']):
                data_files_in_git.append(line.strip())
        
        if data_files_in_git:
            print("✅ Data files are tracked by git:")
            for f in data_files_in_git:
                print(f"   {f}")
        else:
            print("⚠️  No data files found in git status")
            print("   Run: git add backend/data/ backend/vector_store/ backend/database/SB_publication_PMC.csv")
            
    except FileNotFoundError:
        print("⚠️  Git not found or not in a git repository")

if __name__ == "__main__":
    data_ok = check_data_files()
    check_git_status()
    
    if data_ok:
        print(f"\n🚀 Ready for deployment!")
        print(f"   Run: git add . && git commit -m 'Add data files' && git push")
    else:
        print(f"\n❌ Please create missing data files before deployment")
