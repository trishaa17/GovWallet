import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table
import requests
from io import StringIO
from loadcsv import load_csv_data

def create_dash_heatmap(server):
    # url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EfFwqNRlqjdKgUnvBWe53SEBKKJA9yK7RomjADmwfuT6iQ?download=1"
    # response = requests.get(url)
    # response.raise_for_status()
    # csv_data = response.content.decode('utf-8')
    # df = pd.read_csv(StringIO(csv_data))

    df = load_csv_data()

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
        # Header
        html.Div([
            html.H1("Disbursement Heatmap by Location and Date", 
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

        # Filters section
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id='campaign-filter',
                    options=[{'label': camp, 'value': camp} for camp in sorted(df['registration_location_id'].dropna().unique())],
                    multi=True,
                    placeholder='Filter by Campaign',
                    style={'width': '280px', 'marginBottom': '10px', 'fontSize': '14px'}
                ),
                dcc.Dropdown(
                    id='location-filter',
                    options=[{'label': loc, 'value': loc} for loc in sorted(df['location'].dropna().unique())],
                    multi=True,
                    placeholder='Filter by Location',
                    style={'width': '280px', 'fontSize': '14px'}
                )
            ], style={'flex': '1'}),

            html.Div([
                dcc.DatePickerRange(
                    id='date-range-picker',
                    min_date_allowed=min_date,
                    max_date_allowed=max_date,
                    start_date=min_date,
                    end_date=max_date,
                    display_format='YYYY-MM-DD',
                    with_portal=True,
                    clearable=True
                )
            ], style={'flex': '1', 'display': 'flex', 'justifyContent': 'flex-end'})

        ], style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'flex-start',
            'margin': '20px 40px'
        }),

        # Heatmap section
        html.Div([
            dcc.Graph(id='heatmap-graph')
        ], style={'margin': '0 40px'}),

        # Summary Table Section
        html.Div([
        html.H3("Select Location for Summary Table:", 
                style={'marginTop': '30px', 'fontWeight': '600', 'color': '#1f2937'}),

        dcc.Dropdown(
            id='table-location-dropdown',
            options=[{'label': loc, 'value': loc} for loc in sorted(df['location'].dropna().unique())],
            placeholder='Select a location',
            clearable=True,
            searchable=True,
            style={'width': '300px', 'marginBottom': '20px'}
        ),

        html.H2("Amount distributed per campaign at selected location", 
                style={
                    'textAlign': 'center',
                    'fontSize': '18px',
                    'fontWeight': '600',
                    'color': '#1f2937',
                    'marginBottom': '20px'
                }),

        dash_table.DataTable(
            id='summary-table',
            columns=[
                {'name': 'Campaign', 'id': 'campaign'},
                {'name': 'Total Amount (SGD)', 'id': 'amount', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                {'name': 'Unique ID Count', 'id': 'unique_ids', 'type': 'numeric'},
            ],
            data=[],
            page_size=10,
            sort_action='native',
            style_table={
                'overflowX': 'auto',
                'border': '1px solid #e5e7eb',
                'borderRadius': '8px'
            },
            style_header={
                'backgroundColor': "#c4b8fa",
                'fontWeight': '600',
                'fontSize': '14px',
                'color': '#374151',
                'border': '1px solid #e5e7eb',
                'textAlign': 'left'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '12px',
                'fontSize': '14px',
                'color': '#374151',
                'border': '1px solid #e5e7eb'
            },
            style_data={
                'backgroundColor': '#F1F1F1FF',
                'border': '1px solid #e5e7eb'
            },
            style_data_conditional=[
                {
                    'if': {'filter_query': '{amount} > 1000', 'column_id': 'amount'},
                    'backgroundColor': "#F1F1F1FF",
                    'color': '#374151',
                    'fontWeight': '600'
                },
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#ddd6fe'
                }
            ],
        )
    ], style={
        'padding': '0 20px',
        'marginBottom': '40px'
    }),


        # Campaigns by Location section
        html.Div([
            html.H2("📌 Key: Campaigns by Location", style={
                'textAlign': 'center',
                'fontSize': '18px',
                'fontWeight': '600',
                'marginBottom': '10px',
                'paddingBottom': '10px',
                'borderBottom': '1px solid #ffffff',
                'color': '#1f2937'
            }),

            html.Div([
                html.Div([
                    html.H4(f"{loc} ({len(camps)} campaign{'s' if len(camps) != 1 else ''})", style={
                        'fontSize': '16px',
                        'fontWeight': '600',
                        'color': '#4b5563',
                        'marginBottom': '4px'
                    }),
                    html.Ul([
                        html.Li(c, style={
                            'fontSize': '14px',
                            'color': '#374151',
                            'marginBottom': '4px'
                        }) for c in camps
                    ], style={
                        'listStyleType': 'disc',
                        'paddingLeft': '20px',
                        'margin': '0 0 10px 0'
                    })
                ], style={
                    'marginBottom': '16px',
                    'textAlign': 'left',
                    'backgroundColor': '#f9fafb',
                    'padding': '12px',
                    'borderRadius': '8px',
                    'boxShadow': '0 1px 2px rgba(0,0,0,0.05)'
                }) for loc, camps in sorted(legend_mapping.items())
            ], style={
                'maxWidth': '800px',
                'margin': '0 auto'
            })
        ], style={
            'backgroundColor': '#E6E8EC',
            'padding': '20px',
            'borderRadius': '10px',
            'textAlign': 'center',
            'maxWidth': '1200px',
            'margin': '40px auto 0 auto',
            'boxSizing': 'border-box'
        })

    ], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f3f4f6', 'minHeight': '100vh'})



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
