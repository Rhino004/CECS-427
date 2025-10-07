#CECS 427 - Homework 2 Graph Analysis

**Team Members:**
- Ryan Tomas(028210102)
- Nick Fan(028347343)

Description:
In this project we only had to make one python file "Graph_analysis.py" that takes multiple parameters. However this program has to take a '.gml' file. Each parameters analysis different parts of the given graph.
--components n
Partition the graph into n communities using the Girvan–Newman method.
--robustness_check k	Perform multiple simulations of k random edge failures and report network robustness metrics.
--split_output_dir path	(Optional) Export each detected community to a separate .gml file in the given directory.
--verify_homophily	Performs a t-test to determine if nodes with similar attributes are more likely to connect (homophily).
--verify_balanced_graph	Checks if the signed graph is structurally balanced (no cycles with odd number of negative edges).
--simulate_failures k	Randomly removes k edges, measuring the resulting changes in:
– Average shortest path
– Number of components
– Betweenness centrality.
--temporal_simulation file.csv	Loads a CSV of edge additions/removals (source,target,timestamp,action) and animates graph evolution.
--output out.gml	Save the final analyzed graph (with computed attributes) to the given .gml file.
The program runs directly from the terminal and uses command-line options to control all major analysis operations.

# Setup
- Python >= 3.11
- install dependencies:

    `pip install networkx matplotlib numpy pandas scipy` or `pip install -r requirements.txt` 

# Running the code
Example commands: 
`python ./graph_analysis.py input_file.gml --components 3 --plot C --simulate_failure 5 --output output.gml`
`python ./graph_analysis.py input_file.gml --plot n --temporal_simulation edges.csv`
`python ./graph_analysis.py input_file.gml --verify_homophily --verify_balanced_graph --output out/verified_graph.gml` 
