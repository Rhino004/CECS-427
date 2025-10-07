mkdir -p out/
python ./graph_analysis.py input_file.gml --components 3 --plot C --simulate_failure 5 --output out/output.gml
python ./graph_analysis.py input_file.gml --plot n --temporal_simulation out/edges.csv
python ./graph_analysis.py input_file.gml --verify_homophily --verify_balanced_graph --output out/verified_graph.gml