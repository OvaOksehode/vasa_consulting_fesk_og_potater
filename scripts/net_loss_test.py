# total_profit_time_series.py
import json
from collections import defaultdict
from pathlib import Path
import plotly.graph_objects as go

TRANSACTIONS_DIR = Path("transactions")
PRICES_DIR = Path("prices")
AMOUNTS_DIR = Path("amounts")
SUPPLIER_FILE = Path("supplier_prices.json")
WORKERS_FILE = Path("workers/workers.jsonl")
SCHEDULES_DIR = Path("schedules")


def load_workers():
    """Load worker data from JSONL file and return a dict mapping worker_id to salary."""
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
            if worker_id in workers:
                total_salary += workers[worker_id]
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return total_salary


def generate_total_profit_figure():
    """Generate Plotly figure showing weekly & cumulative profit/loss and potential stock sales."""
    if not SUPPLIER_FILE.exists():
        return go.Figure()

    with open(SUPPLIER_FILE) as f:
        supplier_prices = json.load(f)

    # Load worker salaries
    workers = load_workers()

    weeks = sorted(int(p.stem.split("_")[1]) for p in TRANSACTIONS_DIR.glob("transactions_*.json"))
    weekly_profits = []
    cumulative_profits = []
    potential_sales = []  # <-- NEW

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
            potential_sales.append(0)
            continue

        sold_totals = defaultdict(int)
        for trans_list in transactions.values():
            for t in trans_list:
                for merch, amount in zip(t.get("merch_types", []), t.get("merch_amounts", [])):
                    sold_totals[merch] += amount

        # Weekly net profit calculation
        total_weekly = sum(
            sold_totals.get(merch, 0) * weekly_prices.get(merch, 0)
            - stock_data.get(merch, 0) * supplier_prices.get(merch, 0)
            for merch in stock_data
        )

        # Potential sales if all stock sold (retail value)
        potential_total = sum(
            stock_data.get(merch, 0) * weekly_prices.get(merch, 0)
            for merch in stock_data
        )
        potential_sales.append(potential_total)

        # Subtract weekly salary costs
        weekly_salary_cost = get_weekly_salary_cost(week, workers)
        net_weekly = total_weekly - weekly_salary_cost

        weekly_profits.append(net_weekly)
        cumulative += net_weekly
        cumulative_profits.append(cumulative)

    # Build figure
    fig = go.Figure()

    # Weekly profit
    fig.add_trace(go.Scatter(
        x=weeks,
        y=weekly_profits,
        mode="lines+markers",
        name="Weekly Profit",
        line=dict(color="orange", width=2)
    ))

    # Cumulative profit
    fig.add_trace(go.Scatter(
        x=weeks,
        y=cumulative_profits,
        mode="lines+markers",
        name="Cumulative Profit",
        line=dict(color="blue", width=3)
    ))

    # Potential total sales value (new line)
    fig.add_trace(go.Scatter(
        x=weeks,
        y=potential_sales,
        mode="lines+markers",
        name="Potential Sales (if all stock sold)",
        line=dict(color="green", width=2, dash="dot")
    ))

    # Layout
    fig.update_layout(
        title="Profit/Loss & Potential Sales Value (including salaries)",
        xaxis_title="Week Number",
        yaxis_title="Amount (kr)",
        template="plotly_white",
        legend=dict(orientation="h"),
    )

    return fig


if __name__ == "__main__":
    fig = generate_total_profit_figure()
    fig.show()
