mkdir -p out/
python ./Graph.py --create_random_graph 200 1.5 --multi_BFS 0 5 20 --analyze --plot --output out/final_graph.gml
python ./Graph.py --input out/final_graph.gml --analyze --plot