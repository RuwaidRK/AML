import pandas as pd

# Points added when a rule fires on an account
WEIGHTS = {
    "cycle": 45,
    "structuring": 40,
    "fan_in_out": 40,
    "pass_through": 30,
}

LABELS = {
    "cycle": "Circular flow",
    "structuring": "Structuring",
    "fan_in_out": "Fan-in / Fan-out",
    "pass_through": "Rapid pass-through",
}


def risk_level(score):
    if score >= 70:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"


def score_accounts(G, flags):
    """flags = output of run_all_rules(df, G). Returns one row per account."""
    rows = []
    for acc in G.nodes():
        fired = [r for r in WEIGHTS if acc in flags.get(r, {})]
        score = min(sum(WEIGHTS[r] for r in fired), 100)
        rows.append({
            "Account": acc,
            "Risk Score": score,
            "Risk Level": risk_level(score),
            "Rules Triggered": ", ".join(LABELS[r] for r in fired),
            "Reasons": " | ".join(flags[r][acc] for r in fired),
        })
    out = pd.DataFrame(rows)
    return out.sort_values(["Risk Score", "Account"],
                           ascending=[False, True]).reset_index(drop=True)


if __name__ == "__main__":
    from graph_builder import load_transactions, build_graph
    from rule_engine import run_all_rules

    df = load_transactions()
    G = build_graph(df)
    scores = score_accounts(G, run_all_rules(df, G))
    print(scores[["Account", "Risk Score", "Risk Level", "Rules Triggered"]].head(10).to_string(index=False))