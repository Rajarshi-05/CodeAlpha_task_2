"""Data visualization project: retail sales story.

Run:  python src/visualize.py
Reads  data/retail_sales.csv
Writes visuals/*.png  and  insights.txt

Design rules followed
- One message per chart (title states the finding, not the topic)
- Categorical colors in fixed order: blue, orange, aqua (colorblind-safe trio)
- Sequential = one hue light->dark; diverging = blue/red around a gray zero
- No dual axes, light gridlines, direct labels instead of crowded legends
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.ticker as mtick
import seaborn as sns

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "visuals"
OUT.mkdir(exist_ok=True)

# ---------- design tokens ----------
BLUE, ORANGE, AQUA, RED = "#2a78d6", "#eb6834", "#1baf7a", "#e34948"
CAT_COLORS = {"Technology": BLUE, "Furniture": ORANGE, "Office Supplies": AQUA}
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, SURFACE, MID = "#e1e0d9", "#fcfcfb", "#f0efec"
SEQ = LinearSegmentedColormap.from_list("seq", ["#cde2fb", "#6da7ec", "#2a78d6", "#184f95", "#0d366b"])
# Diverging: red = losing money, gray = break-even, blue = profitable
DIV = LinearSegmentedColormap.from_list("div", ["#b52a2a", "#ee8a89", MID, "#6da7ec", "#184f95"])

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": GRID,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": .8,
    "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.titlepad": 14, "axes.labelsize": 10, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "legend.frameon": False, "figure.dpi": 110,
})

def money(x, _=None):
    if abs(x) >= 1e6: return f"${x/1e6:.1f}M"
    if abs(x) >= 1e3: return f"${x/1e3:.0f}K"
    return f"${x:.0f}"

def finish(fig, name, subtitle=None):
    if subtitle:
        fig.text(0.0, 0.0, "", alpha=0)
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)

def subtitle(ax, text):
    ax.text(0, 1.02, text, transform=ax.transAxes, fontsize=9.5, color=INK2, va="bottom")

# ---------- load ----------
df = pd.read_csv(ROOT / "data" / "retail_sales.csv", parse_dates=["order_date"])
df["year"] = df.order_date.dt.year
df["month"] = df.order_date.dt.month
df["ym"] = df.order_date.dt.to_period("M").dt.to_timestamp()
df["margin"] = df.profit / df.sales

total_sales, total_profit = df.sales.sum(), df.profit.sum()
overall_margin = total_profit / total_sales

# ======================================================================
# 1. Revenue trend (line + 3-month rolling average)
# ======================================================================
monthly = df.groupby("ym").sales.sum()
roll = monthly.rolling(3, center=True).mean()
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.plot(monthly.index, monthly.values, color=BLUE, alpha=.35, lw=1.5, label="Monthly revenue")
ax.plot(roll.index, roll.values, color=BLUE, lw=2.5, label="3-month average")
peaks = monthly[monthly.index.month == 12]
ax.scatter(peaks.index, peaks.values, s=55, color=ORANGE, zorder=5, edgecolor=SURFACE, linewidth=1.5)
for d, v in peaks.items():
    ax.annotate(f"Dec {d.year}\n{money(v)}", (d, v), xytext=(0, 12), textcoords="offset points",
                ha="center", fontsize=8.5, color=INK2)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(money))
ax.set_ylim(0, monthly.max() * 1.25)
ax.set_title("Revenue grows each year, with sharp year-end peaks")
ax.legend(loc="upper left", ncol=2)
ax.grid(axis="x", visible=False)
finish(fig, "01_revenue_trend.png")

# ======================================================================
# 2. Category performance: revenue (bar) + margin (labels)
# ======================================================================
cat = df.groupby("category").agg(sales=("sales", "sum"), profit=("profit", "sum"))
cat["margin"] = cat.profit / cat.sales
cat = cat.sort_values("sales")
fig, ax = plt.subplots(figsize=(9, 3.8))
bars = ax.barh(cat.index, cat.sales, color=[CAT_COLORS[c] for c in cat.index], height=.55)
for b, (c, r) in zip(bars, cat.iterrows()):
    ax.text(b.get_width() + cat.sales.max() * .01, b.get_y() + b.get_height() / 2,
            f"{money(r.sales)}  |  {r.margin:.1%} margin", va="center", fontsize=10, color=INK)
ax.set_xlim(0, cat.sales.max() * 1.4)
ax.xaxis.set_major_formatter(mtick.FuncFormatter(money))
ax.grid(axis="y", visible=False)
ax.set_title("Technology leads on revenue and margin; Furniture keeps only ~3%")
finish(fig, "02_category_performance.png")

# ======================================================================
# 3. Profit margin heatmap: region x category (diverging around 0)
# ======================================================================
rc = df.groupby(["region", "category"]).agg(s=("sales", "sum"), p=("profit", "sum"))
heat = (rc.p / rc.s).unstack()
heat = heat.loc[heat.mean(axis=1).sort_values(ascending=False).index, ["Technology", "Office Supplies", "Furniture"]]
lim = max(abs(heat.values.min()), abs(heat.values.max()))
fig, ax = plt.subplots(figsize=(8, 4.3))
sns.heatmap(heat, annot=heat.map(lambda v: f"{v:.1%}"), fmt="", cmap=DIV, center=0,
            vmin=-lim, vmax=lim, linewidths=3, linecolor=SURFACE, cbar_kws={"label": "Profit margin", "shrink": .8},
            annot_kws={"fontsize": 11, "fontweight": "bold"}, ax=ax)
ax.set_xlabel(""); ax.set_ylabel("")
ax.tick_params(length=0, labelsize=10)
ax.grid(False)
ax.set_title("Furniture is the weak spot, and Central Furniture barely breaks even")
finish(fig, "03_margin_heatmap.png")

# ======================================================================
# 4. Discount vs margin (the root cause)
# ======================================================================
dm = df.groupby(["category", "discount"]).apply(
    lambda g: pd.Series({"margin": g.profit.sum() / g.sales.sum(), "orders": len(g)}), include_groups=False).reset_index()
fig, ax = plt.subplots(figsize=(9, 5))
ax.axhline(0, color=INK2, lw=1)
for c, g in dm.groupby("category"):
    ax.plot(g.discount, g.margin, color=CAT_COLORS[c], lw=2.2, marker="o", ms=7,
            markeredgecolor=SURFACE, markeredgewidth=1.5, label=c)
ax.xaxis.set_major_formatter(mtick.PercentFormatter(1, decimals=0))
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1, decimals=0))
ax.set_xlabel("Discount given"); ax.set_ylabel("Profit margin")
ax.set_ylim(-.15, .25)
ax.legend(loc="lower left")
ax.annotate("Furniture turns loss-making\nbeyond ~25% discount", xy=(.3, dm[(dm.discount == .3) & (dm.category == "Furniture")].margin.iloc[0]),
            xytext=(.15, -.105), fontsize=9.5, color=INK2,
            arrowprops=dict(arrowstyle="-", color=MUTED))
ax.grid(axis="x", visible=False)
ax.set_title("Every extra point of discount eats margin, in every category")
finish(fig, "04_discount_vs_margin.png")

# ======================================================================
# 5. Order value distribution
# ======================================================================
fig, ax = plt.subplots(figsize=(9, 4.3))
cap = df.sales.quantile(.97)
ax.hist(df.sales.clip(upper=cap), bins=40, color=BLUE, edgecolor=SURFACE, linewidth=1)
med = df.sales.median()
ax.axvline(med, color=ORANGE, lw=2)
ax.text(med * 1.05, ax.get_ylim()[1] * .92, f"Median order: {money(med)}", color=INK, fontsize=10)
ax.xaxis.set_major_formatter(mtick.FuncFormatter(money))
ax.set_xlabel("Order value (top 3% grouped at right edge)"); ax.set_ylabel("Orders")
ax.grid(axis="x", visible=False)
ax.set_title("Most orders are small; a long tail of big orders drives revenue")
finish(fig, "05_order_distribution.png")

# ======================================================================
# 6. Seasonality heatmap: month x year (sequential)
# ======================================================================
piv = df.pivot_table(index="year", columns="month", values="sales", aggfunc="sum")
fig, ax = plt.subplots(figsize=(10, 3.4))
sns.heatmap(piv / 1e3, cmap=SEQ, annot=True, fmt=".0f", linewidths=3, linecolor=SURFACE,
            cbar_kws={"label": "Revenue ($K)"}, annot_kws={"fontsize": 9}, ax=ax)
ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], rotation=0)
ax.set_xlabel(""); ax.set_ylabel(""); ax.grid(False); ax.tick_params(length=0)
ax.set_title("Q4 is consistently the strongest quarter")
finish(fig, "06_seasonality_heatmap.png")

# ======================================================================
# 7. Small multiples: yearly revenue by region
# ======================================================================
reg_year = df.groupby(["region", "year"]).sales.sum().unstack()
order = reg_year.sum(axis=1).sort_values(ascending=False).index
fig, axes = plt.subplots(1, 4, figsize=(11, 3.6), sharey=True)
for ax, r in zip(axes, order):
    vals = reg_year.loc[r]
    ax.bar(vals.index.astype(str), vals.values, color=BLUE, width=.6)
    for x, v in zip(vals.index.astype(str), vals.values):
        ax.text(x, v + reg_year.values.max() * .02, money(v), ha="center", fontsize=8, color=INK2)
    ax.set_title(r, fontsize=11, pad=8)
    ax.grid(axis="x", visible=False)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(money))
    ax.set_ylim(0, reg_year.values.max() * 1.15)
fig.suptitle(f"Yearly revenue by region: {order[0]} leads", x=0.01, ha="left", fontsize=14, fontweight="bold")
finish(fig, "07_region_small_multiples.png")

# ======================================================================
# 8. Dashboard
# ======================================================================
fig = plt.figure(figsize=(14, 9.5))
gs = fig.add_gridspec(3, 12, height_ratios=[.4, 1.5, 1.5], hspace=.6, wspace=1.2)
fig.text(0.06, 0.93, "Retail Sales Dashboard 2023-2025", fontsize=20, fontweight="bold", ha="left")

yoy = df[df.year == 2025].sales.sum() / df[df.year == 2024].sales.sum() - 1
kpis = [("Total revenue", money(total_sales)), ("Total profit", money(total_profit)),
        ("Profit margin", f"{overall_margin:.1%}"), ("Orders", f"{len(df):,}"),
        ("Avg order value", money(df.sales.mean())), ("Revenue growth 2025", f"{yoy:+.1%}")]
for i, (lab, val) in enumerate(kpis):
    ax = fig.add_subplot(gs[0, i * 2:(i + 1) * 2])
    ax.axis("off")
    ax.text(0, .62, val, fontsize=22, fontweight="bold", color=INK, transform=ax.transAxes)
    ax.text(0, .15, lab, fontsize=10, color=INK2, transform=ax.transAxes)

ax = fig.add_subplot(gs[1, :7])
ax.plot(monthly.index, monthly.values, color=BLUE, alpha=.35, lw=1.2)
ax.plot(roll.index, roll.values, color=BLUE, lw=2.4)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(money)); ax.grid(axis="x", visible=False)
ax.set_title("Monthly revenue (3-month average in bold)", fontsize=11)

ax = fig.add_subplot(gs[1, 7:])
bars = ax.barh(cat.index, cat.sales, color=[CAT_COLORS[c] for c in cat.index], height=.55)
for b, (c, r) in zip(bars, cat.iterrows()):
    ax.text(b.get_width() * 1.02, b.get_y() + b.get_height() / 2, f"{r.margin:.0%} margin", va="center", fontsize=9)
ax.set_xlim(0, cat.sales.max() * 1.45)
ax.xaxis.set_major_formatter(mtick.FuncFormatter(money)); ax.grid(axis="y", visible=False)
ax.set_title("Revenue and margin by category", fontsize=11)

ax = fig.add_subplot(gs[2, :6])
sns.heatmap(heat, annot=heat.map(lambda v: f"{v:.0%}"), fmt="", cmap=DIV, center=0,
            vmin=-lim, vmax=lim, linewidths=3, linecolor=SURFACE, cbar=False,
            annot_kws={"fontsize": 10, "fontweight": "bold"}, ax=ax)
ax.set_xlabel(""); ax.set_ylabel(""); ax.grid(False); ax.tick_params(length=0)
ax.set_title("Profit margin: region x category", fontsize=11)

ax = fig.add_subplot(gs[2, 6:])
ax.axhline(0, color=INK2, lw=1)
for c, g in dm.groupby("category"):
    ax.plot(g.discount, g.margin, color=CAT_COLORS[c], lw=2, marker="o", ms=5,
            markeredgecolor=SURFACE, label=c)
ax.xaxis.set_major_formatter(mtick.PercentFormatter(1, decimals=0))
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1, decimals=0))
ax.set_xlabel("Discount"); ax.legend(fontsize=8, loc="lower left"); ax.grid(axis="x", visible=False)
ax.set_title("Margin falls as discount rises", fontsize=11)
fig.savefig(OUT / "08_dashboard.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("saved 08_dashboard.png")

# ======================================================================
# Insights text (numbers used in the README story)
# ======================================================================
cf = rc.loc[("Central", "Furniture")]
hi = df[df.discount >= .3]; lo = df[df.discount <= .1]
lines = [
    f"Total revenue: {money(total_sales)}  profit: {money(total_profit)}  margin: {overall_margin:.1%}",
    f"Revenue by year: " + ", ".join(f"{y}: {money(v)}" for y, v in df.groupby('year').sales.sum().items()),
    f"2025 growth vs 2024: {yoy:+.1%}",
    f"Q4 share of revenue: {df[df.month >= 10].sales.sum() / total_sales:.1%}",
    f"Central Furniture margin: {cf.p / cf.s:.1%} (profit {money(cf.p)})",
    f"Margin at discount >=30%: {hi.profit.sum() / hi.sales.sum():.1%}; at <=10%: {lo.profit.sum() / lo.sales.sum():.1%}",
    f"Share of orders with >=30% discount: {len(hi) / len(df):.1%}",
    f"Loss-making orders: {(df.profit < 0).mean():.1%} of orders",
    f"Median order: {money(df.sales.median())}  mean: {money(df.sales.mean())}",
]
(ROOT / "insights.txt").write_text("\n".join(lines))
print("\n".join(lines))
