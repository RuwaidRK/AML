import pandas as pd
import networkx as nx


def load_transactions(path="data/transactions.csv"):
    return pd.read_csv(path, parse_dates=["timestamp"])


def build_graph(df):
    """One directed edge per (sender, receiver) pair, with aggregated stats."""
    G = nx.DiGraph()
    for (s, r), g in df.groupby(["sender", "receiver"]):
        G.add_edge(
            s, r,
            total_amount=float(g["amount"].sum()),
            tx_count=int(len(g)),
            first_ts=g["timestamp"].min(),
            last_ts=g["timestamp"].max(),
        )
    return G


if __name__ == "__main__":
    df = load_transactions()
    G = build_graph(df)
    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")
    print("ACC9010 in/out degree:", G.in_degree("ACC9010"), G.out_degree("ACC9010"))
    print("ACC9020 -> ACC9021 edge:", G["ACC9020"]["ACC9021"])