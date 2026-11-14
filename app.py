import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from graph_builder import load_transactions, build_graph
from rule_engine import run_all_rules
from risk_scoring import score_accounts
from sar_report import generate_sar

st.set_page_config(page_title="TraceFin", page_icon="🕵️", layout="wide")

BG = "#0b0f19"
COLORS = {"High": "#ff3b5c", "Medium": "#ffb020", "Low": "#3ea6ff"}

st.markdown(f"""
<style>
.stApp {{
    background: radial-gradient(circle at 15% 0%, #16264a 0%, {BG} 55%);
}}
section[data-testid="stSidebar"] {{
    background: #0f1524;
    border-right: 1px solid #1f2a44;
}}
.hero h1 {{
    font-size: 2.6rem; font-weight: 800; margin: 0;
    background: linear-gradient(90deg, #00e5ff, #7c4dff, #ff3b5c);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.hero p {{ color: #8b98b8; margin: 0 0 1rem 0; }}
.card {{
    background: linear-gradient(145deg, #131c33, #0e1527);
    border: 1px solid #22304f; border-radius: 14px;
    padding: 16px 20px;
}}
.card .label {{ color: #8b98b8; font-size: 0.8rem; letter-spacing: 1px; text-transform: uppercase; }}
.card .value {{ font-size: 2rem; font-weight: 700; }}
.badge {{
    display: inline-block; padding: 3px 12px; border-radius: 999px;
    font-weight: 700; font-size: 0.85rem;
}}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load():
    df = load_transactions("data/transactions.csv")
    G = build_graph(df)
    flags = run_all_rules(df, G)
    scores = score_accounts(G, flags)
    return df, G, scores


def card(col, label, value, color):
    col.markdown(
        f'<div class="card" style="border-top:3px solid {color}">'
        f'<div class="label">{label}</div>'
        f'<div class="value" style="color:{color}">{value}</div></div>',
        unsafe_allow_html=True,
    )


df, G, scores = load()
flagged = scores[scores["Risk Score"] > 0]

# ---------- Sidebar ----------
st.sidebar.markdown("### 🎛️ Filters")
min_score = st.sidebar.slider("Minimum risk score", 0, 100, 0, 5)
view = flagged[flagged["Risk Score"] >= min_score]
st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Risk levels**  \n"
    "🔴 High: 70+  \n🟠 Medium: 30-69  \n🔵 Low: under 30"
)

# ---------- Header ----------
st.markdown('<div class="hero"><h1>🕵️ TraceFin</h1>'
            '<p>Graph-based money laundering detection</p></div>',
            unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
card(m1, "Transactions", f"{len(df):,}", "#00e5ff")
card(m2, "Accounts", f"{G.number_of_nodes():,}", "#7c4dff")
card(m3, "Flagged", len(flagged), COLORS["Medium"])
card(m4, "High risk", int((scores["Risk Level"] == "High").sum()), COLORS["High"])
st.write("")

if view.empty:
    st.warning("No accounts match this filter. Lower the minimum risk score.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📊 Leaderboard", "🕸️ Network", "📄 SAR Report"])

# ---------- Tab 1: Leaderboard ----------
with tab1:
    left, right = st.columns([2, 1])
    with left:
        st.subheader("High-Risk Account Leaderboard")
        table = view[["Account", "Risk Score", "Risk Level", "Rules Triggered"]]

        def color_level(v):
            c = COLORS.get(v, "#ffffff")
            return f"color:{c}; font-weight:700"

        st.dataframe(
            table.style.map(color_level, subset=["Risk Level"]),
            width="stretch", hide_index=True,
            column_config={"Risk Score": st.column_config.ProgressColumn(
                "Risk Score", min_value=0, max_value=100, format="%d")},
        )
    with right:
        st.subheader("Rules triggered")
        counts = (flagged["Rules Triggered"].str.split(", ").explode()
                  .value_counts())
        st.bar_chart(counts, color="#00e5ff")

# ---------- Tab 2: Network ----------
with tab2:
    st.subheader("Transaction Network")
    selected = st.selectbox("Account to investigate", view["Account"], key="net_acc")
    row = scores[scores["Account"] == selected].iloc[0]

    sub = nx.ego_graph(G, selected, radius=1, undirected=True)
    level = dict(zip(scores["Account"], scores["Risk Level"]))
    node_colors = [COLORS[level[n]] for n in sub.nodes()]
    sizes = [1300 if n == selected else 520 for n in sub.nodes()]
    widths = [0.8 + min(d["total_amount"] / 20000, 3.5)
              for _, _, d in sub.edges(data=True)]

    fig, ax = plt.subplots(figsize=(8, 6.5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    pos = nx.spring_layout(sub, seed=42, k=0.9)

    nx.draw_networkx_edges(sub, pos, ax=ax, edge_color="#4b5a7a", width=widths,
                           arrows=True, arrowsize=16, node_size=sizes, alpha=0.85,
                           connectionstyle="arc3,rad=0.12")
    # glow layer, then solid nodes
    nx.draw_networkx_nodes(sub, pos, ax=ax, node_color=node_colors,
                           node_size=[s * 3 for s in sizes], alpha=0.14)
    nx.draw_networkx_nodes(sub, pos, ax=ax, node_color=node_colors, node_size=sizes,
                           edgecolors=["white" if n == selected else c
                                       for n, c in zip(sub.nodes(), node_colors)],
                           linewidths=[2.5 if n == selected else 1 for n in sub.nodes()])
    nx.draw_networkx_labels(sub, pos, ax=ax, font_size=7, font_color="white")
    ax.axis("off")
    ax.legend(
        handles=[Line2D([0], [0], marker="o", color="none", markerfacecolor=c,
                        markersize=10, label=f"{k} risk") for k, c in COLORS.items()],
        loc="upper right", facecolor="#0f1524", edgecolor="#22304f", labelcolor="white")

    g1, g2 = st.columns([2, 1])
    with g1:
        st.pyplot(fig)
    with g2:
        c = COLORS[row["Risk Level"]]
        st.markdown(
            f'<div class="card"><div class="label">Selected account</div>'
            f'<div class="value">{selected}</div><br>'
            f'<span class="badge" style="background:{c}33;color:{c}">'
            f'{row["Risk Level"]} · {row["Risk Score"]}/100</span></div>',
            unsafe_allow_html=True)
        st.write("")
        st.markdown("**Why it was flagged**")
        for r in row["Reasons"].split(" | "):
            st.markdown(f"- {r}")
        st.caption(f"{sub.number_of_nodes() - 1} directly connected accounts")

# ---------- Tab 3: SAR ----------
with tab3:
    st.subheader("Suspicious Activity Report")
    sar_acc = st.selectbox("Select account for SAR", view["Account"], key="sar_acc")
    sar_row = scores[scores["Account"] == sar_acc].iloc[0]
    report = generate_sar(df, sar_row)

    with st.expander("Preview report", expanded=True):
        st.code(report, language=None)

    st.download_button(
        label="⬇️ Download SAR report (.txt)",
        data=report,
        file_name=f"SAR_{sar_acc}.txt",
        mime="text/plain",
    )