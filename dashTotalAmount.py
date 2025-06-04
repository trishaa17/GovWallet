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
        html.H1("Total Disbursement Dashboard (by role/campaign)", style={'textAlign': 'center'}),

        html.H2("Select Date Mode"),
        dcc.RadioItems(
            id='date-mode',
            options=[
                {'label': 'Single Date', 'value': 'single'},
                {'label': 'Date Range', 'value': 'range'}
            ],
            value='range',  # default to range mode
            labelStyle={'display': 'inline-block', 'marginRight': '15px'}
        ),

        html.Div([
            dcc.DatePickerSingle(
                id='single-date-picker',
                min_date_allowed=min_date,
                max_date_allowed=max_date,
                placeholder='Select a date',
                display_format='YYYY-MM-DD',
            )
        ], id='single-date-container', style={'display': 'none'}),  # hidden by default

        html.Div([
            dcc.DatePickerRange(
                id='range-date-picker',
                min_date_allowed=min_date,
                max_date_allowed=max_date,
                display_format='YYYY-MM-DD',
                start_date=min_date,  # default start date
                end_date=max_date,    # default end date
            )
        ], id='range-date-container', style={'display': 'block'}),  # visible by default


        html.Div([
            html.Div([
                html.H2("Filter by Role (Multi-select)"),
                dcc.Dropdown(
                    id='role-filter',
                    options=[{'label': role, 'value': role} for role in sorted(df['gms_role_name'].dropna().unique())],
                    multi=True,
                    placeholder='Select roles...',
                    style={'marginBottom': '20px'}
                ),
            ], style={'width': '48%', 'display': 'inline-block'}),

            html.Div([
                html.H2("Filter by Campaign (Multi-select)"),
                dcc.Dropdown(
                    id='campaign-filter',
                    options=[{'label': camp, 'value': camp} for camp in sorted(df['registration_location_id'].dropna().unique())],
                    multi=True,
                    placeholder='Select campaigns...',
                    style={'marginBottom': '20px'}
                ),
            ], style={'width': '48%', 'display': 'inline-block', 'float': 'right'}),
        ]),

        html.H2("View Payouts By"),
        dcc.Dropdown(
            id='group-by-selector',
            options=[
                {'label': 'Role', 'value': 'gms_role_name'},
                {'label': 'Campaign', 'value': 'registration_location_id'}
            ],
            value='gms_role_name',
            clearable=False,
            style={'width': '50%', 'marginBottom': '20px'}
        ),

        html.H2("Sort by Amount"),
        dcc.RadioItems(
            id='sort-order',
            options=[
                {'label': 'Descending', 'value': 'desc'},
                {'label': 'Ascending', 'value': 'asc'},
            ],
            value='desc',
            labelStyle={'display': 'inline-block', 'marginRight': '15px'},
            style={'marginBottom': '20px'}
        ),

        dcc.Graph(id='payout-bar-chart')
    ])

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
            color=group_by,
            title=title,
            labels={group_by: group_by.replace('_', ' ').title(), 'total_paid': 'Total Paid (SGD)', 'registration_location_id': 'Campaign'},
        )

        return fig

    return app
