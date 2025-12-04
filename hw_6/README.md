# CECS-427 Network Dynamic Population Model

**Team Members:**
- Ryan Tomas(028210102)
- Nick Fan(028347343)

## Requirements
Python 3.9+
pip install networkx matplotlib

# Description:
The program reads a graph with a file type of GML. Then it will run simulations a spread of a viruas across a population. This is possible with the use of casscabing behavior. 
This project provides a command-line simulation tool, dynamic_population.py, for modeling:

Cascade activation on a directed graph (threshold model)

COVID-19 epidemic spread using a SIRS model with optional shelter-in-place and vaccination dynamics

The program accepts a directed graph in GML format, simulates the chosen process, and optionally visualizes the results.

### how to run 
` python ./dynamic_population.py cascadebehaviour.gml --action cascade --initiator 1,2,5 --threshold 0.33 --plot `

` python ./dynamic_population.py cascadebehaviour.gml --action covid  --initiator 3,5 --probability_of_infection 0.02 --probability_of_death 0.01 --lifespan 100 --shelter 0.3 --vaccination 0.24 --interactive --plot `
