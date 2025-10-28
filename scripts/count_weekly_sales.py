import json
from pathlib import Path
from collections import defaultdict

TRANSACTIONS_DIR = Path("transactions")

def analyze_product_sales(start_week: int = 0, end_week: int = 4):
    """
    Analyze sales per product across weeks and find each product's best week.
    """
    # Structure: {product: {week: amount}}
    product_weekly_sales = defaultdict(lambda: defaultdict(int))
    
    for week in range(start_week, end_week + 1):
        file_transactions = TRANSACTIONS_DIR / f"transactions_{week}.json"
        
        try:
            with open(file_transactions, "r") as f:
                transactions = json.load(f)
        except FileNotFoundError:
            print(f"Warning: transactions_{week}.json not found, skipping...")
            continue
        
        # Sum up sales per product for this week
        for trans_list in transactions.values():
            for t in trans_list:
                merch_types = t.get("merch_types", [])
                merch_amounts = t.get("merch_amounts", [])
                
                for product, amount in zip(merch_types, merch_amounts):
                    product_weekly_sales[product][week] += amount
    
    # Analyze each product
    print("Product Sales Analysis")
    print("=" * 80)
    
    for product in sorted(product_weekly_sales.keys()):
        weekly_data = product_weekly_sales[product]
        total_sold = sum(weekly_data.values())
        
        # Find best week
        best_week = max(weekly_data, key=weekly_data.get)
        best_week_amount = weekly_data[best_week]
        
        print(f"{product} - total sold: {total_sold} - most sold week: week {best_week} - most sold: {best_week_amount}")
    
    print("=" * 80)

if __name__ == "__main__":
    analyze_product_sales()
