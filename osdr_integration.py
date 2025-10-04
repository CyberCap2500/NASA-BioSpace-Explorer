"""
NASA OSDR (Open Science Data Repository) Integration Module

This module enriches the literature database with links to experimental datasets
from NASA's Biological & Physical Sciences Data hub (OSDR/PSI).

Resources:
- OSDR API: https://osdr.nasa.gov/bio/repo/
- NASA BPS Data: https://science.nasa.gov/biological-physical/data/
"""

import requests
import json
import sqlite3
import pandas as pd
from typing import Dict, List, Optional
import time
from urllib.parse import quote

class OSDRIntegrator:
    """Integrates NASA OSDR experimental datasets with literature"""
    
    def __init__(self, db_path: str = "backend/database/outputs/corpus_per_row.db"):
        self.db_path = db_path
        self.osdr_api_base = "https://osdr.nasa.gov/bio/repo/search"
        self.cache = {}
        
    def search_osdr_by_keywords(self, keywords: List[str], max_results: int = 5) -> List[Dict]:
        """
        Search OSDR for datasets matching keywords
        
        Args:
            keywords: List of search terms (e.g., ["microgravity", "bone density"])
            max_results: Maximum number of results to return
            
        Returns:
            List of dataset metadata dictionaries
        """
        query = " ".join(keywords)
        cache_key = f"osdr_{query}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # OSDR API search endpoint
            params = {
                "q": query,
                "size": max_results,
                "type": "study"  # Focus on study-level datasets
            }
            
            response = requests.get(self.osdr_api_base, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                datasets = []
                
                # Parse OSDR response format
                if "hits" in data and "hits" in data["hits"]:
                    for hit in data["hits"]["hits"][:max_results]:
                        source = hit.get("_source", {})
                        datasets.append({
                            "osdr_id": source.get("accession", ""),
                            "title": source.get("title", ""),
                            "description": source.get("description", ""),
                            "organism": source.get("organism", []),
                            "assay_type": source.get("assay_type", []),
                            "url": f"https://osdr.nasa.gov/bio/repo/data/studies/{source.get('accession', '')}",
                            "release_date": source.get("release_date", ""),
                            "factors": source.get("factors", [])
                        })
                
                self.cache[cache_key] = datasets
                return datasets
            else:
                print(f"OSDR API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error searching OSDR: {e}")
            return []
    
    def extract_keywords_from_paper(self, title: str, abstract: str) -> List[str]:
        """
        Extract relevant keywords from paper title and abstract
        
        Args:
            title: Paper title
            abstract: Paper abstract
            
        Returns:
            List of keywords for OSDR search
        """
        # Key terms related to space biology
        space_terms = [
            "microgravity", "spaceflight", "ISS", "space station",
            "radiation", "cosmic ray", "hypergravity", "simulated microgravity",
            "parabolic flight", "centrifuge", "ground control"
        ]
        
        biological_terms = [
            "gene expression", "RNA-seq", "proteomics", "metabolomics",
            "bone density", "muscle atrophy", "immune system", "cell culture",
            "plant growth", "microbiome", "stem cells", "tissue engineering"
        ]
        
        text = (title + " " + abstract).lower()
        keywords = []
        
        # Extract matching terms
        for term in space_terms + biological_terms:
            if term.lower() in text:
                keywords.append(term)
        
        # Limit to top 5 most relevant
        return keywords[:5] if keywords else ["space biology"]
    
    def enrich_paper_with_datasets(self, paper_id: str, title: str, abstract: str) -> Dict:
        """
        Find related OSDR datasets for a given paper
        
        Args:
            paper_id: Paper identifier (PMC ID)
            title: Paper title
            abstract: Paper abstract
            
        Returns:
            Dictionary with paper info and linked datasets
        """
        keywords = self.extract_keywords_from_paper(title, abstract)
        datasets = self.search_osdr_by_keywords(keywords, max_results=3)
        
        return {
            "paper_id": paper_id,
            "title": title,
            "keywords": keywords,
            "linked_datasets": datasets,
            "dataset_count": len(datasets)
        }
    
    def enrich_database(self, limit: Optional[int] = None, delay: float = 0.5):
        """
        Enrich the entire database with OSDR dataset links
        
        Args:
            limit: Maximum number of papers to process (None = all)
            delay: Delay between API calls to avoid rate limiting
        """
        conn = sqlite3.connect(self.db_path)
        
        # Read papers from database
        query = "SELECT id, title, abstract FROM corpus"
        if limit:
            query += f" LIMIT {limit}"
        
        df = pd.read_sql_query(query, conn)
        
        enriched_data = []
        
        print(f"Processing {len(df)} papers...")
        
        for idx, row in df.iterrows():
            paper_id = row.get('id', '')
            title = row.get('title', '')
            abstract = row.get('abstract', '')
            
            if not title or not abstract:
                continue
            
            print(f"[{idx+1}/{len(df)}] Processing: {title[:50]}...")
            
            enrichment = self.enrich_paper_with_datasets(paper_id, title, abstract)
            enriched_data.append(enrichment)
            
            # Rate limiting
            time.sleep(delay)
        
        conn.close()
        
        # Save enriched data
        output_path = "backend/database/outputs/osdr_enrichment.json"
        with open(output_path, 'w') as f:
            json.dump(enriched_data, f, indent=2)
        
        print(f"\n✅ Enrichment complete! Saved to {output_path}")
        print(f"📊 Papers processed: {len(enriched_data)}")
        print(f"📊 Papers with datasets: {sum(1 for e in enriched_data if e['dataset_count'] > 0)}")
        
        return enriched_data
    
    def create_enrichment_table(self):
        """Create a new table in the database for OSDR dataset links"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table for dataset links
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS osdr_datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id TEXT,
                osdr_id TEXT,
                dataset_title TEXT,
                dataset_url TEXT,
                organism TEXT,
                assay_type TEXT,
                relevance_score REAL,
                FOREIGN KEY (paper_id) REFERENCES corpus(id)
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ OSDR datasets table created")
    
    def load_enrichment_to_db(self, enrichment_file: str = "backend/database/outputs/osdr_enrichment.json"):
        """Load enriched data into the database"""
        with open(enrichment_file, 'r') as f:
            enriched_data = json.load(f)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for paper in enriched_data:
            paper_id = paper['paper_id']
            for dataset in paper['linked_datasets']:
                cursor.execute("""
                    INSERT INTO osdr_datasets 
                    (paper_id, osdr_id, dataset_title, dataset_url, organism, assay_type, relevance_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    paper_id,
                    dataset['osdr_id'],
                    dataset['title'],
                    dataset['url'],
                    ", ".join(dataset.get('organism', [])),
                    ", ".join(dataset.get('assay_type', [])),
                    1.0  # Default relevance score
                ))
        
        conn.commit()
        conn.close()
        print(f"✅ Loaded {len(enriched_data)} enriched papers to database")


def main():
    """Example usage"""
    integrator = OSDRIntegrator()
    
    # Option 1: Test with a single paper
    print("🔍 Testing OSDR integration with sample search...")
    datasets = integrator.search_osdr_by_keywords(["microgravity", "bone density"], max_results=3)
    print(f"\nFound {len(datasets)} datasets:")
    for ds in datasets:
        print(f"  - {ds['title'][:60]}... ({ds['osdr_id']})")
    
    # Option 2: Enrich a subset of papers (uncomment to run)
    # print("\n🚀 Enriching database with OSDR datasets...")
    # integrator.create_enrichment_table()
    # enriched = integrator.enrich_database(limit=10)  # Start with 10 papers
    # integrator.load_enrichment_to_db()
    
    print("\n✅ Integration test complete!")


if __name__ == "__main__":
    main()
