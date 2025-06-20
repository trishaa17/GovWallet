import sqlite3
import plotly.express as px
import pandas as pd
from dash import Dash, dcc, html, Input, Output, dash_table
# import requests
# from io import StringIO
from datetime import datetime, date, timedelta
from loadcsv import load_csv_data

def create_dash_individual_amount(server):
    # url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EfFwqNRlqjdKgUnvBWe53SEBKKJA9yK7RomjADmwfuT6iQ?download=1"
    # response = requests.get(url)
    # response.raise_for_status()
    # csv_data = response.content.decode('utf-8')
    # df = pd.read_csv(StringIO(csv_data))

    df = load_csv_data()

    df = df[df['approval_stage'] == 'completed']
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
        # Header
        html.Div([
            html.H1("Individual Disbursement Dashboard", 
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
            # Top controls section
            html.Div([
                # Left side - GMS ID dropdown and checkbox
                html.Div([
                    dcc.Dropdown(
                        id='gmsid-filter',
                        options=[
                            {'label': str(gms_id), 'value': gms_id}
                            for gms_id in sorted(df['gms_id'].unique())
                        ],
                        placeholder="Select GMS ID(s)",
                        multi=True,
                        style={
                            'width': '300px',
                            'fontSize': '14px'
                        }
                    ),
                    # Checkbox filter moved here
                    html.Div([
                        dcc.Checklist(
                            id='amount-check',
                            options=[{'label': 'Show only entries with total amount > 60', 'value': 'over60'}],
                            value=[],
                            style={
                                'marginTop': '10px',
                                'fontSize': '14px',
                                'color': '#374151'
                            }
                        )
                    ])
                ], style={'flex': '1'}),
                
                # Right side - Date controls
                html.Div([
                    # Date mode radio buttons
                    dcc.RadioItems(
                        id='date-mode',
                        options=[
                            {'label': 'Single Date', 'value': 'single'},
                            {'label': 'Date Range', 'value': 'range'}
                        ],
                        value='range',
                        labelStyle={
                            'display': 'inline-block', 
                            'marginRight': '15px',
                            'fontSize': '14px',
                            'color': '#6b7280'
                        },
                        style={'marginBottom': '10px'}
                    ),
                    
                    # Date pickers container
                    html.Div([
                        # Single date picker
                        html.Div([
                            dcc.DatePickerSingle(
                                id='date-single',
                                min_date_allowed=agg_df['date_created'].min(),
                                max_date_allowed=agg_df['date_created'].max(),
                                date=today,
                                display_format='DD/MM/YYYY', 
                                clearable=True,
                                with_portal=True
                            )
                        ], id='date-single-container', style={'display': 'none'}),
                        
                        
                        # Date range picker
                        html.Div([
                            dcc.DatePickerRange(
                                id='date-range',
                                min_date_allowed=agg_df['date_created'].min(),
                                max_date_allowed=agg_df['date_created'].max(),
                                start_date=start_of_week,
                                end_date=end_of_week,
                                display_format='DD/MM/YYYY',  # matches the screenshot
                                clearable=True,
                                with_portal=True
                            )

                        ], id='date-range-container', style={'display': 'block'})
                    ])
                ], style={
                    'display': 'flex',
                    'flexDirection': 'column',
                    'alignItems': 'flex-end'
                })
            ], style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'flex-start',
                'marginBottom': '20px',
                'padding': '0 20px'
            }),
            
            # Table section
            html.Div([
                html.H2("Amount earned by each individual for each day", 
                    style={
                        'textAlign': 'center',
                        'fontSize': '18px',
                        'fontWeight': '600',
                        'color': '#1f2937',
                        'marginBottom': '20px'
                    }),
                
                dash_table.DataTable(
                    id='result-table',
                    columns=[
                        {'name': 'GMS ID', 'id': 'gms_id'},
                        {'name': 'Names', 'id': 'name'},
                        {'name': 'Date Created', 'id': 'date_created'},
                        {'name': 'Total Amount', 'id': 'amount'},
                    ],
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
                            'if': {'filter_query': '{amount} > 60', 'column_id': 'amount'},
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
            
            # Bar chart container 
            html.Div([
                html.H2("Total Amount Earned per individual for Selected Period", 
                    style={
                        'textAlign': 'center',
                        'fontSize': '18px',
                        'fontWeight': '600',
                        'color': '#1f2937',
                        'marginBottom': '20px'
                    }),
                
                dcc.Graph(
                    id='amount-bar-chart',
                    config={
                        'displayModeBar': False,
                        'plotlyServerURL': "https://chart-studio.plotly.com"
                    },
                    style={'height': '300px'},
                    figure={
                        'data': [],
                        'layout': {
                            'plot_bgcolor': 'rgba(0,0,0,0)',
                            'paper_bgcolor': 'rgba(0,0,0,0)',
                            'colorway': ['#5A6ACF']
                        }
                    }
                )
            ], id='bar-chart-container', 
            style={
                'display': 'none',
                'padding': '0 20px',
                'marginBottom': '40px'  
            }),
            
            # Line chart section
            html.Div([
                html.H2("Total Amount Earned per individual for Selected Period", 
                    style={
                        'textAlign': 'center',
                        'fontSize': '18px',
                        'fontWeight': '600',
                        'color': '#1f2937',
                        'marginBottom': '20px'
                    }),
                
                html.Div(dcc.Graph(
                    id='amount-line-chart',
                    config={'displayModeBar': False},
                    style={'height': '300px'}
                ), id='line-chart-container', style={'display': 'none'})
            ], style={
                'padding': '0 20px',
                'marginBottom': '40px'
            })
            
        ], style={
            'padding': '30px 20px',
            'backgroundColor': '#ffffff',
            'minHeight': 'calc(100vh - 80px)'
        })
        
    ], style={
        'backgroundImage': 'url("https://images.unsplash.com/photo-1454117096348-e4abbeba002c?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")',
        'backgroundSize': 'cover',
        'backgroundRepeat': 'no-repeat',
        'backgroundAttachment': 'fixed', 
        'backgroundPosition': 'center',
        'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
    })

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
    )
    def update_table_and_charts(selected_gmsids, date_mode, single_date, start_date, end_date, amount_filter):
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

        if bar_fig:
            bar_fig.update_traces(marker_color='#5A6ACF')
            bar_fig.update_layout(
                plot_bgcolor='#E6E8EC',
                paper_bgcolor='#E6E8EC'
            )


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

        line_fig.update_traces(line_color='#5A6ACF', marker=dict(color='#5A6ACF'))
        line_fig.update_layout(
            plot_bgcolor='#E6E8EC',
            paper_bgcolor='#E6E8EC'
        )


        return table_data, bar_style, bar_fig, {'display': 'block'}, line_fig

    return app
