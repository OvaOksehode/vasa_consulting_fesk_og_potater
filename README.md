# Sales Dashboard

A **Dash-based interactive sales dashboard** for tracking, analyzing, and visualizing sales data, stock levels, revenue, and worker performance.  
The project is designed to be modular, making it easy to add new graphs, metrics, and data sources.

---

## Project Overview

This dashboard has three main sections:

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

### 3. Generate Changes
- Allows generating new files based on selected past weeks.
- Weeks can be **toggled on/off** with a checklist.
- Click “Generate Files” to create the corresponding output.
- Useful for scenario testing or simulating future outcomes based on previous data.

---

## File Structure