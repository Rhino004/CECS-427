#CECS 427: Assignment game theory 
#10/21/2025
#Ryan Tomas
#Nick Fan

import argparse
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from sympy import symbols, Eq, solve, diff

def load_graph(fileName):
    """
    Load a graph from an edge list file.
    """
    try:
        # Try reading as GML
        Graph = nx.read_gml(fileName)
        if not Graph.is_directed():
            raise nx.NetworkXError("Graph is not directed.")
        print(f"[input] Successfully loaded '{fileName}' as GML.")
        return Graph
    except FileNotFoundError:
        print(f"[input] Error: The file '{fileName}' does not exist.")
        return None
    except (nx.NetworkXError, OSError, ValueError) as e:
        print(f"[input] Error: Failed to read '{fileName}' as both GML and edge list: {e}")
        return None

def path_cost(edges, path):
    """
    Calculate the total cost of a given path.
    """
    a_total, b_total = 0, 0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        for (x, y), a, b in edges:
            if (x, y) == (u, v):
                a_total += a
                b_total += b
                break
        else:
            raise ValueError(f"Missing edge ({u}->{v}) in edge list.")
    return a_total, b_total

def compute_equilibrium(edges, paths, n):
    """Compute the travel (Nash) equilibrium for a 2-path network."""
    if len(paths) < 2:
        print("[equilibrium] Error: Need at least 2 paths between start and end.")
        return None

    f1 = symbols("f1", real=True)
    a1, b1 = path_cost(edges, paths[0])
    a2, b2 = path_cost(edges, paths[1])

    # Equal cost condition for both paths
    eq = Eq(a1 * f1 + b1, a2 * (n - f1) + b2)
    sol = solve(eq, f1)

    if not sol:
        print("[equilibrium] No valid equilibrium found.")
        return None

    f1_val = float(sol[0])
    f2_val = n - f1_val

    print("\n=== Travel Equilibrium (Nash) ===")
    print(f"Path 1: {paths[0]} | Flow: {f1_val:.2f}")
    print(f"Path 2: {paths[1]} | Flow: {f2_val:.2f}")
    cost_eq = a1 * f1_val + b1
    print(f"Equilibrium travel cost per driver: {cost_eq:.2f}")

    return f1_val, f2_val, cost_eq

def compute_social_optimum(edges, paths, n):
    """Compute the social optimum for a 2-path network."""
    if len(paths) < 2:
        print("[optimum] Error: Need at least 2 paths between start and end.")
        return None

    f1 = symbols("f1", real=True)
    a1, b1 = path_cost(edges, paths[0])
    a2, b2 = path_cost(edges, paths[1])

    # Total cost function
    total_cost = f1 * (a1 * f1 + b1) + (n - f1) * (a2 * (n - f1) + b2)
    d_total_cost = diff(total_cost, f1)
    sol = solve(Eq(d_total_cost, 0), f1)

    if not sol:
        print("[optimum] No valid social optimum found.")
        return None

    f1_val = float(sol[0])
    f2_val = n - f1_val

    print("\n=== Social Optimum ===")
    print(f"Path 1: {paths[0]} | Flow: {f1_val:.2f}")
    print(f"Path 2: {paths[1]} | Flow: {f2_val:.2f}")
    cost_opt = a1 * f1_val + b1
    print(f"Optimal travel cost per driver: {cost_opt:.2f}")

    return f1_val, f2_val, cost_opt

def plot_costs(edges, n):
    """Plot the linear cost functions of each edge."""
    plt.figure()
    x = np.linspace(0, n, 100)
    for (u, v), a, b in edges:
        y = a * x + b
        plt.plot(x, y, label=f"{u}->{v}: {a}x + {b}")
    plt.xlabel("Vehicles (x)")
    plt.ylabel("Cost (C)")
    plt.title("Edge Cost Functions")
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_graph(Graph, paths, start, end):
    """
    Plot the graph with drivers' paths highlighted.
    """
    pos = nx.spring_layout(Graph, seed=42)

    # Collect all edges that appear in any path
    highlighted_edges = set()
    for path in paths:
        for i in range(len(path) - 1):
            highlighted_edges.add((path[i], path[i + 1]))

    # Assign colors: red for highlighted edges, black for others
    edge_colors = [
        'red' if (u, v) in highlighted_edges else 'black'
        for u, v in Graph.edges()
    ]

    # Build edge labels showing cost functions
    edge_labels = {}
    for u, v, data in Graph.edges(data=True):
        a = data.get("a", 0)
        b = data.get("b", 0)
        edge_labels[(u, v)] = f"{a}x + {b}"

    # Draw the network
    nx.draw(
        Graph, pos,
        with_labels=True,
        node_color='lightblue',
        edge_color=edge_colors,
        node_size=600,
        arrows=True
    )
    # Draw edge labels (cost functions)
    nx.draw_networkx_edge_labels(Graph, pos, edge_labels=edge_labels, font_color="blue", font_size=9)


    # Highlight start and end nodes
    nx.draw_networkx_nodes(Graph, pos, nodelist=[start], node_color='green', node_size=800)
    nx.draw_networkx_nodes(Graph, pos, nodelist=[end], node_color='orange', node_size=800)

    # Legend
    red_patch = mpatches.Patch(color='red', label='Driver Paths')
    green_patch = mpatches.Patch(color='green', label='Start Node')
    orange_patch = mpatches.Patch(color='orange', label='End Node')
    plt.legend(handles=[red_patch, green_patch, orange_patch])
    plt.title("Traffic Network with Driver Paths Highlighted")
    plt.show()

def extract_costs(Graph):
    """
    Extract costs from graph edges.
    """
    edges = []
    for u, v, data in Graph.edges(data=True):
        try:
            a = float(data['a'])
            b = float(data['b'])
        except KeyError as e:
            print(f"[input] Error: Edge ({u}, {v}) is missing attribute {e}.")
            continue
        edges.append(((u, v), a, b))
    return edges

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Traffic Analysis using Game Theory")
    parser.add_argument("Graph", type=str, help="Path to the input file containing the graph data")
    parser.add_argument("drivers", type=int, help="Number of drivers in the simulation")
    parser.add_argument("start", type=str, help="Starting node for drivers")
    parser.add_argument("end", type=str, help="Ending node for drivers")
    parser.add_argument("--plot", 
                        help="Plot the graph with drivers' paths highlighted",
                        action="store_true")
    args = parser.parse_args()

    #checks if the file is a GML file
    if not args.Graph.endswith(".gml"):
        print(f"[input] Warning: '{args.Graph}' is not a .gml file.")
        exit(1)
    Graph = load_graph(args.Graph)
    if Graph is None:
        exit(1)
    print(f"Graph loaded with {Graph.number_of_nodes()} nodes and {Graph.number_of_edges()} edges.")
    edges = extract_costs(Graph)

    # List paths
    try:
        paths = list(nx.all_simple_paths(Graph, source=args.start, target=args.end))
    except nx.NetworkXNoPath:
        print(f"[input] No path found between {args.start} and {args.end}.")
        exit(1)

    print("\nAvailable paths:")
    for i, p in enumerate(paths):
        print(f"  Path {i+1}: {p}")

    if len(paths) < 2:
        print("\n[warning] Only one path found — equilibrium/optimum not applicable.")
        exit(0)

    # Compute equilibrium and optimum
    compute_equilibrium(edges, paths, args.drivers)
    compute_social_optimum(edges, paths, args.drivers)

    # Optional plotting
    if args.plot:
        plot_graph(Graph, paths, args.start, args.end)
        plot_costs(edges, args.drivers)