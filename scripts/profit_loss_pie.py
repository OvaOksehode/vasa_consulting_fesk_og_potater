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
    - Products with profit (sales revenue > cost) → profit amounts
    - Products with loss (sales revenue < cost) → loss amounts
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

    # --- Compute profit/loss per product ---
    profit_loss = {}
    for merch, stock_amount in stock_data.items():
        sold_amount = sold_totals.get(merch, 0)
        buy_price = supplier_prices.get(merch, 0)
        sell_price = weekly_prices.get(merch, 0)

        cost = stock_amount * buy_price
        revenue = sold_amount * sell_price
        
        net_profit_loss = revenue - cost
        profit_loss[merch] = net_profit_loss

    # --- Split profit vs loss ---
    profit_data = {k: v for k, v in profit_loss.items() if v > 0}
    loss_data = {k: abs(v) for k, v in profit_loss.items() if v < 0}

    # --- Helper to make pie chart ---
    def make_pie(data, title):
        if not data:
            return go.Figure()
        return go.Figure(
            go.Pie(
                labels=list(data.keys()),
                values=list(data.values()),
                hole=0.3,
                hovertemplate="<b>%{label}</b><br>Amount: %{value:.2f}<br>Percentage: %{percent}<extra></extra>",
                textinfo="label+percent"
            )
        ).update_layout(title=title, template="plotly_white")

    fig_profit = make_pie(profit_data, f"Week {week_number} — Total Profit by Product")
    fig_loss = make_pie(loss_data, f"Week {week_number} — Total Loss by Product")

    return fig_profit, fig_loss