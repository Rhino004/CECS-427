#CECS 427: Assignment Graphs 
#09/16/2025
#Ryan Tomas
#design, implement, and analyze a modular program capable of: 
#Generating and exporting Erdős–Rényi graphs; Importing and analyzing graphs from .gml files; 
#Performing multi-source BFS with path tracking; Identifying connected components; Detecting cycles and isolated nodes; 
#Visualizing graphs with annotated paths and substructures; Exporting computed metadata alongside the graph
import matplotlib #to graph the output
import argparse #this allows parmeters in the command line

def input(graph_file):
    """
    Reads a graph from the given .gml file and uses it for all subsequent operations.
    """
    pass

def create_random_graph(n,c):
    """
    This function is a Command_Line strcture which makes n nodes and edge probablity p = (c * ln n) /n
    Overrides --input command and nodes must be labeled with strings ("0", "1",..,"n-1")
    """
    pass

def multi_BFS(a1,a2):
    """
    Accepts one or more starting nodes and computes BFS trees from each, storing all shortest paths. Each BFS tree must be independently visualized and compared.
    """
    pass

def analyze():
    """
    Performs additional structural analyses on the graph, including:Connected Components, Cycle Detection, Isolated Nodes,Graph Density, Average Shortest Path Length
    """
    pass

def plot():
    """
    visulaes the graph with Highlighted shortest paths from each BFS root node; Distinct styling for isolated nodes; Optional visualization of individual connected components.
    """
    pass

def output(filename):
    """Saves the final graph, with all computed attributes (e.g., distances, parent nodes, component IDs), to the specified .gml file."""
    pass

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