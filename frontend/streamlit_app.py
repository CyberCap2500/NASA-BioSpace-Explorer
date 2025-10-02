import os
import math
import requests
import streamlit as st
import plotly.express as px
from html import escape

API_HOST = os.environ.get("API_HOST", "http://localhost")
API_PORT = os.environ.get("API_PORT", "8000")
API_URL = f"{API_HOST}:{API_PORT}"

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
      --accent1: #4B0082; /* indigo */
      --accent2: #00FFFF; /* cyan */
    }

    html, body, [data-testid="stAppViewContainer"] {
      background: radial-gradient(1200px 600px at 20% 10%, rgba(75,0,130,0.12), transparent 60%),
                  radial-gradient(900px 500px at 80% 0%, rgba(0,255,255,0.10), transparent 60%),
                  var(--bg-dark) !important;
      color: var(--text);
      font-family: 'Roboto', sans-serif;
    }

    /* subtle stars */
    [data-testid="stAppViewContainer"]::before {
      content: '';
      position: fixed; inset: 0; pointer-events: none; opacity: 0.25;
      background-image:
        radial-gradient(2px 2px at 20% 30%, #ffffff 30%, transparent 30%),
        radial-gradient(2px 2px at 70% 20%, #ffffff 30%, transparent 30%),
        radial-gradient(1.5px 1.5px at 40% 70%, #ffffff 30%, transparent 30%),
        radial-gradient(1.5px 1.5px at 85% 60%, #ffffff 30%, transparent 30%),
        radial-gradient(1.2px 1.2px at 10% 80%, #ffffff 30%, transparent 30%);
      background-repeat: no-repeat;
    }

    .hero { padding: 24px 0 8px 0; text-align:center; }
    .hero-title { font-family:'Orbitron', sans-serif; font-weight:800; font-size: 38px;
      background: linear-gradient(90deg, var(--accent1), var(--accent2));
      -webkit-background-clip: text; background-clip: text; color: transparent; }
    .hero-tag { color: var(--muted); margin-top: 6px; }

    /* Search input styling */
    .search-wrap { max-width: 900px; margin: 12px auto 10px auto; }
    /* Streamlit input field */
    div[data-baseweb="input"] > div { background: #0f1330; border:1px solid #2a2d54; border-radius: 12px; }
    input[type="text"] { color:#fff !important; }

    .chip-row { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin: 10px auto 18px auto; }
    .chip { background:#151835; border:1px solid #2a2d54; color:#ddd; padding:6px 10px; border-radius:999px; font-size:13px; cursor:pointer; }
    .chip:hover { border-color:#3d4180; }

    .result-card { padding:16px; border:1px solid #2a2d54; border-radius:12px; margin-bottom:12px; background: linear-gradient(180deg, rgba(27,29,59,0.95), rgba(27,29,59,0.88)); transition: box-shadow 180ms ease, transform 180ms ease; }
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

# Ensure session state
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

# --- Sidebar ---
with st.sidebar:
    st.header("Options")
    mode = st.selectbox("Mode", options=["hybrid", "vector", "keyword"], index=0)
    organism = st.text_input("Organism")
    year_from = st.number_input("Year from", min_value=0, max_value=2100, value=0)
    year_to = st.number_input("Year to", min_value=0, max_value=2100, value=2100)
    keywords = st.text_input("Keywords (comma-separated)")
    if st.button("Apply Filters"):
        payload = {
            "organism": organism or None,
            "year_from": int(year_from) if year_from else None,
            "year_to": int(year_to) if year_to else None,
            "keywords": [k.strip() for k in (keywords or "").split(",") if k.strip()],
            "limit": 100,
        }
        r = requests.post(f"{API_URL}/filter", json=payload)
        if r.ok:
            st.session_state["filtered"] = r.json()["results"]
        else:
            st.error("Filter request failed")

# --- Search Bar ---
st.markdown('<div class="search-wrap">', unsafe_allow_html=True)
# Use selected chip as default value if available
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

# Map chips to Streamlit buttons for accessibility
chip_cols = st.columns(len(example_queries))
chip_clicked = False
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
    summarize_clicked = st.button("Summarize with Gemini", use_container_width=True)

results = []
current_query = st.session_state.get("query_input", "")
if search_clicked and current_query:
    st.session_state["query"] = current_query
    # Clear the selected chip after using it
    st.session_state["selected_chip"] = ""
    with st.spinner("Searching & analyzing..."):
        # Related docs
        r = requests.post(f"{API_URL}/search", json={"query": current_query, "top_k": 100, "mode": mode})
        if r.ok:
            results = r.json().get("results", [])
            st.session_state["results"] = results
            st.session_state["page"] = 1
        else:
            st.error("Search failed")
        # AI answer
        a = requests.post(f"{API_URL}/summarize", json={"query": current_query, "top_k": 10})
        if a.ok:
            payload = a.json()
            st.session_state["answer"] = payload.get("answer")
            st.session_state["citations"] = payload.get("citations", [])
        else:
            st.session_state["answer"] = None
            st.session_state["citations"] = []

if not results:
    results = st.session_state.get("results", [])

# --- AI Answer on top ---
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
    st.caption(f"Mode: {mode} · Showing {start+1}-{end} of {total}")

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

# --- Trends ---
st.subheader("Trends")
data = st.session_state.get("filtered")
if data:
    years = [d.get("year") for d in data if d.get("year")]
    if years:
        fig = px.histogram(x=years, nbins=30, title="Publications by Year")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Apply filters in the sidebar to see trend charts.")

# --- Footer ---
st.markdown(
    """
    <div class="footer">Powered by Gemini (optional) + FAISS. Data from NASA/PMC sources.</div>
    """,
    unsafe_allow_html=True,
)



