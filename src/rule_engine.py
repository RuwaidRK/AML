import pandas as pd
import networkx as nx

# Each rule returns {account: "human readable reason"}


def detect_structuring(df, low=8000, high=9999, min_count=5):
    """Many transactions just under the 10,000 reporting limit."""
    s = df[(df["amount"] >= low) & (df["amount"] <= high)]
    counts = s.groupby("sender").size()
    return {
        acc: f"{n} transfers between {low:,} and {high:,} (just under the 10,000 limit)"
        for acc, n in counts.items() if n >= min_count
    }


def detect_fan(df, window_hours=24, threshold=8):
    """Many distinct accounts sending to / receiving from one account in a short window."""
    flagged = {}
    window = pd.Timedelta(hours=window_hours)
    for col, other, label in [("receiver", "sender", "fan-in"),
                              ("sender", "receiver", "fan-out")]:
        for acc, g in df.groupby(col):
            if len(g) < threshold:
                continue
            g = g.sort_values("timestamp")
            best = 0
            for t in g["timestamp"]:
                w = g[(g["timestamp"] >= t) & (g["timestamp"] < t + window)]
                best = max(best, w[other].nunique())
            if best >= threshold:
                msg = f"{label}: {best} distinct accounts within {window_hours}h"
                flagged[acc] = flagged[acc] + "; " + msg if acc in flagged else msg
    return flagged


def detect_cycles(G, min_amount=10000, max_len=5):
    """Large money flowing in a circle: A -> B -> C -> A."""
    big = nx.DiGraph([(u, v) for u, v, d in G.edges(data=True)
                      if d["total_amount"] >= min_amount])
    flagged = {}
    for cycle in nx.simple_cycles(big, length_bound=max_len):
        path = " -> ".join(cycle + [cycle[0]])
        for acc in cycle:
            flagged[acc] = f"part of circular flow: {path}"
    return flagged


def detect_pass_through(df, min_amount=5000, max_hours=4, keep_ratio=0.9):
    """Money comes in and almost the same amount leaves within hours."""
    m = df.merge(df, left_on="receiver", right_on="sender", suffixes=("_in", "_out"))
    delta = m["timestamp_out"] - m["timestamp_in"]
    hit = m[
        (m["amount_in"] >= min_amount)
        & (delta > pd.Timedelta(0))
        & (delta <= pd.Timedelta(hours=max_hours))
        & (m["amount_out"] >= keep_ratio * m["amount_in"])
        & (m["amount_out"] <= m["amount_in"])
    ]
    return {
        r.receiver_in: (f"received {r.amount_in:,.0f}, sent {r.amount_out:,.0f} "
                        f"within {max_hours}h")
        for r in hit.itertuples()
    }


def run_all_rules(df, G):
    return {
        "structuring": detect_structuring(df),
        "fan_in_out": detect_fan(df),
        "cycle": detect_cycles(G),
        "pass_through": detect_pass_through(df),
    }


if __name__ == "__main__":
    from graph_builder import load_transactions, build_graph

    df = load_transactions()
    G = build_graph(df)
    for rule, flagged in run_all_rules(df, G).items():
        print(f"\n{rule}: {len(flagged)} flagged")
        for acc, reason in flagged.items():
            print(f"  {acc} -> {reason}")