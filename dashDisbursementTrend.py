import pandas as pd
import sqlite3
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table
import requests
from io import StringIO

def create_dash_disbursement_trend(server):
    url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EfFwqNRlqjdKgUnvBWe53SEBKKJA9yK7RomjADmwfuT6iQ?download=1"
    response = requests.get(url)
    response.raise_for_status()
    csv_data = response.content.decode('utf-8')
    df = pd.read_csv(StringIO(csv_data))

    df = df[df['wallet_status'] == 'completed']
    df['payout_date'] = pd.to_datetime(df['payout_date'])

    conn = sqlite3.connect('wallet_trend.db')
    df.to_sql('wallet_raw', conn, if_exists='replace', index=False)
    conn.close()

    print("Trend database created successfully.")

    app = Dash(__name__, server=server, url_base_pathname='/appDisbursementTrend/')

    app.layout = html.Div([
        html.H1("Disbursement Trend Over Time"),

        dcc.Dropdown(
            id='gmsid-filter',
            options=[{'label': str(i), 'value': i} for i in sorted(df['gms_id'].unique())],
            multi=True,
            placeholder="Select GMS ID(s)"
        ),

        dcc.Dropdown(
            id='name-filter',
            options=[{'label': str(i), 'value': i} for i in sorted(df['name'].unique())],
            multi=True,
            placeholder="Select Name(s)"
        ),

        dcc.DatePickerRange(
            id='date-range',
            min_date_allowed=df['payout_date'].min().date(),
            max_date_allowed=df['payout_date'].max().date(),
            start_date=df['payout_date'].min().date(),
            end_date=df['payout_date'].max().date()
        ),

        dcc.RadioItems(
            id='time-grouping',
            options=[
                {'label': 'Daily', 'value': 'D'},
                {'label': 'Weekly', 'value': 'W'},
                {'label': 'Monthly', 'value': 'M'}
            ],
            value='W',
            labelStyle={'display': 'inline-block', 'marginRight': '10px'},
            style={'marginTop': '10px'}
        ),

        dcc.Graph(id='line-chart', style={'marginTop': '20px'})
    ])

    @app.callback(
        Output('line-chart', 'figure'),
        Input('gmsid-filter', 'value'),
        Input('name-filter', 'value'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date'),
        Input('time-grouping', 'value')
    )
    def update_line_chart(gms_ids, names, start_date, end_date, grouping):
        query = "SELECT * FROM wallet_raw WHERE 1=1"
        params = []

        if gms_ids:
            placeholders = ','.join('?' for _ in gms_ids)
            query += f" AND gms_id IN ({placeholders})"
            params.extend(gms_ids)

        if names:
            placeholders = ','.join('?' for _ in names)
            query += f" AND name IN ({placeholders})"
            params.extend(names)

        if start_date:
            query += " AND payout_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND payout_date <= ?"
            params.append(end_date)

        conn = sqlite3.connect('wallet_trend.db')
        temp_df = pd.read_sql(query, conn, params=params, parse_dates=['payout_date'])
        conn.close()

        if temp_df.empty:
            return px.line(title="No data available")

        grouped = temp_df.groupby(pd.Grouper(key='payout_date', freq=grouping))['amount'].sum().reset_index()

        fig = px.line(
            grouped,
            x='payout_date',
            y='amount',
            title=f'Total Disbursed Amount Over Time ({grouping})',
            labels={'payout_date': 'Date', 'amount': 'Total Disbursed'}
        )
        fig.update_traces(mode='lines+markers')
        return fig

    return app
