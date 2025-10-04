#!/usr/bin/env python3

import sys
import traceback

try:
    print("Testing imports...")
    import streamlit
    print(f"✅ Streamlit: {streamlit.__version__}")

    import torch
    print(f"✅ PyTorch: {torch.__version__}")

    import transformers
    print(f"✅ Transformers: {transformers.__version__}")

    import sentence_transformers
    print(f"✅ Sentence Transformers: {sentence_transformers.__version__}")

    import faiss
    print(f"✅ FAISS: {faiss.__version__}")

    import pandas
    print(f"✅ Pandas: {pandas.__version__}")

    import plotly
    print(f"✅ Plotly: {plotly.__version__}")

    print("\n🎉 All imports successful! Ready to run the app.")
    print("📝 Run: python -m streamlit run streamlit_standalone.py")

except Exception as e:
    print(f"❌ Import error: {e}")
    print(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)
