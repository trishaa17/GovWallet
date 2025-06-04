import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table
import requests
from io import StringIO

def create_dash_heatmap(server):
    url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EfFwqNRlqjdKgUnvBWe53SEBKKJA9yK7RomjADmwfuT6iQ?download=1"
    response = requests.get(url)
    response.raise_for_status()
    csv_data = response.content.decode('utf-8')
    df = pd.read_csv(StringIO(csv_data))

    df = df[df['wallet_status'] == 'completed']
    df['payout_date'] = pd.to_datetime(df['payout_date'])

    location_keywords = [
        'AQC', 'WCA', 'KHALL', 'SEN', 'TSA', 'AIRPT',
        'ITEE', 'NEXUS', 'OTH', 'CONGR', 'OC', 'HOTEL1', 'HOTEL2', 'HOTEL3'
    ]

    def extract_location(campaign_name):
        campaign_parts = str(campaign_name).replace('-', '_').split('_')
        for keyword in location_keywords:
            if keyword.lower() in [part.lower() for part in campaign_parts]:
                return keyword
        return campaign_name  # Use campaign name itself if no keyword matched

    df['location'] = df['registration_location_id'].apply(extract_location)

    # Prepare legend dictionary
    legend_mapping = {}
    for _, row in df.iterrows():
        loc = row['location']
        camp = row['registration_location_id']
        legend_mapping.setdefault(loc, set()).add(camp)

    # Convert sets to sorted lists for display
    legend_mapping = {k: sorted(list(v)) for k, v in legend_mapping.items()}

    app = Dash(__name__, server=server, routes_pathname_prefix='/appLocationHeatmap/')
    app.title = "GovWallet Disbursement Heatmap"

    min_date = df['payout_date'].min().date()
    max_date = df['payout_date'].max().date()

    app.layout = html.Div([
        html.H1("Disbursement Heatmap by Location and Date", style={'textAlign': 'center'}),

        dcc.DatePickerRange(
            id='date-range-picker',
            min_date_allowed=min_date,
            max_date_allowed=max_date,
            start_date=min_date,
            end_date=max_date,
            display_format='YYYY-MM-DD'
        ),

        dcc.Dropdown(
            id='campaign-filter',
            options=[{'label': camp, 'value': camp} for camp in sorted(df['registration_location_id'].dropna().unique())],
            multi=True,
            placeholder='Filter by Campaign'
        ),

        dcc.Dropdown(
            id='location-filter',
            options=[{'label': loc, 'value': loc} for loc in sorted(df['location'].dropna().unique())],
            multi=True,
            placeholder='Filter by Location'
        ),

        dcc.Graph(id='heatmap-graph'),

        # New location selector for the summary table (single select)
        html.H3("Select Location for Summary Table:"),
        dcc.Dropdown(
            id='table-location-dropdown',
            options=[{'label': loc, 'value': loc} for loc in sorted(df['location'].dropna().unique())],
            placeholder='Select a location',
            clearable=True,
            searchable=True,
        ),

        dash_table.DataTable(
            id='summary-table',
            columns=[
                {'name': 'Campaign', 'id': 'campaign'},
                {'name': 'Total Amount (SGD)', 'id': 'amount', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                {'name': 'Unique ID Count', 'id': 'unique_ids', 'type': 'numeric'},
            ],
            data=[],
            style_cell={'textAlign': 'center'},
            style_header={'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
        ),

        html.H2("📌 Campaigns by Location", style={'marginTop': 40}),
        html.Div([
            html.Details([
                html.Summary(f"{loc} ({len(camps)} campaign{'s' if len(camps) != 1 else ''})"),
                html.Ul([html.Li(c) for c in camps])
            ], style={'marginBottom': '10px'})
            for loc, camps in sorted(legend_mapping.items())
        ])
    ])


    @app.callback(
        Output('heatmap-graph', 'figure'),
        Input('date-range-picker', 'start_date'),
        Input('date-range-picker', 'end_date'),
        Input('campaign-filter', 'value'),
        Input('location-filter', 'value'),  # new input
    )
    def update_heatmap(start_date, end_date, selected_campaigns, selected_locations):
        filtered = df.copy()

        if start_date and end_date:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            filtered = filtered[(filtered['payout_date'] >= start) & (filtered['payout_date'] <= end)]

        if selected_campaigns:
            filtered = filtered[filtered['registration_location_id'].isin(selected_campaigns)]

        if selected_locations:
            filtered = filtered[filtered['location'].isin(selected_locations)]

        if filtered.empty:
            fig = px.density_heatmap(
                title="No data available for the selected filters."
            )
            return fig

        filtered['payout_date'] = filtered['payout_date'].dt.date
        grouped = filtered.groupby(['location', 'payout_date'])['amount'].sum().reset_index()

        fig = px.density_heatmap(
            grouped,
            x='payout_date',
            y='location',
            z='amount',
            histfunc='sum',
            color_continuous_scale='Viridis',
            title="Heatmap of Amount Disbursed by Location and Date",
            labels={
                'payout_date': 'Date',
                'location': 'Location',
                'amount': 'Total Disbursed (SGD)'
            }
        )
        fig.update_layout(xaxis_nticks=20)
        return fig
    
    @app.callback(
        Output('summary-table', 'data'),
        Input('table-location-dropdown', 'value'),
        Input('date-range-picker', 'start_date'),
        Input('date-range-picker', 'end_date'),
        Input('campaign-filter', 'value'),
        Input('location-filter', 'value'),
    )
    def update_summary_table(selected_location, start_date, end_date, selected_campaigns, selected_locations):
        if not selected_location:
            return []

        filtered = df.copy()

        # Filter by date range
        if start_date and end_date:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            filtered = filtered[(filtered['payout_date'] >= start) & (filtered['payout_date'] <= end)]

        # Filter by campaigns if selected
        if selected_campaigns:
            filtered = filtered[filtered['registration_location_id'].isin(selected_campaigns)]

        # Filter by locations if selected
        if selected_locations:
            filtered = filtered[filtered['location'].isin(selected_locations)]

        # Filter for the selected location for the summary table
        filtered = filtered[filtered['location'] == selected_location]

        if filtered.empty:
            return []

        # Group by campaign name, sum amounts and count unique_ids
        grouped = filtered.groupby('registration_location_id').agg(
            amount=('amount', 'sum'),
            unique_ids=('gms_id', 'nunique')
        ).reset_index()

        # Rename columns for table display
        grouped.rename(columns={'registration_location_id': 'campaign'}, inplace=True)

        # Calculate totals row
        total_amount = grouped['amount'].sum()
        total_unique_ids = grouped['unique_ids'].sum()

        total_row = {
            'campaign': 'Total',
            'amount': total_amount,
            'unique_ids': total_unique_ids
        }

        # Append total row to data
        table_data = grouped.to_dict('records') + [total_row]

        return table_data



    return app
