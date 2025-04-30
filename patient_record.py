import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import requests

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
API = "http://localhost:8000"

app.layout = dbc.Container([
    html.H2("📋 Top Risky Patients", className="my-4 text-primary"),

    # Filters
    dbc.Row([
        dbc.Col([
            html.Label("🧬 Risk Type"),
            dcc.Dropdown(
                id="risk-type",
                options=[
                    {"label": "Heart Risk", "value": "heart"},
                    {"label": "Diabetes Risk", "value": "diabetes"},
                    {"label": "Both", "value": "both"}
                ],
                value="both",
                clearable=False
            )
        ], md=3),

        dbc.Col([
            html.Label("⚠️ Minimum Risk Threshold"),
            dcc.Slider(
                id="min-risk",
                min=0,
                max=1,
                step=0.05,
                value=0.4,
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], md=5),

        dbc.Col([
            html.Label("🧑 Gender (optional)"),
            dcc.Dropdown(id="gender-filter", placeholder="All", clearable=True)
        ], md=4)
    ], className="mb-4"),

    html.Div(id="patient-table"),

    dcc.Interval(id='interval-update', interval=15 * 1000, n_intervals=0)
], fluid=True)


@app.callback(
    Output("gender-filter", "options"),
    Input("interval-update", "n_intervals")
)
def populate_gender_filter(_):
    try:
        data = requests.get(f"{API}/risk_scores").json()
        df = pd.DataFrame(data)
        genders = df["gender"].dropna().unique()
        return [{"label": gender.title(), "value": gender} for gender in genders]
    except:
        return []


@app.callback(
    Output("patient-table", "children"),
    Input("interval-update", "n_intervals"),
    Input("risk-type", "value"),
    Input("min-risk", "value"),
    Input("gender-filter", "value")
)
def load_patient_table(_, risk_type, min_risk, gender_filter):
    try:
        data = requests.get(f"{API}/risk_scores").json()
        df = pd.DataFrame(data)

        # Filter by gender if selected
        if gender_filter:
            df = df[df["gender"] == gender_filter]

        # Risk filtering
        if risk_type == "heart":
            df = df[df["heart_disease_risk"] >= min_risk]
        elif risk_type == "diabetes":
            df = df[df["diabetes_risk"] >= min_risk]
        else:  # both
            df = df[(df["heart_disease_risk"] >= min_risk) | (df["diabetes_risk"] >= min_risk)]

        # Combine for ranking
        df["combined_risk"] = df["heart_disease_risk"] + df["diabetes_risk"]
        df = df.sort_values(by="combined_risk", ascending=False).head(100)

        # Format risk visually
        def format_risk(val):
            if val > 0.7:
                return html.Span(f"{val:.2f}", style={"color": "red", "fontWeight": "bold"})
            elif val > 0.4:
                return html.Span(f"{val:.2f}", style={"color": "orange", "fontWeight": "bold"})
            return html.Span(f"{val:.2f}")

        table_header = [
            html.Thead(html.Tr([
                html.Th("Patient Name"),
                html.Th("Heart Risk"),
                html.Th("Diabetes Risk"),
                html.Th("Gender"),
                html.Th("Last Updated")
            ]))
        ]

        table_rows = []
        for _, row in df.iterrows():
            table_rows.append(html.Tr([
                html.Td(f"{row['first_name']} {row['last_name']}"),
                html.Td(format_risk(row['heart_disease_risk'])),
                html.Td(format_risk(row['diabetes_risk'])),
                html.Td(row.get("gender", "N/A")),
                html.Td(row['score_date'])
            ]))

        return dbc.Table(table_header + [html.Tbody(table_rows)],
                         bordered=True, hover=True, responsive=True, striped=True)

    except Exception as e:
        return html.Div(f"Error loading records: {str(e)}", className="text-danger")


if __name__ == "__main__":
    app.run(debug=True, port=8052)
