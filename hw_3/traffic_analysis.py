#CECS 427: Assignment game theory 
#10/21/2025
#Ryan Tomas
#Nick Fan

import argparse
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def load_graph(fileName):
    """
    Load a graph from an edge list file.
    """
    try:
        # Try reading as GML
        Graph = nx.read_gml(fileName, label='id')
        # Normalize node labels to strings for consistency
        for u, v, data in Graph.edges(data=True):
            if "sign" in data:
                sign = data["sign"]
                if sign in ["+", "+1"]:
                    data["sign"] = 1
                elif sign in ["-", "-1"]:
                    data["sign"] = -1
                else:
                    try:
                        data["sign"] = int(sign)
                    except ValueError:
                        data["sign"] = 1  # default positive
        print(f"[input] Successfully loaded '{fileName}' as GML.")
        return Graph

    except FileNotFoundError:
        print(f"[input] Error: The file '{fileName}' does not exist.")
        return None
    except (nx.NetworkXError, OSError, ValueError) as e:
        print(f"[input] Error: Failed to read '{fileName}' as both GML and edge list: {e}")
        return None
    
def plot_graph(Graph, drivers, start, end):
    """
    Plot the graph with drivers' paths highlighted.
    """
    pos = nx.spring_layout(Graph)
    edge_colors = []
    for u, v in Graph.edges():
        if any((u, v) in path or (v, u) in path for path in drivers):
            edge_colors.append('red')
        else:
            edge_colors.append('black')

    nx.draw(Graph, pos, with_labels=True, edge_color=edge_colors, node_color='lightblue', node_size=500)
    
    # Highlight start and end nodes
    nx.draw_networkx_nodes(Graph, pos, nodelist=[start], node_color='green', node_size=700)
    nx.draw_networkx_nodes(Graph, pos, nodelist=[end], node_color='orange', node_size=700)

    # Create legend
    red_patch = mpatches.Patch(color='red', label='Driver Paths')
    green_patch = mpatches.Patch(color='green', label='Start Node')
    orange_patch = mpatches.Patch(color='orange', label='End Node')
    plt.legend(handles=[red_patch, green_patch, orange_patch])

    plt.title("Traffic Network with Driver Paths")
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Traffic Analysis using Game Theory")
    parser.add_argument("input_file", type=str, help="Path to the input file containing the graph data")
    parser.add_argument("--plot", 
                        help="The input are n (number of drivers), starting node, ending node",
                        nargs=3)
    args = parser.parse_args()

    #checks if the file is a GML file
    if not args.Graph.endswith(".gml"):
        print(f"[input] Warning: '{args.Graph}' is not a .gml file.")
        exit(1)
    Graph = load_graph(args.Graph)
    print(f"Graph loaded with {Graph.number_of_nodes()} nodes and {Graph.number_of_edges()} edges.")