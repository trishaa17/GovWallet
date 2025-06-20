import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, dash_table, Input, Output, State
import requests
from io import StringIO
import random
from datetime import date, timedelta
import colorsys
# from loadcsv import load_csv_data


def generate_pastel_colors(n):
    pastel_colors = []
    alpha = 0.4  

    for i in range(n):
        h = i / n
        s = 0.4
        v = 0.95
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        pastel_colors.append(f'rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, {alpha})')

    random.shuffle(pastel_colors)
    return pastel_colors

def detect_clashes_by_keyword(df, category_keywords):
    # Normalize registration_location_id: lowercase and remove dashes/underscores
    df['registration_location_id_norm'] = df['registration_location_id'].str.lower().str.replace(r'[-_]', '', regex=True)

    clashes_by_category = {}
    used_campaigns = set()

    # Process more specific keywords first (order matters)
    for label, keyword in category_keywords.items():
        clashing = []

        grouped = df.groupby(['gms_id', 'date_created'])

        for (gms_id, date), group in grouped:
            # Match campaigns for this category, excluding ones already matched to earlier categories
            matched_campaigns = set(
                group.loc[
                    group['registration_location_id_norm'].str.contains(keyword) &
                    ~group['registration_location_id_norm'].isin(used_campaigns),
                    'registration_location_id_norm'
                ]
            )

            if len(matched_campaigns) >= 2:
                clash_rows = group[group['registration_location_id_norm'].isin(matched_campaigns)]
                clashing.append(clash_rows)

        if clashing:
            result_df = pd.concat(clashing).drop_duplicates()
            clashes_by_category[label] = result_df

            # Track used campaigns to prevent overlaps
            used_campaigns.update(result_df['registration_location_id_norm'].unique())
        else:
            clashes_by_category[label] = pd.DataFrame(columns=df.columns)

    return clashes_by_category


def create_dash_shift_clashes_venue(server):
    # url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EWMP-swatlRCjdz-VttIKnIBwf0pSEuxp5lq2aAXhCszNg?download=1"
    url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EXMm4it_HQtPiiDnLuS4iWQB_QX4KRWYNExsu-yRGrK0bg?download=1"
    response = requests.get(url)
    response.raise_for_status()
    csv_data = response.content.decode('utf-8')

    df = pd.read_csv(StringIO(csv_data))
    # df = load_csv_data()
    df['date_created'] = pd.to_datetime(df['date_created'], utc=True)
    df['date_created'] = df['date_created'].dt.date
    df = df[df['approval_final_status'].str.lower() == 'pending']


    category_keywords = {
        "Silent Hour 11pm - 7am": "silenthour11pm7am",
        "Silent Hours AM": "silenthoursam",
        "AM": "attendanceam",
        "PM": "attendancepm",
    }


    clash_dfs = detect_clashes_by_keyword(df, category_keywords)

    app = Dash(__name__, server=server, routes_pathname_prefix='/appShiftClashesVenue/')
    app.title = "GovWallet Shift Timing Clashes"

    min_date = min(df['date_created'])
    max_date = max(df['date_created'])

    # Get current week's Monday and Sunday
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
            html.H1(
                "GovWallet Shift Timing Clashes (Venue Manager Version)",
                style={
                    'margin': '0',
                    'fontSize': '24px',
                    'fontWeight': '600',
                    'color': '#1f2937',
                    'textAlign': 'center',
                    'padding': '20px 40px',
                    'backgroundColor': '#ffffff',
                    'borderBottom': '1px solid #e5e7eb'
                }
            )
        ], style={
            'padding': '20px 40px',
            'backgroundColor': '#ffffff',
            'borderBottom': '1px solid #e5e7eb'
        }),

        # Main content
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

        # Clash Summary Chart
        html.Div(id='clash-summary-chart', style=section_style),

        # Clash Detail Section
        html.Div([
            html.Label("Select Clash Shift Timing to View Details:", style={'fontWeight': '600', 'marginBottom': '10px'}),
            dcc.Dropdown(
                id='category-dropdown',
                placeholder='Select a clashing shift timing',
                style={'fontSize': '14px', 'marginBottom': '20px'}
            ),
            html.Div(id='category-table')
        ], style=section_style),

        # High-Risk GMS IDs Section
        html.Div([
            html.H2(
                "High-Risk GMS IDs",
                style={
                    'textAlign': 'center',
                    'fontSize': '18px',
                    'fontWeight': '600',
                    'color': '#1f2937',
                    'marginTop': '40px',
                    'marginBottom': '20px'
                }
            ),
            html.Div(id='high-risk-gms-table')
        ], style=section_style),

    ], style={
        'padding': '30px 40px',
        'backgroundColor': '#ffffff',
        'minHeight': 'calc(100vh - 80px)',
        'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
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
