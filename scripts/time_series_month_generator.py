import json
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path
import re

TRANSACTIONS_DIR = Path("transactions")

def main():
    # Find all transaction_<n>.json files
    files = sorted(
        TRANSACTIONS_DIR.glob("transactions_*.json"),
        key=lambda f: int(re.search(r"transactions_(\d+)\.json", f.name).group(1))
    )

    if not files:
        print("⚠️ No transaction files found.")
        return

    print(f"Found {len(files)} weekly files: {[f.name for f in files]}")

    # day_totals[merch][global_day] = total sold that day (across all weeks)
    day_totals = defaultdict(lambda: defaultdict(int))
    global_day_counter = 0

    for week_index, file in enumerate(files, start=1):
        with open(file, "r", encoding="utf-8") as f:
            week_data = json.load(f)

        for local_day in sorted(map(int, week_data.keys())):
            global_day = global_day_counter + local_day  # e.g. week 2's "2" -> global day 9
            transactions = week_data[str(local_day)]
            for record in transactions:
                merch_types = record.get("merch_types", [])
                merch_amounts = record.get("merch_amounts", [])
                for merch, amount in zip(merch_types, merch_amounts):
                    try:
                        day_totals[merch][global_day] += int(amount)
                    except (ValueError, TypeError):
                        continue

        # Advance global day counter by 7 for the next week
        global_day_counter += 7

    if not day_totals:
        print("⚠️ No merchandise data found.")
        return

    # Collect all days across the whole month
    days = sorted({d for d_lists in day_totals.values() for d in d_lists})

    plt.figure(figsize=(10, 6))

    for merch, day_values in day_totals.items():
        y = [day_values.get(d, 0) for d in days]
        plt.plot(days, y, marker="o", label=merch)

    plt.xlabel("Day of Month")
    plt.ylabel("Quantity Sold")
    plt.title("Daglig salg per varetype (Hele måneden)")
    plt.xticks(days, [str(d) for d in days])
    plt.legend(title="Merch Type", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
