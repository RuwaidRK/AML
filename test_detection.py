
import pandas as pd

from src.preprocessing import preprocess_transactions
from src.rule_engine import detect_suspicious_patterns
from src.graph_builder import build_transaction_graph
from src.graph_detection import (
    detect_cycles,
    detect_layering_chains
)

print("\nTRACEFIN AI - DETECTION ENGINE")
print("=" * 40)

# Load dataset
df = pd.read_csv("data/transactions.csv")

print("\n1. Loading transaction dataset...")
print("Total records:", len(df))

# Preprocessing
df = preprocess_transactions(df)

print("\n2. Preprocessing completed")
print("Valid records:", len(df))

# Rule-based detection
suspicious = detect_suspicious_patterns(df)

print("\n3. Suspicious transactions detected")
print("Flagged records:", len(suspicious))

if not suspicious.empty:
    print(suspicious.head(10).to_string(index=False))

# Build graph
G = build_transaction_graph(df)

print("\n4. Transaction graph created")
print("Accounts:", G.number_of_nodes())
print("Transactions:", G.number_of_edges())

# Cycle detection
cycles = detect_cycles(G)

print("\n5. Circular patterns detected")
print("Number of cycles:", len(cycles))

for cycle in cycles:
    print(cycle)

# Layering detection
layering = detect_layering_chains(G)

print("\n6. Layering patterns detected")
print("Number of chains:", len(layering))

for chain in layering:
    print(chain)

print("\n" + "=" * 40)
print("TRACEFIN AI TEST COMPLETED")
