# potential_net_profit_timeseries.py
import json
from collections import defaultdict
from pathlib import Path
import plotly.graph_objects as go

AMOUNTS_DIR = Path("amounts")
PRICES_DIR = Path("prices")
SUPPLIER_FILE = Path("supplier_prices.json")
WORKERS_FILE = Path("workers/workers.jsonl")
SCHEDULES_DIR = Path("schedules")


def load_workers():
    """Load worker data and return dict mapping worker_id to salary."""
    workers = {}
    try:
        with open(WORKERS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    worker_data = json.loads(line)
                    workers[worker_data["worker_id"]] = worker_data["salary"]
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"Warning: Workers file not found: {WORKERS_FILE}")
    return workers


def get_weekly_salary_cost(week_number: int, workers: dict):
    """Calculate total weekly salary cost for workers scheduled that week."""
    file_schedule = SCHEDULES_DIR / f"schedules_{week_number}.json"
    total_salary = 0
    try:
        with open(file_schedule, "r") as f:
            schedule = json.load(f)

        scheduled_workers = set()
        for day_schedule in schedule.values():
            for shift in day_schedule:
                if "worker_id" in shift:
                    scheduled_workers.add(shift["worker_id"])

        for worker_id in scheduled_workers:
            total_salary += workers.get(worker_id, 0)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return total_salary


def calculate_potential_net_profit_for_week(week_num: int, workers: dict, supplier_prices: dict) -> float:
    """Calculate potential net profit if all stock is sold at retail price."""
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

    potential_profit = 0.0
    for merch, stock_amount in stock_data.items():
        sell_price = price_data.get(merch, 0)
        buy_price = supplier_prices.get(merch, 0)
        potential_profit += stock_amount * (sell_price - buy_price)

    # Subtract weekly salary costs
    weekly_salary_cost = get_weekly_salary_cost(week_num, workers)
    net_profit = potential_profit - weekly_salary_cost

    return net_profit


def generate_potential_net_profit_timeseries():
    """Generate Plotly line chart showing potential net profit per week."""
    if not SUPPLIER_FILE.exists():
        return go.Figure()

    with open(SUPPLIER_FILE) as f:
        supplier_prices = json.load(f)

    workers = load_workers()

    weeks = sorted(
        int(p.stem.split("_")[1])
        for p in AMOUNTS_DIR.glob("amounts_*.json")
        if p.stem.split("_")[1].isdigit()
    )

    potential_profits = [calculate_potential_net_profit_for_week(w, workers, supplier_prices) for w in weeks]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=weeks,
        y=potential_profits,
        mode="lines+markers",
        name="Potential Net Profit (All Stock Sold)",
        line=dict(color="green", width=3, dash="dot"),
        marker=dict(size=8)
    ))

    fig.update_layout(
        title="Potential Net Profit (If All Stock Sold)",
        xaxis_title="Week Number",
        yaxis_title="Potential Net Profit (kr)",
        template="plotly_white",
        legend=dict(x=0.02, y=0.98)
    )

    return fig


if __name__ == "__main__":
    fig = generate_potential_net_profit_timeseries()
    fig.show()
