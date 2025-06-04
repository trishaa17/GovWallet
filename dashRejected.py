import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table
import requests
from io import StringIO
from loadcsv import load_csv_data

def create_dash_rejection_rate(server):
    # url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EfFwqNRlqjdKgUnvBWe53SEBKKJA9yK7RomjADmwfuT6iQ?download=1"
    # response = requests.get(url)
    # response.raise_for_status()
    # csv_data = response.content.decode('utf-8')
    # df = pd.read_csv(StringIO(csv_data))

    df = load_csv_data()

    df['payout_date'] = pd.to_datetime(df['payout_date']).dt.date
    df['wallet_status'] = df['wallet_status'].str.lower()
    df['gms_role_name'] = df['gms_role_name'].fillna('Unknown Role')
    df['registration_location_id'] = df['registration_location_id'].fillna('Unknown Campaign')


    app = Dash(__name__, server=server, url_base_pathname='/appRejectionRate/')

    app.layout = html.Div([
        html.H1("Rejection Rate Dashboard"),

        dcc.DatePickerRange(
            id='date-filter',
            min_date_allowed=df['payout_date'].min(),
            max_date_allowed=df['payout_date'].max(),
            start_date=df['payout_date'].min(),
            end_date=df['payout_date'].max()
        ),

        dcc.Dropdown(
            id='role-filter',
            options=[{'label': r, 'value': r} for r in sorted(df['gms_role_name'].dropna().unique())],
            placeholder="Select Role(s)",
            multi=True
        ),

        dcc.Dropdown(
            id='campaign-filter',
            options=[{'label': c, 'value': c} for c in sorted(df['registration_location_id'].dropna().unique())],
            placeholder="Select Campaign(s)",
            multi=True
        ),

        dcc.Graph(id='rejection-pie'),

        
        html.H3("Rejection/Success Summary by Role and Campaign"),
        dash_table.DataTable(
            id='summary-table',
            columns=[],
            data=[],
            style_table={'overflowX': 'auto'},
            sort_action='native',
            style_cell={'textAlign': 'center', 'padding': '5px'},
            style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
            style_data_conditional=[]  # will be filled in callback
        )
    ])

    @app.callback(
        Output('rejection-pie', 'figure'),
        Output('summary-table', 'columns'),
        Output('summary-table', 'data'),
        Output('summary-table', 'style_data_conditional'),
        Input('date-filter', 'start_date'),
        Input('date-filter', 'end_date'),
        Input('role-filter', 'value'),
        Input('campaign-filter', 'value'),

    )
    def update_dashboard(start_date, end_date, selected_roles, selected_campaigns):

        filtered = df.copy()

        if start_date:
            filtered = filtered[filtered['payout_date'] >= pd.to_datetime(start_date).date()]
        if end_date:
            filtered = filtered[filtered['payout_date'] <= pd.to_datetime(end_date).date()]
        if selected_roles:
            filtered = filtered[filtered['gms_role_name'].isin(selected_roles)]
        if selected_campaigns:
            filtered = filtered[filtered['registration_location_id'].isin(selected_campaigns)]

        # Pie chart
        status_counts = filtered['approval_final_status'].value_counts().reset_index()
        status_counts.columns = ['approval_final_status', 'count']
        print(status_counts)

        fig = px.pie(status_counts, values='count', names='approval_final_status',
                     title='Rejection vs Acceptance Rate',
                     color_discrete_map={'approved': 'green', 'rejected': 'red'})

        # Summary table
        summary = (
            filtered.groupby(['gms_role_name', 'registration_location_id', 'approval_final_status'])
            .size()
            .reset_index(name='count')
        )

        summary_pivot = (
            summary.pivot_table(index=['gms_role_name', 'registration_location_id'],
                                columns='approval_final_status',
                                values='count',
                                fill_value=0)
            .reset_index()
        )

        summary_pivot.columns.name = None
        summary_pivot['Total'] = summary_pivot.get('approved', 0) + summary_pivot.get('rejected', 0)
        summary_pivot['Rejection Rate'] = round((summary_pivot.get('rejected', 0) / summary_pivot['Total']) * 100, 2)
        summary_pivot['Rejection Rate'] = summary_pivot['Rejection Rate'].fillna(0.00)


        columns = [
            {'name': 'Index', 'id': 'Index'},
            {'name': 'Role', 'id': 'gms_role_name'},
            {'name': 'Campaign', 'id': 'registration_location_id'},
            {'name': 'Approved Count', 'id': 'approved'},
            {'name': 'Rejected Count', 'id': 'rejected'},
            {'name': 'Total Submissions', 'id': 'Total'},
            {'name': 'Rejection Rate (%)', 'id': 'Rejection Rate'},
        ]

        data = summary_pivot.to_dict('records')


        # Add index column
        summary_pivot.insert(0, 'Index', range(1, len(summary_pivot) + 1))

        # Calculate total row
        total_approved = summary_pivot.get('approved', pd.Series(dtype=float)).sum()
        total_rejected = summary_pivot.get('rejected', pd.Series(dtype=float)).sum()
        grand_total = summary_pivot['Total'].sum()
        overall_rejection_rate = round((total_rejected / grand_total) * 100, 2) if grand_total else 0.00

        summary_row = {
            'Index': '—',
            'gms_role_name': 'Total',
            'registration_location_id': '',
            'approved': total_approved,
            'rejected': total_rejected,
            'Total': grand_total,
            'Rejection Rate': overall_rejection_rate
        }

        data = summary_pivot.to_dict('records')
        data.append(summary_row)

        # Update column definitions
        columns = [
            {'name': 'Index', 'id': 'Index'},
            {'name': 'Role', 'id': 'gms_role_name'},
            {'name': 'Campaign', 'id': 'registration_location_id'},
            {'name': 'Approved Count', 'id': 'approved'},
            {'name': 'Rejected Count', 'id': 'rejected'},
            {'name': 'Total Submissions', 'id': 'Total'},
            {'name': 'Rejection Rate (%)', 'id': 'Rejection Rate'},
        ]

        # Highlight rows where rejection rate > 50%
        style_conditional = [
            {
                'if': {
                    'filter_query': '{Rejection Rate} > 50',
                    'column_id': 'Rejection Rate'
                },
                'backgroundColor': '#ffcccc',
                'color': 'red',
                'fontWeight': 'bold'
            }
        ]

        return fig, columns, data, style_conditional

    return app
