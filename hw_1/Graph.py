#CECS 427: Assignment Graphs 
#09/16/2025
#Ryan Tomas
#Nick Fan
import matplotlib.pyplot as plt #to graph the output
import matplotlib.patches as mpatches
import argparse #this allows parmeters in the command line
import networkx as nx
import numpy as np
from pathlib import Path

def input(fileName):
    """
    Reads a graph from the given .gml file and uses it for all subsequent operations.
    """
    try:

        # Convert to simple undirected graph (remove direction/multi edges if any)
        graph = nx.Graph(nx.read_gml(fileName))
        # Normalize node labels to strings for consistency
        return nx.relabel_nodes(graph, lambda x: str(x))
    except FileNotFoundError:
        print(f"[input]The File {fileName} doesn't exist")
    except (nx.NetworkXError, OSError, ValueError) as e:
        print(f"[input] Error: Could not read graph from '{fileName}': {e}")
        return None

def create_random_graph(n,c):
    """
    This function is a Command_Line strcture which makes n nodes and edge probablity p = (c * ln n) /n
    Overrides --input command and nodes must be labeled with strings ("0", "1",..,"n-1")
    """
    if n <= 0: raise ValueError("n must be positive.")
    p =  max(0.0, min(1.0, float(c * (np.log(n)/n)))) # we find the probabilty, clamp 0-1 range
    graph = nx.erdos_renyi_graph(n, p)
    graph = nx.relabel_nodes(graph, lambda x: str(x)) #making the nodes into string
    return graph

def hierarchical_pos(tree, root):
    """
    This function is to help neetly organize the BFS tree
    when plotting
    """
    def _hierarchy_pos(node, left, right, depth=0, pos=None):
        if pos is None:
            pos = {}
        # Place node in the center of its allocated horizontal space
        pos[node] = ((left + right) / 2, -depth)
        children = list(tree.neighbors(node))
        if not children:
            return pos
        dx = (right - left) / max(1, len(children))  #divide space
        for i, child in enumerate(children):
            child_left = left + i * dx
            child_right = left + (i + 1) * dx
            _hierarchy_pos(child, child_left, child_right, depth + 1, pos)
        return pos

    return _hierarchy_pos(root, -2, 2)

def multi_BFS(G, *sources):
    """
    Accepts one or more starting nodes and computes BFS trees from each, storing all shortest paths.
    Each BFS tree is independently visualized in a hierarchical layout.
    """
    if G is None:
        print("[multi_BFS] Error: Graph is not defined.")
        return {}
    converted_sources = []
    for s in sources: # go through the parameters given
        if s in G:
            converted_sources.append(s)
        elif isinstance(s, str) and s.isdigit() and int(s) in G:
            converted_sources.append(int(s))
        else:
            print(f"[multi_BFS] Skipping {s}: not in graph")
    if not converted_sources:
        print("[multi_BFS] No valid source nodes found")
        return {}

    trees = {}
    for s in converted_sources:
        print(f"[multi_BFS] BFS from {s}")
        
        # BFS tree rooted at s
        tree = nx.bfs_tree(G, s)
        trees[s] = tree
        
        # Report stats
        paths = dict(nx.single_source_shortest_path(G, s))
        print(f"  Reached {len(paths)} nodes")
        
        # Visualize tree hierarchically
        pos = hierarchical_pos(tree, s)
        plt.figure(figsize=(7, 7))
        nx.draw(tree, pos, with_labels=True, node_color="lightgreen", edge_color="black", node_size = 500)
        plt.title(f"BFS Tree from {s}")
        plt.gcf().canvas.manager.set_window_title(f"BFS Tree from {s}")
        plt.show()

    # Compare coverage if multiple BFS sources
    if len(converted_sources) > 1:
        print("[multi_BFS] Comparing BFS trees...")
        covered_sets = {s: set(t.nodes()) for s, t in trees.items()}
        for i, s1 in enumerate(converted_sources):
            for s2 in converted_sources[i+1:]:
                overlap = covered_sets[s1] & covered_sets[s2]
                print(f"  Overlap between {s1} and {s2}: {len(overlap)} nodes")
    
    return trees

def analyze(Graph):
    """
    Performs additional structural analyses on the graph, including:Connected Components,
    Cycle Detection, Isolated Nodes,Graph Density, Average Shortest Path Length
    """
    print("[analyze] Performing structural analysis...")

    #Connected components
    num_components = nx.number_connected_components(Graph)
    print(f"  Connected Components: {num_components}")

    #Cycle detection
    try:
        cycles = nx.cycle_basis(Graph)
        for c in cycles:
            c.append(c[0])
        print(f"  Contains cycle: Yes (example cycle: {cycles})")
    except nx.exception.NetworkXNoCycle:
        print("  Contains cycle: No")

    #Isolated nodes
    isolated = list(nx.isolates(Graph))
    if isolated:
        print(f"  Isolated Nodes: {len(isolated)} -> {isolated}")
    else:
        print("  Isolated Nodes: None")

    #Graph density
    density = nx.density(Graph)
    print(f"  Graph Density: {density:.4f}")

    #Average shortest path length
    if nx.is_connected(Graph):
        avg_path_len = nx.average_shortest_path_length(Graph)
        print(f"  Avg Shortest Path Length: {avg_path_len:.4f}")
    else:
        print("  Avg Shortest Path Length: Not computed (graph is disconnected)")

def plot(graph, bfs_roots=None):
    """
    Visualizes the graph with highlighted shortest paths from each BFS root node.
    Distinct styling for isolated nodes, optional visualization of individual connected components.
    """
    pos = nx.spring_layout(graph, seed=123)  # deterministic layout

    # Identify isolated nodes
    isolated_nodes = list(nx.isolates(graph))
    normal_nodes = [n for n in graph.nodes() if n not in isolated_nodes]

    # Draw normal nodes and edges
    nx.draw_networkx_nodes(graph, pos, nodelist=normal_nodes, node_color="lightblue", node_size=500)
    nx.draw_networkx_edges(graph, pos, edge_color="gray")
    nx.draw_networkx_labels(graph, pos)

    # Draw isolated nodes differently
    if isolated_nodes:
        nx.draw_networkx_nodes(graph, pos, nodelist=isolated_nodes, node_color="red", node_size=500)

    # Highlight BFS shortest paths if roots are provided
    legend_patches = [
        mpatches.Patch(color="lightblue", label="Normal Node"),
        mpatches.Patch(color="red", label="Isolated Node")
    ]

    if bfs_roots:
        colors = ["green", "orange", "purple", "cyan", "magenta", "yellow"]  # cycle if needed
        for i, root in enumerate(bfs_roots):
            if root in graph:
                color = colors[i % len(colors)]
                paths = nx.single_source_shortest_path(graph, root)
                for target, path in paths.items():
                    if len(path) > 1:
                        edges_in_path = list(zip(path[:-1], path[1:]))
                        nx.draw_networkx_edges(graph, pos, edgelist=edges_in_path, width=2.5, edge_color=color)
                # Add legend entry for this root
                legend_patches.append(mpatches.Patch(color=color, label=f"BFS from {root}"))

    plt.title("Graph Visualization")
    plt.legend(handles=legend_patches, loc="upper right")
    plt.show()

def output(graph, filename):
    """Saves the final graph, with all computed attributes
    (e.g., distances, parent nodes, component IDs), to the specified .gml file.
    """
    try:
        print(f"[output] Saving graph to {filename}")
        nx.write_gml(graph, Path(filename))
    except Exception as e:
        print(f"[output] Error: Could not save graph to '{filename}': {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("graph_example")
    #if no input graph is given
    parser.add_argument("--create_random_graph", nargs=2, type=float,
                        help= "creates a random graph: <num_nodes> <average degree of a node>")
    
    parser.add_argument("--multi_BFS", nargs="+", type=str,
                        help="Accepts one or more starting nodes and computes BFS trees from each <node>")
    #if a input is graph is given
    parser.add_argument("--input", type=str,
                        help="Accepts a string that is <fileName>")
    
    #other arguments
    parser.add_argument("--analyze", action="store_true",
                        help="Analyze the graph structure")
    
    parser.add_argument("--plot", action="store_true",
                        help="plot the graph structure")
    
    parser.add_argument("--output", type=str,
                        help="Accepts a string that is <fileName>")

    args = parser.parse_args()
    G = None
    if args.create_random_graph:
        n, c = args.create_random_graph
        G = create_random_graph(int(n), c)
    elif args.input:
        G = input(args.input)

    if G is None:
        raise ValueError("You must create a random graph or load one with --input")

    if args.multi_BFS:
        multi_BFS(G, *args.multi_BFS)

    if args.analyze:
        analyze(G)

    if args.plot:
        plot(G, args.multi_BFS)

    if args.output:
        output(G, args.output)