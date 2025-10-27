# worker_product_sales.py
import json
from collections import defaultdict
from pathlib import Path
import plotly.graph_objects as go

TRANSACTIONS_DIR = Path("transactions")
WORKERS_FILE = Path("workers/workers.jsonl")
SCHEDULES_DIR = Path("schedules")


def load_workers():
    """Load worker data from JSONL file and return a dict mapping worker_id to name."""
    workers = {}
    try:
        with open(WORKERS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    worker_data = json.loads(line)
                    workers[worker_data["worker_id"]] = worker_data["name"]
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line: {line[:50]}... Error: {e}")
                    continue
    except FileNotFoundError:
        print(f"Warning: Workers file not found: {WORKERS_FILE}")
    return workers


def get_workers_on_schedule(week_number: int):
    """Get set of worker IDs who were on schedule for the specified week in the 'registers' department."""
    file_schedule = SCHEDULES_DIR / f"schedules_{week_number}.json"
    scheduled_workers = set()
    
    try:
        with open(file_schedule, "r") as f:
            schedule = json.load(f)
        
        # Iterate through all days in the schedule
        for day_schedule in schedule.values():
            for shift in day_schedule:
                # Only include workers from the "registers" department
                if "worker_id" in shift and shift.get("department") == "registers":
                    scheduled_workers.add(shift["worker_id"])
    except FileNotFoundError:
        print(f"Warning: Schedule file not found: {file_schedule}")
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse schedule file: {e}")
    
    return scheduled_workers


def generate_worker_product_sales_figure(week_number: int, worker_id: str = None):
    """
    Returns a Plotly figure for product amounts sold by a specific worker.
    If worker_id is None, shows all workers' data combined.
    """
    file_transactions = TRANSACTIONS_DIR / f"transactions_{week_number}.json"

    try:
        with open(file_transactions, "r") as f:
            transactions = json.load(f)
    except FileNotFoundError:
        return go.Figure()

    # Load worker names
    workers = load_workers()

    # Sum up product amounts sold per worker
    product_amounts = defaultdict(int)

    for trans_list in transactions.values():
        for transaction in trans_list:
            # Filter by worker if specified
            if worker_id is not None and transaction.get("register_worker") != worker_id:
                continue

            for merch, amount in zip(
                transaction.get("merch_types", []),
                transaction.get("merch_amounts", [])
            ):
                product_amounts[merch] += amount

    if not product_amounts:
        # Return empty figure if no data
        return go.Figure().update_layout(
            title="No sales data available for selected worker",
            template="plotly_white"
        )

    # Sort by amount (descending)
    sorted_products = sorted(product_amounts.items(), key=lambda x: x[1], reverse=True)
    labels = [item[0] for item in sorted_products]
    amounts = [item[1] for item in sorted_products]

    # Build Plotly figure with horizontal bar chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels,
        x=amounts,
        orientation='h',
        marker_color="steelblue"
    ))
    
    worker_name = workers.get(worker_id, "All Workers") if worker_id else "All Workers"
    fig.update_layout(
        title=f"Week {week_number} — Product Sales by {worker_name}",
        yaxis_title="Product",
        xaxis_title="Total Amount Sold",
        template="plotly_white",
        height=500
    )
    
    return fig


def generate_worker_product_pie_figure(week_number: int, worker_id: str = None):
    """
    Returns a Plotly pie chart for product amounts sold by a specific worker.
    If worker_id is None, shows all workers' data combined.
    """
    file_transactions = TRANSACTIONS_DIR / f"transactions_{week_number}.json"

    try:
        with open(file_transactions, "r") as f:
            transactions = json.load(f)
    except FileNotFoundError:
        return go.Figure()

    # Load worker names
    workers = load_workers()

    # Sum up product amounts sold per worker
    product_amounts = defaultdict(int)

    for trans_list in transactions.values():
        for transaction in trans_list:
            # Filter by worker if specified
            if worker_id is not None and transaction.get("register_worker") != worker_id:
                continue

            for merch, amount in zip(
                transaction.get("merch_types", []),
                transaction.get("merch_amounts", [])
            ):
                product_amounts[merch] += amount

    if not product_amounts:
        # Return empty figure if no data
        return go.Figure().update_layout(
            title="No sales data available for selected worker",
            template="plotly_white"
        )

    # Sort by amount (descending) and take top items for better readability
    sorted_products = sorted(product_amounts.items(), key=lambda x: x[1], reverse=True)
    # Take top 10 items, group the rest as "Others"
    top_items = sorted_products[:10]
    others_sum = sum(amount for _, amount in sorted_products[10:])
    
    labels = [item[0] for item in top_items]
    amounts = [item[1] for item in top_items]
    
    if others_sum > 0:
        labels.append("Others")
        amounts.append(others_sum)

    # Build Plotly figure with pie chart
    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=labels,
        values=amounts,
        hole=0.3,
        hoverinfo="label+percent+value",
        textinfo="label+percent"
    ))
    
    worker_name = workers.get(worker_id, "All Workers") if worker_id else "All Workers"
    fig.update_layout(
        title=f"Week {week_number} — Product Sales Distribution by {worker_name}",
        template="plotly_white",
        height=500
    )
    
    return fig
