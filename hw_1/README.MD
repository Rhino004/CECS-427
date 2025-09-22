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

# Setup
- Python >= 3.11
- install dependencies:

    `pip install networkx matplotlib numpy` or `pip install -r requirements.txt` 

# Running the code
Example commands: 

To generate: `python ./Graph.py --create_random_graph 200 1.5 --multi_BFS 0 5 20 --analyze --plot --output out/final_graph.gml` 

If generating a graph (as in the above command), you should see the resulting graph's BFS 0, 5, 20, then itself consecutively as you close each window:
[from0](./images/from0.png)
[from5](./images/from5.png)
[graph](./images/graph.png)

To view: `python ./graph.py --input out/final_graph.gml --analyze --plot`

