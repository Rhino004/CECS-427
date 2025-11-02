#CECS 427 - Homework 3 Game Theory 

**Team Members:**
- Ryan Tomas(028210102)
- Nick Fan(028347343)

Description:
IN this assigment we are read a driected network graph off a gml file. When reading the graph we are doing a Nash Equilibriumm where no driver can reduce their travel cost by switching paths and a social optimum when the traffic disrubiton that minimizes total system cost. When running the traffic_analysis.py it takes a GML file, amount of drivers, starting node, and end nodes. There is a option to show the graph with --plot.
# Setup
- Python >= 3.11
- install dependencies:

    `pip install networkx matplotlib` or `pip install -r requirements.txt` 

# Running the code
Example commands with GML file called traffic.gml and traffic2.gml:  
`python ./traffic_analysis.py traffic.gml 4 0 3 --plot`
`python ./traffic_analysis.py traffic.gml 4 1 3 --plot`
`python ./traffic_analysis.py traffic2.gml 4 0 4 --plot`
`python ./traffic_analysis.py traffic2.gml 4 0 5 --plot`

