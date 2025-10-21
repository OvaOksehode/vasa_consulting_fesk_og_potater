# revenue_per_product.py
import json
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
import plotly.graph_objects as go

TRANSACTIONS_DIR = Path("transactions")
PRICES_DIR = Path("prices")
AMOUNTS_DIR = Path("amounts")
SUPPLIER_FILE = Path("supplier_prices.json")


def generate_revenue_per_product_figure(week_number: int):
    """
    Returns a Plotly figure for revenue/profit per product for the given week.
    Suitable for dashboard usage.
    """
    file_transactions = TRANSACTIONS_DIR / f"transactions_{week_number}.json"
    file_weekly_prices = PRICES_DIR / f"prices_{week_number}.json"
    file_stock = AMOUNTS_DIR / f"amounts_{week_number}.json"
    file_supplier_prices = SUPPLIER_FILE

    try:
        with open(file_transactions, "r") as f:
            transactions = json.load(f)
        with open(file_supplier_prices, "r") as f:
            supplier_prices = json.load(f)
        with open(file_weekly_prices, "r") as f:
            weekly_prices = json.load(f)
        with open(file_stock, "r") as f:
            stock_data = json.load(f)
    except FileNotFoundError:
        return go.Figure()

    # Sum up products sold
    sold_totals = defaultdict(int)
    for trans_list in transactions.values():
        for t in trans_list:
            for merch, amount in zip(t.get("merch_types", []), t.get("merch_amounts", [])):
                sold_totals[merch] += amount

    # Calculate profit per product
    profit_data = {}
    for merch, stock_amount in stock_data.items():
        sold_amount = sold_totals.get(merch, 0)
        buy_price = supplier_prices.get(merch, 0)
        sell_price = weekly_prices.get(merch, 0)

        stock_cost = stock_amount * buy_price
        sales_revenue = sold_amount * sell_price
        profit = sales_revenue - stock_cost
        profit_data[merch] = profit

    # Build Plotly figure
    labels = list(profit_data.keys())
    profits = list(profit_data.values())
    colors = ["green" if p >= 0 else "red" for p in profits]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=profits, marker_color=colors))
    fig.update_layout(
        title=f"Week {week_number} — Profit per Product",
        xaxis_title="Product",
        yaxis_title="Profit (kr)",
        template="plotly_white",
        xaxis_tickangle=-45
    )
    return fig


def show_revenue_per_product_matplotlib(week_number: int):
    """
    Produces the original matplotlib graph for standalone usage.
    """
    file_transactions = TRANSACTIONS_DIR / f"transactions_{week_number}.json"
    file_weekly_prices = PRICES_DIR / f"prices_{week_number}.json"
    file_stock = AMOUNTS_DIR / f"amounts_{week_number}.json"
    file_supplier_prices = SUPPLIER_FILE

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

    # Sum up products sold
    sold_totals = defaultdict(int)
    for trans_list in transactions.values():
        for t in trans_list:
            for merch, amount in zip(t.get("merch_types", []), t.get("merch_amounts", [])):
                sold_totals[merch] += amount

    # Calculate profit per product
    profit_data = {}
    for merch, stock_amount in stock_data.items():
        sold_amount = sold_totals.get(merch, 0)
        buy_price = supplier_prices.get(merch, 0)
        sell_price = weekly_prices.get(merch, 0)

        stock_cost = stock_amount * buy_price
        sales_revenue = sold_amount * sell_price
        profit = sales_revenue - stock_cost
        profit_data[merch] = profit

    labels = list(profit_data.keys())
    profits = [profit_data[l] for l in labels]
    colors = ['green' if p >= 0 else 'red' for p in profits]

    plt.figure(figsize=(12, 6))
    bars = plt.bar(labels, profits, color=colors)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Profit (kr)")
    plt.title(f"Profit per Product (green=profit, red=loss) – Week {week_number}")

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height + (0 if height < 0 else 0),
                 f"{height:.0f}", ha='center', va='bottom' if height >= 0 else 'top', fontsize=8)

    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------
# Allow standalone usage
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python revenue_per_product.py <week_number>")
    else:
        try:
            week_num = int(sys.argv[1])
            show_revenue_per_product_matplotlib(week_num)
        except ValueError:
            print("⚠️ Week number must be an integer.")
