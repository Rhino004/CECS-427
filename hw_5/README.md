# PageRank Crawler

## Requirements
Python 3.9+
pip install networkx requests beautifulsoup4 matplotlib

## Outputs
- node_rank.txt: one line per node: <pagerank>\t<url>
- degree_loglog.png: log-log plot of degree distribution
- out_graph.gml: (optional) GML of crawled graph.

## Notes
- Crawler only visits HTML pages within the provided domain.
- Respectful throttling (0.25s delay/request).
- If you already have a GML file, use --input instead of --crawler.

### how to run 
` python ./page_rank.py --crawler crawlingFile.txt --loglogplot --crawler_graph out_graph.gml --pagerank_values node_rank.txt --plot `

` python ./page_rank.py --input input_graph.gml --loglogplot --pagerank_values node_rank.txt `
`  python ./page_rank.py --input input_graph.gml --loglogplot --pagerank_values node_rank.txt `