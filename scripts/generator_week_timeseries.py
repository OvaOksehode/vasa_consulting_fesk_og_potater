import json
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path
import sys

TRANSACTIONS_DIR = Path("transactions")

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/daily_sales.py <week_number>")
        return

    try:
        week_number = int(sys.argv[1])
    except ValueError:
        print("⚠️ Week number must be an integer.")
        return

    file_path = TRANSACTIONS_DIR / f"transactions_{week_number}.json"
    if not file_path.exists():
        print(f"⚠️ Transaction file not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # day_totals[merch][day] = total sold that day
    day_totals = defaultdict(lambda: defaultdict(int))

    for day, transactions in data.items():
        if not isinstance(transactions, list):
            continue
        for record in transactions:
            if not isinstance(record, dict):
                continue
            merch_types = record.get("merch_types", [])
            merch_amounts = record.get("merch_amounts", [])
            for merch, amount in zip(merch_types, merch_amounts):
                try:
                    day_totals[merch][int(day)] += int(amount)
                except (ValueError, TypeError):
                    continue

    if not day_totals:
        print(f"⚠️ No merchandise data found for week {week_number}.")
        return

    # Sort days numerically
    days = sorted({int(d) for d_lists in day_totals.values() for d in d_lists})

    plt.figure(figsize=(9, 6))

    for merch, day_values in day_totals.items():
        y = [day_values.get(d, 0) for d in days]  # fill missing days with 0
        plt.plot(days, y, marker="o", label=merch)

    plt.xlabel("Day of Week")
    plt.ylabel("Quantity Sold")
    plt.title(f"Daglig salg per varetype – Uke {week_number}")
    plt.xticks(days, [f"Day {d}" for d in days])
    plt.legend(title="Merch Type", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
