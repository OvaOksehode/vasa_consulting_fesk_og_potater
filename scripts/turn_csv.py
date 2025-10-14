import os
import json
import csv
import zipfile
from glob import glob

# --- Folders ---
folders = {
    "amounts": "amounts",
    "prices": "prices",
    "schedules": "schedules",
    "transactions": "transactions",
    "workers": "workers",
}
single_files = ["supplier_prices.json"]  # single JSON files in root

output_zip = "all_csv_files.zip"

def json_to_csv(json_path, csv_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    # Handle dictionary of lists (like transactions or schedules)
    if isinstance(data, dict):
        # Convert dict of lists into rows
        rows = []
        # Check if inner elements are dicts
        for key, value in data.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        row = {"key": key, **item}
                        rows.append(row)
                    else:
                        rows.append({"key": key, "value": item})
            else:
                rows.append({"key": key, "value": value})
    elif isinstance(data, list):
        # list of dicts
        rows = data
    else:
        # single value
        rows = [{"value": data}]

    # Determine CSV headers
    headers = set()
    for row in rows:
        headers.update(row.keys())
    headers = list(headers)

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

def jsonl_to_csv(jsonl_path, csv_path):
    rows = []
    with open(jsonl_path, "r") as f:
        for line in f:
            rows.append(json.loads(line))

    headers = set()
    for row in rows:
        headers.update(row.keys())
    headers = list(headers)

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

# Create a temp folder to hold CSV files
import tempfile
temp_dir = tempfile.mkdtemp()

# Convert folder files
for folder, path in folders.items():
    files = glob(os.path.join(path, "*.json")) + glob(os.path.join(path, "*.jsonl"))
    for file in files:
        rel_path = os.path.relpath(file)  # keep folder structure
        csv_path = os.path.join(temp_dir, os.path.splitext(rel_path)[0] + ".csv")
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

        if file.endswith(".jsonl"):
            jsonl_to_csv(file, csv_path)
        else:
            json_to_csv(file, csv_path)

# Convert single JSON files in root
for file in single_files:
    csv_path = os.path.join(temp_dir, os.path.splitext(file)[0] + ".csv")
    json_to_csv(file, csv_path)

# --- Create ZIP ---
with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, temp_dir)  # preserve folder structure
            zipf.write(abs_path, rel_path)

print(f"All CSV files packed into {output_zip}")
