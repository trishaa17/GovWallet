import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import requests
from io import StringIO


def create_dash_number_of_roles(server):
    url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EfFwqNRlqjdKgUnvBWe53SEBKKJA9yK7RomjADmwfuT6iQ?download=1"
    response = requests.get(url)
    response.raise_for_status()
    csv_data = response.content.decode('utf-8')
    df = pd.read_csv(StringIO(csv_data))
    df['date_created'] = pd.to_datetime(df['date_created'], utc=True)

    # Treat missing or empty role names as 'Others'
    df['gms_role_name'] = df['gms_role_name'].fillna('Others')
    df.loc[df['gms_role_name'].str.strip() == '', 'gms_role_name'] = 'Others'

    total_per_role = df.groupby('gms_role_name')['gms_id'].nunique().reset_index()
    total_per_role.rename(columns={'gms_id': 'total_unique_accounts'}, inplace=True)

    total_unique_people = df['gms_id'].nunique()


    app = Dash(__name__, server=server, routes_pathname_prefix='/appNumberOfRoles/')
    app.title = "Manpower Count Dashboard"

    # Get min and max dates from date_created column (as date only)
    min_date = df['date_created'].dt.date.min()
    max_date = df['date_created'].dt.date.max()

    app.layout = html.Div([
        html.H1("Manpower Count Dashboard", style={'textAlign': 'center'}),

        html.H2("Select Date Mode"),
        dcc.RadioItems(
            id='date-mode',
            options=[
                {'label': 'Single Date', 'value': 'single'},
                {'label': 'Date Range', 'value': 'range'}
            ],
            value='single',
            labelStyle={'display': 'inline-block', 'marginRight': '15px'}
        ),

        html.Div([
            dcc.DatePickerSingle(
                id='single-date-picker',
                min_date_allowed=min_date,
                max_date_allowed=max_date,
                placeholder='Select a date',
                display_format='YYYY-MM-DD',
            )
        ], id='single-date-container'),

        html.Div([
            dcc.DatePickerRange(
                id='range-date-picker',
                min_date_allowed=min_date,
                max_date_allowed=max_date,
                display_format='YYYY-MM-DD',
                start_date=min_date,
                end_date=max_date,
            )
        ], id='range-date-container', style={'display': 'none'}),

        html.H2("Filter by Registration Location"),
        dcc.Dropdown(
            id='location-filter',
            options=[{'label': loc, 'value': loc} for loc in sorted(df['registration_location_id'].dropna().unique())],
            multi=True,
            placeholder="Select one or more locations",
            value=[]  # default no filter, show all
        ),


        html.H2("Number of people working per role"),
        dcc.Graph(id='bar-chart'),

        html.H2("Total number of people working per role (All Dates)"),
        html.Ul([
            html.Li(f"{row['gms_role_name']}: {row['total_unique_accounts']} unique accounts")
            for _, row in total_per_role.iterrows()
        ]),
        html.H3(f"Total unique people (all roles): {total_unique_people}")

    ])

    # Toggle between single and range date pickers
    @app.callback(
        Output('single-date-container', 'style'),
        Output('range-date-container', 'style'),
        Input('date-mode', 'value')
    )
    def toggle_date_picker(mode):
        if mode == 'single':
            return {'display': 'block'}, {'display': 'none'}
        else:
            return {'display': 'none'}, {'display': 'block'}

    # Update bar chart based on date filter
    @app.callback(
        Output('bar-chart', 'figure'),
        Input('date-mode', 'value'),
        Input('single-date-picker', 'date'),
        Input('range-date-picker', 'start_date'),
        Input('range-date-picker', 'end_date'),
        Input('location-filter', 'value')  # new input for locations
    )
    def update_bar_chart(mode, single_date, start_date, end_date, selected_locations):
        filtered = df.copy()

        # Filter by registration_location_id if any selected
        if selected_locations:
            filtered = filtered[filtered['registration_location_id'].isin(selected_locations)]

        # Then filter by date mode
        if mode == 'single' and single_date:
            selected = pd.to_datetime(single_date).date()
            filtered = filtered[filtered['date_created'].dt.date == selected]
            if filtered.empty:
                return px.pie(title=f"No data for {selected}")
            title = f"Number of people working per role on {selected}"
        elif mode == 'range' and start_date and end_date:
            start = pd.to_datetime(start_date).date()
            end = pd.to_datetime(end_date).date()
            filtered = filtered[(filtered['date_created'].dt.date >= start) & (filtered['date_created'].dt.date <= end)]
            if filtered.empty:
                return px.pie(title=f"No data from {start} to {end}")
            title = f"Number of people working per role from {start} to {end}"
        else:
            title = "Number of people working per role (All Dates)"

        summary = (
            filtered.groupby('gms_role_name')['gms_id']
            .nunique().reset_index()
            .rename(columns={'gms_id': 'unique_accounts'})
        )

        fig = px.pie(
            summary,
            names='gms_role_name',
            values='unique_accounts',
            title=title,
            color='gms_role_name'
        )
        return fig


    return app
