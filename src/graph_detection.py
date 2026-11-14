
import networkx as nx
from datetime import timedelta



def detect_cycles(G):

    simple_graph = nx.DiGraph(G)

    results = []

    # Examine short cycles only to control computation
    for cycle in nx.simple_cycles(
        simple_graph,
        length_bound=4
    ):

        if len(cycle) < 3:
            continue

        cycle_edges = []

        for i in range(len(cycle)):

            u = cycle[i]
            v = cycle[(i + 1) % len(cycle)]

            edge_data = G.get_edge_data(u, v)

            if not edge_data:
                break

            cycle_edges.append(
                list(edge_data.values())[0]
            )

        if len(cycle_edges) != len(cycle):
            continue

        times = [e["timestamp"] for e in cycle_edges]
        amounts = [e["amount"] for e in cycle_edges]

        ordered = all(
            times[i] <= times[i + 1]
            for i in range(len(times) - 1)
        )

        duration = times[-1] - times[0]

        if (
            ordered
            and duration <= timedelta(hours=24)
            and min(amounts) / max(amounts) >= 0.70
        ):

            results.append({
                "accounts": cycle,
                "pattern": "Potential circular transaction"
            })

        # Limit the number of reported findings
        if len(results) >= 100:
            break

    return results



def detect_layering_chains(G):

    results = []

    simple_graph = nx.DiGraph(G)

    for source in simple_graph.nodes():

        paths = nx.single_source_shortest_path(
            simple_graph,
            source,
            cutoff=5
        )

        for target, path in paths.items():

            if len(path) < 4:
                continue

            edges = []

            for u, v in zip(path, path[1:]):

                edge_data = G.get_edge_data(u, v)

                if not edge_data:
                    break

                edges.append(
                    list(edge_data.values())[0]
                )

            if len(edges) != len(path) - 1:
                continue

            times = [
                edge["timestamp"] for edge in edges
            ]

            amounts = [
                edge["amount"] for edge in edges
            ]

            ordered = all(
                times[i] <= times[i + 1]
                for i in range(len(times) - 1)
            )

            if not ordered:
                continue

            duration = times[-1] - times[0]

            amount_retention = (
                min(amounts) / max(amounts)
            )

            if (
                duration <= timedelta(hours=24)
                and amount_retention >= 0.70
            ):

                results.append({
                    "accounts": path,
                    "pattern": "Potential layering chain"
                })

    return results
