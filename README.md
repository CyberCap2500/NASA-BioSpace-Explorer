# 🚀 NASA Space Biology Knowledge Engine

An AI-powered platform for querying, exploring, and visualizing insights from NASA space biology publications.

## ⚡ Super Easy Setup (Windows)

### 🎯 One-Click Launch
```bash
# Just double-click this file:
run_app.bat
```

**OR**

```powershell
# Right-click and "Run with PowerShell":
run_app.ps1
```

That's it! The app will:
- ✅ Check Python installation
- ✅ Set up everything automatically  
- ✅ Open at http://localhost:8501

---

## 📁 Project Structure

```
NASA25/
├── run_app.bat       # 🚀 One-click launcher (Windows)
├── run_app.ps1       # 🚀 One-click launcher (PowerShell)
├── INSTALL.md        # 📖 Detailed setup instructions
├── backend/          # 🔧 API server and data processing
└── frontend/         # 🎨 Streamlit web interface
```

---

## 🌐 Access Your App
- **Local**: http://localhost:8501
- **Cloud**: https://YOUR_USERNAME-nasa-space-biology-engine.streamlit.app

## ☁️ Deploy to Cloud

### Quick Deploy to Streamlit Cloud:
1. **Push to GitHub**: `git add . && git commit -m "Deploy" && git push`
2. **Go to**: https://share.streamlit.io
3. **Connect repo** and deploy `streamlit_app_cloud.py`
4. **Share your app** with the world!

📖 **Detailed deployment guide**: See `DEPLOYMENT.md`

## 🎯 Features

- **AI-Powered Search**: Natural language queries with semantic understanding
- **Smart Summarization**: AI-generated insights and summaries  
- **Visual Exploration**: Interactive charts and data visualization
- **Filtering**: Search by organism, year, research type, and more
- **Local AI**: Runs entirely offline using sentence-transformers
- **Cloud Ready**: Deploy to Streamlit Cloud with one click

## 📊 Data Sources

- NASA Space Biology publications (608 articles)
- PMC XML metadata  
- PDF content extraction
- Vector embeddings for semantic search

## 🛠️ Technology Stack

- **Backend**: FastAPI, SQLite, FAISS, sentence-transformers
- **Frontend**: Streamlit, Plotly
- **AI**: HuggingFace Transformers, DistilBART, T5
- **Cloud**: Streamlit Cloud, GitHub