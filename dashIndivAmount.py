import sqlite3
import plotly.express as px
import pandas as pd
from dash import Dash, dcc, html, Input, Output, dash_table
import requests
from io import StringIO
from datetime import datetime, date, timedelta

def create_dash_individual_amount(server):
    url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EfFwqNRlqjdKgUnvBWe53SEBKKJA9yK7RomjADmwfuT6iQ?download=1"
    response = requests.get(url)
    response.raise_for_status()
    csv_data = response.content.decode('utf-8')
    df = pd.read_csv(StringIO(csv_data))

    df = df[df['wallet_status'] == 'completed']
    df['date_created'] = pd.to_datetime(df['date_created']).dt.date

    # Aggregate names for display later
    agg_df = df.groupby(['gms_id', 'date_created']) \
               .agg({'amount': 'sum', 'name': lambda x: ', '.join(sorted(set(x)))}) \
               .reset_index()

    # Store aggregated data into SQLite
    conn = sqlite3.connect('wallet_data.db')
    agg_df.to_sql('wallet_data', conn, if_exists='replace', index=False)
    conn.close()

    app = Dash(__name__, server=server, url_base_pathname='/appMaxAmount/')

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)

    app.layout = html.Div([
        html.H1("Individual Disbursement Dashboard", style={'textAlign': 'center'}),

        dcc.Dropdown(
            id='gmsid-filter',
            options=[
                {'label': str(gms_id), 'value': gms_id}
                for gms_id in sorted(df['gms_id'].unique())
            ],
            placeholder="Select GMS ID(s)",
            multi=True
        ),

        dcc.RadioItems(
            id='date-mode',
            options=[
                {'label': 'Single Date', 'value': 'single'},
                {'label': 'Date Range', 'value': 'range'}
            ],
            value='range',
            labelStyle={'display': 'inline-block', 'marginRight': '15px'},
            style={'marginTop': '10px'}
        ),

        html.Div([
            dcc.DatePickerSingle(
                id='date-single',
                min_date_allowed=agg_df['date_created'].min(),
                max_date_allowed=agg_df['date_created'].max(),
                date=today
            )
        ], id='date-single-container', style={'display': 'none'}),

        html.Div([
            dcc.DatePickerRange(
                id='date-range',
                min_date_allowed=agg_df['date_created'].min(),
                max_date_allowed=agg_df['date_created'].max(),
                start_date=start_of_week,
                end_date=end_of_week
            )
        ], id='date-range-container', style={'display': 'block'}),

        dcc.Checklist(
            id='amount-check',
            options=[{'label': 'Show only entries with total amount > 60', 'value': 'over60'}],
            value=[],
            style={'marginTop': '10px'}
        ),

        html.H2("Amount earned by each individual for each day", style={'textAlign': 'center'}),

        dcc.RadioItems(
            id='sort-mode',
            options=[
                {'label': 'Sort by Date', 'value': 'date'},
                {'label': 'Sort by Amount (Descending)', 'value': 'amount_desc'},
                {'label': 'Sort by Amount (Ascending)', 'value': 'amount_asc'}
            ],
            value='date',
            labelStyle={'display': 'block'},
            style={'marginTop': '10px'}
        ),

        dash_table.DataTable(
            id='result-table',
            columns=[
                {'name': 'GMS ID', 'id': 'gms_id'},
                {'name': 'Names', 'id': 'name'},
                {'name': 'Date Created', 'id': 'date_created'},
                {'name': 'Total Amount', 'id': 'amount'},
            ],
            page_size=20,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{amount} > 60', 'column_id': 'amount'},
                    'backgroundColor': '#ffcccc',
                    'color': 'black'
                }
            ],
        ),

        html.Div(dcc.Graph(id='amount-bar-chart'), id='bar-chart-container', style={'display': 'none'}),

        html.H2("Total Amount Earned per individual for Selected Period", style={'textAlign': 'center'}),

        html.Div(dcc.Graph(id='amount-line-chart'), id='line-chart-container', style={'display': 'none'}),
    ])

    @app.callback(
        Output('date-single-container', 'style'),
        Output('date-range-container', 'style'),
        Input('date-mode', 'value')
    )
    def toggle_date_picker(mode):
        return ({'display': 'block'}, {'display': 'none'}) if mode == 'single' else ({'display': 'none'}, {'display': 'block'})

    @app.callback(
        Output('result-table', 'data'),
        Output('bar-chart-container', 'style'),
        Output('amount-bar-chart', 'figure'),
        Output('line-chart-container', 'style'),
        Output('amount-line-chart', 'figure'),
        Input('gmsid-filter', 'value'),
        Input('date-mode', 'value'),
        Input('date-single', 'date'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date'),
        Input('amount-check', 'value'),
        Input('sort-mode', 'value'),
    )
    def update_table_and_charts(selected_gmsids, date_mode, single_date, start_date, end_date, amount_filter, sort_mode):
        query = """
            SELECT gms_id, name, date_created, amount
            FROM wallet_data
            WHERE 1=1
        """
        params = []

        if selected_gmsids:
            placeholders = ','.join('?' for _ in selected_gmsids)
            query += f" AND gms_id IN ({placeholders})"
            params.extend(selected_gmsids)

        if date_mode == 'single' and single_date:
            query += " AND date_created = ?"
            params.append(single_date)
        elif date_mode == 'range':
            if start_date:
                query += " AND date_created >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date_created <= ?"
                params.append(end_date)

        conn = sqlite3.connect('wallet_data.db')
        filtered = pd.read_sql(query, conn, params=params)
        conn.close()

        if filtered.empty:
            return [], {'display': 'none'}, {}, {'display': 'none'}, {}

        filtered['date_created'] = pd.to_datetime(filtered['date_created']).dt.date

        if 'over60' in amount_filter:
            filtered = filtered[filtered['amount'] > 60]

        # Sort
        if sort_mode == 'date':
            filtered = filtered.sort_values(by=['date_created', 'gms_id'])
        else:
            filtered = filtered.sort_values(by='amount', ascending=(sort_mode == 'amount_asc'))

        # Table: group by gms_id + date_created, aggregate names as comma list
        grouped_table = filtered.groupby(['gms_id', 'date_created']) \
            .agg({'amount': 'sum', 'name': lambda x: ', '.join(sorted(set(x)))}) \
            .reset_index()

        table_data = grouped_table.to_dict('records')

        # Bar Chart: per gms_id + date_created
        bar_data = grouped_table.copy()
        bar_data['hover_text'] = bar_data['name']
        bar_data['label'] = bar_data['gms_id'].astype(str) + " (" + bar_data['date_created'].astype(str) + ")"

        bar_fig = px.bar(
            bar_data,
            x='label',
            y='amount',
            hover_name='hover_text',
            title='Total Amount per Individual (Group by Date)',
            labels={'label': 'GMS ID (Date)', 'amount': 'Total Amount'}
        ) if 'over60' in amount_filter else {}

        bar_style = {'display': 'block'} if 'over60' in amount_filter else {'display': 'none'}

        # Line Chart: per gms_id across period
        line_data = filtered.groupby(['gms_id']) \
            .agg({'amount': 'sum', 'name': lambda x: ', '.join(sorted(set(x)))}) \
            .reset_index()

        line_data['gms_id_name'] = line_data['gms_id'].astype(str)
        line_data['hover_text'] = line_data['name']

        line_fig = px.line(
            line_data,
            x='gms_id_name',
            y='amount',
            hover_name='hover_text',
            markers=True,
            title='Total Amount per GMS ID for Selected Period',
            labels={'gms_id_name': 'GMS ID', 'amount': 'Total Amount'}
        )

        return table_data, bar_style, bar_fig, {'display': 'block'}, line_fig

    return app
