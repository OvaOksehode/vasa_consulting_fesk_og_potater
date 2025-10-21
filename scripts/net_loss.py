import json
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt

TRANSACTIONS_DIR = Path("transactions")
PRICES_DIR = Path("prices")
AMOUNTS_DIR = Path("amounts")
SUPPLIER_FILE = Path("supplier_prices.json")


def calculate_weekly_profit(week_number, supplier_prices):
    """Return total profit for the given week."""
    file_transactions = TRANSACTIONS_DIR / f"transactions_{week_number}.json"
    file_weekly_prices = PRICES_DIR / f"prices_{week_number}.json"
    file_stock = AMOUNTS_DIR / f"amounts_{week_number}.json"

    try:
        with open(file_transactions, "r") as f:
            transactions = json.load(f)
        with open(file_weekly_prices, "r") as f:
            weekly_prices = json.load(f)
        with open(file_stock, "r") as f:
            stock_data = json.load(f)
    except FileNotFoundError:
        return None  # skip missing weeks

    sold_totals = defaultdict(int)
    for trans_list in transactions.values():
        for t in trans_list:
            for merch, amount in zip(t.get("merch_types", []), t.get("merch_amounts", [])):
                sold_totals[merch] += amount

    total_profit = 0
    for merch, stock_amount in stock_data.items():
        sold_amount = sold_totals.get(merch, 0)
        buy_price = supplier_prices.get(merch, 0)
        sell_price = weekly_prices.get(merch, 0)
        stock_cost = stock_amount * buy_price
        sales_revenue = sold_amount * sell_price
        profit = sales_revenue - stock_cost
        total_profit += profit

    return total_profit


def main():
    if not SUPPLIER_FILE.exists():
        print(f"⚠️ Supplier prices file not found: {SUPPLIER_FILE}")
        return

    with open(SUPPLIER_FILE, "r") as f:
        supplier_prices = json.load(f)

    # Find all weeks by scanning the transactions folder
    weeks = sorted(int(p.stem.split("_")[1]) for p in TRANSACTIONS_DIR.glob("transactions_*.json"))

    profits = []
    for week in weeks:
        profit = calculate_weekly_profit(week, supplier_prices)
        if profit is not None:
            profits.append((week, profit))

    if not profits:
        print("⚠️ No profit data found.")
        return

    # Unpack weeks and profit values
    weeks, profit_values = zip(*profits)

    # Plot time series
    plt.figure(figsize=(10, 6))
    plt.plot(weeks, profit_values, marker="o", color="blue")
    plt.axhline(0, color="black", linewidth=0.8, linestyle="--")
    plt.fill_between(weeks, profit_values, 0, where=[p >= 0 for p in profit_values],
                     interpolate=True, color="green", alpha=0.3, label="Profit")
    plt.fill_between(weeks, profit_values, 0, where=[p < 0 for p in profit_values],
                     interpolate=True, color="red", alpha=0.3, label="Loss")
    plt.xticks(weeks)
    plt.xlabel("Week Number")
    plt.ylabel("Net Profit (kr)")
    plt.title("Net Profit/Loss Over Weeks")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
