#CECS 427: Assignment Graphs 
#10/07/2025
#Ryan Tomas
#Nick Fan

import argparse
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from networkx.algorithms.community import girvan_newman

def load_graph(fileName):
    """
    Load a graph from an edge list file.
    """
    try:
        # Try reading as GML
        graph = nx.read_gml(fileName, label='id')

        # Normalize node labels to strings for consistency
        graph = nx.relabel_nodes(graph, str)
        print(f"[input] Successfully loaded '{fileName}' as GML.")
        return graph

    except FileNotFoundError:
        print(f"[input] Error: The file '{fileName}' does not exist.")
        return None

    except (nx.NetworkXError, OSError, ValueError) as e:
        print(f"[input] Warning: Could not read '{fileName}' as GML ({e}). Trying edge list instead...")
        try:
            graph = nx.read_edgelist(fileName, data=(('sign', int),))
            graph = nx.relabel_nodes(graph, str)
            print(f"[input] Successfully loaded '{fileName}' as edge list.")
            return graph
        except Exception as e2:
            print(f"[input] Error: Failed to read '{fileName}' as both GML and edge list: {e2}")
            return None

def compute_clustering_coefficient(Graph):
    """Compute clustering coefficient for all nodes"""
    return nx.clustering(Graph)

def compute_neighborhood_overlap(Graph):
    """Compute neighborhood overlap for all edges"""
    overlap = {}
    for u, v in Graph.edges():
        neighbors_u = set(Graph.neighbors(u))
        neighbors_v = set(Graph.neighbors(v))
        intersection = len(neighbors_u & neighbors_v)
        union = len(neighbors_u | neighbors_v)
        overlap[(u, v)] = intersection / union if union != 0 else 0
    return overlap

def partition_graph(Graph, n):
    """
    --components n:
    partition the graph into n components using the Girvan-Newman method
    """
    comp = girvan_newman(Graph)
    try:
        for _ in range(n - 1):
            communities = next(comp)
        return [list(c) for c in communities]
    except StopIteration:
        print(f"Warning: Cannot partition into {n} components. Returning current split.")
        return [list(c) for c in communities]

def plot(Graph, mode = "C"):
    """
    controls the visualization output
    C: Clustering coefficient (node size = CC, color = degree)
    N: Neighborhood overlap (edge thickness= NO, color = sum of degrees at and points)
    P: Plot the attributes e.g., node color, edge signs
    """
    pos = nx.spring_layout(Graph)
    mode = mode.upper()

    if mode == "C":  # Clustering coefficient
        cc = compute_clustering_coefficient(Graph)
        fig, ax = plt.subplots()
        fig.canvas.manager.set_window_title('Clustering Coefficient Visualization')
        nx.draw(
            Graph, pos, with_labels=True,
            node_size=[2000 * cc[n] for n in Graph.nodes()],
            node_color=[Graph.degree(n) for n in Graph.nodes()],
            cmap=plt.cm.viridis,
            edge_color="lightgrey"
        )

    elif mode == "N":  # Neighborhood overlap
        fig, ax = plt.subplots()
        fig.canvas.manager.set_window_title('Neighborhood Overlap Visualization')
        overlap = compute_neighborhood_overlap(Graph)
        edge_colors = [Graph.degree(u) + Graph.degree(v) for u, v in Graph.edges()]
        edge_widths = [5 * overlap[(u, v)] for u, v in Graph.edges()]
        nx.draw(
            Graph, pos, with_labels=True,
            node_size=500,
            node_color="lightblue",
            edge_color=edge_colors,
            width=edge_widths,
            edge_cmap=plt.cm.plasma
        )

    elif mode == "P":  # Plot attributes
        fig, ax = plt.subplots()
        fig.canvas.manager.set_window_title('Attribute Visualization')
        node_colors = [Graph.nodes[n].get("color", "grey") for n in Graph.nodes()]
        edge_colors = [Graph[u][v].get("sign", "black") for u, v in Graph.edges()]
        nx.draw(
            Graph, pos, with_labels=True,
            node_color=node_colors,
            edge_color=edge_colors
        )
        
    plt.show()

def verify_homophily(Graph, attr = "color"):
    """
    Statistical test (t-test) to check homophily using color-coded nodes attrbutes
    """
    same, diff = [], []
    for u, v in Graph.edges():
        if attr in Graph.nodes[u] and attr in Graph.nodes[v]:
            if Graph.nodes[u][attr] == Graph.nodes[v][attr]:
                same.append(1)
            else:
                diff.append(1)

    if same and diff:
        t, p = stats.ttest_ind(same, diff, equal_var=False)
        return {"t-statistic": t, "p-value": p}
    else:
        print("[verify_homophily] Not enough data for statistical test.")
        return None

def verify_balanced_graph(Graph):
    """
    Check if the signed graph is balanced using the BFS-based methods.
    """
    for cycle in nx.simple_cycles(Graph.to_directed()):
        prod = 1
        for i in range(len(cycle)):
            u, v = cycle[i], cycle[(i + 1) % len(cycle)]
            prod *= Graph[u][v].get("sign", 1)
        if prod < 0:
            return False
    return True

def output(graph, fileName):
    """
    Save the final graph with all updated node/edge attributes.
    """
    nx.write_gml(graph, fileName)

def safe_avg_shortest_path(G):
    if nx.is_connected(G):
        return nx.average_shortest_path_length(G)
    else:
        return np.mean([nx.average_shortest_path_length(G.subgraph(c)) for c in nx.connected_components(G)])

def simulate_failures(Graph, k):
    """
    Randomly remove k edges and analyze:
    Change in average shortest path
    Number of disconnected components
    Impact on betweenness centrality
    """
    original_avg_shortest_path = safe_avg_shortest_path(Graph)
    original_num_components = nx.number_connected_components(Graph)
    original_betweenness_centrality = nx.betweenness_centrality(Graph)

    # Randomly remove k edges
    edges = list(Graph.edges())
    np.random.shuffle(edges)
    for u, v in edges[:k]:
        Graph.remove_edge(u, v)

    # Analyze the impact
    new_avg_shortest_path = safe_avg_shortest_path(Graph)
    new_num_components = nx.number_connected_components(Graph)
    new_betweenness_centrality = nx.betweenness_centrality(Graph)

    # Report the findings
    return {
        "avg_shortest_path": (original_avg_shortest_path, new_avg_shortest_path),
        "num_components": (original_num_components, new_num_components),
        "betweenness_centrality": (original_betweenness_centrality, new_betweenness_centrality)
    }


def robustness_check(Graph, k):
    """
    Perform multiple simulations of k random edge failures and report:
    Average number of connected components
    Max/min component sizes
    Whether original clusters persist
    """
    
    num_simulations = 10
    component_counts = []
    component_sizes = []

    for _ in range(num_simulations):
        G_copy = Graph.copy()
        edges = list(G_copy.edges())
        np.random.shuffle(edges)
        for u, v in edges[:k]:
            G_copy.remove_edge(u, v)

        components = list(nx.connected_components(G_copy))
        component_counts.append(len(components))
        component_sizes.extend([len(c) for c in components])

    return {
        "avg_num_components": np.mean(component_counts),
        "max_component_size": max(component_sizes),
        "min_component_size": min(component_sizes)
    }
def temporal_simulation(Graph, fileName):
    """
    Load a time series of edge changes in CSV format (source,target,timestamp,action) and animate the graph evolution:
    """
    df = pd.read_csv(fileName)
    if df.empty:
        print(f"[temporal_simulation] '{fileName}' is empty or invalid.")
        return
    
    pos = nx.spring_layout(Graph)
    plt.ion()  # turn on interactive plotting
    fig, ax = plt.subplots()
    fig.canvas.manager.set_window_title("Temporal Simulation")
    pos = nx.spring_layout(Graph)

    for _, row in df.iterrows():
        u, v = str(row["source"]), str(row["target"])
        action = row["action"].lower()

        if action == "add":
            Graph.add_edge(u, v)
        elif action == "remove" and Graph.has_edge(u, v):
            Graph.remove_edge(u, v)

        ax.clear()
        nx.draw(Graph, pos, ax=ax, with_labels=True, node_color="lightblue", edge_color="grey")
        plt.title(f"t = {row['timestamp']} | {action} edge ({u}, {v})")
        plt.pause(0.5)

    plt.ioff()
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("Graph", 
                        help="name of the graph file")
    parser.add_argument("--components", 
                        help="number of components that you want to partition")
    parser.add_argument("--plot", 
                        help="The input can C, N, P, or T")
    parser.add_argument("--verify_homophily", action="store_true",
                        help="Check if the graph exhibits homophily")
    parser.add_argument("--verify_balanced_graph", action="store_true",
                        help="Check if the signed graph is balanced")
    parser.add_argument("--output", 
                        help="The name you want the output file to be")
    parser.add_argument("--simulate_failures", 
                        help="number of edges that would be randomly removed")
    parser.add_argument("--robustness_check",
                        help="Perform multiple simulations of k random edge failures and report:")
    parser.add_argument("--temporal_simulation",
                        help="name of the csv file that would animate the graph evolution")

    args = parser.parse_args()

    Graph = load_graph(args.Graph)
    print(f"Graph loaded with {Graph.number_of_nodes()} nodes and {Graph.number_of_edges()} edges.")
    # Perform requested analyses
    # Each function should print or return its results as appropriate
    #Partition the graph into n components
    if args.components:
        n = int(args.components)
        communities = partition_graph(Graph, n)
        print(f"Graph partitioned into {n} components: {communities}")
    #Robustness check
    if args.robustness_check:
        k = int(args.robustness_check)
        robustness_results = robustness_check(Graph, k)
        print(f"Robustness check results: {robustness_results}")
    #Temporal simulation
    if args.temporal_simulation:
        temporal_simulation(Graph, args.temporal_simulation)
    #Plotting
    if args.plot:
        plot(Graph, args.plot)
    #Homophily and balanced graph verification
    if args.verify_homophily:
        homophily_results = verify_homophily(Graph)
        if homophily_results:
            print(f"Homophily test results: {homophily_results}")
        else:
            print("Not enough data to perform homophily test.")
    
    if args.verify_balanced_graph:
        balanced_results = verify_balanced_graph(Graph)
        if balanced_results:
            print(f"Balanced graph test results: {balanced_results}")
        else:
            print("Not enough data to perform balanced graph test.")
    #Simulate failures
    if args.simulate_failures:
        k = int(args.simulate_failures)
        failure_results = simulate_failures(Graph, k)
        print(f"Simulation of failures results: {failure_results}")
    #Output the graph
    if args.output:
        output(Graph, args.output)
        print(f"Graph saved to {args.output}")