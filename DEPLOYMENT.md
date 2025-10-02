# 🚀 Deployment Guide - GitHub + Streamlit Cloud

## 📋 Prerequisites

1. **GitHub Account** - https://github.com
2. **Streamlit Cloud Account** - https://share.streamlit.io (free)

## 🔧 Step 1: Prepare for GitHub

### 1.1 Initialize Git Repository
```bash
git init
git add .
git commit -m "Initial commit: NASA Space Biology Knowledge Engine"
```

### 1.2 Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `nasa-space-biology-engine`
3. Description: `AI-powered platform for exploring NASA space biology publications`
4. Make it **Public** (required for free Streamlit Cloud)
5. Click "Create repository"

### 1.3 Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/nasa-space-biology-engine.git
git branch -M main
git push -u origin main
```

## ☁️ Step 2: Deploy to Streamlit Cloud

### 2.1 Connect to Streamlit Cloud
1. Go to https://share.streamlit.io
2. Sign in with your GitHub account
3. Click "New app"

### 2.2 Configure Deployment
- **Repository**: `YOUR_USERNAME/nasa-space-biology-engine`
- **Branch**: `main`
- **Main file path**: `streamlit_app_cloud.py`
- **App URL**: `nasa-space-biology-engine` (or your choice)

### 2.3 Advanced Settings (Optional)
```toml
[streamlit]
serverPort = 8501
serverAddress = "0.0.0.0"

[browser]
gatherUsageStats = false
```

## 📁 Required Files for Deployment

Make sure these files are in your repository:

```
nasa-space-biology-engine/
├── streamlit_app_cloud.py    # Main Streamlit app for cloud
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore file
├── README.md                # Project documentation
├── backend/                 # Backend code
│   ├── app/                 # FastAPI application
│   ├── data/
│   │   └── metadata.sqlite  # ✅ ESSENTIAL: Article database
│   ├── database/
│   │   └── SB_publication_PMC.csv  # ✅ ESSENTIAL: NASA data
│   └── vector_store/
│       ├── faiss_index      # ✅ ESSENTIAL: Vector index
│       └── faiss_index.ids  # ✅ ESSENTIAL: Vector IDs
└── DEPLOYMENT.md            # This file
```

### ⚠️ **Critical Data Files**
These files MUST be included for the search engine to work:
- `backend/data/metadata.sqlite` (139KB)
- `backend/vector_store/faiss_index` (932KB) 
- `backend/vector_store/faiss_index.ids` (7KB)
- `backend/database/SB_publication_PMC.csv` (97KB)

## 🔑 Environment Variables (if needed)

In Streamlit Cloud settings, you can add:
- `GOOGLE_API_KEY` (if using Gemini API)
- Any other API keys

## 📊 Data Requirements

### Option 1: Include Data in Repository
- Add your processed data files to the repository
- Update `.gitignore` to allow data files
- Larger repository but faster startup

### Option 2: Download Data on Startup
- Add data download script to `streamlit_app_cloud.py`
- Downloads data when app starts
- Smaller repository but slower first load

## 🚀 Quick Deployment Commands

```bash
# 1. Prepare repository
git init
git add .
git commit -m "Ready for deployment"

# 2. Create GitHub repo (do this manually on GitHub)
# 3. Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/nasa-space-biology-engine.git
git push -u origin main

# 4. Deploy on Streamlit Cloud (do this manually on share.streamlit.io)
```

## 🔧 Troubleshooting

### Common Issues:

1. **Import Errors**: Make sure all dependencies are in `requirements.txt`
2. **Data Not Found**: Ensure data files are included or downloadable
3. **Memory Issues**: Streamlit Cloud has 1GB RAM limit
4. **Slow Startup**: Consider pre-processing data

### Performance Tips:

1. **Use `@st.cache_data`** for expensive operations
2. **Lazy load** data when needed
3. **Optimize** model sizes for cloud deployment
4. **Use** smaller datasets for demo purposes

## 📱 Custom Domain (Optional)

Streamlit Cloud Pro users can use custom domains:
- Go to app settings
- Add custom domain
- Update DNS records

## 🔄 Updates

To update your deployed app:
```bash
git add .
git commit -m "Update app"
git push origin main
```
Streamlit Cloud will automatically redeploy!

## 📊 Monitoring

Streamlit Cloud provides:
- App usage statistics
- Error logs
- Performance metrics
- Uptime monitoring

---

## 🎯 Final Result

Your app will be available at:
**https://YOUR_USERNAME-nasa-space-biology-engine.streamlit.app**

Share this link with anyone to use your NASA Space Biology Knowledge Engine!
