import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import requests
from io import StringIO
from loadcsv import load_csv_data

def create_dash_total_amount(server):
    # url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EfFwqNRlqjdKgUnvBWe53SEBKKJA9yK7RomjADmwfuT6iQ?download=1"
    # response = requests.get(url)
    # response.raise_for_status()
    # csv_data = response.content.decode('utf-8')
    # df = pd.read_csv(StringIO(csv_data))

    df = load_csv_data()

    df = df[df['wallet_status'] == 'completed']

    df['payout_date'] = pd.to_datetime(df['payout_date'])

    app = Dash(__name__, server=server, routes_pathname_prefix='/appTotalAmount/')
    app.title = "GovWallet Payout Amount Tracker"

    min_date = df['payout_date'].min().date()
    max_date = df['payout_date'].max().date()

    app.layout = html.Div([

        # Header (kept white for contrast)
        html.Div([
            html.H1("Total Disbursement Dashboard (by role/campaign)", 
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

        # Component 1: Select Date (background #E6E8EC)
        html.Div([
            html.Div([
                html.Div([
                    html.H2("Select Date Mode", style={'fontSize': '16px', 'color': '#374151'}),
                    dcc.RadioItems(
                        id='date-mode',
                        options=[
                            {'label': 'Single Date', 'value': 'single'},
                            {'label': 'Date Range', 'value': 'range'}
                        ],
                        value='range',
                        labelStyle={'display': 'inline-block', 'marginRight': '15px', 'fontSize': '14px', 'color': '#4b4b7d'},
                        style={'marginBottom': '10px'}
                    ),
                    html.Div([
                        dcc.DatePickerSingle(
                            id='single-date-picker',
                            min_date_allowed=min_date,
                            max_date_allowed=max_date,
                            placeholder='Select a date',
                            display_format='YYYY-MM-DD',
                            with_portal=True
                        )
                    ], id='single-date-container', style={'display': 'none'}),
                    html.Div([
                        dcc.DatePickerRange(
                            id='range-date-picker',
                            min_date_allowed=min_date,
                            max_date_allowed=max_date,
                            start_date=min_date,
                            end_date=max_date,
                            display_format='YYYY-MM-DD',
                            with_portal=True
                        )
                    ], id='range-date-container', style={'display': 'block'})
                ], style={'flex': '1'}),
            ], style={'display': 'flex', 'padding': '30px 40px'})
        ], style={
            'display': 'flex',
            'justifyContent': 'flex-start',
            'alignItems': 'flex-start',
            'marginBottom': '20px',
            'padding': '0 20px'
        }),

        # Component 2: Overview + Sort + View Payout + Graph (background #E6E8EC)
        html.Div([

            # Disbursement Overview heading
            html.Div([
                html.H2("Total Disbursement Overview", 
                    style={
                        'textAlign': 'center',
                        'fontSize': '20px',
                        'fontWeight': '600',
                        'color': '#1f2937',
                        'marginBottom': '10px',        # smaller margin below text
                        'paddingBottom': '10px',       # space below text before line
                        'borderBottom': '1px solid #ffffff',  # thicker white line
                        'marginLeft': 'auto',
                        'marginRight': 'auto'
                    })
            ]),

            # Sorting, grouping, and filters
            html.Div([
                html.Div([

                    # Sort by amount
                    html.Div([
                        html.H2("Sort by Amount", style={'fontSize': '16px', 'color': '#374151'}),
                        dcc.RadioItems(
                            id='sort-order',
                            options=[
                                {'label': 'Ascending', 'value': 'asc'},
                                {'label': 'Descending', 'value': 'desc'},
                            ],
                            value='desc',
                            labelStyle={'display': 'block', 'marginBottom': '8px', 'fontSize': '14px', 'color': '#4b4b7d'}
                        )
                    ], style={'minWidth': '180px', 'marginRight': '20px'}),

                    # View payout by
                    html.Div([
                        html.H2("View Payouts By", style={'fontSize': '16px', 'color': '#374151'}),
                        dcc.Dropdown(
                            id='group-by-selector',
                            options=[
                                {'label': 'Role', 'value': 'gms_role_name'},
                                {'label': 'Campaign', 'value': 'registration_location_id'}
                            ],
                            value='gms_role_name',
                            clearable=False,
                            style={'width': '200px', 'fontSize': '14px'}
                        ),
                    ], style={'marginRight': '20px'}),

                    # Role filter
                    html.Div([
                        html.H2("Role Filter", style={'fontSize': '16px', 'color': '#374151'}),
                        dcc.Dropdown(
                            id='role-filter',
                            options=[{'label': role, 'value': role} for role in sorted(df['gms_role_name'].dropna().unique())],
                            multi=True,
                            placeholder="Select roles...",
                            style={'width': '220px', 'fontSize': '14px'}
                        )
                    ], style={'marginRight': '20px'}),

                    # Campaign filter
                    html.Div([
                        html.H2("Campaign Filter", style={'fontSize': '16px', 'color': '#374151'}),
                        dcc.Dropdown(
                            id='campaign-filter',
                            options=[{'label': camp, 'value': camp} for camp in sorted(df['registration_location_id'].dropna().unique())],
                            multi=True,
                            placeholder="Select campaigns...",
                            style={'width': '220px', 'fontSize': '14px'}
                        )
                    ])

                ], style={
                    'display': 'flex',
                    'flexWrap': 'wrap',
                    'alignItems': 'flex-start',
                    'gap': '20px',
                    'justifyContent': 'center',
                    'margin': '0 auto',
                    'maxWidth': '1000px'
                })
            ], style={'paddingBottom': '30px'}),


            # Graph
            html.Div([
                dcc.Graph(id='payout-bar-chart', config={'displayModeBar': False})
            ], style={'backgroundColor': '#ffffff', 'padding': '10px', 'borderRadius': '8px'}),

        ], style={
            'backgroundColor': '#E6E8EC',
            'margin': '20px',
            'borderRadius': '12px',
            'padding': '30px 40px 40px 40px'
        }),

    ], style={
        'backgroundColor': '#f9fafb',
        'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        'minHeight': '100vh',
        'paddingBottom': '40px'
    })



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

    # Callback for role filter toggle
    @app.callback(
        Output('role-filter-dropdown-container', 'style'),
        Input('role-filter-toggle-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def toggle_role_filter(n_clicks):
        if n_clicks and n_clicks % 2 == 1:
            return {'display': 'block', 'position': 'absolute', 'top': '100%', 'left': '0', 'zIndex': '1000'}
        else:
            return {'display': 'none', 'position': 'absolute', 'top': '100%', 'left': '0', 'zIndex': '1000'}

    # Callback for campaign filter toggle
    @app.callback(
        Output('campaign-filter-dropdown-container', 'style'),
        Input('campaign-filter-toggle-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def toggle_campaign_filter(n_clicks):
        if n_clicks and n_clicks % 2 == 1:
            return {'display': 'block', 'position': 'absolute', 'top': '100%', 'left': '0', 'zIndex': '1000'}
        else:
            return {'display': 'none', 'position': 'absolute', 'top': '100%', 'left': '0', 'zIndex': '1000'}

    @app.callback(
        Output('payout-bar-chart', 'figure'),
        Input('date-mode', 'value'),
        Input('single-date-picker', 'date'),
        Input('range-date-picker', 'start_date'),
        Input('range-date-picker', 'end_date'),
        Input('group-by-selector', 'value'),
        Input('role-filter', 'value'),
        Input('campaign-filter', 'value'),
        Input('sort-order', 'value'),

    )
    def update_chart(mode, single_date, start_date, end_date, group_by, selected_roles, selected_campaigns, sort_order):
        filtered = df.copy()

        # Handle filtering by date
        if mode == 'single' and single_date:
            selected = pd.to_datetime(single_date)
            filtered = filtered[filtered['payout_date'] == selected]

            if group_by == 'gms_role_name':
                title = f"Total amount paid by each role on {selected.date()}"
            elif group_by == 'registration_location_id':
                title = f"Total amount paid by each campaign on {selected.date()}"
            else:
                title = f"Total amount paid on {selected.date()}"

        elif mode == 'range' and start_date and end_date:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            filtered = filtered[(filtered['payout_date'] >= start) & (filtered['payout_date'] <= end)]

            if group_by == 'gms_role_name':
                title = f"Total amount paid by each role from {start.date()} to {end.date()}"
            elif group_by == 'registration_location_id':
                title = f"Total amount paid by each campaign from {start.date()} to {end.date()}"
            else:
                title = f"Total amount paid from {start.date()} to {end.date()}"
        else:
            return px.bar(title="Please select a valid date.")

        # Apply Role filter
        if selected_roles:
            filtered = filtered[filtered['gms_role_name'].isin(selected_roles)]

        # Apply Campaign filter
        if selected_campaigns:
            filtered = filtered[filtered['registration_location_id'].isin(selected_campaigns)]

        if filtered.empty:
            return px.bar(title="No data available for the selected filters.")

        grouped = (
            filtered.groupby(group_by)['amount']
            .sum().reset_index()
            .rename(columns={'amount': 'total_paid'})
        )

        # Sort grouped data by total_paid
        ascending = True if sort_order == 'asc' else False
        grouped = grouped.sort_values(by='total_paid', ascending=ascending)

        fig = px.bar(
            grouped,
            x=group_by,
            y='total_paid',
            color=group_by,  # still coloring by group if desired
            title=title,
            labels={
                group_by: group_by.replace('_', ' ').title(),
                'total_paid': 'Total Paid (SGD)',
                'registration_location_id': 'Campaign'
            },
            color_discrete_sequence=px.colors.qualitative.Pastel  # or other palettes like Plotly, Set2, etc.
        )

        # Layout styling
        fig.update_layout(
            title_font=dict(size=20, family='Arial', color='#374151'),
            font=dict(size=14, family='Arial', color='#4B5563'),
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(
                title=group_by.replace('_', ' ').title(),
                showgrid=False,
                linecolor='#E5E7EB'
            ),
            yaxis=dict(
                title='Total Paid (SGD)',
                showgrid=True,
                gridcolor='#E5E7EB',
                zeroline=False
            ),
            legend_title='',
            margin=dict(t=50, l=150, r=150, b=40) 
        )

        return fig


    return app