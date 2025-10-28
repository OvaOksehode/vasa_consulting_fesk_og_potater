# scripts/salesrate_dash.py
import json
from collections import defaultdict
from pathlib import Path
import plotly.graph_objects as go

TRANSACTIONS_DIR = Path("transactions")
AMOUNTS_DIR = Path("amounts")

def calculate_weekly_metrics(week_num: int):
    """Calculate metrics for a single week."""
    transactions_path = TRANSACTIONS_DIR / f"transactions_{week_num}.json"
    stock_path = AMOUNTS_DIR / f"amounts_{week_num}.json"

    if not transactions_path.exists() or not stock_path.exists():
        return {}

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

    # Compute metrics per product
    product_metrics = {}
    
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

        product_metrics[product] = {
            'total_sold': total,
            'avg_daily_rate': avg_rate,
            'estimated_weekly': avg_rate * 7,
            'stock': stock
        }
    
    return product_metrics


def generate_salesrate_figure(week_num: int = None):
    """
    Generate sales rate figure. If week_num is None, aggregate across all weeks (excluding week 5).
    """
    if week_num is not None:
        # Original single-week behavior
        transactions_path = TRANSACTIONS_DIR / f"transactions_{week_num}.json"
        stock_path = AMOUNTS_DIR / f"amounts_{week_num}.json"

        if not transactions_path.exists() or not stock_path.exists():
            return go.Figure()

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

            if stockout_day is None:
                sold_before_stockout = total
                days_counted = 7
            else:
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

        title = f"Sales vs Estimated Weekly Rate vs Stock — Week {week_num}"
    
    else:
        # Multi-week aggregation (excluding week 5)
        all_products = set()
        weekly_data = {}
        
        # Collect data from all weeks
        for week in range(0, 10):  # Check weeks 0-9
            if week == 5:  # Exclude week 5
                continue
            metrics = calculate_weekly_metrics(week)
            if metrics:
                weekly_data[week] = metrics
                all_products.update(metrics.keys())
        
        if not weekly_data:
            return go.Figure()
        
        # Calculate averages for each product
        products = []
        total_sold = []
        estimated_weekly = []
        stock_amount = []
        
        for product in sorted(all_products):
            total_sold_values = []
            estimated_weekly_values = []
            stock_values = []
            
            for week, metrics in weekly_data.items():
                if product in metrics:
                    total_sold_values.append(metrics[product]['total_sold'])
                    estimated_weekly_values.append(metrics[product]['estimated_weekly'])
                    stock_values.append(metrics[product]['stock'])
            
            if total_sold_values:
                products.append(product)
                total_sold.append(sum(total_sold_values) / len(total_sold_values))
                estimated_weekly.append(sum(estimated_weekly_values) / len(estimated_weekly_values))
                stock_amount.append(sum(stock_values) / len(stock_values))
        
        weeks_included = sorted([w for w in weekly_data.keys()])
        title = f"Average Sales Metrics Across Weeks {weeks_included} (excluding week 5)"

    # Create Plotly bar chart
    x = list(range(len(products)))

    fig = go.Figure()
    fig.add_trace(go.Bar(x=x, y=total_sold, width=0.25, name="Total Sold (Avg)" if week_num is None else "Total Sold", marker_color="#1f77b4"))
    fig.add_trace(go.Bar(x=x, y=estimated_weekly, width=0.25, name="Avg Rate ×7", marker_color="#ff7f0e"))
    fig.add_trace(go.Bar(x=x, y=stock_amount, width=0.25, name="Stock Amount (Avg)" if week_num is None else "Stock Amount", marker_color="#2ca02c"))

    fig.update_layout(
        title=title,
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
        # No argument: show aggregated view
        fig = generate_salesrate_figure()
        fig.show()
    else:
        # With argument: show specific week
        week = int(sys.argv[1])
        fig = generate_salesrate_figure(week)
        fig.show()