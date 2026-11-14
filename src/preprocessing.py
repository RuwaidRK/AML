
import pandas as pd


REQUIRED_COLUMNS = [
    "transaction_id",
    "sender",
    "receiver",
    "amount",
    "timestamp"
]


def preprocess_transactions(df):

    df = df.copy()

    # Check required columns
    missing = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    # Remove duplicate transaction IDs
    df = df.drop_duplicates(
        subset=["transaction_id"]
    )

    # Clean account IDs
    df["sender"] = df["sender"].astype(str).str.strip()
    df["receiver"] = df["receiver"].astype(str).str.strip()

    # Convert amount
    df["amount"] = pd.to_numeric(
        df["amount"], errors="coerce"
    )

    # Convert timestamps
    df["timestamp"] = pd.to_datetime(
        df["timestamp"], errors="coerce"
    )

    # Remove invalid transactions
    df = df.dropna(
        subset=REQUIRED_COLUMNS
    )

    df = df[
        (df["amount"] > 0) &
        (df["sender"] != "") &
        (df["receiver"] != "") &
        (df["sender"] != df["receiver"])
    ]

    return df.reset_index(drop=True)
