import pandas as pd
from pathlib import Path

dataset_dir = Path(__file__).resolve().parent / "datasets"

for csv_file in sorted(dataset_dir.glob("*.csv")):
    df = pd.read_csv(csv_file)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    print(f"\\nDataset: {csv_file.name}")
    print("Transactions:", len(df))
    print("Total expenses: ₹", round(df["amount"].sum(), 2))
    print("\\nCategory totals:")
    print(df.groupby("category")["amount"].sum().sort_values(ascending=False))
