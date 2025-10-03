import os
import sys
import math
import requests
import streamlit as st
import plotly.express as px
from html import escape

# Add backend to path for cloud deployment
sys.path.append('backend')

# Import backend services
try:
    from backend.app.services.embeddings import EmbeddingService
    from backend.app.services.vector_store import VectorStore
    from backend.app.services.search import SearchService
    
    # Check if data files exist
    data_files = [
        "backend/data/metadata.sqlite",
        "backend/vector_store/faiss_index",
        "backend/vector_store/faiss_index.ids"
    ]
    
    missing_files = [f for f in data_files if not os.path.exists(f)]
    
    if missing_files:
        st.warning("⚠️ Data files not found. Please run data ingestion first.")
        st.info("For deployment, ensure these files are included:")
        for f in missing_files:
            st.code(f)
        LOCAL_MODE = False
    else:
        # Initialize services
        embedding_service = EmbeddingService()
        vector_store = VectorStore()
        search_service = SearchService(embedding_service, vector_store)
        
        LOCAL_MODE = True
        st.success("✅ Local AI services loaded successfully!")
        
except ImportError as e:
    st.error(f"❌ Could not load local AI services: {e}")
    st.info("Running in API mode. Make sure backend is running.")
    LOCAL_MODE = False

st.set_page_config(page_title="BioSpace Explorer", layout="wide")

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
    .pill { display:inline-block; padding:2px 8px; border-radius:999px; background:#202458; border:1px solid #2a2d54; margin-right:6px; font-size:12px; }
    .score { font-size:12px; color:#aaa; }

    .footer { color:#7fbfe0; border-top:1px solid #2a2d54; padding-top:10px; margin-top:20px; font-size:12px; text-align:center; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Hero ---
st.markdown(
    """
    <div class="hero">
      <div class="hero-title">BioSpace Explorer</div>
      <div class="hero-tag">Explore NASA Bioscience Publications and Discover Their Impact</div>
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
if "citations" not in st.session_state:
    st.session_state["citations"] = []

# --- Search Bar ---
st.markdown('<div class="search-wrap">', unsafe_allow_html=True)
default_query = st.session_state.get("selected_chip", "")
query = st.text_input("Search NASA bioscience (e.g., microgravity bone loss)", value=default_query, key="query_input")
st.markdown('</div>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

PAGE_SIZE = 10

# Example queries
example_queries = [
    "effects of microgravity on bone density",
    "radiation DNA damage mechanisms in space",
    "plant biology experiments on ISS",
    "immune system changes during long-duration spaceflight",
]

quick_topics = [
    "Microgravity", "Radiation", "Plants", "Humans", "Mice",
]

st.markdown('<div class="chip-row">' + ''.join([f'<span class="chip">{escape(q)}</span>' for q in example_queries]) + '</div>', unsafe_allow_html=True)
st.markdown('<div class="chip-row">' + ''.join([f'<span class="chip">{escape(q)}</span>' for q in quick_topics]) + '</div>', unsafe_allow_html=True)

# Map chips to Streamlit buttons
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
    search_clicked = st.button("Search", use_container_width=True)
with col2:
    summarize_clicked = st.button("Summarize with AI", use_container_width=True)

# Search functionality
results = []
current_query = st.session_state.get("query_input", "")
if search_clicked and current_query:
    st.session_state["query"] = current_query
    st.session_state["selected_chip"] = ""
    
    with st.spinner("Searching & analyzing..."):
        if LOCAL_MODE:
            # Use local search service
            try:
                search_results = search_service.search(current_query, top_k=100, mode="hybrid")
                results = search_results.get("results", [])
                
                # Generate AI answer
                if results:
                    answer_result = search_service.generate_answer(current_query, results[:10])
                    st.session_state["answer"] = answer_result.get("answer")
                    st.session_state["citations"] = answer_result.get("citations", [])
                
            except Exception as e:
                st.error(f"Search error: {e}")
                results = []
        else:
            # Fallback to API mode (for development)
            try:
                r = requests.post("http://localhost:8000/search", json={"query": current_query, "top_k": 100, "mode": "hybrid"})
                if r.ok:
                    results = r.json().get("results", [])
                    
                    # AI answer
                    a = requests.post("http://localhost:8000/summarize", json={"query": current_query, "top_k": 10})
                    if a.ok:
                        payload = a.json()
                        st.session_state["answer"] = payload.get("answer")
                        st.session_state["citations"] = payload.get("citations", [])
                else:
                    st.error("Search failed")
            except requests.exceptions.ConnectionError:
                st.error("Backend not running. Please start the backend API.")
        
        if results:
            st.session_state["results"] = results
            st.session_state["page"] = 1

if not results:
    results = st.session_state.get("results", [])

# --- AI Answer ---
if st.session_state.get("answer"):
    st.subheader("AI Answer")
    st.write(st.session_state["answer"])
    if st.session_state.get("citations"):
        st.subheader("Citations")
        for c in st.session_state["citations"]:
            title = c.get('title') or '(untitled)'
            url = c.get('url')
            st.markdown(f"- {escape(title)} — [{'link' if url else 'no-link'}]({url})" if url else f"- {escape(title)}")

# --- Results ---
if results:
    total = len(results)
    pages = max(1, math.ceil(total / PAGE_SIZE))
    start = (st.session_state["page"] - 1) * PAGE_SIZE
    end = min(total, start + PAGE_SIZE)

    st.subheader("Related Articles")
    st.caption(f"Showing {start+1}-{end} of {total}")

    for h in results[start:end]:
        title = h.get('title') or '(untitled)'
        url = h.get('url')
        year = h.get('year')
        authors = h.get('authors')
        snippet = h.get('snippet') or (h.get('abstract') or '')[:400]
        score = h.get('score')
        badges = []
        if year:
            badges.append(f"<span class='pill'>Year: {escape(str(year))}</span>")
        if authors:
            first_author = authors.split(',')[0]
            badges.append(f"<span class='pill'>{escape(first_author)}</span>")
        badge_html = ' '.join(badges)
        
        def highlight(text: str, query: str) -> str:
            if not text:
                return ""
            out = escape(text)
            for term in set(query.split()):
                if len(term) < 3:
                    continue
                out = out.replace(escape(term), f"<strong>{escape(term)}</strong>")
                out = out.replace(escape(term.lower()), f"<strong>{escape(term.lower())}</strong>")
                out = out.replace(escape(term.capitalize()), f"<strong>{escape(term.capitalize())}</strong>")
            return out
        
        html_snippet = highlight(snippet, st.session_state["query"]) if snippet else ""
        st.markdown(
            f"""
            <div class="result-card">
              <div><a href="{url or '#'}" target="_blank"><strong>{escape(title)}</strong></a></div>
              <div class="muted">{badge_html} <span class="score">score={score:.3f}</span></div>
              <div class="snippet">{html_snippet}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("⟵ Prev") and st.session_state["page"] > 1:
            st.session_state["page"] -= 1
    with c2:
        st.write(f"Page {st.session_state['page']} / {pages}")
    with c3:
        if st.button("Next ⟶") and st.session_state["page"] < pages:
            st.session_state["page"] += 1

# --- Footer ---
st.markdown(
    """
    <div class="footer">Powered by Local AI + FAISS. Data from NASA/PMC sources.</div>
    """,
    unsafe_allow_html=True,
)
