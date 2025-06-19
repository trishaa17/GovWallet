import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table, State
import requests
from io import StringIO
from datetime import datetime, date
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify


def create_dash_entries(server):
    # Load the Excel file
    df = pd.read_excel("C:/Users/User/OneDrive - WORLD AQUATICS CHAMPIONSHIPS SINGAPORE PTE. LTD/Desktop/sportsg-swc-2024_attendance_report_20241101T105358+01Nov24.xlsx", sheet_name= "Sheet1")
    
    # Filter for attendance-assisted-exit records
    df = df[df['How'] == 'attendance-assisted-exit']
    
    # Convert When column to datetime with explicit format handling
    df['When'] = pd.to_datetime(df['When'], format='mixed', errors='coerce')
    df['date'] = df['When'].dt.date
    
    # Extract first and last names from the Who column
    # Assuming the Who column contains names that can be split
    df['name_parts'] = df['Who'].astype(str).str.split()
    df['first_name'] = df['name_parts'].apply(lambda x: x[0] if len(x) > 0 else '')
    df['last_name'] = df['name_parts'].apply(lambda x: x[-1] if len(x) > 1 else '')
    df['full_name'] = df['first_name'] + ' ' + df['last_name']
    df['full_name'] = df['full_name'].str.strip()  # Remove extra spaces
    
    # Get date range for filters
    min_date = df['date'].min()
    max_date = df['date'].max()
    
    app = Dash(__name__, server=server, routes_pathname_prefix='/appEntries/', external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.title = "SportSG SWC 2024 Attendance Dashboard"

    # Updated background style with no gaps
    background_style = {
        'margin': '0',
        'padding': '0',
        'backgroundSize': 'cover',
        'backgroundImage': 'url("https://images.unsplash.com/photo-1454117096348-e4abbeba002c?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")',
        'minHeight': '100vh',
        'backgroundRepeat': 'no-repeat',
        'backgroundAttachment': 'fixed',
        'backgroundPosition': 'center center'
    }
    
    # Content wrapper style for consistent spacing
    content_wrapper_style = {
        'margin': '0',
        'padding': '20px',
        'minHeight': '100vh'
    }
    
    app.layout = html.Div([
        dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H2("SportSG SWC 2024 Attendance Dashboard", 
                           className="text-center mb-4", 
                           style={
                            'color': 'Black', 'textAlign': 'center',
                            'fontSize': '2.5rem', 'fontWeight': 'bold',
                            'marginBottom': '30px', 'fontFamily': 'Arial, sans-serif'
                })
                ])
            ], className="mb-0"),  # Remove bottom margin
            
            # Summary Statistics - with no top margin
            dbc.Row(id='summary-stats', className="mb-4 mt-0"),
            
            # Main Filters - Collapsible
            
            # Charts Row - No top margin
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                                    html.Div([
                html.Div([
                    html.H5("Daily Attendance Entries"),
                    html.Button([
                        DashIconify(icon="carbon:filter", width=20, style={'marginRight': '8px'}),
                        "Graph Filters"
                    ],
                    id='collapse-button',
                    n_clicks=0,
                    style={
                        'border': '1px solid #3498db',
                        'borderRadius': '8px',
                        'padding': '8px 16px',
                        'backgroundColor': '#3498db',
                        'color': 'white',
                        'cursor': 'pointer',
                        'fontSize': '14px',
                        'fontWeight': '500',
                        'display': 'flex',
                        'alignItems': 'center'
                    })
                ], style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'space-between',
                    'marginBottom': '10px',  # Reduced margin
                    'padding': '15px',
                    'backgroundColor': 'rgba(248, 249, 250, 1)',  # Semi-transparent
                    'borderRadius': '8px'
                }),
                
                dbc.Collapse([
                    dbc.Card([
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Date Range", className="fw-bold mb-2"),
                                    dcc.DatePickerRange(
                                        id='date-range-picker',
                                        start_date=min_date,
                                        end_date=max_date,
                                        display_format='DD/MM/YYYY',
                                        style={'width': '100%'}
                                    )
                                ], width=4),
                                
                                dbc.Col([
                                    html.Label("Location", className="fw-bold mb-2"),
                                    dcc.Dropdown(
                                        id='location-dropdown',
                                        options=[{'label': loc, 'value': loc} for loc in sorted(df['Where'].unique())],
                                        value=df['Where'].unique().tolist(),
                                        multi=True,
                                        placeholder="Select locations...",
                                        className="mb-0"
                                    )
                                ], width=4),
                                
                                dbc.Col([
                                    html.Label("Category", className="fw-bold mb-2"),
                                    dcc.Dropdown(
                                        id='category-dropdown',
                                        options=[{'label': cat, 'value': cat} for cat in sorted(df['Category'].unique())],
                                        value=df['Category'].unique().tolist(),
                                        multi=True,
                                        placeholder="Select categories...",
                                        className="mb-0"
                                    )
                                ], width=4)
                            ])
                        ])
                    ], style={'backgroundColor': 'rgba(248, 250, 252, 0.95)', 'border': '1px solid #e2e8f0'})
                ], id="collapse", is_open=False)
            ], className="mb-3"),  # Reduced bottom margin
                        dbc.CardBody([
                            dcc.Graph(id='attendance-chart')
                        ])
                    ], style={'border': '1px solid #e2e8f0', 'backgroundColor': 'rgba(255, 255, 255, 0.98)'})
                ], width=12)
            ], className="mb-4 mt-0"),  # No top margin, consistent bottom margin
            
            # Location Breakdown - No gaps
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.H5("Daily Entries by Location", style={'margin': '0', 'color': '#1f2937'}),
                            ], style={
                                'display': 'flex',
                                'alignItems': 'center',
                                'justifyContent': 'space-between',
                                'padding': '15px',
                                'backgroundColor': 'rgba(248, 249, 250, 0.9)',
                                'borderRadius': '8px'
                            })
                        ]),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Select Date", className="fw-bold mb-2"),
                                    dcc.Dropdown(
                                        id='date-selector',
                                        placeholder="Select a date...",
                                        className="mb-3"
                                    )
                                ], width=4)
                            ]),
                            dcc.Graph(id='location-breakdown-chart')
                        ])
                    ], style={'border': '1px solid #e2e8f0', 'backgroundColor': 'rgba(255, 255, 255, 0.98)'})
                ], width=12)
            ], className="mb-4 mt-0"),  # No top margin
            
            # Entries Table Section - Simplified, no gaps
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.H5("All Entries", style={'margin': '0', 'color': '#1f2937'}),
                                html.Button([
                                    DashIconify(icon="carbon:filter", width=20, style={'marginRight': '8px'}),
                                    "Table Filters"
                                ],
                                id='table-collapse-button',
                                n_clicks=0,
                                style={
                                    'border': '1px solid #3498db',
                                    'borderRadius': '8px',
                                    'padding': '8px 16px',
                                    'backgroundColor': '#3498db',
                                    'color': 'white',
                                    'cursor': 'pointer',
                                    'fontSize': '14px',
                                    'fontWeight': '500',
                                    'display': 'flex',
                                    'alignItems': 'center'
                                })
                            ], style={
                                'display': 'flex',
                                'alignItems': 'center',
                                'justifyContent': 'space-between',
                                'padding': '15px',
                                'backgroundColor': 'rgba(248, 249, 250, 1)',
                                'borderRadius': '8px'
                            })
                        ]),
                        dbc.CardBody([
                            # Collapsible Table Filters
                            dbc.Collapse([
                                dbc.Card([
                                    dbc.CardBody([
                                        dbc.Row([
                                            dbc.Col([
                                                html.Label("Filter by Date", className="fw-bold mb-2"),
                                                dcc.DatePickerSingle(
                                                    id='table-date-filter',
                                                    date=max_date,
                                                    display_format='DD/MM/YYYY',
                                                    placeholder="Select date..."
                                                )
                                            ], width=6),
                                            dbc.Col([
                                                html.Label("Filter by Name", className="fw-bold mb-2"),
                                                dcc.Input(
                                                    id='table-name-filter',
                                                    type='text',
                                                    placeholder="Enter name to search...",
                                                    className="form-control"
                                                )
                                            ], width=6)
                                        ])
                                    ])
                                ], style={'backgroundColor': 'rgba(248, 250, 252, 0.95)', 'border': '1px solid #e2e8f0'})
                            ], id="table-collapse", is_open=False, className="mb-3"),
                            
                            # Entry count info
                            html.Div(id='table-info', className="mb-3"),
                            
                            # Data table
                            html.Div(id='data-table')
                        ])
                    ], style={'border': '1px solid #e2e8f0', 'backgroundColor': 'rgba(255, 255, 255, 0.98)'})
                ], width=12)
            ], className="mt-0")  # No top margin for seamless connection
            
        ], style=content_wrapper_style, fluid=True)
    ], style=background_style)
    
    # Rest of your callbacks remain the same...
    # Callback for main filters collapse
    @app.callback(
        Output("collapse", "is_open"),
        [Input("collapse-button", "n_clicks")],
        [State("collapse", "is_open")],
    )
    def toggle_collapse(n, is_open):
        if n:
            return not is_open
        return is_open
    
    # Callback for table filters collapse
    @app.callback(
        Output("table-collapse", "is_open"),
        [Input("table-collapse-button", "n_clicks")],
        [State("table-collapse", "is_open")],
    )
    def toggle_table_collapse(n, is_open):
        if n:
            return not is_open
        return is_open
    
    @app.callback(
        [Output('attendance-chart', 'figure'),
         Output('summary-stats', 'children'),
         Output('date-selector', 'options'),
         Output('location-breakdown-chart', 'figure')],
        [Input('date-range-picker', 'start_date'),
         Input('date-range-picker', 'end_date'),
         Input('location-dropdown', 'value'),
         Input('category-dropdown', 'value'),
         Input('date-selector', 'value')]
    )
    def update_main_dashboard(start_date, end_date, selected_locations, selected_categories, selected_date):
        # Filter data
        filtered_df = df.copy()
        
        if start_date and end_date:
            filtered_df = filtered_df[
                (filtered_df['date'] >= pd.to_datetime(start_date).date()) &
                (filtered_df['date'] <= pd.to_datetime(end_date).date())
            ]
        
        if selected_locations:
            filtered_df = filtered_df[filtered_df['Where'].isin(selected_locations)]
            
        if selected_categories:
            filtered_df = filtered_df[filtered_df['Category'].isin(selected_categories)]
        
        # Create daily attendance chart with better styling
        daily_counts = filtered_df.groupby('date').size().reset_index(name='count')
        daily_counts['date_str'] = daily_counts['date'].astype(str)
        
        fig = px.bar(
            daily_counts, 
            x='date_str', 
            y='count',
            #title='Daily Attendance Entries',
            labels={'date_str': 'Date', 'count': 'Number of Entries'}
        )
        
        # Improve chart styling
        fig.update_traces(marker_color='#3b82f6', marker_line_color='#1d4ed8', marker_line_width=1)
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Entries",
            title_x=0.5,
            title_font_size=16,
            title_font_color='#1f2937',
            showlegend=False,
            height=400,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font={'color': '#374151'},
            xaxis={'gridcolor': '#f3f4f6'},
            yaxis={'gridcolor': '#f3f4f6'}
        )
        
        fig.update_xaxes(tickangle=45)
        
        # Summary statistics with better design
        total_entries = len(filtered_df)
        unique_people = filtered_df['full_name'].nunique()
        date_range_days = (filtered_df['date'].max() - filtered_df['date'].min()).days + 1 if not filtered_df.empty else 0
        
        summary_stats = [
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{total_entries:,}", className="text-primary mb-0", style={'fontWeight': '700'}),
                        html.P("Total Entries", className="text-muted mb-0", style={'fontSize': '14px'})
                    ], className="text-center")
                ], style={'border': '1px solid #dbeafe', 'backgroundColor': 'rgba(239, 246, 255, 0.95)'})
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{unique_people:,}", className="text-success mb-0", style={'fontWeight': '700'}),
                        html.P("Unique People", className="text-muted mb-0", style={'fontSize': '14px'})
                    ], className="text-center")
                ], style={'border': '1px solid #dcfce7', 'backgroundColor': 'rgba(240, 253, 244, 0.95)'})
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{date_range_days}", className="text-danger mb-0", style={'fontWeight': '700'}),
                        html.P("Days Covered", className="text-muted mb-0", style={'fontSize': '14px'})
                    ], className="text-center")
                ], style={'border': '1px solid #fecaca', 'backgroundColor': 'rgba(254, 242, 242, 0.95)'})
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{total_entries/date_range_days:.1f}" if date_range_days > 0 else "0", 
                               className="text-warning mb-0", style={'fontWeight': '700'}),
                        html.P("Avg/Day", className="text-muted mb-0", style={'fontSize': '14px'})
                    ], className="text-center")
                ], style={'border': '1px solid #fed7aa', 'backgroundColor': 'rgba(255, 247, 237, 0.95)'})
            ], width=3)
        ]
        
        # Date options for location breakdown
        available_dates = sorted(filtered_df['date'].unique(), reverse=True)
        date_options = [{'label': str(date), 'value': str(date)} for date in available_dates]
        
        # Location breakdown chart
        location_fig = px.bar(
            title='Select a date to view location breakdown',
            labels={'x': 'Location', 'y': 'Number of Entries'}
        )
        
        if selected_date:
            selected_date_obj = pd.to_datetime(selected_date).date()
            date_filtered_df = filtered_df[filtered_df['date'] == selected_date_obj]
            
            if not date_filtered_df.empty:
                location_counts = date_filtered_df.groupby('Where').size().reset_index(name='count')
                location_fig = px.bar(
                    location_counts,
                    x='Where',
                    y='count',
                    title=f'Entries by Location on {selected_date}',
                    labels={'Where': 'Location', 'count': 'Number of Entries'}
                )
                location_fig.update_traces(marker_color='#10b981', marker_line_color='#059669', marker_line_width=1)
                location_fig.update_xaxes(tickangle=45)
            else:
                location_fig = px.bar(
                    title=f'No entries found for {selected_date}',
                    labels={'x': 'Location', 'y': 'Number of Entries'}
                )
        
        location_fig.update_layout(
            height=400,
            title_x=0.5,
            title_font_size=16,
            title_font_color='#1f2937',
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font={'color': '#374151'},
            xaxis={'gridcolor': '#f3f4f6'},
            yaxis={'gridcolor': '#f3f4f6'}
        )
        
        return fig, summary_stats, date_options, location_fig
    
    @app.callback(
        [Output('data-table', 'children'),
         Output('table-info', 'children')],
        [Input('table-date-filter', 'date'),
         Input('table-name-filter', 'value')]
    )
    def update_entries_table(table_date, table_name):
        # Filter data for table
        table_df = df.copy()
        
        # Single date filter
        if table_date:
            table_df = table_df[table_df['date'] == pd.to_datetime(table_date).date()]
        
        # Name filter
        if table_name:
            table_df = table_df[table_df['full_name'].str.contains(table_name, case=False, na=False) |
                               table_df['Who'].str.contains(table_name, case=False, na=False)]
        
        # Sort by most recent first
        table_df = table_df.sort_values('When', ascending=False)
        
        # Prepare table data
        table_data = table_df[['When', 'full_name', 'Where', 'Category']].copy()
        table_data['When'] = table_data['When'].dt.strftime('%d/%m/%Y %H:%M')
        table_data = table_data.rename(columns={
            'When': 'Time',
            'full_name': 'Name',
            'Where': 'Location',
            'Category': 'Category'
        })
        
        # Create info message
        total_filtered = len(table_data)
        if table_date:
            date_str = pd.to_datetime(table_date).strftime('%d/%m/%Y')
            info_message = dbc.Alert(
                f"Showing {total_filtered:,} entries for {date_str}", 
                color="info", 
                className="py-2 mb-0"
            )
        else:
            info_message = dbc.Alert(
                f"Showing {total_filtered:,} entries (all dates)", 
                color="info", 
                className="py-2 mb-0"
            )
        
        # Create data table
        if not table_data.empty:
            data_table = dash_table.DataTable(
                data=table_data.to_dict('records'),
                columns=[{"name": col, "id": col} for col in table_data.columns],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '12px',
                    'fontFamily': 'system-ui, -apple-system, sans-serif',
                    'fontSize': '14px'
                },
                style_header={
                    'backgroundColor': '#f8fafc',
                    'fontWeight': 'bold',
                    'border': '1px solid #e2e8f0',
                    'color': '#1f2937'
                },
                style_data={
                    'backgroundColor': 'white',
                    'border': '1px solid #f3f4f6'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f9fafb'
                    }
                ],
                page_size=20,
                sort_action="native",
                filter_action="native"
            )
        else:
            data_table = dbc.Alert("No entries found with current filters.", color="warning")
        
        return data_table, info_message
    
    return app