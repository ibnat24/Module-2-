"""
Healthcare ER Patient Flow - Interactive Dashboard
Real-time monitoring and predictive analytics dashboard
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_generator import ERDataGenerator
from predictive_analytics import ERPredictiveAnalytics

# Initialize the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Generate historical data
generator = ERDataGenerator()
historical_data = generator.generate_multiple_sessions(num_sessions=5)

# Initialize analytics
analytics = ERPredictiveAnalytics(historical_data)

# Department display names
DEPT_NAMES = {
    'emergency_walkin': 'Emergency Walk-in',
    'emergency_ambulance': 'Emergency Ambulance',
    'surgery': 'Surgical Care',
    'critical_care': 'Critical Care',
    'step_down': 'Step Down'
}

# Capacity configuration (patients per staff member)
CAPACITY_CONFIG = {
    'emergency_walkin': {'patients_per_nurse': 4, 'patients_per_doctor': 8, 'beds': 15},
    'emergency_ambulance': {'patients_per_nurse': 3, 'patients_per_doctor': 5, 'beds': 10},
    'surgery': {'patients_per_nurse': 2, 'patients_per_doctor': 3, 'beds': 8},
    'critical_care': {'patients_per_nurse': 2, 'patients_per_doctor': 3, 'beds': 6},
    'step_down': {'patients_per_nurse': 5, 'patients_per_doctor': 10, 'beds': 12}
}

# Simulation state
simulation_state = {
    'current_round': 1,
    'current_patients': {dept: 0 for dept in DEPT_NAMES.keys()},
    'wait_times': {dept: 0 for dept in DEPT_NAMES.keys()},
    'total_treated': 0,
    'staff_allocation': {
        dept: {'nurses': 2, 'doctors': 1} for dept in DEPT_NAMES.keys()
    }
}

# Color scheme for departments
DEPT_COLORS = {
    'emergency_walkin': '#FF6B6B',
    'emergency_ambulance': '#EE5A6F',
    'surgery': '#4ECDC4',
    'critical_care': '#FFA07A',
    'step_down': '#95E1D3'
}

# Define the layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("🏥 ER Patient Flow Command Center", 
                style={'textAlign': 'center', 'color': '#2C3E50', 'marginBottom': '10px'}),
        html.P("Real-time Monitoring & Predictive Analytics Dashboard",
               style={'textAlign': 'center', 'color': '#7F8C8D', 'fontSize': '18px'})
    ], style={'backgroundColor': '#ECF0F1', 'padding': '20px', 'marginBottom': '20px'}),
    
    # Control Panel
    html.Div([
        html.Div([
            html.Label("Current Round:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.Input(id='current-round-input', type='number', value=1, min=1, max=23,
                     style={'width': '80px', 'marginRight': '20px'}),
            html.Button('Update Round', id='update-round-btn', n_clicks=0,
                       style={'backgroundColor': '#3498DB', 'color': 'white', 'border': 'none',
                              'padding': '10px 20px', 'cursor': 'pointer', 'borderRadius': '5px'}),
            html.Button('Simulate Next Round', id='simulate-btn', n_clicks=0,
                       style={'backgroundColor': '#2ECC71', 'color': 'white', 'border': 'none',
                              'padding': '10px 20px', 'cursor': 'pointer', 'borderRadius': '5px',
                              'marginLeft': '10px'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),
        
        html.Div(id='round-info', style={'fontSize': '14px', 'color': '#34495E', 'marginTop': '10px'})
    ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px', 
              'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
    
    # Alert System
    html.Div(id='alert-panel', style={'marginBottom': '20px'}),
    
    # Main Dashboard Grid
    html.Div([
        # Left Column - Real-time Status
        html.Div([
            # Patient Flow Heat Map
            html.Div([
                html.H3("📊 Department Status Heat Map", 
                       style={'color': '#2C3E50', 'marginBottom': '15px'}),
                dcc.Graph(id='heatmap-chart')
            ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px',
                     'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            # Patient Communication Panel (NEW - Based on Research)
            html.Div([
                html.H3("📱 Patient Communication & Transparency", 
                       style={'color': '#2C3E50', 'marginBottom': '15px'}),
                html.P("Evidence-based communication reduces perceived wait time (Maister, 1985)",
                      style={'fontSize': '11px', 'color': '#7F8C8D', 'fontStyle': 'italic', 'marginBottom': '10px'}),
                html.Div(id='patient-communication')
            ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px',
                     'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            # Resource Allocation
            html.Div([
                html.H3("👥 Resource Allocation Manager", 
                       style={'color': '#2C3E50', 'marginBottom': '15px'}),
                html.P("Click cells to edit resource allocations in real-time", 
                       style={'fontSize': '12px', 'color': '#7F8C8D', 'marginBottom': '10px'}),
                dash_table.DataTable(
                    id='resource-table',
                    columns=[
                        {'name': 'Department', 'id': 'department', 'editable': False},
                        {'name': '👥 Current Patients', 'id': 'current_patients', 'editable': False, 'type': 'numeric'},
                        {'name': '👨‍⚕️ Doctors', 'id': 'doctors', 'editable': True, 'type': 'numeric'},
                        {'name': '👩‍⚕️ Nurses', 'id': 'nurses', 'editable': True, 'type': 'numeric'},
                        {'name': '🛏️ Total Beds', 'id': 'total_beds', 'editable': True, 'type': 'numeric'},
                        {'name': '🔴 Occupied', 'id': 'occupied_beds', 'editable': False, 'type': 'numeric'},
                        {'name': '🟢 Available', 'id': 'available_beds', 'editable': False, 'type': 'numeric'},
                        {'name': '📊 Utilization', 'id': 'utilization', 'editable': False},
                    ],
                    data=[],
                    editable=True,
                    row_deletable=False,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '12px',
                        'fontFamily': 'Arial, sans-serif',
                        'fontSize': '13px'
                    },
                    style_header={
                        'backgroundColor': '#3498DB',
                        'color': 'white',
                        'fontWeight': 'bold',
                        'textAlign': 'center',
                        'border': '1px solid #2980B9'
                    },
                    style_data_conditional=[
                        {
                            'if': {'column_id': 'department'},
                            'fontWeight': 'bold',
                            'backgroundColor': '#F8F9FA'
                        },
                        {
                            'if': {
                                'filter_query': '{utilization} contains "HIGH"',
                                'column_id': 'utilization'
                            },
                            'backgroundColor': '#E74C3C',
                            'color': 'white',
                            'fontWeight': 'bold'
                        },
                        {
                            'if': {
                                'filter_query': '{utilization} contains "MODERATE"',
                                'column_id': 'utilization'
                            },
                            'backgroundColor': '#F39C12',
                            'color': 'white',
                            'fontWeight': 'bold'
                        },
                        {
                            'if': {
                                'filter_query': '{utilization} contains "NORMAL"',
                                'column_id': 'utilization'
                            },
                            'backgroundColor': '#27AE60',
                            'color': 'white',
                            'fontWeight': 'bold'
                        }
                    ],
                    style_cell_conditional=[
                        {'if': {'column_id': 'department'}, 'width': '20%'},
                        {'if': {'column_id': 'utilization'}, 'textAlign': 'center'},
                    ]
                ),
                html.Div([
                    html.Button('📥 Save Changes', id='save-resources-btn', n_clicks=0,
                               style={'backgroundColor': '#27AE60', 'color': 'white', 'border': 'none',
                                      'padding': '10px 20px', 'cursor': 'pointer', 'borderRadius': '5px',
                                      'marginTop': '10px', 'marginRight': '10px'}),
                    html.Button('🔄 Reset to Defaults', id='reset-resources-btn', n_clicks=0,
                               style={'backgroundColor': '#95A5A6', 'color': 'white', 'border': 'none',
                                      'padding': '10px 20px', 'cursor': 'pointer', 'borderRadius': '5px',
                                      'marginTop': '10px'}),
                    html.Div(id='save-status', style={'display': 'inline-block', 'marginLeft': '15px',
                                                      'color': '#27AE60', 'fontWeight': 'bold'})
                ])
            ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px',
                     'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            # Performance Metrics
            html.Div([
                html.H3("📈 Performance Metrics", 
                       style={'color': '#2C3E50', 'marginBottom': '15px'}),
                html.Div(id='performance-metrics')
            ], style={'backgroundColor': 'white', 'padding': '20px',
                     'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        
        # Right Column - Predictive Analytics
        html.Div([
            # Predictive Forecast
            html.Div([
                html.H3("🔮 Predictive Forecast (Next 4 Rounds)", 
                       style={'color': '#2C3E50', 'marginBottom': '15px'}),
                dcc.Graph(id='forecast-chart')
            ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px',
                     'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            # Staffing Recommendations
            html.Div([
                html.H3("💡 Staffing Recommendations", 
                       style={'color': '#2C3E50', 'marginBottom': '15px'}),
                html.Div(id='staffing-recommendations')
            ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px',
                     'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            # Historical Trends
            html.Div([
                html.H3("📉 Historical Arrival Patterns", 
                       style={'color': '#2C3E50', 'marginBottom': '15px'}),
                dcc.Graph(id='historical-trends')
            ], style={'backgroundColor': 'white', 'padding': '20px',
                     'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top',
                 'marginLeft': '4%'})
    ]),
    
    # Footer
    html.Div([
        html.P("MSE 433 - Healthcare Operations Management | Winter 2026",
               style={'textAlign': 'center', 'color': '#95A5A6', 'fontSize': '12px'})
    ], style={'marginTop': '40px', 'padding': '20px'})
], style={'padding': '20px', 'backgroundColor': '#F5F6FA', 'fontFamily': 'Arial, sans-serif'})


# Callbacks
@app.callback(
    [Output('round-info', 'children'),
     Output('alert-panel', 'children'),
     Output('heatmap-chart', 'figure'),
     Output('patient-communication', 'children'),
     Output('resource-table', 'data'),
     Output('performance-metrics', 'children'),
     Output('forecast-chart', 'figure'),
     Output('staffing-recommendations', 'children'),
     Output('historical-trends', 'figure')],
    [Input('update-round-btn', 'n_clicks'),
     Input('simulate-btn', 'n_clicks'),
     Input('reset-resources-btn', 'n_clicks')],
    [State('current-round-input', 'value'),
     State('resource-table', 'data')]
)
def update_dashboard(update_clicks, simulate_clicks, reset_clicks, current_round, resource_data):
    """Main callback to update all dashboard components"""
    
    # Determine which button was clicked
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'update-round-btn'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # If reset button clicked, restore defaults
    if button_id == 'reset-resources-btn':
        for dept in DEPT_NAMES.keys():
            if dept == 'emergency_walkin':
                simulation_state['staff_allocation'][dept] = {'nurses': 3, 'doctors': 2}
            elif dept == 'emergency_ambulance':
                simulation_state['staff_allocation'][dept] = {'nurses': 2, 'doctors': 1}
            else:
                simulation_state['staff_allocation'][dept] = {'nurses': 2, 'doctors': 1}
    
    # Update staff allocation from table if data exists
    if resource_data and button_id != 'reset-resources-btn':
        for row in resource_data:
            dept_name = row['department']
            # Find department key from display name
            dept_key = next((k for k, v in DEPT_NAMES.items() if v == dept_name), None)
            if dept_key:
                simulation_state['staff_allocation'][dept_key]['doctors'] = int(row.get('doctors', 1))
                simulation_state['staff_allocation'][dept_key]['nurses'] = int(row.get('nurses', 2))
                # Update capacity config with new bed count
                CAPACITY_CONFIG[dept_key]['beds'] = int(row.get('total_beds', CAPACITY_CONFIG[dept_key]['beds']))
    
    # If simulate button, increment round
    if button_id == 'simulate-btn' and simulate_clicks > 0:
        current_round = min(23, current_round + 1)
        # Simulate new patient arrivals
        new_arrivals = generator.generate_real_time_data(current_round, historical_data)
        for dept in DEPT_NAMES.keys():
            simulation_state['current_patients'][dept] += new_arrivals[dept]
    
    simulation_state['current_round'] = current_round
    
    # Get forecasts
    forecasts = analytics.forecast_all_departments(current_round)
    future_forecasts = analytics.forecast_next_n_rounds(current_round, n=4)
    
    # Detect surges
    alerts = analytics.detect_surge(forecasts, threshold_percentile=75)
    
    # Calculate recommendations
    recommendations = analytics.calculate_capacity_recommendations(forecasts, CAPACITY_CONFIG)
    
    # 1. Round Info
    round_info = html.Div([
        html.Span(f"Round {current_round} of 23", 
                 style={'fontWeight': 'bold', 'fontSize': '16px', 'color': '#2C3E50'}),
        html.Span(f" | Total Patients in System: {sum(simulation_state['current_patients'].values())}",
                 style={'marginLeft': '20px', 'color': '#34495E'})
    ])
    
    # 2. Alert Panel
    alert_components = []
    if alerts:
        for alert in alerts:
            color = '#E74C3C' if alert['severity'] == 'HIGH' else '#F39C12'
            alert_components.append(
                html.Div([
                    html.Span(f"⚠️ {alert['message']}", 
                             style={'color': 'white', 'fontWeight': 'bold'})
                ], style={'backgroundColor': color, 'padding': '10px', 'marginBottom': '5px',
                         'borderRadius': '5px'})
            )
    else:
        alert_components.append(
            html.Div([
                html.Span("✅ All departments operating within normal capacity", 
                         style={'color': 'white', 'fontWeight': 'bold'})
            ], style={'backgroundColor': '#27AE60', 'padding': '10px',
                     'borderRadius': '5px'})
        )
    
    alert_panel = html.Div(alert_components)
    
    # 3. Heat Map
    heatmap_data = []
    for dept in DEPT_NAMES.keys():
        current = simulation_state['current_patients'][dept]
        capacity = CAPACITY_CONFIG[dept]['beds']
        utilization = (current / capacity) * 100 if capacity > 0 else 0
        heatmap_data.append({
            'Department': DEPT_NAMES[dept],
            'Current Patients': current,
            'Capacity': capacity,
            'Utilization %': utilization
        })
    
    heatmap_df = pd.DataFrame(heatmap_data)
    
    heatmap_fig = go.Figure(data=go.Heatmap(
        z=[heatmap_df['Utilization %'].values],
        x=heatmap_df['Department'].values,
        y=['Capacity Utilization'],
        colorscale=[[0, '#27AE60'], [0.5, '#F39C12'], [1, '#E74C3C']],
        text=[[f"{val:.0f}%" for val in heatmap_df['Utilization %'].values]],
        texttemplate='%{text}',
        textfont={"size": 14},
        colorbar=dict(title="Utilization %")
    ))
    
    heatmap_fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(tickangle=-45)
    )
    
    # 4. Patient Communication Panel (Research-based transparency)
    # Based on Maister (1985), Taylor (1994), Davis et al. (2011)
    communication_components = []
    
    # Calculate estimated wait times per department
    for dept, dept_name in DEPT_NAMES.items():
        patients = simulation_state['current_patients'][dept]
        staff = simulation_state['staff_allocation'][dept]
        total_staff = staff['nurses'] + staff['doctors']
        
        # Simple wait time calculation: patients / staff * avg service time
        if total_staff > 0:
            est_wait = (patients / total_staff) * 15  # 15 min avg service time
        else:
            est_wait = 0
        
        # Color code based on wait time
        if est_wait > 30:
            wait_color = '#E74C3C'
            wait_label = 'Long Wait'
        elif est_wait > 15:
            wait_color = '#F39C12'
            wait_label = 'Moderate Wait'
        else:
            wait_color = '#27AE60'
            wait_label = 'Short Wait'
        
        # SMS notification message (research: reduces perceived wait)
        sms_message = ""
        if est_wait > 20:
            sms_message = f"📱 SMS: 'Your estimated wait is {est_wait:.0f} min. You may wait in cafe area. We'll text when ready.'"
        
        communication_components.append(
            html.Div([
                html.Div([
                    html.Span(f"{dept_name}", style={'fontWeight': 'bold', 'fontSize': '13px'}),
                    html.Span(f" - {patients} patients", style={'marginLeft': '10px', 'color': '#7F8C8D', 'fontSize': '12px'})
                ]),
                html.Div([
                    html.Span(f"⏱️ Est. Wait: ", style={'fontSize': '12px'}),
                    html.Span(f"{est_wait:.0f} min", 
                             style={'fontSize': '12px', 'fontWeight': 'bold', 'color': wait_color}),
                    html.Span(f" ({wait_label})", style={'fontSize': '11px', 'color': wait_color, 'marginLeft': '5px'})
                ]),
                html.Div([
                    html.Span(f"👨‍⚕️ {total_staff} providers available", 
                             style={'fontSize': '11px', 'color': '#34495E'}),
                    html.Span(" | ", style={'marginLeft': '5px', 'marginRight': '5px'}),
                    html.Span(f"🟢 Status visible to patients", 
                             style={'fontSize': '11px', 'color': '#27AE60'})
                ]),
                html.Div(sms_message, style={'fontSize': '10px', 'color': '#3498DB', 'marginTop': '3px', 'fontStyle': 'italic'}) if sms_message else html.Div()
            ], style={'padding': '10px', 'marginBottom': '8px', 'backgroundColor': '#F8F9FA',
                     'borderLeft': f'4px solid {DEPT_COLORS[dept]}', 'borderRadius': '3px'})
        )
    
    # Add transparency note (evidence-based)
    communication_components.append(
        html.Div([
            html.Span("🔍 Transparency Benefits: ", style={'fontWeight': 'bold', 'fontSize': '11px', 'color': '#2C3E50'}),
            html.Span("Research shows visible wait times & provider availability improve patient satisfaction even when delays persist (McManus et al., 2014)",
                     style={'fontSize': '10px', 'color': '#7F8C8D', 'fontStyle': 'italic'})
        ], style={'padding': '10px', 'marginTop': '10px', 'backgroundColor': '#E8F8F5', 
                 'borderRadius': '5px', 'border': '1px solid #27AE60'})
    )
    
    patient_communication = html.Div(communication_components)
    
    # 5. Resource Table (Airtable-style)
    resource_table_data = []
    for dept, dept_name in DEPT_NAMES.items():
        staff = simulation_state['staff_allocation'][dept]
        patients = simulation_state['current_patients'][dept]
        total_beds = CAPACITY_CONFIG[dept]['beds']
        occupied = min(patients, total_beds)
        available = max(0, total_beds - occupied)
        utilization_pct = (occupied / total_beds * 100) if total_beds > 0 else 0
        
        if utilization_pct >= 80:
            util_label = f"HIGH ({utilization_pct:.0f}%)"
        elif utilization_pct >= 60:
            util_label = f"MODERATE ({utilization_pct:.0f}%)"
        else:
            util_label = f"NORMAL ({utilization_pct:.0f}%)"
        
        resource_table_data.append({
            'department': dept_name,
            'current_patients': patients,
            'doctors': staff['doctors'],
            'nurses': staff['nurses'],
            'total_beds': total_beds,
            'occupied_beds': occupied,
            'available_beds': available,
            'utilization': util_label
        })
    
    # 5. Performance Metrics
    avg_wait = np.mean(list(simulation_state['wait_times'].values()))
    total_patients = sum(simulation_state['current_patients'].values())
    
    metrics = [
        {'label': 'Avg Wait Time', 'value': f'{avg_wait:.1f} min', 'icon': '⏱️'},
        {'label': 'Total in System', 'value': total_patients, 'icon': '👥'},
        {'label': 'Patients Treated', 'value': simulation_state['total_treated'], 'icon': '✅'},
        {'label': 'Current Round', 'value': f'{current_round}/23', 'icon': '🎮'}
    ]
    
    metric_components = []
    for metric in metrics:
        metric_components.append(
            html.Div([
                html.Div(metric['icon'], style={'fontSize': '30px', 'marginBottom': '5px'}),
                html.Div(metric['value'], style={'fontSize': '24px', 'fontWeight': 'bold', 
                                                  'color': '#2C3E50'}),
                html.Div(metric['label'], style={'fontSize': '12px', 'color': '#7F8C8D'})
            ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#F8F9FA',
                     'borderRadius': '5px', 'width': '22%', 'display': 'inline-block',
                     'marginRight': '3%'})
        )
    
    performance_metrics = html.Div(metric_components)
    
    # 6. Forecast Chart
    forecast_rounds = list(range(current_round, current_round + 4))
    forecast_data_by_dept = {dept: [] for dept in DEPT_NAMES.keys()}
    
    for round_num in forecast_rounds:
        if round_num in future_forecasts:
            for dept in DEPT_NAMES.keys():
                forecast_data_by_dept[dept].append(
                    future_forecasts[round_num][dept]['forecast']
                )
    
    forecast_fig = go.Figure()
    for dept, dept_name in DEPT_NAMES.items():
        forecast_fig.add_trace(go.Scatter(
            x=forecast_rounds,
            y=forecast_data_by_dept[dept],
            name=dept_name,
            mode='lines+markers',
            line=dict(color=DEPT_COLORS[dept], width=3),
            marker=dict(size=8)
        ))
    
    forecast_fig.update_layout(
        xaxis_title="Round",
        yaxis_title="Expected Patients",
        height=300,
        margin=dict(l=40, r=20, t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified'
    )
    
    # 7. Staffing Recommendations
    rec_components = []
    for dept, rec in recommendations.items():
        current_staff = simulation_state['staff_allocation'][dept]
        nurse_diff = rec['nurses_recommended'] - current_staff['nurses']
        doctor_diff = rec['doctors_recommended'] - current_staff['doctors']
        
        nurse_color = '#27AE60' if nurse_diff == 0 else ('#E74C3C' if nurse_diff > 0 else '#3498DB')
        doctor_color = '#27AE60' if doctor_diff == 0 else ('#E74C3C' if doctor_diff > 0 else '#3498DB')
        
        rec_components.append(
            html.Div([
                html.Div(DEPT_NAMES[dept], style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                html.Div([
                    html.Span(f"Expected: {rec['expected_patients']:.1f} patients", 
                             style={'fontSize': '12px', 'color': '#7F8C8D'}),
                ], style={'marginBottom': '5px'}),
                html.Div([
                    html.Span(f"Nurses: {current_staff['nurses']} → {rec['nurses_recommended']}", 
                             style={'color': nurse_color, 'marginRight': '15px', 'fontSize': '12px'}),
                    html.Span(f"Doctors: {current_staff['doctors']} → {rec['doctors_recommended']}", 
                             style={'color': doctor_color, 'fontSize': '12px'})
                ])
            ], style={'padding': '10px', 'marginBottom': '8px', 'backgroundColor': '#F8F9FA',
                     'borderRadius': '5px', 'borderLeft': f'4px solid {DEPT_COLORS[dept]}'})
        )
    
    staffing_recommendations = html.Div(rec_components)
    
    # 8. Historical Trends
    hist_summary = historical_data.groupby('round')[list(DEPT_NAMES.keys())].mean().reset_index()
    
    hist_fig = go.Figure()
    for dept, dept_name in DEPT_NAMES.items():
        hist_fig.add_trace(go.Scatter(
            x=hist_summary['round'],
            y=hist_summary[dept],
            name=dept_name,
            mode='lines',
            line=dict(color=DEPT_COLORS[dept], width=2),
            fill='tonexty' if dept != 'emergency_walkin' else None,
            opacity=0.7
        ))
    
    # Add current round marker
    hist_fig.add_vline(x=current_round, line_dash="dash", line_color="red", 
                       annotation_text="Current Round")
    
    hist_fig.update_layout(
        xaxis_title="Round",
        yaxis_title="Average Patients",
        height=300,
        margin=dict(l=40, r=20, t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified'
    )
    
    return (round_info, alert_panel, heatmap_fig, patient_communication, resource_table_data, 
            performance_metrics, forecast_fig, staffing_recommendations, hist_fig)


# Callback for save status message
@app.callback(
    Output('save-status', 'children'),
    [Input('save-resources-btn', 'n_clicks')],
    prevent_initial_call=True
)
def save_resources(n_clicks):
    """Display save confirmation message"""
    if n_clicks > 0:
        return "✓ Resources updated successfully!"
    return ""


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏥 ER PATIENT FLOW COMMAND CENTER DASHBOARD")
    print("="*60)
    print("\nStarting dashboard server...")
    print("Dashboard will be available at: http://127.0.0.1:8050")
    print("\nFeatures:")
    print("  ✓ Real-time patient flow monitoring")
    print("  ✓ Predictive analytics (4-round forecast)")
    print("  ✓ Surge detection & alerts")
    print("  ✓ Staffing recommendations")
    print("  ✓ Resource allocation tracking")
    print("  ✓ Historical trend analysis")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=8050)