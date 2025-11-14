import argparse
import collections
import math
import os
import sys
import time
from urllib.parse import urljoin, urldefrag, urlparse

import networkx as nx

# Third-party: requests & bs4 (BeautifulSoup), matplotlib for plotting
try:
    import requests
    from bs4 import BeautifulSoup
except Exception as e:
    print("Missing dependencies. Please install: requests, beautifulsoup4, networkx, matplotlib",
            file=sys.stderr)
    raise

import matplotlib
matplotlib.use("Agg")  # safe for headless use
import matplotlib.pyplot as plt

from urllib import robotparser


# ----------------------------- Utilities ---------------------------------- #

def die(msg: str, code: int = 2):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


def is_html_response(resp: requests.Response) -> bool:
    ctype = resp.headers.get("Content-Type", "")
    return resp.status_code == 200 and "text/html" in ctype.lower()


def normalize_url(base: str, href: str) -> str | None:
    """Join relative links, remove fragments, keep scheme/netloc/path/query."""
    if not href:
        return None
    try:
        u = urljoin(base, href)
        u, _frag = urldefrag(u)
        p = urlparse(u)
        if not p.scheme.startswith("http"):
            return None
        # normalize: drop default ports and normalize path
        netloc = p.hostname or ""
        if p.port:
            # keep port only if non-default
            default = (p.scheme == "http" and p.port == 80) or (p.scheme == "https" and p.port == 443)
            if not default:
                netloc = f"{netloc}:{p.port}"
        path = p.path or "/"
        query = f"?{p.query}" if p.query else ""
        return f"{p.scheme}://{netloc}{path}{query}"
    except Exception:
        return None


def same_domain(u: str, domain_root: str) -> bool:
    """Restrict to a single domain rooted at domain_root (prefix match on netloc+path)."""
    pu = urlparse(u)
    pr = urlparse(domain_root)
    # enforce same hostname (allow subpath restriction)
    return (pu.hostname == pr.hostname) and (pu.scheme == pr.scheme)


def extract_links(base_url: str, html: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        nu = normalize_url(base_url, a.get("href"))
        if nu:
            links.add(nu)
    return links


# ----------------------------- Crawler ------------------------------------ #

def load_crawler_file(path: str):
    if not os.path.exists(path):
        die(f"crawler file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    if len(lines) < 2:
        die("crawler file must have at least 2 lines: N and domain")
    try:
        n = int(lines[0])
    except ValueError:
        die("first line of crawler file must be an integer (max number of nodes)")
    domain = lines[1]
    seeds = lines[2:] or [domain]
    # normalize domain line to a full URL
    if not urlparse(domain).scheme:
        die("domain line must be a full URL including scheme, e.g., https://example.com")
    return n, domain.rstrip("/"), [s.rstrip("/") for s in seeds]


def allowed_by_robots(user_agent: str, robots_url: str, target_url: str) -> bool:
    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, target_url)
    except Exception:
        # Fail-open if robots fetch fails (common in assignments);
        # change to False if your instructor requires strict behavior.
        return True


def crawl_domain(max_nodes: int, domain_root: str, seeds: list[str],
                request_timeout: float = 8.0, throttle_s: float = 0.25) -> nx.DiGraph:
    ua = "CS-Pagerank-Crawler/1.0 (+educational; contact=noreply@example.com)"
    rob_url = urljoin(domain_root, "/robots.txt")
    G = nx.DiGraph()
    q = collections.deque()

    # init queue with seed URLs in domain
    seedset = []
    for s in seeds:
        nu = normalize_url(domain_root, s)
        if nu and same_domain(nu, domain_root):
            seedset.append(nu)
    if not seedset:
        die("No valid seeds in domain for crawling.")

    for s in seedset:
        q.append(s)

    visited = set()

    session = requests.Session()
    session.headers.update({"User-Agent": ua})

    while q and len(G) < max_nodes:
        url = q.popleft()
        if url in visited:
            continue
        visited.add(url)

        if not allowed_by_robots(ua, rob_url, url):
            continue

        try:
            resp = session.get(url, timeout=request_timeout, allow_redirects=True)
        except requests.RequestException:
            continue

        # Only HTML pages
        if not is_html_response(resp):
            continue

        G.add_node(url)
        try:
            links = extract_links(resp.url, resp.text)
        except Exception:
            links = set()

        # Only keep links in same domain and to HTML-looking paths (skip binaries quickly)
        outlinks = set()
        for v in links:
            if not same_domain(v, domain_root):
                continue
            lower = v.lower()
            if any(lower.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".pdf",
                                                    ".svg", ".zip", ".tar", ".gz", ".mp4", ".mp3")):
                continue
            outlinks.add(v)

        for v in outlinks:
            G.add_edge(url, v)
            if v not in visited and v not in q and len(G) < max_nodes:
                q.append(v)

        # gentle throttle
        time.sleep(throttle_s)

    return G


# ----------------------------- Analysis ----------------------------------- #

def save_loglog_plot(G: nx.DiGraph, out_png: str = "degree_loglog.png"):
    if len(G) == 0:
        print("Graph is empty; skipping log-log plot.")
        return
    # Use total degree distribution (in+out)
    degrees = [deg for _node, deg in G.degree()]
    counts = collections.Counter(degrees)
    x = sorted(k for k in counts if k > 0)
    y = [counts[k] for k in x]
    plt.figure(figsize=(6, 4.5))
    plt.loglog(x, y, marker="o", linestyle="None")
    plt.xlabel("Degree (log)")
    plt.ylabel("#Nodes (log)")
    plt.title("Degree distribution (log-log)")
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
    # sort by score desc, then by url
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
        # make directed if needed
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


# ------------------------------ Main -------------------------------------- #

def parse_args():
    p = argparse.ArgumentParser(
        description="Create a web graph (crawler or GML), compute PageRank, and optionally plot log-log degree distribution."
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
    return p.parse_args()


def main():
    args = parse_args()

    if args.crawler:
        max_nodes, domain_root, seeds = load_crawler_file(args.crawler)
        print(f"Crawling up to {max_nodes} pages in domain {domain_root} ...")
        G = crawl_domain(max_nodes, domain_root, seeds)
        print(f"Crawled graph: |V|={G.number_of_nodes()} |E|={G.number_of_edges()}")
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

if __name__ == "__main__":
    main()
