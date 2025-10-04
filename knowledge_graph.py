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
    
    # Use spring layout for positioning
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    
    # Separate nodes by type
    article_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'article']
    keyword_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'keyword']
    dataset_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'dataset']
    
    # Create edge traces
    edge_traces = []
    
    # Article-keyword edges (thin, gray)
    edge_x_ak = []
    edge_y_ak = []
    for edge in G.edges():
        if (G.nodes[edge[0]].get('type') == 'article' and G.nodes[edge[1]].get('type') == 'keyword') or \
           (G.nodes[edge[0]].get('type') == 'keyword' and G.nodes[edge[1]].get('type') == 'article'):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x_ak.extend([x0, x1, None])
            edge_y_ak.extend([y0, y1, None])
    
    edge_trace_ak = go.Scatter(
        x=edge_x_ak, y=edge_y_ak,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines',
        showlegend=False
    )
    edge_traces.append(edge_trace_ak)
    
    # Article-dataset edges (medium, green)
    edge_x_ad = []
    edge_y_ad = []
    for edge in G.edges():
        if (G.nodes[edge[0]].get('type') == 'article' and G.nodes[edge[1]].get('type') == 'dataset') or \
           (G.nodes[edge[0]].get('type') == 'dataset' and G.nodes[edge[1]].get('type') == 'article'):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x_ad.extend([x0, x1, None])
            edge_y_ad.extend([y0, y1, None])
    
    if edge_x_ad:
        edge_trace_ad = go.Scatter(
            x=edge_x_ad, y=edge_y_ad,
            line=dict(width=1.5, color='#00FF88'),
            hoverinfo='none',
            mode='lines',
            showlegend=False,
            opacity=0.8
        )
        edge_traces.append(edge_trace_ad)
    
    # Article-article edges (thicker, colored by weight)
    edge_x_aa = []
    edge_y_aa = []
    edge_weights = []
    for edge in G.edges(data=True):
        if G.nodes[edge[0]].get('type') == 'article' and G.nodes[edge[1]].get('type') == 'article':
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x_aa.extend([x0, x1, None])
            edge_y_aa.extend([y0, y1, None])
            edge_weights.append(edge[2].get('weight', 1))
    
    if edge_x_aa:
        # Normalize edge weights for width (1-5 range)
        max_weight = max(edge_weights) if edge_weights else 1
        normalized_widths = [1 + (w / max_weight) * 4 for w in edge_weights]
        avg_width = sum(normalized_widths) / len(normalized_widths) if normalized_widths else 2
        
        edge_trace_aa = go.Scatter(
            x=edge_x_aa, y=edge_y_aa,
            line=dict(width=avg_width, color='#00FFFF'),
            hoverinfo='none',
            mode='lines',
            showlegend=False,
            opacity=0.7
        )
        edge_traces.append(edge_trace_aa)
    
    # Create node traces
    # Article nodes
    article_x = [pos[node][0] for node in article_nodes]
    article_y = [pos[node][1] for node in article_nodes]
    article_text = [G.nodes[node].get('title', node) for node in article_nodes]
    article_scores = [G.nodes[node].get('score', 0) for node in article_nodes]
    
    article_trace = go.Scatter(
        x=article_x, y=article_y,
        mode='markers+text',
        hoverinfo='text',
        text=[f"📄" for _ in article_nodes],
        hovertext=[f"<b>{title}</b><br>Year: {G.nodes[node].get('year', 'N/A')}<br>Score: {score:.3f}" 
                   for node, title, score in zip(article_nodes, article_text, article_scores)],
        textposition="top center",
        marker=dict(
            size=[15 + score * 20 for score in article_scores],
            color=article_scores,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(
                title="Relevance",
                thickness=15,
                len=0.7,
                x=1.1
            ),
            line=dict(width=2, color='white')
        ),
        name='Articles',
        showlegend=True
    )
    
    # Keyword nodes
    keyword_x = [pos[node][0] for node in keyword_nodes]
    keyword_y = [pos[node][1] for node in keyword_nodes]
    keyword_sizes = [G.degree(node) * 3 for node in keyword_nodes]
    
    keyword_trace = go.Scatter(
        x=keyword_x, y=keyword_y,
        mode='markers+text',
        hoverinfo='text',
        text=keyword_nodes,
        hovertext=[f"<b>{node}</b><br>Connections: {G.degree(node)}" for node in keyword_nodes],
        textposition="top center",
        textfont=dict(size=10, color='#00FFFF'),
        marker=dict(
            size=keyword_sizes,
            color='#4B0082',
            line=dict(width=1, color='#00FFFF')
        ),
        name='Keywords',
        showlegend=True
    )
    
    # Dataset nodes (if any)
    traces = [article_trace, keyword_trace]
    if dataset_nodes:
        dataset_x = [pos[node][0] for node in dataset_nodes]
        dataset_y = [pos[node][1] for node in dataset_nodes]
        dataset_text = [G.nodes[node].get('title', node)[:30] for node in dataset_nodes]
        
        dataset_trace = go.Scatter(
            x=dataset_x, y=dataset_y,
            mode='markers+text',
            hoverinfo='text',
            text=[f"🔬" for _ in dataset_nodes],
            hovertext=[f"<b>Dataset: {title}</b><br>OSDR ID: {node}<br>URL: {G.nodes[node].get('url', 'N/A')}" 
                       for node, title in zip(dataset_nodes, dataset_text)],
            textposition="top center",
            marker=dict(
                size=18,
                color='#00FF88',
                symbol='diamond',
                line=dict(width=2, color='white')
            ),
            name='OSDR Datasets',
            showlegend=True
        )
        traces.append(dataset_trace)
    
    # Create figure
    graph_title = '<b>Knowledge Graph: Articles, Keywords & Datasets</b>' if dataset_nodes else '<b>Knowledge Graph: Articles & Keywords</b>'
    fig = go.Figure(data=edge_traces + traces,
                    layout=go.Layout(
                        title=graph_title,
                        titlefont_size=20,
                        showlegend=True,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        plot_bgcolor='#0B0C1F',
                        paper_bgcolor='#0B0C1F',
                        font=dict(color='white'),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        height=700
                    ))
    
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
