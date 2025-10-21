# total_profit_time_series.py
import json
from collections import defaultdict
from pathlib import Path
import plotly.graph_objects as go

TRANSACTIONS_DIR = Path("transactions")
PRICES_DIR = Path("prices")
AMOUNTS_DIR = Path("amounts")
SUPPLIER_FILE = Path("supplier_prices.json")

def generate_total_profit_figure():
    """Generate Plotly figure showing weekly and cumulative profit/loss with colored shading."""
    if not SUPPLIER_FILE.exists():
        return go.Figure()
    
    with open(SUPPLIER_FILE) as f:
        supplier_prices = json.load(f)

    weeks = sorted(int(p.stem.split("_")[1]) for p in TRANSACTIONS_DIR.glob("transactions_*.json"))
    weekly_profits = []
    cumulative_profits = []

    cumulative = 0
    for week in weeks:
        file_transactions = TRANSACTIONS_DIR / f"transactions_{week}.json"
        file_prices = PRICES_DIR / f"prices_{week}.json"
        file_stock = AMOUNTS_DIR / f"amounts_{week}.json"

        try:
            with open(file_transactions) as f:
                transactions = json.load(f)
            with open(file_prices) as f:
                weekly_prices = json.load(f)
            with open(file_stock) as f:
                stock_data = json.load(f)
        except FileNotFoundError:
            weekly_profits.append(0)
            cumulative_profits.append(cumulative)
            continue

        sold_totals = defaultdict(int)
        for trans_list in transactions.values():
            for t in trans_list:
                for merch, amount in zip(t.get("merch_types", []), t.get("merch_amounts", [])):
                    sold_totals[merch] += amount

        total_weekly = sum(
            sold_totals.get(merch, 0) * weekly_prices.get(merch, 0) - stock_data.get(merch, 0) * supplier_prices.get(merch, 0)
            for merch in stock_data
        )

        weekly_profits.append(total_weekly)
        cumulative += total_weekly
        cumulative_profits.append(cumulative)

    # Build figure
    fig = go.Figure()

    # Weekly profit line
    fig.add_trace(go.Scatter(
        x=weeks,
        y=weekly_profits,
        mode="lines+markers",
        name="Weekly Profit",
        line=dict(color="orange", width=2)
    ))

    # Cumulative line
    fig.add_trace(go.Scatter(
        x=weeks,
        y=cumulative_profits,
        mode="lines+markers",
        name="Cumulative Profit",
        line=dict(color="blue", width=3)
    ))

    # Shaded area between cumulative line and zero, color depending on sign
    y0 = [0]*len(weeks)
    y1 = cumulative_profits
    fill_colors = ['rgba(0,255,0,0.2)' if val >= 0 else 'rgba(255,0,0,0.2)' for val in y1]

    for i in range(len(weeks)):
        fig.add_trace(go.Scatter(
            x=[weeks[i], weeks[i+1] if i+1 < len(weeks) else weeks[i]],
            y=[y0[i], y0[i+1] if i+1 < len(weeks) else y0[i]],
            fill='tonexty',
            fillcolor=fill_colors[i],
            line=dict(color='rgba(0,0,0,0)'),
            showlegend=False,
            hoverinfo="skip"
        ))

    fig.update_layout(
        title="Weekly & Cumulative Net Profit/Loss",
        xaxis_title="Week Number",
        yaxis_title="Profit (kr)",
        template="plotly_white",
        legend=dict(orientation="h")
    )

    return fig

def calculate_cumulative_profits():
    """Return list of (week_number, cumulative_profit) tuples for overview."""
    if not SUPPLIER_FILE.exists():
        return []

    with open(SUPPLIER_FILE, "r") as f:
        supplier_prices = json.load(f)

    weeks = sorted(int(p.stem.split("_")[1]) for p in TRANSACTIONS_DIR.glob("transactions_*.json"))
    cumulative_profits = []
    running_total = 0

    for week in weeks:
        file_transactions = TRANSACTIONS_DIR / f"transactions_{week}.json"
        file_prices = PRICES_DIR / f"prices_{week}.json"
        file_stock = AMOUNTS_DIR / f"amounts_{week}.json"

        try:
            with open(file_transactions) as f:
                transactions = json.load(f)
            with open(file_prices) as f:
                weekly_prices = json.load(f)
            with open(file_stock) as f:
                stock_data = json.load(f)
        except FileNotFoundError:
            cumulative_profits.append((week, running_total))
            continue

        sold_totals = defaultdict(int)
        for trans_list in transactions.values():
            for t in trans_list:
                for merch, amount in zip(t.get("merch_types", []), t.get("merch_amounts", [])):
                    sold_totals[merch] += amount

        weekly_profit = 0
        for merch, stock_amount in stock_data.items():
            sold_amount = sold_totals.get(merch, 0)
            buy_price = supplier_prices.get(merch, 0)
            sell_price = weekly_prices.get(merch, 0)
            weekly_profit += sold_amount * sell_price - stock_amount * buy_price

        running_total += weekly_profit
        cumulative_profits.append((week, running_total))

    return cumulative_profits


if __name__ == "__main__":
    weekly_profits = calculate_cumulative_profits()
    if not weekly_profits:
        print("⚠️ No profit data available.")
    else:
        print(f"{'Week':<6} {'Cumulative Profit (kr)':>20}")
        print("-" * 28)
        for week, profit in weekly_profits:
            print(f"{week:<6} {profit:>20.2f}")
