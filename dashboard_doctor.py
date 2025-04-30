# doctor_dashboard.py

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import requests
import plotly.express as px
import joblib

# Load models
heart_model = joblib.load("heart_risk_model.pkl")
diabetes_model = joblib.load("diabetes_risk_model.pkl")

# API Endpoint
API = "http://localhost:8000"

# ========== Sidebar ==========
sidebar = html.Div(
    [
        html.Div(
            [
            
                html.H4("Healthcare Monitoring", className="text-primary text-center mb-4")
            ],
            className="text-center"
        ),
        dbc.Nav(
            [
                dbc.NavLink("🏥 Dashboard", href="/doctor_dashboard", active="exact"),
                dbc.NavLink("🧑‍⚕️ Patient Records", href="/patient_record", active="exact"),
                dbc.NavLink("❤️ Risk Assessment", href="/risk_trend", active="exact"),
                dbc.NavLink("🧪 Lab Results", href="#", active="exact"),
                dbc.NavLink("📄 Reports", href="#", active="exact"),
                dbc.NavLink("⚙️ Settings", href="#", active="exact"),
            ],
            vertical=True,
            pills=True,
            className="flex-column"
        ),
    ],
    style={
        "backgroundColor": "#f8f9fa",
        "height": "100vh",
        "padding": "20px",
        "position": "fixed",
        "width": "16%",
        "borderRight": "1px solid #dee2e6"
    }
)

# ========== Header ==========
header = dbc.Navbar(
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H2("Doctor Portal", className="text-white"), width="auto"),
            dbc.Col(
                dbc.DropdownMenu(
                    label="Dr. SmitRR 👨‍⚕️",
                    children=[
                        dbc.DropdownMenuItem("Profile", href="#"),
                        dbc.DropdownMenuItem("Logout", href="/")
                    ],
                    className="ms-auto"
                ),
                width="auto",
                className="ms-auto"
            )
        ], align="center", className="g-0")
    ]),
    color="primary",
    dark=True,
    className="mb-4",
    style={"marginLeft": "16%"}
)

# ========== Main Layout ==========
layout_content = html.Div([
    html.H3("Patient Risk Assessment", className="mb-4 fw-bold"),

    dbc.Row([
        dbc.Col(dcc.Dropdown(id="patient-selector", placeholder="Select Patient", style={"width": "100%"}), width=4)
    ], className="mb-4"),

    html.Div(id="risk-assessment-body")
], style={"padding": "30px", "marginLeft": "16%"})

# ========== Final Layout ==========
doctor_dashboard_layout = html.Div([
    sidebar,
    header,
    layout_content
])

# ========== Callbacks ==========
def register_doctor_callbacks(app):

    @app.callback(
        Output("patient-selector", "options"),
        Input("patient-selector", "id")
    )
    def load_patients(_):
        try:
            patients = requests.get(f"{API}/active_patients").json()
            return [{"label": f"{p['first_name']} {p['last_name']}", "value": p["patient_id"]} for p in patients]
        except:
            return []

    @app.callback(
        Output("risk-assessment-body", "children"),
        Input("patient-selector", "value")
    )
    def display_patient_risk(patient_id):
        if not patient_id:
            return ""

        try:
            # Get risk scores
            risk_data = requests.get(f"{API}/risk_scores").json()
            risk = next((r for r in risk_data if r["patient_id"] == patient_id), None)
            if not risk:
                return dbc.Alert("❌ No risk score found for this patient.", color="danger")

            heart_risk = risk['heart_disease_risk']
            diabetes_risk = risk['diabetes_risk']
            heart_label = "High Risk" if heart_risk > 0.7 else "Moderate Risk" if heart_risk > 0.4 else "Low Risk"
            diabetes_label = "High Risk" if diabetes_risk > 0.7 else "Moderate Risk" if diabetes_risk > 0.4 else "Low Risk"
            heart_bar_color = "danger" if heart_risk > 0.7 else "warning" if heart_risk > 0.4 else "success"
            diabetes_bar_color = "danger" if diabetes_risk > 0.7 else "warning" if diabetes_risk > 0.4 else "success"

            # Get patient demographics
            info_response = requests.get(f"{API}/patient_details/{patient_id}").json()
            if not info_response:
                return dbc.Alert("❌ No patient details found.", color="danger")

            info = info_response[0]
            full_name = f"{info.get('first_name', 'N/A')} {info.get('last_name', 'N/A')}"
            gender = info.get('gender', 'N/A')

            try:
                dob = pd.to_datetime(info['date_of_birth'])
                age = int((pd.Timestamp.now() - dob).days / 365.25)
            except:
                age = "N/A"

            try:
                last_visit = pd.to_datetime(info['last_visit']).strftime("%Y-%m-%d") if info['last_visit'] else "N/A"
            except:
                last_visit = "N/A"

            # Risk trend
            trend_data = requests.get(f"{API}/patient_risk_trend/{patient_id}").json()
            df_trend = pd.DataFrame(trend_data)
            fig = px.line(df_trend, x='month', y=['avg_heart_risk', 'avg_diabetes_risk'],
                          markers=True, title='Risk Score History')

            return html.Div([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H4(full_name, className="fw-bold"),
                                html.P(f"Patient ID: {patient_id}"),
                                html.P(f"Age: {age} • Gender: {gender}", className="text-muted"),
                                html.P(f"Last Visit: {last_visit}", className="text-muted")
                            ], width=8),
                            dbc.Col([
                                dbc.Button("View Profile", color="primary", className="me-2"),
                                dbc.Button("Message", color="success")
                            ], className="text-end")
                        ])
                    ])
                ], className="mb-4 shadow-sm"),

                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Heart Disease Risk"),
                            dbc.CardBody([
                                dbc.Progress(value=heart_risk * 100, color=heart_bar_color, striped=True, animated=True),
                                html.P(f"Risk Score: {int(heart_risk * 100)}% ({heart_label})", className="mt-2"),
                                html.Small("Factors: High BP, Cholesterol", className="text-muted")
                            ])
                        ], className="shadow-sm")
                    ], width=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Diabetes Risk"),
                            dbc.CardBody([
                                dbc.Progress(value=diabetes_risk * 100, color=diabetes_bar_color, striped=True, animated=True),
                                html.P(f"Risk Score: {int(diabetes_risk * 100)}% ({diabetes_label})", className="mt-2"),
                                html.Small("Factors: Glucose, BMI", className="text-muted")
                            ])
                        ], className="shadow-sm")
                    ], width=6)
                ], className="mb-4"),

                dbc.Card([
                    dbc.CardHeader("Risk Score History"),
                    dbc.CardBody([
                        dcc.Graph(figure=fig)
                    ])
                ], className="shadow-sm")
            ])
        except Exception as e:
            return dbc.Alert(f"❌ Error loading data: {str(e)}", color="danger")
        


