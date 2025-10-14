import json
from collections import defaultdict
import matplotlib.pyplot as plt
from pathlib import Path
import sys

TRANSACTIONS_DIR = Path("transactions")
PRICES_DIR = Path("prices")
AMOUNTS_DIR = Path("amounts")  # stock per week
SUPPLIER_FILE = Path("supplier_prices.json")

def calculate_profit(week_number: int):
    # --- Build file paths for the week ---
    file_transactions = TRANSACTIONS_DIR / f"transactions_{week_number}.json"
    file_weekly_prices = PRICES_DIR / f"prices_{week_number}.json"
    file_stock = AMOUNTS_DIR / f"amounts_{week_number}.json"
    file_supplier_prices = SUPPLIER_FILE

    # --- Read files ---
    try:
        with open(file_transactions, "r") as f:
            transactions = json.load(f)
        with open(file_supplier_prices, "r") as f:
            supplier_prices = json.load(f)
        with open(file_weekly_prices, "r") as f:
            weekly_prices = json.load(f)
        with open(file_stock, "r") as f:
            stock_data = json.load(f)
    except FileNotFoundError as e:
        print(f"⚠️ File not found: {e}")
        return

    # --- Sum up products sold ---
    sold_totals = defaultdict(int)
    for key, trans_list in transactions.items():
        for t in trans_list:
            for merch, amount in zip(t.get("merch_types", []), t.get("merch_amounts", [])):
                sold_totals[merch] += amount

    # --- Calculate profit per product ---
    profit_data = {}
    for merch, stock_amount in stock_data.items():
        sold_amount = sold_totals.get(merch, 0)
        buy_price = supplier_prices.get(merch, 0)
        sell_price = weekly_prices.get(merch, 0)

        stock_cost = stock_amount * buy_price
        sales_revenue = sold_amount * sell_price
        profit = sales_revenue - stock_cost
        net_profit_percent = (profit / stock_cost * 100) if stock_cost != 0 else 0

        profit_data[merch] = {
            "stock_amount": stock_amount,
            "stock_cost": stock_cost,
            "sold_amount": sold_amount,
            "sales_revenue": sales_revenue,
            "profit": profit,
            "net_profit_percent": net_profit_percent
        }

    # --- Print detailed table ---
    print(f"{'Product':<15} {'Stock':>6} {'Stock Cost':>12} {'Sold':>6} {'Revenue':>12} {'Profit':>12} {'Net %':>8}")
    print("-" * 80)
    for merch, data in profit_data.items():
        print(f"{merch:<15} {data['stock_amount']:>6} {data['stock_cost']:>12.2f} "
              f"{data['sold_amount']:>6} {data['sales_revenue']:>12.2f} "
              f"{data['profit']:>12.2f} {data['net_profit_percent']:>8.2f}%")

    total_profit = sum(d["profit"] for d in profit_data.values())
    total_stock_cost = sum(d["stock_cost"] for d in profit_data.values())
    total_net_percent = (total_profit / total_stock_cost * 100) if total_stock_cost != 0 else 0

    print(f"\nTotal profit: {total_profit:.2f} kr")
    print(f"Total net profit %: {total_net_percent:.2f}%")

    # --- Plot bar chart ---
    labels = list(profit_data.keys())
    profits = [d["profit"] for d in profit_data.values()]

    plt.figure(figsize=(12, 6))
    bars = plt.bar(labels, profits, color=['green' if p >= 0 else 'red' for p in profits])
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Profit (kr)")
    plt.title(f"Profit per Product (green=profit, red=loss) – Week {week_number}")

    # Add value labels above bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height + (0 if height < 0 else 0), f"{height:.0f}",
                 ha='center', va='bottom' if height >= 0 else 'top', fontsize=8)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/profit_per_product.py <week_number>")
    else:
        try:
            week_number = int(sys.argv[1])
            calculate_profit(week_number)
        except ValueError:
            print("⚠️ Week number must be an integer.")
