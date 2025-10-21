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
# Run app
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
