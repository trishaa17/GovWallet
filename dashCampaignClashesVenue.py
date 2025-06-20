import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, dash_table, Input, Output
import requests
from io import StringIO
import random
from datetime import date, timedelta
from loadcsv import load_csv_data
from dash import State

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
    # Helper to normalize campaign names
    def normalize_campaign_name(c):
        return c.lower().replace('_', ' ').replace('-', ' ')

    df = df.copy()
    df['normalized_loc'] = df['registration_location_id'].str.lower().str.replace('[-_]', ' ', regex=True)

    clashes_by_category = {}

    # Track all known campaigns to exclude for "Other clashes"
    known_campaigns_set = set()
    for campaigns_to_check in clash_categories.values():
        known_campaigns_set.update(normalize_campaign_name(c) for c in campaigns_to_check)

    # Group once
    grouped = df.groupby(['gms_id', 'date_created'])

    # To track which groups were already classified under any category
    classified_groups = set()

    # First pass: check for specific clash categories
    for label, campaigns_to_check in clash_categories.items():
        clashing = []
        campaigns_to_check_norm = set(normalize_campaign_name(c) for c in campaigns_to_check)

        for (gms_id, date_created), group in grouped:
            group_key = (gms_id, date_created)

            campaigns_in_group = set(group['normalized_loc'])

            present_silent = {camp for camp in campaigns_in_group if camp.endswith(" silent hours am")}
            present_am = {camp for camp in campaigns_in_group if camp.endswith(" am") and not camp.endswith(" silent hours am")}

            if present_silent and present_am:
                all_present = present_silent.union(present_am)

                # Check if all present campaigns are in this category
                if all(camp in campaigns_to_check_norm for camp in all_present):
                    clash_rows = group[group['normalized_loc'].isin(all_present)]
                    clashing.append(clash_rows)
                    classified_groups.add(group_key)

        if clashing:
            clashes_by_category[label] = pd.concat(clashing).drop_duplicates()
        else:
            clashes_by_category[label] = pd.DataFrame(columns=df.columns)

    # Second pass: "Other clashes"
    clashing_other = []
    for (gms_id, date_created), group in grouped:
        group_key = (gms_id, date_created)
        if group_key in classified_groups:
            continue  # already assigned to a known category

        campaigns_in_group = set(group['normalized_loc'])
        present_silent = {camp for camp in campaigns_in_group if camp.endswith(" silent hours am")}
        present_am = {camp for camp in campaigns_in_group if camp.endswith(" am") and not camp.endswith(" silent hours am")}

        if present_silent and present_am:
            all_present = present_silent.union(present_am)
            clash_rows = group[group['normalized_loc'].isin(all_present)]
            clashing_other.append(clash_rows)

    if clashing_other:
        clashes_by_category["Other clashes"] = pd.concat(clashing_other).drop_duplicates()
    else:
        clashes_by_category["Other clashes"] = pd.DataFrame(columns=df.columns)

    return clashes_by_category



def create_dash_campaign_clashes_venue(server):
    url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EXMm4it_HQtPiiDnLuS4iWQB_QX4KRWYNExsu-yRGrK0bg?download=1"
    response = requests.get(url)
    response.raise_for_status()
    csv_data = response.content.decode('utf-8')

    df = pd.read_csv(StringIO(csv_data))
    df['date_created'] = pd.to_datetime(df['date_created'], utc=True)
    df['date_created'] = df['date_created'].dt.date
    df = df[df['approval_final_status'].str.lower() == 'pending']

    not_allowed_clash_categories = {
        "AQC clashes": ("aqc_attendance_am", "aqc_attendance_silent_hours_am"),
        "WAC clashes": ("wac_attendance_am", "wac_attendance_silent_hours_am"),
        "Khall clashes": ("khall_attendance_am", "khall_attendance_silent_hours_am"),
        "Airpt clashes": ("airpt_attendance_am", "airpt_attendance_silent_hours_am", "airpt-attendance-am"),
    }


    clash_dfs = detect_clashes_by_category(df, not_allowed_clash_categories)

    app = Dash(__name__, server=server, routes_pathname_prefix='/appCampaignClashesVenue/')
    app.title = "GovWallet Campaign Clashes"

    min_date = min(df['date_created'])
    max_date = max(df['date_created'])

    today = date.today()
    this_monday = today - timedelta(days=today.weekday())  # Monday
    this_sunday = this_monday + timedelta(days=6) 

    section_style = {
        'backgroundColor': '#E6E8EC',
        'padding': '20px',
        'borderRadius': '10px',
        'marginBottom': '30px',
        'boxShadow': '0 2px 6px rgba(0,0,0,0.05)'
    }

    app.layout = html.Div([
        # Header
        html.Div([
            html.H1("GovWallet Campaign Clashes (Venue Manager Version)",
                    style={
                        'margin': '0',
                        'fontSize': '24px',
                        'fontWeight': '600',
                        'color': '#1f2937',
                        'textAlign': 'center'
                    })
        ], style={
            'padding': '20px 40px',
            'backgroundColor': '#ffffff',
            'borderBottom': '1px solid #e5e7eb'
        }),

        # Main content
        html.Div([
            html.Div([
                # Date Picker on the left
                html.Div([
                    dcc.DatePickerRange(
                        id='date-range-clashes',
                        min_date_allowed=min_date,
                        max_date_allowed=max_date,
                        start_date=this_monday,
                        end_date=this_sunday,
                        display_format='YYYY-MM-DD',
                        clearable=True,
                        with_portal=True,
                        style={'fontSize': '14px'}
                    )
                ]),
                
                # Filter Button and Dropdown on the right
                html.Div([
                    html.Button([
                        html.Img(
                            src="https://static.thenounproject.com/png/247545-200.png",
                            style={'width': '20px', 'height': '20px'}
                        )
                    ],
                    id='filter-toggle-btn',
                    style={
                        'backgroundColor': "#C1C7D2",
                        'border': 'none',
                        'borderRadius': '50%',
                        'width': '36px',
                        'height': '36px',
                        'cursor': 'pointer',
                        'display': 'flex',
                        'alignItems': 'center',
                        'justifyContent': 'center',
                        'transition': 'all 0.2s ease',
                        'boxShadow': '0 2px 6px rgba(0,0,0,0.15)'
                    }),

                    html.Div([
                        html.Label("Filter by GMS ID:", style={'fontWeight': '600', 'marginTop': '10px'}),
                        dcc.Dropdown(
                            id='filter-gms-id',
                            options=[],
                            multi=True,
                            placeholder='Select GMS ID(s)',
                            style={'width': '300px', 'fontSize': '14px'}
                        ),

                        html.Label("Filter by Name:", style={'fontWeight': '600', 'marginTop': '15px'}),
                        dcc.Dropdown(
                            id='filter-name',
                            options=[],
                            multi=True,
                            placeholder='Select Name(s)',
                            style={'width': '300px', 'fontSize': '14px'}
                        ),

                        html.Label("Filter by Campaign:", style={'fontWeight': '600', 'marginTop': '15px'}),
                        dcc.Dropdown(
                            id='filter-location-id',
                            options=[],
                            multi=True,
                            placeholder='Select Campaign(s)',
                            style={'width': '300px', 'fontSize': '14px'}
                        ),
                    ],
                    id='filter-dropdown-container',
                    style={
                        'display': 'none',
                        'position': 'absolute',
                        'top': 'calc(100% + 10px)',
                        'right': '0',
                        'zIndex': '1000',
                        'backgroundColor': '#fff',
                        'padding': '15px',
                        'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
                        'borderRadius': '8px',
                        'width': '340px'
                    })
                ], style={'position': 'relative'}),

            ], style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'center',
                'marginBottom': '20px'
            }),

            # Silent Hours Section
            html.Div([
                html.H2("Silent_Hours AM & AM clashes",
                        style={
                            'textAlign': 'center',
                            'fontSize': '18px',
                            'fontWeight': '600',
                            'color': '#1f2937',
                            'marginBottom': '20px'
                        }),
                html.Div(id='clash-summary-chart')
            ], style=section_style),

            # Clash Detail Selection Section
            html.Div([
                html.Label("Select Clash Location to View Details:", style={'fontWeight': 'bold', 'marginTop': '10px'}),
                dcc.Dropdown(
                    id='category-dropdown',
                    placeholder='Select a clash location',
                    style={'fontSize': '14px', 'marginBottom': '20px'}
                ),
                html.Div(id='category-table')
            ], style=section_style),

            # Category Key Section
            html.Div([
                html.Label("Key: View Campaigns for Selected Clash Category:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='category-key-dropdown',
                    options=[{'label': key, 'value': key} for key in not_allowed_clash_categories.keys()],
                    placeholder='Select a category to view its campaign key',
                    style={'marginBottom': '10px', 'fontSize': '14px'}
                ),
                html.Div(id='category-key-display')
            ], style=section_style),

            # High-Risk GMS IDs Section
            html.Div([
                html.H2("High-Risk GMS IDs Summary",
                        style={
                            'textAlign': 'center',
                            'fontSize': '18px',
                            'fontWeight': '600',
                            'color': '#1f2937',
                            'marginTop': '10px',
                            'marginBottom': '20px'
                        }),
                html.Div(id='high-risk-gms-table')
            ], style=section_style),

        ], style={
            'padding': '30px 40px',
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
        Output('filter-dropdown-container', 'style'),
        Input('filter-toggle-btn', 'n_clicks'),
        State('filter-dropdown-container', 'style'),
        prevent_initial_call=True
    )
    def toggle_filter_dropdown(n_clicks, current_style):
        if not current_style or current_style.get('display') == 'none':
            # Show dropdown
            new_style = {
                'display': 'block',
                'position': 'absolute',
                'top': 'calc(100% + 10px)',
                'right': '0',
                'zIndex': '1000',
                'backgroundColor': '#fff',
                'padding': '15px',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
                'borderRadius': '8px',
                'width': '340px'
            }
        else:
            # Hide dropdown
            new_style = current_style.copy()
            new_style['display'] = 'none'
        
        return new_style
    
    @app.callback(
        Output('filter-gms-id', 'options'),
        Output('filter-name', 'options'),
        Output('filter-location-id', 'options'),
        Input('date-range-clashes', 'start_date'),
        Input('date-range-clashes', 'end_date'),
    )
    def update_filter_options(start_date, end_date):
        import pandas as pd
        
        if not start_date or not end_date:
            return [], [], []
        
        start = pd.to_datetime(start_date).date()
        end = pd.to_datetime(end_date).date()

        filtered_dfs = [
            df[(df['date_created'] >= start) & (df['date_created'] <= end)]
            for df in clash_dfs.values()
        ]
        
        all_data = pd.concat(filtered_dfs, ignore_index=True) if filtered_dfs else pd.DataFrame()

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

        app.filtered_clash_dfs = filtered_clash_dfs  # Store filtered data

        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('clash_count', ascending=True)

        if summary_df['clash_count'].sum() == 0:
            bar_fig = px.bar(title="No clashes found in selected date range.")
        else:
            bar_fig = px.bar(
                summary_df,
                x='clash_count',
                y='category',
                orientation='h',
                title='Number of Clashes by Location',
                labels={'category': 'Clash Location', 'clash_count': 'Number of Clashes'},
                color='clash_count',
                color_continuous_scale='Inferno'
            )

        dropdown_options = [{"label": label, "value": label} for label in clash_dfs.keys()]
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
                "No clashes found for the selected location.",
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
            columns=[
                {"name": "GMS ID", "id": "gms_id"},
                {"name": "Name", "id": "name"},
                {"name": "Date created", "id": "date_created"},
                {"name": "Campaign", "id": "registration_location_id"},
                {"name": "Final approval status", "id": "approval_final_status"},
                {"name": "Amount", "id": "amount"},
                {"name": "Final approval remarks", "id": "approval_final_remarks"},
                {"name": "Wallet status", "id": "approval_stage"},
            ],
            data=df_filtered.to_dict('records'),
            style_table={
                'overflowX': 'auto',
                'marginBottom': '30px',
                'fontSize': '12px',
                'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
            },
            style_cell={
                'textAlign': 'left',
                'fontSize': '12px',
                'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
            },
            style_header={
                'fontWeight': 'bold',
                'fontSize': '12px',
                'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
            },
            style_data_conditional=style_data_conditional,
            page_size=10,
            sort_action='native',
            
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
            'padding': '20px',
            'border': '1px solid #ccc',
            'borderRadius': '5px',
            'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
            'backgroundColor': '#f9f9f9'
        })

    @app.callback(
        Output('high-risk-gms-table', 'children'),
        Input('date-range-clashes', 'start_date'),
        Input('date-range-clashes', 'end_date'),
        Input('filter-gms-id', 'value'),
        Input('filter-name', 'value'),
        Input('filter-location-id', 'value'),
    )
    def update_high_risk_gms(start_date, end_date, gms_id_filter, name_filter, loc_id_filter):
        start = pd.to_datetime(start_date).date()
        end = pd.to_datetime(end_date).date()

        # Risk category and name aggregation
        gms_risk = {}       # gms_id -> set of clash categories
        gms_names = {}      # gms_id -> set of names

        for label, df_clash in app.filtered_clash_dfs.items():
            df_filtered = df_clash[(df_clash['date_created'] >= start) & (df_clash['date_created'] <= end)]

            if gms_id_filter:
                df_filtered = df_filtered[df_filtered['gms_id'].isin(gms_id_filter)]
            if name_filter:
                df_filtered = df_filtered[df_filtered['name'].isin(name_filter)]
            if loc_id_filter:
                df_filtered = df_filtered[df_filtered['registration_location_id'].isin(loc_id_filter)]

            for _, row in df_filtered.iterrows():
                gms_id = row['gms_id']
                name = row['name']

                gms_risk.setdefault(gms_id, set()).add(label)
                gms_names.setdefault(gms_id, set()).add(name)

        # Prepare the summary DataFrame
        high_risk_data = [
            {
                "gms_id": gms_id,
                "name": ", ".join(sorted(gms_names.get(gms_id, []))),
                "clash_categories": ", ".join(sorted(categories)),
                "num_categories": len(categories)
            }
            for gms_id, categories in gms_risk.items()
        ]

        if not high_risk_data:
            return html.Div("No high-risk GMS IDs found in the selected range.")

        df_risk = pd.DataFrame(high_risk_data).sort_values(by="num_categories", ascending=False)

        return html.Div([
            dash_table.DataTable(
                columns=[
                    {"name": "GMS ID", "id": "gms_id"},
                    {"name": "Name(s)", "id": "name"},
                    {"name": "Categories of the clashes", "id": "clash_categories"},
                    {"name": "Number of clashes", "id": "num_categories"},
                ],

                data=df_risk.to_dict('records'),
                page_size=10,
                sort_action='native',

                style_table={
                    'overflowX': 'auto',
                    'border': '1px solid #e5e7eb',
                    'borderRadius': '8px'
                },

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
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#ddd6fe'
                    }
                ],
            )
        ], style={
            'padding': '0 20px',
            'marginBottom': '40px'
        })






    return app
