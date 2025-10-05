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

# Configure Streamlit
st.set_page_config(page_title="NASA BioSpace Explorer", layout="wide")

# Add backend to path for imports
sys.path.append('backend')

# --- Fonts & Styles ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Roboto:wght@300;400;500&display=swap');

    :root {
      --bg-dark: #0B0C1F;
      --card-bg: #1B1D3B;
      --text: #FFFFFF;
      --muted: #A0E7FF;
      --accent1: #4B0082;
      --accent2: #00FFFF;
    }

    html, body, [data-testid="stAppViewContainer"] {
      background: radial-gradient(1200px 600px at 20% 10%, rgba(75,0,130,0.12), transparent 60%),
                  radial-gradient(900px 500px at 80% 0%, rgba(0,255,255,0.10), transparent 60%),
                  var(--bg-dark) !important;
      color: var(--text);
      font-family: 'Roboto', sans-serif;
    }

    .hero { padding: 24px 0 8px 0; text-align:center; }
    .hero-title { font-family:'Orbitron', sans-serif; font-weight:800; font-size: 38px;
      background: linear-gradient(90deg, var(--accent1), var(--accent2));
      -webkit-background-clip: text; background-clip: text; color: transparent; }
    .hero-tag { color: var(--muted); margin-top: 6px; }

    .search-wrap { max-width: 900px; margin: 12px auto 10px auto; }
    div[data-baseweb="input"] > div { background: #0f1330; border:1px solid #2a2d54; border-radius: 12px; }
    input[type="text"] { color:#fff !important; }

    .chip-row { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin: 10px auto 18px auto; }
    .chip { background:#151835; border:1px solid #2a2d54; color:#ddd; padding:6px 10px; border-radius:999px; font-size:13px; cursor:pointer; }
    .chip:hover { border-color:#3d4180; }

    .result-card { padding:16px; border:1px solid #2a2d54; border-radius:12px; margin-bottom:12px; background: linear-gradient(180deg, rgba(27,29,59,0.95), rgba(27,29,59,0.88)); }
    .result-card:hover { box-shadow: 0 0 0 1px #2a2d54, 0 8px 24px rgba(0,0,0,0.35); transform: translateY(-1px); }
    .snippet strong { color:#f0c419; }
    .score { font-size:12px; color:#aaa; }

    .footer { color:#7fbfe0; border-top:1px solid #2a2d54; padding-top:10px; margin-top:20px; font-size:12px; text-align:center; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Gemini AI integration
@st.cache_resource
def load_gemini_model():
    """Load Gemini AI model for advanced summarization"""
    try:
        import google.generativeai as genai

        # Get API key from environment variable or Streamlit secrets
        api_key = os.getenv('GEMINI_API_KEY') or st.secrets.get('GEMINI_API_KEY', None)

        if not api_key:
            st.warning("⚠️ Gemini API key not found. Please set GEMINI_API_KEY environment variable or add it to Streamlit secrets.")
            return None

        genai.configure(api_key=api_key)

        # Use Gemini Pro model for text generation
        model = genai.GenerativeModel('gemini-pro')
        return model

    except ImportError:
        st.warning("Google Generative AI library not installed. Run: pip install google-generativeai")
        return None
    except Exception as e:
        st.error(f"Error loading Gemini model: {e}")
        return None

@st.cache_resource
def load_embedding_model():
    """Load the sentence transformer model"""
    try:
        from sentence_transformers import SentenceTransformer
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
        # Use a smaller, faster model
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn", max_length=150, min_length=50)
        return summarizer
    except Exception as e:
        st.warning(f"Could not load summarizer: {e}")
        return None

{{ ... }}
def get_db_modification_time(db_path):
    """Get the last modification time of a database file"""
    try:
        return os.path.getmtime(db_path)
    except:
        return 0

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_database():
    """Load data from both corpus_per_row.db and corpus.db databases with optimizations"""
    db_paths = [
        "backend/database/outputs/corpus_per_row.db",
        "backend/database/outputs/corpus.db"
    ]
    
    all_dfs = []
    progress_bar = st.progress(0)
    
    for i, db_path in enumerate(db_paths):
        if not os.path.exists(db_path):
            st.warning(f"Database not found at {db_path}")
            progress_bar.progress((i + 1) / len(db_paths))
            continue
            
        try:
            # First, get the column names without loading all data
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            if not tables:
                st.warning(f"No tables found in {db_path}")
                progress_bar.progress((i + 1) / len(db_paths))
                continue
                
            table_name = tables[0][0]
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Only load text and id columns to save memory
            text_columns = []
            for col in columns:
                col_lower = col.lower()
                if 'text' in col_lower or 'content' in col_lower or 'abstract' in col_lower or 'title' in col_lower or 'body' in col_lower:
                    text_columns.append(col)
            
            # Always include id column if it exists
            id_col = next((col for col in columns if col.lower() == 'id'), None)
            if id_col and id_col not in text_columns:
                text_columns.append(id_col)
                
            if not text_columns:  # If no text columns found, use all columns
                text_columns = columns
            
            # Build query with only needed columns
            columns_str = ", ".join(f'"{col}"' for col in text_columns)
            query = f"SELECT {columns_str} FROM {table_name}"
            
            # Use chunks to process large tables
            chunk_size = 1000
            chunks = []
            for chunk in pd.read_sql_query(query, conn, chunksize=chunk_size):
                chunks.append(chunk)
                
            if chunks:
                df = pd.concat(chunks, ignore_index=True)
                if not df.empty:
                    # Ensure we have an 'id' column
                    if id_col and id_col != 'id':
                        df = df.rename(columns={id_col: 'id'})
                    elif 'id' not in df.columns and len(df.columns) > 0:
                        df = df.rename(columns={df.columns[0]: 'id'})
                    
                    all_dfs.append(df)
            
            conn.close()
                
        except Exception as e:
            st.error(f"Error loading database {db_path}: {str(e)[:200]}")
        
        progress_bar.progress((i + 1) / len(db_paths))
    
    progress_bar.empty()
    
    if not all_dfs:
        st.error("No valid database files could be loaded")
        return None
        
    # Combine all dataframes
    if len(all_dfs) > 1:
        df = pd.concat(all_dfs, ignore_index=True)
    else:
        df = all_dfs[0]
    
    # Remove any potential duplicates based on 'id' column if it exists
    if 'id' in df.columns:
        initial_count = len(df)
        df = df.drop_duplicates(subset=['id'])
        if len(df) < initial_count:
            st.sidebar.info(f"Removed {initial_count - len(df)} duplicate entries")
    
    # Clean up memory
    import gc
    gc.collect()
    
    return df

@st.cache_data
def load_vector_index():
    """Load the FAISS vector index"""
    index_path = "backend/vector_store/faiss_index"
    ids_path = "backend/vector_store/faiss_index.ids"
    
    if not os.path.exists(index_path) or not os.path.exists(ids_path):
        st.error("Vector index files not found")
        return None, None
    
    try:
        index = faiss.read_index(index_path)
        
        # Try different methods to load IDs
        ids = None
        try:
            # Method 1: Standard pickle
            with open(ids_path, 'rb') as f:
                ids = pickle.load(f)
        except:
            try:
                # Method 2: Try with different pickle protocol
                import pickle5
                with open(ids_path, 'rb') as f:
                    ids = pickle5.load(f)
            except:
                try:
                    # Method 3: Try reading as text file
                    with open(ids_path, 'r') as f:
                        ids = [line.strip() for line in f.readlines()]
                except:
                    # Method 4: Generate IDs based on index size
                    st.warning("Could not load IDs file, generating sequential IDs")
                    ids = [f"doc_{i}" for i in range(index.ntotal)]
        
        return index, ids
    except Exception as e:
        st.error(f"Error loading vector index: {e}")
        return None, None

def search_articles(query, df, index, ids, embedding_model, top_k=10):
    """Search articles using vector similarity"""
    if not all([query, df is not None, index is not None, ids is not None, embedding_model]):
        return []
    
    try:
        # Generate query embedding
        query_embedding = embedding_model.encode([query])
        
        # Search in FAISS index
        scores, indices = index.search(query_embedding, min(top_k, len(ids)))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(ids) and idx < len(df):
                article_id = ids[idx]
                # Try to find article by ID in different possible columns
                article = None
                if 'id' in df.columns:
                    matching_rows = df[df['id'] == article_id]
                else:
                    # Try other possible ID columns
                    for col in df.columns:
                        if 'id' in col.lower():
                            matching_rows = df[df[col] == article_id]
                            break
                    else:
                        # If no ID column found, use index
                        matching_rows = df.iloc[idx:idx+1] if idx < len(df) else pd.DataFrame()
                
                if len(matching_rows) > 0:
                    article = matching_rows.iloc[0]
                    # Handle different column names from the database
                    title = article.get('title', '') if 'title' in article else ''
                    abstract = article.get('abstract', '') if 'abstract' in article else ''
                    body = article.get('body', '') if 'body' in article else ''
                    year = article.get('year', '') if 'year' in article else ''
                    pmcid = article.get('pmcid', '') if 'pmcid' in article else article.get('pmc_id', article_id)
                    source_url = article.get('source_url', '') if 'source_url' in article else article.get('url', '')
                    journal = article.get('journal', '') if 'journal' in article else ''
                    
                    # Use abstract or body for snippet
                    snippet_text = abstract if abstract else (body[:500] if body else '')
                    
                    results.append({
                        'title': title,
                        'abstract': abstract,
                        'body': body,
                        'authors': journal,  # Using journal as authors placeholder
                        'year': year,
                        'url': source_url,
                        'pmc_id': pmcid,
                        'score': float(score),
                        'snippet': snippet_text[:300] + '...' if snippet_text else ''
                    })
        
        return results
    except Exception as e:
        st.error(f"Search error: {e}")
        return []

def generate_ai_answer(query, results, gemini_model=None):
    """Generate AI-powered answer from search results using Gemini AI"""
    if not results:
        return "AI answer not available."

    try:
        # Combine relevant abstracts and titles for context
        context_parts = []
        for i, result in enumerate(results[:5], 1):
            title = result.get('title', 'Untitled')
            abstract = result.get('abstract', '')

            if title and abstract:
                context_parts.append(f"Article {i}: {title}\nAbstract: {abstract[:500]}...")
            elif title:
                context_parts.append(f"Article {i}: {title}")

        combined_context = '\n\n'.join(context_parts)

        if len(combined_context) < 100:
            return "Insufficient information to generate a comprehensive answer."

        # Use Gemini AI if available
        if gemini_model:
            try:
                prompt = f"""Based on the following NASA space biology research papers, provide a comprehensive answer to the query: "{query}"

Research Context:
{combined_context}

Please provide a detailed, scientific answer that:
1. Directly addresses the query
2. Synthesizes information from multiple papers
3. Uses clear, professional language
4. Highlights key findings and conclusions
5. Mentions any conflicting evidence if present

Answer:"""

                response = gemini_model.generate_content(prompt)
                return response.text if response.text else "Unable to generate Gemini response."

            except Exception as e:
                st.warning(f"Gemini API error: {e}. Falling back to extractive summary.")
                # Fall back to extractive method

        # Fallback: Simple extractive summary
        texts = [r.get('abstract', '') for r in results[:5] if r.get('abstract')]
        combined_text = ' '.join(texts)

        if len(combined_text) < 100:
            return "Insufficient information to generate a comprehensive answer."

        sentences = combined_text.split('. ')
        key_sentences = []
        query_terms = query.lower().split()

        # Score sentences by query term frequency
        for sentence in sentences[:10]:  # Look at first 10 sentences
            score = sum(sentence.lower().count(term) for term in query_terms if len(term) > 3)
            if score > 0:
                key_sentences.append((sentence, score))

        # Sort by score and take top 3
        key_sentences.sort(key=lambda x: x[1], reverse=True)
        summary_sentences = [sent[0] for sent in key_sentences[:3]]

        if summary_sentences:
            return '. '.join(summary_sentences) + '.'
        else:
            # Fallback to first few sentences
            return '. '.join(sentences[:3]) + '.'

    except Exception as e:
        st.warning(f"AI answer generation failed: {e}")
        return "AI answer generation temporarily unavailable."

def highlight_text(text, query):
    """Highlight query terms in text"""
    if not text or not query:
        return text
    
    query_terms = [term.lower() for term in query.split() if len(term) > 2]
    highlighted = text
    
    for term in query_terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        highlighted = pattern.sub(f'<strong>{term}</strong>', highlighted)
    
    return highlighted

# --- Main App ---

# Hero section
st.markdown(
    """
    <div class="hero">
      <div class="hero-title">NASA BioSpace Explorer</div>
      <div class="hero-tag">AI-Powered Search Engine for NASA Space Biology Publications</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Initialize session state
if "results" not in st.session_state:
    st.session_state["results"] = []
if "page" not in st.session_state:
    st.session_state["page"] = 1
if "query" not in st.session_state:
    st.session_state["query"] = ""
if "selected_chip" not in st.session_state:
    st.session_state["selected_chip"] = ""
if "answer" not in st.session_state:
    st.session_state["answer"] = None

# Load Gemini AI model
with st.spinner("Loading Gemini AI (optional)..."):
    gemini_model = load_gemini_model()

# Load summarizer in background (optional)
with st.spinner("Loading backup summarizer (optional)..."):
    summarizer = load_summarizer()

# Check if everything loaded successfully
if not all([embedding_model, df is not None, index is not None, ids is not None]):
    st.error("❌ Failed to load required data files. Please ensure:")
    st.code("""
    - backend/database/outputs/corpus_per_row.db
    - backend/database/outputs/corpus.db
    - backend/vector_store/faiss_index
    - backend/vector_store/faiss_index.ids
    """)
    st.stop()

if gemini_model:
    st.success("✅ AI models and data loaded successfully! (Gemini AI + Full AI summarization available)")
elif summarizer:
    st.success("✅ AI models and data loaded successfully! (Backup AI summarization available)")
else:
    st.success("✅ AI models and data loaded successfully! (Using fast extractive summarization)")

# Search interface
st.markdown('<div class="search-wrap">', unsafe_allow_html=True)
default_query = st.session_state.get("selected_chip", "")
query = st.text_input("Search NASA space biology publications", value=default_query, key="query_input")
st.markdown('</div>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

# Example queries
example_queries = [
    "effects of microgravity on bone density",
    "radiation DNA damage mechanisms in space",
    "plant biology experiments on ISS",
    "immune system changes during spaceflight",
]

quick_topics = [
    "Microgravity", "Radiation", "Plants", "Humans", "Mice",
]

st.markdown('<div class="chip-row">' + ''.join([f'<span class="chip">{escape(q)}</span>' for q in example_queries]) + '</div>', unsafe_allow_html=True)
st.markdown('<div class="chip-row">' + ''.join([f'<span class="chip">{escape(q)}</span>' for q in quick_topics]) + '</div>', unsafe_allow_html=True)

# Chip buttons
chip_cols = st.columns(len(example_queries))
for i, q in enumerate(example_queries):
    if chip_cols[i].button(q):
        st.session_state["selected_chip"] = q
        st.rerun()

topic_cols = st.columns(len(quick_topics))
for i, q in enumerate(quick_topics):
    if topic_cols[i].button(q):
        st.session_state["selected_chip"] = q
        st.rerun()

with col1:
    search_clicked = st.button("🔍 Search", use_container_width=True)
with col2:
    summarize_clicked = st.button("🤖 AI Summary", use_container_width=True)

# Search functionality
results = []
current_query = st.session_state.get("query_input", "")
if search_clicked and current_query:
    st.session_state["query"] = current_query
    st.session_state["selected_chip"] = ""
    
    with st.spinner("Searching NASA publications..."):
        results = search_articles(current_query, df, index, ids, embedding_model, top_k=20)
        
        if results:
            st.session_state["results"] = results
            st.session_state["page"] = 1
            
            # Generate AI answer using Gemini if available
            st.session_state["answer"] = generate_ai_answer(current_query, results, gemini_model)
        else:
            st.warning("No results found. Try different keywords.")

if not results:
    results = st.session_state.get("results", [])

# Create tabs for different views
if results:
    tab1, tab2, tab3 = st.tabs(["📄 Search Results", "🕸️ Knowledge Graph", "🤖 AI Summary"])
    
    with tab3:
        # AI Answer section
        if st.session_state.get("answer"):
            st.subheader("🤖 AI-Generated Answer")
            st.info(st.session_state["answer"])
            
            # Show citations
            citations = results[:3]  # Top 3 citations
            st.subheader("📚 Key References")
            for i, result in enumerate(citations, 1):
                title = result.get('title', 'Untitled')
                url = result.get('url', '')
                year = result.get('year', '')
                
                if url:
                    st.markdown(f"{i}. [{title}]({url}) ({year})")
                else:
                    st.markdown(f"{i}. {title} ({year})")
    
    with tab2:
        # Knowledge Graph section
        st.subheader("🕸️ Knowledge Graph Visualization")
        st.caption("Interactive graph showing relationships between articles and keywords")
        
        # Article Summaries Section
        st.markdown("### 📝 Article Summaries")
        st.caption("AI-generated summaries of top articles")
        
        with st.expander("📚 View Article Summaries", expanded=False):
            for i, result in enumerate(results[:10], 1):
                title = result.get('title', 'Untitled')
                abstract = result.get('abstract', '')
                year = result.get('year', 'N/A')
                url = result.get('url', '')
                
                # Generate a brief summary (first 250 chars of abstract)
                if abstract and len(str(abstract).strip()) > 10:
                    summary = str(abstract)[:250].strip()
                    if len(abstract) > 250:
                        summary += "..."
                else:
                    summary = "No abstract available."
                
                # Display each article summary with cleaner formatting
                st.markdown(f"**{i}. {title[:100]}{'...' if len(title) > 100 else ''}**")
                st.caption(f"Year: {year}")
                st.write(summary)
                
                if url:
                    st.markdown(f"[🔗 Read full article]({url})")
                
                st.markdown("---")
        
        st.markdown("### 🌐 Knowledge Graph")
        st.caption("Visual network showing how articles connect through shared topics")
        
        # Add controls for graph customization
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            max_articles = st.slider("Max Articles", 10, 30, 20, help="Number of articles to include in graph")
        with col_b:
            top_kw = st.slider("Top Keywords", 5, 20, 12, help="Number of main keywords to show")
        with col_c:
            min_weight = st.slider("Min Connection", 0.1, 0.5, 0.15, 0.05, help="Minimum edge weight to display")
        
        with st.spinner("Building knowledge graph..."):
            # Build knowledge graph with user parameters
            G = build_knowledge_graph(results, max_nodes=max_articles, top_keywords=top_kw, min_edge_weight=min_weight)
            
            # Get statistics
            stats = get_graph_statistics(G)
            
            # Display statistics
            if stats.get('datasets', 0) > 0:
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Articles", stats['articles'])
                with col2:
                    st.metric("Keywords", stats['keywords'])
                with col3:
                    st.metric("Datasets", stats['datasets'])
                with col4:
                    st.metric("Connections", stats['total_edges'])
                with col5:
                    st.metric("Avg Links", f"{stats['avg_connections']:.1f}")
            else:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Articles", stats['articles'])
                with col2:
                    st.metric("Keywords", stats['keywords'])
                with col3:
                    st.metric("Connections", stats['total_edges'])
                with col4:
                    st.metric("Avg Links", f"{stats['avg_connections']:.1f}")
            
            # Create and display visualization
            fig = create_graph_visualization(G)
            st.plotly_chart(fig, use_container_width=True)
            
            tip_text = "💡 **Tip:** Hover over nodes to see details. Larger article nodes have higher relevance scores."
            if stats.get('datasets', 0) > 0:
                tip_text += " 🔬 Diamond nodes are OSDR experimental datasets linked to papers."
            st.info(tip_text)
    
    with tab1:
        # Results section
        total = len(results)
        pages = max(1, math.ceil(total / 10))
        start = (st.session_state["page"] - 1) * 10
        end = min(total, start + 10)

        st.subheader(f"📄 Research Articles ({total} found)")
        st.caption(f"Showing {start+1}-{end} of {total}")

        for idx, result in enumerate(results[start:end], start=start):
            title = result.get('title', 'Untitled')
            url = result.get('url', '')
            year = result.get('year', '')
            authors = result.get('authors', '')
            snippet = result.get('snippet', '')
            abstract = result.get('abstract', '')
            score = result.get('score', 0)
            
            badges = []
            if year:
                badges.append(f"<span class='pill'>Year: {year}</span>")
            if authors:
                first_author = authors.split(',')[0].strip()
                badges.append(f"<span class='pill'>{escape(first_author)}</span>")
            badge_html = ' '.join(badges)
            
            # Highlight query terms in snippet
            highlighted_snippet = highlight_text(snippet, st.session_state["query"])
            
            # Create expandable card for each article
            with st.expander(f"📄 {title[:80]}{'...' if len(title) > 80 else ''}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Title:** {title}")
                    if year:
                        st.markdown(f"**Year:** {year}")
                    if authors:
                        st.markdown(f"**Authors/Journal:** {authors}")
                    st.markdown(f"**Relevance Score:** {score:.3f}")
                
                with col2:
                    if url:
                        st.link_button("🔗 View Full Article", url, use_container_width=True)
                
                st.markdown("---")
                st.markdown("**Abstract:**")
                if abstract:
                    st.write(abstract)
                else:
                    st.write(snippet if snippet else "No abstract available.")
                
                # Check for linked OSDR datasets
                pmc_id = result.get('pmc_id', '')
                if pmc_id:
                    try:
                        # Try to load OSDR enrichment data
                        import os
                        osdr_file = "backend/database/outputs/osdr_enrichment.json"
                        if os.path.exists(osdr_file):
                            import json
                            with open(osdr_file, 'r') as f:
                                osdr_data = json.load(f)
                            
                            # Find datasets for this paper
                            paper_datasets = next((p for p in osdr_data if p['paper_id'] == pmc_id), None)
                            if paper_datasets and paper_datasets.get('linked_datasets'):
                                st.markdown("---")
                                st.markdown("**🔬 Related Experimental Datasets (OSDR):**")
                                for ds in paper_datasets['linked_datasets'][:3]:
                                    st.markdown(f"- [{ds['title'][:80]}...]({ds['url']}) `{ds['osdr_id']}`")
                    except:
                        pass  # Silently fail if OSDR data not available
            
            # Also show compact card view
            st.markdown(
                f"""
                <div class="result-card" style="margin-top: -10px;">
                  <div class="muted">{badge_html} <span class="score">Relevance: {score:.3f}</span></div>
                  <div class="snippet">{highlighted_snippet}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Pagination
        if pages > 1:
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("⬅️ Previous") and st.session_state["page"] > 1:
                    st.session_state["page"] -= 1
                    st.rerun()
            with c2:
                st.write(f"Page {st.session_state['page']} / {pages}")
            with c3:
                if st.button("Next ➡️") and st.session_state["page"] < pages:
                    st.session_state["page"] += 1
                    st.rerun()

# Statistics
if df is not None:
    st.subheader("📊 Database Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Articles", len(df))
    with col2:
        if 'year' in df.columns:
            years = df['year'].dropna()
            try:
                # Convert to numeric, handling any non-numeric values
                years_numeric = pd.to_numeric(years, errors='coerce').dropna()
                if len(years_numeric) > 0:
                    st.metric("Year Range", f"{int(years_numeric.min())}-{int(years_numeric.max())}")
                else:
                    st.metric("Year Range", "N/A")
            except:
                st.metric("Year Range", "N/A")
        else:
            st.metric("Year Range", "N/A")
    with col3:
        st.metric("Vector Index Size", len(ids) if ids else 0)

# Footer
st.markdown(
    """
    <div class="footer">
    🚀 Powered by AI • Data from NASA Space Biology Publications • Built with Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
