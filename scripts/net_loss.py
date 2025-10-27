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
                    import json
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
        import json
        with open(file_schedule, "r") as f:
            schedule = json.load(f)
        
        # Get unique workers who were scheduled this week
        scheduled_workers = set()
        for day_schedule in schedule.values():
            for shift in day_schedule:
                if "worker_id" in shift:
                    scheduled_workers.add(shift["worker_id"])
        
        # Sum up their salaries
        for worker_id in scheduled_workers:
            if worker_id in workers:
                # Salary is weekly, so we can just add it
                total_salary += workers[worker_id]
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    return total_salary


def generate_total_profit_figure():
    """Generate Plotly figure showing weekly and cumulative profit/loss with colored shading."""
    if not SUPPLIER_FILE.exists():
        return go.Figure()
    
    with open(SUPPLIER_FILE) as f:
        supplier_prices = json.load(f)
    
    # Load worker salaries
    workers = load_workers()

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
        
        # Subtract weekly salary costs
        weekly_salary_cost = get_weekly_salary_cost(week, workers)
        net_weekly = total_weekly - weekly_salary_cost

        weekly_profits.append(net_weekly)
        cumulative += net_weekly
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
        title="Weekly & Cumulative Net Profit/Loss (including salary costs)",
        xaxis_title="Week Number",
        yaxis_title="Net Profit (kr)",
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
    
    # Load worker salaries
    workers = load_workers()

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
        
        # Subtract weekly salary costs
        weekly_salary_cost = get_weekly_salary_cost(week, workers)
        net_weekly_profit = weekly_profit - weekly_salary_cost

        running_total += net_weekly_profit
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
