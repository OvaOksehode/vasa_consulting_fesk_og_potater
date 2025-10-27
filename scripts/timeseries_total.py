# daily_sales_time_series.py
import json
from collections import defaultdict
from pathlib import Path
import plotly.graph_objects as go

TRANSACTIONS_DIR = Path("transactions")

def generate_daily_sales_figure():
    """Generate a Plotly figure showing daily sales per product across all available data."""
    files = sorted(TRANSACTIONS_DIR.glob("transactions_*.json"))
    if not files:
        fig = go.Figure()
        fig.update_layout(title="⚠️ No transaction files found")
        return fig

    # Aggregate daily sales: key=(week, day), value={product: amount}
    daily_sales = defaultdict(lambda: defaultdict(int))
    all_products = set()
    all_dates = []

    for file in files:
        week_number = int(file.stem.split("_")[1])
        with open(file, "r", encoding="utf-8") as f:
            week_data = json.load(f)

        for day_str, transactions in week_data.items():
            day_number = int(day_str)
            date_label = f"W{week_number}-D{day_number}"
            all_dates.append(date_label)

            for record in transactions:
                merch_types = record.get("merch_types", [])
                merch_amounts = record.get("merch_amounts", [])
                for merch, amount in zip(merch_types, merch_amounts):
                    daily_sales[merch][date_label] += int(amount)
                    all_products.add(merch)

    all_dates = sorted(all_dates, key=lambda x: (int(x.split("-")[0][1:]), int(x.split("-")[1][1:])))
    
    # Build Plotly figure
    fig = go.Figure()
    for product in sorted(all_products):
        y = [daily_sales[product].get(date, 0) for date in all_dates]
        fig.add_trace(go.Scatter(
            x=all_dates,
            y=y,
            mode="lines+markers",
            name=product
        ))

    fig.update_layout(
        title="Daily Sales per Product Across All Weeks",
        xaxis_title="Date (Week-Day)",
        yaxis_title="Units Sold",
        template="plotly_white",
        legend=dict(orientation="v", x=1.05, y=1),
        margin=dict(l=60, r=200, t=80, b=60)
    )
    return fig


# ---------------------------------------------------------------------
# Display if run directly
# ---------------------------------------------------------------------
if __name__ == "__main__":
    fig = generate_daily_sales_figure()
    fig.show()
