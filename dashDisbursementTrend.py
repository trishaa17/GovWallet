from dash import Dash, dcc, html, Input, Output
import pandas as pd
import sqlite3
import plotly.express as px
from loadcsv import load_csv_data

def create_dash_disbursement_trend(server):
    df = load_csv_data()
    df = df[df['approval_stage'] == 'completed']
    df['payout_date'] = pd.to_datetime(df['payout_date'])

    conn = sqlite3.connect('wallet_trend.db')
    df.to_sql('wallet_raw', conn, if_exists='replace', index=False)
    conn.close()
    print("Trend database created successfully.")

    app = Dash(__name__, server=server, url_base_pathname='/appDisbursementTrend/')

    app.layout = html.Div([
        # Header
        html.Div([
            html.H1("Disbursement Trend Over Time",
                    style={'margin': '0', 'fontSize': '24px', 'fontWeight': '600', 'color': '#1f2937'})
        ], style={'padding': '20px 40px', 'backgroundColor': '#ffffff', 'borderBottom': '1px solid #e5e7eb'}),

        # Main content container
        html.Div([
            # Top controls section
            html.Div([
                # Left: GMS ID & Name filters
                html.Div([
                    dcc.Dropdown(
                        id='gmsid-filter',
                        options=[{'label': str(g), 'value': g} for g in sorted(df['gms_id'].unique())],
                        placeholder="Select GMS ID(s)", multi=True,
                        style={'width': '300px', 'fontSize': '14px'}
                    ),
                    dcc.Dropdown(
                        id='name-filter',
                        options=[{'label': str(n), 'value': n} for n in sorted(df['name'].unique())],
                        placeholder="Select Name(s)", multi=True,
                        style={'width': '300px', 'fontSize': '14px', 'marginTop': '10px'}
                    )
                ], style={'flex': '1'}),

                # Right: Date picker and grouping radio
                html.Div([
                    dcc.DatePickerRange(
                        id='date-range',
                        min_date_allowed=df['payout_date'].min().date(),
                        max_date_allowed=df['payout_date'].max().date(),
                        start_date=df['payout_date'].min().date(),
                        end_date=df['payout_date'].max().date(),
                        display_format='DD/MM/YYYY', clearable=True, with_portal=True
                    ),
                    dcc.RadioItems(
                        id='time-grouping',
                        options=[
                            {'label': 'Daily', 'value': 'D'},
                            {'label': 'Weekly', 'value': 'W'},
                            {'label': 'Monthly', 'value': 'M'}
                        ],
                        value='W',
                        labelStyle={'display': 'inline-block', 'marginRight': '15px', 'fontSize': '14px', 'color': '#6b7280'},
                        style={'marginTop': '10px'}
                    )
                ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'flex-end'})
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'flex-start',
                      'padding': '0 20px', 'marginBottom': '20px'}),

            # Line chart section in colored box
            html.Div([
                html.Div([
                    html.H2("Total Disbursed Amount Over Time",
                            style={'textAlign': 'center', 'fontSize': '18px', 'fontWeight': '600',
                                'color': '#1f2937', 'marginBottom': '20px'}),
                    dcc.Graph(id='line-chart', config={'displayModeBar': False}, style={'height': '300px'})
                ], style={
                    'backgroundColor': '#E6E8EC',
                    'padding': '20px',
                    'borderRadius': '12px',
                    'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.05)'
                })
            ], style={'padding': '0 20px', 'marginBottom': '40px'}),


        ], style={'padding': '30px 20px', 'backgroundColor': '#ffffff',
                  'minHeight': 'calc(100vh - 80px)'}),

    ], style={'backgroundColor': '#f9fafb', 'minHeight': '100vh',
              'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'})

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
            qmarks = ','.join('?' for _ in gms_ids)
            query += f" AND gms_id IN ({qmarks})"
            params += gms_ids
        if names:
            qmarks = ','.join('?' for _ in names)
            query += f" AND name IN ({qmarks})"
            params += names
        if start_date:
            query += " AND payout_date >= ?"; params.append(start_date)
        if end_date:
            query += " AND payout_date <= ?"; params.append(end_date)

        conn = sqlite3.connect('wallet_trend.db')
        temp_df = pd.read_sql(query, conn, params=params, parse_dates=['payout_date'])
        conn.close()

        if temp_df.empty:
            return px.line(title="No data available")

        grouped = temp_df.groupby(pd.Grouper(key='payout_date', freq=grouping))['amount'].sum().reset_index()
        fig = px.line(grouped, x='payout_date', y='amount',
                      title=f"Total Disbursed Amount Over Time ({grouping})",
                      labels={'payout_date': 'Date', 'amount': 'Total Disbursed'})
        fig.update_traces(mode='lines+markers')
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
            font=dict(color='#374151')
        )
        return fig

    return app
