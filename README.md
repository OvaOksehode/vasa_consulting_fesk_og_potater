# Sales Dashboard

A **Dash-based interactive sales dashboard** for tracking, analyzing, and visualizing sales data, stock levels, revenue, and worker performance.  
The project is designed to be modular, making it easy to add new graphs, metrics, and data sources.

---

## Project Overview

This dashboard has two views:

### 1. Weekly View
- Allows viewing data for a specific week.
- Displays:
  - **Stock levels per product**  
  - **Revenue per product**  
  - **Sales rate**  
  - **Gross profit & loss pie charts**  
  - **Worker product sales** (bar or pie chart)
- Interactive dropdowns allow filtering by week, worker, and chart type.

### 2. Total View
- Displays cumulative metrics across all available weeks.
- Graphs include:
  - **Weekly & cumulative net profit/loss**  
  - **Total & cumulative sales volume + stock**  
  - **Potential sales value** if all stock were sold

---

## Adding Data

The dashboard reads data from JSON files in **specific folders**:

| Folder          | File format                     | Example                  | Purpose                                   |
|-----------------|---------------------------------|--------------------------|-------------------------------------------|
| `transactions/` | `transactions_<week>.json`      | `transactions_1.json`    | Stores weekly sales transactions         |
| `amounts/`      | `amounts_<week>.json`           | `amounts_1.json`         | Stock levels per product per week        |
| `prices/`       | `prices_<week>.json`            | `prices_1.json`          | Product prices for each week             |
| `schedules/`    | `schedules_<week>.json`         | `schedules_1.json`       | Worker schedules for the week            |

---

## Installation

1. Clone the repository:**

```bash
git clone <repository-url>
cd project
```

2. Create a Python virtual environment (recommended):
```bash
python -m venv .venv
```

Activate it:

### Linux / macOS:

```bash
source .venv/bin/activate
```

### Windows (PowerShell):

```bash
.venv\Scripts\Activate.ps1
```

### Windows (CMD):

```bash
.venv\Scripts\activate.bat
```

3. Install dependencies:
```bash
pip install -r scripts/requirements.txt
```

## How to run
### Run Locally with Python:
```bash
python scripts/dashboard.py
```

* Opens the dashboard at: http://localhost:8050
* Weekly and total graphs are interactive and auto-update when JSON data changes.

### Run with Docker:
1. Build Docker image:
```bash
docker build -t sales-dashboard .
```
* Builds a docker image that can be run as a container
