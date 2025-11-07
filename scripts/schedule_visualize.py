#!/usr/bin/env python3
"""
Print who works each day and shift.

Usage:
    python print_shifts.py <week_number>

Example:
    python print_shifts.py 5
"""

import sys
import json
from pathlib import Path

WORKERS_FILE = Path("workers/workers.jsonl")
SCHEDULES_DIR = Path("schedules")


def load_workers():
    """Load worker data from JSONL file."""
    workers = {}
    try:
        with open(WORKERS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    worker_data = json.loads(line)
                    workers[worker_data["worker_id"]] = worker_data.get("name", worker_data["worker_id"])
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"Error: Workers file not found: {WORKERS_FILE}")
        sys.exit(1)
    
    return workers


def print_schedule(week_number):
    """Print schedule for a given week."""
    workers = load_workers()
    
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
    
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    day_display = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    print(f"\n{'='*70}")
    print(f"SCHEDULE - WEEK {week_number}")
    print(f"{'='*70}\n")
    
    for i, day in enumerate(days):
        day_schedule = schedule.get(day, [])
        
        if not day_schedule:
            print(f"{day_display[i]}:")
            print("  No shifts scheduled\n")
            continue
        
        print(f"{day_display[i]}:")
        
        # Group by shift
        shift_1 = []
        shift_2 = []
        
        for shift_data in day_schedule:
            worker_id = shift_data.get("worker_id", "Unknown")
            worker_name = workers.get(worker_id, worker_id)
            department = shift_data.get("department", "")
            shift_num = shift_data.get("shift")
            
            worker_text = f"{worker_name} ({department})" if department else worker_name
            
            if shift_num == 1:
                shift_1.append(worker_text)
            elif shift_num == 2:
                shift_2.append(worker_text)
        
        if shift_1:
            print(f"  Shift 1: {', '.join(shift_1)}")
        else:
            print(f"  Shift 1: No workers")
            
        if shift_2:
            print(f"  Shift 2: {', '.join(shift_2)}")
        else:
            print(f"  Shift 2: No workers")
        
        print()
    
    print(f"{'='*70}\n")


def main():
    if len(sys.argv) != 2:
        print("Usage: python print_shifts.py <week_number>")
        print("\nExample:")
        print("  python print_shifts.py 5")
        sys.exit(1)
    
    try:
        week_number = int(sys.argv[1])
    except ValueError:
        print(f"Error: Week number must be an integer, got '{sys.argv[1]}'")
        sys.exit(1)
    
    if week_number < 0:
        print(f"Error: Week number must be non-negative, got {week_number}")
        sys.exit(1)
    
    print_schedule(week_number)


if __name__ == "__main__":
    main()