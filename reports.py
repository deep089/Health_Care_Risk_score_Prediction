import dash
from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import sqlite3

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])
server = app.server

# Load data
conn = sqlite3.connect("healthcare.db")
patients_df = pd.read_sql("SELECT * FROM Patients", conn)
vitals_df = pd.read_sql("SELECT * FROM Vitals", conn)
risk_df = pd.read_sql("SELECT * FROM RiskScores", conn)
conn.close()

# Age calculation
patients_df["age"] = pd.to_datetime("today").year - pd.to_datetime(patients_df["date_of_birth"]).dt.year

# Merge data
merged_df = pd.merge(pd.merge(risk_df, patients_df, on="patient_id"), vitals_df, on="patient_id")

# Layout
app.layout = dbc.Container([
    html.H2("📊 Health Overview Report", className="text-center my-4 text-primary"),

    html.P(
        "This dashboard presents a high-level overview of patient demographics and risk score distributions. "
        "It highlights key health indicators including age distribution, gender split, and risk assessments for heart disease and diabetes.",
        className="lead text-center mb-4"
    ),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Gender Distribution"),
            dbc.CardBody([
                dcc.Graph(id="gender-chart"),
                html.Small("This chart shows the gender breakdown of all patients.", className="text-muted")
            ])
        ])),
        dbc.Col(dbc.Card([
            dbc.CardHeader("Age Distribution"),
            dbc.CardBody([
                dcc.Graph(id="age-chart"),
                html.Small("This histogram shows how patients are distributed across different age groups.", className="text-muted")
            ])
        ]))
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Heart Disease Risk Score Distribution"),
            dbc.CardBody([
                dcc.Graph(id="heart-chart"),
                html.Small("This chart illustrates the distribution of heart disease risk scores across all patients.", className="text-muted")
            ])
        ])),
        dbc.Col(dbc.Card([
            dbc.CardHeader("Diabetes Risk Score Distribution"),
            dbc.CardBody([
                dcc.Graph(id="diabetes-chart"),
                html.Small("This chart illustrates the distribution of diabetes risk scores across all patients.", className="text-muted")
            ])
        ]))
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Top High-Risk Patients"),
            dbc.CardBody([
                html.Div(id="high-risk-table"),
                html.Small("This table highlights patients with a high risk score (above 0.8) for heart disease or diabetes.", className="text-muted")
            ])
        ]))
    ]),

    dcc.Interval(id="refresh", interval=60000, n_intervals=0)
], fluid=True)


@app.callback(
    Output("gender-chart", "figure"),
    Output("age-chart", "figure"),
    Output("heart-chart", "figure"),
    Output("diabetes-chart", "figure"),
    Output("high-risk-table", "children"),
    Input("refresh", "n_intervals")
)
def update_report(_):
    gender_fig = px.pie(
        patients_df, names="gender", title="", hole=0.3
    ).update_traces(textinfo='percent+label').update_layout(
        margin=dict(t=30, b=0), showlegend=True
    )

    age_fig = px.histogram(
        patients_df, x="age", nbins=20
    ).update_layout(
        xaxis_title="Age", yaxis_title="Number of Patients", margin=dict(t=10)
    )

    heart_fig = px.histogram(
        risk_df, x="heart_disease_risk", nbins=20
    ).update_layout(
        xaxis_title="Heart Disease Risk Score", yaxis_title="Number of Patients", margin=dict(t=10)
    )

    diabetes_fig = px.histogram(
        risk_df, x="diabetes_risk", nbins=20
    ).update_layout(
        xaxis_title="Diabetes Risk Score", yaxis_title="Number of Patients", margin=dict(t=10)
    )

    high_risk = risk_df[(risk_df['heart_disease_risk'] > 0.8) | (risk_df['diabetes_risk'] > 0.8)]
    top_patients = pd.merge(high_risk, patients_df, on="patient_id")

    table = dbc.Table.from_dataframe(
        top_patients[['patient_id', 'first_name', 'last_name', 'heart_disease_risk', 'diabetes_risk']].head(10),
        striped=True, bordered=True, hover=True, responsive=True, class_name="mt-3"
    )

    return gender_fig, age_fig, heart_fig, diabetes_fig, table


if __name__ == '__main__':
    app.run(debug=True, port=8055)
