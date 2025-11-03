# scripts/time_to_profit.py
import json
from collections import defaultdict
from pathlib import Path
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
        pass
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


def calculate_time_to_million():
    """Calculate how long until we reach 1 million profit from current debt."""
    
    all_weeks, weekly_profits = get_weekly_profits()
    
    if not all_weeks:
        print("No profit data available")
        return
    
    # Get weeks 4-6 data
    weeks_4_6 = [w for w in all_weeks if 4 <= w <= 6]
    idx_4_6 = [i for i, w in enumerate(all_weeks) if w in weeks_4_6]
    weekly_4_6 = [weekly_profits[i] for i in idx_4_6]
    
    if len(weeks_4_6) < 2:
        print("Not enough data for weeks 4-6")
        return
    
    # Calculate trend from weeks 4-6
    x = np.array(weeks_4_6)
    y = np.array(weekly_4_6)
    coeffs = np.polyfit(x, y, 1)
    a, b = coeffs[0], coeffs[1]
    
    print(f"\n=== WEEKS 4-6 TREND ===")
    print(f"Trend equation: y = {a:.2f}x + {b:.2f}")
    print(f"\nWeek 4: {weekly_4_6[0]:,.2f} kr")
    print(f"Week 5: {weekly_4_6[1]:,.2f} kr")
    print(f"Week 6: {weekly_4_6[2]:,.2f} kr")
    
    # Calculate cumulative profit through week 6
    cumulative_profit = sum(weekly_profits)
    print(f"\n=== CURRENT POSITION ===")
    print(f"Cumulative profit through week 6: {cumulative_profit:,.2f} kr")
    
    # Starting debt
    STARTING_DEBT = -5_300_000
    current_position = STARTING_DEBT + cumulative_profit
    print(f"Starting debt: {STARTING_DEBT:,.2f} kr")
    print(f"Current position: {current_position:,.2f} kr")
    
    # Target: reach 1 million profit
    TARGET = 1_000_000
    needed_profit = TARGET - current_position
    print(f"\nProfit needed to reach 1 million: {needed_profit:,.2f} kr")
    
    # Project forward using the trend from week 6
    week = 7
    projected_cumulative = current_position
    
    print(f"\n=== PROJECTION ===")
    while projected_cumulative < TARGET:
        # Use trendline to predict weekly profit
        predicted_weekly = a * week + b
        projected_cumulative += predicted_weekly
        
        print(f"Week {week}: Weekly profit = {predicted_weekly:,.2f} kr, Cumulative = {projected_cumulative:,.2f} kr")
        
        if projected_cumulative >= TARGET:
            print(f"\n🎉 Reach 1 million profit in week {week}!")
            weeks_from_now = week - 6
            print(f"That's {weeks_from_now} weeks from week 6")
            break
        
        week += 1
        
        # Safety check
        if week > 100:
            print("\n⚠️ Would take more than 100 weeks with current trend")
            if predicted_weekly > 0:
                approx_weeks = needed_profit / predicted_weekly
                print(f"Approximate weeks needed: {approx_weeks:.1f}")
            else:
                print("⚠️ Weekly profit trend is not positive - may never reach 1 million")
            break


if __name__ == "__main__":
    calculate_time_to_million()