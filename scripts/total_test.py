import json
from collections import defaultdict
import matplotlib.pyplot as plt

def sum_merch_totals(file_path: str):
    # Read JSON data from file
    with open(file_path, "r") as f:
        data = json.load(f)

    totals = defaultdict(int)

    # Sum up merchandise quantities
    for key, transactions in data.items():
        for transaction in transactions:
            merch_types = transaction.get("merch_types", [])
            merch_amounts = transaction.get("merch_amounts", [])
            for merch, amount in zip(merch_types, merch_amounts):
                totals[merch] += amount

    # Print totals
    print("=== Merch Totals ===")
    for merch, total in totals.items():
        print(f"{merch}: {total}")

    # Create a pie chart (a.k.a. cake chart)
    labels = list(totals.keys())
    sizes = list(totals.values())

    plt.figure(figsize=(7,7))
    plt.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    plt.title("Merchandise Distribution (by total amount)")
    plt.axis("equal")  # Equal aspect ratio ensures a perfect circle

    # Show the chart
    plt.show()

if __name__ == "__main__":
    # Replace this with your file name if it's different
    sum_merch_totals("transactions/transactions_0.json")
