#CECS 427: Assignment game theory 
#10/21/2025
#Ryan Tomas
#Nick Fan

import argparse
import itertools
import networkx as nx
import matplotlib.pyplot as plt

def parse_arguments():
    parser = argparse.ArgumentParser(description="Traffic Equilibrium and Social Optimum Analysis.")
    parser.add_argument("graph_file", help="Path to the directed .gml file")
    parser.add_argument("n", type=int, help="Number of vehicles")
    parser.add_argument("initial", type=int, help="Initial node")
    parser.add_argument("final", type=int, help="Final node")
    parser.add_argument("--plot", action="store_true", help="Plot graph and cost functions")
    return parser.parse_args()

def load_graph(filepath):
    """Load directed graph from .gml file"""
    G = nx.read_gml(filepath, label="id")
    if not G.is_directed():
        G = G.to_directed()
    return G

def cost(a, b, x):
    """Linear cost function"""
    return a * x + b

def all_paths(G, source, target):
    """All simple paths from source to target"""
    return list(nx.all_simple_paths(G, source, target))

def distribute_vehicles(n, num_paths):
    """All integer distributions of n vehicles across num_paths"""
    for combo in itertools.product(range(n+1), repeat=num_paths):
        if sum(combo) == n:
            yield combo

def edge_flows_from_path_distribution(G, paths, flow_distribution):
    """Compute total vehicles per edge given path flow distribution"""
    edge_flows = {(u, v): 0 for u, v in G.edges()}
    for path, num_cars in zip(paths, flow_distribution):
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            edge_flows[(u, v)] += num_cars
    return edge_flows

def compute_path_cost(G, path, edge_flows):
    """Compute total cost of a path given current edge flows"""
    total = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        a, b = G[u][v]["a"], G[u][v]["b"]
        total += cost(a, b, edge_flows[(u, v)])
    return total

def total_cost(G, edge_flows):
    """Total social cost = sum over edges of (x_e * c(x_e))"""
    total = 0.0
    for (u, v), x in edge_flows.items():
        a, b = G[u][v]["a"], G[u][v]["b"]
        total += x * cost(a, b, x)
    return total

def find_social_optimum(G, paths, n):
    """Brute-force search for flow minimizing total cost"""
    best_cost = float("inf")
    best_distribution = None
    best_edge_flows = None

    for dist in distribute_vehicles(n, len(paths)):
        edge_flows = edge_flows_from_path_distribution(G, paths, dist)
        c = total_cost(G, edge_flows)
        if c < best_cost:
            best_cost = c
            best_distribution = dist
            best_edge_flows = edge_flows

    return best_distribution, best_edge_flows, best_cost

def is_equilibrium(G, paths, dist):
    """Check if current flow distribution is a Nash equilibrium"""
    edge_flows = edge_flows_from_path_distribution(G, paths, dist)
    path_costs = [compute_path_cost(G, p, edge_flows) for p in paths]

    for i, num_cars in enumerate(dist):
        if num_cars > 0:
            current_cost = path_costs[i]
            for j, other_cost in enumerate(path_costs):
                # if any other path is cheaper → not equilibrium
                if other_cost + 1e-9 < current_cost:
                    return False
    return True

def find_nash_equilibrium(G, paths, n):
    """Brute-force equilibrium search"""
    for dist in distribute_vehicles(n, len(paths)):
        if is_equilibrium(G, paths, dist):
            edge_flows = edge_flows_from_path_distribution(G, paths, dist)
            return dist, edge_flows
    return None, None

def print_results(paths, eq_dist, eq_flows, opt_dist, opt_flows, opt_cost):
    """Display results to terminal."""
    print("\n=== PATHS ===")
    for i, p in enumerate(paths):
        print(f"Path {i}: {p}")

    print("\n=== Nash Equilibrium ===")
    if eq_dist:
        for i, num in enumerate(eq_dist):
            print(f"  Path {i}: {num} vehicles")
        for e, x in eq_flows.items():
            print(f"  Edge {e}: {x} vehicles")
    else:
        print("  No equilibrium found.")

    print("\n=== Social Optimum ===")
    for i, num in enumerate(opt_dist):
        print(f"  Path {i}: {num} vehicles")
    for e, x in opt_flows.items():
        print(f"  Edge {e}: {x} vehicles")
    print(f"Total Social Cost: {opt_cost:.2f}")

def plot_graph(G):
    """Plot the graph."""
    pos = nx.spring_layout(G)
    edge_labels = {e: f"a={G[e[0]][e[1]]['a']}, b={G[e[0]][e[1]]['b']}" for e in G.edges()}
    nx.draw(G, pos, with_labels=True, node_color="lightblue", arrows=True)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    plt.title("Traffic Network")
    plt.show()

def plot_edge_costs(G):
    xs = range(0, 11)
    plt.figure()
    for (u, v) in G.edges():
        a, b = G[u][v]["a"], G[u][v]["b"]
        ys = [cost(a, b, x) for x in xs]
        plt.plot(xs, ys, label=f"{u}->{v}: {a}x+{b}")
    plt.xlabel("Flow (x)")
    plt.ylabel("Cost (c(x))")
    plt.legend()
    plt.title("Edge Cost Functions")
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    args = parse_arguments()
    G = load_graph(args.graph_file)
    n, s, t = args.n, args.initial, args.final

    paths = all_paths(G, s, t)
    if not paths:
        print(f"No paths found from {s} to {t}.")
        exit(1)

    # Compute results
    eq_dist, eq_flows = find_nash_equilibrium(G, paths, n)
    opt_dist, opt_flows, opt_cost = find_social_optimum(G, paths, n)

    print_results(paths, eq_dist, eq_flows, opt_dist, opt_flows, opt_cost)

    if args.plot:
        plot_graph(G)
        plot_edge_costs(G)