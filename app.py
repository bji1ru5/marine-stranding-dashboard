#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import plotly.express as px
import json
import dash
from dash import Dash, dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc

# ======================================
# Load Data
# ======================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

df = pd.read_csv(os.path.join(BASE_DIR, "new.csv"))

with open(os.path.join(BASE_DIR, "Taiwan_ADM1_wgs84.geojson"), encoding="utf-8") as f:
    geo = json.load(f)

# ======================================
# City Mapping
# ======================================
city_map = {
    "New Tapei City": "New Taipei",
    "Penghu County": "Penghu",
    "Yilan County": "Yilan County",
    "Taitung County": "Taitung County",
    "Pingtung County": "Pingtung County",
    "Kaohsiung City": "Kaohsiung",
    "Lienchiang County": "Matsu Islands",
    "Hualien County ": "Hualien County",
    "Yunlin County": "Yunlin County",
    "Tainan City": "Tainan",
    "Miaoli County": "Miaoli County",
    "Taoyuan City": "Taoyuan",
    "Keelung City": "Keelung",
    "Changhua County": "Changhua County",
    "Kinmen County": "Kinmen",
    "Chiayi County": "Chiayi County",
    "Taichung City": "Taichung",
    "Hsinchu County": "Hsinchu County",
    "Hsinchu City": "Hsinchu"
}

# ======================================
# Dash App
# ======================================
app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
server = app.server    # FOR CLOUD RUN DEPLOYMENT

# ======================================
# UI Styling
# ======================================
ui_css = dcc.Markdown(
    """
    <style>
        * { font-family: 'Noto Sans TC', sans-serif; }
        body { background-color: #f2f4f7; }

        h1 {
            color: #003366 !important;
            font-weight: 800;
            text-align: center;
            margin-bottom: 25px;
        }

        .card-section {
            background: white;
            padding: 25px 30px;
            margin-top: 20px;
            border-radius: 14px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.08);
        }

        .filter-label {
            font-size: 14px;
            font-weight: bold;
            color: #003366;
            margin-bottom: 4px;
        }

        .form-title {
            color: #003366;
            font-weight: 700;
            border-left: 6px solid #003366;
            padding-left: 10px;
            margin-bottom: 10px;
        }

        .btn-primary {
            background-color: #003366 !important;
            border-color: #003366 !important;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: 600;
        }
    </style>
    """,
    dangerously_allow_html=True
)

# ======================================
# Layout
# ======================================
app.layout = dbc.Container([

    ui_css,

    html.H1("Taiwan Marine Stranding Dashboard"),

    # ===== Filters =====
    html.Div([
        dbc.Row([

            dbc.Col([
                html.Div("Year", className="filter-label"),
                dcc.Dropdown(
                    id="year",
                    options=[{"label": y, "value": y} for y in sorted(df["Year"].unique())],
                    placeholder="Select Year"
                ),
            ], width=3),

            dbc.Col([
                html.Div("Month", className="filter-label"),
                dcc.Dropdown(
                    id="month",
                    options=[{"label": str(m), "value": m} for m in sorted(df["Month"].unique())]
                            + [{"label": "All", "value": "All"}],
                    value="All"
                ),
            ], width=3),

            dbc.Col([
                html.Div("City", className="filter-label"),
                dcc.Dropdown(
                    id="city",
                    options=[{"label": c, "value": c} for c in sorted(df["City"].unique())]
                            + [{"label": "All", "value": "All"}],
                    value="All"
                )
            ], width=3),

            dbc.Col([
                html.Div("Category", className="filter-label"),
                dcc.Dropdown(
                    id="category",
                    options=[
                        {"label": "All", "value": "All"},
                        {"label": "Sea Turtle", "value": "Sea Turtle"},
                        {"label": "Cetacean", "value": "Cetacean"},
                    ],
                    value="All"
                )
            ], width=3),

        ])
    ], className="card-section"),

    # ===== Graphs =====
    html.Div([
        dcc.Graph(id="map"),
        dcc.Graph(id="bar_type"),
    ], className="card-section"),

    html.Div([
        dbc.Row([
            dbc.Col(dcc.Graph(id="trend_year"), width=6),
            dbc.Col(dcc.Graph(id="rank_city"), width=6),
        ])
    ], className="card-section"),

    # ===== Submit Form =====
    html.Div([
        html.H3("Report New Stranding Case", className="form-title"),

        dbc.Row([
            dbc.Col(dbc.Input(id="input_year", placeholder="Year"), width=3),
            dbc.Col(dbc.Input(id="input_month", placeholder="Month (1–12)"), width=3),
            dbc.Col(dcc.Dropdown(
                id="input_city",
                options=[{"label": c, "value": c} for c in sorted(df["City"].unique())],
                placeholder="City"), width=3),
            dbc.Col(dcc.Dropdown(
                id="input_type",
                options=[
                    {"label": "Sea Turtle", "value": "Sea Turtle"},
                    {"label": "Cetacean", "value": "Cetacean"},
                ],
                placeholder="Type"), width=3),
        ], className="mb-3"),

        dbc.Textarea(id="input_note", placeholder="Notes (optional)", className="mb-3"),

        dbc.Button("Submit", id="submit_btn", color="primary"),
        html.Div(id="submit_msg", className="text-success mt-3"),

    ], className="card-section"),

])

# ======================================
# Reset Month / City + Map Click Update
# ======================================
GLOBAL_MAX = df["Total Count"].max()

@app.callback(
    Output("city", "value"),
    Output("month", "value"),
    Input("year", "value"),
    Input("map", "clickData"),
    prevent_initial_call=True
)
def update_city_or_reset(year, clickData):

    trigger = callback_context.triggered[0]["prop_id"]

    if trigger.startswith("year"):
        return "All", "All"

    if trigger.startswith("map") and clickData:
        clicked_geo = clickData["points"][0]["location"]
        reverse_map = {v:k for k,v in city_map.items()}
        return reverse_map.get(clicked_geo, "All"), dash.no_update

    return dash.no_update, dash.no_update

# ======================================
# Main Dashboard Callback
# ======================================
@app.callback(
    Output("map", "figure"),
    Output("bar_type", "figure"),
    Output("trend_year", "figure"),
    Output("rank_city", "figure"),
    Input("year", "value"),
    Input("month", "value"),
    Input("city", "value"),
    Input("category", "value")
)
def update_dashboard(year, month, city, category):

    if year is None:
        return {}, {}, {}, {}

    # ---- Data Filter ----
    base = df[df["Year"] == year].copy()
    if month not in (None, "All"):
        base = base[base["Month"] == int(month)]

    filtered = base.copy()
    if city not in (None, "All"):
        filtered = filtered[filtered["City"] == city]

    # ---- Map Data ----
    map_df = base.copy()
    map_df["City_geo"] = map_df["City"].map(city_map).fillna(map_df["City"])

    def map_color(r):
        if city == "All":
            return r["Total Count"]
        return "#003366" if r["City"] == city else "#d3d3d3"

    map_df["MapColor"] = map_df.apply(map_color, axis=1)
    
    # ---- Create BLOCK (binned) categories ----    
    stepped_scale = [
        (0.00, "#fee8c8"),
        (0.25, "#fee8c8"),
        (0.25, "#fdbb84"),
        (0.50, "#fdbb84"),
        (0.50, "#e34a33"),
        (0.75, "#e34a33"),
        (0.75, "#b30000"),
        (1.00, "#b30000"),
    ]

    # ---- Map ----
    if city == "All":

        fig_map = px.choropleth_mapbox(
            map_df,
            geojson=geo,
            locations="City_geo",
            color="Total Count",
            featureidkey="properties.shapeName",
            mapbox_style="open-street-map",
            zoom=6,
            center={"lat": 23.7, "lon": 120.9},
            color_continuous_scale=stepped_scale,
            range_color=[0, GLOBAL_MAX]
        )
        fig_map.update_layout(
            coloraxis_colorbar=dict(
                title="Number of Strandings",
                tickvals=[2, 6, 10, 14, 18],
                ticktext=["0–3", "4–7", "8–11", "12–15", "16–20"]
            )
        )

    else:
        fig_map = px.choropleth_mapbox(
            map_df,
            geojson=geo,
            locations="City_geo",
            color="MapColor",
            featureidkey="properties.shapeName",
            mapbox_style="open-street-map",
            zoom=6,
            center={"lat":23.7, "lon":120.9},
            color_discrete_map="identity"
        )


    # ---- Bar Chart ----
    bar_df = filtered.melt(
        id_vars="City",
        value_vars=["Sea Turtle","Cetacean"],
        var_name="Type",
        value_name="Count"
    )
    fig_bar = px.bar(bar_df, x="City", y="Count", color="Type")

    # ---- Trend Chart ----
    trend_df = df.groupby("Year")[["Sea Turtle","Cetacean","Total Count"]].sum().reset_index()
    trend_long = trend_df.melt(id_vars="Year", value_vars=["Sea Turtle","Cetacean","Total Count"])
    fig_trend = px.line(trend_long, x="Year", y="value", color="variable", markers=True)

    # ---- Ranking ----
    rank_base = df[df["Year"] == year].copy()
    if month not in (None,"All"):
        rank_base = rank_base[rank_base["Month"] == int(month)]

    rank_df = rank_base.groupby("City")[["Sea Turtle","Cetacean","Total Count"]].sum().reset_index()
    rank_df = rank_df.sort_values("Total Count", ascending=False)

    rank_long = rank_df.melt(id_vars=["City"], value_vars=["Sea Turtle","Cetacean"])
    fig_rank = px.bar(
        rank_long,
        x="value",
        y="City",
        color="variable",
        orientation="h",
        category_orders={"City": rank_df["City"].tolist()}
    )

    return fig_map, fig_bar, fig_trend, fig_rank


# ======================================
# Submit New Case
# ======================================
@app.callback(
    Output("submit_msg", "children"),
    Input("submit_btn", "n_clicks"),
    State("input_year", "value"),
    State("input_month", "value"),
    State("input_city", "value"),
    State("input_type", "value"),
    State("input_note", "value"),
    prevent_initial_call=True
)
def submit_case(n, year, month, city, category, note):

    global df

    new_row = {
        "Year": int(year),
        "Month": int(month),
        "City": city,
        "Sea Turtle": 1 if category == "Sea Turtle" else 0,
        "Cetacean": 1 if category == "Cetacean" else 0,
        "Total Count": 1,
        "Note": note
    }

    df = pd.concat([df, pd.DataFrame([new_row])])
    df.to_csv("new.csv", index=False)

    return "Case submitted successfully!"

# ======================================
# Run App（for local + cloud）
# ======================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port)
