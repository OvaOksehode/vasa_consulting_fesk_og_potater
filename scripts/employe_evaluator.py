import json
import glob
import os
import re
from collections import defaultdict


# --- Helpers ---
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def load_jsonl(path):
    workers = {}
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            try:
                entry = json.loads(line)
                workers[entry["worker_id"]] = entry
            except json.JSONDecodeError as e:
                # Try fixing common issues: comma as decimal separator
                try:
                    # Pattern: finds numbers with commas like 5833,6282857143
                    fixed_line = re.sub(r'(\d+),(\d+)', r'\1.\2', line)
                    entry = json.loads(fixed_line)
                    workers[entry["worker_id"]] = entry
                    print(f"ℹ️ Fixed decimal separator in line {line_num}")
                except:
                    print(f"⚠️ Error parsing line {line_num} in {path}: {e}")
                    char_pos = e.pos if hasattr(e, 'pos') else 104
                    start = max(0, char_pos - 50)
                    end = min(len(line), char_pos + 50)
                    print(f"   Context around error (char {char_pos}):")
                    print(f"   ...{line[start:end]}...")
                    continue
    return workers


def calculate_worker_sales(transactions, week_num):
    """Calculate sales per worker for each day."""
    # Map numeric keys to day names
    day_map = {'1': 'monday', '2': 'tuesday', '3': 'wednesday',
               '4': 'thursday', '5': 'friday', '6': 'saturday', '7': 'sunday'}

    # Structure: {day: {worker_id: total_sales}}
    worker_sales = defaultdict(lambda: defaultdict(float))

    print(f"  Transaction data structure keys: {list(transactions.keys())[:5]}")

    for day, records in transactions.items():
        day_name = day_map.get(day, day.lower())
        print(f"  Day {day} ({day_name}): {len(records)} records")

        if records and len(records) > 0:
            print(f"    First record sample: {list(records[0].keys()) if records else 'empty'}")

        for transaction in records:
            transaction_type = transaction.get("transaction_type")
            worker_id = transaction.get("register_worker")  # Changed from worker_id
            amounts = transaction.get("merch_amounts", [])

            if transaction_type == "customer_sale" and worker_id and amounts:
                total = sum(amounts)
                worker_sales[day_name][worker_id] += total

    return worker_sales


def get_day_workers(schedule):
    """Return mapping of day -> list of worker_ids (registers only)."""
    workers_per_day = {}
    for day, shifts in schedule.items():
        # Filter to 'registers' dept only
        registers = [s["worker_id"] for s in shifts if s["department"] == "registers"]
        workers_per_day[day.lower()] = registers
    return workers_per_day


def analyze_cashier_performance():
    # --- Load worker info ---
    workers = load_jsonl(os.path.join("..", "workers", "workers.jsonl"))
    print(f"📊 Loaded {len(workers)} workers")

    # --- Locate weekly files ---
    transaction_files = sorted(glob.glob(os.path.join("..", "transactions", "transactions_*.json")))
    print(f"🔍 Found {len(transaction_files)} transaction files")
    results = []

    for tfile in transaction_files:
        week_num = os.path.splitext(os.path.basename(tfile))[0].split("_")[-1]

        # Load matching schedule file
        schedule_path = os.path.join("..", "schedules", f"schedules_{week_num}.json")
        if not os.path.exists(schedule_path):
            print(f"⚠️ Missing schedule for week {week_num}, skipping...")
            continue

        transactions = load_json(tfile)
        schedule = load_json(schedule_path)

        worker_sales = calculate_worker_sales(transactions, week_num)
        workers_per_day = get_day_workers(schedule)

        print(f"\n📅 Week {week_num}:")

        # Ensure consistent day ordering
        day_order = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        days = [d for d in day_order if d in worker_sales]

        for day in days:
            sales_data = worker_sales[day]
            scheduled_workers = workers_per_day.get(day, [])

            # Filter to only scheduled cashiers
            cashier_sales = {wid: sales for wid, sales in sales_data.items()
                             if wid in scheduled_workers}

            if not cashier_sales:
                print(f"  {day.capitalize()}: No sales data")
                continue

            # Sort by sales amount
            sorted_cashiers = sorted(cashier_sales.items(), key=lambda x: x[1], reverse=True)

            # Get top and bottom performers
            top_worker_id, top_sales = sorted_cashiers[0]
            bottom_worker_id, bottom_sales = sorted_cashiers[-1]

            top_name = workers.get(top_worker_id, {}).get("name", "Unknown")
            bottom_name = workers.get(bottom_worker_id, {}).get("name", "Unknown")

            total_day_sales = sum(cashier_sales.values())

            results.append({
                "week": week_num,
                "day": day,
                "total_sales": total_day_sales,
                "top_performer": {
                    "name": top_name,
                    "worker_id": top_worker_id,
                    "sales": top_sales
                },
                "bottom_performer": {
                    "name": bottom_name,
                    "worker_id": bottom_worker_id,
                    "sales": bottom_sales
                },
                "num_cashiers": len(cashier_sales)
            })

            print(f"  {day.capitalize()}:")
            print(f"    Total Sales: ${total_day_sales:,.2f}")
            print(f"    🏆 Top: {top_name} - ${top_sales:,.2f}")
            print(f"    📉 Bottom: {bottom_name} - ${bottom_sales:,.2f}")
            print(f"    👥 Cashiers: {len(cashier_sales)}")

    return results


# --- Run the analysis ---
if __name__ == "__main__":
    results = analyze_cashier_performance()

    print("\n" + "=" * 60)
    print("=== CASHIER PERFORMANCE REPORT ===")
    print("=" * 60 + "\n")

    for r in results:
        print(f"📅 Week {r['week']} - {r['day'].upper()}")
        print(f"   Total Sales: ${r['total_sales']:,.2f}")
        print(f"   🏆 Top Performer: {r['top_performer']['name']} (${r['top_performer']['sales']:,.2f})")
        print(f"   📉 Bottom Performer: {r['bottom_performer']['name']} (${r['bottom_performer']['sales']:,.2f})")
        print(f"   Cashiers on Shift: {r['num_cashiers']}")
        print()