# profit_loss_pie.py
import json
from collections import defaultdict
from pathlib import Path
import plotly.graph_objects as go

TRANSACTIONS_DIR = Path("transactions")
PRICES_DIR = Path("prices")
AMOUNTS_DIR = Path("amounts")
SUPPLIER_FILE = Path("supplier_prices.json")


def generate_profit_loss_pie_figures(week_number: int):
    """
    Returns two Plotly pie charts:
    - Products with gross income > 1 → profit
    - Products with gross income < 1 → loss
    Gross income formula: (sold_amount * sell_price) / (stock_amount * buy_price)
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
        return go.Figure(), go.Figure()

    # --- Compute sold totals ---
    sold_totals = defaultdict(int)
    for trans_list in transactions.values():
        for t in trans_list:
            for merch, amount in zip(t.get("merch_types", []), t.get("merch_amounts", [])):
                sold_totals[merch] += amount

    # --- Compute gross income per product ---
    gross_income = {}
    for merch, stock_amount in stock_data.items():
        sold_amount = sold_totals.get(merch, 0)
        buy_price = supplier_prices.get(merch, 0)
        sell_price = weekly_prices.get(merch, 0)

        stock_value = stock_amount * buy_price
        sales_value = sold_amount * sell_price

        if stock_value == 0:
            continue  # avoid division by zero

        income_ratio = sales_value / stock_value
        gross_income[merch] = income_ratio

    # --- Split profit vs loss ---
    profit_data = {k: v for k, v in gross_income.items() if v >= 1}
    loss_data = {k: -v for k, v in gross_income.items() if v < 1}  # negative values for pie chart

    # --- Helper to make pie chart ---
    def make_pie(data, title):
        if not data:
            return go.Figure()
        return go.Figure(
            go.Pie(
                labels=list(data.keys()),
                values=[abs(v) for v in data.values()],
                hole=0.3,
                hoverinfo="label+percent+value",
                textinfo="label+percent"
            )
        ).update_layout(title=title, template="plotly_white")

    fig_profit = make_pie(profit_data, f"Week {week_number} — Gross Profit")
    fig_loss = make_pie(loss_data, f"Week {week_number} — Gross Loss")

    return fig_profit, fig_loss
