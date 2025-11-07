# potential_sales_time_series.py
import json
from pathlib import Path
import plotly.graph_objects as go

AMOUNTS_DIR = Path("amounts")
PRICES_DIR = Path("prices")

def calculate_potential_sales_for_week(week_num: int) -> float:
    """
    Calculate the total potential sales (revenue) for a given week
    assuming all stock is sold at retail price.
    """
    amounts_file = AMOUNTS_DIR / f"amounts_{week_num}.json"
    prices_file = PRICES_DIR / f"prices_{week_num}.json"

    if not amounts_file.exists() or not prices_file.exists():
        return 0.0

    try:
        with open(amounts_file, "r") as f:
            stock_data = json.load(f)
        with open(prices_file, "r") as f:
            price_data = json.load(f)
    except json.JSONDecodeError:
        return 0.0

    total_potential_sales = 0.0
    for merch, stock_amount in stock_data.items():
        price = price_data.get(merch, 0)
        total_potential_sales += stock_amount * price

    return total_potential_sales


def generate_potential_sales_timeseries():
    """Generate a Plotly line chart showing potential sales value per week."""
    weeks = sorted(
        int(p.stem.split("_")[1])
        for p in AMOUNTS_DIR.glob("amounts_*.json")
        if p.stem.split("_")[1].isdigit()
    )

    potential_sales_values = [calculate_potential_sales_for_week(w) for w in weeks]

    # Build figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=weeks,
        y=potential_sales_values,
        mode="lines+markers",
        name="Potential Sales (All Stock Sold)",
        line=dict(color="green", width=3, dash="dot"),
        marker=dict(size=8)
    ))

    fig.update_layout(
        title="Potential Sales Value (If All Stock Sold)",
        xaxis_title="Week Number",
        yaxis_title="Potential Revenue (kr)",
        template="plotly_white",
        legend=dict(x=0.02, y=0.98)
    )

    return fig


if __name__ == "__main__":
    fig = generate_potential_sales_timeseries()
    fig.show()
