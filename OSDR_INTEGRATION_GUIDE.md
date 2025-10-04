# 🔬 NASA OSDR Integration Guide

## Overview

This guide explains how to integrate **NASA's Open Science Data Repository (OSDR)** experimental datasets with your literature database to create a comprehensive knowledge platform.

## What is OSDR?

**OSDR** (Open Science Data Repository) is NASA's repository for biological and physical sciences data from space experiments:
- 🧬 **Biological data**: Gene expression, proteomics, metabolomics
- 🔬 **Physical sciences**: Material science, fluid physics, combustion
- 🚀 **Space experiments**: ISS, shuttle missions, ground-based simulations
- 📊 **Open access**: All data freely available for research

**Resources:**
- OSDR Portal: https://osdr.nasa.gov/bio/repo/
- NASA BPS Data Hub: https://science.nasa.gov/biological-physical/data/
- API Documentation: https://osdr.nasa.gov/bio/repo/search

## Integration Benefits

### 1. **Enhanced Search Results**
- Users see both **papers** and **experimental datasets**
- Direct links to raw data behind publications
- More actionable and research-grade results

### 2. **Richer Knowledge Graph**
- **3 node types**: Articles, Keywords, Datasets
- Visual connections showing which papers have experimental data
- Easier discovery of related experiments

### 3. **Data-Driven Insights**
- Link literature findings to actual experimental measurements
- Enable meta-analyses across multiple datasets
- Support reproducibility and validation

## Quick Start

### Step 1: Run OSDR Integration Script

```bash
python osdr_integration.py
```

This will:
1. Load your paper database
2. Extract keywords from each paper
3. Search OSDR for matching datasets
4. Save enrichment data to `backend/database/outputs/osdr_enrichment.json`

### Step 2: Test with Sample Papers

```python
from osdr_integration import OSDRIntegrator

integrator = OSDRIntegrator()

# Test search
datasets = integrator.search_osdr_by_keywords(
    ["microgravity", "bone density"], 
    max_results=5
)

for ds in datasets:
    print(f"- {ds['title']} ({ds['osdr_id']})")
```

### Step 3: Enrich Full Database

```python
# Enrich first 50 papers (test run)
integrator.enrich_database(limit=50)

# Enrich all papers (takes ~10 minutes for 608 papers)
integrator.enrich_database(limit=None)
```

### Step 4: Load into Database (Optional)

```python
# Create table for dataset links
integrator.create_enrichment_table()

# Load enriched data
integrator.load_enrichment_to_db()
```

## How It Works

### 1. Keyword Extraction

The system extracts relevant keywords from paper titles and abstracts:

```python
keywords = extract_keywords_from_paper(title, abstract)
# Example: ["microgravity", "bone density", "gene expression"]
```

### 2. OSDR API Search

Searches OSDR using extracted keywords:

```python
GET https://osdr.nasa.gov/bio/repo/search?q=microgravity+bone+density&type=study
```

### 3. Dataset Matching

Returns top 3 most relevant datasets per paper:

```json
{
  "paper_id": "PMC12345",
  "linked_datasets": [
    {
      "osdr_id": "OSD-123",
      "title": "Bone Density Changes in Microgravity",
      "url": "https://osdr.nasa.gov/bio/repo/data/studies/OSD-123",
      "organism": ["Mus musculus"],
      "assay_type": ["RNA sequencing"]
    }
  ]
}
```

### 4. UI Integration

The Streamlit app automatically displays linked datasets:

**In Search Results:**
```
📄 Paper Title
Abstract: ...
🔬 Related Experimental Datasets (OSDR):
  - Dataset Title (OSD-123)
  - Another Dataset (OSD-456)
```

**In Knowledge Graph:**
- 📄 Blue circles = Articles
- 🔤 Purple circles = Keywords  
- 🔬 Green diamonds = OSDR Datasets

## File Structure

```
NASA25/
├── osdr_integration.py              # Main integration module
├── backend/
│   └── database/
│       └── outputs/
│           ├── corpus_per_row.db    # Your paper database
│           └── osdr_enrichment.json # Generated enrichment data
├── streamlit_standalone.py          # Updated to show datasets
└── knowledge_graph.py               # Updated to include dataset nodes
```

## API Rate Limiting

OSDR API has rate limits:
- **Default**: 0.5 second delay between requests
- **Recommended**: 1 second for large batches
- **Total time**: ~10 minutes for 608 papers

```python
# Adjust delay in enrich_database()
integrator.enrich_database(limit=None, delay=1.0)  # 1 second delay
```

## Example Use Cases

### Use Case 1: Find Datasets for a Topic

```python
# Search for microgravity bone studies
datasets = integrator.search_osdr_by_keywords(
    ["microgravity", "bone", "osteoblast"],
    max_results=10
)
```

### Use Case 2: Enrich Specific Papers

```python
# Enrich a single paper
enrichment = integrator.enrich_paper_with_datasets(
    paper_id="PMC12345",
    title="Effects of Microgravity on Bone Density",
    abstract="This study examines..."
)
```

### Use Case 3: Generate Statistics

```python
import json

with open("backend/database/outputs/osdr_enrichment.json") as f:
    data = json.load(f)

total_papers = len(data)
papers_with_datasets = sum(1 for p in data if p['dataset_count'] > 0)
total_datasets = sum(p['dataset_count'] for p in data)

print(f"Papers: {total_papers}")
print(f"Papers with datasets: {papers_with_datasets} ({papers_with_datasets/total_papers*100:.1f}%)")
print(f"Total datasets linked: {total_datasets}")
```

## Advanced Features

### Custom Keyword Extraction

Modify `extract_keywords_from_paper()` to improve matching:

```python
def extract_keywords_from_paper(self, title, abstract):
    # Add your domain-specific terms
    custom_terms = [
        "CRISPR", "proteomics", "metabolomics",
        "RNA-seq", "single-cell", "organoid"
    ]
    
    text = (title + " " + abstract).lower()
    keywords = [term for term in custom_terms if term.lower() in text]
    
    return keywords[:5]
```

### Filter by Organism

```python
# Only show datasets for specific organisms
datasets = [ds for ds in datasets if "Homo sapiens" in ds.get('organism', [])]
```

### Filter by Assay Type

```python
# Only show RNA-seq datasets
datasets = [ds for ds in datasets if "RNA sequencing" in ds.get('assay_type', [])]
```

## Troubleshooting

### Issue: No datasets found

**Cause**: Keywords too specific or OSDR doesn't have matching data

**Solution**: 
- Broaden keywords (e.g., "microgravity" instead of "simulated microgravity")
- Check OSDR manually: https://osdr.nasa.gov/bio/repo/search

### Issue: API timeout

**Cause**: Network issues or OSDR server slow

**Solution**:
```python
# Increase timeout in search_osdr_by_keywords()
response = requests.get(self.osdr_api_base, params=params, timeout=30)
```

### Issue: Rate limiting errors

**Cause**: Too many requests too quickly

**Solution**:
```python
# Increase delay between requests
integrator.enrich_database(limit=None, delay=2.0)
```

## Performance Optimization

### Caching

The integrator caches API responses:

```python
# Results are cached in memory
datasets = integrator.search_osdr_by_keywords(keywords)  # API call
datasets = integrator.search_osdr_by_keywords(keywords)  # Cached
```

### Batch Processing

Process papers in batches:

```python
# Process 100 papers at a time
for batch_start in range(0, 608, 100):
    integrator.enrich_database(limit=100, offset=batch_start)
```

## Future Enhancements

### 1. **Direct Data Visualization**
- Fetch dataset CSVs from OSDR
- Plot experimental results alongside papers
- Compare findings across studies

### 2. **Semantic Matching**
- Use embeddings to match papers to datasets
- More accurate than keyword matching
- Requires OSDR dataset embeddings

### 3. **Citation Analysis**
- Check if paper cites OSDR dataset
- Verify data-paper relationships
- Build citation network

### 4. **Multi-Source Integration**
- Add GeneLab data
- Include PSI (Physical Sciences Informatics)
- Connect to other NASA repositories

## Resources

- **OSDR Portal**: https://osdr.nasa.gov/bio/repo/
- **NASA BPS Data**: https://science.nasa.gov/biological-physical/data/
- **GeneLab**: https://genelab.nasa.gov/
- **PSI**: https://psi.nasa.gov/
- **API Docs**: https://osdr.nasa.gov/bio/repo/search

## Support

For issues or questions:
1. Check OSDR documentation
2. Review `osdr_integration.py` code comments
3. Test with sample queries first
4. Verify API endpoint is accessible

---

**Status**: ✅ Ready to use
**Last Updated**: 2025-10-04
**Integration Level**: Literature + Experimental Data
