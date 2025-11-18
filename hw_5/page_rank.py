# web_crawler_strict_html_only_no_params.py
# ONLY visits and follows URLs ending with .html
# Exactly n nodes, no exceptions
# → REJECTS query parameters completely
# → Tighter graph layout
from typing import Tuple
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import networkx as nx
import matplotlib.pyplot as plt
import time
import random
import argparse
import sys
import collections
import os
import math

HEADERS = {'User-Agent': 'EducationalCrawler/1.0'}
TIMEOUT = 10

def die(msg: str, code: int = 2):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)

# Read input
def read_input(file: str) -> Tuple[str, str, str]:
    with open(file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    max_nodes = int(lines[0])
    domain = lines[1].rstrip('/').replace('https://', '').replace('http://', '').split('/')[0]
    start_urls = [url for url in lines[2:] if url.strip() and url.endswith('.html')]

    return max_nodes, domain, start_urls

def crawl(max_nodes: int, domain: str, start_urls: list):
    # Graph and control sets
    G = nx.DiGraph()
    visited = set()
    queue = start_urls.copy()
    crawled = 0

    max_depth = math.ceil(max_nodes / 10)

    while queue and len(G) < max_nodes:
        url = queue.pop(0)
        if url in visited:
            continue

        try:
            print(f"[{len(G)}/{max_nodes}] GET → {url}")
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if r.status_code != 200:
                visited.add(url)
                continue
            if 'text/html' not in r.headers.get('Content-Type', ''):
                visited.add(url)
                continue

            soup = BeautifulSoup(r.text, 'html.parser')
            visited.add(url)
            crawled += 1

            # Extract only links that:
            # 1. End with .html
            # 2. Are in the same domain
            # 3. Have NO query parameters
            depth = 0
            for a in soup.find_all('a', href=True):
                candidate = urljoin(url, a['href'])
                p = urlparse(candidate)

                # Must be same domain
                if p.netloc != domain:
                    continue
                # Must be http/https
                if p.scheme not in ('http', 'https'):
                    continue
                # MUST end with .html
                if not p.path.endswith('.html'):
                    continue

                # === NEW: STRIP query parameters completely ===
                clean_url = urlunparse((
                    p.scheme,
                    p.netloc,
                    p.path,
                    '',      # params (deprecated anyway)
                    '',      # query → empty!
                    ''       # fragment → also removed for consistency
                ))

                # Remove trailing ? if it somehow remains
                target = clean_url.rstrip('?')

                if target == url:
                    continue

                G.add_edge(url, target)
                depth += 1

                # Only enqueue if not visited and we still need more nodes
                if target not in visited and target not in queue and len(G) < max_nodes:
                    queue.append(target)
                
                if depth > max_depth:
                    break

            time.sleep(random.uniform(0.6, 1.3))  # polite

        except Exception as e:
            print(f" Error: {e}")
            visited.add(url)

    if len(G) > max_nodes:
        nodes = list(G.nodes)[:max_nodes]
        G = G.subgraph(nodes).copy()
        print(f"Clipped to exactly {max_nodes} nodes")

    print(f"\nCrawling finished!")
    print(f"Pages crawled: {crawled} (all clean .html, no query params)")
    print(f"Graph nodes: {G.number_of_nodes()} | Edges: {G.number_of_edges()}")

    return G

# ----------------------------- Analysis ----------------------------------- #

def save_loglog_plot(G: nx.DiGraph, out_png: str = "degree_loglog.png"):
    if len(G) == 0:
        print("Graph is empty; skipping log-log plot.")
        return

    # total degree (in + out); drop zeros to avoid -inf on log axis
    degs = [d for _, d in G.degree() if d > 0]
    if not degs:
        print("All degrees are zero; skipping log-log plot.")
        return

    counts = collections.Counter(degs)
    x = sorted(counts.keys())
    y = [counts[k] for k in x]

    plt.figure(figsize=(7, 5))
    plt.loglog(x, y)
    plt.title("LogLog Plot")
    plt.xlabel("degree (log)")
    plt.ylabel("number of nodes (log)")
    plt.tight_layout()
    plt.savefig(out_png, dpi=180)
    print(f"Saved log-log plot to {out_png}")


def compute_and_write_pagerank(G: nx.DiGraph, out_path: str, alpha: float = 0.85):
    if len(G) == 0:
        die("Cannot run PageRank on an empty graph.")
    try:
        pr = nx.pagerank(G, alpha=alpha, max_iter=100, tol=1.0e-06)
    except nx.PowerIterationFailedConvergence as e:
        die(f"PageRank did not converge: {e}")
    ranked = sorted(pr.items(), key=lambda kv: (-kv[1], kv[0]))
    with open(out_path, "w", encoding="utf-8") as f:
        for url, score in ranked:
            f.write(f"{score:.12f}\t{url}\n")
    print(f"Wrote PageRank for {len(ranked)} nodes to {out_path}")


# ------------------------------ I/O --------------------------------------- #

def read_gml_graph(gml_path: str) -> nx.DiGraph:
    if not os.path.exists(gml_path):
        die(f"GML file not found: {gml_path}")
    try:
        G = nx.read_gml(gml_path)
    except Exception as e:
        die(f"Failed to read GML: {e}")
    if not isinstance(G, (nx.DiGraph, nx.MultiDiGraph)):
        G = nx.DiGraph(G)
    elif isinstance(G, nx.MultiDiGraph):
        G = nx.DiGraph(G)  # collapse multiedges
    return G

def write_gml_graph(G: nx.DiGraph, out_path: str):
    try:
        nx.write_gml(G, out_path)
        print(f"Wrote directed graph to {out_path}")
    except Exception as e:
        die(f"Failed to write GML: {e}")

def plot_graph(G: nx.Graph):
    # === Tighter, nicer layout ===
    plt.figure(figsize=(15, 15))
    pos = nx.spring_layout(
        G,
        k=5,              # reduced → nodes pulled closer
        iterations=120,      # more iterations for better convergence
        weight='weight',
        seed=42
    )

    nx.draw_networkx_edges(G, pos, alpha=0.4, edge_color='gray', arrows=True, arrowsize=10)
    nx.draw_networkx_nodes(G, pos, node_size=180, node_color='#a0c4ff',
                        edgecolors='darkblue', linewidths=1.4)

    labels = {}
    for node in G.nodes():
        name = node.split('/')[-1].replace('.html', '')
        if len(name) > 20:
            name = name[:17] + "..."
        labels[node] = name or "index"

    nx.draw_networkx_labels(G, pos, labels, font_size=9, font_family='sans-serif')

    plt.title(f"Web Graph: {len(G.nodes)} Nodes.",
            fontsize=18, pad=30, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig("crawler_graph.png", dpi=250, bbox_inches='tight', facecolor='white')
    plt.show()


# ------------------------------ Main -------------------------------------- #

def parse_args():
    p = argparse.ArgumentParser(
        description="Create a web graph (crawler or GML), compute PageRank, and optionally generate plots."
    )
    p.add_argument("--crawler", type=str, default=None,
                   help="Path to crawler.txt (max_nodes, domain, seeds). If given, crawling is used.")
    p.add_argument("--input", type=str, default=None,
                   help="Path to an existing directed graph in GML. Used when --crawler is not provided.")
    p.add_argument("--loglogplot", action="store_true",
                   help="Generate log-log plot of degree distribution (PNG).")
    p.add_argument("--crawler_graph", type=str, default=None,
                   help="If crawling, save resulting graph to this GML path.")
    p.add_argument("--pagerank_values", type=str, default=None,
                   help="Write PageRank scores here (required for grading examples).")

    # plot of the graph structure (11-node induced subgraph)
    p.add_argument("--plot", nargs="?", const="graph_plot.png", default=None,
                   help="Save an induced-subgraph (11 nodes) visualization to PNG (default: graph_plot.png).")
    p.add_argument("--plot_pick", choices=["first", "degree"], default="first",
                   help='How to choose the 11 nodes for the induced subgraph: "first" or "degree".')
    return p.parse_args()


def main():
    args = parse_args()

    G = None

    if args.crawler is not None:
        max_nodes, domain, start_urls = read_input(args.crawler)
        print(f"Config: Max {max_nodes} nodes | Domain: {domain}")
        print(f"Valid seed URLs: {len(start_urls)}\n")
        G = crawl(max_nodes, domain, start_urls)
        if args.crawler_graph:
            write_gml_graph(G, args.crawler_graph)
    else:
        if not args.input:
            die("You must provide either --crawler crawler.txt or --input graph.gml")
        print(f"Reading graph from {args.input} ...")
        G = read_gml_graph(args.input)
        print(f"Loaded graph: |V|={G.number_of_nodes()} |E|={G.number_of_edges()}")

    if args.loglogplot:
        save_loglog_plot(G)

    if args.pagerank_values:
        compute_and_write_pagerank(G, args.pagerank_values)
    else:
        print("Note: --pagerank_values not provided; PageRank results will not be written.")

    if args.plot:
        plot_graph(G)


if __name__ == "__main__":
    main()
