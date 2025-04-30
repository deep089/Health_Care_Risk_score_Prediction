# app.py

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import flask

# Import dashboards
from dashboard_doctor import doctor_dashboard_layout, register_doctor_callbacks
from dashboard_frontdesk import get_frontdesk_dashboard_layout, register_frontdesk_callbacks

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Dummy User Database (can later connect to real DB)
users = {
    "doctor1@example.com": {"password": "doctorpass", "role": "doctor", "name": "Dr. John Doe"},
    "patient1@example.com": {"password": "patientpass", "role": "patient", "name": "Alice Smith"},
    "nurse1@example.com": {"password": "nursepass", "role": "nurse", "name": "Nurse Nancy"},
    "admin1@example.com": {"password": "adminpass", "role": "admin", "name": "Admin Bob"},
    "frontdesk1@example.com": {"password": "frontdeskpass", "role": "frontdesk", "name": "Frontdesk Charlie"}
}

# Layout Definitions
login_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("Healthcare System Login", className="text-center my-4"),
            dbc.Input(id="login-email", placeholder="Email", type="email", className="mb-3"),
            dbc.Input(id="login-password", placeholder="Password", type="password", className="mb-3"),
            dbc.Button("Login", id="login-button", color="primary", className="w-100"),
            html.Div(id="login-alert", className="text-danger mt-3")
        ], width=4)
    ], justify="center", align="center", style={"minHeight": "100vh"})
], fluid=True)

# Placeholder Layouts (for roles not yet implemented)
patient_dashboard_layout = html.Div([
    html.H1("🧑‍⚕️ Patient Dashboard"),
    html.P("Coming Soon...")
], style={"textAlign": "center", "marginTop": "100px"})

nurse_dashboard_layout = html.Div([
    html.H1("💉 Nurse Dashboard"),
    html.P("Coming Soon...")
], style={"textAlign": "center", "marginTop": "100px"})

admin_dashboard_layout = html.Div([
    html.H1("🛡️ Admin Dashboard"),
    html.P("Coming Soon...")
], style={"textAlign": "center", "marginTop": "100px"})

# Import frontdesk dashboard layout
frontdesk_dashboard_layout = get_frontdesk_dashboard_layout()

# App Layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='current_user', storage_type='session'),  # Session store for logged-in user
    html.Div(id='page-content')
])

# Routing Logic (Page Display)
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    State('current_user', 'data')
)
def display_page(pathname, current_user):
    if pathname == '/':
        return login_layout
    if not current_user:
        return html.H1("❌ Unauthorized Access. Please login.", style={"textAlign": "center", "marginTop": "100px"})

    role = current_user.get('role')

    if pathname == '/doctor_dashboard' and role == 'doctor':
        return doctor_dashboard_layout
    elif pathname == '/patient_dashboard' and role == 'patient':
        return patient_dashboard_layout
    elif pathname == '/nurse_dashboard' and role == 'nurse':
        return nurse_dashboard_layout
    elif pathname == '/admin_dashboard' and role == 'admin':
        return admin_dashboard_layout
    elif pathname == '/frontdesk_dashboard' and role == 'frontdesk':
        return frontdesk_dashboard_layout
    else:
        return html.H1("❌ Access Denied. You are not authorized to view this page.", style={"textAlign": "center", "marginTop": "100px"})

# Login Authentication
@app.callback(
    Output('current_user', 'data'),
    Output('url', 'pathname'),
    Output('login-alert', 'children'),
    Input('login-button', 'n_clicks'),
    State('login-email', 'value'),
    State('login-password', 'value'),
    prevent_initial_call=True
)
def login_user(n_clicks, email, password):
    user = users.get(email)
    if user and user['password'] == password:
        # Successful login
        role = user['role']
        if role == 'doctor':
            return user, '/doctor_dashboard', ""
        elif role == 'patient':
            return user, '/patient_dashboard', ""
        elif role == 'nurse':
            return user, '/nurse_dashboard', ""
        elif role == 'admin':
            return user, '/admin_dashboard', ""
        elif role == 'frontdesk':
            return user, '/frontdesk_dashboard', ""
    # Failed login
    return dash.no_update, dash.no_update, "Invalid email or password."

# Register External Dashboard Callbacks
register_doctor_callbacks(app)
register_frontdesk_callbacks(app)

# Run Server
if __name__ == '__main__':
    app.run(debug=True, port=8050)
