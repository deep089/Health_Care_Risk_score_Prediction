# patient_portal.py (Patient Specific Portal)

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import requests

# Initialize Dash App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX], suppress_callback_exceptions=True)
server = app.server
API = "http://localhost:8000"
PATIENT_ID = 1  # For demo, assuming logged-in patient ID is 1

# ===== Layout =====
app.layout = dbc.Container([
    html.H2("\U0001F3E5 Patient Health Portal", className="text-center text-primary my-4 fw-bold"),
    dbc.Tabs([
        dbc.Tab(label="\U0001F4CB Health Records", tab_id="records"),
        dbc.Tab(label="\U0001F48A Medications", tab_id="meds"),
        dbc.Tab(label="\U0001F9EA Lab Results", tab_id="labs"),
        dbc.Tab(label="\u2764\ufe0f Risk Scores", tab_id="risks"),
        dbc.Tab(label="\U0001F489 Vaccinations", tab_id="vaccines"),
        dbc.Tab(label="\U0001F4DA Education", tab_id="education"),
        dbc.Tab(label="\U0001F4E8 Messages", tab_id="messages"),
        dbc.Tab(label="\U0001F4C5 Appointments", tab_id="appointments"),
        dbc.Tab(label="\U0001F4D3 Symptom Journal", tab_id="journal"),
        dbc.Tab(label="\U0001F3AF Health Goals", tab_id="goals")
    ], id="tabs", active_tab="records", className="mb-4"),
    dbc.Spinner(html.Div(id="tab-content"), color="primary")
], fluid=True, style={"padding": "20px"})

# ===== Tab Content Callback =====
@app.callback(Output("tab-content", "children"), Input("tabs", "active_tab"))
def render_tab(tab):
    tabs = {
        "records": get_health_records,
        "meds": get_medications,
        "labs": get_lab_results,
        "risks": get_risk_scores,
        "vaccines": get_vaccination_records,
        "education": get_educational_resources,
        "messages": get_messages_section,
        "appointments": get_appointments,
        "journal": get_symptom_journal,
        "goals": get_health_goals
    }
    return tabs.get(tab, lambda: "Tab not found")()

# ===== Page Functions =====

def get_health_records():
    try:
        patient = requests.get(f"{API}/patient_details/{PATIENT_ID}").json()[0]
        return dbc.Card([
            dbc.CardBody([
                html.H3(f"{patient['first_name']} {patient['last_name']}", className="fw-bold text-primary"),
                html.Hr(),
                html.P(f"\U0001F464 Gender: {patient['gender']}"),
                html.P(f"\U0001F382 Date of Birth: {patient['date_of_birth']}"),
                html.P(f"\U0001FA7A Last Visit: {patient['last_visit'] or 'No recent visit'}")
            ])
        ], className="shadow p-4 mb-4 bg-light rounded")
    except:
        return html.Div("Error loading patient record.")

def get_medications():
    return dbc.Card([
        dbc.CardBody([
            html.H4("Medications", className="fw-bold text-primary mb-3"),
            html.Ul([
                html.Li("\U0001F489 Lisinopril 10mg - Morning"),
                html.Li("\U0001F48A Metformin 500mg - After meals")
            ], style={"fontSize": "18px"})
        ])
    ], className="shadow p-4 mb-4 bg-light rounded")

def get_lab_results():
    try:
        labs = requests.get(f"{API}/lab_reports_by_patient/{PATIENT_ID}").json()
        if not labs:
            return html.Div("No lab results available.")
        df = pd.DataFrame(labs)
        fig = px.scatter(df, x="report_date", y="report_type", color="result",
                         title="My Lab Results", height=400)
        fig.update_traces(marker=dict(size=14, line=dict(width=1, color="DarkSlateGrey")))
        return dcc.Graph(figure=fig)
    except:
        return html.Div("Error loading lab results.")

def get_risk_scores():
    try:
        risks = requests.get(f"{API}/patient_risk_trend/{PATIENT_ID}").json()
        if not risks:
            return html.Div("No risk scores available.")
        df = pd.DataFrame(risks)
        df['month'] = pd.to_datetime(df['month'])
        fig = px.line(df, x="month", y=["avg_heart_risk", "avg_diabetes_risk"],
                      title="Risk Score Trends", markers=True)
        return dcc.Graph(figure=fig)
    except:
        return html.Div("Error loading risk scores.")

def get_vaccination_records():
    return dbc.Card([
        dbc.CardBody([
            html.H4("Vaccination History", className="fw-bold text-primary mb-3"),
            html.Ul([
                html.Li("Flu Vaccine - Oct 2023"),
                html.Li("COVID-19 Booster - Jan 2024")
            ], style={"fontSize": "18px"})
        ])
    ], className="shadow p-4 mb-4 bg-light rounded")

def get_educational_resources():
    return dbc.Card([
        dbc.CardBody([
            html.H4("Educational Resources", className="fw-bold text-primary mb-3"),
            html.Ul([
                html.Li(html.A("Managing Hypertension", href="#")),
                html.Li(html.A("Diabetes Care Tips", href="#")),
                html.Li(html.A("Healthy Lifestyle Habits", href="#"))
            ], style={"fontSize": "18px"})
        ])
    ], className="shadow p-4 mb-4 bg-light rounded")

def get_messages_section():
    return dbc.Card([
        dbc.CardBody([
            html.H4("Secure Messaging", className="fw-bold text-primary mb-3"),
            dbc.Textarea(id="message-box", placeholder="Type a message...", rows=4, className="mb-3"),
            dbc.Button("Send", color="success")
        ])
    ], className="shadow p-4 mb-4 bg-light rounded")

def get_appointments():
    try:
        appointments = requests.get(f"{API}/appointments_by_patient/{PATIENT_ID}").json()
        if not appointments:
            return html.Div("No upcoming appointments.")
        items = [html.Li(f"\U0001F4C5 {appt['appointment_date']} with Dr. {appt.get('doctor_name', 'Unknown')}") for appt in appointments]
        return dbc.Card([
            dbc.CardBody([
                html.H4("Appointments", className="fw-bold text-primary mb-3"),
                html.Ul(items, style={"fontSize": "18px"})
            ])
        ], className="shadow p-4 mb-4 bg-light rounded")
    except:
        return html.Div("Error loading appointments.")

def get_symptom_journal():
    return dbc.Card([
        dbc.CardBody([
            html.H4("Symptom Journal", className="fw-bold text-primary mb-3"),
            dbc.Textarea(placeholder="Describe your symptoms here...", rows=6, className="mb-3"),
            dbc.Button("Save Entry", color="info")
        ])
    ], className="shadow p-4 mb-4 bg-light rounded")

def get_health_goals():
    return dbc.Card([
        dbc.CardBody([
            html.H4("Health Goals", className="fw-bold text-primary mb-3"),
            html.Ul([
                html.Li("Achieve 10,000 steps per day"),
                html.Li("Maintain BP < 120/80 mmHg"),
                html.Li("Maintain healthy blood sugar levels")
            ], style={"fontSize": "18px"})
        ])
    ], className="shadow p-4 mb-4 bg-light rounded")

# ===== Run =====
if __name__ == "__main__":
    app.run(debug=True, port=8056)