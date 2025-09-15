#CECS 427 - Graphs

**Team Members:**
- Ryan Tomas(028210102)
- Nick Fan(028347343)

Description:
This projoct is has one python file ('Graph.py') that takes parameters when initalizing.
It supports creating random Erdős–Rényi graphs, loading pre-defined graphs from `.gml` files, performing structural analyses, computing and visualizing BFS trees, plotting, and saving graphs.  

Key features:
- **Random Graph Generation**: Creates a graph with `n` nodes and edge probability `p = (c * ln(n)) / n`.  
- **Multi-Source BFS**: Runs BFS from one or more starting nodes and visualizes each BFS tree in a hierarchical layout.  
- **Analysis**: Reports connected components, cycles, isolated nodes, graph density, and average shortest path length.  
- **Visualization**: Plots the graph or BFS trees using `matplotlib`.  

# Requirements
- Python 3.11
- install dependencies:
    pip install networkx matplotlib numpy