import random
import os
import pandas as pd
from datetime import datetime, timedelta

random.seed(42)

START = datetime(2026, 10, 1)
accounts = [f"ACC{i:04d}" for i in range(300)]
rows = []
ground_truth = []  # (account, pattern)


def add(sender, receiver, amount, ts):
    rows.append({
        "transaction_id": f"TX{len(rows):06d}",
        "sender": sender,
        "receiver": receiver,
        "amount": round(amount, 2),
        "timestamp": ts,
    })


def rand_time(days=30):
    return START + timedelta(seconds=random.randint(0, days * 86400))


# 1. Normal transactions
for _ in range(5000):
    s, r = random.sample(accounts, 2)
    amt = min(max(random.lognormvariate(6, 1), 10), 5000)
    add(s, r, amt, rand_time())

# 2. Structuring: many deposits just under 10,000
for _ in range(8):
    add("ACC9001", "ACC9002", random.uniform(9000, 9900), rand_time())
ground_truth.append(("ACC9001", "structuring"))

# 3. Fan-in then fan-out through one hub
hub = "ACC9010"
t = rand_time(20)
for i in range(12):
    add(random.choice(accounts), hub, random.uniform(2000, 4000),
        t + timedelta(hours=i))
for i in range(12):
    add(hub, random.choice(accounts), random.uniform(2000, 4000),
        t + timedelta(hours=14 + i))
ground_truth.append((hub, "fan_in_out"))

# 4. Circular flow: A -> B -> C -> A
t = rand_time(20)
ring = ["ACC9020", "ACC9021", "ACC9022"]
amt = 50000
for i in range(3):
    add(ring[i], ring[(i + 1) % 3], amt, t + timedelta(hours=i * 3))
    amt *= 0.98  # small fee skimmed each hop
for a in ring:
    ground_truth.append((a, "cycle"))

# 5. Rapid pass-through: in and out within 2 hours
t = rand_time(20)
add("ACC9031", "ACC9030", 20000, t)
add("ACC9030", "ACC9032", 19800, t + timedelta(hours=2))
ground_truth.append(("ACC9030", "pass_through"))

# Save
os.makedirs("data", exist_ok=True)
df = pd.DataFrame(rows).sort_values("timestamp")
df.to_csv("data/transactions.csv", index=False)
pd.DataFrame(ground_truth, columns=["account", "pattern"]).to_csv(
    "data/ground_truth.csv", index=False)

print(f"Saved {len(df)} transactions to data/transactions.csv")
print(f"Saved {len(ground_truth)} labels to data/ground_truth.csv")