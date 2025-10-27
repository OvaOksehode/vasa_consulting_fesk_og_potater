# scripts/salesrate_dash.py
import json
from collections import defaultdict
from pathlib import Path
import plotly.graph_objects as go

TRANSACTIONS_DIR = Path("transactions")
AMOUNTS_DIR = Path("amounts")

def generate_salesrate_figure(week_num: int):
    transactions_path = TRANSACTIONS_DIR / f"transactions_{week_num}.json"
    stock_path = AMOUNTS_DIR / f"amounts_{week_num}.json"

    if not transactions_path.exists() or not stock_path.exists():
        return go.Figure()  # Return empty figure if missing

    with open(transactions_path, "r") as f:
        transactions = json.load(f)
    with open(stock_path, "r") as f:
        stock_data = json.load(f)

    # Aggregate daily sales
    sales_by_product = defaultdict(lambda: [0]*7)
    for day_num in range(1, 8):
        for t in transactions.get(str(day_num), []):
            if t.get("transaction_type") != "customer_sale":
                continue
            for merch, amount in zip(t["merch_types"], t["merch_amounts"]):
                sales_by_product[merch][day_num - 1] += amount

    # Compute totals, estimated weekly rate
    products = []
    total_sold = []
    estimated_weekly = []
    stock_amount = []

    for product, stock in stock_data.items():
        daily_sales = sales_by_product[product]
        total = sum(daily_sales)
        running = 0
        stockout_day = None

        for i, amt in enumerate(daily_sales, start=1):
            running += amt
            if running >= stock:
                stockout_day = i
                break

        # Determine which days to include in average
        if stockout_day is None:
            sold_before_stockout = total
            days_counted = 7
        else:
            # Include stockout day if its sales > previous day
            if stockout_day == 1:
                sold_before_stockout = total
                days_counted = 1
            else:
                prev_day_sales = daily_sales[stockout_day - 2]
                stockout_sales = daily_sales[stockout_day - 1]
                if stockout_sales > prev_day_sales:
                    sold_before_stockout = sum(daily_sales[:stockout_day])
                    days_counted = stockout_day
                else:
                    sold_before_stockout = sum(daily_sales[:stockout_day-1])
                    days_counted = stockout_day - 1

        avg_rate = sold_before_stockout / days_counted if days_counted > 0 else sold_before_stockout

        products.append(product)
        total_sold.append(total)
        estimated_weekly.append(avg_rate * 7)
        stock_amount.append(stock)

    # Create Plotly bar chart
    x = list(range(len(products)))

    fig = go.Figure()
    fig.add_trace(go.Bar(x=x, y=total_sold, width=0.25, name="Total Sold", marker_color="#1f77b4"))
    fig.add_trace(go.Bar(x=x, y=estimated_weekly, width=0.25, name="Avg Rate ×7", marker_color="#ff7f0e"))
    fig.add_trace(go.Bar(x=x, y=stock_amount, width=0.25, name="Stock Amount", marker_color="#2ca02c"))

    fig.update_layout(
        title=f"Sales vs Estimated Weekly Rate vs Stock — Week {week_num}",
        xaxis=dict(tickmode="array", tickvals=x, ticktext=products),
        yaxis_title="Units",
        barmode="group",
        template="plotly_white"
    )

    return fig

# Optional: allow running standalone for quick check
if __name__ == "__main__":
    import sys
    import plotly.io as pio

    if len(sys.argv) < 2:
        print("Usage: python salesrate_dash.py <week_number>")
        sys.exit(1)

    week = int(sys.argv[1])
    fig = generate_salesrate_figure(week)
    fig.show()
