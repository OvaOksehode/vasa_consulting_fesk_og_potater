# scripts/profit_trends.py
import json
from collections import defaultdict
from pathlib import Path
import plotly.graph_objects as go
import numpy as np

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
        
        # Get unique workers who were scheduled this week
        scheduled_workers = set()
        for day_schedule in schedule.values():
            for shift in day_schedule:
                if "worker_id" in shift:
                    scheduled_workers.add(shift["worker_id"])
        
        # Sum up their salaries
        for worker_id in scheduled_workers:
            if worker_id in workers:
                total_salary += workers[worker_id]
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    return total_salary


def get_weekly_profits():
    """Calculate weekly profits for all weeks."""
    if not SUPPLIER_FILE.exists():
        return [], []
    
    with open(SUPPLIER_FILE) as f:
        supplier_prices = json.load(f)
    
    workers = load_workers()
    weeks = sorted(int(p.stem.split("_")[1]) for p in TRANSACTIONS_DIR.glob("transactions_*.json"))
    
    weekly_profits = []

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
        
        weekly_salary_cost = get_weekly_salary_cost(week, workers)
        net_weekly = total_weekly - weekly_salary_cost

        weekly_profits.append(net_weekly)

    return weeks, weekly_profits


def generate_profit_trend_figures():
    """Generate two figures: weeks 0-3 and weeks 4-6 with trendlines for weekly profit."""
    
    all_weeks, weekly_profits = get_weekly_profits()
    
    if not all_weeks:
        print("No profit data available")
        return None, None
    
    # Split into two periods
    weeks_0_3 = [w for w in all_weeks if 0 <= w <= 3]
    weeks_4_6 = [w for w in all_weeks if 4 <= w <= 6]
    
    # Get corresponding data
    idx_0_3 = [i for i, w in enumerate(all_weeks) if w in weeks_0_3]
    idx_4_6 = [i for i, w in enumerate(all_weeks) if w in weeks_4_6]
    
    weekly_0_3 = [weekly_profits[i] for i in idx_0_3]
    weekly_4_6 = [weekly_profits[i] for i in idx_4_6]
    
    # Create figure for weeks 0-3
    fig1 = go.Figure()
    
    if len(weeks_0_3) >= 2:
        x = np.array(weeks_0_3)
        y = np.array(weekly_0_3)
        
        # Calculate linear regression
        coeffs = np.polyfit(x, y, 1)
        a, b = coeffs[0], coeffs[1]
        trendline_y = a * x + b
        
        # Add data line
        fig1.add_trace(go.Scatter(
            x=weeks_0_3, y=weekly_0_3, 
            mode='markers+lines',
            name='Weekly Profit',
            marker=dict(size=10),
            line=dict(width=3)
        ))
        
        # Add trendline
        fig1.add_trace(go.Scatter(
            x=weeks_0_3, y=trendline_y,
            mode='lines',
            name=f'Trend (y={a:.2f}x+{b:.2f})',
            line=dict(dash='dash', color='red', width=3)
        ))
        
        print("\n=== WEEKS 0-3 TREND EQUATION ===")
        print(f"Weekly Profit: y = {a:.2f}x + {b:.2f}")
    
    fig1.update_layout(
        title="Weekly Profit Trend: Weeks 0-3",
        xaxis_title="Week",
        yaxis_title="Profit (kr)",
        template="plotly_white",
        height=500
    )
    
    # Create figure for weeks 4-6
    fig2 = go.Figure()
    
    if len(weeks_4_6) >= 2:
        x = np.array(weeks_4_6)
        y = np.array(weekly_4_6)
        
        # Calculate linear regression
        coeffs = np.polyfit(x, y, 1)
        a, b = coeffs[0], coeffs[1]
        trendline_y = a * x + b
        
        # Add data line
        fig2.add_trace(go.Scatter(
            x=weeks_4_6, y=weekly_4_6,
            mode='markers+lines',
            name='Weekly Profit',
            marker=dict(size=10),
            line=dict(width=3)
        ))
        
        # Add trendline
        fig2.add_trace(go.Scatter(
            x=weeks_4_6, y=trendline_y,
            mode='lines',
            name=f'Trend (y={a:.2f}x+{b:.2f})',
            line=dict(dash='dash', color='red', width=3)
        ))
        
        print("\n=== WEEKS 4-6 TREND EQUATION ===")
        print(f"Weekly Profit: y = {a:.2f}x + {b:.2f}")
    
    fig2.update_layout(
        title="Weekly Profit Trend: Weeks 4-6",
        xaxis_title="Week",
        yaxis_title="Profit (kr)",
        template="plotly_white",
        height=500
    )
    
    return fig1, fig2


if __name__ == "__main__":
    fig1, fig2 = generate_profit_trend_figures()
    if fig1 and fig2:
        fig1.show()
        fig2.show()