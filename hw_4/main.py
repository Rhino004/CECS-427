"""
Description:
    Reads a bipartite graph in GML format where sellers are nodes 0..n-1
    and buyers are nodes n..2n-1. Seller nodes should have a 'price' attribute
    (defaults to 0). Edges should have a valuation attribute (supported names:
    'valuation', 'value', 'weight').

    Runs an ascending-price market-clearing simulation:
      - Each buyer prefers seller(s) maximizing valuation - price
      - Compute max matching on the preference graph
      - If not perfect, find constricted sellers and increase their prices
      - Repeat until perfect matching (market cleared) or max rounds reached

Flags:
    --plot       : show a plot of the graph (and if --interactive, plot each round)
    --interactive: print round-by-round details
"""
import argparse
import os
import sys
import networkx as nx
import matplotlib.pyplot as plt

eps_default = 1.0  # price increment for constricted sellers each round
max_rounds = 500

# Helper: choose edge valuation attribute (first available)
keys = ("valuation", "value", "weight")


def read_graph(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' does not exist.")

    try:
        G = nx.read_gml(file_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read GML file: {e}")

    # GML often produces string node labels; attempt to coerce to ints if possible
    mapping = {}
    coerced = True
    for node in list(G.nodes):
        try:
            new = int(node)
        except Exception:
            coerced = False
            break
        mapping[node] = new
    if coerced:
        G = nx.relabel_nodes(G, mapping)

    # Validate node count: must be even and >= 2
    if len(G.nodes) == 0:
        raise ValueError("Input graph is empty.")
    if len(G.nodes) % 2 != 0:
        raise ValueError("Graph must contain even number of nodes (2n).")

    return G


def extract_val(G, u, v):
    """Return valuation for edge (u,v). Supports multiple attribute names."""
    data = G.get_edge_data(u, v, default={})
    for k in keys:
        if k in data:
            try:
                return float(data[k])
            except Exception:
                # fallback: if it's not coercible, raise
                raise ValueError(f"Edge ({u},{v}) valuation '{k}' not numeric: {data[k]}")
    # no valuation attribute found
    raise KeyError(f"No valuation attribute found on edge ({u},{v}). Expected one of {keys}.")


def ensure_prices(G, sellers):
    """Ensure each seller node has a numeric 'price' attribute; default 0.0."""
    for s in sellers:
        p = G.nodes[s].get("price", 0.0)
        try:
            p = float(p)
        except Exception:
            raise ValueError(f"Seller node {s} has non-numeric price: {p}")
        G.nodes[s]["price"] = p


def build_preference_graph(G, sellers, buyers):
    """
    For each buyer b, compute utilities u(s) = valuation(b,s) - price(s).
    Add edges (s, b) in preference graph for seller(s) achieving max utility for that buyer.
    Returns an undirected bipartite Graph with sellers on one side and buyers on the other.
    """
    P = nx.Graph()
    P.add_nodes_from(sellers, bipartite=0)
    P.add_nodes_from(buyers, bipartite=1)

    for b in buyers:
        # consider neighbors of b in original graph (should be sellers)
        neighbor_sellers = [s for s in G.neighbors(b) if s in sellers]
        if not neighbor_sellers:
            # buyer b has no incident seller edges — skip (will cause no perfect matching)
            continue

        best_util = None
        best_sellers = []
        for s in neighbor_sellers:
            try:
                val = extract_val(G, s, b) if G.has_edge(s, b) else extract_val(G, b, s)
            except Exception as e:
                raise RuntimeError(f"Error reading valuation between seller {s} and buyer {b}: {e}")
            price = G.nodes[s].get("price", 0.0)
            util = float(val) - float(price)
            if (best_util is None) or (util > best_util + 1e-12):
                best_util = util
                best_sellers = [s]
            elif abs(util - best_util) <= 1e-12:
                best_sellers.append(s)

        # Add edges from each best seller to buyer b (we add seller-buyer undirected edge)
        for s in best_sellers:
            P.add_edge(s, b)

    return P


def maximum_matching_bipartite(P, sellers):
    """
    Return maximum matching on bipartite graph P. The returned dict is matching with both directions.
    Uses networkx.bipartite.maximum_matching.
    """
    if len(P) == 0:
        return {}
    try:
        matching = nx.algorithms.bipartite.matching.maximum_matching(P, top_nodes=set(sellers))
        # networkx returns matching dict mapping nodes to partners for matched nodes only
        return matching
    except Exception as e:
        raise RuntimeError(f"Failed to compute maximum matching: {e}")


def alternating_reachable_sets(P, matching, sellers, buyers):
    """
    Using the matching, compute the set Z of vertices reachable from unmatched sellers
    by alternating paths (edges not-in-matching then edges-in-matching alternating).
    Returns (reachable_sellers, reachable_buyers).
    """
    # Normalize matching to map node->partner (matching may be missing unmatched nodes)
    match = dict(matching)  # shallow copy

    matched_sellers = {s for s in sellers if s in match}
    unmatched_sellers = [s for s in sellers if s not in match]

    reachable_s = set()
    reachable_b = set()
    # BFS queue: tuples (type,node) where type='s' or 'b'
    from collections import deque
    q = deque()

    for s in unmatched_sellers:
        reachable_s.add(s)
        q.append(("s", s))

    while q:
        t, node = q.popleft()
        if t == "s":
            # from seller, follow edges NOT in matching to buyers
            for nbr in P.neighbors(node):
                # edge node-nbr is not in matching iff match.get(node) != nbr
                if match.get(node) == nbr:
                    continue
                if nbr not in reachable_b:
                    reachable_b.add(nbr)
                    q.append(("b", nbr))
        else:  # t == 'b'
            # from buyer, follow matching edge if any to seller
            partner = match.get(node)
            if partner is not None and partner not in reachable_s:
                reachable_s.add(partner)
                q.append(("s", partner))

    return reachable_s, reachable_b


def find_constricted_sellers(P, matching, sellers, buyers):
    """
    Compute constricted sellers given preference graph P and matching.
    Using alternating reachability, constricted sellers = sellers \ reachable_s
    (these sellers are in the left part of the minimum vertex cover and constitute the constricted set).
    """
    reachable_s, reachable_b = alternating_reachable_sets(P, matching, sellers, buyers)
    constricted = set(sellers) - reachable_s
    return constricted


def update_prices(G, constricted_sellers, eps=eps_default):
    """Increase price of each seller in constricted_sellers by eps."""
    for s in constricted_sellers:
        G.nodes[s]["price"] = float(G.nodes[s].get("price", 0.0)) + float(eps)


def plot_market(G, sellers, buyers, matching=None, title=None):
    """Plot bipartite graph with prices and valuations as labels."""
    plt.clf()
    pos = {}
    # place sellers on left vertical, buyers on right vertical
    left_x, right_x = -1, 1
    sellers_sorted = sorted(sellers)
    buyers_sorted = sorted(buyers)

    for i, s in enumerate(sellers_sorted):
        pos[s] = (left_x, -i)
    for i, b in enumerate(buyers_sorted):
        pos[b] = (right_x, -i)

    node_colors = []
    labels = {}
    for n in sellers_sorted + buyers_sorted:
        if n in sellers:
            node_colors.append("lightblue")
            labels[n] = f"{n}\nP={G.nodes[n].get('price', 0.0):.2f}"
        else:
            node_colors.append("lightgreen")
            labels[n] = f"{n}"

    nx.draw_networkx_nodes(G, pos=pos, nodelist=sellers_sorted + buyers_sorted, node_color=node_colors, node_size=900)
    nx.draw_networkx_labels(G, pos=pos, labels=labels, font_size=8)

    # draw preference edges (we draw only edges that exist in original G between sellers and buyers)
    edge_labels = {}
    edges_to_draw = []
    for u, v, data in G.edges(data=True):
        if (u in sellers and v in buyers) or (v in sellers and u in buyers):
            a, b = (u, v) if u in sellers else (v, u)
            edges_to_draw.append((a, b))
            # find valuation attribute
            val = None
            for k in keys:
                if k in data:
                    val = data[k]
                    break
            if val is not None:
                edge_labels[(a, b)] = f"{float(val):.1f}"

    nx.draw_networkx_edges(G, pos=pos, edgelist=edges_to_draw)
    if edge_labels:
        nx.draw_networkx_edge_labels(G, pos=pos, edge_labels=edge_labels, font_size=7)

    if matching:
        # draw matching in red thicker
        match_edges = []
        for u, v in matching.items():
            # matching contains both directions; only draw seller->buyer pairs
            if u in sellers and v in buyers:
                match_edges.append((u, v))
        if match_edges:
            nx.draw_networkx_edges(G, pos=pos, edgelist=match_edges, edge_color="red", width=2.0)

    if title:
        plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.pause(0.3)


def market_clearing(G, plot=False, interactive=False, eps=eps_default, max_rounds=max_rounds):
    num_nodes = len(G.nodes)
    n = num_nodes // 2
    sellers = set(range(0, n))
    buyers = set(range(n, 2 * n))

    # Validate that graph nodes match expected seller/buyer sets
    missing = set(range(0, 2 * n)) - set(G.nodes)
    if missing:
        raise ValueError(f"Graph nodes do not match expected 0..{2*n-1}. Missing nodes: {sorted(missing)}")

    ensure_prices(G, sellers)

    round_num = 0
    final_matching = {}
    while round_num < max_rounds:
        round_num += 1
        if interactive:
            print(f"\n=== Round {round_num} ===")
            print("Prices (seller:price):", {s: G.nodes[s]['price'] for s in sorted(sellers)})

        # Build preference graph P (sellers--buyers) according to current prices
        P = build_preference_graph(G, sellers, buyers)

        # compute maximum matching
        matching = maximum_matching_bipartite(P, sellers) if len(P) > 0 else {}
        # compute matched pairs as seller->buyer only
        matched_pairs = {u: v for u, v in matching.items() if (u in sellers and v in buyers)}
        matched_count = len(matched_pairs)

        if interactive:
            print(f"Matching size: {matched_count} / {n}")
            if matched_pairs:
                print("Current matched pairs (seller->buyer):", matched_pairs)

        # Plot current market if requested
        if plot:
            plot_title = f"Round {round_num} — matched {matched_count}/{n}"
            plot_market(G, sellers, buyers, matching=matching, title=plot_title)

        if matched_count == n:
            if interactive:
                print("✅ Market cleared: perfect matching found.")
            final_matching = matched_pairs
            break

        # find constricted sellers using alternating reachability
        constricted = find_constricted_sellers(P, matching, sellers, buyers)
        if interactive:
            print("Constricted sellers (will have price increased):", sorted(constricted))

        if not constricted:
            # no constricted sellers detected but not perfect matching => likely buyers without edges or malformed graph
            # break to avoid infinite loop
            if interactive:
                print("No constricted sellers found but matching not perfect. Stopping.")
            final_matching = matched_pairs
            break

        # update prices for constricted sellers
        update_prices(G, constricted, eps=eps)

    else:
        # loop ended because max rounds reached
        print(f"Warning: reached max rounds ({max_rounds}). Market may not be cleared.")
        # derive final matching one more time
        P = build_preference_graph(G, sellers, buyers)
        matching = maximum_matching_bipartite(P, sellers) if len(P) > 0 else {}
        final_matching = {u: v for u, v in matching.items() if (u in sellers and v in buyers)}

    return final_matching, G


def parse_args():
    parser = argparse.ArgumentParser(description="Market-clearing algorithm on bipartite graphs (.gml)")
    parser.add_argument("input_file", help="Input .gml file describing the bipartite market")
    parser.add_argument("--plot", action="store_true", help="Plot the graph and (optionally) plot each round")
    parser.add_argument("--interactive", action="store_true", help="Show output for every round")
    parser.add_argument("--eps", type=float, default=eps_default, help="Price increment for constricted sellers (default 1.0)")
    parser.add_argument("--max_rounds", type=int, default=max_rounds, help="Maximum number of rounds (default 500)")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        G = read_graph(args.input_file)
    except Exception as e:
        print("Error loading graph:", e)
        sys.exit(1)

    # Validate expected bipartite labeling 0..2n-1
    if len(G.nodes) % 2 != 0:
        print("Error: graph must contain an even number of nodes (2n).")
        sys.exit(1)

    if args.plot:
        plt.ion()  # interactive mode for live updates
        plt.figure(figsize=(8, 6))

    try:
        matching, G_final = market_clearing(G, plot=args.plot, interactive=args.interactive, eps=args.eps, max_rounds=args.max_rounds)
    except Exception as e:
        print("Error during market-clearing:", e)
        sys.exit(1)

    # Print final result
    print("\n=== Final Result ===")
    if matching:
        print("Final matching (seller -> buyer):")
        for s in sorted(matching):
            print(f"  {s} -> {matching[s]}")
    else:
        print("No matching found.")

    print("\nFinal seller prices:")
    n = len(G_final.nodes) // 2
    for s in range(0, n):
        print(f"  Seller {s}: price = {G_final.nodes[s].get('price', 0.0):.4f}")

    if args.plot:
        # final static plot
        plot_market(G_final, set(range(0, n)), set(range(n, 2*n)), matching=matching, title="Final Market")
        plt.ioff()
        plt.show()


if __name__ == "__main__":
    main()
