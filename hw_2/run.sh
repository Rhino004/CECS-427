python ./graph_analysis.py graph.gml --components 3 --plot C --simulate_failure 5 --output out/output.gml
python ./graph_analysis.py graph.gml --plot T --temporal_simulation edges.csv
python ./graph_analysis.py graph.gml --verify_homophily --verify_balanced_graph --output out/verified_graph.gml