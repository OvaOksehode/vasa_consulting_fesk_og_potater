#!/usr/bin/env python3
"""
Calculate total salary paid to employees for a given week.

Usage:
    python employee_salaries.py <week_number>

Example:
    python employee_salaries.py 5
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

WORKERS_FILE = Path("workers/workers.jsonl")
SCHEDULES_DIR = Path("schedules")


def load_workers():
    """Load worker data from JSONL file and return a dict mapping worker_id to worker info."""
    workers = {}
    try:
        with open(WORKERS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    worker_data = json.loads(line)
                    workers[worker_data["worker_id"]] = {
                        "name": worker_data.get("name", "Unknown"),
                        "salary": worker_data["salary"]
                    }
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"Error: Workers file not found: {WORKERS_FILE}")
        sys.exit(1)
    
    return workers


def get_scheduled_workers(week_number: int):
    """Get list of worker IDs scheduled for the given week."""
    schedule_file = SCHEDULES_DIR / f"schedules_{week_number}.json"
    
    try:
        with open(schedule_file, "r") as f:
            schedule = json.load(f)
    except FileNotFoundError:
        print(f"Error: Schedule file not found: {schedule_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in schedule file: {schedule_file}")
        sys.exit(1)
    
    # Collect unique workers scheduled this week
    scheduled_workers = set()
    shifts_per_worker = defaultdict(int)
    
    for day, day_schedule in schedule.items():
        for shift in day_schedule:
            if "worker_id" in shift:
                worker_id = shift["worker_id"]
                scheduled_workers.add(worker_id)
                shifts_per_worker[worker_id] += 1
    
    return scheduled_workers, shifts_per_worker


def calculate_weekly_salaries(week_number: int):
    """Calculate and display salary information for a given week."""
    workers = load_workers()
    scheduled_workers, shifts_per_worker = get_scheduled_workers(week_number)
    
    if not scheduled_workers:
        print(f"No workers scheduled for week {week_number}")
        return
    
    print(f"\n{'='*60}")
    print(f"SALARY REPORT - WEEK {week_number}")
    print(f"{'='*60}\n")
    
    print(f"{'Worker ID':<15} {'Name':<20} {'Shifts':<10} {'Salary (kr)':<15}")
    print(f"{'-'*60}")
    
    total_salary = 0
    worker_salary_list = []
    
    for worker_id in sorted(scheduled_workers):
        if worker_id in workers:
            worker_info = workers[worker_id]
            name = worker_info["name"]
            salary = worker_info["salary"]
            shifts = shifts_per_worker[worker_id]
            
            worker_salary_list.append((worker_id, name, shifts, salary))
            total_salary += salary
        else:
            print(f"{worker_id:<15} {'UNKNOWN':<20} {'N/A':<10} {'N/A':<15}")
    
    # Sort by salary (highest first)
    worker_salary_list.sort(key=lambda x: x[3], reverse=True)
    
    for worker_id, name, shifts, salary in worker_salary_list:
        print(f"{worker_id:<15} {name:<20} {shifts:<10} {salary:<15,.2f}")
    
    print(f"{'-'*60}")
    print(f"{'TOTAL':<46} {total_salary:>13,.2f}")
    print(f"{'='*60}\n")
    
    # Summary statistics
    num_workers = len(scheduled_workers)
    avg_salary = total_salary / num_workers if num_workers > 0 else 0
    total_shifts = sum(shifts_per_worker.values())
    
    print(f"Summary:")
    print(f"  - Total workers scheduled: {num_workers}")
    print(f"  - Total shifts: {total_shifts}")
    print(f"  - Average salary per worker: {avg_salary:,.2f} kr")
    print(f"  - Total salary cost: {total_salary:,.2f} kr\n")


def main():
    if len(sys.argv) != 2:
        print("Usage: python employee_salaries.py <week_number>")
        print("\nExample:")
        print("  python employee_salaries.py 5")
        sys.exit(1)
    
    try:
        week_number = int(sys.argv[1])
    except ValueError:
        print(f"Error: Week number must be an integer, got '{sys.argv[1]}'")
        sys.exit(1)
    
    if week_number < 0:
        print(f"Error: Week number must be non-negative, got {week_number}")
        sys.exit(1)
    
    calculate_weekly_salaries(week_number)


if __name__ == "__main__":
    main()