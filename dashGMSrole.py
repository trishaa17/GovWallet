import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import requests
from io import StringIO


def create_dash1(server):
    url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EdyAJaCQLpFAp3JTaMCmK_8BkXS81I50q0dg7t5bDrsSEg?download=1"
    response = requests.get(url)
    response.raise_for_status()
    csv_data = response.content.decode('utf-8')
    df = pd.read_csv(StringIO(csv_data))

    df['payout_date'] = pd.to_datetime(df['payout_date'])

    total_per_role = df.groupby('gms_role_name')['gms_id'].nunique().reset_index()
    total_per_role.rename(columns={'gms_id': 'total_unique_accounts'}, inplace=True)

    app = Dash(__name__, server=server, routes_pathname_prefix='/app1/')
    app.title = "GovWallet Disbursement Dashboard"

    min_date = df['payout_date'].min().date()
    max_date = df['payout_date'].max().date()

    app.layout = html.Div([
        html.H1("GovWallet Disbursement Summary", style={'textAlign': 'center'}),

        html.H2("Filter by Single Payout Date"),
        dcc.DatePickerSingle(
            id='single-date-picker',
            min_date_allowed=min_date,
            max_date_allowed=max_date,
            placeholder='Select a date',
            display_format='YYYY-MM-DD',
            style={'marginBottom': '20px'}
        ),

        html.H2("Unique Accounts per Role on Selected Date"),
        dcc.Graph(id='bar-chart'),

        html.H2("Total Unique Accounts per Role (All Dates)"),
        html.Ul([
            html.Li(f"{row['gms_role_name']}: {row['total_unique_accounts']} unique accounts")
            for _, row in total_per_role.iterrows()
        ])
    ])

    @app.callback(
        Output('bar-chart', 'figure'),
        Input('single-date-picker', 'date')
    )
    def update_bar_chart(selected_date):
        if not selected_date:
            return px.bar(title="Please select a date to display results.")

        selected = pd.to_datetime(selected_date)
        filtered = df[df['payout_date'] == selected]

        if filtered.empty:
            return px.bar(title=f"No data for {selected.date()}")

        summary = (
            filtered.groupby(['payout_date', 'gms_role_name'])['gms_id']
            .nunique().reset_index()
            .rename(columns={'gms_id': 'unique_accounts'})
        )

        fig = px.bar(
            summary,
            x='gms_role_name',
            y='unique_accounts',
            color='gms_role_name',
            title=f"Unique Accounts by Role on {selected.date()}",
            labels={'gms_role_name': 'Role', 'unique_accounts': 'Unique Accounts'}
        )
        return fig

    return app
    
    