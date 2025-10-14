import json
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path
import re

TRANSACTIONS_DIR = Path("transactions")
AMOUNTS_DIR = Path("amounts")  # stock per week

def main():
    # Find all weekly transaction files
    transaction_files = sorted(
        TRANSACTIONS_DIR.glob("transactions_*.json"),
        key=lambda f: int(re.search(r"transactions_(\d+)\.json", f.name).group(1))
    )
    if not transaction_files:
        print("⚠️ No transaction files found.")
        return

    # Find all weekly stock files
    stock_files = sorted(
        AMOUNTS_DIR.glob("amounts_*.json"),
        key=lambda f: int(re.search(r"amounts_(\d+)\.json", f.name).group(1))
    )
    if len(transaction_files) != len(stock_files):
        print("⚠️ Warning: number of transaction files != stock files")

    # Process each week separately
    for week_index, tx_file in enumerate(transaction_files, start=1):
        # Load transactions
        with open(tx_file, "r", encoding="utf-8") as f:
            week_data = json.load(f)

        # Load stock for this week
        try:
            stock_file = stock_files[week_index - 1]
            with open(stock_file, "r", encoding="utf-8") as f:
                stock = json.load(f)
        except IndexError:
            print(f"⚠️ No stock file for week {week_index}, skipping")
            continue

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
            print(f"⚠️ No sales data found for week {week_index}")
            continue

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
        plt.title(f"Kumulativ prosentandel av lager solgt per varetype – Uke {week_index}")
        plt.xticks(days, [f"Day {d}" for d in days])
        plt.ylim(0, 100)
        plt.legend(title="Merch Type", bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    main()
