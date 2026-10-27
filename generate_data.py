"""Generate a realistic retail sales dataset (2023-2025) with built-in patterns
worth discovering: seasonality, growth, and discount-driven losses.

Run:  python src/generate_data.py
Output: data/retail_sales.csv

Swap this file out for your own CSV (Kaggle "Superstore", etc.) - visualize.py
only needs the columns listed in the README.
"""
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N = 6000

dates = pd.to_datetime("2023-01-01") + pd.to_timedelta(rng.integers(0, 365 * 3, N), unit="D")
# Seasonality: Nov/Dec boost, mild Mar bump. Keep rows proportionally.
month_w = {1: .8, 2: .8, 3: 1.0, 4: .9, 5: .9, 6: .9, 7: .85, 8: .9, 9: 1.0, 10: 1.1, 11: 1.5, 12: 1.7}
keep = rng.random(N) < dates.month.map(month_w).values / 1.7
dates = dates[keep]
n = len(dates)

region = rng.choice(["West", "East", "Central", "South"], n, p=[.32, .28, .22, .18])
category = rng.choice(["Technology", "Furniture", "Office Supplies"], n, p=[.22, .26, .52])
segment = rng.choice(["Consumer", "Corporate", "Home Office"], n, p=[.52, .31, .17])

base_price = {"Technology": 420, "Furniture": 310, "Office Supplies": 48}
price = np.array([base_price[c] for c in category]) * rng.lognormal(0, .45, n)
qty = rng.integers(1, 8, n)

# Discounts: Furniture gets heavier discounts, especially in Central
disc_choices = np.array([0, .05, .1, .2, .3, .4])
probs = {"Technology": [.45, .2, .15, .1, .07, .03],
         "Furniture": [.15, .1, .15, .25, .22, .13],
         "Office Supplies": [.4, .2, .15, .12, .08, .05]}
discount = np.array([rng.choice(disc_choices, p=probs[c]) for c in category])
discount = np.where((region == "Central") & (category == "Furniture") & (rng.random(n) < .4),
                    np.maximum(discount, .3), discount)

# Growth ~12%/yr
years_since = (dates - pd.Timestamp("2023-01-01")).days / 365
growth = 1 + 0.12 * years_since
sales = price * qty * (1 - discount) * growth

margin_base = {"Technology": .22, "Furniture": .14, "Office Supplies": .18}
margin = np.array([margin_base[c] for c in category]) - 0.62 * discount + rng.normal(0, .05, n)
profit = sales * margin

df = pd.DataFrame({
    "order_id": [f"ORD-{100000 + i}" for i in range(n)],
    "order_date": dates,
    "region": region,
    "segment": segment,
    "category": category,
    "quantity": qty,
    "discount": discount,
    "sales": sales.round(2),
    "profit": profit.round(2),
}).sort_values("order_date").reset_index(drop=True)

out = Path(__file__).resolve().parent.parent / "data" / "retail_sales.csv"
out.parent.mkdir(exist_ok=True)
df.to_csv(out, index=False)
print(f"Wrote {len(df):,} rows -> {out}")
