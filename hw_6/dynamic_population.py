import argparse
import os
import sys
import random

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx


# ----------------------------- Helpers --------------------------------- #

def error(msg: str, exit_code: int = 1):
    """Print an error to stderr and exit."""
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(exit_code)


def load_graph(gml_path: str) -> nx.DiGraph:
    """Load a graph from a GML file and return a directed NetworkX graph."""
    if not os.path.isfile(gml_path):
        error(f"File not found: {gml_path}")

    try:
        G = nx.read_gml(gml_path)
    except Exception as e:
        error(f"Failed to read GML file '{gml_path}': {e}")

    if G.number_of_nodes() == 0:
        error("The graph is empty (0 nodes). Nothing to simulate.")

    # Ensure directed
    if not isinstance(G, nx.DiGraph):
        G = G.to_directed()

    return G


def parse_initiators(initiator_str: str, G: nx.DiGraph):
    """Parse comma-separated initiator IDs and verify they exist in the graph."""
    if not initiator_str:
        return []

    try:
        # Try int-like node labels
        initiators = [int(x.strip()) for x in initiator_str.split(",") if x.strip() != ""]
    except ValueError:
        # Fall back to raw strings if not ints
        initiators = [x.strip() for x in initiator_str.split(",") if x.strip() != ""]

    # Node labels in the GML might be strings; convert types if needed
    converted = []
    for init in initiators:
        if init in G:
            converted.append(init)
        else:
            # Try string form
            s_init = str(init)
            if s_init in G:
                converted.append(s_init)
            else:
                error(f"Initiator node '{init}' not found in graph.")

    return converted


def parse_shelter_arg(s_arg: str, nodes):
    """
    Parse the shelter argument:
    - If numeric in [0,1]: return a random subset of that fraction.
    - Else treat as comma-separated node IDs.
    """
    if s_arg is None:
        return set()

    s_arg = str(s_arg).strip()
    if s_arg == "":
        return set()

    # Try to parse as fraction
    try:
        frac = float(s_arg)
        if frac < 0 or frac > 1:
            raise ValueError
        num = int(round(frac * len(nodes)))
        return set(random.sample(list(nodes), num))
    except ValueError:
        # Treat as node list
        raw_nodes = [x.strip() for x in s_arg.split(",") if x.strip() != ""]
        shelter_nodes = set()
        for rn in raw_nodes:
            candidate = rn
            # try int first
            try:
                candidate_int = int(rn)
                if candidate_int in nodes:
                    candidate = candidate_int
            except ValueError:
                pass

            if candidate not in nodes and str(candidate) in nodes:
                candidate = str(candidate)

            if candidate not in nodes:
                error(f"Sheltered node '{rn}' not found in graph.")
            shelter_nodes.add(candidate)
        return shelter_nodes


def validate_prob(name: str, val: float):
    if val < 0 or val > 1:
        error(f"{name} must be between 0 and 1. Got {val}.")


# ------------------------ Cascade Simulation --------------------------- #

def simulate_cascade(G: nx.DiGraph, initiators, threshold: float,
                     interactive: bool = False, plot: bool = False):
    """
    Simple threshold cascade model:

    - Nodes start inactive except initiators (active).
    - At each step, an inactive node becomes active if
      (# of active in-neighbors / # of in-neighbors) >= threshold.
    """
    validate_prob("threshold", threshold)

    nodes = list(G.nodes())
    active = set(initiators)
    for a in active:
        if a not in G:
            error(f"Initiator '{a}' not in graph.")

    inactive = set(nodes) - active

    # For plotting over time
    new_active_counts = [len(active)]  # round 0

    # Layout for visualization (fixed so the graph doesn't jump)
    pos = nx.spring_layout(G, seed=42)

    round_idx = 0

    # Prepare a single figure/axes for interactive mode
    fig, ax = None, None
    if interactive:
        plt.ion()
        fig, ax = plt.subplots()

    while True:
        round_idx += 1
        newly_active = set()

        for node in inactive:
            in_neighbors = list(G.predecessors(node))
            if not in_neighbors:
                continue
            active_in = sum(1 for n in in_neighbors if n in active)
            frac = active_in / len(in_neighbors)
            if frac >= threshold:
                newly_active.add(node)

        if not newly_active:
            # No more changes, stop
            break

        active |= newly_active
        inactive -= newly_active
        new_active_counts.append(len(newly_active))

        if interactive:
            ax.clear()
            colors = ["red" if n in active else "lightgray" for n in nodes]
            nx.draw(G, pos, with_labels=True, node_color=colors, ax=ax)

            # Legend (colors meaning)
            active_patch = mpatches.Patch(color='red', label='Active')
            inactive_patch = mpatches.Patch(color='lightgray', label='Inactive')

            ax.legend(handles=[active_patch, inactive_patch], loc="upper right")
            ax.set_title(f"Cascade dynamics - Round {round_idx}")

            fig.canvas.draw()
            fig.canvas.flush_events()

    if interactive:
        plt.ioff()
        plt.show()

    # Print result about completeness of cascade
    print("Cascade simulation complete.")
    print(f"Total nodes: {len(nodes)}")
    print(f"Active nodes: {len(active)}")
    print(f"Complete cascade: {len(active) == len(nodes)}")

    if plot:
        plt.figure()
        plt.plot(range(len(new_active_counts)), new_active_counts, marker="o")
        plt.xlabel("Round")
        plt.ylabel("New activations")
        plt.title("Cascade: new activations per round")
        plt.grid(True)
        plt.show()


# ------------------------ COVID / SIRS Simulation ---------------------- #

def simulate_covid(G: nx.DiGraph,
                   initiators,
                   p_infection: float,
                   p_death: float,
                   lifespan: int,
                   shelter_arg,
                   vaccination: float,
                   interactive: bool = False,
                   plot: bool = False):
    """
    COVID-like SIRS model with shelter-in-place and vaccination.

    States:
        S - Susceptible
        I - Infectious
        R - Recovered (temporary immunity)
        D - Dead
        V - Vaccinated (permanent immunity)

    Assumptions:
        - Infection duration before recovery: 14 time steps.
        - Immunity duration before R returns to S: 60 time steps.
        - Probability of infection from k infectious neighbors:
            P(infection) = 1 - (1 - p_infection)^k

        - Sheltered nodes:
            * Do not get infected (no new infections onto them).
            * Do not infect others (their infectious state doesn't spread).
        - Vaccinated nodes start as V and never change state.
    """
    if lifespan <= 0:
        error("lifespan must be positive.")

    validate_prob("probability_of_infection", p_infection)
    validate_prob("probability_of_death", p_death)
    validate_prob("vaccination", vaccination)

    nodes = list(G.nodes())

    # Initial states: everyone susceptible
    state = {n: "S" for n in nodes}

    # Infection/R & immunity timers (days in state)
    infection_time = {}
    immunity_time = {}

    # Vaccination
    num_vaccinated = int(round(vaccination * len(nodes)))
    vaccinated_nodes = set()
    if num_vaccinated > 0:
        # avoid vaccinating initiators
        available = list(set(nodes) - set(initiators))
        if num_vaccinated > len(available):
            num_vaccinated = len(available)
        vaccinated_nodes = set(random.sample(available, num_vaccinated))
        for n in vaccinated_nodes:
            state[n] = "V"

    # Shelter
    sheltered_nodes = parse_shelter_arg(shelter_arg, nodes)

    # Initiate infection
    for init in initiators:
        if init not in G:
            error(f"Initiator '{init}' not in graph.")
        if state[init] == "V":
            # Vaccinated initiator: override to infected (user choice dominated)
            pass
        state[init] = "I"
        infection_time[init] = 0

    # Parameters (assumed)
    infection_duration = 14   # days until recovery
    immunity_duration = 60    # days until susceptible again

    # For time series plot (new infections per day)
    new_infections_per_day = []

    pos = nx.spring_layout(G, seed=42)

    # Prepare a single figure/axes for interactive graph
    fig, ax = None, None
    if interactive:
        plt.ion()
        fig, ax = plt.subplots()

    # Legend for node states (used in interactive graph)
    legend_elements = [
        mpatches.Patch(facecolor='lightgray', edgecolor='black', label='Susceptible (S)'),
        mpatches.Patch(facecolor='red', edgecolor='black', label='Infected (I)'),
        mpatches.Patch(facecolor='green', edgecolor='black', label='Recovered (R)'),
        mpatches.Patch(facecolor='black', edgecolor='black', label='Dead (D)'),
        mpatches.Patch(facecolor='blue', edgecolor='black', label='Vaccinated (V)'),
        mpatches.Patch(facecolor='yellow', edgecolor='black', label='Sheltered (S)')
    ]

    for t in range(lifespan):
        newly_infected = set()
        newly_dead = set()
        newly_recovered = set()
        newly_susceptible = set()

        # 1) Infection step: S nodes may become I
        for n in nodes:
            if state[n] != "S":
                continue
            if n in sheltered_nodes:
                # Sheltered: no new infection
                continue

            # Infectious neighbors that are NOT sheltered
            inf_neighbors = [
                nb for nb in G.predecessors(n)
                if state.get(nb) == "I" and nb not in sheltered_nodes
            ]
            k = len(inf_neighbors)
            if k == 0:
                continue

            # Probability of infection from k neighbors
            p_inf = 1 - (1 - p_infection) ** k
            if random.random() < p_inf:
                newly_infected.add(n)

        # 2) Disease progression for infected nodes
        for n in [x for x in nodes if state[x] == "I"]:
            # Death
            if random.random() < p_death:
                newly_dead.add(n)
                continue

            # Survive this step
            infection_time[n] = infection_time.get(n, 0) + 1
            if infection_time[n] >= infection_duration:
                newly_recovered.add(n)

        # 3) Immunity waning for recovered
        for n in [x for x in nodes if state[x] == "R"]:
            immunity_time[n] = immunity_time.get(n, 0) + 1
            if immunity_time[n] >= immunity_duration:
                newly_susceptible.add(n)

        # 4) Apply updates in a consistent order
        for n in newly_dead:
            state[n] = "D"
            infection_time.pop(n, None)
            immunity_time.pop(n, None)

        for n in newly_infected:
            if state[n] in ["S"]:  # still susceptible
                state[n] = "I"
                infection_time[n] = 0

        for n in newly_recovered:
            if state[n] == "I":   # still infected and not dead
                state[n] = "R"
                infection_time.pop(n, None)
                immunity_time[n] = 0

        for n in newly_susceptible:
            if state[n] == "R":
                state[n] = "S"
                immunity_time.pop(n, None)

        new_infections_per_day.append(len(newly_infected))

        if interactive:
            ax.clear()
            color_map = []
            for n in nodes:
                s = state[n]
                if s == "S":
                    c = "lightgray"
                elif s == "I":
                    c = "red"
                elif s == "R":
                    c = "green"
                elif s == "D":
                    c = "black"
                elif s == "V":
                    c = "blue"
                else:
                    c = "lightgray"

                # Sheltered + susceptible highlighted in yellow
                if n in sheltered_nodes and s == "S":
                    c = "yellow"

                color_map.append(c)

            nx.draw(G, pos, with_labels=True, node_color=color_map, ax=ax)

            ax.legend(handles=legend_elements, loc="upper right")
            ax.set_title(f"COVID SIRS - Day {t + 1}")

            fig.canvas.draw()
            fig.canvas.flush_events()

    if interactive:
        plt.ioff()
        plt.show()

    # Final summary
    counts = {st: 0 for st in ["S", "I", "R", "D", "V"]}
    for s in state.values():
        if s in counts:
            counts[s] += 1

    print("COVID SIRS simulation complete.")
    print(f"Days simulated: {lifespan}")
    print(f"Total nodes:   {len(nodes)}")
    print("Final counts:")
    for k in ["S", "I", "R", "D", "V"]:
        print(f"  {k}: {counts[k]}")

    if plot:
        plt.figure()
        plt.plot(range(1, lifespan + 1), new_infections_per_day, marker="o", label="New infections")
        plt.xlabel("Day")
        plt.ylabel("New infections")
        plt.title("COVID SIRS: new infections per day")
        plt.grid(True)
        plt.legend()
        plt.show()


# ------------------------------ Main ----------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Simulate cascades or COVID SIRS dynamics on a directed graph."
    )

    parser.add_argument(
        "graph",
        help="Path to the input graph in GML format (e.g., graph.gml)."
    )

    parser.add_argument(
        "--action",
        choices=["cascade", "covid"],
        required=True,
        help="Type of simulation to run: 'cascade' or 'covid'."
    )

    parser.add_argument(
        "--initiator",
        type=str,
        default="",
        help="Comma-separated list of initial nodes (e.g., '1,2,5')."
    )

    # Cascade-only parameters
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Threshold q (0-1) for cascade activation."
    )

    # COVID-only parameters
    parser.add_argument(
        "--probability_of_infection",
        type=float,
        default=None,
        help="Probability p (0-1) of infection per contact."
    )
    parser.add_argument(
        "--probability_of_death",
        type=float,
        default=0.0,
        help="Probability q (0-1) of death per time step while infected."
    )
    parser.add_argument(
        "--lifespan",
        type=int,
        default=0,
        help="Number of time steps (days) for COVID simulation."
    )
    parser.add_argument(
        "--shelter",
        type=str,
        default="0",
        help="Sheltering parameter s: fraction in [0,1] OR comma-separated node list."
    )
    parser.add_argument(
        "--vaccination",
        type=float,
        default=0.0,
        help="Vaccination rate r (0-1), proportion of nodes vaccinated at t=0."
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="If set, show the graph at each round/day."
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="If set, plot time series (new activations/infections) at the end."
    )

    args = parser.parse_args()

    # Load graph
    G = load_graph(args.graph)

    # Parse initiators
    initiators = parse_initiators(args.initiator, G)

    if args.action == "cascade":
        simulate_cascade(
            G,
            initiators=initiators,
            threshold=args.threshold,
            interactive=args.interactive,
            plot=args.plot,
        )

    elif args.action == "covid":
        if args.probability_of_infection is None:
            error("For --action covid, --probability_of_infection is required.")
        if args.lifespan <= 0:
            error("For --action covid, --lifespan must be > 0.")

        simulate_covid(
            G,
            initiators=initiators,
            p_infection=args.probability_of_infection,
            p_death=args.probability_of_death,
            lifespan=args.lifespan,
            shelter_arg=args.shelter,
            vaccination=args.vaccination,
            interactive=args.interactive,
            plot=args.plot,
        )
    else:
        error(f"Unknown action: {args.action}")


if __name__ == "__main__":
    main()
