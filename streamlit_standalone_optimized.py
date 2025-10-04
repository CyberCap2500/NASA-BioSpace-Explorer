"""
Memory-Optimized NASA BioSpace Explorer
Fixed for Streamlit Cloud resource limits
"""

import os
import sys
import math
import sqlite3
import streamlit as st
import pandas as pd
import numpy as np
import faiss
import pickle
import gc
import re
from html import escape

# Configure Streamlit for memory efficiency
st.set_page_config(page_title="NASA BioSpace Explorer", layout="wide")

# Add backend to path for imports
sys.path.append('backend')

# --- Memory-Optimized Functions ---

@st.cache_resource
def load_embedding_model():
    """Load a lightweight embedding model"""
    try:
        from sentence_transformers import SentenceTransformer
        # Use the smallest available model for demo - mobile optimized
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        return model
    except Exception as e:
        st.error(f"Error loading embedding model: {e}")
        return None

@st.cache_resource
def load_summarizer():
    """Load a lightweight summarization model"""
    try:
        from transformers import pipeline
        # Use a smaller, faster model with CPU-only
        summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            max_length=150,
            min_length=50,
            device=-1  # Force CPU
        )
        return summarizer
    except Exception as e:
        st.warning(f"Could not load summarizer: {e}. Using extractive method.")
        return None

@st.cache_data(ttl=3600)
def load_database_sample():
    """Load only a sample of the database for demo (memory optimization)"""
    db_paths = [
        "backend/database/outputs/corpus_per_row.db",
        "backend/database/outputs/corpus.db"
    ]

    all_dfs = []

    for db_path in db_paths:
        if not os.path.exists(db_path):
            continue

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get table info
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            if not tables:
                continue

            table_name = tables[0][0]

            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]

            # Only load essential columns to save memory
            text_columns = []
            for col in columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['text', 'content', 'abstract', 'title', 'body']):
                    text_columns.append(col)

            # Always include id column if it exists
            id_col = next((col for col in columns if col.lower() == 'id'), None)
            if id_col and id_col not in text_columns:
                text_columns.append(id_col)

            if not text_columns:
                text_columns = columns[:5]  # Limit to first 5 columns

            # Build query with only needed columns
            columns_str = ", ".join(f'"{col}"' for col in text_columns)
            query = f"SELECT {columns_str} FROM {table_name}"

            # Load only a sample for demo (every 10th row to reduce memory)
            sample_query = f"""
                SELECT * FROM ({query}) WHERE ROWID % 10 = 0 LIMIT 200
            """

            df = pd.read_sql_query(sample_query, conn)

            if not df.empty:
                # Ensure we have an 'id' column
                if id_col and id_col != 'id':
                    df = df.rename(columns={id_col: 'id'})
                elif 'id' not in df.columns and len(df.columns) > 0:
                    df = df.rename(columns={df.columns[0]: 'id'})

                all_dfs.append(df)

            conn.close()

        except Exception as e:
            st.error(f"Error loading database {db_path}: {str(e)[:100]}")
            continue

    if not all_dfs:
        st.error("No valid database files could be loaded")
        return None

    # Combine all dataframes
    df = pd.concat(all_dfs, ignore_index=True) if len(all_dfs) > 1 else all_dfs[0]

    # Remove duplicates
    if 'id' in df.columns:
        df = df.drop_duplicates(subset=['id'])

    # Force garbage collection
    gc.collect()

    return df

@st.cache_data
def load_vector_index():
    """Load a subset of the FAISS vector index for memory efficiency"""
    index_path = "backend/vector_store/faiss_index"
    ids_path = "backend/vector_store/faiss_index.ids"

    if not os.path.exists(index_path) or not os.path.exists(ids_path):
        st.error("Vector index files not found")
        return None, None

    try:
        # Load only a subset of the index for demo
        index = faiss.read_index(index_path)

        # Load only first 1000 IDs to reduce memory
        try:
            with open(ids_path, 'rb') as f:
                all_ids = pickle.load(f)
                # Sample every 5th ID for demo
                ids = all_ids[::5][:200]  # Max 200 for demo
        except:
            # Generate sequential IDs
            ids = [f"doc_{i*5}" for i in range(min(200, index.ntotal))]

        return index, ids
    except Exception as e:
        st.error(f"Error loading vector index: {e}")
        return None, None
