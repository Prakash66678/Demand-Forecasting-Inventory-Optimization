from pathlib import Path
import numpy as np
import pandas as pd

# Development-only synthetic data, not real retail records
rng = np.random.default_rng(42)
dates = pd.date_range("2025-01-01", periods=180, freq="D")
products = {
    "P001": 50,
    "P002": 35,
    "P003": 70,
}

rows = []

for product_id, base_demand in products.items():
    for date in dates:
        weekly_effect = 1.20 if date.dayofweek >= 5 else 1.0
        trend = 1 + (date.dayofyear / 1800)
        demand = max(
            0,
            round(base_demand * weekly_effect * trend
                  + rng.normal(0, base_demand * 0.12))
        )
        rows.append({
            "date": date,
            "product_id": product_id,
            "units_sold": demand,
        })

df = pd.DataFrame(rows)
output_path = Path("data/raw/retail_demand.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output_path, index=False)

print("Development dataset created successfully!")
print(f"Saved to: {output_path}")
print(f"Rows: {len(df)}")
print(df.head())
