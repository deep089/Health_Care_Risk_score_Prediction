# nurse_portal.py (Nurse Specific Portal with Patient Dropdown for Vitals & Lab Reports)

import dash
from dash import html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import requests

# Initialize Dash App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX], suppress_callback_exceptions=True)
server = app.server
API = "http://localhost:8000"

# ===== Page Functions =====

def get_patient_options():
    try:
        patients = requests.get(f"{API}/active_patients").json()
        return [{'label': f"{p['first_name']} {p['last_name']}", 'value': p['patient_id']} for p in patients]
    except:
        return []

def get_active_patients():
    try:
        patients = requests.get(f"{API}/active_patients").json()
        if not patients:
            return html.Div("No active patients available.")
        df = pd.DataFrame(patients)
        table = dbc.Table.from_dataframe(df[['first_name', 'last_name', 'gender', 'date_of_birth']], striped=True, bordered=True, hover=True)
        return dbc.Card([
            dbc.CardBody([
                html.H4("Currently Checked-In Patients", className="fw-bold text-primary mb-3"),
                table
            ])
        ], className="shadow p-4 mb-4 bg-light rounded")
    except:
        return html.Div("Error loading patients.")

def get_lab_reports(patient_id=None):
    try:
        labs = requests.get(f"{API}/recent_lab_reports").json()
        if not labs or not patient_id:
            return html.Div("No lab reports found.")
        df = pd.DataFrame(labs)
        df = df[df['patient_id'] == patient_id]
        if df.empty:
            return html.Div("No lab reports found.")
        fig = px.scatter(df, x="report_date", y="report_type", color="result",
                         title="Lab Reports", height=400)
        fig.update_traces(marker=dict(size=14, line=dict(width=1, color="DarkSlateGrey")))
        return dcc.Graph(figure=fig)
    except:
        return html.Div("Error loading lab reports.")

def get_risk_scores(patient_id=None):
    try:
        scores = requests.get(f"{API}/risk_scores").json()
        if not scores or not patient_id:
            return html.Div("No risk scores found.")
        df = pd.DataFrame(scores)
        df = df[df['patient_id'] == patient_id]
        if df.empty:
            return html.Div("No risk scores found.")
        df['score_date'] = pd.to_datetime(df['score_date'])
        fig = px.line(df, x="score_date", y=["heart_disease_risk", "diabetes_risk"],
                      title="Risk Score Trends", markers=True)
        return dcc.Graph(figure=fig)
    except:
        return html.Div("Error loading risk scores.")

def get_appointments():
    try:
        appointments = requests.get(f"{API}/appointments_today").json()
        if not appointments:
            return html.Div("No appointments today.")
        items = [html.Li(f"\U0001F4C5 {appt['appointment_date']} for {appt.get('first_name', '')} {appt.get('last_name', '')}") for appt in appointments]
        return dbc.Card([
            dbc.CardBody([
                html.H4("Today's Appointments", className="fw-bold text-primary mb-3"),
                html.Ul(items, style={"fontSize": "18px"})
            ])
        ], className="shadow p-4 mb-4 bg-light rounded")
    except:
        return html.Div("Error loading appointments.")

def get_settings():
    return dbc.Card([
        dbc.CardBody([
            html.H4("Settings", className="fw-bold text-primary mb-3"),
            html.P("Settings for notifications, alerts, and profile will appear here.")
        ])
    ], className="shadow p-4 mb-4 bg-light rounded")

# ===== Layout =====
app.layout = dbc.Container([
    html.H2("\U0001F691 Nurse Dashboard", className="text-center text-primary my-4 fw-bold"),
    dbc.Tabs([
        dbc.Tab(label="\U0001F3E5 Active Patients", tab_id="patients"),
        dbc.Tab(label="\U0001F9EA Lab Reports", tab_id="labs"),
        dbc.Tab(label="\U0001F489 Vitals & Risk Scores", tab_id="vitals"),
        dbc.Tab(label="\U0001F527 Manage Appointments", tab_id="appointments"),
        dbc.Tab(label="⚙️ Settings", tab_id="settings")
    ], id="tabs", active_tab="patients", className="mb-4"),
    html.Div(id="dynamic-content")
], fluid=True, style={"padding": "20px"})

# ===== Callbacks =====
@app.callback(
    Output("dynamic-content", "children"),
    Input("tabs", "active_tab"),
    State("dynamic-content", "children"),
    prevent_initial_call=False
)
def update_page(tab, children):
    if tab == "patients":
        return get_active_patients()
    elif tab == "labs" or tab == "vitals":
        return html.Div([
            dcc.Dropdown(id="patient-dropdown", options=get_patient_options(), placeholder="Select a patient", className="mb-4"),
            html.Div(id="patient-data")
        ])
    elif tab == "appointments":
        return get_appointments()
    elif tab == "settings":
        return get_settings()
    else:
        return html.Div("Tab not found.")

@app.callback(
    Output("patient-data", "children"),
    Input("patient-dropdown", "value"),
    State("tabs", "active_tab"),
    prevent_initial_call=True
)
def update_patient_data(patient_id, tab):
    if not patient_id:
        return html.Div("Please select a patient.")
    if tab == "labs":
        return get_lab_reports(patient_id)
    elif tab == "vitals":
        return get_risk_scores(patient_id)
    else:
        return html.Div()

# ===== Run =====
if __name__ == "__main__":
    app.run(debug=True, port=8057)
