# prepare_data.py
import pandas as pd
import sqlite3
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table
import requests
from io import StringIO


def create_dash2(server):
    url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EdyAJaCQLpFAp3JTaMCmK_8BkXS81I50q0dg7t5bDrsSEg?download=1"
    response = requests.get(url)
    response.raise_for_status()
    csv_data = response.content.decode('utf-8')
    df = pd.read_csv(StringIO(csv_data))

    df['payout_date'] = pd.to_datetime(df['payout_date']).dt.date

    # Compute max amount per volunteer per date
    agg_df = df.groupby(['name', 'payout_date'], as_index=False)['amount'].max()

    # Save to SQLite
    conn = sqlite3.connect('wallet_data.db')
    agg_df.to_sql('wallet_data', conn, if_exists='replace', index=False)
    conn.close()

    print("Database created successfully.")

    app = Dash(__name__)

    app.layout = html.Div([
        html.H1("Volunteer Max Credits Dashboard"),

        dcc.Dropdown(
            id='name-filter',
            options=[{'label': n, 'value': n} for n in sorted(meta_df['name'].unique())],
            placeholder="Select Volunteer Name(s)",
            multi=True
        ),

        dcc.DatePickerRange(
            id='date-filter',
            min_date_allowed=meta_df['payout_date'].min(),
            max_date_allowed=meta_df['payout_date'].max(),
            start_date=meta_df['payout_date'].min(),
            end_date=meta_df['payout_date'].max(),
        ),

        dcc.Checklist(
            id='amount-check',
            options=[{'label': 'Show only entries with amount > 60', 'value': 'over60'}],
            value=[],
            style={'marginTop': '10px'}
        ),

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
                {'name': 'Name', 'id': 'name'},
                {'name': 'Payout Date', 'id': 'payout_date'},
                {'name': 'Max Amount', 'id': 'amount'},
            ],
            page_size=15,
            virtualization=True,
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

        dcc.Graph(id='amount-bar-chart'),
    ])


    @app.callback(
        Output('result-table', 'data'),
        Output('amount-bar-chart', 'figure'),
        Input('name-filter', 'value'),
        Input('date-filter', 'start_date'),
        Input('date-filter', 'end_date'),
        Input('amount-check', 'value'),
        Input('sort-mode', 'value')
    )
    def update_table_and_chart(selected_names, start_date, end_date, amount_filter, sort_mode):
        query = "SELECT name, payout_date, amount FROM wallet_data WHERE 1=1"
        params = []

        if selected_names:
            placeholders = ','.join('?' for _ in selected_names)
            query += f" AND name IN ({placeholders})"
            params.extend(selected_names)

        if start_date:
            query += " AND payout_date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND payout_date <= ?"
            params.append(end_date)

        if 'over60' in amount_filter:
            query += " AND amount > 60"

        conn = sqlite3.connect('wallet_data.db')
        filtered = pd.read_sql(query, conn, params=params)
        conn.close()

        if filtered.empty:
            return [], px.bar(title="No data to display")

        # Table sorting
        table_data = filtered.sort_values(by='amount', ascending=(sort_mode == 'amount_asc')).to_dict('records')

        # Chart sorting logic
        if sort_mode == 'date':
            filtered = filtered.sort_values(by=['payout_date', 'name'])
            x_col = 'payout_date'
            fig = px.bar(
                filtered,
                x=x_col,
                y='amount',
                color='name',
                barmode='group',
                labels={'payout_date': 'Payout Date', 'amount': 'Amount'},
                title='Amount per Volunteer per Day (Sorted by Date)'
            )
        else:
            ascending = (sort_mode == 'amount_asc')
            filtered['label'] = filtered['payout_date'] + ' - ' + filtered['name']
            filtered = filtered.sort_values(by='amount', ascending=ascending)
            fig = px.bar(
                filtered,
                x='label',
                y='amount',
                color='name',
                labels={'label': 'Date - Name', 'amount': 'Amount'},
                title='Amount per Volunteer per Day (Sorted by Amount)'
            )
            fig.update_layout(
                xaxis={'categoryorder': 'array', 'categoryarray': filtered['label'].tolist()}
            )

        return table_data, fig
    return app 
