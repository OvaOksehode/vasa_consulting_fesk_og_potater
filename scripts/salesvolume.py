# scripts/salesrate_dash.py
import json
from pathlib import Path
import plotly.graph_objects as go

TRANSACTIONS_DIR = Path("transactions")

def calculate_weekly_total_sales(week_num: int) -> int:
    """Return the total number of units sold across all products for a given week."""
    transactions_path = TRANSACTIONS_DIR / f"transactions_{week_num}.json"
    if not transactions_path.exists():
        return 0

    with open(transactions_path, "r") as f:
        transactions = json.load(f)

    total_sales = 0
    for day_num in range(1, 8):
        for t in transactions.get(str(day_num), []):
            if t.get("transaction_type") != "customer_sale":
                continue
            total_sales += sum(t["merch_amounts"])

    return total_sales


def generate_total_sales_volume_timeseries(start_week=0, end_week=6):
    """Generate a time-series showing weekly and cumulative total units sold."""
    week_nums = list(range(start_week, end_week + 1))
    weekly_totals = [calculate_weekly_total_sales(w) for w in week_nums]

    # Compute cumulative totals
    cumulative_totals = []
    running_sum = 0
    for val in weekly_totals:
        running_sum += val
        cumulative_totals.append(running_sum)

    # Create the figure
    fig = go.Figure()

    # Weekly totals (bars or line)
    fig.add_trace(go.Scatter(
        x=week_nums,
        y=weekly_totals,
        mode="lines+markers",
        name="Weekly Sales Volume",
        line=dict(width=3, color="#1f77b4"),
        marker=dict(size=8)
    ))

    # Cumulative totals (line)
    fig.add_trace(go.Scatter(
        x=week_nums,
        y=cumulative_totals,
        mode="lines+markers",
        name="Cumulative Sales Volume",
        line=dict(width=3, dash="dash", color="#ff7f0e"),
        marker=dict(size=8)
    ))

    # Layout
    fig.update_layout(
        title=f"Total & Cumulative Sales Volume (All Products) — Weeks {start_week} to {end_week}",
        xaxis_title="Week Number",
        yaxis_title="Units Sold",
        template="plotly_white",
        legend=dict(x=0.02, y=0.98)
    )

    return fig


if __name__ == "__main__":
    fig = generate_total_sales_volume_timeseries(0, 6)
    fig.show()
