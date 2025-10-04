import networkx as nx
import plotly.graph_objects as go
import pandas as pd
import re
from collections import Counter

def extract_keywords(text, top_n=5):
    """Extract top keywords from text"""
    if not text or pd.isna(text):
        return []
    
    # Simple keyword extraction - remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                  'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 
                  'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
                  'these', 'those', 'it', 'its', 'they', 'their', 'them'}
    
    # Extract words (lowercase, alphanumeric only)
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    
    # Filter stop words and count
    filtered_words = [w for w in words if w not in stop_words]
    word_counts = Counter(filtered_words)
    
    # Return top N keywords
    return [word for word, count in word_counts.most_common(top_n)]

def build_knowledge_graph(results, max_nodes=20, top_keywords=15, min_edge_weight=0.15, include_datasets=True):
    """Build a pruned, meaningful knowledge graph from search results"""
    G = nx.Graph()
    
    # Load OSDR dataset enrichment if available
    osdr_data = {}
    if include_datasets:
        try:
            import json
            import os
            osdr_file = "backend/database/outputs/osdr_enrichment.json"
            if os.path.exists(osdr_file):
                with open(osdr_file, 'r') as f:
                    osdr_list = json.load(f)
                    osdr_data = {p['paper_id']: p for p in osdr_list}
        except:
            pass
    
    # Extract all keywords first to find most common ones
    all_keywords = Counter()
    article_keywords = {}
    
    for i, result in enumerate(results[:max_nodes]):
        text = f"{result.get('title', '')} {result.get('abstract', '')}"
        keywords = extract_keywords(text, top_n=5)
        article_id = result.get('pmc_id', f'Article_{i}')
        article_keywords[article_id] = keywords
        all_keywords.update(keywords)
    
    # Get top N most common keywords across all articles
    top_keyword_list = [kw for kw, count in all_keywords.most_common(top_keywords)]
    
    # Add article nodes with only top keywords
    for i, result in enumerate(results[:max_nodes]):
        article_id = result.get('pmc_id', f'Article_{i}')
        title = result.get('title', 'Untitled')[:50]
        score = result.get('score', 0)
        
        # Only add article if it has at least one top keyword
        article_kws = [kw for kw in article_keywords.get(article_id, []) if kw in top_keyword_list]
        
        if article_kws:
            # Add article node
            G.add_node(article_id, 
                       type='article',
                       title=title,
                       year=result.get('year', ''),
                       score=score)
            
            # Add keyword nodes and edges (only for top keywords)
            for keyword in article_kws:
                if not G.has_node(keyword):
                    G.add_node(keyword, type='keyword', count=all_keywords[keyword])
                G.add_edge(article_id, keyword, weight=1.0)
            
            # Add OSDR dataset nodes if available
            if article_id in osdr_data:
                datasets = osdr_data[article_id].get('linked_datasets', [])
                for ds in datasets[:2]:  # Limit to 2 datasets per paper
                    dataset_id = ds.get('osdr_id', '')
                    if dataset_id:
                        dataset_title = ds.get('title', '')[:40]
                        G.add_node(dataset_id,
                                   type='dataset',
                                   title=dataset_title,
                                   url=ds.get('url', ''))
                        G.add_edge(article_id, dataset_id, weight=2.0, relation='has_data')
    
    # Connect articles that share keywords (with threshold)
    articles = [n for n, d in G.nodes(data=True) if d.get('type') == 'article']
    for i, art1 in enumerate(articles):
        art1_score = G.nodes[art1].get('score', 0)
        for art2 in articles[i+1:]:
            art2_score = G.nodes[art2].get('score', 0)
            shared_keywords = set(article_keywords.get(art1, [])) & set(article_keywords.get(art2, []))
            shared_keywords = [kw for kw in shared_keywords if kw in top_keyword_list]
            
            if shared_keywords:
                # Weight by number of shared keywords and article relevance
                edge_weight = len(shared_keywords) * (art1_score + art2_score) / 2
                
                # Only add edge if weight is above threshold
                if edge_weight >= min_edge_weight:
                    G.add_edge(art1, art2, weight=edge_weight, shared=list(shared_keywords))
    
    return G

def create_graph_visualization(G):
    """Create an interactive Plotly visualization of the knowledge graph"""
    import plotly.graph_objs as go
    import networkx as nx

    # Use spring layout for positioning
    pos = nx.spring_layout(G, seed=42)
    edge_traces = []
    node_x = []
    node_y = []
    node_text = []
    node_color = []

    # Edges
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_traces.append(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                line=dict(width=1, color='#888'),
                hoverinfo='none',
                mode='lines'
            )
        )

    # Nodes
    for node, data in G.nodes(data=True):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(str(data.get('label', node)))
        node_color.append(
            'skyblue' if data.get('type') == 'article' else
            'orange' if data.get('type') == 'keyword' else
            'green' if data.get('type') == 'dataset' else
            'gray'
        )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=node_text,
        textposition='top center',
        hoverinfo='text',
        marker=dict(
            color=node_color,
            size=18,
            line=dict(width=2)
        )
    )

    graph_title = '<b>Knowledge Graph Visualization</b>'
    fig = go.Figure(
        data=edge_traces + [node_trace],
        layout=go.Layout(
            title={'text': graph_title, 'x': 0.5},
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=700,
            plot_bgcolor='#0B0C1F',
            paper_bgcolor='#0B0C1F',
            font=dict(color='white')
        )
    )
    return fig

def get_graph_statistics(G):
    """Get statistics about the knowledge graph"""
    article_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'article']
    keyword_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'keyword']
    dataset_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'dataset']
    
    stats = {
        'total_nodes': G.number_of_nodes(),
        'total_edges': G.number_of_edges(),
        'articles': len(article_nodes),
        'keywords': len(keyword_nodes),
        'datasets': len(dataset_nodes),
        'avg_connections': sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0,
        'density': nx.density(G)
    }
    
    return stats
