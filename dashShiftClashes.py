import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, dash_table, Input, Output
import requests
from io import StringIO
import random




def generate_pastel_colors(n):
    import colorsys
    pastel_colors = []
    alpha = 0.4  # transparency

    for i in range(n):
        h = i / n
        s = 0.4
        v = 0.95
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        pastel_colors.append(f'rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, {alpha})')

    random.shuffle(pastel_colors)
    return pastel_colors

def detect_clashes_by_category(df, clash_categories):
    df['registration_location_id_lower'] = df['registration_location_id'].str.lower()
    clashes_by_category = {}

    for label, campaigns_to_check in clash_categories.items():
        clashing = []

        grouped = df.groupby(['gms_id', 'date_created'])
        for (gms_id, date), group in grouped:
            campaigns = set(group['registration_location_id_lower'])
            
            present_campaigns = campaigns.intersection(campaigns_to_check)
            if len(present_campaigns) >= 2:
                clash_rows = group[group['registration_location_id_lower'].isin(present_campaigns)]
                clashing.append(clash_rows)

        if clashing:
            clashes_by_category[label] = pd.concat(clashing).drop_duplicates()
        else:
            clashes_by_category[label] = pd.DataFrame(columns=df.columns)

    return clashes_by_category


def create_dash_shift_clashes(server):
    url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EfhI3QwOuY9LjQ1hrKQLEg0BNwneyp0l8Xhd4LAu-IOf8Q?download=1"
    response = requests.get(url)
    response.raise_for_status()
    csv_data = response.content.decode('utf-8')

    df = pd.read_csv(StringIO(csv_data), parse_dates=['date_created'])
    df['date_created'] = df['date_created'].dt.date

    not_allowed_clash_categories = {
        "Silent Hours AM": ("aqc_attendance_silent_hours_am", 
                            "wac_attendance_silent_hours_am", 
                            "khall_attendance_silent_hours_am", 
                            "sen_attendance_silent_hours_am", 
                            "airpt_attendance_silent_hours_am"),
        "AM": ("aqc_attendance_am",
               "wac_attendance_am",
                "khall_attendance_am",
                "itee_attendance_am",
                "nexus_attendance_am",
                "oth-attendance-am",
                "congr-attendance-am",
                "oc-attendance-am",
                "hotel1_attendance_am",
                "hotel2_attendance_am",
                "hotel3_attendance_am",
                "airpt-attendance-am"),
        "PM": ("aqc_attendance_pm",
               "wac_attendance_pm",
               "khall_attendance_pm",
               "itee_attendance_pm",
                "nexus_attendance_pm",
                "oth-attendance-pm",
                "congr-attendance-pm",
                "oc-attendance-pm",
                "hotel1_attendance_pm",
                "hotel2_attendance_pm",
                "hotel3_attendance_pm",
                "airpt-attendance-pm"),
        "Silent Hour 11pm - 7am": ("aqc_attendance_silent_hour_11pm_7am",
                                   "wac_attendance_silent_hour_11pm_7am",
                                   "khall_attendance_silent_hour_11pm_7am", 
                                   "airpt_attendance_silent_hour_11pm_7am"),
    }


    clash_dfs = detect_clashes_by_category(df, not_allowed_clash_categories)

    app = Dash(__name__, server=server, routes_pathname_prefix='/appShiftClashes/')
    app.title = "GovWallet Shift Timing Clashes"

    min_date = min(df['date_created'])
    max_date = max(df['date_created'])

    app.layout = html.Div([
        html.H1("GovWallet Shift Timing Clashes", style={'textAlign': 'center'}),

        dcc.DatePickerRange(
            id='date-range-clashes',
            min_date_allowed=min_date,
            max_date_allowed=max_date,
            start_date=min_date,
            end_date=max_date,
            display_format='YYYY-MM-DD'
        ),

        html.Div([
            html.Label("Filter by GMS ID:"),
            dcc.Dropdown(id='filter-gms-id', options=[], multi=True, placeholder='Select GMS ID(s)'),

            html.Label("Filter by Name:", style={'marginLeft': '20px'}),
            dcc.Dropdown(id='filter-name', options=[], multi=True, placeholder='Select Name(s)'),

            html.Label("Filter by Registration Location ID:", style={'marginLeft': '20px'}),
            dcc.Dropdown(id='filter-location-id', options=[], multi=True, placeholder='Select Location ID(s)'),
        ], style={'marginTop': '20px', 'marginBottom': '20px'}),



        html.Div(id='clash-summary-chart'),

        html.Label("Select Clash Shift Timing to View Details:", style = {'fontWeight': 'bold'}),
        dcc.Dropdown(id='category-dropdown', placeholder='Select a clashing shift timing'),

        html.Div(id='category-table'),

        html.Label("Key: View Campaigns for Selected Clash Timing:", style = {'fontWeight': 'bold'}),
        dcc.Dropdown(
            id='category-key-dropdown',
            options=[{'label': key, 'value': key} for key in not_allowed_clash_categories.keys()],
            placeholder='Select a category to view its campaign key',
            style={'marginBottom': '10px'}
        ),
        html.Div(id='category-key-display')
    ])

    @app.callback(
        Output('filter-gms-id', 'options'),
        Output('filter-name', 'options'),
        Output('filter-location-id', 'options'),
        Input('date-range-clashes', 'start_date'),
        Input('date-range-clashes', 'end_date'),
    )
    def update_filter_options(start_date, end_date):
        start = pd.to_datetime(start_date).date()
        end = pd.to_datetime(end_date).date()

        # Combine all clash_dfs into one for dropdown values
        all_data = pd.concat([df[(df['date_created'] >= start) & (df['date_created'] <= end)] for df in clash_dfs.values()])

        gms_options = [{'label': x, 'value': x} for x in sorted(all_data['gms_id'].dropna().unique())]
        name_options = [{'label': x, 'value': x} for x in sorted(all_data['name'].dropna().unique())]
        loc_options = [{'label': x, 'value': x} for x in sorted(all_data['registration_location_id'].dropna().unique())]

        return gms_options, name_options, loc_options


    @app.callback(
        Output('clash-summary-chart', 'children'),
        Output('category-dropdown', 'options'),
        Output('category-dropdown', 'value'), 
        Input('date-range-clashes', 'start_date'),
        Input('date-range-clashes', 'end_date'),
        Input('filter-gms-id', 'value'),
        Input('filter-name', 'value'),
        Input('filter-location-id', 'value'),
    )
    def update_clashes(start_date, end_date, gms_id_filter, name_filter, loc_id_filter):
        start = pd.to_datetime(start_date).date()
        end = pd.to_datetime(end_date).date()

        filtered_clash_dfs = {}
        summary_data = []

        for label, df_clash in clash_dfs.items():
            df_filtered = df_clash[(df_clash['date_created'] >= start) & (df_clash['date_created'] <= end)]

            # Apply additional filters
            if gms_id_filter:
                df_filtered = df_filtered[df_filtered['gms_id'].isin(gms_id_filter)]
            if name_filter:
                df_filtered = df_filtered[df_filtered['name'].isin(name_filter)]
            if loc_id_filter:
                df_filtered = df_filtered[df_filtered['registration_location_id'].isin(loc_id_filter)]

            filtered_clash_dfs[label] = df_filtered
            unique_person_dates = df_filtered.groupby(['gms_id', 'date_created']).ngroups
            summary_data.append({'category': label, 'clash_count': unique_person_dates})

        app.filtered_clash_dfs = filtered_clash_dfs

        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('clash_count', ascending=True)

        if summary_df['clash_count'].sum() == 0:
            bar_fig = px.bar(title="No clashes found in selected date range and filters.")
        else:
            bar_fig = px.bar(
                summary_df,
                x='clash_count',
                y='category',
                orientation='h',
                title='Number of Clashes by Shift Timing',
                labels={'category': 'Clashing Shift Timing', 'clash_count': 'Number of Clashes'},
                color='clash_count',
                color_continuous_scale='Inferno'
            )

        dropdown_options = [{"label": label, "value": label} for label in filtered_clash_dfs.keys()]
        default_value = dropdown_options[0]["value"] if dropdown_options else None

        return dcc.Graph(figure=bar_fig), dropdown_options, default_value


    @app.callback(
        Output('category-table', 'children'),
        Input('category-dropdown', 'value')
    )
    def update_category_table(selected_category):
        if not selected_category or selected_category not in app.filtered_clash_dfs:
            return html.Div("No data available.")

        df_filtered = app.filtered_clash_dfs[selected_category]

        if df_filtered.empty:
            return html.Div(
                "No clashes found for the selected shift timing.",
                style={
                    'textAlign': 'center',
                    'fontWeight': 'bold',
                    'paddingTop': '20px',
                    'paddingBottom': '20px'
                }
            )


        unique_groups = df_filtered[['gms_id', 'date_created']].drop_duplicates().reset_index(drop=True)
        colors = generate_pastel_colors(len(unique_groups))
        color_map = {
            (row['gms_id'], row['date_created']): colors[i]
            for i, row in unique_groups.iterrows()
        }

        style_data_conditional = [
            {
                'if': {
                    'filter_query': f'{{gms_id}} = "{gms_id}" && {{date_created}} = "{date_created}"',
                },
                'backgroundColor': color,
                'color': 'black',
            }
            for (gms_id, date_created), color in color_map.items()
        ]

        return dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in [
                "gms_id", "name", "date_created", "registration_location_id",
                "approval_final_status", "amount", "approval_final_remarks", "wallet_status"
            ] if i in df_filtered.columns],
            data=df_filtered.to_dict('records'),
            style_table={'overflowX': 'auto', 'marginBottom': '30px'},
            style_cell={'textAlign': 'left'},
            style_data_conditional=style_data_conditional,
            page_size=10,
            style_header={'fontWeight': 'bold'},
        )

    @app.callback(
        Output('category-key-display', 'children'),
        Input('category-key-dropdown', 'value')
    )
    def display_category_key(selected_key):
        if not selected_key:
            return html.Div()

        campaigns = not_allowed_clash_categories.get(selected_key, [])
        return html.Div([
            html.B(f"{selected_key} includes the following campaigns:"),
            html.Ul([html.Li(campaign) for campaign in campaigns]),
        ], style={
            'marginTop': '10px',
            'padding': '10px',
            'border': '1px solid #ccc',
            'borderRadius': '5px',
            'backgroundColor': '#f9f9f9'
        })


    return app
