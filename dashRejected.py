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
        # Header
        html.Div([
            html.H1("Rejection Rate Dashboard", 
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
        
        # Main content container
        html.Div([
            # Filters section
            html.Div([
                # Left-side filters: Role and Campaign
                html.Div([
                    dcc.Dropdown(
                        id='role-filter',
                        options=[{'label': r, 'value': r} for r in sorted(df['gms_role_name'].dropna().unique())],
                        placeholder="Select Role(s)",
                        multi=True,
                        style={
                            'width': '280px',
                            'marginBottom': '10px',
                            'fontSize': '14px'
                        }
                    ),
                    dcc.Dropdown(
                        id='campaign-filter',
                        options=[{'label': c, 'value': c} for c in sorted(df['registration_location_id'].dropna().unique())],
                        placeholder="Select Campaign(s)",
                        multi=True,
                        style={
                            'width': '280px',
                            'fontSize': '14px'
                        }
                    )
                ], style={'flex': '1'}),
                
                # Right-side: Date range
                html.Div([
                    dcc.DatePickerRange(
                        id='date-filter',
                        min_date_allowed=df['payout_date'].min(),
                        max_date_allowed=df['payout_date'].max(),
                        start_date=df['payout_date'].min(),
                        end_date=df['payout_date'].max(),
                        display_format='DD/MM/YYYY',
                        with_portal=True,
                        clearable=True
                    )
                ], style={
                    'flex': '1',
                    'display': 'flex',
                    'justifyContent': 'flex-end'
                })
            ], style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'flex-start',
                'margin': '20px 40px'
            }),
            
            # Graph section
            html.Div([
                dcc.Graph(id='rejection-pie')
            ], style={
                'margin': '20px 40px',
                'backgroundColor': '#E6E8EC',
                'padding': '20px',
                'borderRadius': '8px'
            }),


            dash_table.DataTable(
                id='summary-table',
                columns=[],
                data=[],
                page_size=20,
                style_table={
                    'overflowX': 'auto',
                    'border': '1px solid #e5e7eb',
                    'borderRadius': '8px'
                },
                sort_action='native',
                style_header={
                    'backgroundColor': "#c4b8fa",
                    'fontWeight': '600',
                    'fontSize': '14px',
                    'color': '#374151',
                    'border': '1px solid #e5e7eb',
                    'textAlign': 'center'
                },
                style_cell={
                    'textAlign': 'center',
                    'padding': '12px',
                    'fontSize': '14px',
                    'color': '#374151',
                    'border': '1px solid #e5e7eb'
                },
                style_data={
                    'backgroundColor': '#F1F1F1FF',
                    'border': '1px solid #e5e7eb'
                },
                style_data_conditional=[]  # Filled in by callback
            )

        ], style={'padding': '0 20px 40px'})
        
    ], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f3f4f6', 'minHeight': '100vh'})


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

        fig = px.pie(
            status_counts,
            values='count',
            names='approval_final_status',
            title='Rejection vs Acceptance Rate',
            color='approval_final_status',
            color_discrete_map={
                'approved': "#a1eea1",   # pastel green
                'rejected': "#f5847e"    # pastel red
            }
        )

        fig.update_layout(
            title={'x': 0.5},  # Center title
            paper_bgcolor='#E6E8EC'  # Background for the pie chart container
        )


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
                'if': {'row_index': 'odd'},
                'backgroundColor': '#ddd6fe'
            },
            {
                'if': {
                    'filter_query': '{Rejection Rate} > 50',
                    'column_id': 'Rejection Rate'
                },

                'color': "#c25c5c",  # deeper red font
                'fontWeight': '600'
            }
        ]


        return fig, columns, data, style_conditional

    return app
