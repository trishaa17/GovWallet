from dash import Dash, dcc, html, Input, Output, dash_table, State
import pandas as pd
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme
import requests
from io import StringIO
import urllib.parse
from dash import callback
from urllib.parse import unquote
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
from graphs_people import DisbursementDashboardGraphs

app = None  # global placeholder
url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EfFwqNRlqjdKgUnvBWe53SEBKKJA9yK7RomjADmwfuT6iQ?download=1"
response = requests.get(url)
response.raise_for_status()
csv_data = response.content.decode('utf-8')
df1 = pd.read_csv(StringIO(csv_data))

def get_data_raw():
    df = df1.copy()
    df['payout_date'] = pd.to_datetime(df['payout_date'], errors='coerce').dt.date
    # Only drop rows where essential data is missing, but keep rejected entries
    df = df.dropna(subset=['approval_final_status'])  # Keep entries with approval status
    df['shift_count'] = 1
    return df

def get_data():
    df = df1.copy()
    df['payout_date'] = pd.to_datetime(df['payout_date'], errors='coerce').dt.date
    df = df.dropna(subset=['name', 'payout_date'])
    df = df[df['wallet_status'].str.lower() != 'pending']  # 👈 Filter out pending
    df['shift_count'] = 1
    return df

graphs_module = DisbursementDashboardGraphs(get_data, get_data_raw)

def detect_conflicts(df):
    df = df.copy()
    df['registration_date'] = pd.to_datetime(df['registration_date'], errors='coerce').dt.date
    
    conflicts = []
    # Define mutually exclusive substrings
    mutually_exclusive_pairs = [
        ('Attendance_Silent-Hours_AM', 'Attendance_AM'),
        # Add more if needed
    ]

    # Define substrings to check for duplicates
    shift_keywords_to_check_duplicates = [
        'Silent_Hours_AM',
        'Attendance_AM',
        'Attendance_PM',
        'Attendance_Silent_Hour_11PM_7AM',
        'SEN_Attendance_BENTO',
        'TSA_Attendance',
        'test',
    ]

    # Group by person and date
    for (name, date), group in df.groupby(['name', 'registration_date']):
        if pd.isna(date):  # Skip if date is NaN
            continue
            
        shift_types = group['registration_location_id'].tolist()
        shift_types_lower = [str(s).lower() for s in shift_types if pd.notna(s)]

        # CONFLICT TYPE 1: Mutually Exclusive Substring Shifts
        for kw1, kw2 in mutually_exclusive_pairs:
            if any(kw1.lower() in s for s in shift_types_lower) and any(kw2.lower() in s for s in shift_types_lower):
                conflicts.append({
                    'name': name,
                    'date': date,
                    'conflict_type': 'Mutually Exclusive Shifts',
                    'description': f"Shifts contain both '{kw1}' and '{kw2}'",
                    'shifts_involved': [s for s in shift_types if kw1.lower() in str(s).lower() or kw2.lower() in str(s).lower()],
                    'severity': 'HIGH'
                })

        # CONFLICT TYPE 2: Duplicate Substring Shifts
        for keyword in shift_keywords_to_check_duplicates:
            matched_shifts = [s for s in shift_types if keyword.lower() in str(s).lower()]
            if len(matched_shifts) > 1:
                conflicts.append({
                    'name': name,
                    'date': date,
                    'conflict_type': 'Duplicate Shift Entry',
                    'description': f"Multiple shifts contain '{keyword}' ({len(matched_shifts)} times)",
                    'shifts_involved': matched_shifts,
                    'severity': 'MEDIUM'
                })

    return pd.DataFrame(conflicts)

def get_data_with_conflicts():
    """
    Enhanced version of get_data() that includes conflict detection
    """
    df = get_data()  # Your existing function
    
    # Detect conflicts
    conflicts_df = detect_conflicts(df)
    
    # Add conflict flags to main dataframe
    df['has_conflict'] = False
    df['conflict_types'] = ''
    
    if not conflicts_df.empty:
        # Mark rows with conflicts
        for _, conflict in conflicts_df.iterrows():
            # Use registration_date for conflict matching instead of payout_date
            mask = (df['name'] == conflict['name'])
            # Add date matching if both dates exist
            if 'registration_date' in df.columns:
                df['registration_date'] = pd.to_datetime(df['registration_date'], errors='coerce').dt.date
                mask = mask & (df['registration_date'] == conflict['date'])
            
            if mask.any():
                df.loc[mask, 'has_conflict'] = True
                
                # Accumulate conflict types for each row
                for idx in df[mask].index:
                    existing_conflicts = df.loc[idx, 'conflict_types']
                    new_conflict = conflict['conflict_type']
                    if existing_conflicts:
                        df.loc[idx, 'conflict_types'] = f"{existing_conflicts}, {new_conflict}"
                    else:
                        df.loc[idx, 'conflict_types'] = new_conflict
    
    return df, conflicts_df

def layout_avg():
    df = get_data()
    daily_shifts = df.groupby(['name', 'payout_date'])['shift_count'].sum().reset_index()
    avg_shifts = daily_shifts.groupby('name')['shift_count'].mean().reset_index(name='avg_shifts_per_day')
    
    return html.Div([
        html.H2("Volunteer Finder"),
        dcc.Dropdown(
            id='name-filter-bottom',
            options=[{'label': n, 'value': n} for n in sorted(df['name'].unique()) if pd.notna(n)],
            placeholder="Search or Select Name(s)",
            multi=True,
            style={'marginTop': '10px', 'marginBottom': '10px'}
        ),
        dcc.RadioItems(
            id='avg-sort-order',
            options=[
                {'label': 'Descending', 'value': 'desc'},
                {'label': 'Ascending', 'value': 'asc'}
            ],
            value='desc',
            labelStyle={'display': 'inline-block', 'marginRight': '10px'}
        ),
        dash_table.DataTable(
            id='avg-shift-table',
            columns=[
                {"name": "Name", "id": "link", "presentation": "markdown", "type": "text"},
                {"name": "Avg Shifts/Day", "id": "avg_shifts_per_day", "type": "numeric", "format": Format(precision=2, scheme=Scheme.fixed)}
            ],
            markdown_options={"html": True},
            data=[
                {
                    "link": f"[{row['name']}](/app3/person/{urllib.parse.quote(str(row['name']))})",
                    "avg_shifts_per_day": row['avg_shifts_per_day']
                }
                for _, row in avg_shifts.iterrows()
                if pd.notna(row['name'])
            ],
            style_cell={'textAlign': 'left'},
            page_size=15
        ),
        html.Hr()
    ])

def layout_person(name):
    name = unquote(name)
    df2 = df1[df1['name'] == name].copy()
    
    if df2.empty:
        return html.Div([
            html.H2(f"No data found for {name}"),
            dcc.Link("← Back to Avg Shift Summary", href="/app3/")
        ])
    
    df2['shift_count'] = 1 
    df2['payout_date'] = pd.to_datetime(df2['payout_date'], errors='coerce').dt.date
    df2 = df2.dropna(subset=['payout_date'])
    df2 = df2[df2['wallet_status'].str.lower() != 'pending']  # 👈 Filter out pending


    # Get profile information with safe access
    total_shifts = df2.shape[0]
    gms_id = df2['gms_id'].iloc[0] if 'gms_id' in df2.columns and not df2.empty else "Unknown"
    badge_id = df2['badge_id'].iloc[0] if 'badge_id' in df2.columns and not df2.empty else "Unknown"
    role = df2['gms_role_name'].iloc[0] if 'gms_role_name' in df2.columns and not df2.empty else "Unknown"

    # Create initial accordion items
    grouped = df2.groupby('payout_date')
    accordion_items = []
    
    for date, group in grouped:
        total_shifts_date = group.shape[0]
        
        # Safe access to columns with defaults
        shifts = group.get('registration_location_id', pd.Series(['Unknown'] * len(group)))
        statuses = group.get('wallet_status', pd.Series(['Unknown'] * len(group)))
        amounts = group.get('amount', pd.Series([0.0] * len(group)))
        
        shift_details = [
            html.Tr([
                html.Td(str(shift)),
                html.Td(str(status)),
                html.Td(f"${float(amount):.2f}" if pd.notna(amount) else "$0.00"),
            ]) for shift, status, amount in zip(shifts, statuses, amounts)
        ]
        
        total_amount = amounts.sum() if not amounts.empty else 0.0
        shift_details.append(
            html.Tr([
                html.Td(html.B("Total Amount Earned")),
                html.Td(),
                html.Td(html.B(f"${total_amount:.2f}"))
            ], style={"backgroundColor": "#f8f9fa", "borderTop": "2px solid #ccc"})
        )

        # Create work schedule for this date
        work_schedule = []
        unique_shifts = shifts.unique()
        for shift in unique_shifts:
            if pd.notna(shift):
                shift_count_for_day = len(group[group['registration_location_id'] == shift])
                work_schedule.append(
                    html.Div([
                        html.Span(f"• {shift}", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                        html.Span(f"({shift_count_for_day} time{'s' if shift_count_for_day > 1 else ''})", 
                                 style={'color': '#666', 'fontSize': '0.9em'})
                    ], style={'marginBottom': '5px'})
                )

        accordion_items.append(
            dbc.AccordionItem([
                html.Br(),
                html.P(f"Total shifts: {total_shifts_date}", style={'fontWeight': 'bold'}),
                dbc.Table([
                    html.Thead(html.Tr([
                        html.Th("Shift Name"), 
                        html.Th("Status"), 
                        html.Th("Amount Paid")
                    ])),
                    html.Tbody(shift_details)
                ], bordered=True),
                html.Hr(),
                html.H6("Work Schedule for this Day:", style={'fontWeight': 'bold', 'marginTop': '15px'}),
                html.Div(work_schedule, style={'marginTop': '10px'})
            ], title=date.strftime("%Y-%m-%d") if pd.notna(date) else "Unknown Date", className="bg-light")
        )
    
    # Get conflicts data
    df, conflicts_df = get_data_with_conflicts()
    
    # Filter conflicts for this specific person
    person_conflicts = conflicts_df[conflicts_df['name'] == name] if not conflicts_df.empty else pd.DataFrame()
    
    # Prepare conflicts section with improved layout
    if person_conflicts.empty:
        conflicts_section = html.Div([
            html.Div([
                html.Div([
                    html.Div("✅", style={'fontSize': '24px', 'marginBottom': '10px'}),
                    html.H5("All Clear!", style={'margin': 0, 'color': '#27ae60'}),
                    html.P("No conflicts detected for this person", 
                           style={'margin': '5px 0 0 0', 'color': '#7f8c8d', 'fontSize': '14px'})
                ], style={'textAlign': 'center'})
            ], style={
                'padding': '30px', 
                'backgroundColor': '#e8f5e8', 
                'borderRadius': '12px',
                'border': '2px solid #27ae60'
            })
        ])
    else:
        # Group conflicts by severity
        high_conflicts = person_conflicts[person_conflicts['severity'] == 'HIGH']
        medium_conflicts = person_conflicts[person_conflicts['severity'] == 'MEDIUM']
        low_conflicts = person_conflicts[person_conflicts['severity'] == 'LOW']
        
        conflicts_section = html.Div([            
            # Improved conflicts table with better styling
            html.Div([
                html.H4("Shift Conflicts Detected!", style={
                    'fontWeight': 'bold', 
                    'marginBottom': '20px',
                    'color': "#000000",
                    'textAlign': 'center'
                }),
                html.Div([
                html.Div([
                    #html.Div("🚫", style={'fontSize': '24px', 'marginBottom': '8px'}),
                    html.H4(str(len(high_conflicts)), style={'color': '#e74c3c', 'margin': '0 0 5px 0', 'fontSize': '28px'}),
                    html.P("Mutually Exclusive", style={'margin': 0, 'fontSize': '13px', 'fontWeight': '500'}),
                    html.P("Shifts", style={'margin': 0, 'fontSize': '13px', 'fontWeight': '500'})
                ], style={
                    'textAlign': 'center', 
                    'padding': '20px 15px', 
                    'backgroundColor': '#fdf2f2', 
                    'borderRadius': '12px', 
                    'flex': 1, 
                    'margin': '0 8px',
                    'border': '2px solid #fecaca',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
                }),
                
                html.Div([
                    #html.Div("🔄", style={'fontSize': '24px', 'marginBottom': '8px'}),
                    html.H4(str(len(medium_conflicts)), style={'color': '#f39c12', 'margin': '0 0 5px 0', 'fontSize': '28px'}),
                    html.P("Duplicate Shift", style={'margin': 0, 'fontSize': '13px', 'fontWeight': '500'}),
                    html.P("Entries", style={'margin': 0, 'fontSize': '13px', 'fontWeight': '500'})
                ], style={
                    'textAlign': 'center', 
                    'padding': '20px 15px', 
                    'backgroundColor': '#fefbf2', 
                    'borderRadius': '12px', 
                    'flex': 1, 
                    'margin': '0 8px',
                    'border': '2px solid #fed7aa',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
                }),
                
                html.Div([
                    #html.Div("💰", style={'fontSize': '24px', 'marginBottom': '8px'}),
                    html.H4(str(len(low_conflicts)), style={'color': '#8e44ad', 'margin': '0 0 5px 0', 'fontSize': '28px'}),
                    html.P("Amount Limit", style={'margin': 0, 'fontSize': '13px', 'fontWeight': '500'}),
                    html.P("Exceeded", style={'margin': 0, 'fontSize': '13px', 'fontWeight': '500'})
                ], style={
                    'textAlign': 'center', 
                    'padding': '20px 15px', 
                    'backgroundColor': '#faf7ff', 
                    'borderRadius': '12px', 
                    'flex': 1, 
                    'margin': '0 8px',
                    'border': '2px solid #ddd6fe',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
                })
            ], style={
                'display': 'flex', 
                'marginBottom': '30px',
                'gap': '0px'
            }),
                dash_table.DataTable(
                    columns=[
                        {"name": "Date", "id": "date", "type": "datetime"},
                        {"name": "Type", "id": "conflict_type"},
                        {"name": "Description", "id": "description"},
                        {"name": "Severity", "id": "severity"},
                    ],
                    data=person_conflicts.to_dict('records'),
                    style_cell={
                        'textAlign': 'left', 
                        'whiteSpace': 'normal', 
                        'height': 'auto',
                        'padding': '12px',
                        'fontFamily': 'Inter, sans-serif'
                    },
                    style_header={
                        'backgroundColor': '#f8f9fa',
                        'fontWeight': 'bold',
                        'fontSize': '14px',
                        'color': '#2c3e50',
                        'border': '1px solid #dee2e6'
                    },
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{severity} = HIGH'},
                            'backgroundColor': '#fdf2f2',
                            'color': '#2d3748',
                            'border': '1px solid #fecaca'
                        },
                        {
                            'if': {'filter_query': '{severity} = MEDIUM'},
                            'backgroundColor': '#fefbf2',
                            'color': '#2d3748',
                            'border': '1px solid #fed7aa'
                        },
                        {
                            'if': {'filter_query': '{severity} = LOW'},
                            'backgroundColor': '#faf7ff',
                            'color': '#2d3748',
                            'border': '1px solid #ddd6fe'
                        }
                    ],
                    page_size=10,
                    sort_action="native",
                    style_table={
                        'borderRadius': '8px',
                        'overflow': 'hidden',
                        'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
                    }
                )
            ], style={
                'backgroundColor': '#fff4f4',
                'border': '3px solid #ff4d4d',
                'borderRadius': '16px',
                'padding': '30px',
                'boxShadow': '0 4px 12px rgba(255, 77, 77, 0.2)',
                'marginBottom': '40px'
            })
        ])
        
    # Safe calculation of totals
    total_earned = df2['amount'].sum() if 'amount' in df2.columns else 0.0
    days_worked = df2['payout_date'].nunique() if not df2.empty else 1
    avg_per_day = total_earned / days_worked if days_worked > 0 else 0.0
        
    return html.Div([
        # Add proper spacing and container
        html.Div([
            html.Div([
                html.Div([
                    # Avatar with better styling
                    html.Img(src='https://resources.fina.org/photo-resources/2024/07/12/e3c65862-2e4a-469a-a358-e6a23545bfa9/7fafa8e5-db48-4647-bfca-3fbf5ccfa45b?height=240', style={
                        'borderRadius': '50%',
                        'height': '150px',
                        'width': '170px',
                        'marginRight': '25px',
                    }),

                    # Name and details with improved typography
                    html.Div([
                        html.H2(name, style={
                            'margin': '0 0 10px 0', 
                            'color': "#000000",
                            'fontWeight': '700'
                        }),
                        html.Div([
                            html.Span(style={'marginRight': '5px'}),
                            html.Span(f"GMS ID: {gms_id}", style={'color': 'black', 'fontSize': '14px'})
                        ], style={'marginBottom': '5px'}),
                        html.Div([
                            html.Span( style={'marginRight': '5px'}),
                            html.Span(f"Badge ID: {badge_id}", style={'color': 'black', 'fontSize': '14px'})
                        ], style={'marginBottom': '5px'}),
                        html.Div([
                            html.Span(style={'marginRight': '5px'}),
                            html.Span(f"Role: {role}", style={'color': 'black', 'fontSize': '14px'})
                        ], style={'marginBottom': '15px'}),
                        html.Div([
                            html.Span(style={'marginRight': '5px'}),
                            html.Span(f"Total Shifts: {total_shifts}", style={'fontWeight': 'bold', 'color': "#000000", 'fontSize': '16px'})
                        ])
                    ])
                ], style={
                    'display': 'flex',
                    'alignItems': 'center'
                }),
            ], style={
                'width': '100%',
                'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'color': 'white',
                'padding': '25px',
                'borderRadius': '15px',
                'marginBottom': '30px',
                'boxShadow': '0 4px 12px rgba(0, 0, 0, 0.15)'
            })
        ]),
        
        # Volunteer's Shifts Table with better styling
        html.Div([
            html.H4("Volunteer's Shifts", style={
                'marginBottom': '20px',
                'color': '#2c3e50',
                'fontWeight': '600'
            }),
            dash_table.DataTable(
                columns=[
                    {"name": "Name", "id": "name"},
                    {"name": "Date", "id": "payout_date"},
                    {"name": "Shift Name", "id": "registration_location_id"}
                ],
                data=df2.to_dict('records'),
                style_table={'overflowX': 'auto', 'borderRadius': '8px', 'overflow': 'hidden'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '12px',
                    'fontFamily': 'Inter, sans-serif'
                },
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': 'bold',
                    'color': '#2c3e50'
                },
                style_data={
                    'backgroundColor': '#ffffff',
                    'border': '1px solid #e2e8f0'
                },
                page_size=20
            )
        ], style={
            'backgroundColor': 'white',
            'padding': '25px',
            'borderRadius': '12px',
            'marginBottom': '30px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
            'border': '1px solid #e2e8f0'
        }),
        
        # Dashboard Cards Section with improved design
        html.Div([
            html.Div([
                # Card 1 - Total Earnings
                html.Div([
                    html.Div([
                        html.Div("💰", style={'fontSize': '32px', 'marginBottom': '10px'}),
                        html.H3(f"${total_earned:.2f}", style={'margin': '0 0 5px 0', 'color': '#27ae60', 'fontSize': '32px'}),
                        html.P("Total Earned", style={'margin': 0, 'color': '#7f8c8d', 'fontSize': '14px', 'fontWeight': '500'})
                    ], style={'textAlign': 'center'})
                ], style={
                    'backgroundColor': 'white',
                    'padding': '25px 20px',
                    'borderRadius': '15px',
                    'boxShadow': '0 4px 12px rgba(0,0,0,0.08)',
                    'border': '2px solid #d5edda',
                    'flex': '1',
                    'margin': '0 10px',
                    'transition': 'transform 0.2s'
                }),
                
                # Card 2 - Days Worked
                html.Div([
                    html.Div([
                        html.Div("📅", style={'fontSize': '32px', 'marginBottom': '10px'}),
                        html.H3(f"{days_worked}", style={'margin': '0 0 5px 0', 'color': '#3498db', 'fontSize': '32px'}),
                        html.P("Days Worked", style={'margin': 0, 'color': '#7f8c8d', 'fontSize': '14px', 'fontWeight': '500'})
                    ], style={'textAlign': 'center'})
                ], style={
                    'backgroundColor': 'white',
                    'padding': '25px 20px',
                    'borderRadius': '15px',
                    'boxShadow': '0 4px 12px rgba(0,0,0,0.08)',
                    'border': '2px solid #cce7ff',
                    'flex': '1',
                    'margin': '0 10px',
                    'transition': 'transform 0.2s'
                }),
                
                # Card 3 - Average per Day
                html.Div([
                    html.Div([
                        html.Div("📊", style={'fontSize': '32px', 'marginBottom': '10px'}),
                        html.H3(f"${avg_per_day:.2f}", style={'margin': '0 0 5px 0', 'color': '#e74c3c', 'fontSize': '32px'}),
                        html.P("Avg per Day", style={'margin': 0, 'color': '#7f8c8d', 'fontSize': '14px', 'fontWeight': '500'})
                    ], style={'textAlign': 'center'})
                ], style={
                    'backgroundColor': 'white',
                    'padding': '25px 20px',
                    'borderRadius': '15px',
                    'boxShadow': '0 4px 12px rgba(0,0,0,0.08)',
                    'border': '2px solid #ffdddd',
                    'flex': '1',
                    'margin': '0 10px',
                    'transition': 'transform 0.2s'
                })
            ], style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'gap': '0px',
                'marginBottom': '40px'
            })
        ]),

        # Conflicts section (already improved above)
        conflicts_section,

        html.Br(),
        
        # Summary of Daily Shifts with improved design
        html.Div([
            html.Div([
                html.H4("Summary of Daily Shifts", style={
                    'fontWeight': '600',
                    'color': '#2c3e50',
                    'marginBottom': '20px'
                }),
                html.Div([
                    html.Div([
                        html.Label("Sort Options:", style={'fontWeight': '600', 'marginRight': '15px', 'color': '#2c3e50'}),
                        dcc.RadioItems(
                            id='date-sort-order',
                            options=[
                                {'label': 'Ascending', 'value': 'asc'},
                                {'label': 'Descending', 'value': 'desc'},
                                {'label': 'Show All', 'value': 'all'}
                            ],
                            value='asc',
                            labelStyle={'display': 'inline-block', 'marginRight': '20px', 'fontSize': '14px'}
                        )
                    ], style={'display': 'flex', 'alignItems': 'center', 'flex': 1}),
                    
                    html.Button([
                        DashIconify(icon="carbon:filter", width=20, style={'marginRight': '8px'}),
                        "Filter by Date"
                    ],
                        id='toggle-date-filter',
                        n_clicks=0,
                        style={
                            'border': '1px solid #3498db',
                            'borderRadius': '8px',
                            'padding': '8px 16px',
                            'backgroundColor': '#3498db',
                            'color': 'white',
                            'cursor': 'pointer',
                            'fontSize': '14px',
                            'fontWeight': '500',
                            'display': 'flex',
                            'alignItems': 'center'
                        }
                    )
                ], style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'space-between',
                    'marginBottom': '20px',
                    'padding': '15px',
                    'backgroundColor': '#f8f9fa',
                    'borderRadius': '8px'
                }),

                html.Div(
                    dcc.DatePickerSingle(
                        id='date-filter',
                        style={'width': '100%'}
                    ),
                    id='date-filter-container',
                    style={'display': 'none', 'marginBottom': '20px'}
                ),
                
                # Accordion container with better styling
                html.Div(
                    dbc.Accordion(accordion_items, start_collapsed=True, style={
                        'borderRadius': '8px',
                        'overflow': 'hidden'
                    }),
                    id='accordion-container'
                ),
                
                # Pagination with improved design
                html.Div([
                    html.Span(id="page-indicator", style={
                        'marginRight': '20px',
                        'alignSelf': 'center',
                        'fontWeight': '600',
                        'color': '#2c3e50'
                    }),
                    html.Button("← Previous", id="prev-page", n_clicks=0, style={
                        'padding': '8px 16px',
                        'fontSize': '14px',
                        'borderRadius': '8px',
                        'border': '1px solid #3498db',
                        'backgroundColor': 'white',
                        'color': '#3498db',
                        'marginRight': '10px',
                        'cursor': 'pointer',
                        'fontWeight': '500'
                    }),
                    html.Button("Next →", id="next-page", n_clicks=0, style={
                        'padding': '8px 16px',
                        'fontSize': '14px',
                        'borderRadius': '8px',
                        'border': '1px solid #3498db',
                        'backgroundColor': '#3498db',
                        'color': 'white',
                        'cursor': 'pointer',
                        'fontWeight': '500'
                    })
                ], style={
                    'display': 'flex',
                    'justifyContent': 'flex-end',
                    'alignItems': 'center',
                    'paddingTop': '20px',
                    'paddingBottom': '10px',
                    'borderTop': '1px solid #e2e8f0',
                    'marginTop': '30px'
                })
            ], style={
                'backgroundColor': "white",
                'padding': '30px',
                'borderRadius': '15px',
                'border': '1px solid #e2e8f0',
                'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.06)',
                'marginBottom': '40px'
            })
        ]),

        html.Br(),

        # Graphs Section with improved styling
        html.Div([
            html.Div([
                html.H4("Visualizations", style={
                    'marginBottom': '25px',
                    'fontWeight': '600',
                    'color': '#2c3e50'
                }),
                html.Label("Select Graph Type:", style={
                    'fontWeight': '600', 
                    'marginBottom': '15px',
                    'display': 'block',
                    'color': '#2c3e50'
                }),
                dcc.Dropdown(
                    id='person-graph-selector',
                    options=graphs_module.get_graph_options(),
                    value='shifts_per_person',
                    style={
                        'marginBottom': '20px',
                        'borderRadius': '8px'
                    },
                    placeholder="Choose a visualization..."
                ),
            html.Div(id='person-graph-container', style={'marginTop': '20px'})
            ], style={
                'backgroundColor': 'white',
                'padding': '25px',
                'borderRadius': '12px',
                'border': '1px solid #e2e8f0',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
            })
        ]),

        # Back link with better styling
        html.Div([
            dcc.Link([
                html.Span("← ", style={'marginRight': '5px'}),
                "Back to Volunteer Finder"
            ], href="/app3/", style={
                'color': '#3498db',
                'textDecoration': 'none',
                'fontSize': '16px',
                'fontWeight': '500',
                'padding': '12px 20px',
                'border': '1px solid #3498db',
                'borderRadius': '8px',
                'display': 'inline-block',
                'marginTop': '20px'
            })
        ], style={'textAlign': 'center'})
    ], style={
        'maxWidth': '12000px',
        'margin': '0 auto',
        'padding': '20px',
'backgroundColor': '#e9ecef',  # light gray-blue
        'minHeight': '100vh'
    })

