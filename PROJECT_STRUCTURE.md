# 📁 NASA Space Biology Knowledge Engine - Project Structure

## 🎯 Overview
AI-powered search engine with knowledge graph visualization for NASA Space Biology publications.

---

## 📂 Directory Structure

```
NASA25/
├── 📄 streamlit_standalone.py      # Main application (run this!)
├── 📄 knowledge_graph.py           # Knowledge graph generation & visualization
├── 📄 requirements.txt             # Python dependencies
├── 📄 run_streamlit.ps1           # Windows launcher script
├── 📄 README.md                    # Project documentation
├── 📄 DEPLOYMENT.md                # Deployment guide
│
├── 📁 backend/                     # Data and models
│   ├── 📁 data/                   # Database files
│   │   └── metadata.sqlite        # Article metadata (legacy)
│   ├── 📁 database/
│   │   └── 📁 outputs/
│   │       ├── corpus.db          # Main article database
│   │       ├── corpus_per_row.db  # Row-based article database
│   │       └── metadata.csv       # CSV export
│   └── 📁 vector_store/           # AI embeddings
│       ├── faiss_index            # Vector search index
│       └── faiss_index.ids        # Document IDs
│
├── 📁 .venv/                      # Virtual environment (Python packages)
├── 📁 venv/                       # Alternative venv
│
└── 📁 utils/                      # Helper scripts
    ├── check_data.py              # Database inspection
    ├── check_schema.py            # Schema validation
    └── schema_output.txt          # Schema documentation
```

---

## 🚀 Quick Start

### 1. **Install Dependencies**
```powershell
.venv/Scripts/pip.exe install -r requirements.txt
```

### 2. **Run the App**
```powershell
.venv/Scripts/streamlit.exe run streamlit_standalone.py
```

### 3. **Access the App**
Open your browser at: **http://localhost:8501**

---

## 📦 Core Files

### **Main Application**
- **`streamlit_standalone.py`** (26KB)
  - Main Streamlit web application
  - Handles search, results display, and UI
  - Integrates knowledge graph visualization
  - Contains 3 tabs: Search Results, Knowledge Graph, AI Summary

### **Knowledge Graph Module**
- **`knowledge_graph.py`** (9KB)
  - Builds semantic knowledge graphs from search results
  - Extracts keywords and creates relationships
  - Generates interactive Plotly visualizations
  - Functions:
    - `extract_keywords()` - Extract important terms
    - `build_knowledge_graph()` - Create graph structure
    - `create_graph_visualization()` - Generate interactive plot
    - `get_graph_statistics()` - Calculate graph metrics

### **Dependencies**
- **`requirements.txt`**
  - streamlit==1.38.0
  - pandas==2.2.3
  - numpy==1.26.4
  - faiss-cpu==1.8.0.post1
  - plotly==5.24.1
  - networkx==3.1
  - torch==2.2.2
  - transformers==4.38.2
  - sentence-transformers==2.5.1

---

## 🗄️ Database Files

### **Primary Database**
- **`backend/database/outputs/corpus.db`** (47MB)
  - Main SQLite database with full article data
  - Contains: id, pmcid, title, abstract, body, year, journal, source_url
  - 608+ NASA Space Biology articles

### **Alternative Database**
- **`backend/database/outputs/corpus_per_row.db`** (49MB)
  - Row-based storage format
  - Same schema as corpus.db

### **Vector Store**
- **`backend/vector_store/faiss_index`** (932KB)
  - FAISS vector embeddings for semantic search
  - Pre-computed embeddings using sentence-transformers
- **`backend/vector_store/faiss_index.ids`** (7KB)
  - Document ID mappings for vector index

---

## 🎨 Features

### 1. **AI-Powered Search** 🔍
- Semantic search using sentence-transformers
- FAISS vector similarity matching
- Relevance scoring and ranking

### 2. **Knowledge Graph** 🕸️
- Visual network of articles and keywords
- Interactive Plotly visualization
- Adjustable parameters:
  - Max articles (10-30)
  - Top keywords (5-20)
  - Min connection strength (0.1-0.5)

### 3. **Article Summaries** 📝
- Brief summaries from abstracts
- Expandable full details
- Links to original sources

### 4. **AI Summary** 🤖
- AI-generated answers from search results
- Key references and citations
- Powered by DistilBART

---

## 🛠️ Utility Scripts

### **Database Inspection**
```powershell
python check_schema.py
```
- Displays database schema
- Shows sample data
- Validates structure

### **Data Verification**
```powershell
python check_data.py
```
- Checks data integrity
- Displays statistics

---

## 🎯 Usage Guide

### **Search for Articles**
1. Enter query (e.g., "microgravity effects on bone density")
2. Click "🔍 Search"
3. View results in 3 tabs

### **Explore Knowledge Graph**
1. Go to "🕸️ Knowledge Graph" tab
2. Adjust sliders for customization
3. Hover over nodes for details
4. Expand "📚 View Article Summaries"

### **View Article Details**
1. Click on article expander in Search Results
2. Read full abstract
3. Click "🔗 View Full Article" to open source

---

## 📊 Database Schema

### **Articles Table**
| Column      | Type | Description                    |
|-------------|------|--------------------------------|
| id          | TEXT | Unique identifier              |
| pmcid       | TEXT | PubMed Central ID              |
| title       | TEXT | Article title                  |
| abstract    | TEXT | Article abstract               |
| body        | TEXT | Full article text              |
| year        | TEXT | Publication year               |
| journal     | TEXT | Journal name                   |
| source_url  | TEXT | Link to original article       |

---

## 🔧 Configuration

### **Knowledge Graph Parameters**
- **max_nodes**: Number of articles to include (default: 20)
- **top_keywords**: Number of main keywords (default: 12)
- **min_edge_weight**: Minimum connection strength (default: 0.15)

### **Search Parameters**
- **top_k**: Number of results to return (default: 20)
- **embedding_model**: 'all-MiniLM-L6-v2'

---

## 📝 Notes

- **Backup files**: `knowledge_graph_backup.py` is a backup copy
- **Legacy files**: `check_data.py`, `check_schema.py` are utilities
- **Virtual environments**: Both `.venv` and `venv` exist (use `.venv`)

---

## 🚀 Deployment

See `DEPLOYMENT.md` for cloud deployment instructions.

---

## 📧 Support

For issues or questions, refer to the main `README.md` file.

---

**Last Updated**: 2025-10-04
**Version**: 1.0.0
