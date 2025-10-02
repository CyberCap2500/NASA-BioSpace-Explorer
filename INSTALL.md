# 🚀 NASA Space Biology Knowledge Engine - Easy Setup

## One-Click Installation & Run

### For Windows Users (Super Easy!)

1. **Download Python** (if not installed):
   - Go to https://python.org/downloads/
   - Download Python 3.8 or newer
   - ✅ **IMPORTANT**: Check "Add Python to PATH" during installation

2. **Run the App**:
   ```powershell
   # Right-click on run_app.ps1 and select "Run with PowerShell"
   # OR double-click run_app.ps1
   ```

3. **That's it!** 
   - The app will open automatically at http://localhost:8501
   - Everything is set up automatically (environments, dependencies, etc.)

---

## What This Does Automatically

✅ **Checks Python installation**  
✅ **Creates virtual environments**  
✅ **Installs all dependencies**  
✅ **Starts backend API**  
✅ **Starts web interface**  
✅ **Opens your browser**  

---

## Alternative: Manual Setup (If Needed)

If the one-click doesn't work:

```powershell
# 1. Install dependencies
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

cd ..\frontend  
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2. Run (in separate terminals)
# Terminal 1:
cd backend && .venv\Scripts\activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2:
cd frontend && .venv\Scripts\activate && streamlit run streamlit_app.py --server.port 8501
```

---

## Troubleshooting

**"Python not found"**: Install Python from https://python.org and check "Add to PATH"

**"Execution Policy Error"**: Run this in PowerShell as Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Port already in use**: Close other applications using ports 8000 or 8501

---

## Features

🔍 **AI-Powered Search** - Natural language queries  
📊 **Smart Summarization** - AI-generated insights  
🎯 **Visual Exploration** - Interactive charts  
🔬 **NASA Data** - 608+ space biology publications  
⚡ **Fast & Local** - No internet required for AI  

---

**Need Help?** Check the README.md for more details!
