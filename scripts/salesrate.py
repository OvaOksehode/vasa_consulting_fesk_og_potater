import json
import sys
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# Load week number
# ---------------------------------------------------------------------
if len(sys.argv) < 2:
    print("Usage: python scripts/salesrate.py <week_number>")
    sys.exit(1)

week_num = sys.argv[1]
transactions_path = Path(f"transactions/transactions_{week_num}.json")
stock_path = Path(f"amounts/amounts_{week_num}.json")

if not transactions_path.exists():
    print(f"❌ No transactions file found for week {week_num}")
    sys.exit(1)

# ---------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------
with open(transactions_path, "r") as f:
    transactions = json.load(f)

with open(stock_path, "r") as f:
    stock_data = json.load(f)

# ---------------------------------------------------------------------
# Aggregate daily sales per product
# ---------------------------------------------------------------------
sales_by_product = defaultdict(lambda: [0] * 7)

for day_num in range(1, 8):  # day 1–7
    day_key = str(day_num)
    for t in transactions.get(day_key, []):
        if t.get("transaction_type") != "customer_sale":
            continue
        for merch, amount in zip(t["merch_types"], t["merch_amounts"]):
            sales_by_product[merch][day_num - 1] += amount

# ---------------------------------------------------------------------
# Print detailed daily progression
# ---------------------------------------------------------------------
print(f"\n📊 SALES PROGRESSION UNTIL STOCKOUT — WEEK {week_num}\n")

summary = []

for product, stock in stock_data.items():
    daily_sales = sales_by_product[product]
    total = 0
    stockout_day = None

    print(f"{product} (stock={stock}):")

    for i, amount in enumerate(daily_sales, start=1):
        total += amount
        if total >= stock and stockout_day is None:
            stockout_day = i
            print(f"  day {i}: +{amount:<4} (total {total})  <-- STOCKOUT")
            break
        else:
            print(f"  day {i}: +{amount:<4} (total {total})")

    if stockout_day is None:
        print(f"  (never reached stockout; total sold={total})")

    print()

    # -----------------------------------------------------------------
    # Calculate daily rate logic (exclude stockout day)
    # -----------------------------------------------------------------
    if stockout_day is None:
        sold_before_stockout = total
        days_counted = 7
        avg_rate = sold_before_stockout / 7 if days_counted > 0 else 0
        stockout_flag = "❌"
    else:
        if stockout_day == 1:
            sold_before_stockout = total
            days_counted = 1
        else:
            sold_before_stockout = sum(daily_sales[:stockout_day - 1])
            days_counted = stockout_day - 1
        avg_rate = sold_before_stockout / days_counted if days_counted > 0 else sold_before_stockout
        stockout_flag = "✅"

    summary.append({
        "product": product,
        "stock": stock,
        "sold_before_stockout": sold_before_stockout,
        "days_counted": days_counted,
        "avg_rate": avg_rate,
        "stockout_flag": stockout_flag,
        "total_sold": total  # Include stockout day in total sold
    })

# ---------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------
print("📈 DAILY SALES RATE SUMMARY")
print(f"{'Product':<20} {'Stock':>6} {'DaysCounted':>12} {'Sold<Stock':>12} {'Avg/Day':>10} {'Stockout?':>10}")
print("-" * 70)

for s in summary:
    print(f"{s['product']:<20} {s['stock']:>6} {s['days_counted']:>12} {s['sold_before_stockout']:>12} "
          f"{s['avg_rate']:>10.2f} {s['stockout_flag']:>10}")

# ---------------------------------------------------------------------
# Bar graph: Total sold vs Avg rate × 7 vs Stock
# ---------------------------------------------------------------------
products = [s["product"] for s in summary]
total_sold = [s["total_sold"] for s in summary]
estimated_weekly = [s["avg_rate"] * 7 for s in summary]
stock_amount = [s["stock"] for s in summary]

x = range(len(products))
width = 0.25

fig, ax = plt.subplots(figsize=(12, 6))

bars1 = ax.bar([i - width for i in x], total_sold, width, label="Total Sold", color="#1f77b4")
bars2 = ax.bar(x, estimated_weekly, width, label="Avg Rate ×7", color="#ff7f0e")
bars3 = ax.bar([i + width for i in x], stock_amount, width, label="Stock Amount", color="#2ca02c")

ax.set_xticks(x)
ax.set_xticklabels(products, rotation=45, ha="right")
ax.set_ylabel("Units")
ax.set_title(f"Sales vs Estimated Weekly Rate vs Stock — Week {week_num}")
ax.legend()
ax.grid(axis="y", linestyle="--", alpha=0.7)

plt.tight_layout()
plt.show()
