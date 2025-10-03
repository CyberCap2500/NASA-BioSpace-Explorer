# 🚀 Quick Start Guide

## NASA Space Biology Knowledge Engine

---

## ⚡ 3-Step Setup

### 1️⃣ **Install Dependencies**
```powershell
.venv/Scripts/pip.exe install -r requirements.txt
```

### 2️⃣ **Run the App**
```powershell
.venv/Scripts/streamlit.exe run streamlit_standalone.py
```

### 3️⃣ **Open Browser**
Navigate to: **http://localhost:8501**

---

## 🎯 How to Use

### **Search for Articles**
1. Enter a query (e.g., "microgravity effects on bone density")
2. Click **🔍 Search**
3. Browse results in 3 tabs

### **Explore Knowledge Graph**
1. Go to **🕸️ Knowledge Graph** tab
2. Adjust sliders:
   - **Max Articles**: 10-30 (how many articles to show)
   - **Top Keywords**: 5-20 (main topics)
   - **Min Connection**: 0.1-0.5 (edge strength filter)
3. Hover over nodes for details
4. Expand **📚 View Article Summaries** for text summaries

### **View Article Details**
1. Click article expander in **📄 Search Results** tab
2. Read full abstract
3. Click **🔗 View Full Article** to open source (new tab)

### **Get AI Summary**
1. Go to **🤖 AI Summary** tab
2. Read AI-generated answer
3. Check key references

---

## 🎨 Features Overview

| Feature | Description |
|---------|-------------|
| **Semantic Search** | AI-powered natural language queries |
| **Knowledge Graph** | Visual network of article relationships |
| **Article Summaries** | Brief abstracts for quick scanning |
| **AI Answers** | Context-aware responses with citations |
| **Expandable Cards** | View full details without leaving page |

---

## 🔧 Troubleshooting

### **App won't start?**
```powershell
# Check if dependencies are installed
.venv/Scripts/pip.exe list

# Reinstall if needed
.venv/Scripts/pip.exe install -r requirements.txt --force-reinstall
```

### **Database not found?**
Ensure these files exist:
- `backend/database/outputs/corpus.db`
- `backend/vector_store/faiss_index`
- `backend/vector_store/faiss_index.ids`

### **Slow performance?**
- Reduce **Max Articles** slider (try 10-15)
- Reduce **Top Keywords** slider (try 8-10)
- Increase **Min Connection** slider (try 0.2-0.3)

---

## 📚 Documentation

- **Full Documentation**: `README.md`
- **Project Structure**: `PROJECT_STRUCTURE.md`
- **Deployment Guide**: `DEPLOYMENT.md`

---

## 💡 Example Queries

Try these searches to explore the database:

- `"radiation effects on DNA"`
- `"microgravity bone loss"`
- `"plant growth in space"`
- `"immune system changes spaceflight"`
- `"fungi on International Space Station"`

---

## 🎓 Understanding the Knowledge Graph

### **Nodes**
- **📄 Purple/Colored circles** = Articles (size = relevance score)
- **🔵 Blue text** = Keywords (size = number of connections)

### **Edges (Lines)**
- **Gray lines** = Article-keyword connections
- **Cyan lines** = Articles sharing keywords
- **Thicker lines** = Stronger relationships

### **Controls**
- **Max Articles**: More articles = broader view, but more complex
- **Top Keywords**: Fewer keywords = cleaner graph
- **Min Connection**: Higher value = only strong relationships shown

---

**Happy Exploring! 🚀**
