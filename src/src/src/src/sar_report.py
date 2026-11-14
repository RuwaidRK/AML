from datetime import datetime

ACTIONS = {
    "High": "Escalate immediately for investigation. Consider freezing the account and filing with the financial intelligence unit.",
    "Medium": "Open an enhanced due-diligence review and monitor the account for 30 days.",
    "Low": "No action required. Continue routine monitoring.",
}


def generate_sar(df, row, max_tx=15):
    """df = transactions, row = one row of the scores table (a pandas Series)."""
    acc = row["Account"]
    txs = df[(df["sender"] == acc) | (df["receiver"] == acc)]
    money_in = txs.loc[txs["receiver"] == acc, "amount"].sum()
    money_out = txs.loc[txs["sender"] == acc, "amount"].sum()
    partners = (set(txs["sender"]) | set(txs["receiver"])) - {acc}
    key = txs.nlargest(max_tx, "amount").sort_values("timestamp")

    rules = [r for r in row["Rules Triggered"].split(", ") if r]
    reasons = [r for r in row["Reasons"].split(" | ") if r]

    L = []
    L.append("=" * 64)
    L.append("SUSPICIOUS ACTIVITY REPORT (SAR)")
    L.append("=" * 64)
    L.append(f"Account:      {acc}")
    L.append(f"Generated:    {datetime.now():%Y-%m-%d %H:%M}")
    L.append(f"Risk score:   {row['Risk Score']} / 100  ({row['Risk Level']})")
    L.append("")
    L.append("1. SUMMARY")
    if rules:
        L.append(f"   Account triggered {len(rules)} detection rule(s): {', '.join(rules)}.")
    else:
        L.append("   No detection rules were triggered.")
    L.append("")
    L.append("2. EVIDENCE")
    for i, (rule, reason) in enumerate(zip(rules, reasons), 1):
        L.append(f"   {i}. {rule}: {reason}")
    L.append("")
    L.append("3. ACTIVITY TOTALS")
    L.append(f"   Money received:  {money_in:,.2f}")
    L.append(f"   Money sent:      {money_out:,.2f}")
    L.append(f"   Transactions:    {len(txs)}")
    L.append(f"   Counterparties:  {len(partners)}")
    L.append("")
    L.append(f"4. KEY TRANSACTIONS (top {len(key)} by amount)")
    L.append(f"   {'Date':<17}{'From':<10}{'To':<10}{'Amount':>12}")
    for t in key.itertuples():
        L.append(f"   {t.timestamp:%Y-%m-%d %H:%M}  {t.sender:<10}{t.receiver:<10}{t.amount:>12,.2f}")
    L.append("")
    L.append("5. RECOMMENDED ACTION")
    L.append(f"   {ACTIONS[row['Risk Level']]}")
    L.append("")
    L.append("Generated automatically by TraceFin. Requires analyst review.")
    return "\n".join(L)