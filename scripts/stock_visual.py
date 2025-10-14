import json
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path
import re
import sys

TRANSACTIONS_DIR = Path("transactions")
AMOUNTS_DIR = Path("amounts")  # stock per week

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/stock_visual.py <week_number>")
        return

    try:
        week_number = int(sys.argv[1])
    except ValueError:
        print("⚠️ Week number must be an integer.")
        return

    # Find the specific transaction file
    tx_file = TRANSACTIONS_DIR / f"transactions_{week_number}.json"
    stock_file = AMOUNTS_DIR / f"amounts_{week_number}.json"

    if not tx_file.exists():
        print(f"⚠️ Transaction file for week {week_number} not found: {tx_file}")
        return
    if not stock_file.exists():
        print(f"⚠️ Stock file for week {week_number} not found: {stock_file}")
        return

    # Load transactions
    with open(tx_file, "r", encoding="utf-8") as f:
        week_data = json.load(f)

    # Load stock
    with open(stock_file, "r", encoding="utf-8") as f:
        stock = json.load(f)

    # Aggregate daily cumulative sales per merchandise
    day_totals = defaultdict(lambda: defaultdict(int))
    cumulative_totals = defaultdict(int)

    days = sorted(map(int, week_data.keys()))
    for day in days:
        transactions = week_data[str(day)]
        for record in transactions:
            merch_types = record.get("merch_types", [])
            merch_amounts = record.get("merch_amounts", [])
            for merch, amount in zip(merch_types, merch_amounts):
                if merch in stock:
                    cumulative_totals[merch] += int(amount)
        # Save cumulative totals for this day
        for merch, total in cumulative_totals.items():
            day_totals[merch][day] = total

    if not day_totals:
        print(f"⚠️ No sales data found for week {week_number}")
        return

    # Plot cumulative percent of stock sold
    plt.figure(figsize=(10, 6))
    for merch, day_values in day_totals.items():
        stock_amount = stock.get(merch)
        if not stock_amount:
            continue
        y = [(day_values.get(d, 0) / stock_amount) * 100 for d in days]
        plt.plot(days, y, marker="o", label=merch)

    plt.xlabel("Day of Week")
    plt.ylabel("Cumulative Percent of Stock Sold (%)")
    plt.title(f"Kumulativ prosentandel av lager solgt per varetype – Uke {week_number}")
    plt.xticks(days, [f"Day {d}" for d in days])
    plt.ylim(0, 100)
    plt.legend(title="Merch Type", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
