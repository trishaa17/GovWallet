import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table

# Load your CSV file
df = pd.read_csv(r"C:\Users\User\WORLD AQUATICS CHAMPIONSHIPS SINGAPORE PTE. LTD\WORLD AQUATICS CHAMPIONSHIPS SINGAPORE PTE. LTD - Technology & Innovation\Ewallet\govwallet_data.csv")

# Convert payout_date to datetime
df['payout_date'] = pd.to_datetime(df['payout_date'])

# Aggregate max amount per volunteer per payout_date
agg_df = df.groupby(['name', 'payout_date'], as_index=False)['amount'].max()

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Volunteer Max Credits Dashboard"),

    dcc.Dropdown(
        id='name-filter',
        options=[{'label': n, 'value': n} for n in sorted(df['name'].unique())],
        placeholder="Select Volunteer Name(s)",
        multi=True
    ),

    dcc.DatePickerRange(
        id='date-filter',
        min_date_allowed=df['payout_date'].min(),
        max_date_allowed=df['payout_date'].max(),
        start_date=df['payout_date'].min(),
        end_date=df['payout_date'].max(),
    ),

    dcc.Checklist(
        id='amount-check',
        options=[{'label': 'Show only entries with amount > 60', 'value': 'over60'}],
        value=[],
        style={'marginTop': '10px'}
    ),

    dash_table.DataTable(
        id='result-table',
        columns=[
            {'name': 'Name', 'id': 'name'},
            {'name': 'Payout Date', 'id': 'payout_date'},
            {'name': 'Max Amount', 'id': 'amount', 'type': 'numeric'},
        ],
        page_size=15,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{amount} > 60',
                    'column_id': 'amount'
                },
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
    Input('amount-check', 'value')
)
def update_table_and_chart(selected_names, start_date, end_date, amount_filter):
    filtered = agg_df.copy()

    if selected_names:
        filtered = filtered[filtered['name'].isin(selected_names)]

    if start_date:
        filtered = filtered[filtered['payout_date'] >= start_date]

    if end_date:
        filtered = filtered[filtered['payout_date'] <= end_date]

    if 'over60' in amount_filter:
        filtered = filtered[filtered['amount'] > 60]

    filtered['payout_date'] = filtered['payout_date'].dt.strftime('%Y-%m-%d')

    table_data = filtered.to_dict('records')

    if filtered.empty:
        fig = px.bar(title="No data to display")
    else:
        fig = px.bar(
            filtered,
            x='payout_date',
            y='amount',
            color='name',
            barmode='group',
            labels={
                'payout_date': 'Payout Date',
                'amount': 'Max Amount',
                'name': 'Volunteer Name'
            },
            title='Max Amount per Volunteer per Day'
        )
        fig.update_xaxes(type='category')

    return table_data, fig


if __name__ == '__main__':
    app.run(debug=True)
