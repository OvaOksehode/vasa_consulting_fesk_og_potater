# app.py
from pathlib import Path
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go

# ---------------------------------------------------------------------
# Imports from refactored scripts
# ---------------------------------------------------------------------
from net_loss import generate_total_profit_figure
from stock_visual import generate_stock_visual_figure
from salesrate import generate_salesrate_figure
from revenue_per_product import generate_revenue_per_product_figure
from profit_loss_pie import generate_profit_loss_pie_figures
from worker_product_sales import generate_worker_product_sales_figure, generate_worker_product_pie_figure, load_workers, get_workers_on_schedule

# ---------------------------------------------------------------------
# File locations
# ---------------------------------------------------------------------
TRANSACTIONS_DIR = Path("transactions")

# Detect available weeks
AVAILABLE_WEEKS = sorted([
    int(p.stem.split("_")[1])
    for p in TRANSACTIONS_DIR.glob("transactions_*.json")
    if p.stem.split("_")[1].isdigit()
])

# ---------------------------------------------------------------------
# Dash app
# ---------------------------------------------------------------------
app = Dash(__name__)
app.title = "Sales Dashboard"

# ---------------------------------------------------------------------
# Layout with all components in place
# ---------------------------------------------------------------------
app.layout = html.Div(
    [
        html.H1("Sales Dashboard", style={"textAlign": "center", "margin": "20px"}),

        dcc.Tabs(id="tabs", value="weekly", children=[
            dcc.Tab(label="Weekly View", value="weekly"),
            dcc.Tab(label="Total View", value="total"),
        ]),

        # Weekly tab content (all components exist, visibility toggled)
        html.Div(id="weekly-tab", style={"display": "block"}, children=[
            # Week selector
            html.Div(
                [
                    html.Label("Select Week:", style={"marginRight": "10px", "fontWeight": "bold"}),
                    dcc.Dropdown(
                        id="week-dropdown",
                        options=[{"label": f"Week {w}", "value": w} for w in AVAILABLE_WEEKS],
                        value=AVAILABLE_WEEKS[0] if AVAILABLE_WEEKS else None,
                        clearable=False,
                        style={"width": "200px"},
                    ),
                ],
                style={"display": "flex", "justifyContent": "center", "alignItems": "center", "marginBottom": "20px"},
            ),

            # Top row: stock visual + profit/revenue
            html.Div(
                [
                    html.Div(dcc.Graph(id="stock-graph"), style={"flex": "1", "padding": "10px"}),
                    html.Div(dcc.Graph(id="profit-graph"), style={"flex": "1", "padding": "10px"}),
                ],
                style={"display": "flex", "flexWrap": "wrap", "justifyContent": "space-around"},
            ),

            # Bottom row: salesrate + pie chart
            html.Div(
                [
                    html.Div(dcc.Graph(id="salesrate-graph"), style={"flex": "1", "padding": "10px", "height": "400px"}),
                    html.Div(
                        [
                            html.Label("Pie Chart View:", style={"fontWeight": "bold"}),
                            dcc.Dropdown(
                                id="pie-view-dropdown",
                                options=[
                                    {"label": "Gross Profit", "value": "profit"},
                                    {"label": "Gross Loss", "value": "loss"},
                                    {"label": "Both", "value": "both"}
                                ],
                                value="profit",
                                clearable=False,
                                style={"marginBottom": "10px"}
                            ),
                            dcc.Graph(id="pie-graph", style={"height": "400px"})
                        ],
                        style={"flex": "1", "padding": "10px"}
                    )
                ],
                style={"display": "flex", "flexWrap": "wrap", "justifyContent": "space-around"},
            ),

            # New row: worker product sales bar chart
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Worker Product Sales:", style={"fontWeight": "bold", "marginBottom": "10px"}),
                            html.Div(
                                [
                                    html.Label("Select Worker:", style={"marginRight": "10px", "fontWeight": "bold"}),
                                    dcc.Dropdown(
                                        id="worker-dropdown",
                                        options=[{"label": "All Workers", "value": "all"}],
                                        value="all",
                                        clearable=False,
                                        style={"width": "250px", "marginRight": "20px"}
                                    ),
                                    html.Label("Select Week:", style={"marginRight": "10px", "fontWeight": "bold"}),
                                    dcc.Dropdown(
                                        id="worker-week-dropdown",
                                        options=[{"label": f"Week {w}", "value": w} for w in AVAILABLE_WEEKS],
                                        value=AVAILABLE_WEEKS[0] if AVAILABLE_WEEKS else None,
                                        clearable=False,
                                        style={"width": "180px", "marginRight": "20px"}
                                    ),
                                    html.Label("Chart Type:", style={"marginRight": "10px", "fontWeight": "bold"}),
                                    dcc.Dropdown(
                                        id="worker-chart-type-dropdown",
                                        options=[
                                            {"label": "Bar Chart", "value": "bar"},
                                            {"label": "Pie Chart", "value": "pie"}
                                        ],
                                        value="bar",
                                        clearable=False,
                                        style={"width": "180px"}
                                    ),
                                ],
                                style={"display": "flex", "alignItems": "center", "marginBottom": "10px"}
                            ),
                            dcc.Graph(id="worker-product-graph", style={"height": "500px"})
                        ],
                        style={"flex": "1", "padding": "10px", "minWidth": "800px"}
                    )
                ],
                style={"display": "flex", "justifyContent": "space-around", "width": "100%"},
            ),
        ]),

        # Total tab
        html.Div(id="total-tab", style={"display": "none"}, children=[
            dcc.Graph(id="total-profit-graph", figure=generate_total_profit_figure())
        ])

    ],
    style={"fontFamily": "Arial, sans-serif", "maxWidth": "2000px", "margin": "0 auto"},
)

# ---------------------------------------------------------------------
# Callback to switch tab visibility
# ---------------------------------------------------------------------
@app.callback(
    Output("weekly-tab", "style"),
    Output("total-tab", "style"),
    Input("tabs", "value")
)
def switch_tab(selected_tab):
    if selected_tab == "weekly":
        return {"display": "block"}, {"display": "none"}
    else:
        return {"display": "none"}, {"display": "block"}

# ---------------------------------------------------------------------
# Callback to populate worker dropdown based on schedule
# ---------------------------------------------------------------------
@app.callback(
    Output("worker-dropdown", "options"),
    Output("worker-dropdown", "value"),
    Input("worker-week-dropdown", "value")
)
def update_worker_dropdown(selected_week):
    workers = load_workers()
    
    # Start with "All Workers" option
    options = [{"label": "All Workers", "value": "all"}]
    
    if selected_week is not None:
        # Get workers who were on schedule for this week
        scheduled_workers = get_workers_on_schedule(selected_week)
        print(f"Week {selected_week}: Found {len(scheduled_workers)} scheduled workers")
        
        # Only include workers who were on schedule
        for worker_id, name in workers.items():
            if worker_id in scheduled_workers:
                options.append({"label": name, "value": worker_id})
    else:
        # If no week selected, show all workers
        for worker_id, name in workers.items():
            options.append({"label": name, "value": worker_id})
    
    # Sort by name (but keep "All Workers" first)
    options[1:] = sorted(options[1:], key=lambda x: x["label"])
    
    print(f"Total options in dropdown: {len(options)}")
    
    # Reset to "all" when week changes
    return options, "all"

# ---------------------------------------------------------------------
# Callback to update weekly tab graphs
# ---------------------------------------------------------------------
@app.callback(
    Output("stock-graph", "figure"),
    Output("profit-graph", "figure"),
    Output("salesrate-graph", "figure"),
    Output("pie-graph", "figure"),
    Input("week-dropdown", "value"),
    Input("pie-view-dropdown", "value")
)
def update_weekly_graphs(selected_week, pie_view):
    if selected_week is None:
        empty_fig = go.Figure()
        return empty_fig, empty_fig, empty_fig, empty_fig

    # Top row
    fig_stock = generate_stock_visual_figure(selected_week)
    fig_profitbar = generate_revenue_per_product_figure(selected_week)

    # Bottom-left
    fig_salesrate = generate_salesrate_figure(selected_week)

    # Bottom-right pie chart
    fig_profit_pie, fig_loss_pie = generate_profit_loss_pie_figures(selected_week)
    if pie_view == "profit":
        fig_pie = fig_profit_pie
    elif pie_view == "loss":
        fig_pie = fig_loss_pie
    else:
        fig_pie = go.Figure()
        for trace in fig_profit_pie.data:
            fig_pie.add_trace(trace)
        for trace in fig_loss_pie.data:
            fig_pie.add_trace(trace)
        fig_pie.update_layout(title="Gross Profit & Loss", showlegend=True)

    return fig_stock, fig_profitbar, fig_salesrate, fig_pie

# ---------------------------------------------------------------------
# Callback to update worker product sales graph
# ---------------------------------------------------------------------
@app.callback(
    Output("worker-product-graph", "figure"),
    Input("worker-week-dropdown", "value"),
    Input("worker-dropdown", "value"),
    Input("worker-chart-type-dropdown", "value")
)
def update_worker_product_graph(selected_week, selected_worker, chart_type):
    if selected_week is None:
        return go.Figure()

    worker_id = None if selected_worker == "all" else selected_worker
    
    if chart_type == "pie":
        fig_worker_product = generate_worker_product_pie_figure(selected_week, worker_id)
    else:
        fig_worker_product = generate_worker_product_sales_figure(selected_week, worker_id)
    
    return fig_worker_product

# ---------------------------------------------------------------------
# Run app
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
