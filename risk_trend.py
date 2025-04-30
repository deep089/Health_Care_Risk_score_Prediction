import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import requests

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server
API = "http://localhost:8000"

app.layout = dbc.Container([
    html.H2("📊 Patient Risk Trend Dashboard", className="my-4 text-center text-primary fw-bold"),

    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Select Patient", className="fw-bold"),
                    dcc.Dropdown(id="patient-selector", placeholder="Select Patient", className="mb-2")
                ], md=6),

                dbc.Col([
                    html.Label("Filter by Gender", className="fw-bold"),
                    dcc.Dropdown(
                        id="gender-filter",
                        options=[
                            {"label": "All Genders", "value": "all"},
                            {"label": "Male", "value": "Male"},
                            {"label": "Female", "value": "Female"}
                        ],
                        value="all"
                    )
                ], md=3),

                dbc.Col([
                    html.Label("Export", className="fw-bold", style={"visibility": "hidden"}),
                    html.Div(html.Button("⬇️ Download CSV", id="download-btn", className="btn btn-success w-100"))
                ], md=3),
            ])
        ])
    ], className="mb-4 shadow rounded"),

    dbc.Card([
        dbc.CardBody([
            dcc.Graph(id="patient-trend-graph")
        ])
    ], className="mb-4 shadow rounded"),

    dbc.Row([
        dbc.Col(html.Div(id="risk-insight"), md=6),
        dbc.Col(html.Div(id="risk-details-panel"), md=6),
    ], className="gy-3"),

    dcc.Download(id="download-data"),
    dcc.Interval(id="refresh", interval=30*1000, n_intervals=0)
], fluid=True)


@app.callback(
    Output("patient-selector", "options"),
    Input("refresh", "n_intervals"),
    Input("gender-filter", "value")
)
def load_patients(_, gender):
    try:
        data = requests.get(f"{API}/active_patients").json()
        if gender != "all":
            data = [p for p in data if p['gender'] == gender]
        return [{"label": f"{p['first_name']} {p['last_name']}", "value": p['patient_id']} for p in data]
    except:
        return []

@app.callback(
    [Output("patient-trend-graph", "figure"),
     Output("risk-insight", "children"),
     Output("risk-details-panel", "children")],
    Input("patient-selector", "value"),
    Input("refresh", "n_intervals")
)
def load_trend(patient_id, _):
    if not patient_id:
        return px.line(title="Select a patient to view risk trend"), "", ""

    try:
        risk_data = requests.get(f"{API}/risk_scores").json()
        history = [r for r in risk_data if r['patient_id'] == patient_id]
        df = pd.DataFrame(history)

        if df.empty:
            return px.line(title="No historical risk data found for this patient"), "", ""

        df['score_date'] = pd.to_datetime(df['score_date'])
        df = df.sort_values('score_date')

        fig = px.line(df, x='score_date', y=['heart_disease_risk', 'diabetes_risk'],
                      markers=True, title='Risk Score History Over Time')
        fig.update_layout(xaxis_title="Date", yaxis_title="Risk Score", legend_title="Risk Type")

        latest = df.iloc[-1]
        heart = latest['heart_disease_risk']
        diabetes = latest['diabetes_risk']

        # Suggestions box
        suggestions = []
        if heart > 0.7:
            suggestions.append(html.Li("⚠️ High Heart Risk: Statins, BP medication, and lifestyle changes."))
        elif heart > 0.4:
            suggestions.append(html.Li("🟠 Moderate Heart Risk: Monitor BP and cholesterol."))

        if diabetes > 0.7:
            suggestions.append(html.Li("⚠️ High Diabetes Risk: Metformin, reduce sugar intake."))
        elif diabetes > 0.4:
            suggestions.append(html.Li("🟠 Moderate Diabetes Risk: Exercise and dietary care."))

        if not suggestions:
            suggestions.append(html.Li("✅ Risk scores are low. Keep healthy habits."))

        insight_box = dbc.Card([
            dbc.CardHeader("🩺 Suggestions", className="bg-primary text-white"),
            dbc.CardBody([
                html.Ul(suggestions, className="mb-0"),
                html.Small("Note: Please consult a physician.", className="text-muted")
            ])
        ], className="shadow-sm rounded")

        # Simulated vitals (replace with actual from Vitals table if available)
        simulated_vitals = {
            "Glucose": latest.get("glucose_level", 130),
            "Cholesterol": latest.get("cholesterol", 220),
            "Heart Rate": latest.get("heart_rate", 95),
            "BMI": latest.get("bmi", 28),
            "Hemoglobin": latest.get("hemoglobin", 13)
        }

        warnings = []
        if simulated_vitals["Glucose"] > 140:
            warnings.append("🩸 High Glucose")
        if simulated_vitals["Cholesterol"] > 240:
            warnings.append("🧬 High Cholesterol")
        if simulated_vitals["Heart Rate"] > 100:
            warnings.append("💓 Elevated Heart Rate")
        if simulated_vitals["BMI"] > 30:
            warnings.append("⚖️ High BMI")
        if simulated_vitals["Hemoglobin"] < 12:
            warnings.append("🧪 Low Hemoglobin")

        details_panel = dbc.Card([
            dbc.CardHeader("📘 Risk Formula & Vitals", className="bg-secondary text-white"),
            dbc.CardBody([
                html.H6("Heart Disease Risk Factors"),
                html.Ul([html.Li(f) for f in ["Age", "BP", "Heart Rate", "Cholesterol", "BMI"]]),
                html.H6("Diabetes Risk Factors"),
                html.Ul([html.Li(f) for f in ["Age", "Glucose", "BMI", "Hemoglobin"]]),
                html.Hr(),
                html.H6("🚩 Flagged Vitals"),
                html.Ul([html.Li(w) for w in warnings]) if warnings else html.P("✅ All vitals normal."),
            ])
        ], className="shadow-sm rounded")

        return fig, insight_box, details_panel

    except Exception as e:
        return px.line(title=f"Error loading risk data: {e}"), f"Error: {e}", ""

@app.callback(
    Output("download-data", "data"),
    Input("download-btn", "n_clicks"),
    State("patient-selector", "value"),
    prevent_initial_call=True
)
def export_patient_history(n_clicks, patient_id):
    try:
        risk_data = requests.get(f"{API}/risk_scores").json()
        history = [r for r in risk_data if r['patient_id'] == patient_id]
        df = pd.DataFrame(history)
        return dcc.send_data_frame(df.to_csv, filename=f"patient_{patient_id}_risk_history.csv")
    except:
        return None

if __name__ == '__main__':
    app.run(debug=True, port=8054)
