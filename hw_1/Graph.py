#CECS 427: Assignment Graphs 
#09/16/2025
#Ryan Tomas
import matplotlib.pyplot as plt #to graph the output
import argparse #this allows parmeters in the command line
import networkx as nx
import numpy as np

def input(fileName):
    """
    Reads a graph from the given .gml file and uses it for all subsequent operations.
    """
    graph = nx.read_gml(fileName)
    return graph

def create_random_graph(n,c):
    """
    This function is a Command_Line strcture which makes n nodes and edge probablity p = (c * ln n) /n
    Overrides --input command and nodes must be labeled with strings ("0", "1",..,"n-1")
    """
    p = c * (np.log(n)/n)
    graph = nx.gnp_random_graph(n, p)
    return graph

def multi_BFS(G,*sources):#need to fix this parameters
    """
    Accepts one or more starting nodes and computes BFS trees from each, storing all shortest paths. Each BFS tree must be independently visualized and compared.
    """
    trees = {}
    for s in sources:
        print(f"[multi_BFS] BFS from {s}")
        
        # BFS tree rooted at s
        tree = nx.bfs_tree(G, s)
        trees[s] = tree
        
        # Report some stats
        paths = dict(nx.single_source_shortest_path(G, s))
        print(f"  Reached {len(paths)} nodes")
        
        # Visualize tree
        plt.figure(figsize=(5, 4))
        nx.draw(tree, with_labels=True, node_color="lightgreen", edge_color="black")
        plt.title(f"BFS Tree from {s}")
        plt.show()

    # Optional: Compare coverage between BFS trees
    if len(sources) > 1:
        print("[multi_BFS] Comparing BFS trees...")
        covered_sets = {s: set(t.nodes()) for s, t in trees.items()}
        for s1 in sources:
            for s2 in sources:
                if s1 < s2:
                    overlap = covered_sets[s1] & covered_sets[s2]
                    print(f"  Overlap between {s1} and {s2}: {len(overlap)} nodes")
    
    return trees

def analyze(Graph):
    """
    Performs additional structural analyses on the graph, including:Connected Components, Cycle Detection, Isolated Nodes,Graph Density, Average Shortest Path Length
    """
    print("[analyze] Performing structural analysis...")

    #Connected components
    num_components = nx.number_connected_components(Graph)
    print(f"  Connected Components: {num_components}")

    #Cycle detection
    try:
        cycle = nx.find_cycle(Graph)
        print(f"  Contains cycle: Yes (example cycle: {cycle})")
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

def plot(graph):
    """
    visulaes the graph with Highlighted shortest paths from each BFS root node; Distinct styling for isolated nodes; Optional visualization of individual connected components.
    """
    nx.draw(graph, with_labels=True, node_color="lightblue", edge_color="gray")
    plt.show()

def output(graph, filename):
    """Saves the final graph, with all computed attributes (e.g., distances, parent nodes, component IDs), to the specified .gml file."""
    print(f"[output] Saving graph to {filename}")
    nx.write_gml(graph, filename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("graph_example")
    #if no input graph is given
    parser.add_argument("create_random_graph", nargs=2, type=float,
                        help= "creates a random graph: <num_nodes> <average degree of a node>")
    
    parser.add_argument("multi_BFS", nargs="+", type=int,
                        help="Accepts one or more starting nodes and computes BFS trees from each <node>")
    #if a input is graph is given
    parser.add_argument("input", nargs=1, type=str,
                        help="Acceaptes a string that is <fileName>")
    
    #other arguments
    parser.add_argument("analyze", action="store_true",
                        help="Analyze the graph structure")
    
    parser.add_argument("plot", action="store_true",
                        help="plot the graph structure")
    
    parser.add_argument("output", nargs=1, type=str,
                        help="Acceaptes a string that is <fileName>")

    args = parser.parse_args()
    #still need to add the logic of main
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
        plot(G)

    if args.output:
        output(G, args.output)