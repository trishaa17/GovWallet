import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import requests
from io import StringIO
from loadcsv import load_csv_data


def create_dash_number_of_roles(server):
    # url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EfFwqNRlqjdKgUnvBWe53SEBKKJA9yK7RomjADmwfuT6iQ?download=1"
    # response = requests.get(url)
    # response.raise_for_status()
    # csv_data = response.content.decode('utf-8')
    # df = pd.read_csv(StringIO(csv_data))
    df = load_csv_data()
    df['date_created'] = pd.to_datetime(df['date_created'], utc=True)

    # Treat missing or empty role names as 'Others'
    df['gms_role_name'] = df['gms_role_name'].fillna('Others')
    df.loc[df['gms_role_name'].str.strip() == '', 'gms_role_name'] = 'Others'

    total_per_role = df.groupby('gms_role_name')['gms_id'].nunique().reset_index()
    total_per_role.rename(columns={'gms_id': 'total_unique_accounts'}, inplace=True)

    total_unique_people = df['gms_id'].nunique()


    app = Dash(__name__, server=server, routes_pathname_prefix='/appNumberOfRoles/')
    app.title = "Manpower Count Dashboard"

    # Get min and max dates from date_created column (as date only)
    min_date = df['date_created'].dt.date.min()
    max_date = df['date_created'].dt.date.max()

    app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Manpower Count Dashboard", 
                style={
                    'margin': '0',
                    'fontSize': '24px',
                    'fontWeight': '600',
                    'color': '#1f2937'
                })
    ], style={
        'padding': '20px 40px',
        'backgroundColor': '#ffffff',
        'borderBottom': '1px solid #e5e7eb'
    }),
    
    # Main content
    html.Div([

            # Top controls section
            html.Div([
                # Date mode and pickers
                html.Div([
                    html.Div([
                        html.Label("Select Date Mode", style={
                            'fontSize': '14px', 
                            'fontWeight': '600', 
                            'color': '#374151'
                        }),
                        dcc.RadioItems(
                            id='date-mode',
                            options=[
                                {'label': 'Single Date', 'value': 'single'},
                                {'label': 'Date Range', 'value': 'range'}
                            ],
                            value='single',
                            labelStyle={
                                'display': 'inline-block',
                                'marginRight': '15px',
                                'fontSize': '14px',
                                'color': '#6b7280'
                            },
                            style={'marginBottom': '10px'}
                        ),
                    ]),
                    
                    # Date pickers
                    html.Div([
                        html.Div([
                            dcc.DatePickerSingle(
                                id='single-date-picker',
                                min_date_allowed=min_date,
                                max_date_allowed=max_date,
                                placeholder='Select a date',
                                display_format='YYYY-MM-DD',
                                with_portal=True,
                                clearable=True
                            )
                        ], id='single-date-container', style={'display': 'block'}),

                        html.Div([
                            dcc.DatePickerRange(
                                id='range-date-picker',
                                min_date_allowed=min_date,
                                max_date_allowed=max_date,
                                start_date=min_date,
                                end_date=max_date,
                                display_format='YYYY-MM-DD',
                                with_portal=True,
                                clearable=True
                            )
                        ], id='range-date-container', style={'display': 'none'})
                    ])
                ], style={'flex': '1'})
            ], style={
                'display': 'flex',
                'justifyContent': 'flex-start',
                'alignItems': 'flex-start',
                'marginBottom': '20px',
                'padding': '0 20px'
            }),

            

            # Wrapper div for the two components for consistent width & centering
            html.Div([
                # Bar chart container
                html.Div([
                    # Header with title and filter button
                    html.Div([
                        # Empty div for left spacing
                        html.Div(style={'flex': '1'}),
                        
                        html.H2("Number of people working per role", style={
                            'fontSize': '18px',
                            'fontWeight': '600',
                            'color': '#1f2937',
                            'margin': '0',
                            'flex': '1',
                            'textAlign': 'center'
                        }),
                        
                        # Location filter with collapsible dropdown
                        html.Div([ 
                            html.Button([ 
                                html.Img(src="https://static.thenounproject.com/png/247545-200.png",  
                                        style={'width': '16px', 'height': '16px'}) 
                            ],  
                            id='filter-toggle-btn', 
                            style={ 
                                'backgroundColor': "#C1C7D2", 
                                'border': 'none', 
                                'borderRadius': '50%', 
                                'width': '32px',
                                'height': '32px',
                                'cursor': 'pointer', 
                                'display': 'flex', 
                                'alignItems': 'center', 
                                'justifyContent': 'center',
                                'transition': 'all 0.2s ease' 
                            }), 
                            
                            html.Div([ 
                                dcc.Dropdown( 
                                    id='location-filter', 
                                    options=[{'label': loc, 'value': loc} for loc in sorted(df['registration_location_id'].dropna().unique())], 
                                    multi=True, 
                                    placeholder="Select one or more campaigns", 
                                    style={'width': '300px', 'fontSize': '14px', 'marginTop': '10px', 'textAlign': 'left'} 
                                ) 
                            ], id='filter-dropdown-container', style={'display': 'none', 'position': 'absolute', 'top': '100%', 'right': '0', 'zIndex': '1000'}) 
                        ], style={'position': 'relative', 'flex': '1', 'display': 'flex', 'justifyContent': 'flex-end'})
                    ], style={
                        'display': 'flex',
                        'alignItems': 'center',
                        'marginBottom': '20px'
                    }),
                    
                    dcc.Graph(
                        id='bar-chart',
                        config={'displayModeBar': False},
                        style={'height': '500px'}
                    )
                ], style={
                    'backgroundColor': '#E6E8EC',
                    'padding': '20px',
                    'borderRadius': '10px',
                    'textAlign': 'center',
                    'maxWidth': '1200px',
                    'margin': '0 auto',     # centers the div horizontally
                    'boxSizing': 'border-box'
                }),

                # Spacer between blocks
                html.Div(style={'height': '40px'}),

                # Total per role container
                html.Div([
                    html.H2("Total number of people working per role (All Dates)", style={
                        'textAlign': 'center',
                        'fontSize': '18px',
                        'fontWeight': '600',
                        'marginBottom': '10px',       
                        'paddingBottom': '10px',  
                        'borderBottom': '1px solid #ffffff',
                        'color': '#1f2937'
                    }),

                    html.Ul([
                        html.Li(f"{row['gms_role_name']}: {row['total_unique_accounts']} unique accounts",
                                style={'fontSize': '14px', 'color': '#374151', 'marginBottom': '6px'})
                        for _, row in total_per_role.iterrows()
                    ], style={
                        'listStyleType': 'none',
                        'padding': '0',
                        'margin': '0 auto',
                        'textAlign': 'center'
                    }),

                    html.H3(f"Total unique people (all roles): {total_unique_people}", style={
                        'fontSize': '16px',
                        'fontWeight': '600',
                        'color': '#1f2937',
                        'marginTop': '10px',
                        'textAlign': 'center'
                    })
                ], style={
                    'backgroundColor': '#E6E8EC',
                    'padding': '20px',
                    'borderRadius': '10px',
                    'textAlign': 'center',
                    'maxWidth': '1200px',
                    'margin': '0 auto',
                    'boxSizing': 'border-box'
                })
            ], style={
                'padding': '0 20px',
                'marginBottom': '40px',
                'textAlign': 'center',
            })




        ], style={
            'padding': '30px 20px',
            'backgroundColor': '#ffffff',
            'minHeight': 'calc(100vh - 80px)'
        })

    ], style={
        'backgroundColor': '#f9fafb',
        'minHeight': '100vh',
        'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
    })


    # Toggle between single and range date pickers
    @app.callback(
        Output('single-date-container', 'style'),
        Output('range-date-container', 'style'),
        Input('date-mode', 'value')
    )
    def toggle_date_picker(mode):
        if mode == 'single':
            return {'display': 'block'}, {'display': 'none'}
        else:
            return {'display': 'none'}, {'display': 'block'}

    # Toggle filter dropdown visibility
    @app.callback(
        Output('filter-dropdown-container', 'style'),
        Input('filter-toggle-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def toggle_filter_dropdown(n_clicks):
        if n_clicks and n_clicks % 2 == 1:
            return {'display': 'block'}
        else:
            return {'display': 'none'}
    # Update bar chart based on date filter
    @app.callback(
        Output('bar-chart', 'figure'),
        Input('date-mode', 'value'),
        Input('single-date-picker', 'date'),
        Input('range-date-picker', 'start_date'),
        Input('range-date-picker', 'end_date'),
        Input('location-filter', 'value')  # new input for locations
    )
    def update_bar_chart(mode, single_date, start_date, end_date, selected_locations):
        filtered = df.copy()

        # Filter by registration_location_id if any selected
        if selected_locations:
            filtered = filtered[filtered['registration_location_id'].isin(selected_locations)]

        # Then filter by date mode
        if mode == 'single' and single_date:
            selected = pd.to_datetime(single_date).date()
            filtered = filtered[filtered['date_created'].dt.date == selected]
            if filtered.empty:
                return px.pie(title=f"No data for {selected}")
            title = f"Number of people working per role on {selected}"
        elif mode == 'range' and start_date and end_date:
            start = pd.to_datetime(start_date).date()
            end = pd.to_datetime(end_date).date()
            filtered = filtered[(filtered['date_created'].dt.date >= start) & (filtered['date_created'].dt.date <= end)]
            if filtered.empty:
                return px.pie(title=f"No data from {start} to {end}")
            title = f"Number of people working per role from {start} to {end}"
        else:
            title = "Number of people working per role (All Dates)"

        summary = (
            filtered.groupby('gms_role_name')['gms_id']
            .nunique().reset_index()
            .rename(columns={'gms_id': 'unique_accounts'})
        )

        fig = px.pie(
            summary,
            names='gms_role_name',
            values='unique_accounts',
            title=title,
            color_discrete_sequence=px.colors.qualitative.Pastel 
        )
        return fig


    return app
