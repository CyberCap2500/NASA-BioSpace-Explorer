import networkx as nx
import plotly.graph_objects as go
import pandas as pd
import re
from collections import Counter

def extract_entities(text):
    """Extract biological entities, research areas, and missions from text"""
    if not text or pd.isna(text):
        return {'organisms': [], 'research_areas': [], 'missions': [], 'keywords': []}
    
    text_lower = text.lower()
    
    # Define entity patterns
    organisms = ['mice', 'mouse', 'rat', 'human', 'yeast', 'bacteria', 'fungus', 'fungi', 
                 'plant', 'arabidopsis', 'cell', 'cells', 'aspergillus', 'candida',
                 'escherichia', 'salmonella', 'bac

def build_knowledge_graph(results, max_nodes=50):
    """Build a knowledge graph from search results"""
    G = nx.Graph()
    
    # Add article nodes and extract keywords
    article_keywords = {}
    
    for i, result in enumerate(results[:max_nodes]):
        article_id = result.get('pmc_id', f'Article_{i}')
        title = result.get('title', 'Untitled')[:50]
        
        # Add article node
        G.add_node(article_id, 
                   type='article',
                   title=title,
                   year=result.get('year', ''),
                   score=result.get('score', 0))
        
        # Extract keywords from title and abstract
        text = f"{result.get('title', '')} {result.get('abstract', '')}"
        keywords = extract_keywords(text, top_n=3)
        article_keywords[article_id] = keywords
        
        # Add keyword nodes and edges
        for keyword in keywords:
            if not G.has_node(keyword):
                G.add_node(keyword, type='keyword')
            G.add_edge(article_id, keyword, weight=1)
    
    # Connect articles that share keywords
    articles = [n for n, d in G.nodes(data=True) if d.get('type') == 'article']
    for i, art1 in enumerate(articles):
        for art2 in articles[i+1:]:
            shared_keywords = set(article_keywords.get(art1, [])) & set(article_keywords.get(art2, []))
            if shared_keywords:
                G.add_edge(art1, art2, weight=len(shared_keywords), shared=list(shared_keywords))
    
    return G

def create_graph_visualization(G):
    """Create an interactive Plotly visualization of the knowledge graph"""
    
    # Use spring layout for positioning
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    
    # Separate nodes by type
    article_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'article']
    keyword_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'keyword']
    
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
        edge_trace_aa = go.Scatter(
            x=edge_x_aa, y=edge_y_aa,
            line=dict(width=2, color='#00FFFF'),
            hoverinfo='none',
            mode='lines',
            showlegend=False,
            opacity=0.6
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
    
    # Create figure
    fig = go.Figure(data=edge_traces + [article_trace, keyword_trace],
                    layout=go.Layout(
                        title='<b>Knowledge Graph: Articles & Keywords</b>',
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
    
    stats = {
        'total_nodes': G.number_of_nodes(),
        'total_edges': G.number_of_edges(),
        'articles': len(article_nodes),
        'keywords': len(keyword_nodes),
        'avg_connections': sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0,
        'density': nx.density(G)
    }
    
    return stats
