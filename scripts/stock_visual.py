import json
from collections import defaultdict
from pathlib import Path
import plotly.graph_objects as go

TRANSACTIONS_DIR = Path("transactions")
AMOUNTS_DIR = Path("amounts")

def generate_stock_visual_figure(week_number: int):
    """Return a Plotly figure of cumulative percent of stock sold per merchandise."""
    tx_file = TRANSACTIONS_DIR / f"transactions_{week_number}.json"
    stock_file = AMOUNTS_DIR / f"amounts_{week_number}.json"

    if not tx_file.exists() or not stock_file.exists():
        fig = go.Figure()
        fig.update_layout(title=f"⚠️ Missing data for week {week_number}")
        return fig

    with open(tx_file, "r", encoding="utf-8") as f:
        week_data = json.load(f)
    with open(stock_file, "r", encoding="utf-8") as f:
        stock = json.load(f)

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
        for merch, total in cumulative_totals.items():
            day_totals[merch][day] = total

    # Build the Plotly figure
    fig = go.Figure()
    for merch, day_values in day_totals.items():
        stock_amount = stock.get(merch)
        if not stock_amount:
            continue
        y = [(day_values.get(d, 0) / stock_amount) * 100 for d in days]
        fig.add_trace(go.Scatter(
            x=days,
            y=y,
            mode="lines+markers",
            name=merch
        ))

    fig.update_layout(
        title=f"Cumulative % of Stock Sold per Product — Week {week_number}",
        xaxis_title="Day of Week",
        yaxis_title="Cumulative % of Stock Sold",
        template="plotly_white",
        yaxis=dict(range=[0, 100]),
        legend=dict(orientation="v", x=1.05, y=1),
    )
    return fig

# ---------------------------------------------------------------------
# Display if run directly
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        week_input = input("Enter week number: ")
    else:
        week_input = sys.argv[1]

    try:
        week_number = int(week_input)
    except ValueError:
        print("⚠️ Week number must be an integer")
        sys.exit(1)

    fig = generate_stock_visual_figure(week_number)
    fig.show()
